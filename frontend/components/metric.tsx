import type { LucideIcon } from "lucide-react";

export function Metric({ icon: Icon, value, label, note }: { icon: LucideIcon; value: string; label: string; note: string }) {
  return <article className="metric-card"><span className="metric-icon"><Icon size={18} /></span><div className="metric-value">{value}</div><div className="metric-label">{label}</div><div className="metric-note">{note}</div></article>;
}
