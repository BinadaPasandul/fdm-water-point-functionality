"""Complete raw-DataFrame-to-class pipeline for the official Notebook-05 RF."""

import json
from functools import partial
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.pipeline import Pipeline

from src.preprocessing.pipeline import build_tree_base_preprocessor
from src.preprocessing.schema import CLASS_TO_ID


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK_PATH = PROJECT_ROOT / "reports/model_optimization/final_selection_locked.json"
RANDOM_STATE = 42  # Notebook-05 fitting and mutual-information seed.


def load_locked_specification(lock_path=None):
    path = Path(lock_path) if lock_path is not None else DEFAULT_LOCK_PATH
    lock = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "model_family": "Random Forest",
        "preprocessing_variant": "tree_base",
        "imbalance_strategy": "none",
        "feature_set": "base",
        "class_mapping": CLASS_TO_ID,
    }
    for name, expected in required.items():
        if lock.get(name) != expected:
            raise ValueError(f"Locked {name} differs from the official configuration")
    if lock.get("feature_selection_k") != 60:
        raise ValueError("Official feature-selection count must be 60")
    if lock.get("rare_min_frequency") != 10:
        raise ValueError("Official rare-category threshold must be 10")
    if lock.get("development_rows") != 1434:
        raise ValueError("Official development row count must be 1434")
    if not isinstance(lock.get("hyperparameters"), dict):
        raise ValueError("Lock must provide RF hyperparameters")
    return lock


def build_final_inference_pipeline(lock_path=None):
    """Construct the unfitted official pipeline; all settings come from the lock."""
    lock = load_locked_specification(lock_path)
    preprocessor = build_tree_base_preprocessor(lock["rare_min_frequency"])
    selector = SelectKBest(
        partial(mutual_info_classif, random_state=RANDOM_STATE),
        k=lock["feature_selection_k"],
    )
    classifier = RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=2,
        **lock["hyperparameters"],
    )
    for key, expected in lock["hyperparameters"].items():
        if classifier.get_params()[key] != expected:
            raise AssertionError(f"RF parameter {key} does not match lock")
    if classifier.class_weight is not None:
        raise AssertionError("Official RF must not use class weighting")
    return Pipeline([
        ("preprocessing", preprocessor),
        ("selection", selector),
        ("classifier", classifier),
    ])


def assert_final_pipeline_structure(pipeline, lock, fitted=False):
    """Fail closed if the serialized artifact departs from the official design."""
    if list(pipeline.named_steps) != ["preprocessing", "selection", "classifier"]:
        raise AssertionError("Unexpected final pipeline steps")
    pre = pipeline.named_steps["preprocessing"]
    if list(pre.named_steps) != ["fixed_cleaning", "feature_engineering", "preprocessing"]:
        raise AssertionError("Unexpected preprocessing steps")
    if pre.named_steps["fixed_cleaning"].__class__.__module__ != "src.preprocessing.transformers":
        raise AssertionError("Cleaner is not importable from project module")
    if pre.named_steps["feature_engineering"].__class__.__module__ != "src.preprocessing.transformers":
        raise AssertionError("FeatureEngineer is not importable from project module")
    selector = pipeline.named_steps["selection"]
    classifier = pipeline.named_steps["classifier"]
    if not isinstance(selector, SelectKBest) or selector.k != lock["feature_selection_k"]:
        raise AssertionError("Feature selection differs from lock")
    if not isinstance(classifier, RandomForestClassifier):
        raise AssertionError("Final classifier is not RandomForestClassifier")
    for key, expected in lock["hyperparameters"].items():
        if classifier.get_params()[key] != expected:
            raise AssertionError(f"RF parameter {key} differs from lock")
    if classifier.get_params()["random_state"] != RANDOM_STATE or classifier.class_weight is not None:
        raise AssertionError("RF random state or imbalance policy differs")
    ct = pre.named_steps["preprocessing"]
    for name in ("cat_not_applicable", "cat_unknown"):
        branch = (ct.named_transformers_[name] if fitted else
                  next(transformer for branch_name, transformer, _ in ct.transformers
                       if branch_name == name))
        onehot = branch.named_steps["onehot"]
        if onehot.min_frequency != lock["rare_min_frequency"]:
            raise AssertionError("Rare-category threshold differs from lock")
    if fitted and not np.array_equal(classifier.classes_, np.array([0, 1, 2])):
        raise AssertionError("Classifier class order differs from nominal class mapping")
