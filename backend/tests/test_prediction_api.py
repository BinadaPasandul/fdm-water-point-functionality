"""API contract, startup verification, evidence endpoints, and inference parity."""

import json

import pandas as pd
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.config import PROJECT_ROOT, Settings
from backend.main import app, create_app
from backend.model_loader import ModelLoadError, load_production_model
from backend.services.dashboard_service import DashboardAssetError, DashboardService
from src.preprocessing.schema import RAW_PREDICTOR_COLUMNS


VALID_REQUEST = {
    "country": "Nepal", "admin1": "Central", "latitude_wp": 27.04051,
    "longitude_wp": 86.29366, "elevation_wp": 811.7984, "cwfunded_wp": "Yes",
    "wptype": "Public tap / standpipe", "pumptype": None, "drillmethod": None,
    "piped_source": "Protected spring", "piped_pump": "Gravity Fed", "rehabyn": None,
    "qtyhh_wp": 2.0, "whomanage_wp": "Water committee", "wp_age": 1.0,
    "rehab_age": None, "qtypeople_wp": 11.0, "lockedfullday_wp": "No",
    "pumpstrokes": None, "wc_present_wp": None, "paytocollect_wp": None,
    "improved_wponly_wp": None, "qtyhh_c_wp": None, "wc_admin_index_wp": None,
    "wc_finance_index_wp": None, "wc_mgmt_index_wp": None, "wc_maint_index_wp": None,
    "wc_savings_wp": None, "wpqty_wp": None, "pop_1000": None,
    "annual_rain": None, "season": None,
}
CLASSES = ["Functional", "Partially functional", "Abandoned or not functional"]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_startup_loads_model_once_and_health_succeeds(monkeypatch):
    import backend.model_loader as loader_module

    original = loader_module.joblib.load
    calls = []

    def counted(path):
        calls.append(path)
        return original(path)

    monkeypatch.setattr(loader_module.joblib, "load", counted)
    test_app = create_app()
    with TestClient(test_app) as test_client:
        assert test_client.get("/health").json() == {"status": "ok", "model_loaded": True}
        assert test_client.get("/health").json()["model_loaded"] is True
    assert len(calls) == 1


def test_model_info_and_input_schema(client):
    info = client.get("/api/v1/model-info")
    assert info.status_code == 200
    assert info.json()["model_family"] == "Random Forest"
    assert info.json()["raw_predictor_count"] == 32
    assert info.json()["selected_feature_count"] == 60
    assert info.json()["target_classes"] == CLASSES

    schema = client.get("/api/v1/input-schema").json()
    assert schema["field_count"] == 32
    assert [field["name"] for field in schema["fields"]] == list(RAW_PREDICTOR_COLUMNS)
    assert all(field["required"] and field["nullable"] for field in schema["fields"])


def test_valid_prediction_has_labelled_probabilities(client):
    response = client.post("/api/v1/predict", json=VALID_REQUEST)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["prediction"]["class_id"] in (0, 1, 2)
    assert body["prediction"]["label"] in CLASSES
    probabilities = body["probabilities"]
    assert list(probabilities) == CLASSES
    assert all(0 <= value <= 1 for value in probabilities.values())
    assert sum(probabilities.values()) == pytest.approx(1.0, abs=1e-8)
    assert body["prediction"]["confidence"] == pytest.approx(max(probabilities.values()))


def test_direct_pipeline_api_parity(client):
    response = client.post("/api/v1/predict", json=VALID_REQUEST)
    assert response.status_code == 200, response.text
    service = app.state.prediction_service
    frame = pd.DataFrame([[VALID_REQUEST[name] for name in RAW_PREDICTOR_COLUMNS]],
                         columns=list(RAW_PREDICTOR_COLUMNS))
    frame = frame.apply(lambda column: column.map(lambda value: np.nan if value is None else value))
    direct_id = int(service.pipeline.predict(frame)[0])
    direct_probabilities = service.pipeline.predict_proba(frame)[0]
    metadata_labels = {int(key): value for key, value in service.metadata["id_to_class"].items()}
    api_body = response.json()
    assert api_body["prediction"]["class_id"] == direct_id
    assert api_body["prediction"]["label"] == metadata_labels[direct_id]
    assert [api_body["probabilities"][metadata_labels[class_id]] for class_id in
            service.pipeline.named_steps["classifier"].classes_] == pytest.approx(direct_probabilities, abs=1e-12)


