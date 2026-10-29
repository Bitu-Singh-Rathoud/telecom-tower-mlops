"""
Comprehensive Pytest Test Suite — Telecom Tower Failure Prediction Service
Group 3: Nishant & Bitu
Course: Elective II: Machine Learning Operations (MLOps)
Faculty: Dr. Santosh Kumar

Tests cover:
 - Unit tests (features, schemas, model loading)
 - API integration tests (FastAPI TestClient — no live server needed)
 - Input validation: valid, invalid, edge cases, empty batch
 - Endpoint tests: /health, /version, /metrics, /predict, /predict/batch
 - Parity test: offline vs API predictions (50 samples)

Run:  pytest tests/test_pytest_suite.py -v
"""

import json
import os
import sys
import pytest
import numpy as np
import pandas as pd
import joblib
from fastapi.testclient import TestClient

# Ensure src is importable regardless of working directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app import app
from src.features import TowerFeatureTransformer, RAW_COLS, SENSOR_LIMITS
from src.schemas import TowerTelemetryInput, BatchTelemetryInput

# ---------------------------------------------------------------------------
# Shared client fixture
# ---------------------------------------------------------------------------
client = TestClient(app)

# Valid base telemetry record (all fields within bounds)
VALID_RECORD = {
    "Tower_ID": "TWR-09001",
    "Temperature_C": 45.0,
    "Battery_Voltage": 48.0,
    "Power_Consumption_W": 1200.0,
    "Signal_Strength_Percent": 75.0,
    "Fan_Speed_RPM": 3000.0,
    "Humidity_Percent": 60.0,
    "Traffic_Load": 800.0,
    "Tower_Age_Years": 5,
}


# ===========================================================================
# UNIT TESTS — TowerFeatureTransformer
# ===========================================================================

class TestTowerFeatureTransformer:
    """Unit tests for feature engineering logic."""

    def test_transformer_fit_on_dataframe(self):
        """Transformer must fit on a DataFrame without error."""
        df = pd.DataFrame([VALID_RECORD])
        t = TowerFeatureTransformer()
        t.fit(df[RAW_COLS])
        assert t.is_fitted is True

    def test_transformer_produces_correct_number_of_features(self):
        """Transformer must output 13 features (8 raw + 5 engineered)."""
        df = pd.DataFrame([VALID_RECORD])
        t = TowerFeatureTransformer()
        t.fit(df[RAW_COLS])
        out = t.transform(df[RAW_COLS])
        assert out.shape[1] == 13, f"Expected 13 features, got {out.shape[1]}"

    def test_transformer_imputes_missing_values(self):
        """Missing sensor values must be filled with training medians."""
        df_train = pd.DataFrame([VALID_RECORD] * 10)
        t = TowerFeatureTransformer()
        t.fit(df_train[RAW_COLS])

        # A record with all sensor values missing (only Tower_ID present)
        df_missing = pd.DataFrame([{"Tower_ID": "TWR-MISSING"}])
        for col in RAW_COLS:
            df_missing[col] = np.nan

        out = t.transform(df_missing[RAW_COLS])
        assert not out.isnull().any().any(), "Transformer left NaN values after imputation"

    def test_transformer_clips_out_of_range_values(self):
        """Values beyond sensor limits must be clipped to the boundary."""
        df_train = pd.DataFrame([VALID_RECORD] * 5)
        t = TowerFeatureTransformer()
        t.fit(df_train[RAW_COLS])

        # Temperature way above max 85°C
        df_extreme = pd.DataFrame([VALID_RECORD.copy()])
        df_extreme["Temperature_C"] = 999.0
        out = t.transform(df_extreme[RAW_COLS])
        max_temp = SENSOR_LIMITS["Temperature_C"][1]
        assert float(out["Temperature_C"].iloc[0]) == max_temp

    def test_unfitted_transformer_raises(self):
        """Transform without fit must raise RuntimeError."""
        t = TowerFeatureTransformer()
        df = pd.DataFrame([VALID_RECORD])
        with pytest.raises(RuntimeError):
            t.transform(df[RAW_COLS])

    def test_engineered_features_are_present(self):
        """All 5 engineered features must appear in transformer output."""
        df = pd.DataFrame([VALID_RECORD] * 3)
        t = TowerFeatureTransformer()
        t.fit(df[RAW_COLS])
        out = t.transform(df[RAW_COLS])
        for feat in ["Thermal_Stress_Ratio", "Power_Per_Traffic",
                     "Battery_Voltage_Dev48", "Heat_Humidity_Index", "Aging_Power_Stress"]:
            assert feat in out.columns, f"Engineered feature '{feat}' missing from output"

    def test_thermal_stress_ratio_formula(self):
        """Thermal_Stress_Ratio = Temperature_C / (Fan_Speed_RPM / 1000)."""
        row = VALID_RECORD.copy()
        row["Temperature_C"] = 60.0
        row["Fan_Speed_RPM"] = 3000.0
        expected = 60.0 / (3000.0 / 1000.0)  # = 20.0

        df = pd.DataFrame([row] * 5)
        t = TowerFeatureTransformer()
        t.fit(df[RAW_COLS])
        out = t.transform(df[RAW_COLS])
        assert abs(float(out["Thermal_Stress_Ratio"].iloc[0]) - expected) < 1e-6

    def test_battery_voltage_dev48_formula(self):
        """Battery_Voltage_Dev48 = |Battery_Voltage - 48.0|."""
        row = VALID_RECORD.copy()
        row["Battery_Voltage"] = 52.0
        expected = abs(52.0 - 48.0)  # = 4.0

        df = pd.DataFrame([row] * 5)
        t = TowerFeatureTransformer()
        t.fit(df[RAW_COLS])
        out = t.transform(df[RAW_COLS])
        assert abs(float(out["Battery_Voltage_Dev48"].iloc[0]) - expected) < 1e-6


