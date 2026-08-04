import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useOperationsOverview } from "@/features/operations/hooks/use-operations";
import * as operationsService from "@/services/operations";

vi.mock("@/services/operations", async () => {
  const actual = await vi.importActual<typeof operationsService>("@/services/operations");
  return {
    ...actual,
    operationsApi: {
      overview: vi.fn(),
      inventory: vi.fn(),
      supplierPerformance: vi.fn(),
      returns: vi.fn(),
      warehousePerformance: vi.fn(),
      operationalRisks: vi.fn(),
    },
  };
});

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useOperationsOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads operations overview metrics", async () => {
    vi.mocked(operationsService.operationsApi.overview).mockResolvedValue({
      metrics: [
        {
          id: "inventory_value",
          label: "Inventory Value",
          value: 5000,
          formatted_value: "$5,000",
          unit: "USD",
          delta: null,
          delta_label: null,
          trend: null,
          format: "currency",
          available: true,
          source: "inventory_summary",
        },
      ],
      period_start: null,
      period_end: null,
      generated_at: "2024-02-01T00:00:00Z",
    });

    const filters = { regionIds: ["West"] };
    const { result } = renderHook(() => useOperationsOverview(filters), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.id).toBe("inventory_value");
    expect(operationsService.operationsApi.overview).toHaveBeenCalledWith(filters);
  });

  it("preserves unavailable metrics", async () => {
    vi.mocked(operationsService.operationsApi.overview).mockResolvedValue({
      metrics: [
        {
          id: "stock_turnover",
          label: "Stock Turnover",
          value: null,
          formatted_value: null,
          unit: null,
          delta: null,
          delta_label: null,
          trend: null,
          format: "number",
          available: false,
          source: "inventory_summary+sales_summary",
        },
      ],
      period_start: null,
      period_end: null,
      generated_at: "2024-02-01T00:00:00Z",
    });

    const { result } = renderHook(() => useOperationsOverview({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.available).toBe(false);
  });
});
