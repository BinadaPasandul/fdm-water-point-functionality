import type { ApiError, DashboardSummary, Health, InputSchema, Prediction } from "./types";
import { CLASS_COLORS } from "./chart-colors";
export { CLASS_COLORS, CHART_COLORS, CHART_PALETTE } from "./chart-colors";

const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { ...init, headers: { "Content-Type": "application/json", ...init?.headers }, cache: "no-store" });
  } catch {
    throw new Error("The API could not be reached. Check that the backend is running and try again.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as ApiError;
    throw new Error(body.error?.message ?? `The request could not be completed (${response.status}).`);
  }
  return response.json() as Promise<T>;
}

export const getHealth = () => request<Health>("/health");
export const getModelInfo = () => request<Record<string, unknown>>("/api/v1/model-info");
export const getInputSchema = () => request<InputSchema>("/api/v1/input-schema");
export const predictWaterPoint = (payload: Record<string, string | number | null>) => request<Prediction>("/api/v1/predict", { method: "POST", body: JSON.stringify(payload) });
export const getDashboardSummary = () => request<DashboardSummary>("/api/v1/dashboard/summary");
export const getEdaInsights = () => request<Record<string, unknown>>("/api/v1/dashboard/eda");
export const getModelPerformance = () => request<Record<string, unknown>>("/api/v1/dashboard/model-performance");
export const getFeatureImportance = () => request<Record<string, unknown>>("/api/v1/dashboard/feature-importance");
export const getRobustness = () => request<Record<string, unknown>>("/api/v1/dashboard/robustness");

export const classColors = CLASS_COLORS;

export function records(value: unknown): Record<string, string | number>[] {
  if (!value || typeof value !== "object" || !("records" in value)) return [];
  const rows = (value as { records?: unknown }).records;
  return Array.isArray(rows) ? rows.filter((row): row is Record<string, string | number> => !!row && typeof row === "object") : [];
}
