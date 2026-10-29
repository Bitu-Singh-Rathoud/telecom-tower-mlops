# Telecom Tower Failure Prediction Service: Production MLOps System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-v2+-blue.svg)](https://docs.docker.com/compose/)
[![Prometheus](https://img.shields.io/badge/Prometheus-v2.50+-orange.svg)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/Grafana-v10.3+-red.svg)](https://grafana.com)

**Course**: Elective II: Machine Learning Operations (MLOps)  
**Instructor**: Dr. Santosh Kumar  
**Group**: Group 3 — Nishant & Bitu  
**Syllabus Topics Covered**: 3 (Load Testing), 6 (Serving Deployment), 7 (Monitoring), 8 & 9 (Linux System Administration)

---

## 1. Quick Start (Single-Command Launch)

Deploy the entire production stack (Prediction Service + Prometheus + Grafana) with one command:

```bash
docker compose up -d --build
```

### Access URLs:
- **FastAPI Prediction Service**: [http://localhost:8000](http://localhost:8000)
- **API Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Metrics Engine**: [http://localhost:9090](http://localhost:9090)
- **Grafana Live Observability**: [http://localhost:3000](http://localhost:3000) *(User: `admin` / Password: `admin`)*

---

## 2. Repository Layout

```text
├── artifacts/
│   ├── model_v1.0.0.joblib            # Serialized model + shared transformer bundle
│   └── model_metadata_v1.0.0.json     # Feature schema, threshold & metrics metadata
├── docs/
│   ├── demonstration_guide.md         # 5-minute presentation script & viva defense
│   ├── mlops_project_report.md        # Comprehensive 4-page formal project report
│   ├── task1_linux_command_log.md     # 28 distinct Linux commands with justifications
│   ├── task6_load_test_report.md      # Before-and-after load testing & diagnosis
│   └── task8_capacity_alert_memo.md   # 1-page capacity & alert defense memo
├── load_testing/
│   ├── locustfile.py                  # Locust load test script
│   ├── run_load_test.py               # Pure Python multi-threaded benchmark suite
│   └── load_test_summary.csv          # Measured benchmark results
├── monitoring/
│   ├── grafana/
│   │   ├── dashboards/tower_operations.json
│   │   └── provisioning/              # Auto-provisioned datasource & dashboards
│   └── prometheus/
│       ├── alert_rules.yml            # Latency (150ms) and Error Rate (5%) alert rules
│       └── prometheus.yml             # Scrape config
├── scripts/
│   ├── healthcheck_watchdog.sh        # Self-healing watchdog with restart loop prevention
│   └── telecom_logrotate.conf         # Log rotation configuration
├── src/
│   ├── __init__.py
│   ├── app.py                         # FastAPI service with Prometheus instrumentation
│   ├── features.py                    # Shared feature engineering pipeline (Task 2 & Rule 7)
│   └── schemas.py                     # Strict Pydantic v2 domain schemas
├── tests/
│   └── test_service_acceptance.py     # Automated acceptance test suite (50-sample parity)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── telecom_tower_failure.csv
```

---

## 3. Verification & Acceptance Testing

Run the automated acceptance suite to verify 100% prediction parity and input contract enforcement:

```bash
python -m tests.test_service_acceptance
```

Expected output:
- `/health` and `/version` endpoints verified.
- **50 sample rows** from `load_test_requests.csv` verified to match offline model output with 100% parity.
- Sensor range violations (e.g. 250°C, <20V battery) safely rejected with `HTTP 422 Unprocessable Content` without server crash.

---

## 4. Running Load Tests (Task 6)

Execute multi-stage load scenarios (Baseline: 10 users, Peak: 100 users, Breaking Spike: 500 users):

```bash
python load_testing/run_load_test.py
```

---

## 5. Self-Healing & Crash Recovery (Task 7)

Demonstrate automated recovery when the service stops:

```bash
# 1. Simulate service failure
docker stop telecom_tower_service

# 2. Run the watchdog script
./scripts/healthcheck_watchdog.sh

# 3. View the timestamped recovery log
tail -n 10 /var/log/telecom_watchdog.log
```

---

## 6. Comprehensive Automated Test Suite (69 Tests)

Run the full pytest suite covering unit tests, schema boundaries, API endpoints, empty payload handling, 50-sample prediction parity, and model artifact integrity:

```bash
pytest tests/test_pytest_suite.py -v
```

All 69 tests pass with zero failures.

---

## 7. Academic Deliverables & Reports

This repository includes a complete, evidence-backed academic documentation package for postgraduate evaluation:

| Deliverable | File Path | Format & Details |
| :--- | :--- | :--- |
| **Academic Technical Report** | [`reports/Telecom_Tower_MLOps_Technical_Report.docx`](reports/Telecom_Tower_MLOps_Technical_Report.docx) | Full 9-Chapter formal report with embedded figures & tables |
| **Academic Technical Report (PDF)** | [`reports/Telecom_Tower_MLOps_Technical_Report.pdf`](reports/Telecom_Tower_MLOps_Technical_Report.pdf) | Print-ready PDF report |
| **Comprehensive Viva Guide** | [`reports/Telecom_Tower_MLOps_Viva_Guide.docx`](reports/Telecom_Tower_MLOps_Viva_Guide.docx) | 45 In-depth Q&As, 2-min pitch, 5-min walkthrough, trap defenses |
| **Comprehensive Viva Guide (PDF)** | [`reports/Telecom_Tower_MLOps_Viva_Guide.pdf`](reports/Telecom_Tower_MLOps_Viva_Guide.pdf) | Print-ready PDF viva guide |
| **Evidence Index** | [`reports/EVIDENCE_INDEX.md`](reports/EVIDENCE_INDEX.md) | Traceability matrix mapping claims to code and outputs |
| **Project Technical Audit** | [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md) | Complete component inventory and defect resolution log |
| **Repository Inventory** | [`REPOSITORY_INVENTORY.md`](REPOSITORY_INVENTORY.md) | File-by-file technical catalog |
| **Requirements & Gap Analysis** | [`REQUIREMENTS_AND_GAPS.md`](REQUIREMENTS_AND_GAPS.md) | Syllabus topic mapping and defect closure |
| **Changelog** | [`CHANGELOG.md`](CHANGELOG.md) | Chronological version history |

---

## 8. Reproducing Experiments & Regenerating Outputs

```bash
# 1. Run reproducible Exploratory Data Analysis (generates figures 01-05 and summary tables)
python -m src.eda

# 2. Run independent Model Evaluation (generates figures 06-10, ROC/PR curves, comparison CSV, and metrics.json)
python -m src.evaluate

# 3. Regenerate formal DOCX and PDF Academic Reports
python scripts/generate_all_reports.py
```

