import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { CustomerIntelligencePage } from "@/features/customers/components/customer-intelligence-page";
import * as customerHooks from "@/features/customers/hooks/use-customers";

const searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/customers",
  useSearchParams: () => searchParams,
}));

vi.mock("@/features/customers/hooks/use-customers", () => ({
  useCustomerOverview: vi.fn(),
  useRfmSegments: vi.fn(),
  useCustomerCohorts: vi.fn(),
  useCustomerDistribution: vi.fn(),
  useTopCustomersDetail: vi.fn(),
  useChurnRisk: vi.fn(),
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

describe("CustomerIntelligencePage", () => {
  it("renders layout and unavailable KPI label", () => {
    vi.mocked(customerHooks.useCustomerOverview).mockReturnValue(
      idleQuery({
        metrics: [
          {
            id: "active_customers",
            label: "Active Customers",
            value: null,
            formatted_value: null,
            unit: null,
            delta: null,
            delta_label: null,
            trend: null,
            format: "number",
            available: false,
            source: "customer_360",
          },
        ],
        period_start: null,
        period_end: null,
        generated_at: "2024-02-01T00:00:00Z",
      }) as never,
    );
    vi.mocked(customerHooks.useRfmSegments).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(customerHooks.useCustomerCohorts).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(customerHooks.useCustomerDistribution).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(customerHooks.useTopCustomersDetail).mockReturnValue(
      idleQuery({
        rows: [],
        pagination: { page: 1, page_size: 10, total_items: 0, total_pages: 0 },
        available: false,
      }) as never,
    );
    vi.mocked(customerHooks.useChurnRisk).mockReturnValue(
      idleQuery({ rows: [], available: false, source: null }) as never,
    );

    render(<CustomerIntelligencePage />, { wrapper });

    expect(screen.getByRole("heading", { name: "Customer Intelligence" })).toBeTruthy();
    expect(screen.getByText("Unavailable")).toBeTruthy();
    expect(screen.getByLabelText("Analytics filters")).toBeTruthy();
    expect(screen.getByText("Customer Segment")).toBeTruthy();
  });
});
