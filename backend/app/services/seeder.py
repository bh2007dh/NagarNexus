from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.data_processing.profiler import profile_dataframe
from app.machine_learning.ml_engine import train_and_evaluate_model
from app.models.dataset import Dataset, DatasetColumn
from app.models.location import Location, DataSource, Observation
from app.models.prediction import MLModel, Prediction
from app.models.risk import RiskAlert
from app.models.user import User, ActivityLog
from app.schemas.ml import MLTrainRequest


SAMPLE_LOCATIONS = [
    {
        "code": "LOC-M1",
        "name": "North Coastal Industrial Corridor (Sample Zone)",
        "city": "Metro Coastal Belt",
        "state": "Tamil Nadu",
        "latitude": 13.1485,
        "longitude": 80.2960,
        "geographical_resolution": "locality_benchmark_grid",
        "elevation_m": 6.5,
        "zone_type": "Industrial & Port Corridor",
        "temp_base": 33.2,
        "pm25_base": 64.0,
        "rain_base": 18.0,
    },
    {
        "code": "LOC-M2",
        "name": "Central Commercial Transit Hub (Sample Zone)",
        "city": "Metro Coastal Belt",
        "state": "Tamil Nadu",
        "latitude": 13.0418,
        "longitude": 80.2341,
        "geographical_resolution": "locality_benchmark_grid",
        "elevation_m": 11.0,
        "zone_type": "High-Density Commercial",
        "temp_base": 34.1,
        "pm25_base": 54.0,
        "rain_base": 14.0,
    },
    {
        "code": "LOC-M3",
        "name": "South IT & Wetland Basin (Sample Zone)",
        "city": "Metro Coastal Belt",
        "state": "Tamil Nadu",
        "latitude": 12.9716,
        "longitude": 80.2206,
        "geographical_resolution": "locality_benchmark_grid",
        "elevation_m": 4.2,
        "zone_type": "Low-Lying Floodplain & Tech Corridor",
        "temp_base": 31.8,
        "pm25_base": 38.0,
        "rain_base": 29.5,
    },
    {
        "code": "LOC-M4",
        "name": "West Suburban Green Canopy (Sample Zone)",
        "city": "Metro Inland Belt",
        "state": "Tamil Nadu",
        "latitude": 13.0102,
        "longitude": 80.1415,
        "geographical_resolution": "locality_benchmark_grid",
        "elevation_m": 19.5,
        "zone_type": "Residential & Vegetated Zone",
        "temp_base": 30.4,
        "pm25_base": 27.0,
        "rain_base": 12.0,
    },
    {
        "code": "LOC-M5",
        "name": "East Shoreline Microclimate Station (Sample Zone)",
        "city": "Metro Coastal Belt",
        "state": "Tamil Nadu",
        "latitude": 13.0005,
        "longitude": 80.2668,
        "geographical_resolution": "monitoring_station_benchmark",
        "elevation_m": 5.0,
        "zone_type": "Coastal Marine Boundary",
        "temp_base": 31.1,
        "pm25_base": 31.0,
        "rain_base": 21.0,
    },
]


