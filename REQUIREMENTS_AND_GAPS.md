# Requirements and Gap Analysis: Telecom Tower Failure Prediction MLOps

**Project Group:** Group 3 (Nishant & Bitu)  
**Academic Course:** Elective II: Machine Learning Operations (MLOps)  
**Faculty / Evaluator:** Dr. Santosh Kumar  
**Audit Status:** Remediated and Closed

---

## 1. Context & Motivation

The project was initially critiqued as being a *"code dump without a comprehensive project report and empirical verification"*. The objective of this gap analysis is to delineate the academic and engineering requirements for a postgraduate-level MLOps project, evaluate what was previously present, identify what was missing or broken, and document how each gap has been addressed.

---

## 2. Requirements Traceability Matrix

| Requirement Area | Specification / Acceptance Criteria | Initial State (Prior to Audit) | Remediated Current State | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01: Problem Definition & Data Provenance** | Clear definition of BTS failure, 48-hour forward prediction horizon, dataset profiling, and synthetic data risk analysis. | Brief description in README; no formal EDA or dataset provenance details. | Comprehensive EDA pipeline implemented (`src/eda.py`). 1,500 rows, 10 columns analyzed. Data limitations documented in report. | Figures `01` to `05` in `reports/figures/`, summary tables in `reports/tables/`. |
| **REQ-02: Preprocessing & Leakage Prevention** | Strictly fit feature scalers/imputers on training split; share identical logic between training and inference. | Transformer existed in `src/features.py`, but lacked automated unit tests. | Transformer verified via `tests/test_pytest_suite.py`. Model artifact bundles transformer with fitted medians. | Unit tests in `TestTowerFeatureTransformer` pass 100%. |
| **REQ-03: Model Training & Evaluation** | Reproducible training, stratified split, multi-metric evaluation (Recall, Precision, F1, ROC-AUC), comparison with baseline. | Model trained, but algorithm mismatch bug existed in `/version`. Metrics informally quoted as "85% recall". | Algorithm mismatch fixed. Evaluated RandomForest vs Logistic Regression baseline on held-out 300 test samples. | `reports/tables/model_comparison.csv`, `reports/results/metrics.json`, ROC/PR curves. |
| **REQ-04: API Engineering & Robustness** | Production REST service, single & batch inference, schema enforcement, zero crashes on malformed inputs (HTTP 422). | API existed (`src/app.py`), but empty `[]` request caused unhandled HTTP 500 error. | Added explicit check for empty lists returning HTTP 422. Out-of-bounds checks enforced via Pydantic. | 69 automated pytest cases pass, including `test_empty_raw_list_to_predict_returns_422`. |
| **REQ-05: Offline vs Online Prediction Parity** | 100% mathematical parity between offline scoring and API responses for identical telemetry inputs. | Informal claim of 50/50 parity without automated CI validation. | Automated parity test comparing offline `joblib` scoring against FastAPI test client for 50 records. | `TestOfflineOnlineParity::test_50_sample_parity` passes with 0 mismatches. |
| **REQ-06: Containerization & Reproducibility** | Functional Dockerfile, deterministic package installation, healthcheck probes, non-root user execution. | Dockerfile existed, but `requirements.txt` had invalid `httpx>=` syntax and lacked test dependencies. | Cleaned `requirements.txt`. Verified multi-stage Docker build and compose stack. | Clean package install verified. Docker compose stack with Prometheus and Grafana. |
| **REQ-07: Observability & Monitoring** | Prometheus metrics endpoint exporting request counts, latencies, failure predictions, and failure ratio gauge. | Endpoint existed, but unverified under full automated test suite. | Verified `/metrics` endpoint with 5 test cases testing metric presence and formatting. | `TestMetricsEndpoint` passes 100%. |
| **REQ-08: Academic Documentation** | Complete research-grade technical project report (DOCX/PDF) with verified figures, tables, math, and viva defense guide. | Critical gap: Professor noted project was a "code dump without report". | Generated 9-chapter formal Academic Technical Report (`.docx`) and 45-question Viva Guide (`.docx`). | Deliverables in `reports/`. |

---

## 3. Detailed Technical Defect Closure

### Defect 1: Algorithm Identifier Discrepancy
- **Location:** `src/app.py` line 317 (`/version` endpoint).
- **Issue:** The API returned `"algorithm": "HistGradientBoostingClassifier"`, while the actual serialized model in `artifacts/model_v1.0.0.joblib` was a `RandomForestClassifier`.
- **Resolution:** Updated `app.py` line 317 to return `"algorithm": "RandomForestClassifier"`. Added automated test `test_version_has_correct_algorithm` in pytest suite.

### Defect 2: HTTP 500 Server Error on Empty List Payload
- **Location:** `src/app.py` line 273 (`/predict` endpoint).
- **Issue:** Sending a raw JSON array `[]` was accepted by FastAPI as `List[TowerTelemetryInput]`, passed to `_score_records`, converted to an empty pandas DataFrame (0 rows), and passed to `RandomForestClassifier.predict_proba()`. Scikit-learn raised `ValueError: Found array with 0 sample(s)`, crashing the request handler with HTTP 500.
- **Resolution:** Added defensive input validation checking `if len(payload) == 0:` and returning a clean HTTP 422 Unprocessable Content error. Verified with automated test `test_empty_raw_list_to_predict_returns_422`.

### Defect 3: Lifespan Context Manager Isolation in Test Execution
- **Location:** `src/app.py` (`MODEL_STATE` global initialization).
- **Issue:** When importing `app` for testing with `fastapi.testclient.TestClient(app)` outside of a context manager, the FastAPI `lifespan` handler did not trigger, leaving `MODEL_STATE["model"]` as `None` and causing all valid requests to return HTTP 503.
- **Resolution:** Implemented `_load_model_state()` helper that lazily verifies and loads the artifact on first access if not already loaded by lifespan, supporting both local cwd and package relative path resolution.

### Defect 4: Metric Ambiguity (85% vs 54.84%)
- **Location:** Project documentation and viva records.
- **Issue:** Informal project documents claimed 85% recall, whereas model evaluation showed 54.84% recall at the standard 0.50 decision threshold.
- **Resolution:** Re-evaluated the model on the held-out test split (300 samples). Discovered that 86.08% was the 5-fold cross-validation ROC-AUC score, which had been conflated with recall. Documented exact metrics: Recall = 54.84%, Specificity = 89.08%, Precision = 56.67%, ROC-AUC = 80.52%, CV ROC-AUC = 86.08%.
