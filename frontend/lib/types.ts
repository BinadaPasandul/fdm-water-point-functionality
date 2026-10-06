export type Field = {
  name: string;
  label: string;
  type: "categorical" | "number";
  required: boolean;
  nullable: boolean;
  description?: string;
};

export type InputSchema = { field_count: number; fields: Field[] };
export type ApiError = { error?: { code?: string; message?: string; details?: { loc?: (string | number)[]; msg?: string }[] } };
export type Prediction = {
  prediction: { class_id: number; label: string; confidence: number };
  probabilities: Record<string, number>;
  model_version: string;
};
export type Health = { status: string; model_loaded: boolean };
export type RecordCollection = { records: Record<string, string | number>[]; metadata?: Record<string, unknown> };
export type DashboardSummary = {
  dataset: { rows: number; columns: number; countries: number; target_class_counts: Record<string, number> };
  final_model: { family: string; preprocessing_variant: string; selected_feature_count: number; development_cv: Record<string, number>; historical_holdout: Record<string, number>; holdout_recomputed: boolean };
};
