"""Recover and render reusable report/dashboard assets from existing evidence.

This script may read the raw workbook for Notebook-02 descriptive EDA. It never
opens either processed holdout file and never fits or predicts with a model.
"""

from __future__ import annotations

import ast
import gc
import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import confusion_matrix, precision_recall_curve, average_precision_score


ASSET_ROOT = ROOT / "reports/dashboard_assets"
FIG = {name: ASSET_ROOT / "figures" / name for name in
       ["eda", "modelling", "optimization", "robustness", "final_model"]}
DATA = {name: ASSET_ROOT / "data" / name for name in
        ["eda", "modelling", "optimization", "robustness", "final_model"]}
CLASS_ORDER = ["Functional", "Partially functional", "Abandoned or not functional"]
CLASS_COLORS = ["#4C72B0", "#DD8452", "#C44E52"]
MODEL_COLORS = ["#277DA1", "#43AA8B", "#F8961E", "#F94144", "#8E6C9F", "#577590"]
MANIFEST: list[dict] = []
PROTECTED = [
    "notebooks/02_eda.ipynb", "notebooks/03_preprocessing.ipynb",
    "notebooks/04_model_development.ipynb", "notebooks/05_model_optimization.ipynb",
    "notebooks/06_posthoc_robustness.ipynb", "notebooks/06b_posthoc_robustness.ipynb",
    "reports/model_optimization/final_selection_locked.json",
    "models/final_inference_pipeline.joblib",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str | None]:
    return {name: sha256(ROOT / name) if (ROOT / name).is_file() else None for name in PROTECTED}


def notebook(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def notebook_cell(path: str, index: int) -> dict:
    return notebook(path)["cells"][index]


def notebook_assignment(path: str, variable: str):
    """Read a literal assignment from notebook source without executing code."""
    nb = notebook(path)
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        tree = ast.parse("".join(cell["source"]))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == variable for target in node.targets
            ):
                try:
                    return ast.literal_eval(node.value)
                except Exception:
                    continue
    raise KeyError(f"Could not find literal {variable!r} in {path}")


def json_ready(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if pd.isna(value) if not isinstance(value, (list, dict, tuple)) else False:
        return None
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(v) for v in value]
    return value


def write_table(frame: pd.DataFrame, rel_csv: str, rel_json: str | None = None,
                metadata: dict | None = None):
    csv_path = ASSET_ROOT / rel_csv
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv_path, index=False)
    json_path = None
    if rel_json:
        json_path = ASSET_ROOT / rel_json
        json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"metadata": json_ready(metadata or {}),
                   "records": json_ready(frame.to_dict(orient="records"))}
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                             encoding="utf-8")
    return rel_csv, rel_json


def write_json(relative: str, obj):
    path = ASSET_ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_ready(obj), indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8")
    return relative


def register(asset_id: str, title: str, category: str, notebook_name: str,
             section: str, retrieval_method: str, intended_use: list[str],
             holdout: bool = False, source_report: str | None = None,
             data_csv: str | None = None, data_json: str | None = None,
             dashboard_priority: str = "SECONDARY", notes: str = ""):
    png = f"figures/{category}/{asset_id}.png"
    svg = f"figures/{category}/{asset_id}.svg"
    MANIFEST.append({
        "asset_id": asset_id, "category": category, "title": title,
        "image_png": png if (ASSET_ROOT / png).is_file() else None,
        "image_svg": svg if (ASSET_ROOT / svg).is_file() else None,
        "data_csv": data_csv, "data_json": data_json,
        "source_notebook": notebook_name, "source_section_cell": section,
        "source_report_file": source_report,
        "retrieval_method": retrieval_method,
        "intended_use": intended_use,
        "uses_holdout_evidence": bool(holdout), "holdout_recomputed": False,
        "dashboard_priority": dashboard_priority, "notes": notes,
    })


def save_figure(fig, category: str, asset_id: str):
    png = FIG[category] / f"{asset_id}.png"
    svg = FIG[category] / f"{asset_id}.svg"
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=205, bbox_inches="tight", facecolor="white",
                metadata={"Software": "dashboard asset export"})
    fig.savefig(svg, bbox_inches="tight", facecolor="white",
                metadata={"Date": None, "Creator": "dashboard asset export"})
    fig.clear()
    plt.close(fig)
    gc.collect()


def style():
    sns.set_theme(style="whitegrid", context="notebook", font_scale=0.9)
    plt.rcParams.update({
        "figure.dpi": 120, "savefig.dpi": 300, "axes.spines.top": False,
        "axes.spines.right": False, "svg.fonttype": "none", "font.family": "DejaVu Sans",
    })


