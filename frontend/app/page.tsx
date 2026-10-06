"use client";

import Link from "next/link";
import { ArrowRight, Droplet, Globe2, Layers3, Target } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { CountryChart, DistributionChart, HorizontalBars, PerformanceLines } from "@/components/charts";
import { Metric } from "@/components/metric";
import { Card, ErrorPanel, PageHeading, SkeletonGrid } from "@/components/ui";
import { getDashboardSummary, getEdaInsights, getFeatureImportance, getRobustness, getModelPerformance, records } from "@/lib/api";
import type { DashboardSummary } from "@/lib/types";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [eda, setEda] = useState<Record<string, unknown> | null>(null);
  const [importance, setImportance] = useState<Record<string, unknown> | null>(null);
  const [robustness, setRobustness] = useState<Record<string, unknown> | null>(null);
  const [performance, setPerformance] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = useCallback(async () => {
    setLoading(true); setError("");
    const results = await Promise.allSettled([getDashboardSummary(), getEdaInsights(), getFeatureImportance(), getRobustness(), getModelPerformance()]);
    if (results[0].status === "fulfilled") setSummary(results[0].value); else setError(results[0].reason instanceof Error ? results[0].reason.message : "Dashboard data is unavailable.");
    if (results[1].status === "fulfilled") setEda(results[1].value);
    if (results[2].status === "fulfilled") setImportance(results[2].value);
    if (results[3].status === "fulfilled") setRobustness(results[3].value);
    if (results[4].status === "fulfilled") setPerformance(results[4].value);
    setLoading(false);
  }, []);
  useEffect(() => {
    Promise.allSettled([getDashboardSummary(), getEdaInsights(), getFeatureImportance(), getRobustness(), getModelPerformance()]).then((results) => {
      if (results[0].status === "fulfilled") setSummary(results[0].value); else setError(results[0].reason instanceof Error ? results[0].reason.message : "Dashboard data is unavailable.");
      if (results[1].status === "fulfilled") setEda(results[1].value);
      if (results[2].status === "fulfilled") setImportance(results[2].value);
      if (results[3].status === "fulfilled") setRobustness(results[3].value);
      if (results[4].status === "fulfilled") setPerformance(results[4].value);
      setLoading(false);
    });
  }, []);
  if (loading) return <div className="page-enter"><PageHeading eyebrow="Rural Water Infrastructure Intelligence" title="Water Point Functionality Dashboard" description="Monitor dataset patterns, understand model performance, and predict the functionality of rural water points." /><SkeletonGrid /></div>;
  if (error && !summary) return <><PageHeading eyebrow="Rural Water Infrastructure Intelligence" title="Water Point Functionality Dashboard" description="Monitor dataset patterns, understand model performance, and predict the functionality of rural water points." /><ErrorPanel message={error} retry={() => void load()} /></>;
  const holdout = summary?.final_model.historical_holdout ?? {};
  const targetRows = records(eda?.target_distribution);
  const countryRows = records(eda?.functionality_by_country);
  const features = records(importance?.raw_feature_importance).slice(0, 7).map((row) => ({ ...row, name: String(row.raw_feature).replaceAll("_", " "), value: Number(row.mean_importance) }));
  const curve = records(robustness?.learning_curves).filter((row) => row.configuration === "Locked RF");
  const opt = records(performance?.baseline_vs_optimized).find((row) => row.family === summary?.final_model.family);
  return <div className="page-enter">
    <PageHeading eyebrow="Rural Water Infrastructure Intelligence" title="Water Point Functionality Dashboard" description="Monitor dataset patterns, understand model performance, and predict the functionality of rural water points." action={<div className="hero-actions"><Link className="button" href="/predict">Predict Water Point <ArrowRight size={16} /></Link><Link className="text-link" href="/model-insights">Explore Model Insights</Link></div>} />
    <div className="metrics-grid">
      <Metric icon={Droplet} value={(summary?.dataset.rows ?? 1793).toLocaleString()} label="Water points" note="In the analyzed dataset" />
      <Metric icon={Globe2} value={String(summary?.dataset.countries ?? 9)} label="Countries" note="Represented in the dataset" />
      <Metric icon={Layers3} value="3" label="Functionality classes" note="Functional · partial · abandoned" />
      <Metric icon={Target} value={Number(holdout.macro_f1 ?? 0).toFixed(4)} label="Historical holdout Macro-F1" note="Recorded once · not recomputed" />
    </div>
    <div className="dashboard-grid">
      <div className="grid-5"><DistributionChart rows={targetRows} /></div>
      <div className="grid-7"><CountryChart rows={countryRows} /></div>
      <div className="grid-6"><Card title="Final model performance" subtitle={`${summary?.final_model.family ?? "Final model"} · historical holdout`}><div className="performance-stats"><div><span>Macro-F1</span><strong>{Number(holdout.macro_f1 ?? 0).toFixed(3)}</strong></div><div><span>MCC</span><strong>{Number(holdout.mcc ?? 0).toFixed(3)}</strong></div><div><span>Accuracy</span><strong>{Number(holdout.accuracy ?? 0).toFixed(3)}</strong></div></div><p className="metric-note">Development CV Macro-F1: {Number(summary?.final_model.development_cv.macro_f1 ?? 0).toFixed(3)}. The holdout value is historical evidence.</p><Link href="/model-insights" className="text-link inline-link">View model evaluation <ArrowRight size={14} /></Link></Card></div>
      <div className="grid-6"><Card title="Baseline to optimized" subtitle="Repeated cross-validation Macro-F1">{opt ? <div className="compare-bars"><div><span>Baseline</span><div className="compare-track"><i style={{ width: `${Number(opt.baseline_macro_f1) * 100}%` }} /></div><b>{Number(opt.baseline_macro_f1).toFixed(3)}</b></div><div><span>Optimized</span><div className="compare-track optimized"><i style={{ width: `${Number(opt.optimized_macro_f1) * 100}%` }} /></div><b>{Number(opt.optimized_macro_f1).toFixed(3)}</b></div><p className="metric-note">Change: {Number(opt.macro_f1_change) >= 0 ? "+" : ""}{Number(opt.macro_f1_change).toFixed(3)} · {summary?.final_model.family}</p></div> : <p className="empty-state">Optimization comparison is unavailable.</p>}</Card></div>
      <div className="grid-6"><HorizontalBars title="Top feature importance" subtitle="Raw feature permutation importance · mean decrease" rows={features} nameKey="name" valueKey="value" color="#4D728F" footer={<p className="metric-note">Importance reflects predictive reliance, not causation.</p>} /></div>
      <div className="grid-6"><HorizontalBars title="Cross-country robustness" subtitle="Leave-one-country-out evaluation · Macro-F1" rows={records(robustness?.country_robustness).map((row) => ({ ...row, score: Number(row.macro_f1_observed_classes) })).sort((a, b) => Number(b.score) - Number(a.score))} nameKey="country" valueKey="score" color="#25AFC0" /></div>
      <div className="grid-12"><PerformanceLines rows={curve} /></div>
    </div>
    {error && <div className="inline-error">Some dashboard panels could not be loaded: {error}</div>}
  </div>;
}
