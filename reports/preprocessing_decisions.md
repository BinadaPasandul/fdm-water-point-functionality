# Preprocessing Decision Plan

**Project:** Predicting Rural Water Point Functionality Using Data Mining
**Target variable:** `functional3` (Functional / Partially functional / Abandoned or not functional)
**Task:** Multiclass classification
**Raw dataset:** `data/raw/water_pump_functionality.xlsx` (1,793 rows x 52 columns)

This document is a **decision plan only**. It is based entirely on the findings documented in [`notebooks/02_eda.ipynb`](../notebooks/02_eda.ipynb), plus additional column-level checks run to complete the feature-selection categorization (noted where they go beyond what is in the EDA notebook). **No code in this document has been applied to the raw dataset.** No columns have been dropped, no values imputed, no encoding or scaling performed. All of this is scoped for the next stage, once these decisions are reviewed and approved.

---

## 1. Summary Decision Table

| # | Issue / Variable | EDA Finding | Proposed Action | Reason | Risk / Consideration |
|---|---|---|---|---|---|
| 1 | **Duplicate records** | 0 fully duplicated rows (0.0%) — EDA §6 | No action needed | Nothing to remove | None |
| 2 | **Missing values** | 40/52 columns have missing values, ranging 0.06%–99.0%; much of it is structural (e.g. `rehab_age` 100% missing when `rehabyn`="No") — EDA §5 | Column-specific strategy: "Not applicable" category, missing-indicator, or drop, depending on the mechanism (see Section 3) | A single blanket strategy would misrepresent structurally-missing fields as if they were unknown | Wrong strategy could inject false signal (e.g. imputing a rehab age for water points never rehabilitated) |
| 3 | **Invalid values** | `wc_savings_wp` contains values 1.0 (n=869) and 0.0 (n=236) that look like a binary yes/no, plus 999.0 (n=84) and 888.0 (n=2) that look like survey sentinel codes ("don't know"/"other"), not genuine savings amounts (checked beyond the EDA notebook) | Recode 999/888 as an explicit missing/"Unknown" category rather than treating them as numeric magnitudes | Treating 999 as a numeric value would badly distort any mean/scaling computed on this column | If missed, this single column could silently corrupt scaling or imputation statistics |
| 4 | **Outliers** | IQR-flagged extremes in `wp_age`, `qtypeople_wp`, `qtyhh_wp`, `minutesfill20l`, `brokendays_wp`, `qtymonthsnowater_wp`, `pumpstrokes`; `elevation_wp` has 107 negative values (106 in West Bengal, India) — EDA §9 | No removal. Classify per variable (Section 4) and revisit only where evidence is strong (e.g. `elevation_wp`) | EDA explicitly found most extremes plausible; premature removal risks discarding real signal | Removing "outliers" that are actually valid (e.g. a 74-year-old water point) would bias the dataset |
| 5 | **Target variable** | `functional3`: Functional 1,333 (74.34%), Abandoned or not functional 303 (16.90%), Partially functional 157 (8.76%) — EDA §4 | Keep all 3 classes as-is; no merging of classes | The 3-class structure is the assignment's defined task | Merging classes would change the problem definition without justification |
| 6 | **Potential target leakage** | `wateravailable`, `whynowatertoday_wp` (+`_other`), `downtime2weeks`, `minutesfill20l`, `brokendays_wp`, `qtymonthsnowater_wp` all show near-perfect or very strong class separation — EDA §12 | Exclude all 6 from the predictive feature set | These variables describe current/recent water availability — essentially a restatement of the target | Keeping any of them would make offline accuracy look artificially high and the model useless in practice |
| 7 | **Identifier columns** | `id` (1,793 unique), `instance_wp` (1,793 unique), `photo_wp` (1,792 unique), `commid_wp` (1,395 unique), `cwid` (948 unique, 46.5% missing) all have very high/near-total cardinality relative to row count | Exclude all from the predictive feature set | Row-level identifiers and a photo URL carry no generalizable signal and risk the model "memorizing" rows | None if excluded; if kept, high risk of overfitting/data leakage between train and test via ID-correlated artifacts |
| 8 | **Categorical variables** | 32 categorical columns; several nominal (`country`, `wptype`, `pumptype`), several binary (`rehabyn`, `season`, `wateravailable`), some ordinal-looking (`wc_*_index_wp`: Inadequate/Minimum/Moderate/Advanced); several with rare categories (n<5) — EDA §8 | Encode by type: one-hot for low-cardinality nominal, binary mapping for Yes/No fields, ordinal encoding for the `wc_*_index_wp` scale, grouped "Other" bucket for rare categories | Matches encoding to the actual structure of each variable rather than one generic approach | One-hot on rare categories creates unstable, near-empty columns |
| 9 | **Numerical variables** | `wp_age`, `qtypeople_wp`, `qtyhh_wp`, `pop_1000` are strongly right-skewed (skew 2.96–4.14); `annual_rain`, `elevation_wp` close to symmetric — EDA §7 | Scale only if a scale-sensitive algorithm (KNN, SVM, logistic regression) is used; consider log-transform for the most skewed variables in that case | Tree-based models (planned as a likely candidate given mixed types and outliers) do not require scaling | Scaling raw skewed data for a distance-based model without transformation can let large-magnitude variables dominate distance calculations |
| 10 | **Class imbalance** | Functional 74.34% vs. Partially functional 8.76% — EDA §4 | Do not resample yet. Plan to evaluate with macro-F1 / per-class precision-recall / confusion matrix; consider `class_weight="balanced"` or resampling only if evaluation shows the minority classes are poorly learned | Accuracy alone would be misleading on this distribution | Resampling before evaluating the plain baseline could mask whether it was actually needed |
| 11 | **Feature engineering opportunities** | See Section 6 for the full list and justification (e.g. `wp_age` grouping, people-per-household ratio) | Propose only, no implementation yet | Each proposal ties to a concrete EDA finding | Engineered features must be built from train-only statistics where they involve any aggregation, to avoid leakage |
| 12 | **Feature selection** | Full column-by-column categorization in Section 7 | Categorize into predictors / leakage / identifiers / high-missingness / redundant, not yet finalized into a drop list | Selection should combine domain meaning, leakage risk, missingness, redundancy, and cardinality — not target correlation alone | Over-aggressive removal at this stage could discard variables that turn out useful once properly encoded |

