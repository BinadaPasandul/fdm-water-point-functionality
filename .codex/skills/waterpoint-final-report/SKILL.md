---
name: waterpoint-final-report
summary: Create, audit, and refine the final IT3051 technical report for the Rural Water Point Functionality project. Use the approved assignment requirements, current executed notebooks/results, production model metadata, backend/frontend implementation, exported figures, and the supplied Word template while preserving historical experiment integrity.
---

# WaterPoint Final Technical Report Skill

Use this skill whenever creating, editing, validating, or exporting the final technical report for:

**Predicting Rural Water Point Functionality Using Data Mining**

The final deliverable is an academically written Microsoft Word report grounded in the actual project repository. The report must explain the complete data-mining lifecycle and integrated prediction system, not merely summarize notebook cells.

## 1. First actions

Before writing anything:

1. Inspect the repository tree.
2. Locate and read the IT3051 assignment brief.
3. Locate and read the approved dataset proposal.
4. Read the current executed notebooks in numerical order, including model development, optimization, and post-hoc robustness notebooks if present.
5. Inspect saved experiment/result artifacts under `reports/`.
6. Inspect `models/final_model_metadata.json` and the final inference artifact/export code.
7. Inspect backend source and tests.
8. Inspect frontend source and tests/screenshots.
9. Inspect `reports/dashboard_assets/asset_manifest.json` and the exported figures/data.
10. Inspect the supplied sample final report only as a structural/depth reference.
11. Inspect `docs/report/template.docx` (or the actual template path given by the task) and use it as the Word visual shell.

Do not begin drafting the final report until these sources have been inventoried.

## 2. Source authority and conflict resolution

Use this priority when sources disagree:

1. **IT3051 assignment brief** — authoritative for mandatory deliverables and report coverage.
2. **Current executed notebooks and saved final experiment outputs** — authoritative for actual methodology, experiments, metrics, and chronology.
3. **Locked final-model metadata and production inference code** — authoritative for the deployed model configuration and inference contract.
4. **Backend/frontend source and tests** — authoritative for the implemented application architecture and behavior.
5. **Exported report/dashboard assets and manifests** — authoritative reusable visualization artifacts when they match the executed notebooks.
6. **Dataset proposal** — authoritative for approved scenario, dataset source, original problem framing, users, and initial plan; not authoritative for final modelling decisions that later changed.
7. **Early viva/preparation documents** — historical context only; never allow them to override later executed notebooks.
8. **Sample final report** — layout, chapter flow, academic depth, and presentation reference only. Never copy its domain content, results, wording, figures, or citations.

If two current high-authority sources conflict, stop and report the conflict rather than silently choosing a value.

## 3. Historical integrity rules

The report must preserve the real experimental timeline.

- Baseline model development happens before optimization.
- Model selection must be based only on development/CV evidence available before the final holdout was opened.
- The one-time historical holdout evaluation is reported only after the final model was locked.
- Never imply that holdout results were used to tune or select the final model.
- Post-hoc robustness experiments occur after the Stage-7 final selection and must be labelled **post-hoc**.
- Post-hoc results must not rewrite the original model-selection story.
- Do not retrain, retune, reopen, or reevaluate the holdout simply to write the report.
- Prefer stored executed outputs and exported figures.

Ignore obsolete/superseded notes if they claim a different final configuration. In particular, any old audit describing a 500-tree Random Forest, `max_depth=20`, ~0.6811 holdout Macro-F1, or 110 final processed features is not the current final Stage-7 result and must not be used unless the current notebooks explicitly show that the project reverted to it.

## 4. Locked project facts to cross-check

These are guardrails from the completed project history. Verify them against the repository before publication. If the repository materially disagrees, flag the mismatch.

- Dataset: 1,793 water points, 52 raw variables, 9 countries.
- Target: `functional3` with three classes: Functional, Partially functional, Abandoned or not functional.
- Approximate class distribution: 74.3% Functional, 8.8% Partially functional, 16.9% Abandoned/not functional.
- Production raw predictor count: 32.
- Development/holdout split: 1,434 / 359, stratified, random state 42.
- Primary model-selection metric: Macro-F1 due class imbalance.
- Stage-6 model families: Logistic Regression, Random Forest, HistGradientBoosting, XGBoost, CatBoost.
- Stage-6 shortlist: HistGradientBoosting, XGBoost, Random Forest.
- Final selected model: Random Forest using `tree_base` preprocessing, rare-category threshold 10, `SelectKBest(mutual_info_classif, k=60)`, no imbalance treatment.
- Final RF parameters expected: `n_estimators=336`, `max_depth=None`, `max_features=0.5`, `min_samples_split=8`, `min_samples_leaf=5`, `bootstrap=False`, `random_state=42`.
- Final repeated-CV Macro-F1 expected: ~0.6996 ± 0.0481.
- Historical holdout expected: Macro-F1 ~0.6699, balanced accuracy ~0.6392, MCC ~0.6466, accuracy ~0.8663.
- Historical holdout class results expected approximately:
  - Functional: P 0.8810 / R 0.9700 / F1 0.9234
  - Partially functional: P 0.6667 / R 0.1935 / F1 0.3000
  - Abandoned/not functional: P 0.8214 / R 0.7541 / F1 0.7863