def export_eda():
    eda_nb = "notebooks/02_eda.ipynb"
    target = notebook_assignment(eda_nb, "TARGET")
    class_order = notebook_assignment(eda_nb, "CLASS_ORDER")
    core_numeric = notebook_assignment(eda_nb, "core_numeric")
    key_numeric = notebook_assignment(eda_nb, "key_numeric")
    key_categorical = notebook_assignment(eda_nb, "key_categorical")
    cat_vs_target = notebook_assignment(eda_nb, "cat_vs_target_cols")
    num_vs_target = notebook_assignment(eda_nb, "num_vs_target_cols")
    if class_order != CLASS_ORDER:
        raise AssertionError("Notebook 02 class ordering differs from project labels")
    source = ROOT / "data/raw/water_pump_functionality.xlsx"
    df = pd.read_excel(source)
    if df.shape != (1793, 52) or target not in df:
        raise AssertionError(f"Raw EDA source shape/target changed: {df.shape}")

    # Dataset, target, missingness and duplicate evidence from Notebook-02 logic.
    target_counts = df[target].value_counts().reindex(class_order).fillna(0).astype(int)
    target_pct = (df[target].value_counts(normalize=True) * 100).reindex(class_order).round(2)
    target_data = pd.DataFrame({"class": class_order,
                                "count": target_counts.to_numpy(),
                                "percentage": target_pct.to_numpy()})
    write_table(target_data, "data/eda/target_class_distribution.csv",
                "data/eda/target_class_distribution.json",
                {"source": "Notebook 02 cell 8", "rows": len(df), "target": target})
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(target_data["class"], target_data["count"], color=CLASS_COLORS)
    for bar, row in zip(bars, target_data.itertuples()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 15,
                f"{row.count:,}\n({row.percentage:.2f}%)", ha="center", va="bottom", fontsize=10)
    ax.set_title("Distribution of Target Variable: functional3")
    ax.set_ylabel("Number of Water Points")
    ax.set_ylim(0, target_data["count"].max() * 1.2)
    ax.tick_params(axis="x", rotation=10)
    fig.tight_layout()
    save_figure(fig, "eda", "eda_target_class_distribution")
    register("eda_target_class_distribution", "Water Point Functionality Distribution", "eda",
             eda_nb, "Target Variable Analysis; cells 8–9", "lightweight_eda_reproduction",
             ["dashboard", "report", "presentation"], data_csv="data/eda/target_class_distribution.csv",
             data_json="data/eda/target_class_distribution.json", dashboard_priority="CORE",
             notes="Counts and percentages use the full raw dataset as in Notebook 02, before the locked split.")

    missing_count = df.isnull().sum()
    missing_count = missing_count[missing_count > 0].sort_values(ascending=False)
    missing = pd.DataFrame({"column": missing_count.index,
                            "missing_count": missing_count.values.astype(int),
                            "missing_percent": (missing_count.values / len(df) * 100).round(2)})
    write_table(missing, "data/eda/missingness_summary.csv", "data/eda/missingness_summary.json",
                {"source": "Notebook 02 cell 12", "rows": len(df), "columns_with_missing": len(missing)})
    top_missing = missing.head(20).sort_values("missing_percent")
    write_table(top_missing, "data/eda/missing_values_top20.csv", "data/eda/missing_values_top20.json",
                {"source": "Notebook 02 cell 13", "selection": "20 highest missing percentages"})
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(top_missing["column"], top_missing["missing_percent"], color="#C44E52")
    ax.set_xlabel("Missing (%)")
    ax.set_title("Top 20 Columns by Missing Percentage")
    fig.tight_layout()
    save_figure(fig, "eda", "eda_top20_missing_values")
    register("eda_top20_missing_values", "Top 20 Columns by Missing Percentage", "eda", eda_nb,
             "Missing Value Analysis; cells 12–13", "lightweight_eda_reproduction",
             ["dashboard", "report", "presentation"], data_csv="data/eda/missing_values_top20.csv",
             data_json="data/eda/missing_values_top20.json", dashboard_priority="CORE")

    # Numerical descriptions and outlier table reuse exact Notebook-02 variable lists/rule.
    desc = df[key_numeric].describe().T
    desc["skew"] = df[key_numeric].skew()
    desc = desc.round(2).rename_axis("variable").reset_index()
    write_table(desc, "data/eda/numerical_descriptive_summary.csv",
                "data/eda/numerical_descriptive_summary.json", {"source": "Notebook 02 cell 21"})
    outlier_rows = []
    for col in key_numeric:
        series = df[col].dropna()
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((series < lower) | (series > upper)).sum())
        outlier_rows.append({"variable": col, "n": len(series), "min": series.min(), "max": series.max(),
                             "iqr_lower": round(lower, 2), "iqr_upper": round(upper, 2),
                             "n_outliers": count, "pct_outliers": round(count / len(series) * 100, 2)})
    outliers = pd.DataFrame(outlier_rows)
    write_table(outliers, "data/eda/outlier_summary.csv", "data/eda/outlier_summary.json",
                {"source": "Notebook 02 cells 30–33", "rule": "1.5 × IQR; values not removed"})
    numeric_long = df[core_numeric].melt(var_name="variable", value_name="value").dropna()
    write_table(numeric_long, "data/eda/key_numeric_distribution_data.csv",
                "data/eda/key_numeric_distribution_data.json", {"source": "Notebook 02 cell 22"})
    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    for ax, col in zip(axes.flat, core_numeric):
        sns.histplot(df[col].dropna(), bins=30, ax=ax, color=CLASS_COLORS[0])
        ax.set_title(col); ax.set_xlabel("")
    fig.suptitle("Distributions of Key Numerical Variables")
    fig.tight_layout()
    save_figure(fig, "eda", "eda_key_numeric_distributions")
    register("eda_key_numeric_distributions", "Distributions of Key Numerical Variables", "eda", eda_nb,
             "Numerical Variable Analysis; cell 22", "lightweight_eda_reproduction",
             ["report", "presentation"], data_csv="data/eda/key_numeric_distribution_data.csv",
             data_json="data/eda/key_numeric_distribution_data.json", dashboard_priority="SECONDARY")

    fig, axes = plt.subplots(2, 3, figsize=(14, 7))
    for ax, col in zip(axes.flat, core_numeric):
        sns.boxplot(y=df[col].dropna(), ax=ax, color=CLASS_COLORS[1])
        ax.set_title(col); ax.set_ylabel("")
    fig.suptitle("Boxplots of Key Numerical Variables")
    fig.tight_layout()
    save_figure(fig, "eda", "eda_key_numeric_boxplots")
    register("eda_key_numeric_boxplots", "Boxplots of Key Numerical Variables", "eda", eda_nb,
             "Numerical Variable Analysis; cell 23", "lightweight_eda_reproduction",
             ["report", "presentation"], dashboard_priority="SECONDARY")

    cat_rows = []
    for col in key_categorical:
        counts = df[col].value_counts(dropna=False)
        for value, count in counts.items():
            cat_rows.append({"variable": col, "category": "(Missing)" if pd.isna(value) else str(value),
                             "count": int(count), "percentage": float(count / len(df) * 100)})
    category_counts = pd.DataFrame(cat_rows)
    write_table(category_counts, "data/eda/key_categorical_frequencies.csv",
                "data/eda/key_categorical_frequencies.json", {"source": "Notebook 02 cells 26–27"})
    fig, axes = plt.subplots(4, 2, figsize=(13, 16))
    for ax, col in zip(axes.flat, key_categorical):
        order = df[col].value_counts().index
        sns.countplot(y=df[col], order=order, ax=ax, color="#55A868")
        ax.set_title(col); ax.set_ylabel(""); ax.set_xlabel("count")
    fig.delaxes(axes.flat[-1])
    fig.suptitle("Category Frequencies for Key Categorical Variables", y=1.0)
    fig.tight_layout()
    save_figure(fig, "eda", "eda_key_categorical_frequencies")
    register("eda_key_categorical_frequencies", "Category Frequencies for Key Categorical Variables", "eda",
             eda_nb, "Categorical Variable Analysis; cells 26–27", "lightweight_eda_reproduction",
             ["report", "presentation"], data_csv="data/eda/key_categorical_frequencies.csv",
             data_json="data/eda/key_categorical_frequencies.json", dashboard_priority="SECONDARY")

    country_ct = pd.crosstab(df["country"], df[target], normalize="index").reindex(columns=class_order) * 100
    country_ct = country_ct.sort_values("Functional")
    country_data = country_ct.rename_axis("country").reset_index()
    write_table(country_data, "data/eda/functionality_by_country.csv",
                "data/eda/functionality_by_country.json", {"source": "Notebook 02 cell 36", "unit": "row percent"})
    fig, ax = plt.subplots(figsize=(8, 5))
    country_ct.plot(kind="barh", stacked=True, ax=ax, color=CLASS_COLORS)
    ax.set_title("functional3 Distribution by Country (%)")
    ax.set_xlabel("Percentage"); ax.set_ylabel("country")
    ax.legend(title="functional3", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    save_figure(fig, "eda", "eda_functionality_by_country")
    register("eda_functionality_by_country", "Functionality Distribution by Country (%)", "eda", eda_nb,
             "Feature vs Target Analysis; cell 36", "lightweight_eda_reproduction",
             ["dashboard", "report", "presentation"], data_csv="data/eda/functionality_by_country.csv",
             data_json="data/eda/functionality_by_country.json", dashboard_priority="CORE",
             notes="Row-normalized percentages, sorted by Functional share; descriptive EDA across the raw dataset.")

    # Preserve the notebook's exact row-normalized percentage calculation and n >= 10 rule.
    cat_vs_rows = []
    for col in cat_vs_target:
        ct = pd.crosstab(df[col], df[target], normalize="index").reindex(columns=class_order) * 100
        counts = df[col].value_counts()
        ct = ct.loc[counts[counts >= 10].index]
        for category, row in ct.iterrows():
            for label in class_order:
                cat_vs_rows.append({"feature": col, "category": str(category), "class": label,
                                    "percentage": float(row[label]), "category_n": int(counts[category])})
    cat_vs_data = pd.DataFrame(cat_vs_rows)
    write_table(cat_vs_data, "data/eda/categorical_features_vs_target.csv",
                "data/eda/categorical_features_vs_target.json",
                {"source": "Notebook 02 cell 38", "category_filter": "n >= 10",
                 "normalization": "row percentages (as implemented in notebook)"})
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    for ax, col in zip(axes, cat_vs_target):
        ct = pd.crosstab(df[col], df[target], normalize="index").reindex(columns=class_order) * 100
        counts = df[col].value_counts()
        ct = ct.loc[counts[counts >= 10].index]
        ct.plot(kind="barh", stacked=True, ax=ax, color=CLASS_COLORS, legend=False)
        ax.set_title(f"{col} vs functional3 (n>=10)"); ax.set_xlabel("Percentage"); ax.set_ylabel("")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="functional3", bbox_to_anchor=(1.02, 0.5), loc="center left")
    fig.tight_layout()
    save_figure(fig, "eda", "eda_categorical_features_vs_target")
    register("eda_categorical_features_vs_target", "Categorical Features vs Functionality", "eda", eda_nb,
             "Feature vs Target Analysis; cell 38", "lightweight_eda_reproduction",
             ["report", "presentation"], data_csv="data/eda/categorical_features_vs_target.csv",
             data_json="data/eda/categorical_features_vs_target.json", dashboard_priority="SECONDARY",
             notes="Exact Notebook-02 category filter n >= 10 retained.")

    numeric_group = df.groupby(target)[num_vs_target].describe().round(3)
    num_rows = []
    for variable in num_vs_target:
        for label in class_order:
            values = df.loc[df[target] == label, variable].dropna()
            num_rows.append({"class": label, "variable": variable, "n": len(values),
                             "mean": values.mean(), "median": values.median(),
                             "q1": values.quantile(.25), "q3": values.quantile(.75)})
    num_data = pd.DataFrame(num_rows)
    write_table(num_data, "data/eda/numeric_features_vs_target.csv",
                "data/eda/numeric_features_vs_target.json", {"source": "Notebook 02 cell 42"})
    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    for ax, col in zip(axes, num_vs_target):
        sns.boxplot(data=df, x=target, y=col, order=class_order, ax=ax,
                    hue=target, hue_order=class_order, palette=CLASS_COLORS, legend=False)
        ax.set_title(f"{col} by functional3"); ax.set_xlabel(""); ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    save_figure(fig, "eda", "eda_numeric_features_vs_target")
    register("eda_numeric_features_vs_target", "Numerical Features by Functionality", "eda", eda_nb,
             "Feature vs Target Analysis; cell 42", "lightweight_eda_reproduction",
             ["dashboard", "report", "presentation"], data_csv="data/eda/numeric_features_vs_target.csv",
             data_json="data/eda/numeric_features_vs_target.json", dashboard_priority="CORE")

    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != "id"]
    corr = df[numeric_cols].corr()
    corr_long = corr.rename_axis("variable").reset_index().melt(id_vars="variable", var_name="other_variable",
                                                                 value_name="pearson_correlation")
    write_table(corr_long, "data/eda/numeric_correlation_matrix.csv",
                "data/eda/numeric_correlation_matrix.json", {"source": "Notebook 02 cells 45–46"})
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, cmap="coolwarm", center=0, annot=False, square=True,
                cbar_kws={"label": "Pearson correlation"}, ax=ax)
    ax.set_title("Correlation Heatmap — Numerical Variables")
    fig.tight_layout()
    save_figure(fig, "eda", "eda_numeric_correlation_heatmap")
    register("eda_numeric_correlation_heatmap", "Correlation Heatmap — Numerical Variables", "eda", eda_nb,
             "Correlation Analysis; cell 45", "lightweight_eda_reproduction",
             ["report", "presentation"], data_csv="data/eda/numeric_correlation_matrix.csv",
             data_json="data/eda/numeric_correlation_matrix.json", dashboard_priority="SECONDARY")

    # Leakage diagnostic is retained strictly for technical report/viva use.
    leakage_tables = []
    for col in ["wateravailable", "downtime2weeks"]:
        ct = pd.crosstab(df[col], df[target]).reindex(columns=class_order, fill_value=0)
        for value, row in ct.iterrows():
            for label in class_order:
                leakage_tables.append({"variable": col, "value": str(value), "class": label,
                                       "count": int(row[label])})
    leakage_tables = pd.DataFrame(leakage_tables)
    write_table(leakage_tables, "data/eda/leakage_crosstabs.csv", "data/eda/leakage_crosstabs.json",
                {"source": "Notebook 02 cells 49–52", "intended_use": "technical_report_only"})
    leakage_numeric = df.groupby(target)["minutesfill20l"].describe().reset_index()
    write_table(leakage_numeric, "data/eda/leakage_minutesfill20l_summary.csv",
                "data/eda/leakage_minutesfill20l_summary.json",
                {"source": "Notebook 02 cells 51–52", "scale": "log in figure"})
    secondary_leak_rows = []
    for col in ["brokendays_wp", "qtymonthsnowater_wp"]:
        summary = df.groupby(target)[col].describe()[["count", "mean", "50%", "max"]]
        for label, row in summary.iterrows():
            secondary_leak_rows.append({"variable": col, "class": label, **row.to_dict()})
    for col, series in [
        ("whynowatertoday_wp_recorded", df["whynowatertoday_wp"].notna()),
        ("lockedfullday_wp", df["lockedfullday_wp"]),
    ]:
        ct = pd.crosstab(series, df[target]).reindex(columns=class_order, fill_value=0)
        for value, row in ct.iterrows():
            for label in class_order:
                secondary_leak_rows.append({"variable": col, "value": str(value), "class": label,
                                            "count": int(row[label])})
    write_table(pd.DataFrame(secondary_leak_rows), "data/eda/leakage_secondary_evidence.csv",
                "data/eda/leakage_secondary_evidence.json",
                {"source": "Notebook 02 cell 54 stored analysis, reproduced from raw descriptive data",
                 "intended_use": "technical_report_only"})
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, col in zip(axes, ["wateravailable", "downtime2weeks"]):
        ct = pd.crosstab(df[col], df[target]).reindex(columns=class_order, fill_value=0)
        ct.plot(kind="bar", stacked=True, ax=ax, color=CLASS_COLORS, legend=False)
        ax.set_title(f"{col} vs functional3 (counts)"); ax.tick_params(axis="x", rotation=0)
    sns.boxplot(data=df, x=target, y="minutesfill20l", order=class_order, ax=axes[2],
                hue=target, hue_order=class_order, palette=CLASS_COLORS, legend=False)
    axes[2].set_yscale("log"); axes[2].set_title("minutesfill20l by functional3 (log scale)")
    axes[2].tick_params(axis="x", rotation=30)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, title="functional3", bbox_to_anchor=(1.02, 0.5), loc="center left")
    fig.tight_layout()
    save_figure(fig, "eda", "eda_leakage_diagnostic")
    register("eda_leakage_diagnostic", "Potential Leakage Diagnostic", "eda", eda_nb,
             "Potential Data Leakage Investigation; cells 49–52", "lightweight_eda_reproduction",
             ["technical_report_only"],
             data_csv="data/eda/leakage_crosstabs.csv", data_json="data/eda/leakage_crosstabs.json",
             dashboard_priority="REPORT_ONLY", notes="Potential leakage variables are excluded from final model input.")

    rehab_context = (df.groupby("rehabyn", dropna=False)["rehab_age"]
                     .apply(lambda series: series.isnull().mean() * 100).round(2)
                     .rename("rehab_age_missing_percent").reset_index())
    duplicate_count = int(df.duplicated().sum())
    duplicate_summary = {"rows": len(df), "duplicate_rows": duplicate_count,
                         "duplicate_percent": round(duplicate_count / len(df) * 100, 2),
                         "source": "Notebook 02 cell 18"}
    dataset_summary = {
        "rows": int(len(df)), "columns": int(df.shape[1]), "target": target,
        "numeric_columns_excluding_id_count": len(numeric_cols),
        "categorical_columns_excluding_target_and_id_count": int(
            len([c for c in df.columns if c not in numeric_cols and c not in ["id", target]])
        ),
        "columns_with_missing": int((df.isna().sum() > 0).sum()),
        "duplicate_rows": duplicate_count,
        "negative_elevation_rows": int((df["elevation_wp"] < 0).sum()),
        "negative_elevation_by_country": {str(k): int(v) for k, v in
                                          df.loc[df.elevation_wp < 0, "country"].value_counts().items()},
        "target_class_counts": dict(zip(target_data["class"], target_data["count"].astype(int))),
        "source": "Notebook 02 descriptive analysis; raw workbook before locked split",
    }
    write_json("data/eda/dataset_summary.json", dataset_summary)
    write_json("data/eda/duplicate_summary.json", duplicate_summary)
    write_table(rehab_context, "data/eda/missingness_context.csv", "data/eda/missingness_context.json",
                {"source": "Notebook 02 cell 15"})
    rare_rows = []
    for col in key_categorical:
        counts = df[col].value_counts(dropna=False)
        for label, count in counts.items():
            if count < 10:
                rare_rows.append({"variable": col, "category": "(Missing)" if pd.isna(label) else str(label),
                                  "count": int(count)})
    write_table(pd.DataFrame(rare_rows), "data/eda/rare_categories_under10.csv",
                "data/eda/rare_categories_under10.json", {"source": "Notebook 02 cells 26–28"})
    corr_pairs = (corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
                  .sort_values(key=abs, ascending=False).head(10))
    corr_pair_data = corr_pairs.rename("correlation").rename_axis(["variable", "other_variable"]).reset_index()
    write_table(corr_pair_data,
                "data/eda/top_numeric_correlations.csv", "data/eda/top_numeric_correlations.json",
                {"source": "Notebook 02 cell 46", "top_n": 10})
    print("EDA assets reproduced from raw workbook:", len([x for x in MANIFEST if x["source_notebook"] == eda_nb]))


