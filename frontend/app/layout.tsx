import type { Metadata } from "next";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

export const metadata: Metadata = {
  title: "WaterPoint Intelligence | Functionality Dashboard",
  description: "Dataset insights and water point functionality prediction using the rural water infrastructure model.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning><body><SiteHeader /><main className="main-shell">{children}</main><footer className="site-footer"><span>WaterPoint Intelligence</span><span>Rural Water Point Functionality · Data Mining Project</span></footer></body></html>;
}
