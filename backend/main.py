"""FastAPI application for the locked rural water-point inference pipeline."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import Settings
from backend.model_loader import load_production_model
from backend.schemas import WaterPointPredictionRequest, WaterPointPredictionResponse
from backend.services.dashboard_service import DashboardAssetError, DashboardService
from backend.services.prediction_service import PredictionService
from src.preprocessing.schema import RAW_PREDICTOR_COLUMNS

logger = logging.getLogger(__name__)

FIELD_LABELS = {
    "country": "Country", "admin1": "Administrative Region", "latitude_wp": "Latitude",
    "longitude_wp": "Longitude", "elevation_wp": "Elevation", "cwfunded_wp": "Community Water Point Funding",
    "wptype": "Water Point Type", "pumptype": "Pump Type", "drillmethod": "Drilling Method",
    "piped_source": "Piped Water Source", "piped_pump": "Piped Water Delivery",
    "rehabyn": "Rehabilitated", "qtyhh_wp": "Households Served",
    "whomanage_wp": "Water Point Manager", "wp_age": "Water Point Age",
    "rehab_age": "Age at Rehabilitation", "qtypeople_wp": "People Served",
    "lockedfullday_wp": "Locked All Day", "pumpstrokes": "Pump Strokes",
    "wc_present_wp": "Water Committee Present", "paytocollect_wp": "Payment Collected",
    "improved_wponly_wp": "Improved Water Point Only", "qtyhh_c_wp": "Census Households",
    "wc_admin_index_wp": "Water Committee Administration Index",
    "wc_finance_index_wp": "Water Committee Finance Index",
    "wc_mgmt_index_wp": "Water Committee Management Index",
    "wc_maint_index_wp": "Water Committee Maintenance Index",
    "wc_savings_wp": "Water Committee Savings", "wpqty_wp": "Water Point Quantity",
    "pop_1000": "Population per 1,000", "annual_rain": "Annual Rainfall", "season": "Season",
}
CATEGORICAL_FIELDS = {
    "country", "admin1", "cwfunded_wp", "wptype", "pumptype", "drillmethod", "piped_source",
    "piped_pump", "rehabyn", "whomanage_wp", "lockedfullday_wp", "wc_present_wp",
    "paytocollect_wp", "wc_admin_index_wp", "wc_finance_index_wp", "wc_mgmt_index_wp",
    "wc_maint_index_wp", "season",
}


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings.from_environment()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Starting prediction API; verifying and loading locked model")
        try:
            loaded = load_production_model(config.model_path, config.metadata_path)
        except Exception:
            logger.exception("Prediction API startup failed during model verification")
            raise
        app.state.prediction_service = PredictionService(loaded)
        app.state.dashboard_service = DashboardService(config.dashboard_assets_path, loaded.metadata)
        yield
        app.state.prediction_service = None
        app.state.dashboard_service = None
        logger.info("Prediction API stopped")

    api = FastAPI(
        title=config.title,
        version=config.version,
        description="Stateless inference through the project's locked production pipeline.",
        lifespan=lifespan,
    )
    api.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @api.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [{
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg", "Invalid value"),
            "type": error.get("type", "value_error"),
        } for error in exc.errors()]
        return JSONResponse(status_code=422, content={"error": {
            "code": "VALIDATION_ERROR", "message": "Invalid prediction input.",
            "details": details,
        }})

    @api.exception_handler(DashboardAssetError)
    async def dashboard_asset_error_handler(_: Request, exc: DashboardAssetError) -> JSONResponse:
        logger.error("Dashboard evidence request failed: %s", exc)
        return JSONResponse(status_code=503, content={"error": {
            "code": "DASHBOARD_ASSET_UNAVAILABLE",
            "message": "Dashboard data is temporarily unavailable.",
        }})

    @api.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"service": config.title, "status": "running", "api_version": config.version}

    @api.get("/health", tags=["system"])
    def health(request: Request) -> dict[str, object]:
        loaded = getattr(request.app.state, "prediction_service", None)
        ready = loaded is not None and loaded.model_loaded
        return {"status": "ok" if ready else "unavailable", "model_loaded": bool(ready)}

    @api.post("/api/v1/predict", response_model=WaterPointPredictionResponse, tags=["prediction"])
    def predict(payload: WaterPointPredictionRequest, request: Request) -> WaterPointPredictionResponse:
        service = getattr(request.app.state, "prediction_service", None)
        if service is None or not service.model_loaded:
            return JSONResponse(status_code=503, content={"error": {
                "code": "MODEL_UNAVAILABLE", "message": "Prediction model is unavailable.",
            }})
        try:
            return service.predict(payload)
        except Exception as exc:
            logger.exception("Prediction inference failed")
            return JSONResponse(status_code=500, content={"error": {
                "code": "INFERENCE_ERROR", "message": "Prediction could not be generated.",
            }})

    @api.get("/api/v1/model-info", tags=["model"])
    def model_info(request: Request) -> dict[str, object]:
        service = request.app.state.prediction_service
        metadata = service.metadata
        return {
            "model_family": metadata["model_family"],
            "model_version": service.model_version,
            "raw_predictor_count": metadata["raw_predictor_count"],
            "selected_feature_count": metadata["selected_processed_feature_count"],
            "target_classes": [metadata["id_to_class"][str(class_id)]
                               for class_id in metadata["classifier_class_order"]],
            "preprocessing_variant": metadata["preprocessing_variant"],
            "feature_selection_k": metadata["feature_selection_k"],
            "imbalance_strategy": metadata["imbalance_strategy"],
        }

    @api.get("/api/v1/input-schema", tags=["prediction"])
    def input_schema() -> dict[str, object]:
        fields = []
        for name in RAW_PREDICTOR_COLUMNS:
            fields.append({
                "name": name,
                "label": FIELD_LABELS.get(name, name.replace("_", " ").title()),
                "type": "categorical" if name in CATEGORICAL_FIELDS else "number",
                "required": True,
                "nullable": True,
                "description": (
                    f"Raw model input: {name}. Unseen categorical values are accepted by the model pipeline."
                    if name in CATEGORICAL_FIELDS else f"Raw model input: {name}."
                ),
            })
        return {"field_count": len(fields), "fields": fields}

    def dashboard(request: Request) -> DashboardService:
        service = getattr(request.app.state, "dashboard_service", None)
        if service is None:
            raise DashboardAssetError("Dashboard data service is unavailable.")
        return service

    @api.get("/api/v1/dashboard/summary", tags=["dashboard"])
    def dashboard_summary(request: Request) -> dict[str, object]:
        return dashboard(request).summary()

    @api.get("/api/v1/dashboard/eda", tags=["dashboard"])
    def dashboard_eda(request: Request) -> dict[str, object]:
        return dashboard(request).eda()

    @api.get("/api/v1/dashboard/model-performance", tags=["dashboard"])
    def dashboard_model_performance(request: Request) -> dict[str, object]:
        return dashboard(request).model_performance()

    @api.get("/api/v1/dashboard/feature-importance", tags=["dashboard"])
    def dashboard_feature_importance(request: Request) -> dict[str, object]:
        return dashboard(request).feature_importance()

    @api.get("/api/v1/dashboard/robustness", tags=["dashboard"])
    def dashboard_robustness(request: Request) -> dict[str, object]:
        return dashboard(request).robustness()

    return api


app = create_app()