def export_preprocessing_summary():
    metadata = json.loads((ROOT / "data/processed/modern/preprocessing_variants.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "reports/model_optimization/final_selection_locked.json").read_text(encoding="utf-8"))
    export_meta = json.loads((ROOT / "models/final_model_metadata.json").read_text(encoding="utf-8"))
    summary = {
        "raw_predictor_count": len(metadata["raw_predictor_columns"]),
        "raw_predictor_columns": metadata["raw_predictor_columns"],
        "target": metadata["target"],
        "tree_base": metadata["variants"]["tree_base"],
        "locked_model": {
            "preprocessing_variant": lock["preprocessing_variant"],
            "rare_min_frequency": lock["rare_min_frequency"],
            "feature_set": lock["feature_set"],
            "feature_selection_k": lock["feature_selection_k"],
            "imbalance_strategy": lock["imbalance_strategy"],
            "preprocessing_output_count": export_meta["preprocessing_feature_count"],
        },
    }
    write_json("data/preprocessing/preprocessing_summary.json", summary)
    variants = []
    for name, config in metadata["variants"].items():
        variants.append({"variant": name, **config})
    write_table(pd.json_normalize(variants), "data/preprocessing/preprocessing_variants.csv",
                "data/preprocessing/preprocessing_variants.json",
                {"source": "preprocessing_variants.json; model policy from final selection lock"})


def export_model_development():
    source_nb = "notebooks/04_model_development.ipynb"
    base = pd.read_csv(ROOT / "reports/model_development/baseline_cv_summary.csv")
    ablation = pd.read_csv(ROOT / "reports/model_development/feature_ablation_summary.csv")
    oof_classes = pd.read_csv(ROOT / "reports/model_development/oof_class_metrics.csv")
    oof_predictions = pd.read_csv(ROOT / "reports/model_development/oof_predictions.csv")
    winners = pd.read_csv(ROOT / "reports/model_development/model_family_winners.csv")

    data_path, data_json = write_table(base, "data/modelling/baseline_cv_summary.csv",
                                       "data/modelling/baseline_cv_summary.json",
                                       {"source": "reports/model_development/baseline_cv_summary.csv"})
    order = base["configuration"].tolist()
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(base["configuration"], base["mean_macro_f1"], yerr=base["sd_macro_f1"],
           capsize=3, color="#4678A8")
    ax.set_ylabel("Mean repeated-CV Macro-F1 ± SD"); ax.set_title("Primary baseline metric")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    save_figure(fig, "modelling", "model_baseline_macro_f1")
    register("model_baseline_macro_f1", "Primary Baseline Macro-F1", "modelling", source_nb,
             "Baseline Visualizations; cell 38", "saved_report_regeneration", ["dashboard", "report", "presentation"],
             source_report="reports/model_development/baseline_cv_summary.csv", data_csv=data_path,
             data_json=data_json, dashboard_priority="CORE", notes="Mean repeated-CV Macro-F1 with fold SD.")

    write_table(ablation, "data/modelling/base_vs_engineered_ablation.csv",
                "data/modelling/base_vs_engineered_ablation.json",
                {"source": "reports/model_development/feature_ablation_summary.csv"})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for _, row in ablation.iterrows():
        axes[0].plot(["Base", "Engineered"], [row.base_macro_f1, row.engineered_macro_f1],
                     marker="o", label=row.model_family)
        axes[1].plot(["Base", "Engineered"], [row.base_balanced_accuracy, row.engineered_balanced_accuracy],
                     marker="o", label=row.model_family)
    axes[0].set_title("Macro-F1 ablation"); axes[1].set_title("Balanced Accuracy ablation")
    for ax in axes:
        ax.legend(fontsize=8); ax.grid(alpha=.2)
    fig.tight_layout()
    save_figure(fig, "modelling", "model_base_vs_engineered_ablation")
    register("model_base_vs_engineered_ablation", "Base vs Engineered Feature Ablation", "modelling",
             source_nb, "Feature-Engineering Ablation; cell 38", "saved_report_regeneration",
             ["report", "presentation"], source_report="reports/model_development/feature_ablation_summary.csv",
             data_csv="data/modelling/base_vs_engineered_ablation.csv",
             data_json="data/modelling/base_vs_engineered_ablation.json", dashboard_priority="REPORT_ONLY")

    train_valid = base[["configuration", "model_family", "mean_train_macro_f1", "mean_macro_f1", "mean_mcc"]].copy()
    write_table(train_valid, "data/modelling/baseline_train_validation_mcc.csv",
                "data/modelling/baseline_train_validation_mcc.json",
                {"source": "reports/model_development/baseline_cv_summary.csv"})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].scatter(base.mean_train_macro_f1, base.mean_macro_f1, color="#4678A8")
    for _, row in base.iterrows():
        axes[0].annotate(row.configuration, (row.mean_train_macro_f1, row.mean_macro_f1), fontsize=7)
    axes[0].set_xlabel("Train Macro-F1"); axes[0].set_ylabel("CV Macro-F1"); axes[0].set_title("Training vs validation")
    axes[1].bar(base.configuration, base.mean_mcc, color="#7C9D72")
    axes[1].set_title("Mean CV MCC"); axes[1].tick_params(axis="x", rotation=70)
    fig.tight_layout()
    save_figure(fig, "modelling", "model_train_vs_validation_and_mcc")
    register("model_train_vs_validation_and_mcc", "Training vs Validation and MCC", "modelling", source_nb,
             "Generalization/Overfitting; cell 38", "saved_report_regeneration",
             ["dashboard", "report", "presentation"], source_report="reports/model_development/baseline_cv_summary.csv",
             data_csv="data/modelling/baseline_train_validation_mcc.csv",
             data_json="data/modelling/baseline_train_validation_mcc.json", dashboard_priority="CORE")

    partial = oof_classes[oof_classes["class"] == "Partially functional"].copy()
    partial["_order"] = partial.configuration.map({name: i for i, name in enumerate(order)})
    partial = partial.sort_values("_order").drop(columns="_order")
    write_table(partial, "data/modelling/partial_class_baselines.csv",
                "data/modelling/partial_class_baselines.json",
                {"source": "reports/model_development/oof_class_metrics.csv", "class": "Partially functional"})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].bar(partial.configuration, partial.recall, label="Recall", color="#C47A4A")
    axes[0].bar(partial.configuration, partial.f1, label="F1", alpha=.65, color="#557E9E")
    axes[0].set_title("Partial class: OOF Recall/F1"); axes[0].legend()
    axes[1].bar(partial.configuration, partial.average_precision, color="#9175A5")
    axes[1].set_title("Partial class: OOF AP")
    for ax in axes:
        ax.tick_params(axis="x", rotation=70); ax.grid(axis="y", alpha=.2)
    fig.tight_layout()
    save_figure(fig, "modelling", "model_partial_class_baselines")
    register("model_partial_class_baselines", "Partial Class OOF Metrics", "modelling", source_nb,
             "Per-Class and Minority-Class Evaluation; cells 26–28, figure cell 38",
             "saved_report_regeneration", ["dashboard", "report", "presentation"],
             source_report="reports/model_development/oof_class_metrics.csv",
             data_csv="data/modelling/partial_class_baselines.csv",
             data_json="data/modelling/partial_class_baselines.json", dashboard_priority="CORE")

    # Confusions and PR curves are reconstructed only from saved OOF predictions.
    class_ids = {name: i for i, name in enumerate(CLASS_ORDER)}
    winner_records = []
    matrices = {}
    for _, row in winners.iterrows():
        name = row.configuration
        sub = oof_predictions[oof_predictions.configuration == name]
        if len(sub) != 1434:
            raise AssertionError(f"Saved OOF rows missing for family winner {name}")
        truth = sub.true_class.map(class_ids).to_numpy()
        pred = sub.predicted_class.map(class_ids).to_numpy()
        cm = confusion_matrix(truth, pred, labels=[0, 1, 2])
        matrices[name] = cm
        normalized = cm / cm.sum(axis=1, keepdims=True)
        for ai, actual in enumerate(CLASS_ORDER):
            for pi, predicted in enumerate(CLASS_ORDER):
                winner_records.append({"configuration": name, "actual": actual, "predicted": predicted,
                                       "count": int(cm[ai, pi]), "row_normalized": float(normalized[ai, pi])})
    winner_cm = pd.DataFrame(winner_records)
    write_table(winner_cm, "data/modelling/family_winner_confusion_matrices.csv",
                "data/modelling/family_winner_confusion_matrices.json",
                {"source": "reports/model_development/oof_predictions.csv",
                 "recovered_without_model_fitting": True})
    fig, axes = plt.subplots(len(matrices), 2, figsize=(10, 3.2 * len(matrices)), squeeze=False)
    for i, (name, cm) in enumerate(matrices.items()):
        norm = cm / cm.sum(axis=1, keepdims=True)
        for j, matrix in enumerate([cm, norm]):
            ax = axes[i, j]; ax.imshow(matrix, cmap="Blues", vmin=0)
            for (r, c), val in np.ndenumerate(matrix):
                ax.text(c, r, f"{val:.2f}" if j else f"{int(val)}", ha="center", va="center", fontsize=8)
            ax.set_xticks(range(3), CLASS_ORDER, rotation=35, ha="right")
            ax.set_yticks(range(3), CLASS_ORDER); ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
            ax.set_title(f"{name}: {'normalized' if j else 'counts'}")
    fig.tight_layout()
    save_figure(fig, "modelling", "model_family_winner_confusion_matrices")
    register("model_family_winner_confusion_matrices", "Family-Winner OOF Confusion Matrices", "modelling",
             source_nb, "Confusion Matrices and PR Curves; cell 40",
             "saved_report_regeneration", ["report", "presentation"],
             source_report="reports/model_development/oof_predictions.csv",
             data_csv="data/modelling/family_winner_confusion_matrices.csv",
             data_json="data/modelling/family_winner_confusion_matrices.json",
             dashboard_priority="REPORT_ONLY", notes="Count and row-normalized matrices; OOF development predictions only.")

    shortlisted = winners.sort_values("mean_macro_f1", ascending=False).head(3).configuration.tolist()
    pr_records = []
    fig, axes = plt.subplots(len(shortlisted), 2, figsize=(11, 3.4 * len(shortlisted)), squeeze=False)
    for i, name in enumerate(shortlisted):
        sub = oof_predictions[oof_predictions.configuration == name]
        truth = sub.true_class.map(class_ids).to_numpy()
        for j, class_id in enumerate([1, 2]):
            score = sub[f"probability_{CLASS_ORDER[class_id]}"] .to_numpy()
            binary = (truth == class_id).astype(int)
            precision, recall, _ = precision_recall_curve(binary, score)
            ap = average_precision_score(binary, score)
            axes[i, j].plot(recall, precision, label=f"AP={ap:.3f}", color=MODEL_COLORS[i])
            axes[i, j].set_title(f"{name}: {CLASS_ORDER[class_id]}")
            axes[i, j].set_xlabel("Recall"); axes[i, j].set_ylabel("Precision")
            axes[i, j].legend(); axes[i, j].grid(alpha=.2)
            pr_records.extend({"configuration": name, "class": CLASS_ORDER[class_id],
                               "recall": float(r), "precision": float(p), "average_precision": float(ap)}
                              for p, r in zip(precision, recall))
    fig.tight_layout()
    save_figure(fig, "modelling", "model_shortlist_precision_recall_curves")
    write_table(pd.DataFrame(pr_records), "data/modelling/shortlist_precision_recall_curves.csv",
                "data/modelling/shortlist_precision_recall_curves.json",
                {"source": "reports/model_development/oof_predictions.csv", "shortlist": shortlisted})
    register("model_shortlist_precision_recall_curves", "Shortlist Precision-Recall Curves", "modelling",
             source_nb, "Confusion Matrices and Precision-Recall Curves; cell 40",
             "saved_report_regeneration", ["report", "presentation"],
             source_report="reports/model_development/oof_predictions.csv",
             data_csv="data/modelling/shortlist_precision_recall_curves.csv",
             data_json="data/modelling/shortlist_precision_recall_curves.json",
             dashboard_priority="REPORT_ONLY", notes="Curves use saved OOF scores; no estimator was fitted.")


