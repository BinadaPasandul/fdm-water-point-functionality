import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import DashboardPage from "@/app/page";
import { getDashboardSummary, getEdaInsights, getFeatureImportance, getModelPerformance, getRobustness } from "@/lib/api";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, getDashboardSummary: vi.fn(), getEdaInsights: vi.fn(), getFeatureImportance: vi.fn(), getModelPerformance: vi.fn(), getRobustness: vi.fn() };
});

afterEach(() => cleanup());

describe("dashboard API states", () => {
  it("renders the returned dashboard summary and dataset charts", async () => {
    vi.mocked(getDashboardSummary).mockResolvedValue({ dataset: { rows: 1793, columns: 52, countries: 9, target_class_counts: {} }, final_model: { family: "Random Forest", preprocessing_variant: "tree_base", selected_feature_count: 60, development_cv: { macro_f1: .7 }, historical_holdout: { macro_f1: .6699, mcc: .6466, accuracy: .8663 }, holdout_recomputed: false } });
    vi.mocked(getEdaInsights).mockResolvedValue({ target_distribution: { records: [{ class: "Functional", percentage: 74 }] }, functionality_by_country: { records: [] } });
    vi.mocked(getFeatureImportance).mockResolvedValue({ raw_feature_importance: { records: [] } });
    vi.mocked(getModelPerformance).mockResolvedValue({ baseline_vs_optimized: { records: [] } });
    vi.mocked(getRobustness).mockResolvedValue({ learning_curves: { records: [] }, country_robustness: { records: [] } });
    render(<DashboardPage />);
    expect(await screen.findByText("0.6699")).toBeInTheDocument();
    expect(screen.getByText("Functionality distribution")).toBeInTheDocument();
  });

  it("shows a retryable message when the summary endpoint fails", async () => {
    vi.mocked(getDashboardSummary).mockRejectedValue(new Error("Backend is offline."));
    vi.mocked(getEdaInsights).mockRejectedValue(new Error("Backend is offline."));
    vi.mocked(getFeatureImportance).mockRejectedValue(new Error("Backend is offline."));
    vi.mocked(getModelPerformance).mockRejectedValue(new Error("Backend is offline."));
    vi.mocked(getRobustness).mockRejectedValue(new Error("Backend is offline."));
    render(<DashboardPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Backend is offline.");
    expect(screen.getByRole("button", { name: "Retry loading data" })).toBeInTheDocument();
  });
});
