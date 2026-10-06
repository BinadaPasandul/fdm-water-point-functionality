---
name: waterpoint-dashboard-ui
description: Build and review the Next.js frontend for the Rural Water Point Functionality Prediction project using its blue/navy cozy analytics-dashboard design system, FastAPI contracts, responsive layouts, prediction form, charts, and interaction standards. Use whenever creating, modifying, styling, reviewing, or debugging this project's frontend UI.
---

# WaterPoint Dashboard UI Skill

Use this skill whenever working on the frontend for the Rural Water Point
Functionality Prediction project.

The frontend is a Next.js analytics application connected to the existing
FastAPI backend.

The backend and ML pipeline are already complete.

Do not modify ML behavior while performing frontend work.

## 1. Architecture

Always preserve:

Next.js frontend
        ↓
FastAPI HTTP/JSON API
        ↓
serialized sklearn production pipeline

Never load the `.joblib` model in Next.js.

Never reproduce preprocessing in TypeScript.

Never read raw/training/holdout datasets from the frontend.

Never recompute model metrics in the frontend.

Use only backend API responses.

## 2. Main Routes

The intended frontend routes are:

- `/` — Dashboard
- `/predict` — Predict Water Point
- `/data-insights` — EDA / dataset insights
- `/model-insights` — model performance and robustness
- `/about` — project and model explanation

Do not introduce unrelated admin pages.

## 3. Visual Character

The UI must feel:

- calm
- cozy
- premium
- clean
- modern
- analytical
- trustworthy
- spacious

Avoid generic admin-dashboard styling.

Avoid flashy "AI" styling.

Avoid neon, excessive gradients, glassmorphism, and giant pill elements.

## 4. Color Tokens

Use the following palette unless an existing implementation already defines
equivalent tokens.

Deep Navy:
`#0B1423`

Navy Slate:
`#1F3952`

Steel Blue:
`#4D728F`

Mist Blue:
`#90B0C7`

Ice Blue:
`#C9D9E8`

Page Background:
`#F3F7FA`

Surface:
`#FFFFFF`

Soft Surface:
`#EDF4F8`

Soft Border:
`#DCE7EE`

Aqua Accent:
`#25C9D0`

Soft Aqua:
`#75DDE0`

Primary Text:
`#102033`

Secondary Text:
`#64788A`

Muted Text:
`#8A9BA9`

Success:
`#2FA66A`

Warning:
`#E6A23C`

Danger:
`#D95C5C`

Use aqua as an accent, not as the dominant page color.

## 5. Functionality Class Colors

Keep functionality class colors consistent wherever classes are shown.

Functional:
`#2FA66A`

Partially functional:
`#E6A23C`

Abandoned or not functional:
`#D95C5C`

Do not rely only on color; labels must remain visible.

## 6. Page Background

Use a pale cool background around dashboard surfaces.

Prefer:

`#F3F7FA`

White cards should sit clearly above this background.

A very subtle cool radial tint is acceptable.

Strong gradients are not.

## 7. Cards

Dashboard cards should use:

- white or soft-blue surface
- 18–24px corner radius
- subtle border
- generous internal padding
- soft diffused shadow

Suggested shadow direction:

`0 8px 28px rgba(31, 57, 82, 0.07)`

Interactive cards may move upward approximately 2px on hover.

Non-interactive metric/chart cards should remain mostly stationary.

Never use large harsh shadows.

## 8. Spacing

Prefer comfortable spacing.

Desktop page padding:
28–36px

Card padding:
20–28px

Grid gap:
18–24px

Section gap:
28–40px

Do not overcrowd the dashboard.

## 9. Header

Desktop header navigation must use plain text links.

Expected links:

Dashboard
Predict
Data Insights
Model Insights
About

Do NOT style navigation links as:

- pills
- bordered buttons
- filled tabs

The header should feel lightweight.

## 10. Animated Underline Navigation

Desktop navigation links must use an offset underline reveal.

The line:

- sits 5–7px below the text
- is roughly 2px high
- uses aqua/steel blue
- animates horizontally
- remains visible for the active route