def export_optimization():
    source_nb = "notebooks/05_model_optimization.ipynb"
    baseline = pd.read_csv(ROOT / "reports/model_optimization/baseline_vs_optimized.csv")
    finalists = pd.read_csv(ROOT / "reports/model_optimization/finalist_cv_summary.csv")
    class_metrics = pd.read_csv(ROOT / "reports/model_optimization/finalist_oof_class_metrics.csv")
    confusion = pd.read_csv(ROOT / "reports/model_optimization/finalist_confusion_matrices.csv")
    cv_holdout = pd.read_csv(ROOT / "reports/model_optimization/cv_vs_holdout.csv")
    lock = json.loads((ROOT / "reports/model_optimization/final_selection_locked.json").read_text(encoding="utf-8"))
    final_name = lock["finalist"]

    write_table(baseline, "data/optimization/baseline_vs_optimized.csv",
                "data/optimization/baseline_vs_optimized.json",
                {"source": "reports/model_optimization/baseline_vs_optimized.csv"})
    write_table(finalists, "data/optimization/finalist_cv_summary.csv",
                "data/optimization/finalist_cv_summary.json",
                {"source": "reports/model_optimization/finalist_cv_summary.csv"})
    partial = class_metrics[class_metrics["class"] == "Partially functional"].copy()
    finalist_labels = [
        "RF (k=60)" if row.family == "Random Forest" else
        "XGBoost" if row.family == "XGBoost" else
        "HistGB" if row.family == "HistGradientBoosting" else row.family
        for row in finalists.itertuples()
    ]
    write_table(partial, "data/optimization/finalist_partial_class_metrics.csv",
                "data/optimization/finalist_partial_class_metrics.json",
                {"source": "reports/model_optimization/finalist_oof_class_metrics.csv"})
    final_metrics = finalists[finalists.finalist == final_name]
    if len(final_metrics) != 1:
        raise AssertionError("Locked finalist missing from saved finalist CV summary")
    historical_holdout = pd.read_csv(ROOT / "reports/model_optimization/final_holdout_class_metrics.csv")
    write_table(historical_holdout, "data/final_model/final_class_metrics.csv",
                "data/final_model/final_class_metrics.json",
                {"source": "reports/model_optimization/final_holdout_class_metrics.csv",
                 "historical_recorded_evaluation": True, "holdout_recomputed": False})
    final_metric_payload = {
        "selected_finalist": final_name,
        "cv_and_historical_holdout": cv_holdout.to_dict(orient="records"),
        "historical_holdout_class_metrics": historical_holdout.to_dict(orient="records"),
        "source": ["reports/model_optimization/cv_vs_holdout.csv",
                   "reports/model_optimization/final_holdout_class_metrics.csv"],
        "holdout_recomputed": False,
    }
    write_json("data/final_model/final_model_metrics.json", final_metric_payload)

    # Existing Stage-7 2x2 overview and dashboard-ready individual panels.
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    x = np.arange(len(baseline)); width = .35
    for j, (base_col, opt_col, title) in enumerate([
        ("baseline_macro_f1", "optimized_macro_f1", "Macro-F1"),
        ("baseline_mcc", "optimized_mcc", "MCC"),
    ]):
        ax = axes[0, j]
        ax.bar(x - width / 2, baseline[base_col], width, label="Baseline", color="#7C9D72")
        ax.bar(x + width / 2, baseline[opt_col], width, label="Optimized", color="#4678A8")
        ax.set_xticks(x, baseline.family, rotation=30, ha="right"); ax.set_title(title); ax.legend()
    axes[1, 0].bar(finalist_labels, finalists.macro_f1, yerr=finalists.sd_macro_f1,
                   capsize=3, color="#4678A8")
    axes[1, 0].tick_params(axis="x", rotation=15); axes[1, 0].set_title("Finalist Repeated-CV Macro-F1")
    px = np.arange(len(partial)); pwidth = .36
    axes[1, 1].bar(px - pwidth / 2, partial.recall, pwidth, label="Recall", color="#C47A4A")
    axes[1, 1].bar(px + pwidth / 2, partial.f1, pwidth, label="F1", color="#557E9E")
    axes[1, 1].set_xticks(px, finalist_labels, rotation=15)
    axes[1, 1].set_title("Partial-class OOF"); axes[1, 1].legend()
    fig.tight_layout()
    save_figure(fig, "optimization", "optimization_overview")
    register("optimization_overview", "Notebook 05 Optimization Overview", "optimization", source_nb,
             "Interpretation and plots; cell 43", "saved_report_regeneration",
             ["report", "presentation"], source_report="reports/model_optimization/*.csv",
             data_csv="data/optimization/baseline_vs_optimized.csv",
             data_json="data/optimization/baseline_vs_optimized.json", dashboard_priority="SECONDARY")

    for metric, label, asset_id in [
        ("macro_f1", "Macro-F1", "baseline_vs_optimized_macro_f1"),
        ("mcc", "MCC", "baseline_vs_optimized_mcc"),
    ]:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(x - width / 2, baseline[f"baseline_{metric}"], width, label="Baseline", color="#7C9D72")
        ax.bar(x + width / 2, baseline[f"optimized_{metric}"], width, label="Optimized", color="#4678A8")
        ax.set_xticks(x, baseline.family, rotation=25, ha="right"); ax.set_ylabel(label); ax.set_title(f"Baseline vs Optimized {label}"); ax.legend()
        fig.tight_layout(); save_figure(fig, "optimization", asset_id)
        register(asset_id, f"Baseline vs Optimized {label}", "optimization", source_nb,
                 "Baseline vs exploratory search; cells 17 and 43", "saved_report_regeneration",
                 ["dashboard", "report", "presentation"],
                 source_report="reports/model_optimization/baseline_vs_optimized.csv",
                 data_csv="data/optimization/baseline_vs_optimized.csv",
                 data_json="data/optimization/baseline_vs_optimized.json", dashboard_priority="CORE")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(finalist_labels, finalists.macro_f1, yerr=finalists.sd_macro_f1, capsize=3, color="#4678A8")
    ax.set_ylabel("Mean repeated-CV Macro-F1 ± SD"); ax.set_title("Finalist Repeated-CV Macro-F1")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout(); save_figure(fig, "optimization", "finalist_repeated_cv_macro_f1")
    register("finalist_repeated_cv_macro_f1", "Finalist Repeated-CV Macro-F1", "optimization", source_nb,
             "Complete finalists common repeated CV; saved summary", "saved_report_regeneration",
             ["dashboard", "report", "presentation"],
             source_report="reports/model_optimization/finalist_cv_summary.csv",
             data_csv="data/optimization/finalist_cv_summary.csv",
             data_json="data/optimization/finalist_cv_summary.json", dashboard_priority="CORE")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    px = np.arange(len(partial)); pwidth = .36
    axes[0].bar(px - pwidth / 2, partial.recall, pwidth, label="Recall", color="#C47A4A")
    axes[0].bar(px + pwidth / 2, partial.f1, pwidth, label="F1", color="#557E9E")
    axes[0].set_xticks(px, finalist_labels, rotation=15)
    axes[0].set_title("Partial-class OOF Recall/F1"); axes[0].legend()
    axes[1].bar(partial.finalist, partial.average_precision, color="#9175A5")
    axes[1].set_title("Partial-class OOF AP")
    axes[1].set_xticks(px, finalist_labels, rotation=15)
    fig.tight_layout(); save_figure(fig, "optimization", "finalist_partial_class_metrics")
    register("finalist_partial_class_metrics", "Finalist Partial-Class Metrics", "optimization", source_nb,
             "One OOF prediction per development row; saved class metrics", "saved_report_regeneration",
             ["dashboard", "report", "presentation"],
             source_report="reports/model_optimization/finalist_oof_class_metrics.csv",
             data_csv="data/optimization/finalist_partial_class_metrics.csv",
             data_json="data/optimization/finalist_partial_class_metrics.json", dashboard_priority="CORE")

    cm_data = confusion.copy()
    write_table(cm_data, "data/optimization/finalist_confusion_matrices.csv",
                "data/optimization/finalist_confusion_matrices.json",
                {"source": "reports/model_optimization/finalist_confusion_matrices.csv", "OOF": True})
    finalists_order = finalists.finalist.tolist()
    fig, axes = plt.subplots(len(finalists_order), 2, figsize=(12, 3.2 * len(finalists_order)), squeeze=False)
    for i, name in enumerate(finalists_order):
        subset = cm_data[cm_data.finalist == name]
        cm = subset.pivot(index="actual", columns="predicted", values="count").reindex(
            index=CLASS_ORDER, columns=CLASS_ORDER).to_numpy()
        norm = subset.pivot(index="actual", columns="predicted", values="row_normalized").reindex(
            index=CLASS_ORDER, columns=CLASS_ORDER).to_numpy()
        for j, matrix in enumerate([cm, norm]):
            ax = axes[i, j]; ax.imshow(matrix, cmap="Blues", vmin=0)
            for (r, c), value in np.ndenumerate(matrix):
                ax.text(c, r, f"{value:.2f}" if j else f"{int(value)}", ha="center", va="center", fontsize=8)
            short = ["Functional", "Partial", "Abandoned"]
            ax.set_xticks(range(3), short, rotation=35, ha="right"); ax.set_yticks(range(3), short)
            short_name = finalist_labels[i]
            ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title(f"{short_name}: {'normalized' if j else 'counts'}")
    fig.tight_layout(); save_figure(fig, "optimization", "optimization_finalist_confusion_matrices")
    register("optimization_finalist_confusion_matrices", "Finalist OOF Confusion Matrices", "optimization", source_nb,
             "One OOF prediction per development row; saved confusion evidence", "saved_report_regeneration",
             ["report", "presentation"], source_report="reports/model_optimization/finalist_confusion_matrices.csv",
             data_csv="data/optimization/finalist_confusion_matrices.csv",
             data_json="data/optimization/finalist_confusion_matrices.json",
             dashboard_priority="REPORT_ONLY", notes="Three candidates, count and row-normalized matrices.")

    write_table(cv_holdout, "data/final_model/cv_vs_holdout.csv", "data/final_model/cv_vs_holdout.json",
                {"source": "reports/model_optimization/cv_vs_holdout.csv", "historical_evaluation": True,
                 "holdout_recomputed": False})
    comparison = cv_holdout[cv_holdout.metric.isin(["macro_f1", "balanced_accuracy", "mcc", "accuracy"])]
    x = np.arange(len(comparison))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - .18, comparison.repeated_cv, .36, label="Repeated CV", color="#4678A8")
    ax.bar(x + .18, comparison.holdout, .36, label="Previously recorded holdout", color="#DD8452")
    ax.set_xticks(x, comparison.metric, rotation=25, ha="right"); ax.legend()
    ax.set_title("Selected model: CV versus holdout")
    fig.tight_layout(); save_figure(fig, "final_model", "final_model_cv_vs_holdout")
    register("final_model_cv_vs_holdout", "Locked Model CV vs Previously Recorded Holdout", "final_model",
             source_nb, "CV versus holdout; cell 43", "saved_report_regeneration",
             ["report", "presentation"], holdout=True,
             source_report="reports/model_optimization/cv_vs_holdout.csv",
             data_csv="data/final_model/cv_vs_holdout.csv", data_json="data/final_model/cv_vs_holdout.json",
             dashboard_priority="REPORT_ONLY", notes="Historical evaluation comparison; no holdout data or prediction was reopened.")

    export_holdout_confusion(source_nb)
    export_country_robustness(source_nb, final_name)


