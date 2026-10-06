"""Strict raw-input contract and nominal class labels for final inference."""

import pandas as pd


RAW_PREDICTOR_COLUMNS = (
    "country", "admin1", "latitude_wp", "longitude_wp", "elevation_wp", "cwfunded_wp",
    "wptype", "pumptype", "drillmethod", "piped_source", "piped_pump", "rehabyn",
    "qtyhh_wp", "whomanage_wp", "wp_age", "rehab_age", "qtypeople_wp",
    "lockedfullday_wp", "pumpstrokes", "wc_present_wp", "paytocollect_wp",
    "improved_wponly_wp", "qtyhh_c_wp", "wc_admin_index_wp", "wc_finance_index_wp",
    "wc_mgmt_index_wp", "wc_maint_index_wp", "wc_savings_wp", "wpqty_wp", "pop_1000",
    "annual_rain", "season",
)
CLASS_TO_ID = {
    "Functional": 0,
    "Partially functional": 1,
    "Abandoned or not functional": 2,
}
ID_TO_CLASS = {value: key for key, value in CLASS_TO_ID.items()}
TARGET_COLUMN = "functional3"


def validate_raw_input_frame(df):
    """Return canonical 32-column order; reject absent, duplicate or extra fields.

    Missing values inside the required columns pass to the fitted pipeline.
    Prediction IDs are nominal, and predict_proba follows classifier.classes_.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Inference input must be a pandas DataFrame")
    duplicates = df.columns[df.columns.duplicated()].tolist()
    if duplicates:
        raise ValueError(f"Duplicate input columns: {duplicates}")
    if TARGET_COLUMN in df.columns:
        raise ValueError(f"Target column {TARGET_COLUMN!r} is not an inference predictor")
    missing = [name for name in RAW_PREDICTOR_COLUMNS if name not in df.columns]
    extra = [name for name in df.columns if name not in RAW_PREDICTOR_COLUMNS]
    if missing:
        raise ValueError(f"Missing required predictor columns: {missing}")
    if extra:
        raise ValueError(f"Unexpected or leakage input columns: {extra}")
    return df.loc[:, list(RAW_PREDICTOR_COLUMNS)].copy()


def label_for_class_id(class_id):
    """Map a nominal class ID to its Notebook-05 display label."""
    return ID_TO_CLASS[int(class_id)]
