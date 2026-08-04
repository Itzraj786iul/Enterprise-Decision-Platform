import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { SalesIntelligencePage } from "@/features/sales/components/sales-intelligence-page";
import * as salesHooks from "@/features/sales/hooks/use-sales";

const searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/sales",
  useSearchParams: () => searchParams,
}));

vi.mock("@/features/sales/hooks/use-sales", () => ({
  useSalesOverview: vi.fn(),
  useSalesTrends: vi.fn(),
  useCategoryPerformance: vi.fn(),
  useProductPerformance: vi.fn(),
  useRegionalSales: vi.fn(),
  useTopCustomers: vi.fn(),
}));

function idleQuery<T>(data: T) {
  return {
    data,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    isSuccess: true,
  };
}

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("SalesIntelligencePage", () => {
  it("renders layout and unavailable KPI label", () => {
    vi.mocked(salesHooks.useSalesOverview).mockReturnValue(
      idleQuery({
        metrics: [
          {
            id: "revenue",
            label: "Revenue",
            value: null,
            formatted_value: null,
            unit: null,
            delta: null,
            delta_label: null,
            trend: null,
            format: "currency",
            available: false,
            source: "sales_summary",
          },
        ],
        period_start: null,
        period_end: null,
        generated_at: "2024-02-01T00:00:00Z",
      }) as never,
    );
    vi.mocked(salesHooks.useSalesTrends).mockReturnValue(
      idleQuery({ points: [], grain: "daily", available: false }) as never,
    );
    vi.mocked(salesHooks.useRegionalSales).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(salesHooks.useCategoryPerformance).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(salesHooks.useProductPerformance).mockReturnValue(
      idleQuery({
        rows: [],
        pagination: { page: 1, page_size: 8, total_items: 0, total_pages: 0 },
        available: false,
      }) as never,
    );
    vi.mocked(salesHooks.useTopCustomers).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );

    render(<SalesIntelligencePage />, { wrapper });

    expect(screen.getByRole("heading", { name: "Sales Intelligence" })).toBeTruthy();
    expect(screen.getByText("Unavailable")).toBeTruthy();
    expect(screen.getByLabelText("Analytics filters")).toBeTruthy();
  });
});
