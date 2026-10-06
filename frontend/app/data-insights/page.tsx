"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CountryChart, DistributionChart, HorizontalBars } from "@/components/charts";
import { Card, ErrorPanel, PageHeading, SkeletonGrid } from "@/components/ui";
import { getEdaInsights, records } from "@/lib/api";
import { CHART_COLORS } from "@/lib/chart-colors";

export default function DataInsightsPage() {
  const [data, setData] = useState<Record<string, unknown> | null>(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  async function load() { setLoading(true); try { setData(await getEdaInsights()); setError(""); } catch (e) { setError(e instanceof Error ? e.message : "Dataset insights are unavailable."); } finally { setLoading(false); } }
  useEffect(() => { getEdaInsights().then(setData).catch((e: unknown) => setError(e instanceof Error ? e.message : "Dataset insights are unavailable.")).finally(() => setLoading(false)); }, []);
  if (loading) return <><PageHeading eyebrow="Dataset exploration" title="Data Insights" description="Explore the shape, coverage, and patterns in the water point dataset." /><SkeletonGrid /></>;
  if (error || !data) return <><PageHeading eyebrow="Dataset exploration" title="Data Insights" description="Explore the shape, coverage, and patterns in the water point dataset." /><ErrorPanel message={error || "Dataset insights are unavailable."} retry={() => void load()} /></>;
  const summary = data.dataset as Record<string, unknown>;
  return <div className="page-enter"><PageHeading eyebrow="Dataset exploration" title="Data Insights" description="A descriptive view of the dataset used in the project, served from the backend's exported analytical evidence." />
    <div className="insight-strip"><div><b>{Number(summary.rows).toLocaleString()}</b><span>Records</span></div><div><b>{String(summary.columns)}</b><span>Columns</span></div><div><b>{records(data.functionality_by_country).length}</b><span>Countries</span></div><div><b>{String(summary.columns_with_missing)}</b><span>Columns with missing values</span></div></div>
    <div className="dashboard-grid data-grid"><div className="grid-5"><DistributionChart rows={records(data.target_distribution)} /></div><div className="grid-7"><CountryChart rows={records(data.functionality_by_country)} /></div>
      <div className="grid-6"><HorizontalBars title="Columns with highest missingness" subtitle="Top 10 by missing value percentage" rows={records(data.missing_values).slice(-10).reverse().map((row) => ({ ...row, label: String(row.column).replaceAll("_", " "), percent: Number(row.missing_percent) }))} nameKey="label" valueKey="percent" color={CHART_COLORS.mistBlue} /></div>
      <div className="grid-6"><Card title="Dataset notes" subtitle="Scope and interpretation"><ul className="insight-list"><li><b>Target:</b> functionality status (`functional3`) across three classes.</li><li><b>Missingness:</b> 40 columns contain at least one missing value; missing values are handled within the production pipeline.</li><li><b>Duplicates:</b> {String(summary.duplicate_rows ?? "—")} duplicate rows were recorded.</li><li><b>Source:</b> full dataset descriptive analysis before the locked model split.</li></ul><p className="metric-note">These charts describe historical data and do not imply that any feature causes functionality.</p></Card></div>
      <div className="grid-12"><Card title="Missingness profile" subtitle="Top twenty fields · percent missing"><div className="chart-area tall"><ResponsiveContainer width="100%" height="100%"><BarChart data={records(data.missing_values)} layout="vertical" margin={{ left: 42, right: 18, top: 4, bottom: 0 }}><CartesianGrid horizontal={false} stroke="#EAF0F4" /><XAxis type="number" domain={[0,100]} tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} /><YAxis type="category" dataKey="column" width={160} tickFormatter={(v) => String(v).replaceAll("_", " ")} tickLine={false} axisLine={false} tick={{ fill: "#64788A", fontSize: 10 }} /><Tooltip formatter={(v) => `${Number(v).toFixed(1)}%`} /><Bar dataKey="missing_percent" name="Missing" fill="#4D728F" radius={[0,6,6,0]} barSize={11} /></BarChart></ResponsiveContainer></div></Card></div>
    </div>
  </div>;
}
