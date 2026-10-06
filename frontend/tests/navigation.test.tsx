import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { SiteHeader } from "@/components/site-header";
import { getHealth } from "@/lib/api";

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("@/lib/api", () => ({ getHealth: vi.fn() }));
afterEach(() => cleanup());

describe("responsive navigation", () => {
  it("opens the mobile navigation links", async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: "ok", model_loaded: true });
    render(<SiteHeader />);
    fireEvent.click(screen.getByRole("button", { name: "Open navigation menu" }));
    const nav = screen.getByRole("navigation", { name: "Mobile navigation" });
    expect(within(nav).getByRole("link", { name: "Predict" })).toBeInTheDocument();
    expect(within(nav).getAllByRole("link")).toHaveLength(5);
  });
});
