import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useFinanceOverview } from "@/features/finance/hooks/use-finance";
import * as financeService from "@/services/finance";

vi.mock("@/services/finance", async () => {
  const actual = await vi.importActual<typeof financeService>("@/services/finance");
  return {
    ...actual,
    financeApi: {
      overview: vi.fn(),
      profitability: vi.fn(),
      costBreakdown: vi.fn(),
      cashflow: vi.fn(),
      financialRisks: vi.fn(),
      budgetVariance: vi.fn(),
    },
  };
});

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useFinanceOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads finance overview metrics", async () => {
    vi.mocked(financeService.financeApi.overview).mockResolvedValue({
      metrics: [
        {
          id: "revenue",
          label: "Revenue",
          value: 10000,
          formatted_value: "$10,000",
          unit: "USD",
          delta: null,
          delta_label: null,
          trend: null,
          format: "currency",
          available: true,
          source: "sales_summary",
        },
      ],
      period_start: "2024-01-01",
      period_end: "2024-01-31",
      generated_at: "2024-02-01T00:00:00Z",
    });

    const filters = { regionIds: ["West"] };
    const { result } = renderHook(() => useFinanceOverview(filters), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.id).toBe("revenue");
    expect(financeService.financeApi.overview).toHaveBeenCalledWith(filters);
  });

  it("preserves unavailable metrics", async () => {
    vi.mocked(financeService.financeApi.overview).mockResolvedValue({
      metrics: [
        {
          id: "net_profit",
          label: "Net Profit",
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
    });

    const { result } = renderHook(() => useFinanceOverview({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.available).toBe(false);
  });
});
