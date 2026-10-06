# Predicting Rural Water Point Functionality Using Data Mining

A university mini project for the Fundamentals of Data Mining (FDM) course. The goal is to
predict the functionality status of rural water points using data mining and machine
learning techniques.

## Dataset

- **Dataset name:** Rural Water Point Functionality Dataset (`rwpfunctionality`)
- **Source:** [openwashdata.github.io/rwpfunctionality](https://openwashdata.github.io/rwpfunctionality/)
- **File location:** `data/raw/water_pump_functionality.xlsx` (raw, unmodified)
- **Number of records:** 1,793
- **Number of variables:** 52
- **Target variable:** `functional3`
- **ML task:** Multiclass classification
- **Target classes:**
  - Functional
  - Partially functional
  - Abandoned or not functional

## Project Status

The data understanding, EDA, preprocessing, model development, and model optimization stages are complete. The final inference pipeline is available at `models/final_inference_pipeline.joblib`.

## Prediction API

Install dependencies with `pip install -r requirements.txt`, then start the FastAPI backend from the repository root:

```bash
uvicorn backend.main:app --reload
```

Interactive API documentation is available at <http://127.0.0.1:8000/docs>. Check service and model readiness with `GET /health`; submit one raw water-point record to `POST /api/v1/predict`.

## Next.js Dashboard

The frontend is in `frontend/` and uses the FastAPI service as its only source of prediction and dashboard data.

```powershell
# Terminal 1: from the repository root
uvicorn backend.main:app --reload

# Terminal 2
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. The frontend reads `NEXT_PUBLIC_API_BASE_URL` from `frontend/.env.local`; copy `frontend/.env.example` as a starting point. The default API URL is `http://127.0.0.1:8000`.

Pages: Dashboard (`/`), Predict (`/predict`), Data Insights (`/data-insights`), Model Insights (`/model-insights`), and About (`/about`).
