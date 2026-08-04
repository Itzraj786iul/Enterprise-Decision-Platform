import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { OperationsIntelligencePage } from "@/features/operations/components/operations-intelligence-page";
import * as operationsHooks from "@/features/operations/hooks/use-operations";

const searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/operations",
  useSearchParams: () => searchParams,
}));

vi.mock("@/features/operations/hooks/use-operations", () => ({
  useOperationsOverview: vi.fn(),
  useOperationsInventory: vi.fn(),
  useSupplierPerformance: vi.fn(),
  useOperationsReturns: vi.fn(),
  useWarehousePerformance: vi.fn(),
  useOperationalRisks: vi.fn(),
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

describe("OperationsIntelligencePage", () => {
  it("renders layout and unavailable KPI label", () => {
    vi.mocked(operationsHooks.useOperationsOverview).mockReturnValue(
      idleQuery({
        metrics: [
          {
            id: "inventory_value",
            label: "Inventory Value",
            value: null,
            formatted_value: null,
            unit: null,
            delta: null,
            delta_label: null,
            trend: null,
            format: "currency",
            available: false,
            source: "inventory_summary",
          },
        ],
        period_start: null,
        period_end: null,
        generated_at: "2024-02-01T00:00:00Z",
      }) as never,
    );
    vi.mocked(operationsHooks.useOperationsInventory).mockReturnValue(
      idleQuery({
        rows: [],
        pagination: { page: 1, page_size: 10, total_items: 0, total_pages: 0 },
        available: false,
      }) as never,
    );
    vi.mocked(operationsHooks.useSupplierPerformance).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(operationsHooks.useOperationsReturns).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(operationsHooks.useWarehousePerformance).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(operationsHooks.useOperationalRisks).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );

    render(<OperationsIntelligencePage />, { wrapper });

    expect(screen.getByRole("heading", { name: "Operations Intelligence" })).toBeTruthy();
    expect(screen.getByText("Unavailable")).toBeTruthy();
    expect(screen.getByLabelText("Analytics filters")).toBeTruthy();
    expect(screen.getByText("Supplier")).toBeTruthy();
  });
});
