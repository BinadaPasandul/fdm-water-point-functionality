"use client";

import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReactNode } from "react";
import { Card } from "./ui";
import { CHART_COLORS, CHART_PALETTE, classColors } from "@/lib/api";

const palette = CHART_PALETTE;
const fmt = (value: number) => `${Number(value).toFixed(1)}%`;
function EmptyChart() { return <div className="chart-empty"><span>No chart data is available.</span></div>; }

export function DistributionChart({ rows }: { rows: Record<string, string | number>[] }) {
  if (!rows.length) return <Card title="Functionality distribution" subtitle="Recorded status across water points"><EmptyChart /></Card>;
  return <Card title="Functionality distribution" subtitle="Recorded status across all 1,793 water points"><div className="chart-area donut-area"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={rows} dataKey="percentage" nameKey="class" innerRadius={62} outerRadius={91} paddingAngle={3} stroke="none">{rows.map((row) => <Cell key={String(row.class)} fill={classColors[String(row.class)] ?? palette[0]} />)}</Pie><Tooltip formatter={(value) => fmt(Number(value))} /></PieChart></ResponsiveContainer></div><div className="class-legend">{rows.map((row) => <div key={String(row.class)}><i style={{ background: classColors[String(row.class)] ?? palette[0] }} /><span>{String(row.class)}</span><b>{fmt(Number(row.percentage))}</b></div>)}</div></Card>;
}

export function CountryChart({ rows }: { rows: Record<string, string | number>[] }) {
  if (!rows.length) return <Card title="Functionality by country" subtitle="Within-country class distribution · percent"><EmptyChart /></Card>;
  return <Card title="Functionality by country" subtitle="Within-country class distribution · percent"><div className="chart-area country-chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} margin={{ top: 8, right: 8, left: -16, bottom: 28 }}><CartesianGrid vertical={false} stroke="#EAF0F4" /><XAxis dataKey="country" interval={0} angle={-25} textAnchor="end" height={54} tickLine={false} axisLine={false} tick={{ fill: "#64788A", fontSize: 10 }} /><YAxis tickLine={false} axisLine={false} tick={{ fill: "#8A9BA9", fontSize: 11 }} tickFormatter={(value) => `${value}%`} /><Tooltip formatter={(value) => fmt(Number(value))} /><Bar dataKey="Functional" stackId="a" fill={classColors.Functional} radius={[0, 0, 0, 0]} /><Bar dataKey="Partially functional" stackId="a" fill={classColors["Partially functional"]} /><Bar dataKey="Abandoned or not functional" stackId="a" fill={classColors["Abandoned or not functional"]} radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div><div className="class-legend compact"><div><i style={{ background: classColors.Functional }} /><span>Functional</span></div><div><i style={{ background: classColors["Partially functional"] }} /><span>Partially functional</span></div><div><i style={{ background: classColors["Abandoned or not functional"] }} /><span>Abandoned or not functional</span></div></div></Card>;
}

export function HorizontalBars({ title, subtitle, rows, nameKey, valueKey, color = palette[0], footer }: { title: string; subtitle?: string; rows: Record<string, string | number>[]; nameKey: string; valueKey: string; color?: string; footer?: ReactNode }) {
  if (!rows.length) return <Card title={title} subtitle={subtitle}><EmptyChart /></Card>;
  return <Card title={title} subtitle={subtitle}><div className="chart-area"><ResponsiveContainer width="100%" height="100%"><BarChart data={rows} layout="vertical" margin={{ top: 2, right: 18, left: 22, bottom: 0 }}><CartesianGrid horizontal={false} stroke="#EAF0F4" /><XAxis type="number" tickLine={false} axisLine={false} tick={{ fill: "#8A9BA9", fontSize: 11 }} /><YAxis type="category" dataKey={nameKey} width={170} tickLine={false} axisLine={false} tick={{ fill: CHART_COLORS.muted, fontSize: 11 }} /><Tooltip formatter={(value) => Number(value).toFixed(3)} /><Bar dataKey={valueKey} fill={color} radius={[0, 6, 6, 0]} barSize={17} /></BarChart></ResponsiveContainer></div>{footer}</Card>;
}

export function PerformanceLines({ rows }: { rows: Record<string, string | number>[] }) {
  if (!rows.length) return <Card title="Learning curve" subtitle="Macro-F1 across increasing training set sizes"><EmptyChart /></Card>;
  return <Card title="Learning curve" subtitle="Macro-F1 across increasing training set sizes"><div className="chart-area tall"><ResponsiveContainer width="100%" height="100%"><LineChart data={rows} margin={{ top: 10, right: 18, left: -12, bottom: 0 }}><CartesianGrid stroke="#EAF0F4" vertical={false} /><XAxis dataKey="train_rows" tickLine={false} axisLine={false} tick={{ fill: "#64788A", fontSize: 11 }} label={{ value: "Training rows", position: "insideBottom", offset: -2, fill: "#8A9BA9", fontSize: 11 }} /><YAxis domain={[0, 1]} tickLine={false} axisLine={false} tick={{ fill: "#8A9BA9", fontSize: 11 }} /><Tooltip formatter={(value) => Number(value).toFixed(3)} /><Legend /><Line type="monotone" dataKey="train_macro_f1_mean" name="Training Macro-F1" stroke={palette[0]} strokeWidth={2.5} dot={{ r: 3 }} /><Line type="monotone" dataKey="cv_macro_f1_mean" name="Cross-validation Macro-F1" stroke="#25C9D0" strokeWidth={2.5} dot={{ r: 3 }} /></LineChart></ResponsiveContainer></div></Card>;
}

export function ConfusionTable({ rows }: { rows: Record<string, string | number>[] }) {
  if (!rows.length) return <Card title="Historical holdout confusion matrix" subtitle="Counts · rows show actual class, columns show predicted class"><EmptyChart /></Card>;
  const classes = ["Functional", "Partially functional", "Abandoned or not functional"];
  return <Card title="Historical holdout confusion matrix" subtitle="Counts · rows show actual class, columns show predicted class"><div className="table-wrap"><table className="data-table"><thead><tr><th>Actual / predicted</th>{classes.map((label) => <th key={label}>{label}</th>)}</tr></thead><tbody>{classes.map((actual) => <tr key={actual}><th>{actual}</th>{classes.map((predicted) => { const item = rows.find((row) => row.actual === actual && row.predicted === predicted); return <td key={predicted}>{item?.count ?? "—"}</td>; })}</tr>)}</tbody></table></div></Card>;
}
