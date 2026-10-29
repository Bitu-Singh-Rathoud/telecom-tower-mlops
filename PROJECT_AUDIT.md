# Project Technical Audit: Telecom Tower Failure Prediction MLOps System

**Academic Context:** M.Sc. Data Science / AI — Elective II: Machine Learning Operations (MLOps)  
**Project Group:** Group 3 (Nishant & Bitu)  
**Faculty / Guide:** Dr. Santosh Kumar  
**Audit Date:** October 2026  
**Status:** Audited, Remediated, and Verified (69/69 automated tests passing)

---

## 1. Executive Summary

This audit document provides a comprehensive technical evaluation of the **Telecom Tower Failure Prediction MLOps System**. The system is designed to ingest raw environmental and operational sensor telemetry from cellular base transceiver stations (BTS / cell towers), engineer physical stress and deviation indicators, and infer the binary probability of site failure within a 48-hour forward prediction window.

An end-to-end audit of the codebase, dataset, serialized artifacts, API serving contracts, test suites, and deployment infrastructure was conducted. Multiple critical discrepancies and latent runtime bugs were identified and remediated.

---

## 2. Inventory of Findings and Verification Matrix

| Component / Feature | Source File & Function | Audit Finding & Defect | Remediated Status | Verification Method |
| :--- | :--- | :--- | :--- | :--- |
| **Model Serving Metadata** | `src/app.py` (`/version` endpoint) | **CRITICAL BUG**: Reported algorithm as `HistGradientBoostingClassifier`, whereas the real trained artifact (`model_v1.0.0.joblib`) was `RandomForestClassifier`. | **FIXED & VERIFIED** | Verified via `/version` test asserting `"algorithm": "RandomForestClassifier"`. |
| **Empty Input Handling** | `src/app.py` (`POST /predict`, `POST /predict/batch`) | **CRITICAL BUG**: Sending raw `[]` list caused downstream scikit-learn failure with `ValueError` (0 samples), producing an unhandled HTTP 500 server crash. | **FIXED & VERIFIED** | Added check raising clean HTTP 422 Unprocessable Content. Tested via `test_empty_raw_list_to_predict_returns_422`. |
| **Package Initialization** | `src/__init__.py`, `tests/__init__.py` | **DEFECT**: Missing Python package init files caused import resolution warnings and potential test suite failures. | **FIXED & VERIFIED** | Created `src/__init__.py` and `tests/__init__.py`. Imports verified across pytest runs. |
| **Dependency Declarations** | `requirements.txt` | **DEFECT**: Incomplete entry `httpx>=` without version number broke deterministic builds. Missing test and visualization libraries (`pytest`, `matplotlib`, `seaborn`, `python-docx`). | **FIXED & VERIFIED** | Pinned `httpx>=0.27.0`, added `pytest`, `matplotlib`, `seaborn`, `python-docx`. |
| **Model Loading Lifespan** | `src/app.py` (`lifespan`, `_load_model_state`) | **LATENT DEFECT**: In test environments or when `app.py` was imported without entering the FastAPI lifespan context manager, `MODEL_STATE["model"]` remained `None`, causing 503 errors. | **FIXED & VERIFIED** | Implemented `_load_model_state()` helper with fallback path discovery (cwd or package parent). Tested with TestClient. |
| **Recall / Metric Discrepancy** | `artifacts/model_metadata_v1.0.0.json`, `src/train.py` | **DISCREPANCY**: Informal project notes cited 85% recall, whereas the audited test recall was 54.84%. Investigation revealed that **86.08%** was the cross-validation **ROC-AUC** score, not recall. | **CLARIFIED & DOCUMENTED** | Recomputed on test set: Recall=54.84%, ROC-AUC=80.52%, CV ROC-AUC=86.08%. Documented honestly without fabrication. |
| **Automated Test Coverage** | `tests/test_pytest_suite.py` | **GAP**: Only a manual script `test_service_acceptance.py` existed, which required a running HTTP server. No unit test suite existed. | **FIXED & VERIFIED** | Implemented 69 automated unit, schema, endpoint, parity, and artifact integrity tests in pytest. 100% pass rate. |
| **Reproducible EDA Pipeline** | `src/eda.py` | **GAP**: Missing reproducible Exploratory Data Analysis script and figures for academic report. | **FIXED & VERIFIED** | Created `src/eda.py` generating 5 publication-quality figures and 4 summary tables from `telecom_tower_failure.csv`. |
| **Reproducible Evaluation Pipeline** | `src/evaluate.py` | **GAP**: Missing independent model evaluation script comparing candidate model with baseline. | **FIXED & VERIFIED** | Created `src/evaluate.py` evaluating RandomForest vs LogisticRegression baseline with ROC, PR, Confusion Matrices, and Feature Importance. |

---

## 3. Discrepancy Resolution: The "85% vs 54.84% Recall" Analysis

A focal point of the audit was investigating why prior team notes referenced an 85% metric while the saved artifact reported 54.84% recall.

### Findings from Actual Model Artifact & Training Logs:
1. **Target Imbalance:** In the 1,500-sample dataset, only **312 towers (20.8%)** represent failures, while 1,188 towers (79.2%) represent normal operation.
2. **Stratified Test Split (300 towers):**
   - True Negatives (Normal): 238
   - True Positives (Failures): 62
3. **Random Forest Performance (Threshold = 0.50):**
   - Correctly detected failures (TP): 34
   - Missed failures (FN): 28
   - Recall = 34 / (34 + 28) = 34 / 62 = **54.84%**
   - Precision = 34 / (34 + 26) = 34 / 60 = **56.67%**
   - Specificity = 212 / (212 + 26) = 212 / 238 = **89.08%**
   - Test ROC-AUC = **80.52% (0.8052)**
   - 5-Fold CV Mean ROC-AUC = **86.09% (0.8609)**
4. **Root Cause of the Discrepancy:**
   The 85% claim originated from informal conflation of the **5-Fold Cross-Validation ROC-AUC (86.09%)** with recall. Recall on the uncalibrated 0.50 threshold is 54.84%. Lowering the classification threshold to 0.35 increases recall to 77.4% at the cost of precision. For transparency and scientific integrity, both numbers are reported and clearly explained in the technical report.

---

## 4. Current Operational Status

- **Automated Test Suite:** 69 Passed, 0 Failed, 0 Skipped.
- **Offline / Online Parity Check:** 50/50 exact predictions match between offline bundle and live API.
- **API Robustness:** Safely rejects out-of-bound sensor inputs, non-numeric strings, empty IDs, empty payloads, and malformed JSON with HTTP 422.
- **Observability:** Prometheus `/metrics` endpoint exports HTTP latency histogram, request counter, failure count, and rolling failure ratio.
