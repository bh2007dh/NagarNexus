import io
import uuid
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app

RUN_TAG = uuid.uuid4().hex[:6]
EMAIL_A = f"priya.{RUN_TAG}@nagarnexus.org"
EMAIL_B = f"karthik.{RUN_TAG}@nagarnexus.org"
DATASET_NAME_A = f"Private Urban Telemetry CSV {RUN_TAG}"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_and_seeded_database(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_auth_registration_login_and_protected_routes(client: TestClient):
    # Unauthenticated request to protected route must fail with 401
    unauth = client.get("/api/auth/me")
    assert unauth.status_code == 401

    # Register User A
    reg_res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Priya Sundaram",
            "email": EMAIL_A,
            "password": "StrongPassword123!",
            "role": "analyst",
            "organization": "Chennai Urban Lab",
            "preferred_city": "Chennai",
        },
    )
    assert reg_res.status_code in (200, 201)
    token_a = reg_res.json()["access_token"]
    assert token_a

    # Duplicate email registration must return 400
    dup_res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Priya Duplicate",
            "email": EMAIL_A,
            "password": "StrongPassword123!",
        },
    )
    assert dup_res.status_code == 400

    # Login User A
    login_res = client.post(
        "/api/auth/login",
        json={"email": EMAIL_A, "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["user"]["email"] == EMAIL_A

    # Get current user profile
    headers_a = {"Authorization": f"Bearer {token_a}"}
    me_res = client.get("/api/auth/me", headers=headers_a)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Priya Sundaram"


def test_csv_and_excel_upload_invalid_rejection_and_access_control(client: TestClient):
    # Login as User A
    login_a = client.post(
        "/api/auth/login",
        json={"email": EMAIL_A, "password": "StrongPassword123!"},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    # Register User B to test private dataset isolation
    reg_b = client.post(
        "/api/auth/register",
        json={
            "full_name": "Karthik V",
            "email": EMAIL_B,
            "password": "SecondPassword123!",
        },
    )
    assert reg_b.status_code in (200, 201)
    headers_b = {"Authorization": f"Bearer {reg_b.json()['access_token']}"}

    # 1. Reject invalid file extension (.exe / .txt)
    bad_ext = client.post(
        "/api/datasets/upload",
        headers=headers_a,
        files={"file": ("malicious.exe", b"MZ\x90\x00binarycontent", "application/octet-stream")},
    )
    assert bad_ext.status_code == 400

    # 2. Reject binary file disguised with .csv extension
    fake_csv = client.post(
        "/api/datasets/upload",
        headers=headers_a,
        files={"file": ("disguised.csv", b"col1,col2\x00\x00binarynulls", "text/csv")},
    )
    assert fake_csv.status_code == 400

    # 3. Upload valid CSV with missing values, duplicates, and outliers
    csv_content = (
        "observation_date,locality,temperature_c,rainfall_mm,humidity_pct,pm25\n"
        "2026-09-01,Zone_A,32.5,12.0,70.0,45.2\n"
        "2026-09-01,Zone_A,32.5,12.0,70.0,45.2\n"  # Duplicate row
        "2026-09-02,Zone_A,33.1,15.4,,48.0\n"      # Missing humidity
        "2026-09-03,Zone_B,34.0,0.0,65.0,52.1\n"
        "2026-09-04,Zone_B,35.2,5.0,62.0,59.4\n"
        "2026-09-05,Zone_C,31.8,42.0,84.0,33.0\n"
        "2026-09-06,Zone_C,30.9,68.5,89.0,29.5\n"
        "2026-09-07,Zone_A,36.4,0.0,58.0,74.2\n"
        "2026-09-08,Zone_B,33.8,8.2,71.0,49.8\n"
        "2026-09-09,Zone_C,32.1,22.0,78.0,38.4\n"
        "2026-09-10,Zone_A,34.5,2.0,64.0,61.0\n"
        "2026-09-11,Zone_B,35.8,0.0,60.0,67.5\n"
        "2026-09-12,Zone_C,29.5,95.0,92.0,25.0\n"
        "2026-09-13,Zone_A,33.0,10.0,72.0,44.0\n"
        "2026-09-14,Zone_B,49.5,0.0,55.0,185.0\n"  # Outlier row
        "2026-09-15,Zone_C,31.2,18.5,80.0,36.2\n"
    ).encode("utf-8")

    up_csv = client.post(
        "/api/datasets/upload",
        headers=headers_a,
        files={"file": ("urban_test.csv", csv_content, "text/csv")},
        data={"name": DATASET_NAME_A},
    )
    assert up_csv.status_code == 201
    ds_data = up_csv.json()
    ds_id = ds_data["id"]
    assert ds_data["row_count"] == 16
    assert ds_data["column_count"] == 6
    assert ds_data["profile_json"]["missing_values_total"] == 1
    assert ds_data["profile_json"]["duplicate_records"] == 1

    # 4. Upload valid Excel (.xlsx) file
    df_excel = pd.DataFrame({
        "date": ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04"],
        "temperature_c": [31.2, 32.4, 33.1, 30.8],
        "pm25": [40.1, 44.5, 51.2, 38.0],
    })
    excel_buf = io.BytesIO()
    df_excel.to_excel(excel_buf, index=False, engine="openpyxl")
    excel_buf.seek(0)

    up_xlsx = client.post(
        "/api/datasets/upload",
        headers=headers_a,
        files={
            "file": (
                "excel_telemetry.xlsx",
                excel_buf.read(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert up_xlsx.status_code == 201
    assert up_xlsx.json()["file_type"] == "xlsx"

    # 5. Access control: User B MUST NOT be able to view or delete User A's private dataset
    forbidden_get = client.get(f"/api/datasets/{ds_id}", headers=headers_b)
    assert forbidden_get.status_code == 403
    forbidden_del = client.delete(f"/api/datasets/{ds_id}", headers=headers_b)
    assert forbidden_del.status_code == 403


def test_data_cleaning_eda_statistics_and_ml_pipeline(client: TestClient):
    login_a = client.post(
        "/api/auth/login",
        json={"email": EMAIL_A, "password": "StrongPassword123!"},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    # Find User A's uploaded CSV dataset
    ds_list = client.get("/api/datasets", headers=headers_a).json()["datasets"]
    private_ds = next(d for d in ds_list if d["name"] == DATASET_NAME_A)
    ds_id = private_ds["id"]

    # 1. Data Cleaning: Impute missing values, remove duplicates, clip outliers
    clean_res = client.post(
        f"/api/analysis/{ds_id}/clean",
        headers=headers_a,
        json={
            "missing_strategy": "median",
            "remove_duplicates": True,
            "outlier_action": "clip_iqr",
            "scaling_method": "none",
            "encoding_method": "none",
        },
    )
    assert clean_res.status_code == 200
    c_json = clean_res.json()
    assert c_json["comparison"]["missing_before"] == 1
    assert c_json["comparison"]["missing_after"] == 0
    assert c_json["comparison"]["duplicates_before"] == 1
    assert c_json["comparison"]["duplicates_after"] == 0
    assert c_json["comparison"]["rows_after"] == 15

    # 2. Automated EDA & Visualization
    eda_res = client.post(f"/api/eda/{ds_id}/run", headers=headers_a)
    assert eda_res.status_code == 200
    assert "temperature_c" in eda_res.json()["eda"]["descriptive_statistics"]

    viz_res = client.post(
        f"/api/eda/{ds_id}/visualization",
        headers=headers_a,
        json={"chart_type": "scatter", "x_column": "temperature_c", "y_column": "pm25"},
    )
    assert viz_res.status_code == 200
    assert viz_res.json()["matplotlib_image"].startswith("data:image/png;base64,")
    assert len(viz_res.json()["chart_data"]) > 0

    # 3. Statistical Analysis (all 10 sections)
    stat_res = client.post(
        f"/api/statistics/{ds_id}/calculate",
        headers=headers_a,
        json={
            "target_column": "temperature_c",
            "comparison_column": "pm25",
            "confidence_level": 0.95,
            "hypothesis_test": "auto",
        },
    )
    assert stat_res.status_code == 200
    s_data = stat_res.json()["results"]
    assert "Descriptive_Statistics" in s_data
    assert "Normal_Distribution" in s_data
    assert "Z_Score_Analysis" in s_data
    assert "Correlation_And_Covariance" in s_data
    assert "Hypothesis_Testing" in s_data
    assert "Confidence_Intervals" in s_data
    assert "Outlier_Detection" in s_data
    assert "Trend_Analysis" in s_data

    # 4. Machine Learning Training & Prediction (Regression, K-Means, Isolation Forest)
    train_reg = client.post(
        "/api/ml/train",
        headers=headers_a,
        json={
            "dataset_id": ds_id,
            "model_name": "Test RF PM2.5 Regressor",
            "algorithm": "random_forest_regressor",
            "feature_columns": ["temperature_c", "rainfall_mm", "humidity_pct"],
            "target_column": "pm25",
            "test_size": 0.25,
            "n_estimators": 30,
        },
    )
    assert train_reg.status_code == 201
    model_id = train_reg.json()["id"]
    assert "MAE" in train_reg.json()["metrics_json"]
    assert "RMSE" in train_reg.json()["metrics_json"]

    # Predict using trained model
    pred_res = client.post(
        f"/api/ml/models/{model_id}/predict",
        headers=headers_a,
        json={
            "features": {"temperature_c": 34.0, "rainfall_mm": 5.0, "humidity_pct": 66.0},
            "category": "air_quality",
            "actual_value": 50.0,
        },
    )
    assert pred_res.status_code == 200
    assert pred_res.json()["numeric_prediction"] is not None
    assert "confidence_interval_95" in pred_res.json()["confidence_metadata"]

    # Train K-Means clustering
    train_km = client.post(
        "/api/ml/train",
        headers=headers_a,
        json={
            "dataset_id": ds_id,
            "algorithm": "kmeans",
            "feature_columns": ["temperature_c", "rainfall_mm", "humidity_pct", "pm25"],
            "n_clusters": 3,
        },
    )
    assert train_km.status_code == 201
    assert "silhouette_score" in train_km.json()["metrics_json"]


def test_locations_risk_comparison_insights_and_reports(client: TestClient):
    login_a = client.post(
        "/api/auth/login",
        json={"email": EMAIL_A, "password": "StrongPassword123!"},
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

    # Dashboard summary
    dash = client.get("/api/dashboard/summary", headers=headers_a)
    assert dash.status_code == 200
    assert dash.json()["kpis"]["total_locations_monitored"] >= 5

    # Locations search & details
    locs = client.get("/api/locations/search", headers=headers_a).json()["locations"]
    assert len(locs) >= 2
    loc_detail = client.get(f"/api/locations/{locs[0]['id']}", headers=headers_a)
    assert loc_detail.status_code == 200

    # Location comparison
    comp = client.post(
        "/api/comparison/run",
        headers=headers_a,
        json={"location_ids": [locs[0]["id"], locs[1]["id"]]},
    )
    assert comp.status_code == 200
    assert comp.json()["locations_compared"] >= 2

    # Risk detection
    risk = client.post("/api/risk/analyze", headers=headers_a, json={"use_isolation_forest": True})
    assert risk.status_code == 200
    assert risk.json()["total_alerts"] >= 1

    # AI Insights
    ins = client.post("/api/insights/generate", headers=headers_a, json={})
    assert ins.status_code == 200
    assert len(ins.json()["recommendations"]) >= 1

    # Report generation & PDF/CSV download
    rep = client.post(
        "/api/reports/generate",
        headers=headers_a,
        json={
            "title": "Automated Integration Test Urban Dossier",
            "report_type": "dataset",
            "notes": "Generated during automated Pytest suite.",
        },
    )
    assert rep.status_code == 201
    rep_id = rep.json()["id"]

    pdf_dl = client.get(f"/api/reports/{rep_id}/download?format=pdf", headers=headers_a)
    assert pdf_dl.status_code == 200
    assert pdf_dl.content.startswith(b"%PDF")

    csv_dl = client.get(f"/api/reports/{rep_id}/download?format=csv", headers=headers_a)
    assert csv_dl.status_code == 200
