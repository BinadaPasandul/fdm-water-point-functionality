"""Importable reproduction of Notebook-03's locked tree_base preprocessor."""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, OrdinalEncoder

from .schema import RAW_PREDICTOR_COLUMNS
from .transformers import (
    ORDINAL_CATEGORY_ORDER,
    FeatureEngineer,
    FixedDataCleaner,
    remap_ordinal_missing_code,
)

# Keep this name for existing project imports.
RAW_PREDICTOR_COLS = list(RAW_PREDICTOR_COLUMNS)
CAT_NOT_APPLICABLE_COLS = ["pumptype", "drillmethod", "piped_source", "piped_pump"]
CAT_UNKNOWN_RAW_COLS = [
    "country", "admin1", "wptype", "whomanage_wp", "rehabyn", "season",
    "cwfunded_wp", "wc_present_wp", "paytocollect_wp", "lockedfullday_wp",
]
ORDINAL_COLS = [
    "wc_admin_index_wp", "wc_finance_index_wp", "wc_mgmt_index_wp", "wc_maint_index_wp",
]
NUM_LOG_CANDIDATES = ["wp_age", "qtypeople_wp", "qtyhh_wp", "pop_1000"]
NUM_OTHER = ["elevation_wp", "latitude_wp", "longitude_wp", "rehab_age"]
NUM_WITH_INDICATOR = [
    "annual_rain", "wpqty_wp", "qtyhh_c_wp", "improved_wponly_wp",
    "wc_savings_wp", "pumpstrokes",
]
SEMANTIC_FLAGS = ["rehab_age_missing", "pop_1000_missing"]


def build_tree_base_preprocessor(rare_min_frequency=10):
    """Build the exact no-log, no-scaling, base-feature tree preprocessing."""
    if not isinstance(rare_min_frequency, int) or rare_min_frequency < 1:
        raise ValueError("rare_min_frequency must be a positive integer")

    def categorical_branch(fill_value):
        return Pipeline([
            ("impute", SimpleImputer(strategy="constant", fill_value=fill_value)),
            ("onehot", OneHotEncoder(
                handle_unknown="infrequent_if_exist",
                min_frequency=rare_min_frequency,
                sparse_output=False,
            )),
        ])

    ordinal_branch = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="Missing")),
        ("ordinal", OrdinalEncoder(categories=[ORDINAL_CATEGORY_ORDER] * len(ORDINAL_COLS))),
        ("remap_missing", FunctionTransformer(
            remap_ordinal_missing_code, feature_names_out="one-to-one"
        )),
    ])
    preprocessor = ColumnTransformer([
        ("cat_not_applicable", categorical_branch("Not applicable"), CAT_NOT_APPLICABLE_COLS),
        ("cat_unknown", categorical_branch("Unknown"), CAT_UNKNOWN_RAW_COLS),
        ("ordinal_wc_index", ordinal_branch, ORDINAL_COLS),
        ("num_skew", Pipeline([("impute", SimpleImputer(strategy="median"))]), NUM_LOG_CANDIDATES),
        ("num_other", Pipeline([("impute", SimpleImputer(strategy="median"))]), NUM_OTHER),
        ("num_indicator", Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True))
        ]), NUM_WITH_INDICATOR),
        ("semantic_flags", "passthrough", SEMANTIC_FLAGS),
    ], remainder="drop", verbose_feature_names_out=True)
    preprocessor.set_output(transform="pandas")
    return Pipeline([
        ("fixed_cleaning", FixedDataCleaner()),
        ("feature_engineering", FeatureEngineer()),
        ("preprocessing", preprocessor),
    ])


def build_preprocessing_pipeline():
    """Compatibility name for the final tree_base preprocessing."""
    return build_tree_base_preprocessor()
