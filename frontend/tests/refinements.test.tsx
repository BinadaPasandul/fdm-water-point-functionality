import { afterEach, describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { cleanup, render, screen } from "@testing-library/react";
import ModelInsightsPage from "@/app/model-insights/page";
import AboutPage from "@/app/about/page";
import DataInsightsPage from "@/app/data-insights/page";
import { getEdaInsights, getFeatureImportance, getModelInfo, getModelPerformance, getRobustness } from "@/lib/api";
import { CHART_COLORS, CLASS_COLORS } from "@/lib/chart-colors";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, getEdaInsights: vi.fn(), getModelInfo: vi.fn(), getModelPerformance: vi.fn(), getFeatureImportance: vi.fn(), getRobustness: vi.fn() };
});
vi.mock("@/components/charts", () => ({
  ConfusionTable: () => <div>Confusion matrix</div>,
  PerformanceLines: () => <div>Learning curve</div>,
  CountryChart: () => <div>Country chart</div>,
  DistributionChart: () => <div>Distribution chart</div>,
  HorizontalBars: ({ title, rows }: { title: string; rows: Record<string, unknown>[] }) => <section><h2>{title}</h2>{rows.map((row) => <span key={String(row.label ?? row.country)}>{String(row.label ?? row.country)}</span>)}</section>,
}));
vi.mock("recharts", () => ({
  Bar: () => null, BarChart: () => null, CartesianGrid: () => null, Cell: () => null, Legend: () => null,
  Line: () => null, LineChart: () => null, Pie: () => null, PieChart: () => null, ResponsiveContainer: () => null,
  Tooltip: () => null, XAxis: () => null, YAxis: () => null,
}));

afterEach(() => cleanup());

describe("frontend refinement evidence", () => {
  it("uses the centralized blue/aqua class palette", () => {
    expect(CLASS_COLORS).toEqual({ Functional: CHART_COLORS.aqua, "Partially functional": CHART_COLORS.mistBlue, "Abandoned or not functional": CHART_COLORS.navySlate });
    expect(Object.values(CLASS_COLORS)).not.toContain("#2FA66A");
    expect(Object.values(CLASS_COLORS)).not.toContain("#E6A23C");
    expect(Object.values(CLASS_COLORS)).not.toContain("#D95C5C");
  });

  it("keeps button hover and active styling stationary", () => {
    const css = readFileSync(resolve(process.cwd(), "app/globals.css"), "utf8");
    const hover = css.match(/\.button:hover\s*\{([^}]*)\}/)?.[1] ?? "";
    const active = css.match(/\.button:active\s*\{([^}]*)\}/)?.[1] ?? "";
    expect(hover).not.toMatch(/transform|translate|scale/i);
    expect(active).not.toMatch(/transform|translate|scale/i);
  });

  it("shows all five evaluated baseline families and the three optimization finalists", async () => {
    vi.mocked(getModelPerformance).mockResolvedValue({
      baseline_cv: { records: [
        { model_family: "Logistic Regression", mean_macro_f1: .60 }, { model_family: "Random Forest", mean_macro_f1: .67 },
        { model_family: "HistGradientBoosting", mean_macro_f1: .69 }, { model_family: "XGBoost", mean_macro_f1: .68 }, { model_family: "CatBoost", mean_macro_f1: .62 },
      ] },
      finalists_cv: { records: [{ family: "Random Forest", macro_f1: .70 }, { family: "XGBoost", macro_f1: .68 }, { family: "HistGradientBoosting", macro_f1: .67 }] },
      final_metrics: { cv_and_historical_holdout: [{ metric: "macro_f1", repeated_cv: .70, holdout: .67 }] },
      final_class_metrics: { records: [] }, baseline_vs_optimized: { records: [] }, final_confusion_matrix: { records: [] },
    });
    vi.mocked(getFeatureImportance).mockResolvedValue({ raw_feature_importance: { records: [] } });
    vi.mocked(getRobustness).mockResolvedValue({ country_robustness: { records: [] }, learning_curves: { records: [] } });
    render(<ModelInsightsPage />);
    expect(await screen.findByText("Baseline Model Comparison")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Model Insights" })).toBeInTheDocument();
    for (const name of ["Logistic Regression", "Random Forest", "HistGradientBoosting", "XGBoost", "CatBoost"]) expect((await screen.findAllByText(name)).length).toBeGreaterThan(0);
    expect(screen.getByText("Baseline Model Comparison")).toBeInTheDocument();
    expect(screen.getByText("Optimization Finalists")).toBeInTheDocument();
    expect(screen.getAllByText("Random Forest").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/Historical holdout Macro-F1/)).toBeInTheDocument();
    expect(screen.getAllByText(/Repeated CV Macro-F1/).length).toBeGreaterThan(0);
  });

  it("shows dataset scope, class definitions, stakeholders, and limitations on About", async () => {
    vi.mocked(getModelInfo).mockResolvedValue({ model_family: "Random Forest", preprocessing_variant: "tree_base", raw_predictor_count: 32, selected_feature_count: 60, model_version: "test" });
    vi.mocked(getEdaInsights).mockResolvedValue({ dataset: { rows: 1793, target_class_counts: { Functional: 1, "Partially functional": 1, "Abandoned or not functional": 1 } }, functionality_by_country: { records: Array.from({ length: 9 }, (_, i) => ({ country: String(i) })) } });
    render(<AboutPage />);
    expect(await screen.findByRole("heading", { level: 1, name: "About the Model" })).toBeInTheDocument();
    expect(await screen.findByText("Dataset at a glance")).toBeInTheDocument();
    expect(screen.getByText("1,793")).toBeInTheDocument();
    expect(screen.getByText("9")).toBeInTheDocument();
    expect(screen.getByText("32")).toBeInTheDocument();
    expect(screen.getAllByText("Functionality classes").length).toBeGreaterThan(0);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText(/Operating normally according to the dataset criteria/)).toBeInTheDocument();
    expect(screen.getByText("Who can use this?")).toBeInTheDocument();
    expect(screen.getByText(/Partially functional is the hardest class to identify/)).toBeInTheDocument();
  });

  it("renders the Data Insights page title with backend evidence", async () => {
    vi.mocked(getEdaInsights).mockResolvedValue({
      dataset: { rows: 1793, columns: 52, columns_with_missing: 40, duplicate_rows: 0 },
      target_distribution: { records: [] }, functionality_by_country: { records: [] }, missing_values: { records: [] },
    });
    render(<DataInsightsPage />);
    expect(await screen.findByText("Dataset notes")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Data Insights" })).toBeInTheDocument();
  });
});