Use a pseudo-element or equivalent CSS.

Preferred behavior:

initial:
`scaleX(0)`

hover/active:
`scaleX(1)`

duration:
approximately 220ms

Enter direction:
left → right

Exit may reverse direction.

Do not animate the text position.

## 11. Mobile Navigation

Below desktop/tablet navigation width:

show:

logo/project name
menu icon

Opening the menu should display a clean mobile navigation panel.

Do not force desktop navigation links into a cramped horizontal row.

## 12. Typography

Use an existing modern sans-serif.

Preferred:

- Geist
- Inter
- equivalent clean system font

Avoid decorative fonts.

Typical hierarchy:

Page title:
30–36px desktop

Section title:
18–22px

Card heading:
14–16px semibold

KPI value:
28–36px bold

Body:
14–16px

Metadata:
12–13px

## 13. Buttons

Buttons are allowed for actions.

Navigation links are NOT buttons.

Primary buttons:

- navy background
- white text
- 12–14px radius
- medium weight

Hover:

- move upward about 1px
- slightly deepen color
- increase shadow subtly

Active:

- remove lift
- optional scale around 0.99

Never use dramatic scale animations.

## 14. Loading Buttons

Prediction submission must provide a loading state.

Example:

Normal:
`Predict Functionality`

Loading:
spinner + `Analyzing Water Point...`

Prevent duplicate submissions.

Do not intentionally delay the result.

## 15. Skeleton Loading

Do not show plain text such as only:

`Loading...`

for dashboard content.

Use card-shaped skeletons matching the actual layout.

Skeletons should:

- have rounded geometry
- use pale blue-grey
- use subtle shimmer
- avoid flashing

## 16. Motion

Use subtle motion only.

Good:

- navigation underline
- card hover
- button lift
- chart fade
- result-card entrance
- mobile menu transition
- skeleton shimmer

Avoid:

- bouncing
- large scale
- spinning containers
- cinematic page slides
- constant ambient animation

Respect `prefers-reduced-motion`.

## 17. Dashboard Layout

Use a responsive asymmetric analytics grid inspired by a polished financial
dashboard.

Desktop:

KPI row

then approximately:

Target Distribution | Functionality by Country

Model Performance | Optimization Comparison

Feature Importance | Country Robustness

Learning Curve full width

Do not force identical card dimensions.

Use responsive CSS Grid.

## 18. Dashboard KPIs

Recommended core KPIs:

- 1,793 Water Points
- 9 Countries
- 3 Functionality Classes
- Historical Holdout Macro-F1

Never label Macro-F1 as Accuracy.

Use metric terminology exactly.

## 19. Charts

Use Recharts unless the project already uses another chart library.

Avoid rainbow palettes.

Charts should include:

- meaningful titles
- readable tooltips
- responsive container
- minimal grid lines
- clear axis labels
- accessible legends
- empty/error states

Do not display unnecessary decimal places.

## 20. Prediction Form

The production backend expects 32 raw predictors.

Always obtain field metadata from:

`GET /api/v1/input-schema`

where practical.

Do not independently redefine the ML schema.

The form should be grouped into:

### Location
Country
Administrative region
Latitude
Longitude
Elevation

### Infrastructure
Water point type
Pump type
Drilling method
Piped source
Piped pump
Water point age
Rehabilitation information

### Usage & Demographics
People served
Households served
Population
Water quantity / usage variables

### Management & Finance
Management responsibility
Committee presence
Collection/payment information
Committee indices
Savings

### Environment
Annual rainfall
Season
other relevant environmental field(s)

Verify the exact grouping against the API.

Never omit required fields.

## 21. Nullable Values

A required feature column may still allow a null value.

Do not confuse:

missing field

with:

field whose value is unknown.

Use an explicit:

`Unknown / Not available`

option where useful.

Send JSON `null`, not arbitrary empty strings.

## 22. Prediction Result

The result should clearly show:

Predicted class

Model probability / confidence

all three class probabilities

Use horizontal bars or a compact probability chart.

Always show exact class label.

