"""Read-only access to the pre-exported dashboard JSON evidence."""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DashboardAssetError(RuntimeError):
    """A required exported dashboard asset is missing or malformed."""


class DashboardService:
    # Fixed server-side allowlist: clients cannot select arbitrary files.
    SOURCES = {
        "dataset": "data/eda/dataset_summary.json",
        "target_distribution": "data/eda/target_class_distribution.json",
        "missing_values": "data/eda/missing_values_top20.json",
        "functionality_by_country": "data/eda/functionality_by_country.json",
        "baseline_cv": "data/modelling/baseline_cv_summary.json",
        "ablation": "data/modelling/base_vs_engineered_ablation.json",
        "baseline_vs_optimized": "data/optimization/baseline_vs_optimized.json",
        "finalists_cv": "data/optimization/finalist_cv_summary.json",
        "partial_class": "data/optimization/finalist_partial_class_metrics.json",
        "final_metrics": "data/final_model/final_model_metrics.json",
        "final_class_metrics": "data/final_model/final_class_metrics.json",
        "final_confusion_matrix": "data/final_model/final_holdout_confusion_matrix.json",
        "raw_feature_importance": "data/robustness/raw_feature_permutation_importance.json",
        "selected_feature_importance": "data/robustness/selected_processed_feature_importance.json",
        "country_robustness": "data/robustness/country_robustness_locked_rf.json",
        "learning_curves": "data/robustness/learning_curve_diagnostics.json",
        "posthoc_comparison": "data/robustness/posthoc_comparison.json",
    }

    def __init__(self, assets_root: Path, model_metadata: dict[str, Any]):
        self.assets_root = Path(assets_root).resolve()
        self.model_metadata = model_metadata

    def _read(self, key: str) -> Any:
        relative = self.SOURCES[key]
        path = (self.assets_root / relative).resolve()
        if self.assets_root not in path.parents:
            raise DashboardAssetError("Dashboard asset path is outside the configured asset directory.")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.exception("Dashboard evidence asset unavailable: %s", relative)
            raise DashboardAssetError(f"Dashboard evidence asset is unavailable: {relative}") from exc

    def summary(self) -> dict[str, Any]:
        dataset = self._read("dataset")
        metrics = self._read("final_metrics")
        comparisons = {row["metric"]: row for row in metrics["cv_and_historical_holdout"]}
        return {
            "dataset": {
                "rows": dataset["rows"],
                "columns": dataset["columns"],
                "countries": len(self._read("functionality_by_country")["records"]),
                "target_class_counts": dataset["target_class_counts"],
            },
            "final_model": {
                "family": self.model_metadata["model_family"],
                "preprocessing_variant": self.model_metadata["preprocessing_variant"],
                "selected_feature_count": self.model_metadata["selected_processed_feature_count"],
                "development_cv": {
                    metric: comparisons[metric]["repeated_cv"]
                    for metric in ("macro_f1", "mcc", "accuracy")
                },
                "historical_holdout": {
                    metric: comparisons[metric]["holdout"]
                    for metric in ("macro_f1", "mcc", "accuracy")
                },
                "holdout_recomputed": False,
            },
        }

    def eda(self) -> dict[str, Any]:
        keys = ("dataset", "target_distribution", "missing_values", "functionality_by_country")
        return {key: self._read(key) for key in keys}

    def model_performance(self) -> dict[str, Any]:
        keys = ("baseline_cv", "ablation", "baseline_vs_optimized", "finalists_cv",
                "partial_class", "final_metrics", "final_class_metrics", "final_confusion_matrix")
        return {key: self._read(key) for key in keys}

    def feature_importance(self) -> dict[str, Any]:
        return {key: self._read(key) for key in ("raw_feature_importance", "selected_feature_importance")}

    def robustness(self) -> dict[str, Any]:
        return {key: self._read(key) for key in
                ("country_robustness", "learning_curves", "posthoc_comparison")}
