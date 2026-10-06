import type { ReactNode } from "react";
import { AlertCircle, RefreshCw } from "lucide-react";

export function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p className="page-description">{description}</p></div>{action}</div>;
}

export function Card({ title, subtitle, children, className = "" }: { title: string; subtitle?: string; children: ReactNode; className?: string }) {
  return <section className={`card ${className}`}><div className="card-heading"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div></div>{children}</section>;
}

export function ErrorPanel({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error-panel" role="alert"><AlertCircle size={19} /><div><strong>Insights unavailable</strong><p>{message}</p></div>{retry && <button type="button" className="icon-button" aria-label="Retry loading data" onClick={retry}><RefreshCw size={16} /></button>}</div>;
}

export function SkeletonGrid() {
  return <div className="skeleton-grid" aria-label="Loading dashboard data"><div className="skeleton kpi-skeleton" /><div className="skeleton kpi-skeleton" /><div className="skeleton kpi-skeleton" /><div className="skeleton kpi-skeleton" /><div className="skeleton chart-skeleton wide" /><div className="skeleton chart-skeleton" /><div className="skeleton chart-skeleton" /><div className="skeleton chart-skeleton wide" /></div>;
}
