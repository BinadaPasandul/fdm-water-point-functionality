"""Fail-closed loader for the immutable production inference artifact."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import joblib

# Register project transformers before loading the serialized sklearn pipeline.
import src.preprocessing  # noqa: F401
from src.preprocessing.schema import ID_TO_CLASS, RAW_PREDICTOR_COLUMNS

logger = logging.getLogger(__name__)


class ModelLoadError(RuntimeError):
    """The model or its metadata failed startup verification."""


class LoadedModel:
    def __init__(self, pipeline: Any, metadata: dict[str, Any]):
        self.pipeline = pipeline
        self.metadata = metadata


def load_production_model(model_path: Path, metadata_path: Path) -> LoadedModel:
    model_path, metadata_path = Path(model_path), Path(metadata_path)
    if not model_path.is_file():
        raise ModelLoadError("Required production model artifact is missing.")
    if not metadata_path.is_file():
        raise ModelLoadError("Required production model metadata is missing.")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelLoadError("Production model metadata could not be read.") from exc

    expected_hash = metadata.get("artifact_sha256")
    actual_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if not expected_hash or actual_hash != expected_hash:
        raise ModelLoadError("Production model checksum does not match metadata.")
    if metadata.get("artifact_filename") != model_path.name:
        raise ModelLoadError("Production model filename does not match metadata.")
    if metadata.get("raw_predictor_count") != len(RAW_PREDICTOR_COLUMNS):
        raise ModelLoadError("Metadata raw predictor count is not the expected 32.")
    if metadata.get("raw_predictor_names") != list(RAW_PREDICTOR_COLUMNS):
        raise ModelLoadError("Metadata raw predictor names do not match the project schema.")
    if metadata.get("class_mapping") != {label: key for key, label in ID_TO_CLASS.items()}:
        raise ModelLoadError("Metadata class mapping does not match the project schema.")
    if metadata.get("id_to_class") != {str(key): label for key, label in ID_TO_CLASS.items()}:
        raise ModelLoadError("Metadata ID-to-class mapping does not match the project schema.")

    try:
        pipeline = joblib.load(model_path)
    except Exception as exc:
        logger.exception("Production model artifact could not be deserialized")
        raise ModelLoadError("Production model artifact could not be loaded.") from exc
    classifier = getattr(pipeline, "named_steps", {}).get("classifier")
    if classifier is None or not hasattr(pipeline, "predict_proba"):
        raise ModelLoadError("Loaded artifact is not the expected probability-producing pipeline.")
    classes = [int(value) for value in classifier.classes_]
    expected_classes = [int(value) for value in metadata.get("classifier_class_order", [])]
    if classes != expected_classes or classes != list(ID_TO_CLASS):
        raise ModelLoadError("Loaded classifier class order is incompatible with metadata.")
    logger.info("Production model artifact checksum and metadata verified; model loaded")
    return LoadedModel(pipeline, metadata)
