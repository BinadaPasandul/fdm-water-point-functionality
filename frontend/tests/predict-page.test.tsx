import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PredictPage from "@/app/predict/page";
import { getInputSchema, predictWaterPoint } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  classColors: { Functional: "#2FA66A", "Partially functional": "#E6A23C", "Abandoned or not functional": "#D95C5C" },
  getInputSchema: vi.fn(), predictWaterPoint: vi.fn(),
}));

const names = ["country","admin1","latitude_wp","longitude_wp","elevation_wp","cwfunded_wp","wptype","pumptype","drillmethod","piped_source","piped_pump","rehabyn","qtyhh_wp","whomanage_wp","wp_age","rehab_age","qtypeople_wp","lockedfullday_wp","pumpstrokes","wc_present_wp","paytocollect_wp","improved_wponly_wp","qtyhh_c_wp","wc_admin_index_wp","wc_finance_index_wp","wc_mgmt_index_wp","wc_maint_index_wp","wc_savings_wp","wpqty_wp","pop_1000","annual_rain","season"];
const schema = { field_count: 32, fields: names.map((name) => ({ name, label: name, type: ["latitude_wp","longitude_wp","elevation_wp","qtyhh_wp","wp_age","rehab_age","qtypeople_wp","pumpstrokes","improved_wponly_wp","qtyhh_c_wp","wc_savings_wp","wpqty_wp","pop_1000","annual_rain"].includes(name) ? "number" as const : "categorical" as const, required: true, nullable: true })) };
const prediction = { prediction: { class_id: 0, label: "Functional", confidence: .84 }, probabilities: { Functional: .84, "Partially functional": .10, "Abandoned or not functional": .06 }, model_version: "2026-10-05" };

afterEach(() => cleanup());

describe("prediction form", () => {
  it("renders every API field and sends blank nullable fields as null", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    vi.mocked(predictWaterPoint).mockResolvedValue(prediction);
    const { container } = render(<PredictPage />);
    await screen.findByLabelText("country · may be unknown");
    expect(container.querySelectorAll("form input")).toHaveLength(32);
    await userEvent.setup().click(screen.getByRole("button", { name: /Predict Functionality/i }));
    await screen.findByText("Functional", { selector: ".predicted-label" });
    expect(predictWaterPoint).toHaveBeenCalledWith(Object.fromEntries(names.map((name) => [name, null])));
    expect(screen.getAllByText("84.0%")).toHaveLength(2);
    expect(screen.getByText("10.0%")).toBeInTheDocument();
    expect(screen.getByText("6.0%")).toBeInTheDocument();
  });

  it("shows a friendly error when the backend rejects prediction", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    vi.mocked(predictWaterPoint).mockRejectedValue(new Error("Prediction model is unavailable."));
    render(<PredictPage />);
    await screen.findByLabelText("country · may be unknown");
    await userEvent.setup().click(screen.getByRole("button", { name: /Predict Functionality/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Prediction model is unavailable."));
  });
});
