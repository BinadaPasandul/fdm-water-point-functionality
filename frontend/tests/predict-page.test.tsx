import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PredictPage from "@/app/predict/page";
import { getInputSchema, predictWaterPoint } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  classColors: { Functional: "#25C9D0", "Partially functional": "#90B0C7", "Abandoned or not functional": "#1F3952" },
  getInputSchema: vi.fn(), predictWaterPoint: vi.fn(),
}));

const names = ["country","admin1","latitude_wp","longitude_wp","elevation_wp","cwfunded_wp","wptype","pumptype","drillmethod","piped_source","piped_pump","rehabyn","qtyhh_wp","whomanage_wp","wp_age","rehab_age","qtypeople_wp","lockedfullday_wp","pumpstrokes","wc_present_wp","paytocollect_wp","improved_wponly_wp","qtyhh_c_wp","wc_admin_index_wp","wc_finance_index_wp","wc_mgmt_index_wp","wc_maint_index_wp","wc_savings_wp","wpqty_wp","pop_1000","annual_rain","season"];
const numeric = ["latitude_wp","longitude_wp","elevation_wp","qtyhh_wp","wp_age","rehab_age","qtypeople_wp","pumpstrokes","improved_wponly_wp","qtyhh_c_wp","wc_savings_wp","wpqty_wp","pop_1000","annual_rain"];
const schema = { field_count: 32, fields: names.map((name) => ({ name, label: name, type: numeric.includes(name) ? "number" as const : "categorical" as const, required: true, nullable: true })) };
const prediction = { prediction: { class_id: 0, label: "Functional", confidence: .84 }, probabilities: { Functional: .84, "Partially functional": .10, "Abandoned or not functional": .06 }, model_version: "2026-10-05" };

afterEach(() => cleanup());

describe("progressive prediction form", () => {
  it("preserves all 32 fields across five steps and submits the complete nullable request", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    vi.mocked(predictWaterPoint).mockResolvedValue(prediction);
    const user = userEvent.setup();
    const { container } = render(<PredictPage />);
    await screen.findByLabelText(/country/);
    expect(screen.getByRole("heading", { level: 1, name: "Predict Water Point Functionality" })).toBeInTheDocument();
    expect(container.querySelectorAll("form input")).toHaveLength(5);
    await user.type(screen.getByLabelText(/country/), "Kenya");
    const visited = new Set<string>();
    for (let step = 0; step < 5; step += 1) {
      container.querySelectorAll("form input").forEach((input) => visited.add(input.id));
      if (step < 4) await user.click(screen.getByRole("button", { name: "Next" }));
    }
    expect([...names].filter((name) => !visited.has(name))).toEqual([]);
    expect(screen.getByText("Step 5 of 5")).toBeInTheDocument();
    await user.type(screen.getByLabelText(/season/), "Dry");
    await user.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.getByLabelText(/whomanage_wp/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByLabelText(/season/)).toHaveValue("Dry");
    await user.click(screen.getByRole("button", { name: /Predict Functionality/i }));
    await screen.findByText("Functional", { selector: ".predicted-label" });
    expect(predictWaterPoint).toHaveBeenCalledWith(Object.fromEntries(names.map((name) => [name, name === "country" ? "Kenya" : name === "season" ? "Dry" : null])));
    expect(screen.getAllByText("84.0%")).toHaveLength(2);
    expect(screen.getByText("10.0%")).toBeInTheDocument();
    expect(screen.getByText("6.0%")).toBeInTheDocument();
  });

  it("shows a friendly error when the backend rejects prediction", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    vi.mocked(predictWaterPoint).mockRejectedValue(new Error("Prediction model is unavailable."));
    const user = userEvent.setup();
    render(<PredictPage />);
    await screen.findByLabelText(/country/);
    for (let index = 0; index < 4; index += 1) await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: /Predict Functionality/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Prediction model is unavailable."));
  });
});
