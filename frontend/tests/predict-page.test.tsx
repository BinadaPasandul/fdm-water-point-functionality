import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PredictPage from "@/app/predict/page";
import { getInputSchema, predictWaterPoint } from "@/lib/api";
import type { Field, FieldOption } from "@/lib/types";

vi.mock("@/lib/api", () => ({
  classColors: { Functional: "#25C9D0", "Partially functional": "#90B0C7", "Abandoned or not functional": "#1F3952" },
  getInputSchema: vi.fn(), predictWaterPoint: vi.fn(),
}));

const names = ["country", "admin1", "latitude_wp", "longitude_wp", "elevation_wp", "cwfunded_wp", "wptype", "pumptype", "drillmethod", "piped_source", "piped_pump", "rehabyn", "qtyhh_wp", "whomanage_wp", "wp_age", "rehab_age", "qtypeople_wp", "lockedfullday_wp", "pumpstrokes", "wc_present_wp", "paytocollect_wp", "improved_wponly_wp", "qtyhh_c_wp", "wc_admin_index_wp", "wc_finance_index_wp", "wc_mgmt_index_wp", "wc_maint_index_wp", "wc_savings_wp", "wpqty_wp", "pop_1000", "annual_rain", "season"];
const numeric = new Set(["latitude_wp", "longitude_wp", "elevation_wp", "qtyhh_wp", "wp_age", "rehab_age", "qtypeople_wp", "pumpstrokes", "qtyhh_c_wp", "wpqty_wp", "pop_1000", "annual_rain"]);
const options = (values: (string | number)[]): FieldOption[] => values.map((value) => ({ label: String(value), value }));
const regionMap: Record<string, FieldOption[]> = {
  Ethiopia: options(["Tigray"]), India: options(["Bihar", "West Bengal"]), Malawi: options(["Central", "North", "South"]),
  Mali: options(["Koulikoro", "Segou"]), Mozambique: options(["Nampula", "Zambezia"]), Nepal: options(["Central", "Western"]),
  Niger: options(["Dosso", "Maradi"]), Rwanda: options(["Northern Province"]), Uganda: options(["Eastern"]),
};
const countryOptions = options(Object.keys(regionMap));
const regionOptions = options(Object.values(regionMap).flatMap((items) => items.map((item) => String(item.value))));
const binary = options(["Yes", "No"]);
const labels: Record<string, string> = {
  country: "Country", admin1: "Administrative Region", wptype: "Water Point Type", pumptype: "Pump Type",
  drillmethod: "Drilling Method", piped_source: "Piped Water Source", piped_pump: "Piped Water Delivery",
  rehabyn: "Rehabilitated", rehab_age: "Age at Rehabilitation", whomanage_wp: "Water Point Manager",
  wc_present_wp: "Water Committee Present", wc_savings_wp: "Water Committee Savings",
  wc_admin_index_wp: "Water Committee Administration Index", season: "Season",
  improved_wponly_wp: "Improved Water Point Only",
};
const fieldOptions: Record<string, FieldOption[]> = {
  country: countryOptions, admin1: regionOptions, cwfunded_wp: binary,
  wptype: options(["Borehole with hand pump", "Mechanized borehole", "Piped water into yard / plot", "Protected dug well with hand pump", "Protected spring", "Public tap / standpipe", "Rainwater collection", "Unprotected dug well", "Unprotected spring"]),
  pumptype: options(["Afridev", "Hydro India", "India Mark II", "U3", "Vergnet", "Vergnet Hydro", "Water4"]),
  drillmethod: options(["Drilled by machine", "Hand-dug", "Manually drilled"]),
  piped_source: options(["Borehole", "Protected spring", "Unprotected spring"]),
  piped_pump: options(["Diesel powered pump", "Electric powered pump", "Gravity Fed", "Solar powered pump"]),
  rehabyn: binary, whomanage_wp: options(["Church", "Community leader", "District/local government", "Don't Know", "Health administrator", "No one", "Other", "Private person", "School", "Vendor", "Water committee"]),
  lockedfullday_wp: binary, wc_present_wp: binary, paytocollect_wp: binary,
  improved_wponly_wp: [{ label: "No", value: 0 }, { label: "Yes", value: 1 }], wc_savings_wp: [{ label: "No", value: 0 }, { label: "Yes", value: 1 }],
  wc_admin_index_wp: options(["Inadequate", "Minimum", "Moderate", "Advanced"]), wc_finance_index_wp: options(["Inadequate", "Minimum", "Moderate", "Advanced"]),
  wc_mgmt_index_wp: options(["Inadequate", "Minimum", "Moderate", "Advanced"]), wc_maint_index_wp: options(["Inadequate", "Minimum", "Moderate", "Advanced"]),
  season: [{ label: "Dry", value: "dry" }, { label: "Wet", value: "wet" }],
};
const schema = {
  field_count: 32,
  fields: names.map((name): Field => ({
    name, label: labels[name] ?? name.replaceAll("_", " "), type: numeric.has(name) ? "number" : ["improved_wponly_wp", "wc_savings_wp"].includes(name) ? "binary_numeric" : "categorical",
    required: true, nullable: true, known_options: fieldOptions[name], ...(name === "admin1" ? { options_by_parent: regionMap } : {}),
  })),
};
const prediction = { prediction: { class_id: 0, label: "Functional", confidence: .84 }, probabilities: { Functional: .84, "Partially functional": .10, "Abandoned or not functional": .06 }, model_version: "2026-10-05" };

