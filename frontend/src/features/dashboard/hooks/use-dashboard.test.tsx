import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useDashboardOverview } from "@/features/dashboard/hooks/use-dashboard";
import * as dashboardService from "@/services/dashboard";

vi.mock("@/services/dashboard", async () => {
  const actual = await vi.importActual<typeof dashboardService>("@/services/dashboard");
  return {
    ...actual,
    dashboardApi: {
      overview: vi.fn(),
      trends: vi.fn(),
      regionalPerformance: vi.fn(),
      topRisks: vi.fn(),
      opportunities: vi.fn(),
    },
  };
});

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useDashboardOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads overview metrics", async () => {
    vi.mocked(dashboardService.dashboardApi.overview).mockResolvedValue({
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
          source: "executive_scorecard",
        },
      ],
      period_start: "2024-01-01",
      period_end: "2024-01-31",
      generated_at: "2024-02-01T00:00:00Z",
    });

    const { result } = renderHook(() => useDashboardOverview(30), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.id).toBe("revenue");
    expect(dashboardService.dashboardApi.overview).toHaveBeenCalledWith(30);
  });
});
