export const CHART_COLORS = {
  deepNavy: "#0B1423",
  navySlate: "#1F3952",
  steelBlue: "#4D728F",
  mistBlue: "#90B0C7",
  iceBlue: "#C9D9E8",
  aqua: "#25C9D0",
  softAqua: "#75DDE0",
  muted: "#64788A",
} as const;

export const CLASS_COLORS: Record<string, string> = {
  Functional: CHART_COLORS.aqua,
  "Partially functional": CHART_COLORS.mistBlue,
  "Abandoned or not functional": CHART_COLORS.navySlate,
};

export const CHART_PALETTE = [CHART_COLORS.navySlate, CHART_COLORS.steelBlue, CHART_COLORS.aqua, CHART_COLORS.mistBlue, CHART_COLORS.iceBlue] as const;
