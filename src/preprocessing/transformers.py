"""Notebook-03 transformations required by the locked tree_base model."""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


ORDINAL_CATEGORY_ORDER = ["Inadequate", "Minimum", "Moderate", "Advanced", "Missing"]


class FixedDataCleaner(BaseEstimator, TransformerMixin):
    """Replace the survey's wc_savings_wp sentinel values within the pipeline."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        cleaned = X.copy()
        cleaned["wc_savings_wp"] = cleaned["wc_savings_wp"].replace(
            {999.0: np.nan, 888.0: np.nan}
        )
        return cleaned


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Preserve Notebook-03 always-derived fields and fold-fitted age edges."""

    def fit(self, X, y=None):
        wp_age_train = X["wp_age"].astype(float)
        self.wp_age_median_ = wp_age_train.median()
        wp_age_filled = wp_age_train.fillna(self.wp_age_median_)
        q1, q2 = wp_age_filled.quantile([1 / 3, 2 / 3])
        self.wp_age_edges_ = (float(q1), float(q2))
        return self

    def transform(self, X):
        X = X.copy()
        qtyhh_safe = X["qtyhh_wp"].replace(0, np.nan)
        X["people_per_household"] = X["qtypeople_wp"] / qtyhh_safe
        X["was_rehabilitated"] = X["rehabyn"].map({"Yes": 1, "No": 0})
        X["has_management_committee"] = (X["whomanage_wp"] == "Water committee").astype(int)
        X["rehab_age_missing"] = X["rehab_age"].isna().astype(int)
        X["rehab_age"] = X["rehab_age"].fillna(0)
        X["pop_1000_missing"] = X["pop_1000"].isna().astype(int)
        wp_age_filled = X["wp_age"].fillna(self.wp_age_median_)
        q1, q2 = self.wp_age_edges_
        X["wp_age_group"] = pd.cut(
            wp_age_filled,
            bins=[-np.inf, q1, q2, np.inf],
            labels=["New", "Established", "Old"],
        ).astype(str)
        return X


def remap_ordinal_missing_code(codes):
    """Map Notebook-03's ordinal Missing code (4) to -1."""
    return np.where(codes == 4, -1, codes)


def clean_wc_savings(X):
    """Compatibility helper; the final model uses FixedDataCleaner."""
    return FixedDataCleaner().transform(X)
