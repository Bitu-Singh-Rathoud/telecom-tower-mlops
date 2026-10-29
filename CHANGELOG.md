# Project Changelog: Telecom Tower Failure Prediction MLOps

All notable changes, bug fixes, enhancements, and empirical validations made to this repository are documented in this file.

---

## [1.1.0] — October 2026 (Audit & Remediation Release)

### Added
- **`tests/test_pytest_suite.py`**: Created a comprehensive 69-case automated test suite covering:
  - Unit tests for `TowerFeatureTransformer` (imputation, clipping, ratio feature derivation).
  - Pydantic schema validation tests (boundary enforcement, type safety, empty string rejection).
  - FastAPI endpoint integration tests (`/health`, `/version`, `/metrics`, `/predict`, `/predict/batch`).
  - Input rejection tests for malformed JSON, out-of-range sensor readings, non-numeric values, and empty bodies (HTTP 422).
  - Mathematical parity check asserting 100% agreement between offline `joblib` scoring and live API output for 50 test samples.
  - Model bundle integrity and metadata consistency assertions.
- **`src/__init__.py` & `tests/__init__.py`**: Added Python package initialization files to enable clean relative and absolute imports across test runners.
- **`src/eda.py`**: Added reproducible Exploratory Data Analysis script generating 5 figures (`01_target_distribution.png`, `02_missing_values.png`, `03_feature_distributions.png`, `04_correlation_heatmap.png`, `05_boxplots_by_class.png`) and 4 data tables.
- **`src/evaluate.py`**: Added independent model evaluation pipeline computing confusion matrices, ROC-AUC, PR-AUC, accuracy, precision, recall, and specificity for both RandomForest and Logistic Regression baseline.
- **`PROJECT_AUDIT.md`**: Formal audit report detailing every codebase component, defect analysis, and resolution.
- **`REPOSITORY_INVENTORY.md`**: Complete inventory cataloging all files, modules, classes, and architectural roles.
- **`REQUIREMENTS_AND_GAPS.md`**: Requirements traceability matrix and defect closure documentation.
- **`reports/EVIDENCE_INDEX.md`**: Traceability index linking each project claim to measured empirical evidence.
- **`reports/Telecom_Tower_MLOps_Technical_Report.docx`**: Formal postgraduate-level Academic Technical Report (9 chapters, complete with diagrams, tables, and references).
- **`reports/Telecom_Tower_MLOps_Viva_Guide.docx`**: 45-question examiner viva defense guide with technical answers and project summaries.

### Changed
- **`src/app.py`**:
  - **Fixed Bug**: Corrected `/version` endpoint algorithm name from `"HistGradientBoostingClassifier"` to `"RandomForestClassifier"` to match the actual trained model bundle.
  - **Fixed Bug**: Added validation to `/predict` for raw empty list `[]` payloads to return HTTP 422 instead of crashing with HTTP 500.
  - **Fixed Bug**: Implemented lazy model loader `_load_model_state()` to allow safe execution in test environments where the ASGI lifespan context manager is not explicitly entered.
  - **Enhanced**: Added defensive check in `_score_records()` returning `[]` when an empty list is processed.
- **`requirements.txt`**:
  - Fixed incomplete version specifier `httpx>=` to `httpx>=0.27.0`.
  - Added required testing and visualization dependencies: `pytest>=8.0.0`, `pytest-asyncio>=0.23.0`, `matplotlib>=3.8.0`, `seaborn>=0.13.0`, `python-docx>=1.1.0`.

### Verified
- Automated test suite passed with 69/69 successful tests.
- Offline vs Online prediction parity verified on 50 samples with 0 mismatches.
- EDA and Evaluation pipelines executed cleanly and emitted all figures and machine-readable JSON metrics.