def stored_holdout_confusion():
    """Recover raw and normalized final holdout matrices from executed NB05 output."""
    cell = notebook_cell("notebooks/05_model_optimization.ipynb", 39)
    output_text = "\n".join("".join(out.get("text", [])) for out in cell.get("outputs", []))
    raw_match = re.search(r"Raw confusion matrix:\s*\n\s*\[\[(.*?)\]\]", output_text, flags=re.S)
    norm_match = re.search(r"Normalized confusion matrix:\s*\s*\[\[(.*?)\]\]", output_text, flags=re.S)
    if not raw_match or not norm_match:
        raise AssertionError("Stored final holdout confusion output not found in Notebook 05 cell 39")
    raw_rows = re.findall(r"\[([^\[\]]+)\]", "[" + raw_match.group(1) + "]")
    # Explicitly parse the three matrix rows while ignoring line breaks/spaces.
    raw = np.array([list(map(int, re.findall(r"\d+", row))) for row in raw_rows], dtype=int)
    norm_rows = re.findall(r"\[([^\[\]]+)\]", "[" + norm_match.group(1) + "]")
    normalized = np.array([list(map(float, re.findall(r"\d+(?:\.\d+)?", row))) for row in norm_rows])
    if raw.shape != (3, 3) or normalized.shape != (3, 3):
        raise AssertionError(f"Stored matrices have unexpected shape: {raw.shape}, {normalized.shape}")
    expected = np.array([[259, 1, 7], [22, 6, 3], [13, 2, 46]])
    if not np.array_equal(raw, expected) or raw.sum() != 359:
        raise AssertionError(f"Stored holdout matrix differs from supplied prior record: {raw.tolist()}")
    if not np.allclose(normalized, raw / raw.sum(axis=1, keepdims=True), atol=5e-5, rtol=0):
        raise AssertionError("Stored normalized matrix does not agree with stored raw matrix")
    return raw, normalized