@pytest.mark.parametrize("sentinel", [999, 888])
def test_savings_sentinel_values_are_passed_to_pipeline(client, sentinel):
    payload = {**VALID_REQUEST, "wc_savings_wp": sentinel}
    response = client.post("/api/v1/predict", json=payload)
    null_response = client.post("/api/v1/predict", json={**VALID_REQUEST, "wc_savings_wp": None})
    assert response.status_code == 200
    for label, probability in response.json()["probabilities"].items():
        assert probability == pytest.approx(null_response.json()["probabilities"][label], abs=1e-12)


def test_nullable_supported_values_and_unseen_category(client):
    payload = {**VALID_REQUEST, "annual_rain": None, "country": "Previously unseen region"}
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200, response.text


def test_invalid_numeric_type_is_rejected(client):
    response = client.post("/api/v1/predict", json={**VALID_REQUEST, "latitude_wp": "north"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_nonfinite_number_is_rejected(client):
    payload = {**VALID_REQUEST, "latitude_wp": float("nan")}
    response = client.post("/api/v1/predict", content=json.dumps(payload),
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 422


def test_missing_required_field_is_rejected(client):
    payload = {key: value for key, value in VALID_REQUEST.items() if key != "country"}
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422
    assert any(item["loc"][-1] == "country" for item in response.json()["error"]["details"])


def test_forbidden_target_and_extra_fields_are_rejected(client):
    for key in ("functional3", "wateravailable"):
        response = client.post("/api/v1/predict", json={**VALID_REQUEST, key: "Functional"})
        assert response.status_code == 422


def test_dashboard_endpoints_return_exported_evidence(client):
    summary = client.get("/api/v1/dashboard/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["dataset"]["rows"] == 1793
    assert body["dataset"]["countries"] == 9
    assert "development_cv" in body["final_model"]
    assert "historical_holdout" in body["final_model"]
    assert body["final_model"]["holdout_recomputed"] is False

    for endpoint, expected_key in [
        ("eda", "target_distribution"),
        ("model-performance", "final_confusion_matrix"),
        ("feature-importance", "raw_feature_importance"),
        ("robustness", "country_robustness"),
    ]:
        response = client.get(f"/api/v1/dashboard/{endpoint}")
        assert response.status_code == 200, response.text
        assert expected_key in response.json()


def test_dashboard_missing_asset_returns_clear_service_error(client, tmp_path):
    service = app.state.dashboard_service
    original_root = service.assets_root
    service.assets_root = tmp_path
    try:
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DASHBOARD_ASSET_UNAVAILABLE"
    finally:
        service.assets_root = original_root


def test_malformed_dashboard_json_raises_clear_error(tmp_path):
    target = tmp_path / DashboardService.SOURCES["dataset"]
    target.parent.mkdir(parents=True)
    target.write_text("{invalid", encoding="utf-8")
    service = DashboardService(tmp_path, {})
    with pytest.raises(DashboardAssetError):
        service._read("dataset")


def test_missing_model_or_checksum_mismatch_fails_closed(tmp_path):
    with pytest.raises(ModelLoadError, match="artifact is missing"):
        load_production_model(tmp_path / "missing.joblib", PROJECT_ROOT / "models/final_model_metadata.json")

    metadata = json.loads((PROJECT_ROOT / "models/final_model_metadata.json").read_text(encoding="utf-8"))
    metadata["artifact_sha256"] = "0" * 64
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ModelLoadError, match="checksum"):
        load_production_model(PROJECT_ROOT / "models/final_inference_pipeline.joblib", metadata_path)


def test_startup_failure_does_not_serve_without_model(tmp_path):
    settings = Settings.from_environment()
    missing = Settings(settings.title, settings.version, tmp_path / "missing.joblib",
                       settings.metadata_path, settings.dashboard_assets_path, settings.cors_origins)
    with pytest.raises(ModelLoadError):
        with TestClient(create_app(missing)):
            pass


def test_canonical_contract_rejects_duplicate_columns():
    from src.preprocessing.schema import validate_raw_input_frame

    frame = pd.DataFrame([[None] * 33], columns=[*RAW_PREDICTOR_COLUMNS, "country"])
    with pytest.raises(ValueError, match="Duplicate input columns"):
        validate_raw_input_frame(frame)
