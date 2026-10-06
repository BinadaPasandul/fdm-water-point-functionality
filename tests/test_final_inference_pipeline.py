"""Focused software-contract tests for the locked development-only artifact."""

import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from src.modeling.final_pipeline import build_final_inference_pipeline
from src.preprocessing.schema import (
    ID_TO_CLASS,
    RAW_PREDICTOR_COLUMNS,
    validate_raw_input_frame,
)
from src.preprocessing.transformers import FixedDataCleaner


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def model_and_rows():
    model = joblib.load(ROOT / "models/final_inference_pipeline.joblib")
    rows = validate_raw_input_frame(pd.read_csv(
        ROOT / "data/processed/modern/X_train_raw.csv", nrows=3
    ))
    return model, rows


def test_builder_and_artifact_contract(model_and_rows):
    model, rows = model_and_rows
    built = build_final_inference_pipeline()
    assert list(built.named_steps) == ["preprocessing", "selection", "classifier"]
    assert model.named_steps["selection"].get_support().sum() == 60
    assert model.named_steps["classifier"].classes_.tolist() == [0, 1, 2]
    assert ID_TO_CLASS[1] == "Partially functional"
    assert len(RAW_PREDICTOR_COLUMNS) == rows.shape[1] == 32


def test_single_multiple_and_probability_order(model_and_rows):
    model, rows = model_and_rows
    assert model.predict(rows.iloc[[0]]).shape == (1,)
    assert model.predict(rows).shape == (3,)
    probabilities = model.predict_proba(rows)
    assert probabilities.shape == (3, 3)
    assert np.isfinite(probabilities).all()
    assert np.allclose(probabilities.sum(axis=1), 1, rtol=0, atol=1e-12)


def test_sentinels_match_missing_and_missing_values_work(model_and_rows):
    model, rows = model_and_rows
    samples = []
    for value in (999.0, 888.0, np.nan):
        sample = rows.iloc[[0]].copy()
        sample.loc[:, "wc_savings_wp"] = value
        samples.append(sample)
    for sample in samples[:2]:
        assert pd.isna(FixedDataCleaner().transform(sample)["wc_savings_wp"].iloc[0])
    assert np.array_equal(model.predict_proba(samples[0]), model.predict_proba(samples[1]))
    assert np.array_equal(model.predict_proba(samples[0]), model.predict_proba(samples[2]))
    numeric_missing = rows.iloc[[0]].copy()
    numeric_missing.loc[:, "elevation_wp"] = np.nan
    categorical_missing = rows.iloc[[0]].copy()
    categorical_missing.loc[:, "pumptype"] = np.nan
    unseen = rows.iloc[[0]].copy()
    unseen.loc[:, "pumptype"] = "UNSEEN_TEST_CATEGORY"
    for sample in (numeric_missing, categorical_missing, unseen):
        assert model.predict_proba(sample).shape == (1, 3)


def test_schema_rejections_and_column_order(model_and_rows):
    model, rows = model_and_rows
    with pytest.raises(ValueError, match="Missing required predictor"):
        validate_raw_input_frame(rows.drop(columns=["country"]))
    with pytest.raises(ValueError, match="Target column"):
        validate_raw_input_frame(rows.assign(functional3="Functional"))
    with pytest.raises(ValueError, match="Duplicate input columns"):
        validate_raw_input_frame(pd.concat([rows, rows[["country"]]], axis=1))
    with pytest.raises(ValueError, match="Unexpected or leakage"):
        validate_raw_input_frame(rows.assign(wateravailable="Yes"))
    with pytest.raises(TypeError, match="DataFrame"):
        validate_raw_input_frame(rows.to_dict("records"))
    canonical = validate_raw_input_frame(rows.iloc[:, ::-1])
    assert canonical.columns.tolist() == list(RAW_PREDICTOR_COLUMNS)
    assert np.array_equal(model.predict(canonical), model.predict(rows))


def test_fresh_process_verification(tmp_path):
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_final_model.py")],
        cwd=tmp_path, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((ROOT / "reports/model_export/export_verification.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
    assert report["backend_ready"] is True