# ===========================================================================
# UNIT TESTS — Pydantic Schemas
# ===========================================================================

class TestPydanticSchemas:
    """Unit tests for request/response schema validation."""

    def test_valid_full_record_accepted(self):
        """A fully specified valid record must parse without error."""
        rec = TowerTelemetryInput(**VALID_RECORD)
        assert rec.Tower_ID == "TWR-09001"

    def test_partial_record_with_nulls_accepted(self):
        """Records with some optional fields omitted must be accepted."""
        rec = TowerTelemetryInput(Tower_ID="TWR-PARTIAL")
        assert rec.Tower_ID == "TWR-PARTIAL"
        assert rec.Temperature_C is None

    def test_empty_tower_id_raises(self):
        """Whitespace-only Tower_ID must raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TowerTelemetryInput(Tower_ID="   ", Temperature_C=45.0)

    def test_temperature_above_max_raises(self):
        """Temperature_C > 85 must raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TowerTelemetryInput(Tower_ID="TWR-X", Temperature_C=250.0)

    def test_temperature_below_min_raises(self):
        """Temperature_C < -20 must raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TowerTelemetryInput(Tower_ID="TWR-X", Temperature_C=-50.0)

    def test_battery_voltage_below_min_raises(self):
        """Battery_Voltage < 20.0 must raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TowerTelemetryInput(Tower_ID="TWR-X", Battery_Voltage=10.0)

    def test_signal_strength_above_100_raises(self):
        """Signal_Strength_Percent > 100 must raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TowerTelemetryInput(Tower_ID="TWR-X", Signal_Strength_Percent=150.0)

    def test_batch_with_zero_towers_raises(self):
        """Empty towers list must raise ValidationError (min_length=1)."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            BatchTelemetryInput(towers=[])

    def test_batch_with_one_tower_accepted(self):
        """Batch with exactly one tower must be valid."""
        rec = TowerTelemetryInput(**VALID_RECORD)
        batch = BatchTelemetryInput(towers=[rec])
        assert len(batch.towers) == 1


# ===========================================================================
# API INTEGRATION TESTS — FastAPI TestClient
# ===========================================================================