def generate_sample_csv_files() -> Dict[str, str]:
    """
    Create the 5 clearly labeled sample CSV files in datasets/sample/ if not already present.
    Data is explicitly labeled as synthetic benchmark data (not actual municipal records).
    """
    sample_dir = Path(settings.SAMPLE_DIR)
    sample_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(42)

    base_date = datetime(2026, 8, 1, tzinfo=timezone.utc)
    days = 90

    # 1. Location Metadata CSV
    loc_path = sample_dir / "sample_location_metadata.csv"
    loc_df = pd.DataFrame([
        {
            "locality_code": loc["code"],
            "name": loc["name"],
            "city": loc["city"],
            "state": loc["state"],
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "geographical_resolution": loc["geographical_resolution"],
            "elevation_m": loc["elevation_m"],
            "zone_type": loc["zone_type"],
            "data_nature": "Synthetic Benchmark Metadata",
        }
        for loc in SAMPLE_LOCATIONS
    ])
    loc_df.to_csv(loc_path, index=False)

    # 2. Weather Observations CSV (with a few intentional NaNs for testing Data Cleaning)
    weather_rows = []
    for d in range(days):
        dt_str = (base_date + timedelta(days=d)).strftime("%Y-%m-%d")
        seasonal = 2.2 * np.sin(2 * np.pi * d / 45.0)
        for loc in SAMPLE_LOCATIONS[:3]:
            temp = round(float(loc["temp_base"] + seasonal + rng.normal(0, 1.3)), 2)
            hum = round(float(np.clip(72.0 - 1.4 * seasonal + rng.normal(0, 5.5), 40.0, 98.0)), 1)
            wind = round(float(np.clip(14.5 + rng.normal(0, 3.8), 2.5, 42.0)), 2)
            press = round(float(1008.5 - 0.15 * temp + rng.normal(0, 1.8)), 2)
            heat_idx = round(float(temp + 0.08 * hum), 2)
            weather_rows.append({
                "observation_date": dt_str,
                "locality_code": loc["code"],
                "zone_type": loc["zone_type"],
                "temperature_c": temp,
                "humidity_pct": hum,
                "wind_speed_kmh": wind,
                "surface_pressure_hpa": press,
                "heat_index_c": heat_idx,
            })
    weather_df = pd.DataFrame(weather_rows)
    # Inject 4 missing values for Data Cleaning demonstration
    weather_df.loc[[5, 28, 64], "humidity_pct"] = np.nan
    weather_df.loc[[14, 52], "wind_speed_kmh"] = np.nan
    weather_path = sample_dir / "sample_weather_observations.csv"
    weather_df.to_csv(weather_path, index=False)

    # 3. Air Quality Observations CSV
    aq_rows = []
    for d in range(days):
        dt_str = (base_date + timedelta(days=d)).strftime("%Y-%m-%d")
        for loc in SAMPLE_LOCATIONS[:3]:
            traffic_idx = round(float(np.clip(65.0 + rng.normal(0, 15.0), 20.0, 100.0)), 1)
            pm25 = round(float(np.clip(loc["pm25_base"] + 0.35 * (traffic_idx - 60) + rng.normal(0, 9.5), 10.0, 165.0)), 2)
            pm10 = round(float(pm25 * 1.65 + rng.normal(0, 11.0)), 2)
            no2 = round(float(np.clip(22.0 + 0.45 * traffic_idx + rng.normal(0, 6.0), 8.0, 125.0)), 2)
            o3 = round(float(np.clip(34.0 + rng.normal(0, 8.5), 10.0, 95.0)), 2)
            co = round(float(np.clip(0.55 + 0.012 * traffic_idx + rng.normal(0, 0.15), 0.1, 3.5)), 2)
            aqi = round(float(max(pm25 * 2.1, pm10 * 1.1, no2 * 1.25)), 1)
            cat = "Good" if aqi <= 50 else ("Satisfactory" if aqi <= 100 else ("Moderate" if aqi <= 200 else "Poor"))
            aq_rows.append({
                "observation_date": dt_str,
                "locality_code": loc["code"],
                "traffic_density_index": traffic_idx,
                "pm25": pm25,
                "pm10": pm10,
                "no2": no2,
                "o3": o3,
                "co_mg_m3": co,
                "aqi": aqi,
                "air_quality_category": cat,
            })
    aq_df = pd.DataFrame(aq_rows)
    aq_path = sample_dir / "sample_air_quality_observations.csv"
    aq_df.to_csv(aq_path, index=False)

    # 4. Rainfall & Waterlogging Observations CSV
    rain_rows = []
    for d in range(days):
        dt_str = (base_date + timedelta(days=d)).strftime("%Y-%m-%d")
        monsoon_pulse = 1.0 if (d % 14 in (0, 1, 2)) else 0.25
        for loc in SAMPLE_LOCATIONS[:3]:
            rain = round(float(max(0.0, rng.gamma(shape=1.8, scale=loc["rain_base"] * monsoon_pulse))), 2)
            soil = round(float(np.clip(38.0 + 0.55 * rain + rng.normal(0, 6.0), 15.0, 99.0)), 1)
            drain_cap = round(float(45.0 + 1.8 * loc["elevation_m"] + rng.normal(0, 3.0)), 1)
            imperv = round(float(78.0 - 1.2 * loc["elevation_m"]), 1)
            net_load = rain + 0.3 * soil - 0.5 * drain_cap
            wl_class = "High" if net_load >= 40 else ("Moderate" if net_load >= 15 else "Low")
            rain_rows.append({
                "observation_date": dt_str,
                "locality_code": loc["code"],
                "elevation_m": loc["elevation_m"],
                "rainfall_mm": rain,
                "soil_moisture_pct": soil,
                "drainage_capacity_mm_hr": drain_cap,
                "impervious_surface_pct": imperv,
                "waterlogging_risk_class": wl_class,
            })
    rain_df = pd.DataFrame(rain_rows)
    rain_path = sample_dir / "sample_rainfall_observations.csv"
    rain_df.to_csv(rain_path, index=False)

    # 5. Unified Environmental Indicators CSV
    env_rows = []
    for d in range(days):
        dt_str = (base_date + timedelta(days=d)).strftime("%Y-%m-%d")
        seasonal = 2.0 * np.sin(2 * np.pi * d / 40.0)
        for loc in SAMPLE_LOCATIONS:
            temp = round(float(loc["temp_base"] + seasonal + rng.normal(0, 1.2)), 2)
            rain = round(float(max(0.0, rng.exponential(scale=loc["rain_base"] * 0.45))), 2)
            if d in (18, 47, 73) and loc["code"] == "LOC-M3":
                rain = round(float(rng.uniform(78.0, 128.0)), 2)  # Monsoon storm spike
            hum = round(float(np.clip(68.0 + 0.25 * rain - 0.8 * (temp - 31) + rng.normal(0, 4.0), 42.0, 99.0)), 1)
            wind = round(float(np.clip(15.0 + rng.normal(0, 4.0), 3.0, 40.0)), 2)
            pm25 = round(float(np.clip(loc["pm25_base"] - 0.25 * rain + rng.normal(0, 8.0), 12.0, 148.0)), 2)
            pm10 = round(float(pm25 * 1.62 + rng.normal(0, 9.0)), 2)
            no2 = round(float(np.clip(loc["pm25_base"] * 0.78 + rng.normal(0, 6.0), 10.0, 110.0)), 2)
            aqi = round(float(max(pm25 * 2.05, pm10 * 1.08)), 1)
            wl_score = round(float(np.clip((rain * 1.15) + (100.0 - loc["elevation_m"] * 3.0) * 0.25, 0.0, 100.0)), 1)
            risk_cat = (
                "Critical" if (aqi > 250 or rain > 95 or temp > 39.5)
                else ("High" if (aqi > 160 or rain > 60 or temp > 36.5) else ("Moderate" if (aqi > 100 or rain > 30) else "Low"))
            )
            env_rows.append({
                "observation_date": dt_str,
                "locality_code": loc["code"],
                "zone_type": loc["zone_type"],
                "temperature_c": temp,
                "rainfall_mm": rain,
                "humidity_pct": hum,
                "wind_speed_kmh": wind,
                "pm25": pm25,
                "pm10": pm10,
                "no2": no2,
                "aqi": aqi,
                "waterlogging_risk_score": wl_score,
                "risk_category": risk_cat,
            })
    env_df = pd.DataFrame(env_rows)
    env_path = sample_dir / "sample_environmental_indicators.csv"
    env_df.to_csv(env_path, index=False)

    return {
        "Sample Weather Observations (Synthetic Benchmark)": str(weather_path),
        "Sample Air Quality Observations (Synthetic Benchmark)": str(aq_path),
        "Sample Rainfall & Drainage Observations (Synthetic Benchmark)": str(rain_path),
        "Sample Location Metadata Catalog (Transformed Reference)": str(loc_path),
        "Sample Unified Urban Environmental Indicators (Synthetic Benchmark)": str(env_path),
    }