def export_holdout_confusion(source_nb):
    raw, normalized = stored_holdout_confusion()
    rows = []
    for i, actual in enumerate(CLASS_ORDER):
        for j, predicted in enumerate(CLASS_ORDER):
            rows.append({"actual": actual, "predicted": predicted,
                         "count": int(raw[i, j]), "row_normalized": float(normalized[i, j]),
                         "actual_support": int(raw[i].sum())})
    matrix_data = pd.DataFrame(rows)
    write_table(matrix_data, "data/final_model/final_holdout_confusion_matrix.csv",
                "data/final_model/final_holdout_confusion_matrix.json",
                {"source": "notebooks/05_model_optimization.ipynb cell 39 stored output",
                 "historical_recorded_result": True, "holdout_recomputed": False,
                 "class_order": CLASS_ORDER})
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    short = ["Functional", "Partial", "Abandoned"]
    for ax, matrix, title, fmt in [
        (axes[0], raw, "Recorded counts", "d"),
        (axes[1], normalized, "Recorded row proportions", ".3f"),
    ]:
        ax.imshow(matrix, cmap="Blues", vmin=0)
        for (r, c), value in np.ndenumerate(matrix):
            ax.text(c, r, format(value, fmt), ha="center", va="center", fontsize=10)
        ax.set_xticks(range(3), short, rotation=30, ha="right"); ax.set_yticks(range(3), short)
        ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title(title)
    fig.suptitle("Previously Recorded Final Holdout Confusion Matrix (n=359)")
    fig.tight_layout()
    save_figure(fig, "final_model", "final_holdout_confusion_matrix")
    register("final_holdout_confusion_matrix", "Previously Recorded Final Holdout Confusion Matrix", "final_model",
             source_nb, "One-time final holdout assessment; cell 39 stored output",
             "notebook_output_recovery", ["report", "presentation"], holdout=True,
             source_report="notebooks/05_model_optimization.ipynb cell 39 output",
             data_csv="data/final_model/final_holdout_confusion_matrix.csv",
             data_json="data/final_model/final_holdout_confusion_matrix.json",
             dashboard_priority="CORE", notes="Recovered from executed notebook output; no holdout data were reopened.")