class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_status_is_healthy(self):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "healthy"

    def test_health_model_is_loaded(self):
        resp = client.get("/health")
        data = resp.json()
        assert data["model_loaded"] is True

    def test_health_has_uptime(self):
        resp = client.get("/health")
        data = resp.json()
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0.0

    def test_health_has_version(self):
        resp = client.get("/health")
        data = resp.json()
        assert "version" in data
        assert data["version"] == "v1.0.0"


class TestVersionEndpoint:
    """Tests for GET /version."""

    def test_version_returns_200(self):
        resp = client.get("/version")
        assert resp.status_code == 200

    def test_version_has_correct_model_version(self):
        resp = client.get("/version")
        data = resp.json()
        assert data["model_version"] == "v1.0.0"

    def test_version_has_correct_algorithm(self):
        resp = client.get("/version")
        data = resp.json()
        assert data["algorithm"] == "RandomForestClassifier"

    def test_version_has_features_list(self):
        resp = client.get("/version")
        data = resp.json()
        assert isinstance(data["features"], list)
        assert len(data["features"]) == 13  # 8 raw + 5 engineered

    def test_version_has_threshold(self):
        resp = client.get("/version")
        data = resp.json()
        assert "threshold" in data
        assert 0.0 < data["threshold"] <= 1.0


class TestMetricsEndpoint:
    """Tests for GET /metrics (Prometheus)."""

    def test_metrics_returns_200(self):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_content_type_is_text(self):
        resp = client.get("/metrics")
        assert "text/plain" in resp.headers["content-type"]

    def test_metrics_contains_http_requests_counter(self):
        resp = client.get("/metrics")
        assert "http_requests_total" in resp.text

    def test_metrics_contains_latency_histogram(self):
        resp = client.get("/metrics")
        assert "http_request_duration_seconds" in resp.text

    def test_metrics_contains_predictions_counter(self):
        resp = client.get("/metrics")
        assert "tower_predictions_total" in resp.text


