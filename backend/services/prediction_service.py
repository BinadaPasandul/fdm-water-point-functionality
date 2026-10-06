"""Stateless inference through the single serialized production pipeline."""

import logging

import numpy as np
import pandas as pd

from backend.model_loader import LoadedModel
from backend.schemas import PredictionResult, WaterPointPredictionRequest, WaterPointPredictionResponse
from src.preprocessing.schema import RAW_PREDICTOR_COLUMNS, validate_raw_input_frame

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(self, loaded: LoadedModel):
        self.pipeline = loaded.pipeline
        self.metadata = loaded.metadata
        self.model_loaded = True
        self.model_version = self.metadata.get("serialization_timestamp_utc", "locked")[:10]

    def predict(self, request: WaterPointPredictionRequest) -> WaterPointPredictionResponse:
        values = request.model_dump()
        frame = pd.DataFrame([[values[column] for column in RAW_PREDICTOR_COLUMNS]],
                             columns=list(RAW_PREDICTOR_COLUMNS))
        # JSON null becomes Python None; represent it using pandas' missing marker
        # so the fitted imputers receive the same missing-value form as training.
        frame = frame.apply(lambda column: column.map(
            lambda value: np.nan if value is None else value
        ))
        frame = validate_raw_input_frame(frame)
        prediction_id = int(self.pipeline.predict(frame)[0])
        class_to_label = {int(key): value for key, value in self.metadata["id_to_class"].items()}
        if prediction_id not in class_to_label:
            raise RuntimeError("Model returned a class not declared in metadata.")

        classifier = self.pipeline.named_steps["classifier"]
        class_ids = [int(value) for value in classifier.classes_]
        probability_row = np.asarray(self.pipeline.predict_proba(frame)[0], dtype=float)
        if (len(probability_row) != 3 or len(class_ids) != 3 or
                not np.isfinite(probability_row).all() or
                np.any(probability_row < -1e-12) or np.any(probability_row > 1 + 1e-12) or
                not np.isclose(probability_row.sum(), 1.0, rtol=0, atol=1e-8)):
            raise RuntimeError("Model returned invalid class probabilities.")
        probabilities = {
            class_to_label[class_id]: float(probability)
            for class_id, probability in zip(class_ids, probability_row)
        }
        label = class_to_label[prediction_id]
        return WaterPointPredictionResponse(
            prediction=PredictionResult(
                class_id=prediction_id,
                label=label,
                confidence=float(max(probability_row)),
            ),
            probabilities=probabilities,
            model_version=self.model_version,
        )