- Historical holdout confusion matrix expected in class order Functional / Partial / Abandoned:
  `[[259, 1, 7], [22, 6, 3], [13, 2, 46]]`.
- Post-hoc robustness conclusion: no tested post-hoc candidate provided enough evidence to replace the locked Random Forest.
- Production artifact expected: `models/final_inference_pipeline.joblib` with metadata in `models/final_model_metadata.json`.
- Production pipeline should accept 32 raw predictors and contain the same trained preprocessing + feature selection + classifier used for deployment.
- Backend: FastAPI.
- Frontend: Next.js/TypeScript, direct HTTP/JSON to FastAPI; frontend must not load joblib or duplicate preprocessing.

These facts are cross-check anchors, not permission to bypass reading the repository.

## 5. Final excluded-feature decisions

Use the final current preprocessing notebook as authority. The completed project history indicates that the following were excluded from the final predictor set:

- Leakage: `wateravailable`, `whynowatertoday_wp`, `whynowatertoday_wp_other`, `downtime2weeks`, `minutesfill20l`, `brokendays_wp`, `qtymonthsnowater_wp`.
- Identifier/administrative: `id`, `instance_wp`, `photo_wp`, `commid_wp`, `cwid`, `timepoint_wp`, `dataorg_wp`, `subdate_wp`, `admin2`, `admin3`.
- Pending investigation/not used: `grant_number_wp`, `balance_any_dollars_wp`.

Some early viva notes made different decisions for a few of these variables. Those early notes are superseded by the final executed preprocessing notebook.

## 6. Report structure

Use this structure unless the assignment/template requires a minor adjustment:

Front matter:
- Cover page
- Declaration if required by the course/template convention
- Abstract
- Keywords
- Table of Contents
- List of Figures
- List of Tables
- List of Abbreviations

Main chapters:
1. Introduction
2. Background and Related Concepts
3. Dataset Description and Validation
4. Exploratory Data Analysis
5. Data Preprocessing
6. Feature Engineering and Feature Selection
7. Modelling Methodology
8. Results, Optimization and Final Model Selection
9. Model Robustness and Interpretation
10. System Design and Implementation
11. System Testing
12. Discussion
13. Ethical, Legal and Operational Considerations
14. Limitations
15. Future Work
16. Conclusion

Then:
- References
- Appendices

Keep backend and frontend as substantive subsections under System Design and Implementation unless the assignment or final content density clearly benefits from separate chapters.

## 7. Required chapter content

### Introduction
Explain the rural water infrastructure problem, why delayed identification of failing water points matters, the prediction objective, aim/objectives, scope, stakeholders, contributions, and report organization.

### Background and Related Concepts
Keep this concise and relevant. Cover rural water-point monitoring, multiclass classification, class imbalance, leakage, cross-validation/holdout testing, and brief rationale for the candidate algorithms. Do not turn this into a long generic literature review.

### Dataset
Document OpenWashData source, licensing, 1,793 records, 52 raw variables, 9 countries, target definition, predictor groups, dataset suitability, and validation. Use a compact dataset-profile table.

### EDA
Show evidence on target imbalance, missingness, duplicates/invalid values, numerical distributions/outliers, categorical patterns, functionality by country, numeric-vs-target relationships, correlation, and leakage. End with an explicit **Finding -> Design Decision** table.

### Preprocessing
Explain the leakage-safe order of operations, stratified split, missing-value strategies, `wc_savings_wp` sentinel handling, structural vs unknown categorical missingness, ordinal encoding, one-hot encoding/rare categories, family-specific scaling/log choices, and why outliers were not automatically deleted/capped.

### Feature Engineering/Selection
Explain engineered features that were evaluated, base-vs-engineered comparison, and the later mutual-information `SelectKBest(k=60)` result. Make clear that the final locked model used the base feature representation plus selected processed features.