afterEach(() => cleanup());

async function choose(user: ReturnType<typeof userEvent.setup>, label: RegExp | string, option: string) {
  const combobox = screen.getByRole("combobox", { name: label });
  await user.click(combobox);
  await user.type(combobox, option);
  await user.click(await screen.findByRole("option", { name: option }));
}

async function chooseSelect(user: ReturnType<typeof userEvent.setup>, label: RegExp | string, option: string) {
  await user.click(screen.getByRole("combobox", { name: label }));
  await user.click(await screen.findByRole("option", { name: option }));
}

async function moveToStep(user: ReturnType<typeof userEvent.setup>, target: number) {
  const text = screen.getByText(/Step \d of 5/).textContent ?? "Step 1 of 5";
  const current = Number(text.match(/Step (\d)/)?.[1] ?? 1) - 1;
  for (let i = current; i < target; i += 1) await user.click(screen.getByRole("button", { name: "Next" }));
}

describe("production prediction input UX", () => {
  it("uses known searchable choices, scopes admin regions, and clears an incompatible region", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    const user = userEvent.setup();
    render(<PredictPage />);
    await screen.findByRole("combobox", { name: "Country" });
    await choose(user, "Country", "Ethiopia");
    const admin = screen.getByRole("combobox", { name: "Administrative Region" });
    await user.click(admin);
    const regionList = screen.getByRole("listbox", { name: "Administrative Region" });
    expect(within(regionList).getByRole("option", { name: "Tigray" })).toBeInTheDocument();
    expect(within(regionList).queryByRole("option", { name: "Bihar" })).not.toBeInTheDocument();
    await user.click(within(regionList).getByRole("option", { name: "Tigray" }));
    await choose(user, "Country", "India");
    expect(screen.getByRole("combobox", { name: "Administrative Region" })).toHaveValue("");
    await user.click(screen.getByRole("combobox", { name: "Administrative Region" }));
    expect(screen.getByRole("option", { name: "Bihar" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Tigray" })).not.toBeInTheDocument();
  });

  it("keeps all 32 fields and sends null, binary numbers, season codes, and full values", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    vi.mocked(predictWaterPoint).mockResolvedValue(prediction);
    const user = userEvent.setup();
    render(<PredictPage />);
    await screen.findByRole("combobox", { name: "Country" });
    await choose(user, "Country", "Ethiopia");
    for (let step = 0; step < 4; step += 1) await user.click(screen.getByRole("button", { name: "Next" }));
    await chooseSelect(user, "Season", "Dry");
    await chooseSelect(user, "Improved Water Point Only", "Yes");
    await user.click(screen.getByRole("button", { name: /Predict Functionality/i }));
    await screen.findByText("Functional", { selector: ".predicted-label" });
    const payload = vi.mocked(predictWaterPoint).mock.calls[0][0];
    expect(Object.keys(payload)).toEqual(names);
    expect(payload.country).toBe("Ethiopia");
    expect(payload.season).toBe("dry");
    expect(payload.improved_wponly_wp).toBe(1);
    expect(payload.wc_savings_wp).toBeNull();
    expect(payload.rehab_age).toBeNull();
  });

  it("renders searchable category sets, keeps Don't Know distinct, and preserves ordinal order", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    const user = userEvent.setup();
    render(<PredictPage />);
    await screen.findByRole("combobox", { name: "Country" });
    await user.click(screen.getByRole("button", { name: "Next" }));
    await choose(user, "Water Point Type", "Public tap / standpipe");
    expect(screen.queryByRole("combobox", { name: "Pump Type" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Back" }));
    await user.click(screen.getByRole("button", { name: "Next" }));
    await choose(user, "Water Point Type", "Borehole with hand pump");
    expect(screen.getByRole("combobox", { name: "Pump Type" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: "Next" }));
    const manager = screen.getByRole("combobox", { name: "Water Point Manager" });
    await user.click(manager);
    expect(screen.getByRole("option", { name: "Don't Know" })).toBeInTheDocument();
    await chooseSelect(user, "Water Committee Present", "Yes");
    await user.click(screen.getByRole("combobox", { name: "Water Committee Administration Index" }));
    const ordinalValues = within(screen.getByRole("listbox", { name: "Water Committee Administration Index" })).getAllByRole("option").map((item) => item.textContent).filter((text) => text !== "Unknown / not available");
    expect(ordinalValues).toEqual(["Inadequate", "Minimum", "Moderate", "Advanced"]);
    await user.click(screen.getByRole("combobox", { name: "Water Committee Savings" }));
    const savingsOptions = within(screen.getByRole("listbox", { name: "Water Committee Savings" })).getAllByRole("option");
    expect(savingsOptions).toHaveLength(3);
    expect(savingsOptions.map((item) => item.textContent)).not.toContain("888");
    expect(savingsOptions.map((item) => item.textContent)).not.toContain("999");
  });

  it("clears conditional inputs and marks predictions stale only when API values change", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    vi.mocked(predictWaterPoint).mockResolvedValue(prediction);
    const user = userEvent.setup();
    render(<PredictPage />);
    await screen.findByRole("combobox", { name: "Country" });
    await moveToStep(user, 1);
    await choose(user, "Water Point Type", "Borehole with hand pump");
    await chooseSelect(user, "Rehabilitated", "Yes");
    await user.type(screen.getByLabelText("Age at Rehabilitation"), "4");
    await moveToStep(user, 2);
    await moveToStep(user, 3);
    await chooseSelect(user, "Water Committee Present", "Yes");
    await chooseSelect(user, "Water Committee Savings", "Yes");
    await moveToStep(user, 4);
    await user.click(screen.getByRole("button", { name: /Predict Functionality/i }));
    await screen.findByText("Functional", { selector: ".predicted-label" });
    await user.click(screen.getByRole("button", { name: "Back" }));
    expect(screen.queryByText("Inputs changed")).not.toBeInTheDocument();
    await chooseSelect(user, "Water Committee Present", "No");
    expect(screen.getByText("Inputs changed")).toBeInTheDocument();
    expect(screen.queryByText("Functional", { selector: ".predicted-label" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Back" }));
    await user.click(screen.getByRole("button", { name: "Back" }));
    await chooseSelect(user, "Rehabilitated", "No");
    await waitFor(() => expect(screen.queryByRole("spinbutton", { name: "Age at Rehabilitation" })).not.toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Next" }));
    const requestBeforeRepredict = vi.mocked(predictWaterPoint).mock.calls[0][0];
    expect(requestBeforeRepredict.rehab_age).toBe(4);
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: "Next" }));
    await user.click(screen.getByRole("button", { name: /Predict Functionality/i }));
    await waitFor(() => expect(screen.queryByText("Inputs changed")).not.toBeInTheDocument());
    expect(vi.mocked(predictWaterPoint).mock.calls[1][0].wc_savings_wp).toBeNull();
    expect(vi.mocked(predictWaterPoint).mock.calls[1][0].rehab_age).toBeNull();
  });

  it("shows a friendly error when the backend rejects prediction", async () => {
    vi.mocked(getInputSchema).mockResolvedValue(schema);
    vi.mocked(predictWaterPoint).mockRejectedValue(new Error("Prediction model is unavailable."));
    const user = userEvent.setup();
    render(<PredictPage />);
    await screen.findByRole("combobox", { name: "Country" });
    await moveToStep(user, 4);
    await user.click(screen.getByRole("button", { name: /Predict Functionality/i }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Prediction model is unavailable."));
  });
});
