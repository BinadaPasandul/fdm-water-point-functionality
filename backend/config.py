"""Small environment-backed configuration with repository-relative defaults."""

from dataclasses import dataclass
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _path_setting(name: str, default: Path) -> Path:
    value = os.getenv(name)
    if not value:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


@dataclass(frozen=True)
class Settings:
    title: str
    version: str
    model_path: Path
    metadata_path: Path
    dashboard_assets_path: Path
    cors_origins: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "Settings":
        origins = os.getenv(
            "BACKEND_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501,http://127.0.0.1:8501",
        )
        return cls(
            title=os.getenv("BACKEND_API_TITLE", "Rural Water Point Functionality Prediction API"),
            version=os.getenv("BACKEND_API_VERSION", "1.0.0"),
            model_path=_path_setting(
                "BACKEND_MODEL_PATH", PROJECT_ROOT / "models/final_inference_pipeline.joblib"
            ),
            metadata_path=_path_setting(
                "BACKEND_MODEL_METADATA_PATH", PROJECT_ROOT / "models/final_model_metadata.json"
            ),
            dashboard_assets_path=_path_setting(
                "BACKEND_DASHBOARD_ASSETS_PATH", PROJECT_ROOT / "reports/dashboard_assets"
            ),
            cors_origins=tuple(origin.strip() for origin in origins.split(",") if origin.strip()),
        )