### Modelling Methodology
Explain repeated stratified CV, OOF evidence, Macro-F1 as primary metric, supporting metrics, model families, model-family preprocessing pairing, hyperparameter search strategy, imbalance experiments, and final evaluation protocol.

### Results/Optimization
Report all five model families in the baseline comparison, not only the three finalists. Then show shortlist -> tuning -> imbalance experiments -> rare-threshold/feature-selection experiments -> final three-way comparison -> final RF selection -> one-time holdout evaluation. Keep CV and holdout clearly separated.

### Robustness/Interpretation
Use post-hoc evidence: raw permutation importance, selected RF importance, coordinate ablation, SMOTENC experiment, learning curves, and country-level/leave-one-country-out robustness. State that importance is predictive reliance, not causation.

### System Design/Implementation
Document the real implemented architecture: Next.js frontend -> FastAPI backend -> verified serialized production pipeline. Explain model loading, metadata/checksum validation, 32-field schema, prediction probabilities, dashboard evidence API, frontend pages, and one-source-of-truth principle.

### Testing
Summarize production-pipeline parity/reload checks, backend API tests, frontend tests/build verification, invalid/null/unseen-category behavior, and end-to-end prediction flow. Do not invent latency/performance measurements unless actually recorded.

### Discussion
Interpret the model rather than repeating tables. Address why RF performed well, the difficult Partial class, overfitting/generalization improvements, trade-offs in imbalance treatment, geographic predictive power vs unseen-country transfer, and stakeholder value.

### Ethics/Operations
Present the system as decision support, not a replacement for field inspection. Discuss uncertainty, potential geographic bias/transfer limitations, dataset licensing, responsible use, and reproducibility/auditability.

### Limitations/Future Work
Ground every limitation in actual evidence. Important likely limitations: small dataset, class imbalance, low Partial recall, missingness, cross-country heterogeneity, weaker unseen-country transfer, probability calibration not established, and lack of a completely independent external dataset matching the production schema.

## 8. Figure policy

Prefer existing exported report/dashboard figures over recreating plots.

Inspect `reports/dashboard_assets/asset_manifest.json` and inventory files first.

Recommended main-body figures include, when present:
- target class distribution
- top missing values
- functionality by country
- one strong numeric/categorical relationship figure
- leakage diagnostic
- preprocessing/production-pipeline diagram
- baseline Macro-F1 comparison
- base-vs-engineered ablation
- train-vs-validation/MCC
- baseline-vs-optimized comparison
- finalist repeated-CV Macro-F1
- Partial-class metrics
- final historical holdout confusion matrix
- raw permutation importance
- learning curves
- country robustness
- system architecture diagram
- prediction UI screenshot
- prediction result/dashboard screenshot

Keep roughly 16-20 high-value figures in the main report. Move secondary evidence to appendices.

For every figure:
1. Verify its source and experiment stage.
2. Insert a high-resolution PNG where available.
3. Add a numbered academic caption.
4. Refer to it in the text before or near the figure.
5. Explain the observation and implication.
6. Do not use figures decoratively.

Do not rerun holdout evaluation to regenerate a missing figure. Use saved output or the recorded exported asset.

## 9. Table policy

Prefer compact evidence-rich tables. Important tables normally include:
- stakeholder/system requirements
- dataset profile
- class distribution
- excluded features and reasons
- preprocessing by feature type
- candidate algorithms and rationale
- baseline comparison
- optimization/search summary
- finalist comparison
- final RF configuration
- final holdout per-class metrics
- technology stack
- API endpoints
- system testing summary
- limitations and implications
- team work allocation

Do not paste giant DataFrames into the main report.

## 10. Word template rules

Use the supplied Word template as the base document rather than rebuilding the visual shell from scratch.

The supplied template uses an A4 page, approximately 2 cm margins, an SLIIT-branded header banner, and a centered footer with a dynamic PAGE field. Preserve the visual header/banner on all report pages unless the template requires a different first-page header.

Replace template-specific IT3041 content with IT3051 report content.

Recommended footer text:
`IT3051 | Fundamentals of Data Mining | Mini Project Final Report | Page {PAGE}`

Do not hard-code page numbers.

Cover page should use the template's visual identity but replace its title fields with:
- `Mini Project Final Report`
- `Predicting Rural Water Point Functionality Using Data Mining`
- `Fundamentals of Data Mining (IT3051)`
- `Group Mini Project`
- optional system label: `WaterPoint Intelligence - Rural Water Point Functionality Decision-Support System`

