import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { FinanceIntelligencePage } from "@/features/finance/components/finance-intelligence-page";
import * as financeHooks from "@/features/finance/hooks/use-finance";

const searchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/finance",
  useSearchParams: () => searchParams,
}));

vi.mock("@/features/finance/hooks/use-finance", () => ({
  useFinanceOverview: vi.fn(),
  useProfitability: vi.fn(),
  useCostBreakdown: vi.fn(),
  useCashflow: vi.fn(),
  useFinancialRisks: vi.fn(),
  useBudgetVariance: vi.fn(),
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

describe("FinanceIntelligencePage", () => {
  it("renders layout and unavailable KPI label", () => {
    vi.mocked(financeHooks.useFinanceOverview).mockReturnValue(
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
    vi.mocked(financeHooks.useProfitability).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(financeHooks.useCostBreakdown).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(financeHooks.useCashflow).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(financeHooks.useFinancialRisks).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );
    vi.mocked(financeHooks.useBudgetVariance).mockReturnValue(
      idleQuery({ rows: [], available: false }) as never,
    );

    render(<FinanceIntelligencePage />, { wrapper });

    expect(screen.getByRole("heading", { name: "Finance Intelligence" })).toBeTruthy();
    expect(screen.getByText("Unavailable")).toBeTruthy();
    expect(screen.getByLabelText("Analytics filters")).toBeTruthy();
    expect(screen.getByLabelText("Department")).toBeTruthy();
    expect(screen.getByLabelText("Cost Category")).toBeTruthy();
  });
});
