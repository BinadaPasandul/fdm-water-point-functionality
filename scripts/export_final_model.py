"""Export the official locked RF using development data only.

Run from any working directory with the project environment's Python.
This script never opens the final assessment split.
"""

import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.modeling.final_pipeline import (
    assert_final_pipeline_structure,
    build_final_inference_pipeline,
    load_locked_specification,
)
from src.preprocessing.pipeline import build_tree_base_preprocessor
from src.preprocessing.schema import (
    CLASS_TO_ID,
    ID_TO_CLASS,
    RAW_PREDICTOR_COLUMNS,
    label_for_class_id,
    validate_raw_input_frame,
)
from src.preprocessing.transformers import FixedDataCleaner


LOCK_PATH = ROOT / "reports/model_optimization/final_selection_locked.json"
METADATA_PATH = ROOT / "data/processed/modern/preprocessing_variants.json"
DATA_PATH = ROOT / "data/processed/modern"
MODEL_PATH = ROOT / "models/final_inference_pipeline.joblib"
MODEL_METADATA_PATH = ROOT / "models/final_model_metadata.json"
REPORT_DIR = ROOT / "reports/model_export"
REPORT_PATH = REPORT_DIR / "export_verification.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def authoritative_tree_width():
    """Read Notebook 05's explicit parity assertion without executing it."""
    notebook = json.loads((ROOT / "notebooks/05_model_optimization.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code")
    matches = re.findall(r"tree\.shape\s*==\s*\(1434,\s*(\d+)\)", source)
    if len(matches) != 1:
        raise AssertionError("Could not uniquely identify Notebook-05 tree_base width assertion")
    return int(matches[0])


def assert_schema_behaviors(pipeline, X):
    """Cheap inference-contract checks, with no model refit or CV."""
    row = X.iloc[[0]].copy()
    many = X.iloc[:3].copy()
    assert pipeline.predict(row).shape == (1,)
    assert pipeline.predict(many).shape == (3,)
    sentinel_probabilities = []
    for value in (999.0, 888.0, np.nan):
        sample = row.copy()
        sample.loc[:, "wc_savings_wp"] = value
        sentinel_probabilities.append(pipeline.predict_proba(sample))
    assert np.array_equal(sentinel_probabilities[0], sentinel_probabilities[1])
    assert np.array_equal(sentinel_probabilities[0], sentinel_probabilities[2])
    numeric_missing = row.copy()
    numeric_missing.loc[:, "elevation_wp"] = np.nan
    assert pipeline.predict(numeric_missing).shape == (1,)
    categorical_missing = row.copy()
    categorical_missing.loc[:, "pumptype"] = np.nan
    assert pipeline.predict(categorical_missing).shape == (1,)
    unseen = row.copy()
    unseen.loc[:, "pumptype"] = "UNSEEN_EXPORT_SMOKE_CATEGORY"
    assert pipeline.predict(unseen).shape == (1,)
    assert np.array_equal(pipeline.predict(validate_raw_input_frame(row.iloc[:, ::-1])), pipeline.predict(row))
    for bad, expected in [
        (row.drop(columns=["country"]), "Missing required predictor"),
        (row.assign(functional3="Functional"), "Target column"),
        (pd.concat([row, row[["country"]]], axis=1), "Duplicate input columns"),
        (row.assign(wateravailable="Yes"), "Unexpected or leakage"),
    ]:
        try:
            validate_raw_input_frame(bad)
        except ValueError as exc:
            assert expected in str(exc)
        else:
            raise AssertionError(f"Schema accepted invalid input: {expected}")
    assert label_for_class_id(1) == "Partially functional"
    return "PASS"


def export():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = load_locked_specification(LOCK_PATH)
    project_metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if project_metadata["raw_predictor_columns"] != list(RAW_PREDICTOR_COLUMNS):
        raise AssertionError("Raw predictor schema differs from authoritative metadata")
    variant = project_metadata["variants"]["tree_base"]
    if (variant["rare_min_frequency"] != lock["rare_min_frequency"] or
            variant["include_optional_engineered_features"] is not False or
            variant["use_log_transform"] is not False or
            variant["scale_numeric"] is not False):
        raise AssertionError("Metadata tree_base policy differs from lock")
    if lock["class_mapping"] != CLASS_TO_ID:
        raise AssertionError("Nominal target map differs from lock")

    # The only model data opened in the export phase.
    X = validate_raw_input_frame(pd.read_csv(DATA_PATH / "X_train_raw.csv"))
    y_text = pd.read_csv(DATA_PATH / "y_train.csv").iloc[:, 0]
    if X.shape != (lock["development_rows"], len(RAW_PREDICTOR_COLUMNS)):
        raise AssertionError("Development feature shape differs from lock")
    if len(y_text) != len(X) or set(y_text) != set(CLASS_TO_ID):
        raise AssertionError("Development labels differ from nominal class map")
    y = y_text.map(CLASS_TO_ID).astype(int)

    pre = build_tree_base_preprocessor(lock["rare_min_frequency"])
    transformed = pre.fit_transform(X)
    expected_width = authoritative_tree_width()
    names = pre.named_steps["preprocessing"].get_feature_names_out().tolist()
    if transformed.shape != (len(X), expected_width) or names != transformed.columns.tolist():
        raise AssertionError("Notebook-05 preprocessing width or feature names differ")
    if not np.isfinite(transformed.to_numpy(dtype=float)).all():
        raise AssertionError("Nonfinite values in tree_base output")
    clean_preview = FixedDataCleaner().transform(X)
    if clean_preview["wc_savings_wp"].isin([999, 888]).any():
        raise AssertionError("Survey sentinels remained after cleaning")
    print("PREPROCESSING PARITY: PASS")

    pipeline = build_final_inference_pipeline(LOCK_PATH)
    assert_final_pipeline_structure(pipeline, lock)
    pipeline.fit(X, y)
    assert_final_pipeline_structure(pipeline, lock, fitted=True)
    fitted_pre = pipeline.named_steps["preprocessing"]
    fitted_names = fitted_pre.named_steps["preprocessing"].get_feature_names_out().tolist()
    if fitted_names != names:
        raise AssertionError("Full pipeline preprocessing names differ from parity reference")
    fitted_matrix = fitted_pre.transform(X)
    if not np.array_equal(fitted_matrix.to_numpy(dtype=float), transformed.to_numpy(dtype=float)):
        raise AssertionError("Full pipeline preprocessing values differ from parity reference")
    mask = pipeline.named_steps["selection"].get_support()
    if len(mask) != expected_width or int(mask.sum()) != lock["feature_selection_k"]:
        raise AssertionError("Selected feature count differs from lock")
    selected_names = [name for name, selected in zip(names, mask) if selected]
    historical_selected = pd.read_csv(
        ROOT / "reports/posthoc_robustness/selected_processed_feature_importance.csv"
    )["selected_processed_feature"].tolist()
    if set(selected_names) != set(historical_selected):
        raise AssertionError("Full-development selected features differ from Notebook-06 result")

    pred_before = pipeline.predict(X)
    prob_before = pipeline.predict_proba(X)
    if pred_before.shape != (len(X),) or prob_before.shape != (len(X), 3):
        raise AssertionError("Development reference prediction shapes are invalid")
    if (not np.isfinite(prob_before).all() or
            not np.allclose(prob_before.sum(axis=1), 1, rtol=0, atol=1e-12)):
        raise AssertionError("Development reference probabilities are invalid")
    schema_status = assert_schema_behaviors(pipeline, X)

    pd.DataFrame({
        "index": range(len(names)), "feature_name": names, "selected": mask.astype(bool),
    }).to_csv(REPORT_DIR / "preprocessing_feature_names.csv", index=False)
    pd.DataFrame({
        "index": np.flatnonzero(mask), "feature_name": selected_names,
    }).to_csv(REPORT_DIR / "selected_features.csv", index=False)
    np.savez_compressed(REPORT_DIR / "serialization_reference.npz",
                        predictions=pred_before, probabilities=prob_before)

    temporary_path = MODEL_PATH.with_name(MODEL_PATH.name + ".exporting")
    try:
        joblib.dump(pipeline, temporary_path, compress=3)
        temporary_path.replace(MODEL_PATH)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    artifact_hash = sha256(MODEL_PATH)
    runtime = {
        "python": platform.python_version(), "numpy": np.__version__,
        "pandas": pd.__version__, "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }
    metadata = {
        "artifact_filename": MODEL_PATH.name,
        "artifact_sha256": artifact_hash,
        "project_name": "Predicting Rural Water Point Functionality Using Data Mining",
        "model_family": lock["model_family"],
        "rf_hyperparameters": lock["hyperparameters"],
        "random_state": 42,
        "preprocessing_variant": lock["preprocessing_variant"],
        "rare_min_frequency": lock["rare_min_frequency"],
        "feature_selection_method": "mutual_info_classif",
        "feature_selection_k": lock["feature_selection_k"],
        "imbalance_strategy": lock["imbalance_strategy"],
        "feature_set": lock["feature_set"],
        "raw_predictor_count": len(RAW_PREDICTOR_COLUMNS),
        "raw_predictor_names": list(RAW_PREDICTOR_COLUMNS),
        "preprocessing_feature_count": expected_width,
        "selected_processed_feature_count": len(selected_names),
        "selected_processed_feature_names": selected_names,
        "class_mapping": CLASS_TO_ID,
        "id_to_class": {str(k): value for k, value in ID_TO_CLASS.items()},
        "classifier_class_order": pipeline.named_steps["classifier"].classes_.tolist(),
        "training_row_count": len(X),
        "runtime_versions": runtime,
        "serialization_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_lock_file": str(LOCK_PATH.relative_to(ROOT)),
        "source_lock_sha256": sha256(LOCK_PATH),
        "inference_contract": {
            "input": "pandas DataFrame with exactly the 32 named raw predictors; missing values within columns allowed",
            "output": "nominal class ID from predict(); probabilities from predict_proba() in classifier_class_order",
            "label_lookup": "id_to_class",
        },
    }
    MODEL_METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "PENDING_FRESH_PROCESS_RELOAD", "holdout_access": False,
        "development_rows": len(X), "raw_predictor_count": len(RAW_PREDICTOR_COLUMNS),
        "preprocessing_parity": True, "preprocessing_feature_count": expected_width,
        "selected_feature_count": len(selected_names), "artifact_created": True,
        "artifact_sha256": artifact_hash, "artifact_bytes": MODEL_PATH.stat().st_size,
        "fresh_process_load": False, "prediction_parity": False,
        "probability_parity": False, "class_order_valid": True,
        "schema_tests": schema_status, "serialization_safe": False,
        "backend_ready": False,
        "source_lock_sha256": metadata["source_lock_sha256"],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Pipeline:", " -> ".join(pipeline.named_steps))
    print("Preprocessing:", " -> ".join(fitted_pre.named_steps))
    print("Feature selection:", len(selected_names), "of", expected_width)
    print("RF classes:", pipeline.named_steps["classifier"].classes_.tolist())
    print("Artifact SHA-256:", artifact_hash)
    print("EXPORT-PHASE HOLDOUT ACCESS: NONE")
    print("FINAL PRODUCTION PIPELINE: PASS; fresh-process verification pending")


if __name__ == "__main__":
    export()
