import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useCustomerOverview } from "@/features/customers/hooks/use-customers";
import * as customersService from "@/services/customers";

vi.mock("@/services/customers", async () => {
  const actual = await vi.importActual<typeof customersService>("@/services/customers");
  return {
    ...actual,
    customersApi: {
      overview: vi.fn(),
      rfmSegments: vi.fn(),
      cohorts: vi.fn(),
      distribution: vi.fn(),
      topCustomers: vi.fn(),
      churnRisk: vi.fn(),
    },
  };
});

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

describe("useCustomerOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads customer overview metrics", async () => {
    vi.mocked(customersService.customersApi.overview).mockResolvedValue({
      metrics: [
        {
          id: "active_customers",
          label: "Active Customers",
          value: 120,
          formatted_value: "120",
          unit: null,
          delta: null,
          delta_label: null,
          trend: null,
          format: "number",
          available: true,
          source: "customer_360",
        },
      ],
      period_start: "2024-01-01",
      period_end: "2024-01-31",
      generated_at: "2024-02-01T00:00:00Z",
    });

    const filters = { dateFrom: "2024-01-01" };
    const { result } = renderHook(() => useCustomerOverview(filters), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.id).toBe("active_customers");
    expect(customersService.customersApi.overview).toHaveBeenCalledWith(filters);
  });

  it("preserves unavailable metrics", async () => {
    vi.mocked(customersService.customersApi.overview).mockResolvedValue({
      metrics: [
        {
          id: "retention_rate",
          label: "Retention Rate",
          value: null,
          formatted_value: null,
          unit: null,
          delta: null,
          delta_label: null,
          trend: null,
          format: "percent",
          available: false,
          source: "customer_360",
        },
      ],
      period_start: null,
      period_end: null,
      generated_at: "2024-02-01T00:00:00Z",
    });

    const { result } = renderHook(() => useCustomerOverview({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.metrics[0]?.available).toBe(false);
  });
});