def seed_initial_data(db: Session) -> Dict[str, Any]:
    """
    Idempotently seed the database with:
    - Default analyst & admin user accounts
    - Data sources with clear attribution
    - 5 sample CSV datasets + profiled columns
    - 5 monitored urban locations + historical observations
    - Pre-trained baseline ML models (Regression, Classification, Time-Series, Anomaly Detection)
    - Initial risk alerts and predictions
    """
    sample_files = generate_sample_csv_files()

    # Check if already seeded
    existing_ds = db.query(Dataset).filter(Dataset.source_type == "sample").count()
    if existing_ds > 0 and db.query(Location).count() > 0:
        return {"status": "already_seeded", "datasets": existing_ds}

    # 1. Seed Default Users
    demo_user = db.query(User).filter(User.email == "analyst@nagarnexus.org").first()
    if not demo_user:
        demo_user = User(
            full_name="Dr. Aarav Ramanathan",
            email="analyst@nagarnexus.org",
            password_hash=get_password_hash("NagarNexus@2026"),
            role="admin",
            organization="NagarNexus Urban Intelligence Center",
            preferred_city="Metro Coastal Belt",
        )
        db.add(demo_user)
        db.flush()

    # 2. Seed DataSource records
    src_sample = DataSource(
        source_name="NagarNexus Calibrated Synthetic Urban Benchmark Suite",
        source_url="https://open-meteo.com/ & https://openaq.org/ (Schema Reference)",
        source_type="sample_synthetic",
        attribution="Synthetic benchmark data modeled on coastal urban meteorology; not official municipal station records.",
    )
    src_meteo = DataSource(
        source_name="Open-Meteo Atmospheric Reanalysis & Weather API",
        source_url="https://open-meteo.com/",
        source_type="api",
        attribution="Weather data by Open-Meteo.com (CC BY 4.0)",
    )
    db.add_all([src_sample, src_meteo])
    db.flush()

    # 3. Seed Locations
    loc_by_code = {}
    for loc_info in SAMPLE_LOCATIONS:
        loc_obj = Location(
            name=loc_info["name"],
            city=loc_info["city"],
            state=loc_info["state"],
            country="India",
            latitude=loc_info["latitude"],
            longitude=loc_info["longitude"],
            geographical_resolution=loc_info["geographical_resolution"],
            elevation_m=loc_info["elevation_m"],
            zone_type=loc_info["zone_type"],
        )
        db.add(loc_obj)
        db.flush()
        loc_by_code[loc_info["code"]] = loc_obj

    # 4. Seed Sample Datasets & DatasetColumns
    created_datasets = {}
    for ds_title, f_path in sample_files.items():
        p = Path(f_path)
        df = pd.read_csv(p)
        prof = profile_dataframe(df)
        ds_rec = Dataset(
            user_id=demo_user.id,
            name=ds_title,
            description="Pre-integrated synthetic/transformed benchmark dataset (see datasets/sample/README.md)",
            file_path=str(p.resolve()),
            file_type="csv",
            file_size=p.stat().st_size,
            row_count=prof["row_count"],
            column_count=prof["column_count"],
            source_type="sample",
            is_public=True,
            quality_score=prof["data_quality"]["overall_score"],
            profile_json=prof,
            processing_status="ready",
        )
        db.add(ds_rec)
        db.flush()
        created_datasets[ds_title] = (ds_rec, df)

        for col_meta in prof["columns"]:
            db.add(
                DatasetColumn(
                    dataset_id=ds_rec.id,
                    column_name=col_meta["column_name"],
                    data_type=col_meta["data_type"],
                    raw_dtype=col_meta.get("raw_dtype"),
                    missing_count=col_meta["missing_count"],
                    unique_count=col_meta["unique_count"],
                    sample_values=col_meta.get("sample_values", []),
                )
            )

    # 5. Populate Observations table from Unified Environmental Indicators dataset
    env_ds, env_df = created_datasets["Sample Unified Urban Environmental Indicators (Synthetic Benchmark)"]
    obs_records = []
    indicator_units = {
        "temperature_c": "°C",
        "rainfall_mm": "mm",
        "humidity_pct": "%",
        "wind_speed_kmh": "km/h",
        "pm25": "µg/m³",
        "pm10": "µg/m³",
        "no2": "µg/m³",
        "aqi": "AQI",
    }
    # Take the last 30 days across all 5 locations for fast dashboard queries
    recent_env = env_df.tail(150)
    for _, row in recent_env.iterrows():
        loc_obj = loc_by_code.get(str(row["locality_code"]))
        if not loc_obj:
            continue
        obs_dt = datetime.strptime(str(row["observation_date"]), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        for ind_col, unit_str in indicator_units.items():
            obs_records.append(
                Observation(
                    location_id=loc_obj.id,
                    dataset_id=env_ds.id,
                    indicator=ind_col,
                    value=float(row[ind_col]),
                    unit=unit_str,
                    observed_at=obs_dt,
                    source_id=src_sample.id,
                )
            )
    db.bulk_save_objects(obs_records)
    db.flush()

    # 6. Train Baseline ML Models on Unified Environmental Dataset
    baseline_configs = [
        MLTrainRequest(
            dataset_id=env_ds.id,
            model_name="Urban Temperature Random Forest Regressor",
            algorithm="random_forest_regressor",
            feature_columns=["humidity_pct", "rainfall_mm", "wind_speed_kmh", "pm25"],
            target_column="temperature_c",
            test_size=0.2,
            n_estimators=60,
        ),
        MLTrainRequest(
            dataset_id=env_ds.id,
            model_name="PM2.5 Air Quality Chronological Forecaster",
            algorithm="time_series_lag_rf",
            feature_columns=["temperature_c", "humidity_pct", "wind_speed_kmh", "no2", "pm10"],
            target_column="pm25",
            chronological_split=True,
            date_column="observation_date",
            test_size=0.2,
            n_estimators=60,
        ),
        MLTrainRequest(
            dataset_id=env_ds.id,
            model_name="Urban Risk Category Random Forest Classifier",
            algorithm="random_forest_classifier",
            feature_columns=["temperature_c", "rainfall_mm", "humidity_pct", "pm25", "pm10", "no2"],
            target_column="risk_category",
            test_size=0.2,
            n_estimators=60,
        ),
    ]

    first_model_id = None
    for cfg in baseline_configs:
        trained = train_and_evaluate_model(env_df, cfg)
        m_rec = MLModel(
            user_id=demo_user.id,
            dataset_id=env_ds.id,
            model_name=trained["model_name"],
            model_type=trained["model_type"],
            algorithm=trained["algorithm"],
            model_version=trained["model_version"],
            feature_columns=trained["feature_columns"],
            target_column=trained["target_column"],
            metrics_json=trained["metrics"],
            model_path=trained["model_path"],
            is_public=1,
        )
        db.add(m_rec)
        db.flush()
        if first_model_id is None:
            first_model_id = m_rec.id

    # 7. Seed Initial Predictions & Risk Alerts
    if first_model_id:
        db.add(
            Prediction(
                model_id=first_model_id,
                user_id=demo_user.id,
                category="temperature",
                location_id=loc_by_code["LOC-M1"].id,
                input_json={"humidity_pct": 68.0, "rainfall_mm": 4.5, "wind_speed_kmh": 14.0, "pm25": 58.0},
                predicted_value="33.42",
                numeric_prediction=33.42,
                actual_value=33.10,
                confidence_metadata={"confidence_interval_95": [31.9, 34.9], "model_version": "1.0.0"},
            )
        )

    initial_alerts = [
        RiskAlert(
            location_id=loc_by_code["LOC-M1"].id,
            dataset_id=env_ds.id,
            risk_category="Fine Particulate Pollution (PM2.5)",
            indicator="pm25",
            risk_level="High",
            measured_value=84.6,
            threshold=60.0,
            unit="µg/m³",
            explanation="Measured PM2.5 (84.6 µg/m³) exceeds CPCB 24-hour reference threshold (60.0 µg/m³) along North Coastal Industrial Corridor.",
            suggested_action="Enforce industrial dust suppression and inspect freight corridor emissions.",
            data_source="Sample Unified Urban Environmental Indicators (Synthetic Benchmark)",
            threshold_type="CPCB 24-Hour NAAQS Reference",
        ),
        RiskAlert(
            location_id=loc_by_code["LOC-M3"].id,
            dataset_id=env_ds.id,
            risk_category="Potential Waterlogging Risk Indicator",
            indicator="rainfall_mm",
            risk_level="Critical",
            measured_value=112.4,
            threshold=64.5,
            unit="mm",
            explanation="Monsoon pulse rainfall of 112.4 mm in low-lying South IT & Wetland Basin (elevation 4.2m) exceeds heavy precipitation drainage threshold.",
            suggested_action="Pre-position stormwater pumps and monitor underpass water levels.",
            data_source="Sample Unified Urban Environmental Indicators (Synthetic Benchmark)",
            threshold_type="IMD Heavy Rainfall & Project Experimental Drainage Threshold",
        ),
        RiskAlert(
            location_id=loc_by_code["LOC-M2"].id,
            dataset_id=env_ds.id,
            risk_category="Urban Heat Stress",
            indicator="temperature_c",
            risk_level="Moderate",
            measured_value=36.4,
            threshold=35.0,
            unit="°C",
            explanation="Afternoon surface temperature (36.4 °C) exceeds urban thermal comfort threshold (35.0 °C).",
            suggested_action="Expand shaded transit waiting zones and monitor urban heat island hotspots.",
            data_source="Sample Unified Urban Environmental Indicators (Synthetic Benchmark)",
            threshold_type="Urban Microclimate Reference Threshold",
        ),
    ]
    db.add_all(initial_alerts)

    db.add(
        ActivityLog(
            user_id=demo_user.id,
            activity_type="SYSTEM_INIT",
            description="Initialized NagarNexus database with 5 sample datasets, 5 urban locations, and 3 pre-trained ML models.",
        )
    )
    db.commit()
    return {"status": "seeded", "datasets": len(created_datasets), "locations": len(loc_by_code)}