def export_country_robustness(source_nb, final_name):
    country_all = pd.read_csv(ROOT / "reports/model_optimization/finalist_country_robustness.csv")
    locked = country_all[country_all.finalist == final_name].copy()
    if locked.empty:
        raise AssertionError("No saved leave-one-country-out results for official locked RF")
    locked = locked.sort_values("held_out_country")
    data = locked.rename(columns={
        "held_out_country": "country", "macro_f1_observed_classes": "macro_f1_observed_classes",
    })
    write_table(data, "data/robustness/country_robustness_locked_rf.csv",
                "data/robustness/country_robustness_locked_rf.json",
                {"source": "reports/model_optimization/finalist_country_robustness.csv",
                 "validation": "leave-one-country-out", "metric": "Macro-F1 over observed classes"})
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(data.country, data.macro_f1_observed_classes, color="#4678A8")
    ax.set_xlabel("Macro-F1 over observed classes"); ax.set_ylabel("Held-out country")
    ax.set_title("Locked RF: Leave-One-Country-Out Robustness")
    fig.tight_layout(); save_figure(fig, "robustness", "country_robustness_locked_rf")
    register("country_robustness_locked_rf", "Locked RF Leave-One-Country-Out Robustness", "robustness",
             source_nb, "Secondary country robustness; saved country evidence",
             "saved_report_regeneration", ["dashboard", "report", "presentation"],
             source_report="reports/model_optimization/finalist_country_robustness.csv",
             data_csv="data/robustness/country_robustness_locked_rf.csv",
             data_json="data/robustness/country_robustness_locked_rf.json", dashboard_priority="CORE",
             notes="Cross-country transfer diagnostic; not normal stratified CV or a test-set result.")


def save_figure_svg(fig, category: str, asset_id: str):
    svg = FIG[category] / f"{asset_id}.svg"
    svg.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(svg, bbox_inches="tight", facecolor="white",
                metadata={"Date": None, "Creator": "dashboard asset export"})
    fig.clear()
    plt.close(fig)
    gc.collect()


def copy_posthoc_png(asset_id: str, source_name: str):
    src = ROOT / "reports/posthoc_robustness" / source_name
    if not src.is_file() or src.stat().st_size == 0:
        raise FileNotFoundError(f"Expected saved post-hoc figure is missing: {src}")
    dest = FIG["robustness"] / f"{asset_id}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def export_posthoc():
    source_nb = "notebooks/06_posthoc_robustness.ipynb"
    base = ROOT / "reports/posthoc_robustness"
    raw = pd.read_csv(base / "raw_feature_permutation_importance.csv")
    selected = pd.read_csv(base / "selected_processed_feature_importance.csv")
    comparison = pd.read_csv(base / "posthoc_comparison.csv")
    country = pd.read_csv(base / "posthoc_country_robustness.csv")
    curves = pd.read_csv(base / "learning_curve_diagnostics.csv")
    source_files = {
        "raw_feature_permutation_importance.csv": (raw, "raw_feature_permutation_importance"),
        "selected_processed_feature_importance.csv": (selected, "selected_processed_feature_importance"),
        "posthoc_comparison.csv": (comparison, "posthoc_comparison"),
        "posthoc_country_robustness.csv": (country, "posthoc_country_robustness"),
        "learning_curve_diagnostics.csv": (curves, "learning_curve_diagnostics"),
    }
    for filename, (frame, stem) in source_files.items():
        write_table(frame, f"data/robustness/{filename}", f"data/robustness/{stem}.json",
                    {"source": f"reports/posthoc_robustness/{filename}", "values_reused_without_refitting": True})
    specs = [
        ("robustness_raw_permutation_importance", "raw_permutation_importance.png", "raw_feature_permutation_importance.csv",
         "Raw Feature Permutation Importance", "data/robustness/raw_feature_permutation_importance.csv",
         "data/robustness/raw_feature_permutation_importance.json"),
        ("robustness_selected_rf_feature_importance", "selected_feature_importance.png", "selected_processed_feature_importance.csv",
         "Selected RF Feature Importance", "data/robustness/selected_processed_feature_importance.csv",
         "data/robustness/selected_processed_feature_importance.json"),
        ("robustness_candidate_comparison", "candidate_comparison.png", "posthoc_comparison.csv",
         "Post-Hoc Candidate Comparison", "data/robustness/posthoc_comparison.csv",
         "data/robustness/posthoc_comparison.json"),
        ("robustness_learning_curves", "learning_curves.png", "learning_curve_diagnostics.csv",
         "Post-Hoc Learning Curves", "data/robustness/learning_curve_diagnostics.csv",
         "data/robustness/learning_curve_diagnostics.json"),
        ("robustness_overview", "robustness_dashboard.png", "posthoc_comparison.csv",
         "Post-Hoc Robustness Overview", "data/robustness/posthoc_comparison.csv",
         "data/robustness/posthoc_comparison.json"),
        ("robustness_train_vs_cv_macro_f1", "train_vs_cv_macro_f1.png", "posthoc_comparison.csv",
         "Post-Hoc Train vs CV Macro-F1", "data/robustness/posthoc_comparison.csv",
         "data/robustness/posthoc_comparison.json"),
    ]
    for asset_id, source_png, _, _, _, _ in specs:
        copy_posthoc_png(asset_id, source_png)

    top = raw.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(top.raw_feature, top.mean_importance, xerr=top.sd_across_folds, color="#277DA1", alpha=.85)
    ax.axvline(0, color="black", lw=.8); ax.set_xlabel("Validation Macro-F1 decrease on permutation")
    ax.set_title("Locked RF: raw feature permutation importance"); fig.tight_layout()
    save_figure_svg(fig, "robustness", specs[0][0])

    top = selected.head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(top.selected_processed_feature, top.rf_impurity_importance, color="#F8961E")
    ax.set_xlabel("RF impurity importance"); ax.set_title("Locked RF: selected processed features")
    fig.tight_layout(); save_figure_svg(fig, "robustness", specs[1][0])

    view = comparison.set_index("configuration")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].barh(view.index, view.macro_f1, xerr=view.sd_macro_f1, color="#43AA8B")
    axes[0].set_xlabel("Repeated CV Macro-F1 (mean ± fold SD)")
    axes[1].barh(view.index, view.partial_recall, color="#F3722C")
    axes[1].set_xlabel("Repeated CV Partial recall")
    fig.tight_layout(); save_figure_svg(fig, "robustness", specs[2][0])

    fig, ax = plt.subplots(figsize=(7, 4))
    for name, group in curves.groupby("configuration", sort=False):
        ax.plot(group.train_rows, group.train_macro_f1_mean, "--o", label=f"{name} train")
        ax.plot(group.train_rows, group.cv_macro_f1_mean, "-o", label=f"{name} CV")
    ax.set(xlabel="Training rows per fold", ylabel="Macro-F1", title="Development learning curves")
    ax.legend(fontsize=8); fig.tight_layout(); save_figure_svg(fig, "robustness", specs[3][0])

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, field, title in zip(axes.flat,
                                ["macro_f1", "mcc", "partial_recall", "partial_f1", "partial_ap", "mean_country_macro_f1"],
                                ["CV Macro-F1", "CV MCC", "Partial recall", "Partial F1", "Partial AP", "Mean country Macro-F1"]):
        ax.barh(view.index, view[field], color=MODEL_COLORS[:len(view)])
        ax.set_title(title); ax.set_xlim(left=0)
    fig.tight_layout(); save_figure_svg(fig, "robustness", specs[4][0])

    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(view)); width = .36
    ax.bar(x - width / 2, view.train_macro_f1, width, label="Train", color="#277DA1")
    ax.bar(x + width / 2, view.macro_f1, width, label="Validation", color="#F8961E")
    ax.set_xticks(x, view.index, rotation=20, ha="right"); ax.set_ylabel("Macro-F1"); ax.legend()
    fig.tight_layout(); save_figure_svg(fig, "robustness", specs[5][0])

    sources = {
        "robustness_raw_permutation_importance": "raw_feature_permutation_importance.csv",
        "robustness_selected_rf_feature_importance": "selected_processed_feature_importance.csv",
        "robustness_candidate_comparison": "posthoc_comparison.csv",
        "robustness_learning_curves": "learning_curve_diagnostics.csv",
        "robustness_overview": "posthoc_comparison.csv",
        "robustness_train_vs_cv_macro_f1": "posthoc_comparison.csv",
    }
    for asset_id, source_png, _, title, data_csv, data_json in specs:
        report = f"reports/posthoc_robustness/{sources[asset_id]}"
        register(asset_id, title, "robustness", source_nb,
                 "Saved Notebook-06 figures and existing post-hoc evidence", "existing_file",
                 ["dashboard", "report", "presentation"], source_report=report,
                 data_csv=data_csv, data_json=data_json,
                 dashboard_priority="CORE" if asset_id in {
                     "robustness_raw_permutation_importance", "robustness_selected_rf_feature_importance",
                     "robustness_learning_curves"} else "REPORT_ONLY",
                 notes=f"PNG copied from reports/posthoc_robustness/{source_png}; SVG regenerated from saved CSV.")


