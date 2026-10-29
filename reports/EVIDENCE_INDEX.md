# Evidence Index: Telecom Tower Failure Prediction MLOps

This document maps every empirical claim in the project report and documentation to its corresponding reproducible code, test log, figure, or machine-readable artifact.

---

## 1. Empirical Evidence Mapping

| Claim / Metric | Value / Finding | Supporting Artifact / File | Verification Command | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Dataset Size & Columns** | 1,500 rows, 10 columns | `telecom_tower_failure.csv`, `reports/tables/dataset_summary.csv` | `python -m src.eda` | **Verified** |
| **Target Imbalance** | 312 Failures (20.8%), 1,188 Normal (79.2%) | `reports/figures/01_target_distribution.png`, `reports/tables/dataset_info.json` | `python -m src.eda` | **Verified** |
| **Missing Values** | 180 missing values across 8 numerical features | `reports/figures/02_missing_values.png`, `reports/tables/missing_values.csv` | `python -m src.eda` | **Verified** |
| **Test Set Size** | 300 rows (80/20 stratified split, seed 42) | `reports/results/metrics.json` | `python -m src.evaluate` | **Verified** |
| **Random Forest Test Accuracy** | 82.00% (246 / 300) | `reports/results/metrics.json`, `reports/tables/model_comparison.csv` | `python -m src.evaluate` | **Verified** |
| **Random Forest Test Recall** | 54.84% (34 / 62 true failures detected) | `reports/results/metrics.json`, `reports/tables/model_comparison.csv` | `python -m src.evaluate` | **Verified** |
| **Random Forest Test Precision** | 56.67% (34 / 60 failure alarms correct) | `reports/results/metrics.json`, `reports/tables/model_comparison.csv` | `python -m src.evaluate` | **Verified** |
| **Random Forest Specificity** | 89.08% (212 / 238 normal operations correct) | `reports/results/metrics.json`, `reports/tables/model_comparison.csv` | `python -m src.evaluate` | **Verified** |
| **Random Forest Test F1-Score** | 0.5574 | `reports/results/metrics.json`, `reports/tables/model_comparison.csv` | `python -m src.evaluate` | **Verified** |
| **Random Forest Test ROC-AUC** | 0.8052 | `reports/figures/08_roc_curves.png`, `reports/results/metrics.json` | `python -m src.evaluate` | **Verified** |
| **Random Forest Test PR-AUC** | 0.5880 | `reports/figures/09_pr_curves.png`, `reports/results/metrics.json` | `python -m src.evaluate` | **Verified** |
| **5-Fold CV Mean ROC-AUC** | 0.8609 (86.09%) | `artifacts/model_metadata_v1.0.0.json`, `src/train.py` | `python -m src.train` | **Verified** |
| **Baseline LR Accuracy** | 77.00% | `reports/tables/model_comparison.csv` | `python -m src.evaluate` | **Verified** |
| **Baseline LR Recall** | 67.74% | `reports/tables/model_comparison.csv` | `python -m src.evaluate` | **Verified** |
| **Baseline LR Precision** | 46.15% | `reports/tables/model_comparison.csv` | `python -m src.evaluate` | **Verified** |
| **Baseline LR ROC-AUC** | 0.8168 | `reports/figures/08_roc_curves.png`, `reports/results/metrics.json` | `python -m src.evaluate` | **Verified** |
| **Confusion Matrix (RF)** | TN=212, FP=26, FN=28, TP=34 | `reports/figures/06_confusion_matrix_rf.png` | `python -m src.evaluate` | **Verified** |
| **Confusion Matrix (LR)** | TN=189, FP=49, FN=20, TP=42 | `reports/figures/07_confusion_matrix_lr.png` | `python -m src.evaluate` | **Verified** |
| **Top Feature Importance** | `Battery_Voltage_Dev48`, `Thermal_Stress_Ratio`, `Temperature_C` | `reports/figures/10_feature_importance.png` | `python -m src.evaluate` | **Verified** |
| **Prediction Parity (50 rows)** | Exact 50/50 match between offline model & API | `tests/test_pytest_suite.py::TestOfflineOnlineParity` | `pytest tests/test_pytest_suite.py -k parity -v` | **Verified** |
| **HTTP 422 Rejection** | Rejects invalid temp, battery, empty ID, empty body, empty list | `tests/test_pytest_suite.py::TestPredictEndpoint` | `pytest tests/test_pytest_suite.py -v` | **Verified** |
| **Prometheus Metrics** | Exposes latency histogram, counters, failure gauge | `src/app.py`, `tests/test_pytest_suite.py::TestMetricsEndpoint` | `pytest tests/test_pytest_suite.py -k metrics -v` | **Verified** |
| **Test Suite Pass Rate** | 69 passed, 0 failed, 100% pass | Pytest execution log | `pytest tests/test_pytest_suite.py -v` | **Verified** |