Example:

FUNCTIONAL

Model probability: 84.2%

Functional                   84.2%
Partially functional         10.1%
Abandoned / not functional    5.7%

## 23. Prediction Disclaimer

Include:

"This result is a machine-learning prediction intended to support
prioritisation and field assessment. It should not replace on-site
inspection."

Do not describe model output as certainty.

## 24. API Layer

Centralize API requests in one module, e.g.:

`lib/api.ts`

Expected functions include:

- `getHealth`
- `getModelInfo`
- `getInputSchema`
- `predictWaterPoint`
- `getDashboardSummary`
- `getEdaInsights`
- `getModelPerformance`
- `getFeatureImportance`
- `getRobustness`

Do not scatter duplicated raw fetch calls throughout components.

## 25. Backend Base URL

Use:

`NEXT_PUBLIC_API_BASE_URL`

Do not hardcode localhost in components.

Provide a `.env.example`.

## 26. Dashboard Data

The backend already exposes exported analytical evidence.

Do not read notebooks.

Do not read `reports/` directly from browser code.

Consume:

`/api/v1/dashboard/...`

Only render the evidence received from the backend.

## 27. Data Insights

Prioritize:

- target distribution
- missing-value overview
- functionality by country
- one categorical relationship
- one numerical relationship

Additional technical EDA belongs lower on the page.

Do NOT expose the leakage-diagnostic chart on the ordinary user dashboard.

## 28. Model Insights

Include:

- final model identity
- development CV metrics
- historical holdout metrics
- baseline comparison
- optimization comparison
- Partial-class metrics
- final confusion matrix
- feature importance
- learning curve
- country robustness

Clearly distinguish:

CV

from:

historical holdout.

Never combine them under one ambiguous "model score".

## 29. Feature Importance Disclaimer

Whenever feature importance is presented, include wording equivalent to:

"Importance reflects predictive reliance, not causation."

## 30. Country Robustness

Label it clearly as:

Cross-country robustness

or:

Leave-one-country-out evaluation.

Do not label it as a normal holdout test.

## 31. Responsive Requirements

Verify approximately:

1440px
1280px
1024px
768px
390px
360px

Desktop:
2–4-column dashboard composition

Tablet:
1–2 columns

Mobile:
single-column cards

No horizontal page overflow.

Charts must resize correctly.

## 32. Accessibility

Always include:

- semantic HTML
- accessible labels
- keyboard navigation
- visible focus
- sufficient contrast
- icon button aria-labels
- associated form errors
- reduced-motion support

Never use only color to communicate an outcome.

## 33. Error States

Support:

- backend offline
- API timeout/network error
- prediction validation error
- model unavailable
- dashboard data unavailable

Present user-friendly errors.

Never expose stack traces.

## 34. Empty States

Empty chart/data areas must show a useful message.

Example:

"Insights are currently unavailable."

Where appropriate include a retry action.

## 35. Code Quality

Use TypeScript.

Avoid `any`.

Use reusable components.

Keep business/API logic out of presentation components.

Do not duplicate API types in many locations.

Do not over-abstract simple UI.

## 36. Server / Client Components

Use Server Components by default where practical.

Add `"use client"` only where needed for:

- interactive charts
- forms
- browser interaction

Do not make the entire application a Client Component.

## 37. Scope Protection

Frontend work must NEVER modify:

- notebooks
- datasets
- ML pipeline
- joblib model
- feature preprocessing
- model reports
- optimization results

Do not retrain the model.

Do not recompute analytical evidence.

## 38. Definition of Done

Before declaring frontend work complete:

- navigation works
- animated offset underline works
- mobile navigation works
- dashboard API data loads
- dashboard loading skeletons work
- dashboard error states work
- prediction page contains all 32 fields
- prediction API integration works
- result probabilities map correctly
- responsive layout verified
- keyboard/focus states verified
- TypeScript passes
- lint passes
- production build passes
- tests pass
- no ML/backend behavior changed

The final product should feel like a carefully designed water-infrastructure
analytics dashboard, not a generic generated admin template.