Use a clean table for group details. Never invent group member names/IDs, lecturer name, batch, or submission date; leave clearly marked placeholders if the repository does not contain them.

## 11. Document formatting

Maintain a professional academic style consistent with the template/sample:
- A4 portrait by default.
- Approximately 2 cm margins unless the template specifies otherwise.
- Times New Roman is acceptable and consistent with the supplied template cover; use one body font consistently.
- Body text around 11-12 pt.
- 1.15-1.5 line spacing depending on fit/readability; keep one value consistently.
- Body text justified unless tables/captions require otherwise.
- Heading 1 ~15-16 pt bold in dark navy.
- Heading 2 ~12-13 pt bold.
- Heading 3 ~11-12 pt bold or semibold.
- Use restrained project colors derived from the template/header (navy/blue with a small orange accent if already present in the template).
- No decorative gradients, neon colors, excessive icons, or dashboard-style card layouts in the academic report.
- Keep tables aligned within margins; repeat header rows across pages where needed.
- Avoid leaving headings orphaned at the bottom of a page.
- Do not split small tables/figure captions awkwardly across pages.

## 12. TOC, captions, numbering, and references

- Use real Word Heading styles for all numbered headings.
- Use hierarchical chapter numbering: 1, 1.1, 1.1.1 only as needed.
- Generate a Table of Contents from Heading styles.
- Use numbered Figure and Table captions consistently by chapter or globally; whichever is chosen must remain consistent.
- Generate List of Figures and List of Tables if supported reliably.
- Cross-reference figures/tables in prose by number, not "the chart below".
- Use IEEE-style numbered references unless the course provides another required style.
- Never expose internal ChatGPT/file-citation tokens in the Word document.
- Dataset and software references must be real and verifiable; do not invent DOIs, URLs, authors, or publication details.

## 13. Writing style

Write like a strong undergraduate technical report:
- clear and formal, but readable
- evidence-driven
- concise explanations of theory
- explicit justifications for project decisions
- no first-person singular unless contribution sections require it
- avoid marketing language
- avoid exaggerated claims such as "highly accurate" when metrics do not support them
- distinguish association from causation
- distinguish model probability from certainty
- describe the application as decision support

Do not narrate notebook execution as "then we ran this cell". Present the project as a coherent methodology.

## 14. No invention rule

Never invent:
- metrics
- hyperparameters
- dataset counts
- experiment results
- test counts
- API endpoints
- screenshots
- citations
- team contributions
- deployment behavior

If evidence is unavailable, use a clearly marked placeholder or state the limitation.

## 15. Creation workflow

When generating the final DOCX:

1. Copy the supplied template to a new output file.
2. Preserve its header/banner relationship and image asset.
3. Replace old body content, cover text, and footer course text.
4. Define/normalize Word styles.
5. Insert the full report content, tables, captions, and figures.
6. Add TOC/figure/table fields or a reliable generated equivalent.
7. Update page fields if possible.
8. Render the DOCX to PDF/PNG or otherwise visually inspect every page.
9. Fix clipping, stretched figures, broken tables, widows/orphans, and spacing problems.
10. Re-render after each material formatting correction.

The report is not finished until the final document has passed both content audit and visual QA.

## 16. Final audit

Before completion, verify all of the following:
- Every mandatory assignment topic is covered.
- All five model families are visible in baseline reporting.
- Only the three shortlisted families are presented as optimization finalists.
- Random Forest is described as selected before holdout evaluation.
- Holdout metrics match the recorded historical output.
- Post-hoc experiments are clearly labelled post-hoc.
- No obsolete 500-tree/0.6811 result has leaked into the report.
- Dataset counts and predictor count are consistent throughout.
- 32 production inputs are reported consistently.
- Figures match their captions and chapter claims.
- Backend/frontend architecture matches code.
- Limitations include Partial-class weakness and cross-country transfer concerns.
- References are real and consistent.
- Footer/header/course code are IT3051, not IT3041.
- No placeholder text remains except explicitly unresolved administrative details.
- No visible layout defects remain.

## 17. Definition of done

The task is complete only when:

- A final `.docx` exists and opens normally.
- The supplied template visual identity is preserved appropriately.
- The report covers the full assignment lifecycle.
- All quantitative claims are traceable to project evidence.
- The experimental chronology is historically correct.
- Figures/tables are readable and captioned.
- TOC/navigation and page numbering are correct.
- The final report is visually reviewed page by page.
- A concise evidence-audit summary is produced alongside the report describing sources used, unresolved placeholders, and any detected conflicts.
