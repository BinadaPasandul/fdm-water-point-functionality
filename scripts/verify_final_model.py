"""Fresh-interpreter verification of the complete official inference artifact."""

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.modeling.final_pipeline import assert_final_pipeline_structure, load_locked_specification
from src.preprocessing.schema import RAW_PREDICTOR_COLUMNS, validate_raw_input_frame


MODEL_PATH = ROOT / "models/final_inference_pipeline.joblib"
METADATA_PATH = ROOT / "models/final_model_metadata.json"
REFERENCE_PATH = ROOT / "reports/model_export/serialization_reference.npz"
REPORT_PATH = ROOT / "reports/model_export/export_verification.json"


def verify():
    for path in (MODEL_PATH, METADATA_PATH, REFERENCE_PATH, REPORT_PATH):
        if not path.is_file():
            raise FileNotFoundError(f"Missing export file: {path}")
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    artifact_hash = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
    if artifact_hash != metadata["artifact_sha256"] or artifact_hash != report["artifact_sha256"]:
        raise AssertionError("Artifact checksum differs from metadata or report")
    lock_path = ROOT / metadata["source_lock_file"]
    if hashlib.sha256(lock_path.read_bytes()).hexdigest() != metadata["source_lock_sha256"]:
        raise AssertionError("Official lock checksum changed after export")
    current_versions = {
        "python": platform.python_version(), "numpy": np.__version__,
        "pandas": pd.__version__, "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }
    if current_versions != metadata["runtime_versions"]:
        raise AssertionError("Runtime versions differ from export environment")
    if metadata["raw_predictor_names"] != list(RAW_PREDICTOR_COLUMNS):
        raise AssertionError("Metadata raw predictor schema differs from project module")

    # This is intentionally a normal module import and joblib.load in a fresh process.
    pipeline = joblib.load(MODEL_PATH)
    lock = load_locked_specification(lock_path)
    assert_final_pipeline_structure(pipeline, lock, fitted=True)
    if pipeline.named_steps["selection"].get_support().sum() != lock["feature_selection_k"]:
        raise AssertionError("Loaded selector count differs from lock")
    transformed_names = pipeline.named_steps["preprocessing"].named_steps[
        "preprocessing"
    ].get_feature_names_out()
    selected_names = transformed_names[pipeline.named_steps["selection"].get_support()].tolist()
    if selected_names != metadata["selected_processed_feature_names"]:
        raise AssertionError("Loaded selected feature names differ from export metadata")
    if metadata["classifier_class_order"] != [0, 1, 2]:
        raise AssertionError("Metadata class order differs from nominal class mapping")
    for custom in (
        pipeline.named_steps["preprocessing"].named_steps["fixed_cleaning"],
        pipeline.named_steps["preprocessing"].named_steps["feature_engineering"],
    ):
        if custom.__class__.__module__ != "src.preprocessing.transformers":
            raise AssertionError("Artifact depends on a notebook-local custom transformer")

    # Only development features are loaded; no labels or final assessment files are needed.
    X = validate_raw_input_frame(pd.read_csv(ROOT / "data/processed/modern/X_train_raw.csv"))
    with np.load(REFERENCE_PATH, allow_pickle=False) as reference:
        pred_before = reference["predictions"]
        prob_before = reference["probabilities"]
    pred_after = pipeline.predict(X)
    prob_after = pipeline.predict_proba(X)
    if pred_before.shape != (1434,) or prob_before.shape != (1434, 3):
        raise AssertionError("Saved reference has invalid shapes")
    prediction_parity = bool(np.array_equal(pred_before, pred_after))
    probability_parity = bool(np.allclose(prob_before, prob_after, rtol=0, atol=1e-12))
    class_order_valid = bool(np.array_equal(pipeline.named_steps["classifier"].classes_, [0, 1, 2]))
    if not (prediction_parity and probability_parity and class_order_valid):
        raise AssertionError("Fresh-process predictions, probabilities or class order differ")
    if (not np.isfinite(prob_after).all() or
            not np.allclose(prob_after.sum(axis=1), 1, rtol=0, atol=1e-12)):
        raise AssertionError("Loaded model probabilities are invalid")
    one_row = pipeline.predict_proba(X.iloc[[0]])
    if one_row.shape != (1, 3):
        raise AssertionError("One-row inference failed")

    report.update({
        "status": "PASS", "fresh_process_load": True,
        "prediction_parity": prediction_parity,
        "probability_parity": probability_parity,
        "class_order_valid": class_order_valid,
        "prediction_parity_fraction": 1.0,
        "probability_rtol": 0, "probability_atol": 1e-12,
        "serialization_safe": True, "backend_ready": True,
        "holdout_access": False,
    })
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Fresh-process artifact load: PASS")
    print("Prediction parity: 100%; probability parity: PASS; class order: [0, 1, 2]")
    print("EXPORT-PHASE HOLDOUT ACCESS: NONE")
    print("MODEL SERIALIZATION: PASS")
    print("READY FOR BACKEND INTEGRATION: YES")


if __name__ == "__main__":
    try:
        verify()
    except Exception as exc:
        if REPORT_PATH.exists():
            report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
            report.update({"status": "FAIL", "fresh_process_load": False,
                           "serialization_safe": False, "backend_ready": False,
                           "verification_error": f"{type(exc).__name__}: {exc}"})
            REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        raise
