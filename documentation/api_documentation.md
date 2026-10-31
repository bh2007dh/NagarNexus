# NagarNexus REST API Documentation

Interactive Swagger UI is automatically served at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

## 1. Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new analyst account & receive JWT token | No |
| `POST` | `/api/auth/login` | Authenticate with email/password & receive JWT token | No |
| `GET` | `/api/auth/me` | Retrieve current authenticated user profile | Yes (Bearer) |
| `PUT` | `/api/auth/profile` | Update user full name, organization, or preferred city | Yes (Bearer) |
| `POST` | `/api/auth/reset-password` | Reset user password | No |

## 2. Dashboard (`/api/dashboard`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/dashboard/summary` | Retrieve KPIs, trend series, risk distribution, and available filters (`location_id`, `dataset_id`, `indicator`, `start_date`, `end_date`) |
| `GET` | `/api/dashboard/recent-activity` | Retrieve recent audit activity logs |

## 3. Dataset Management (`/api/datasets`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/datasets/upload` | Multipart upload for `.csv`, `.xlsx`, `.xls` with 12-point profiling |
| `GET` | `/api/datasets` | Paginated, searchable list of user & public sample datasets |
| `GET` | `/api/datasets/{id}` | Retrieve dataset metadata, quality breakdown, and column schema |
| `GET` | `/api/datasets/{id}/preview` | Preview rows (`?version=active\|original\|processed`) |
| `GET` | `/api/datasets/{id}/download` | Download original or cleaned dataset file |
| `DELETE` | `/api/datasets/{id}` | Delete private user-uploaded dataset |

## 4. Data Cleaning, EDA & Statistics

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/analysis/{id}/quality` | Retrieve data quality metrics for dataset `{id}` |
| `POST` | `/api/analysis/{id}/clean` | Execute imputation, deduplication, outlier handling, scaling, or encoding |
| `POST` | `/api/eda/{id}/run` | Run automated Exploratory Data Analysis |
| `GET` | `/api/eda/{id}/results` | Fetch latest EDA results for dataset `{id}` |
| `POST` | `/api/eda/{id}/visualization` | Generate interactive chart series + Matplotlib high-DPI PNG plot |
| `POST` | `/api/statistics/{id}/calculate` | Run 10-part statistical analysis and hypothesis testing |

## 5. Machine Learning & Predictive Analytics

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/ml/algorithms` | List supported regression, classification, clustering & anomaly algorithms |
| `POST` | `/api/ml/train` | Train, evaluate, and persist a leak-free scikit-learn model pipeline |
| `GET` | `/api/ml/models` | List trained models with evaluation metrics |
| `GET` | `/api/ml/models/{id}` | Get model details and validation series |
| `POST` | `/api/ml/models/{id}/predict` | Run single-instance inference with confidence intervals |
| `POST` | `/api/predictions/run` | Run category forecast and multi-step horizon projection |
| `GET` | `/api/predictions/history` | Retrieve historical predictions and actual-vs-predicted comparisons |

## 6. Locations, Risk, Comparison, Insights & Reports

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/locations/search` | Search monitored locations & optional OSM Nominatim geocoding |
| `POST` | `/api/locations` | Create a new monitored coordinate pin |
| `GET` | `/api/locations/{id}` | Retrieve location measurements, trends, risk alerts, and resolution metadata |
| `GET` | `/api/locations/{id}/observations` | Query raw observations for a location |
| `POST` | `/api/locations/{id}/live-weather` | Fetch live Open-Meteo & OpenAQ telemetry for location coordinates |
| `POST` | `/api/risk/analyze` | Run threshold + Isolation Forest urban risk scan |
| `GET` | `/api/risk/alerts` | List persisted urban risk alerts |
| `POST` | `/api/comparison/run` | Compare 2+ locations across environmental indicators |
| `POST` | `/api/insights/generate` | Generate evidence-backed insights and recommendations |
| `POST` | `/api/reports/generate` | Generate multi-section PDF report + companion CSV export |
| `GET` | `/api/reports` | List user's generated reports |
| `GET` | `/api/reports/{id}/download` | Download report (`?format=pdf\|csv`) |

