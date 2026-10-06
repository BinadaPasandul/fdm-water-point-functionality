# Backend API

The API uses the locked serialized inference pipeline. It loads and verifies the model once at startup; prediction requests do not load project datasets or recreate preprocessing.

## Run locally

Install the project dependencies, then from the repository root:

```powershell
uvicorn backend.main:app --reload
```

Swagger UI: <http://127.0.0.1:8000/docs>  
Health: <http://127.0.0.1:8000/health>

## Main routes

- `POST /api/v1/predict` — one water point with all 32 required raw predictor names. Values may be `null` where supported by the production pipeline.
- `GET /api/v1/model-info` — safe model metadata.
- `GET /api/v1/input-schema` — frontend-friendly names, types, and nullability.
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/eda`
- `GET /api/v1/dashboard/model-performance`
- `GET /api/v1/dashboard/feature-importance`
- `GET /api/v1/dashboard/robustness`

Dashboard routes read exported JSON evidence only. The model path, metadata path, dashboard directory, CORS origins, API title, and version can be configured with `BACKEND_MODEL_PATH`, `BACKEND_MODEL_METADATA_PATH`, `BACKEND_DASHBOARD_ASSETS_PATH`, `BACKEND_CORS_ORIGINS`, `BACKEND_API_TITLE`, and `BACKEND_API_VERSION`. Relative paths resolve from the repository root.

## Example request

See [`examples/prediction_request.json`](examples/prediction_request.json). The categorical values are from a development example row; it contains all 32 predictor names. The API accepts new categorical values because the production encoder handles unknown values.

Illustrative response shape (placeholder values only; call the endpoint for a real result):

```json
{
  "prediction": {"class_id": 0, "label": "Functional", "confidence": 0.84},
  "probabilities": {
    "Functional": 0.84,
    "Partially functional": 0.10,
    "Abandoned or not functional": 0.06
  },
  "model_version": "2026-10-05"
}
```

The values above are placeholders, not an artifact prediction for the example request. `confidence` is the maximum model probability and is not presented as calibrated certainty.

## Tests

Run the focused API suite without holdout data:

```powershell
pytest backend/tests -q
```