---

## 2. Target Leakage — Detailed Reasoning

The task explicitly asked to focus on `wateravailable`, `minutesfill20l`, and `downtime2weeks`. EDA Section 12 investigated these plus additional "current status" variables and found the following (counts are from the raw dataset, 1,793 rows):

| Variable | Evidence (from EDA §12) | Exclude? |
|---|---|---|
| `wateravailable` | "No" -> 300 Abandoned + 2 Partially + 0 Functional; "Yes" -> 1,333 Functional + 155 Partially + 3 Abandoned | **Yes** |
| `whynowatertoday_wp` (+ `whynowatertoday_wp_other`) | Non-missing for 300/303 Abandoned and 2/157 Partially functional, but 0/1,333 Functional — the *missingness itself* reveals the class | **Yes** |
| `downtime2weeks` | "Yes" -> 272 Abandoned + 81 Partially + 1 Functional; "No" -> 30 Abandoned + 76 Partially + 1,332 Functional | **Yes** |
| `minutesfill20l` | Mean 1.45 min (Functional) vs. 98.4 min (Partially functional); only 1 non-null value for Abandoned (nothing to time when there's no water) | **Yes** |
| `brokendays_wp` | Mean 429.8 days (Abandoned) vs. 27.2 (Functional) vs. 50.0 (Partially functional) | **Yes** |
| `qtymonthsnowater_wp` | Mean 2.51 months (Abandoned) vs. 0.13 (Functional) vs. 0.53 (Partially functional) | **Yes** |
| `lockedfullday_wp` | Similar class proportions regardless of value (18.4% vs. 11.7% abandoned) — checked in EDA §12 and found **not** to behave like the variables above | No — kept as a candidate predictor |

**Additional variables reviewed here (beyond the EDA notebook) for the same reason — because they may reveal, be derived from, or not realistically be available for, the target:**

| Variable | Concern | Evidence | Recommendation |
|---|---|---|---|
| `id`, `instance_wp`, `photo_wp`, `commid_wp`, `cwid` | Row-level identifiers, not predictive attributes | Cardinality near or equal to the row count (1,793 / 1,793 / 1,792 / 1,395 / 948) | Exclude — identifiers, not leakage per se, but carry no generalizable signal (see Section 7, category D) |
| `timepoint_wp` | Describes which survey sample/wave a record belongs to ("Grant endline: new construction" vs. "Post-implementation monitoring: older construction"), not an inherent property of the water point | Mean `wp_age` is 1.77 years for "new construction" records vs. 5.87 years for "older construction" records (checked beyond the EDA notebook) — this is a study-design artifact, not something a real-world prediction system would have as an independent input | Exclude, or at minimum do not treat as a general-purpose predictor — it encodes the *sampling design*, not a property that generalizes beyond this dataset |
| `wc_admin_index_wp`, `wc_finance_index_wp`, `wc_mgmt_index_wp`, `wc_maint_index_wp` | These committee-capacity ratings (Inadequate/Minimum/Moderate/Advanced) were not deeply profiled against the target in the EDA notebook, but conceptually a surveyor's rating of "maintenance capacity" could be influenced by whether the point is currently broken (circular with the target) | Not yet checked against `functional3` — flagged for a leakage check before being used as a feature | **Requires investigation before use** — not excluded outright, but should not be added to the feature set without first checking association with the target the same way `wateravailable` was checked |
| `dataorg_wp` | Not leakage, but functionally redundant | Checked beyond the EDA notebook: `dataorg_wp` maps 1-to-1 onto `country` (e.g. every `ET.RST` record is Ethiopia, every `IN.WFP` record is India) | Exclude in favor of `country`, or keep only one of the two |

---

## 3. Missing-Value Strategy

No single strategy applies to all 40 columns with missing values. Based on EDA §5 and the mechanism behind each column's missingness:

| Pattern | Example columns | Missingness mechanism (from EDA) | Proposed strategy |
|---|---|---|---|
| **Structurally missing — conditional on another field** | `rehab_age` (84.4% missing), `piped_source`/`piped_pump` (68.0%), `pumptype` (34.4%), `drillmethod` (33.5%) | EDA §5 showed `rehab_age` is missing for 100% of `rehabyn`="No" records — the field does not apply, rather than being unknown. The same logic plausibly extends to pump/piped fields, which only apply to certain `wptype` values. | Encode as an explicit **"Not applicable"** category (categorical) or **0 + missing-indicator flag** (numeric, e.g. `rehab_age`), instead of mean/median/mode imputation which would imply the condition applies when it does not. |
| **Very high missingness, low remaining information** | `whynowatertoday_wp_other` (99.0%), and — once leakage variables are excluded — `whynowatertoday_wp` itself is dropped anyway | Almost no data present, and the column is already excluded as a leakage source | Drop (already excluded under leakage; would have been a drop candidate on missingness grounds regardless) |
| **Moderate missingness, plausibly informative** | `grant_number_wp` (69.5%), `balance_any_dollars_wp` (47.6%), `cwid` (46.5%), `wc_*_index_wp` (37.5% each), `wc_savings_wp` (33.6%), `wpqty_wp`/`qtyhh_c_wp`/`improved_wponly_wp`/`wc_present_wp`/`paytocollect_wp` (33.35% each), `pop_1000` (31.5%), `annual_rain`/`season` (30.5%) | Not yet individually traced to a specific conditional field the way `rehab_age` was; missingness appears batch-like (several columns share exactly 598 or 673 missing, suggesting these were skipped together for a subset of surveys) | For categorical: explicit "Unknown" category. For numerical: median imputation **plus** a missing-indicator column, so the model can distinguish "imputed" from "observed". Do not assume these are random without checking further in the preprocessing notebook. |
| **Low missingness, likely closer to random** | `downtime2weeks`, `whomanage_wp` (0.06% each), `cwfunded_wp` (0.73%), `wp_age` (0.95%), `latitude_wp`/`longitude_wp` (1.45% each), `admin2` (1.84%), `qtypeople_wp` (2.12%), `qtyhh_wp` (3.07%), `lockedfullday_wp` (4.02%), `elevation_wp` (7.53%), `qtymonthsnowater_wp` (9.43%), `admin3` (11.21%) | No specific structural cause identified; low enough volume that simple imputation is unlikely to distort the data materially | Median (numeric) or mode (categorical) imputation is reasonable here, given the small proportion affected. |
| **Invalid-value cleanup needed before imputation** | `wc_savings_wp` | Values include 999.0 (n=84) and 888.0 (n=2), which look like survey sentinel codes rather than genuine savings figures (checked beyond the EDA notebook) | Recode 999/888 to missing/"Unknown" **before** computing any imputation statistic or scaling for this column. |

All strategies above are proposals. The specific imputation values (e.g. which median) must be **fit on the training split only** — see Section 8.

---

## 4. Outlier Treatment Plan

Directly carried over from EDA §9's classification — no new removal decisions are made here:

| Variable | Classification (EDA §9) | Proposed treatment |
|---|---|---|
| `wp_age` (up to 74 years) | Potentially valid extreme observation | No transformation planned beyond the scaling/skew handling in Section 5 |
| `qtypeople_wp` / `qtyhh_wp` (up to 5,000 / 800) | Requires further investigation | Keep as-is for now; flag for a sanity check against `wptype` (e.g. do extreme values cluster in piped systems serving multiple communities?) before any capping decision |
| `minutesfill20l` | Requires further investigation | Moot for modeling — already excluded as a leakage variable (Section 2) |
| `brokendays_wp` (up to 3,650 days) | Potentially valid extreme observation | Moot for modeling — already excluded as a leakage variable |
| `elevation_wp` (min -217m, 107 negative values, 106 in West Bengal) | Potential data-quality issue | Do not correct blindly. Plan to cross-check a sample of the West Bengal coordinates against a reference elevation source during preprocessing before deciding to cap, correct, or leave as-is |
| `pop_1000` (up to ~9,413) | Potentially valid extreme observation | No transformation planned beyond skew handling |
| `pumpstrokes` (up to 95) | Requires further investigation | Keep as-is; flag for a unit-consistency check (e.g. does 95 make sense as "strokes to fill a container" vs. a different unit entirely) |

**No values will be removed or capped without this being made an explicit, documented step in the next (preprocessing implementation) notebook.**

---

## 5. Categorical Encoding Strategy (proposed, not implemented)

| Variable type | Examples | Proposed encoding | Reason |
|---|---|---|---|
| Binary (Yes/No or two-level) | `rehabyn`, `season`, `cwfunded_wp`, `wc_present_wp`, `paytocollect_wp`, `lockedfullday_wp` | Map to 0/1, with an explicit category or indicator for missing values (not silently imputed into one of the two levels) | Simple, avoids inventing a third meaning within the same 0/1 column |
| Low-cardinality nominal | `country` (9), `wptype` (9), `pumptype` (7), `drillmethod` (3), `piped_source` (3), `piped_pump` (4) | One-hot encoding | No inherent order; cardinality is low enough that one-hot stays manageable |
| Nominal with rare categories | `whomanage_wp` (11 categories, several with n<5), `wptype`'s rarest levels (n=1-4) | Group categories below a minimum count threshold (e.g. n<10) into an explicit "Other" category before one-hot encoding | Prevents near-empty one-hot columns that provide unstable signal (EDA §8 already flagged these categories as too small to interpret reliably) |
| Ordinal-looking | `wc_admin_index_wp`, `wc_finance_index_wp`, `wc_mgmt_index_wp`, `wc_maint_index_wp` (Inadequate < Minimum < Moderate < Advanced) | Ordinal integer encoding (0-3), *pending* the leakage check noted in Section 2 | These have a natural order, so one-hot would discard that structure; but they must be confirmed leakage-free before being used at all |
| High-cardinality administrative | `admin1` (15), `admin2` (30), `admin3` (108, 11.2% missing) | Likely keep `admin1` (moderate cardinality) with one-hot or target/frequency encoding; treat `admin2`/`admin3` as candidates for exclusion or a higher-level grouping, to avoid excessive dimensionality relative to 1,793 rows | `admin3` alone would add over 100 columns via one-hot for a dataset of fewer than 1,800 rows |
| Excluded from encoding entirely | Leakage variables (Section 2), identifiers (Section 7-D) | Not encoded | No predictive role |

---

## 6. Numerical Scaling Strategy (proposed, not implemented)

- **Algorithm dependency:** Scaling is only necessary for distance-based or gradient-based algorithms sensitive to feature magnitude (KNN, SVM, logistic regression, neural networks). Tree-based models (Decision Tree, Random Forest, Gradient Boosting) — strong candidates here given the mix of skewed numeric and categorical variables plus the outliers noted in Section 4 — do not require scaling.
- **If a scale-sensitive model is used:** Standardize (`StandardScaler`) or normalize numerical predictors, fit on the training split only (Section 8).
- **Skew handling:** `wp_age`, `qtypeople_wp`, `qtyhh_wp`, and `pop_1000` are strongly right-skewed (skew 2.96-4.14, EDA §7). If used with a linear/distance-based model, a log-transform (e.g. `log1p`) is a reasonable candidate to reduce skew before scaling. This is not needed for tree-based models, which are not sensitive to monotonic transformations.
- **Variables not requiring scaling consideration:** `annual_rain` and `elevation_wp` are already close to symmetric (skew 0.47 and 0.60, EDA §7).

---

## 7. Feature Engineering Opportunities (proposed, not implemented)

Each proposal below is tied to a specific EDA observation, not created for its own sake:

| Proposed feature | Derived from | Justification |
|---|---|---|
| `wp_age_group` (e.g. binned into "new" / "established" / "old") | `wp_age` | EDA §7/§10 found `wp_age` strongly right-skewed and showed a mild association with the target (mean 5.53 years for Abandoned vs. 4.35 for Functional). A grouped version may capture this pattern more robustly than the raw skewed value for models sensitive to scale, and is easier to interpret in a report. |
| `was_rehabilitated` (binary, from `rehabyn`) + keep `rehab_age` only as a numeric feature **conditional** on that flag | `rehabyn`, `rehab_age` | EDA §5 established that `rehab_age` is structurally missing when no rehabilitation occurred. Explicitly separating "was it rehabilitated" from "how long ago" avoids forcing a single numeric column to carry both meanings. |
| `people_per_household` = `qtypeople_wp` / `qtyhh_wp` | `qtypeople_wp`, `qtyhh_wp` | EDA §11 found these two variables strongly correlated (r=0.82). A ratio captures average household size, which may be more informative than either raw count alone, while reducing redundancy (Section 1, row 9 and Section 8, category F). |
| `has_management_committee` (binary, from `whomanage_wp` == "Water committee" vs. other/none) | `whomanage_wp` | EDA §10 found the small "No one" category (n=11) had a strikingly high abandonment rate (72.7%). A simplified binary flag ("has any designated management" vs. "none") may generalize better than the full 11-category variable, whose rarer levels have very few observations. |
| `country_abandonment_rate` or similar aggregated regional statistic | `country` | EDA §10 found `country` strongly associated with functionality (Ethiopia 31.9% abandoned vs. Mozambique 2.6%). **Caution:** if built as a target-derived statistic (e.g. mean historical abandonment rate per country), this must be computed from the **training split only** and merged into the test split, to avoid target leakage through aggregation (see Section 8). |

No engineered feature above has been created in code. Each would need to be implemented and validated (e.g. checked for leakage, checked for missing-value interactions) during the preprocessing implementation stage.

---

## 8. Initial Feature Selection Categorization

All 52 columns, categorized. This is a starting point for discussion, not a final drop list.

### A. Target
- `functional3`

### B. Potential predictors (candidates for the feature set, pending encoding/missing-value treatment)
`country`, `admin1`, `wptype`, `pumptype`, `drillmethod`, `rehabyn`, `rehab_age`, `whomanage_wp`, `wp_age`, `qtypeople_wp`, `qtyhh_wp`, `season`, `annual_rain`, `elevation_wp`, `pop_1000`, `latitude_wp`, `longitude_wp`, `lockedfullday_wp`, `cwfunded_wp`, `wc_present_wp`, `paytocollect_wp`, `piped_source`, `piped_pump`, `improved_wponly_wp`, `wpqty_wp`, `qtyhh_c_wp`, `pumpstrokes`

### C. Leakage candidates (exclude — see Section 2)
`wateravailable`, `whynowatertoday_wp`, `whynowatertoday_wp_other`, `downtime2weeks`, `minutesfill20l`, `brokendays_wp`, `qtymonthsnowater_wp`

### D. Identifier / administrative / survey-design columns (exclude — see Sections 2 and 7)
`id`, `instance_wp`, `photo_wp`, `commid_wp`, `cwid`, `subdate_wp`, `dataorg_wp` (redundant with `country`), `timepoint_wp` (survey-wave artifact), `admin2`, `admin3` (very high cardinality relative to dataset size; `admin1` retained instead)

### E. High-missingness variables requiring further investigation before inclusion
`grant_number_wp` (69.5% missing, also only 10 distinct values — likely a program code, not a continuous variable), `balance_any_dollars_wp` (47.6%), `wc_admin_index_wp` / `wc_finance_index_wp` / `wc_mgmt_index_wp` / `wc_maint_index_wp` (37.5% each, and flagged in Section 2 for a leakage check before use), `wc_savings_wp` (33.6%, and contains sentinel values 999/888 needing cleanup per Section 3)

### F. Potentially redundant variables
- `qtyhh_wp` vs. `qtypeople_wp` (r=0.82, EDA §11) — candidate to keep only one, or replace both with the `people_per_household` ratio proposed in Section 7.
- `dataorg_wp` vs. `country` (1-to-1 mapping, checked beyond the EDA notebook) — redundant, already listed under category D.
- `qtyhh_c_wp` vs. `qtyhh_wp` (correlation only 0.28, checked beyond the EDA notebook) — **not** strongly redundant despite similar naming; needs a definitional check (e.g. "households at construction" vs. "current households") before deciding whether both add value.
- `latitude_wp` / `longitude_wp` vs. `country`/`admin1` — raw coordinates are near-unique (1,764-1,766 distinct values) and risk the model effectively memorizing individual locations rather than learning a generalizable regional effect; using `country`/`admin1` instead (or alongside, with regularization in mind) is likely safer.

**No columns have been dropped from any dataframe.** This categorization is the input to the feature-selection step of the preprocessing implementation, where final inclusion/exclusion will be decided and documented in code.

---

## 9. Train/Test Leakage Prevention Strategy

The preprocessing implementation will follow this fixed order, so that no statistic derived from the test data ever influences training:

```
Raw data (data/raw/water_pump_functionality.xlsx)
        |
        v
Separate features (X) and target (y = functional3)
        |
        v
Train/test split (stratified on functional3, given the class imbalance
noted in Section 1, row 10)
        |
        +--> Training split -----------------+--> Testing split
             |                                |
             v                                v
   Fit ALL data-dependent steps         Apply the SAME fitted
   on the training split ONLY:          transformations to the
     - missing-value imputers           test split (transform
       (medians, modes, "Not            only — never re-fit):
       applicable" categories)             - imputers
     - the "Other" category threshold      - encoders
       for rare categorical levels          - scalers
     - one-hot / ordinal encoders            - any engineered
     - any scaler (if used)                    feature that involves
     - any target-derived aggregate              an aggregate statistic
       feature (e.g. country-level                (e.g. country rate,
       abandonment rate proposed in                looked up from the
       Section 7)                                  training-fitted table)
             |
             v
   Train model on transformed training data
```

Key rules this enforces:
- **Imputation statistics** (e.g. the median used for `wp_age`) are computed from the training split only, then applied unchanged to the test split — never recomputed on the full dataset beforehand.
- **Rare-category grouping** ("Other" bucket, Section 5) uses category frequencies from the training split only, since frequency depends on which rows happen to be in the split.
- **Any aggregated/engineered feature that summarizes the target** (e.g. `country_abandonment_rate` proposed in Section 7) is especially high-risk: it must be computed only from training-split target values and then merged onto the test split by key (e.g. by `country`), never recomputed using rows or target values from the test split.
- **The leakage variables identified in Section 2** are removed before this pipeline even begins, since no split-based safeguard fixes a variable that restates the target itself.
- A `scikit-learn` `Pipeline`/`ColumnTransformer` (or equivalent explicit train-then-transform code) will be used in the implementation stage specifically because it enforces "fit on train, transform on train and test" by construction, reducing the chance of accidentally fitting on the full dataset.

This section describes the planned workflow only — no split, imputer, encoder, or scaler has been created or fit yet.
