"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Droplets, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

const links = [
  ["Dashboard", "/"], ["Predict", "/predict"], ["Data Insights", "/data-insights"],
  ["Model Insights", "/model-insights"], ["About", "/about"],
] as const;

export function SiteHeader() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const [online, setOnline] = useState<boolean | null>(null);
  useEffect(() => { getHealth().then((health) => setOnline(health.model_loaded)).catch(() => setOnline(false)); }, []);
  return <header className="site-header">
    <div className="header-inner">
      <Link href="/" className="brand" aria-label="WaterPoint Intelligence dashboard"><span className="brand-icon"><Droplets size={20} /></span><span><strong>WaterPoint</strong><small>INTELLIGENCE</small></span></Link>
      <nav className="desktop-nav" aria-label="Primary navigation">{links.map(([label, href]) => <Link key={href} href={href} className={`nav-link ${path === href ? "active" : ""}`}>{label}</Link>)}</nav>
      <div className={`api-status ${online === true ? "online" : online === false ? "offline" : "checking"}`}><span className="sr-only">API status: </span><span className="status-dot" />{online === true ? "API Online" : online === false ? "API Offline" : "Checking API"}</div>
      <button className="menu-toggle" type="button" aria-label={open ? "Close navigation menu" : "Open navigation menu"} aria-expanded={open} onClick={() => setOpen((value) => !value)}>{open ? <X /> : <Menu />}</button>
    </div>
    <nav className={`mobile-nav ${open ? "open" : ""}`} aria-label="Mobile navigation" aria-hidden={!open} inert={!open}>{links.map(([label, href]) => <Link key={href} href={href} onClick={() => setOpen(false)} className={path === href ? "active" : ""}>{label}</Link>)}</nav>
  </header>;
}
