# Repository Inventory: Telecom Tower Failure Prediction MLOps

**Repository:** `telecom-tower-mlops-fixed`  
**Group:** Group 3 (Nishant & Bitu)  
**Course:** Elective II: Machine Learning Operations (MLOps)  
**Date:** October 2026

---

## 1. Directory Tree Structure

```
telecom-tower-mlops-fixed/
├── artifacts/
│   ├── model_metadata_v1.0.0.json      # Serialized metadata & training metrics
│   └── model_v1.0.0.joblib             # Serialized bundle (Model + Transformer)
├── docs/
│   ├── demonstration_guide.md          # Viva & interactive demo instructions
│   ├── mlops_project_report.md         # Architecture & setup overview
│   ├── task1_linux_command_log.md      # Linux operational audit log
│   ├── task6_load_test_report.md       # Locust load test results
│   └── task8_capacity_alert_memo.md    # Alerting policy & capacity memo
├── monitoring/
│   ├── grafana/                        # Grafana provisioning & dashboard JSON
│   └── prometheus/                     # Prometheus scraping configuration (prometheus.yml)
├── reports/
│   ├── figures/                        # 10 generated PNG figures (EDA & evaluation)
│   ├── results/                        # metrics.json machine-readable results
│   ├── tables/                         # CSV and JSON summary tables
│   ├── EVIDENCE_INDEX.md               # Evidence index mapping claims to logs
│   ├── Telecom_Tower_MLOps_Technical_Report.docx  # Full Academic Technical Report
│   └── Telecom_Tower_MLOps_Viva_Guide.docx        # 45-Question Viva Preparation Guide
├── scripts/
│   ├── healthcheck_watchdog.sh         # Linux bash daemon for automated container recovery
│   └── telecom_logrotate.conf          # Systemd/logrotate log hygiene specification
├── src/
│   ├── __init__.py                     # Package initialization marker
│   ├── app.py                          # FastAPI serving engine & Prometheus instrumentation
│   ├── eda.py                          # Reproducible Exploratory Data Analysis pipeline
│   ├── evaluate.py                     # Independent model evaluation & baseline benchmark
│   ├── features.py                     # Shared domain cleaning & feature transformer
│   ├── schemas.py                      # Pydantic v2 input/output data contracts
│   └── train.py                        # Model training and artifact serialization script
├── static/
│   └── index.html                      # Interactive web operations console UI
├── tests/
│   ├── __init__.py                     # Test package initialization marker
│   ├── test_pytest_suite.py            # Comprehensive 69-case automated test suite
│   └── test_service_acceptance.py      # 50-sample offline/online parity test script
├── telecom_tower_failure.csv           # Primary dataset (1,500 records, 10 columns)
├── load_test_requests.csv              # 100 sample records for load testing & parity check
├── Dockerfile                          # Multi-stage production container specification
├── docker-compose.yml                  # Multi-service stack (App, Prometheus, Grafana)
├── render.yaml                         # Cloud deployment specification for Render.com
├── requirements.txt                    # Pinned Python package dependencies
└── README.md                           # Project onboarding, architecture, and quickstart guide
```

---

## 2. File-by-File Technical Specification

### A. Core Machine Learning & Application Source (`src/`)

1. **`src/app.py`**
   - **Role:** Production REST inference service built on FastAPI.
   - **Key Functions / Routes:**
     - `POST /predict`: Single tower, batch object, or list telemetry ingestion.
     - `POST /predict/batch`: Explicit batch endpoint enforcing `min_length=1`.
     - `GET /health`: Service liveness, model loading verification, and uptime seconds.
     - `GET /version`: Model version (`v1.0.0`), verified algorithm name (`RandomForestClassifier`), and feature names.
     - `GET /metrics`: Prometheus telemetry scraping exposition.
     - `_load_model_state()`: Safe model artifact resolver with cwd/parent fallback.
     - `_score_records()`: Batch scoring execution using identical `TowerFeatureTransformer`.
   - **Observability:** Custom Prometheus gauges and counters (`http_requests_total`, `http_request_duration_seconds`, `tower_predictions_total`, `tower_failure_prediction_ratio`, `service_uptime_seconds`).

2. **`src/features.py`**
   - **Role:** Shared data cleaning, domain validation, and feature engineering transformer.
   - **Class:** `TowerFeatureTransformer(BaseEstimator, TransformerMixin)`
   - **Input Features (8 Raw Sensors):**
     - `Temperature_C` [-20.0 to 85.0 °C]
     - `Battery_Voltage` [20.0 to 65.0 V]
     - `Power_Consumption_W` [50.0 to 3000.0 W]
     - `Signal_Strength_Percent` [0.0 to 100.0 %]
     - `Fan_Speed_RPM` [500.0 to 6000.0 RPM]
     - `Humidity_Percent` [0.0 to 100.0 %]
     - `Traffic_Load` [0.0 to 2000.0 active calls/data flows]
     - `Tower_Age_Years` [0.0 to 30.0 years]
   - **Engineered Domain Features (5 Features):**
     - `Thermal_Stress_Ratio`: `Temperature_C / (Fan_Speed_RPM / 1000.0)`
     - `Power_Per_Traffic`: `Power_Consumption_W / (Traffic_Load + 1.0)`
     - `Battery_Voltage_Dev48`: `abs(Battery_Voltage - 48.0)`
     - `Heat_Humidity_Index`: `Temperature_C * (Humidity_Percent / 100.0)`
     - `Aging_Power_Stress`: `(Power_Consumption_W / 1000.0) * Tower_Age_Years`

3. **`src/schemas.py`**
   - **Role:** Pydantic v2 schemas enforcing domain contracts at API boundaries.
   - **Models:**
     - `TowerTelemetryInput`: Validates sensor bounds, strips and validates `Tower_ID`.
     - `BatchTelemetryInput`: Validates list of towers with `min_length=1`.
     - `TowerPredictionOutput`: Structured inference result with probability and risk category (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
     - `BatchPredictionOutput`: Aggregated batch response with failure counts.
     - `HealthResponse`: Uptime and model status.
     - `VersionResponse`: Serving metadata.

4. **`src/train.py`**
   - **Role:** Offline model training and serialization pipeline.
   - **Split Strategy:** 80/20 Stratified train/test split (`random_state=42`).
   - **Algorithm:** `RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=4, class_weight='balanced', random_state=42)`.
   - **Cross-Validation:** 5-Fold Stratified K-Fold.
   - **Artifacts Emitted:** `artifacts/model_v1.0.0.joblib` and `artifacts/model_metadata_v1.0.0.json`.

5. **`src/eda.py`**
   - **Role:** Reproducible data profiling and visualization script.
   - **Outputs:** Target balance plot, missing value bar chart, distributions, correlation matrix, and boxplots by class.

6. **`src/evaluate.py`**
   - **Role:** Independent evaluation script assessing performance on held-out test data.
   - **Outputs:** Confusion matrices, ROC curves, PR curves, feature importance ranking, and comparison against Logistic Regression baseline.

---

### B. Automated Testing Suite (`tests/`)

1. **`tests/test_pytest_suite.py`** (69 Automated Tests)
   - Unit tests for transformer fitting, transformation, clipping, and imputation.
   - Pydantic schema validation tests for boundaries, non-numeric values, and empty strings.
   - API integration tests via `fastapi.testclient.TestClient`.
   - Rejection verification for malformed JSON, out-of-bounds readings, empty lists, and missing fields.
   - Parity verification for 50 rows between offline bundle and live API.
   - Model artifact integrity checks.

2. **`tests/test_service_acceptance.py`**
   - Live acceptance verification script against running server on port 8000.