class TestPredictEndpoint:
    """Tests for POST /predict (single tower)."""

    def test_valid_single_predict_returns_200(self):
        resp = client.post("/predict", json=VALID_RECORD)
        assert resp.status_code == 200

    def test_valid_predict_response_has_required_fields(self):
        resp = client.post("/predict", json=VALID_RECORD)
        data = resp.json()
        assert "Tower_ID" in data
        assert "failure_probability" in data
        assert "predicted_failure_48h" in data
        assert "risk_level" in data
        assert "model_version" in data

    def test_valid_predict_tower_id_echoed_correctly(self):
        resp = client.post("/predict", json=VALID_RECORD)
        data = resp.json()
        assert data["Tower_ID"] == VALID_RECORD["Tower_ID"]

    def test_valid_predict_probability_in_range(self):
        resp = client.post("/predict", json=VALID_RECORD)
        data = resp.json()
        prob = data["failure_probability"]
        assert 0.0 <= prob <= 1.0

    def test_valid_predict_prediction_is_binary(self):
        resp = client.post("/predict", json=VALID_RECORD)
        data = resp.json()
        assert data["predicted_failure_48h"] in [0, 1]

    def test_valid_predict_risk_level_is_valid(self):
        resp = client.post("/predict", json=VALID_RECORD)
        data = resp.json()
        assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]

    def test_partial_record_with_nulls_returns_200(self):
        """A record with most sensors missing must still return a prediction."""
        resp = client.post("/predict", json={"Tower_ID": "TWR-NULL"})
        assert resp.status_code == 200

    def test_temperature_above_limit_returns_422(self):
        """Temperature_C = 250°C exceeds the 85°C maximum — must be rejected."""
        bad = VALID_RECORD.copy()
        bad["Temperature_C"] = 250.0
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_battery_below_limit_returns_422(self):
        """Battery_Voltage = 5V is below 20V minimum — must be rejected."""
        bad = VALID_RECORD.copy()
        bad["Battery_Voltage"] = 5.0
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_signal_above_limit_returns_422(self):
        """Signal_Strength_Percent = 150 exceeds 100 — must be rejected."""
        bad = VALID_RECORD.copy()
        bad["Signal_Strength_Percent"] = 150.0
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_fan_speed_below_limit_returns_422(self):
        """Fan_Speed_RPM = 100 is below 500 RPM minimum — must be rejected."""
        bad = VALID_RECORD.copy()
        bad["Fan_Speed_RPM"] = 100.0
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_non_numeric_sensor_returns_422(self):
        """String 'BLOWER_FAILED' in Fan_Speed_RPM must be rejected with 422."""
        bad = VALID_RECORD.copy()
        bad["Fan_Speed_RPM"] = "BLOWER_FAILED"
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_empty_tower_id_returns_422(self):
        """Empty/whitespace Tower_ID must be rejected with 422."""
        bad = VALID_RECORD.copy()
        bad["Tower_ID"] = "   "
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_missing_tower_id_returns_422(self):
        """Request without Tower_ID must be rejected with 422."""
        bad = {k: v for k, v in VALID_RECORD.items() if k != "Tower_ID"}
        resp = client.post("/predict", json=bad)
        assert resp.status_code == 422

    def test_malformed_json_returns_422(self):
        """Malformed JSON body must not crash the service."""
        resp = client.post(
            "/predict",
            content=b"{ not valid json }}",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_empty_body_returns_422(self):
        """Empty body must not crash the service."""
        resp = client.post(
            "/predict",
            content=b"",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_service_alive_after_invalid_inputs(self):
        """Service must remain healthy after receiving several invalid inputs."""
        # Send 5 invalid requests
        for _ in range(5):
            bad = VALID_RECORD.copy()
            bad["Temperature_C"] = 999.0
            client.post("/predict", json=bad)

        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestBatchPredictEndpoint:
    """Tests for POST /predict/batch."""

    def test_valid_single_item_batch_returns_200(self):
        payload = {"towers": [VALID_RECORD]}
        resp = client.post("/predict/batch", json=payload)
        assert resp.status_code == 200

    def test_valid_multi_item_batch_returns_200(self):
        payload = {"towers": [VALID_RECORD, VALID_RECORD, VALID_RECORD]}
        resp = client.post("/predict/batch", json=payload)
        assert resp.status_code == 200

    def test_batch_response_count_matches_input(self):
        payload = {"towers": [VALID_RECORD] * 5}
        resp = client.post("/predict/batch", json=payload)
        data = resp.json()
        assert data["count"] == 5
        assert len(data["predictions"]) == 5

    def test_batch_response_has_failures_predicted(self):
        payload = {"towers": [VALID_RECORD] * 3}
        resp = client.post("/predict/batch", json=payload)
        data = resp.json()
        assert "failures_predicted" in data
        assert 0 <= data["failures_predicted"] <= 3

    def test_empty_batch_returns_422(self):
        """Empty towers list must return HTTP 422 (min_length=1 constraint)."""
        payload = {"towers": []}
        resp = client.post("/predict/batch", json=payload)
        assert resp.status_code == 422

    def test_empty_raw_list_to_predict_returns_422(self):
        """Empty raw JSON list [] to /predict must return 422 and never 500."""
        resp = client.post("/predict", json=[])
        assert resp.status_code == 422
        assert resp.status_code != 500

    def test_batch_with_one_invalid_tower_returns_422(self):
        """Batch containing even one out-of-bounds record must be rejected."""
        bad = VALID_RECORD.copy()
        bad["Temperature_C"] = 999.0
        payload = {"towers": [VALID_RECORD, bad]}
        resp = client.post("/predict/batch", json=payload)
        assert resp.status_code == 422

    def test_batch_each_prediction_has_correct_fields(self):
        payload = {"towers": [VALID_RECORD, VALID_RECORD]}
        resp = client.post("/predict/batch", json=payload)
        data = resp.json()
        for pred in data["predictions"]:
            assert "Tower_ID" in pred
            assert "failure_probability" in pred
            assert "predicted_failure_48h" in pred
            assert "risk_level" in pred

    def test_batch_probabilities_all_in_range(self):
        payload = {"towers": [VALID_RECORD] * 10}
        resp = client.post("/predict/batch", json=payload)
        data = resp.json()
        for pred in data["predictions"]:
            assert 0.0 <= pred["failure_probability"] <= 1.0

    def test_batch_predictions_all_binary(self):
        payload = {"towers": [VALID_RECORD] * 10}
        resp = client.post("/predict/batch", json=payload)
        data = resp.json()
        for pred in data["predictions"]:
            assert pred["predicted_failure_48h"] in [0, 1]


# ===========================================================================
# PARITY TEST — Offline vs API (50 samples)
# ===========================================================================

class TestOfflineOnlineParity:
    """Verifies that the HTTP API returns identical predictions to offline model."""

    def test_50_sample_parity(self):
        """50 test rows from load_test_requests.csv must match offline scoring exactly."""
        # Load model bundle
        bundle_path = os.path.join(
            os.path.dirname(__file__), "..", "artifacts", "model_v1.0.0.joblib"
        )
        assert os.path.exists(bundle_path), f"Model bundle not found at: {bundle_path}"

        bundle = joblib.load(bundle_path)
        model = bundle["model"]
        transformer = bundle["transformer"]
        threshold = bundle["threshold"]

        # Load sample rows
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "load_test_requests.csv"
        )
        assert os.path.exists(csv_path), f"load_test_requests.csv not found at: {csv_path}"

        df_sample = pd.read_csv(csv_path).head(50)

        # Compute offline predictions
        X_tf = transformer.transform(df_sample)
        offline_probs = model.predict_proba(X_tf)[:, 1]
        offline_preds = (offline_probs >= threshold).astype(int).tolist()

        # Send to API via TestClient
        sample_records = df_sample.where(pd.notnull(df_sample), None).to_dict(orient="records")
        payload = {"towers": sample_records}
        resp = client.post("/predict/batch", json=payload)
        assert resp.status_code == 200, f"API returned {resp.status_code}: {resp.text}"

        data = resp.json()
        online_preds = [p["predicted_failure_48h"] for p in data["predictions"]]

        mismatches = [
            (i, offline_preds[i], online_preds[i])
            for i in range(50)
            if offline_preds[i] != online_preds[i]
        ]

        assert len(mismatches) == 0, (
            f"Offline vs API mismatch on {len(mismatches)}/50 rows: {mismatches[:5]}"
        )


# ===========================================================================
# MODEL ARTIFACT TESTS
# ===========================================================================

class TestModelArtifact:
    """Tests for model artifact integrity."""

    @pytest.fixture(scope="class")
    def bundle(self):
        path = os.path.join(
            os.path.dirname(__file__), "..", "artifacts", "model_v1.0.0.joblib"
        )
        assert os.path.exists(path), "Model artifact not found"
        return joblib.load(path)

    def test_bundle_has_model_key(self, bundle):
        assert "model" in bundle

    def test_bundle_has_transformer_key(self, bundle):
        assert "transformer" in bundle

    def test_bundle_has_threshold(self, bundle):
        assert "threshold" in bundle
        assert 0.0 < bundle["threshold"] <= 1.0

    def test_bundle_has_version(self, bundle):
        assert "version" in bundle
        assert bundle["version"] == "v1.0.0"

    def test_bundle_has_feature_names(self, bundle):
        assert "feature_names" in bundle
        assert len(bundle["feature_names"]) == 13

    def test_model_can_predict_proba(self, bundle):
        """Model must support predict_proba (required for threshold-based classification)."""
        model = bundle["model"]
        assert hasattr(model, "predict_proba")

    def test_model_is_random_forest(self, bundle):
        """Actual deployed model must be RandomForestClassifier (verify no mismatch)."""
        model = bundle["model"]
        assert "RandomForest" in type(model).__name__, (
            f"Expected RandomForestClassifier, got {type(model).__name__}"
        )

    def test_transformer_is_fitted(self, bundle):
        """Stored transformer must already be fitted (is_fitted flag set)."""
        transformer = bundle["transformer"]
        assert transformer.is_fitted is True

    def test_model_training_metrics_recorded(self, bundle):
        """Training metrics must be stored in the bundle."""
        assert "training_metrics" in bundle
        metrics = bundle["training_metrics"]
        assert "test_roc_auc" in metrics
        assert "test_recall" in metrics
        assert metrics["test_roc_auc"] > 0.5, "ROC-AUC below random baseline"


if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    raise SystemExit(result.returncode)