def export_all():
    before = protected_hashes()
    style()
    for path in [*FIG.values(), *DATA.values()]:
        path.mkdir(parents=True, exist_ok=True)

    # Only EDA opens the raw workbook; model/optimization values come from saved reports.
    export_eda()
    export_preprocessing_summary()
    export_model_development()
    export_optimization()
    export_posthoc()

    if protected_hashes() != before:
        raise AssertionError("A protected notebook, lock or final model changed during asset export")

    required = {
        "eda_target_class_distribution", "eda_top20_missing_values", "eda_functionality_by_country",
        "eda_key_numeric_distributions", "model_baseline_macro_f1", "baseline_vs_optimized_macro_f1",
        "baseline_vs_optimized_mcc", "finalist_repeated_cv_macro_f1",
        "model_train_vs_validation_and_mcc", "finalist_partial_class_metrics",
        "final_holdout_confusion_matrix", "country_robustness_locked_rf",
        "robustness_raw_permutation_importance", "robustness_selected_rf_feature_importance",
        "robustness_learning_curves",
    }
    found = {item["asset_id"] for item in MANIFEST}
    if not required.issubset(found):
        raise AssertionError(f"Missing mandatory assets: {sorted(required - found)}")
    if len(found) != len(MANIFEST):
        raise AssertionError("Duplicate asset IDs in manifest")

    # Confirm recorded Notebook-02 target totals, stage metrics and stored confusion support.
    target_data = pd.read_csv(DATA["eda"] / "target_class_distribution.csv")
    if target_data["count"].tolist() != [1333, 157, 303]:
        raise AssertionError("Notebook-02 target distribution differs from stored notebook output")
    final_cm = pd.read_csv(DATA["final_model"] / "final_holdout_confusion_matrix.csv")
    if int(final_cm["count"].sum()) != 359:
        raise AssertionError("Recovered final holdout confusion counts do not total 359")
    lock = json.loads((ROOT / "reports/model_optimization/final_selection_locked.json").read_text(encoding="utf-8"))
    finalist = pd.read_csv(ROOT / "reports/model_optimization/finalist_cv_summary.csv")
    locked_row = finalist[finalist.finalist == lock["finalist"]].iloc[0]
    if not np.isclose(locked_row.macro_f1, lock["primary_cv_macro_f1"], atol=1e-12):
        raise AssertionError("Optimization chart data does not agree with the official lock")

    from PIL import Image
    validation_rows = []
    for item in MANIFEST:
        for image_key in ("image_png", "image_svg"):
            rel = item[image_key]
            if not rel:
                continue
            path = ASSET_ROOT / rel
            if not path.is_file() or path.stat().st_size == 0:
                raise AssertionError(f"Empty/missing figure: {rel}")
            if rel.endswith(".png"):
                with Image.open(path) as image:
                    image.verify()
                    if image.width < 700 or image.height < 350:
                        raise AssertionError(f"PNG resolution is too small: {rel} ({image.size})")
                    dpi = image.info.get("dpi", (0, 0))
                    if item["retrieval_method"] != "existing_file" and min(dpi) < 190:
                        raise AssertionError(f"PNG DPI below required threshold: {rel} ({dpi})")
            else:
                ET.parse(path)
            validation_rows.append({"path": rel, "type": "PNG" if rel.endswith(".png") else "SVG",
                                    "bytes": path.stat().st_size, "valid": True})
        for data_key in ("data_csv", "data_json"):
            rel = item[data_key]
            if rel:
                path = ASSET_ROOT / rel
                if not path.is_file() or path.stat().st_size == 0:
                    raise AssertionError(f"Empty/missing data asset: {rel}")
                if rel.endswith(".csv"):
                    pd.read_csv(path)
                else:
                    json.loads(path.read_text(encoding="utf-8"))

    write_json("asset_manifest.json", {
        "project": "Predicting Rural Water Point Functionality Using Data Mining",
        "asset_count": len(MANIFEST), "assets": MANIFEST,
        "holdout_recomputed": False,
    })
    inventory = []
    for item in MANIFEST:
        inventory.append({
            "asset_id": item["asset_id"], "category": item["category"],
            "title": item["title"], "source_notebook": item["source_notebook"],
            "source_evidence": item["source_report_file"] or item["source_section_cell"],
            "png_path": item["image_png"], "svg_path": item["image_svg"],
            "data_path": item["data_csv"] or item["data_json"],
            "dashboard_priority": item["dashboard_priority"],
            "report_priority": "REPORT_ONLY" if "technical_report_only" in item["intended_use"] else item["dashboard_priority"],
            "status": "PASS", "notes": item["notes"],
        })
    pd.DataFrame(inventory).to_csv(ASSET_ROOT / "dashboard_asset_inventory.csv", index=False)

    validation = {
        "status": "PASS", "asset_count": len(MANIFEST),
        "mandatory_assets_present": True,
        "png_count": sum(x["type"] == "PNG" for x in validation_rows),
        "svg_count": sum(x["type"] == "SVG" for x in validation_rows),
        "all_images_valid": True, "all_data_assets_nonempty_and_parseable": True,
        "target_counts_match_notebook_02": True,
        "model_metrics_match_saved_reports": True,
        "final_confusion_support_total": int(final_cm["count"].sum()),
        "holdout_recomputed": False,
        "notebooks_model_lock_and_final_model_unchanged": True,
        "figure_validation": validation_rows,
    }
    write_json("data/export_validation.json", validation)
    print(f"Exported {len(MANIFEST)} manifest assets; {validation['png_count']} PNG and {validation['svg_count']} SVG files")
    print("Notebook hashes, lock, and final model unchanged: YES")
    print("DASHBOARD-ASSET HOLDOUT RE-EVALUATION: NONE")
    print("DASHBOARD / REPORT ASSET EXPORT: PASS")


if __name__ == "__main__":
    export_all()
