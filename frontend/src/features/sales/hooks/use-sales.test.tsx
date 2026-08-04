import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useSalesOverview } from "@/features/sales/hooks/use-sales";
import * as salesService from "@/services/sales";

vi.mock("@/services/sales", async () => {
  const actual = await vi.importActual<typeof salesService>("@/services/sales");
  return {
    ...actual,
    salesApi: {
      overview: vi.fn(),
      trends: vi.fn(),
      categoryPerformance: vi.fn(),
      productPerformance: vi.fn(),
      regionalPerformance: vi.fn(),
      topCustomers: vi.fn(),
    },
  };
});

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useSalesOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads sales overview metrics", async () => {
    vi.mocked(salesService.salesApi.overview).mockResolvedValue({
      metrics: [
        {
          id: "revenue",
          label: "Revenue",
          value: 1000,
          formatted_value: "$1,000",
          unit: "USD",
          delta: 0.1,
          delta_label: "vs prior",
          trend: "up",
          format: "currency",
          available: true,
          source: "sales_summary",
        },
      ],
      period_start: "2024-01-01",
      period_end: "2024-01-31",
      generated_at: "2024-02-01T00:00:00Z",
    });

    const filters = { dateFrom: "2024-01-01", dateTo: "2024-01-31" };
    const { result } = renderHook(() => useSalesOverview(filters), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.id).toBe("revenue");
    expect(salesService.salesApi.overview).toHaveBeenCalledWith(filters);
  });

  it("surfaces unavailable metrics without inventing values", async () => {
    vi.mocked(salesService.salesApi.overview).mockResolvedValue({
      metrics: [
        {
          id: "growth",
          label: "Growth",
          value: null,
          formatted_value: null,
          unit: null,
          delta: null,
          delta_label: null,
          trend: null,
          format: "percent",
          available: false,
          source: "sales_summary",
        },
      ],
      period_start: null,
      period_end: null,
      generated_at: "2024-02-01T00:00:00Z",
    });

    const { result } = renderHook(() => useSalesOverview({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.available).toBe(false);
    expect(result.current.data?.metrics[0]?.value).toBeNull();
  });
});
