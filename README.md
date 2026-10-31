# NAGARNEXUS – AI-Powered Hyperlocal Urban Intelligence and Prediction Platform

> **"Turning Urban Data Into Intelligent Decisions."**

NagarNexus is a full-stack Data Science, Machine Learning, and Geospatial Urban Intelligence platform built with **React (Vite + Tailwind CSS + Recharts + Leaflet)** on the frontend and **Python (FastAPI + SQLAlchemy + Pandas + SciPy + Statsmodels + Scikit-Learn + FPDF2)** on the backend.

---

## 1. Feature Implementation & Verification Status Matrix

| Module / Capability | Status | Implementation & Data Provenance Notes |
| :--- | :--- | :--- |
| **User Authentication & RBAC** | **Fully Implemented & Tested** | Bcrypt password hashing, JWT Bearer tokens, registration, login, profile update, password reset, and private dataset/report isolation (`403 Forbidden` across users). |
| **Overview Dashboard** | **Fully Implemented & Tested** | 6 database-driven KPI cards, 4 dynamic filters, 6 Recharts visualizations, recent activity logs, and latest prediction feed. |
| **Dataset Management & 12-Point Profiler** | **Fully Implemented & Tested** | Drag-and-drop CSV, XLSX, and XLS upload with MIME & binary header verification, automatic 12-point profiling, data quality score, preview, and download. |
| **Data Cleaning Engine** | **Fully Implemented & Tested** | Mean/median/mode/forward-fill/drop imputation, deduplication, IQR/Z-score outlier clipping/removal, MinMax/Z-score scaling, label/one-hot encoding, before/after comparison, and separate processed file storage. |
| **Automated EDA Engine** | **Fully Implemented & Tested** | Mean, median, mode, variance, std dev, quartiles, IQR, skewness, kurtosis, correlation & covariance matrices, plus dual interactive Recharts & downloadable high-DPI Matplotlib/Seaborn PNG plots. |
| **Statistical Analysis Module** | **Fully Implemented & Tested** | Descriptive stats, Shapiro-Wilk normality fit, Z-scores, Pearson/Spearman correlation, covariance, assumption-aware hypothesis testing (Welch $t$-test, Mann-Whitney $U$, ANOVA), Student-$t$ confidence intervals, and Statsmodels OLS trend analysis. |
| **Machine Learning Lab** | **Fully Implemented & Tested** | Leak-free `ColumnTransformer` + `Pipeline` for Linear/DecisionTree/RandomForest Regression, Logistic/DecisionTree/RandomForest Classification, K-Means Clustering (with Silhouette & 2D PCA), and Isolation Forest Anomaly Detection. |
| **Predictive Analytics** | **Fully Implemented & Tested** | Single-point inference and multi-step chronological horizon forecasting with 95% uncertainty intervals and prediction audit history. |
| **Location Intelligence & Comparison** | **Fully Implemented & Tested** | Interactive Leaflet + OpenStreetMap map, locality search, custom coordinate pinning, side-by-side multi-locality comparison, and explicit geographical resolution metadata. |
| **Urban Risk Detection & AI Insights** | **Fully Implemented & Tested** | Combines documented WHO/CPCB/IMD reference thresholds, project experimental statistical thresholds, waterlogging proxy detection, Isolation Forest anomalies, and evidence-backed plain-English insights. |
| **PDF & CSV Report Center** | **Fully Implemented & Tested** | Generates multi-section PDF dossiers (with embedded Matplotlib charts) and companion CSV exports. |
| **Sample Datasets (`datasets/sample/`)** | **Included & Clearly Labeled** | 5 synthetic/transformed benchmark CSV datasets (`weather`, `air_quality`, `rainfall`, `location_metadata`, `environmental_indicators`) with provenance `README.md`. Never misrepresented as official municipal station records. |
| **External Live APIs** | **Implemented with Offline Fallback** | Open-Meteo (`https://open-meteo.com/`) and OpenStreetMap Nominatim work without API keys when internet access is available; OpenAQ (`OPENAQ_API_KEY`) and optional LLM keys can be configured in `backend/.env`. Gracefully falls back to local DB telemetry when offline. |

---

## 2. Quickstart Commands (Windows PowerShell)

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

- **Default Demo Login**: `analyst@nagarnexus.org` / `NagarNexus@2026` (or click the **One-Click Demo Analyst Login** button on the sign-in screen).

---

## 3. Documentation Index

- [Architecture & Data Flow Specification](documentation/architecture.md)
- [Normalized Database Schema (12 Tables)](documentation/database_schema.md)
- [Complete REST API Reference](documentation/api_documentation.md)
- [Data Science & ML Workflow](documentation/data_science_workflow.md)
- [Installation, Execution, Testing & Troubleshooting Guide](documentation/installation.md)
- [Datasets Provenance & Dictionary](datasets/README.md)
- [Machine Learning Model Registry Guide](ml_models/README.md)

