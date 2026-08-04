/**
 * Finance Intelligence API client.
 */

import { apiFetch } from "@/services/api-client";

export type FinanceMetric = {
  id: string;
  label: string;
  value: number | null;
  formatted_value: string | null;
  unit: string | null;
  delta: number | null;
  delta_label: string | null;
  trend: "up" | "down" | "flat" | null;
  format: "currency" | "percent" | "number" | null;
  available: boolean;
  source: string | null;
};

export type FinanceOverview = {
  metrics: FinanceMetric[];
  period_start: string | null;
  period_end: string | null;
  generated_at: string;
};

export type ProfitabilityRow = {
  region: string;
  revenue: number | null;
  cost: number | null;
  profit: number | null;
  margin: number | null;
  growth: number | null;
};

export type Profitability = {
  rows: ProfitabilityRow[];
  available: boolean;
};

export type CostBreakdownRow = {
  cost_category: string;
  amount: number | null;
  percentage: number | null;
  trend: "up" | "down" | "flat" | null;
};

export type CostBreakdown = {
  rows: CostBreakdownRow[];
  available: boolean;
};

export type CashflowRow = {
  period: string;
  inflows: number | null;
  outflows: number | null;
  net_cashflow: number | null;
  profit: number | null;
  margin: number | null;
};

export type Cashflow = {
  rows: CashflowRow[];
  available: boolean;
};

export type FinancialRiskRow = {
  risk: string;
  severity: "low" | "medium" | "high" | "critical";
  estimated_impact: number | null;
  owner: string | null;
  recommendation: string | null;
};

export type FinancialRisks = {
  rows: FinancialRiskRow[];
  available: boolean;
};

export type BudgetVarianceRow = {
  department: string;
  budget: number | null;
  actual: number | null;
  variance: number | null;
  variance_pct: number | null;
};

export type BudgetVariance = {
  rows: BudgetVarianceRow[];
  available: boolean;
};

export type FinanceQueryParams = {
  dateFrom?: string;
  dateTo?: string;
  regionIds?: string[];
  departmentIds?: string[];
  costCategoryIds?: string[];
  search?: string;
};

function toQuery(params: Record<string, string | number | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    sp.set(key, String(value));
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
}

function filterParams(filters: FinanceQueryParams) {
  return {
    date_from: filters.dateFrom || undefined,
    date_to: filters.dateTo || undefined,
    region: filters.regionIds?.length ? filters.regionIds.join(",") : undefined,
    department: filters.departmentIds?.length
      ? filters.departmentIds.join(",")
      : undefined,
    cost_category: filters.costCategoryIds?.length
      ? filters.costCategoryIds.join(",")
      : undefined,
    search: filters.search || undefined,
  };
}

const BASE = "/api/v1/finance";

export const financeApi = {
  overview: (filters: FinanceQueryParams = {}) =>
    apiFetch<FinanceOverview>(`${BASE}/overview${toQuery(filterParams(filters))}`),
  profitability: (filters: FinanceQueryParams = {}) =>
    apiFetch<Profitability>(`${BASE}/profitability${toQuery(filterParams(filters))}`),
  costBreakdown: (filters: FinanceQueryParams = {}) =>
    apiFetch<CostBreakdown>(`${BASE}/cost-breakdown${toQuery(filterParams(filters))}`),
  cashflow: (filters: FinanceQueryParams = {}) =>
    apiFetch<Cashflow>(`${BASE}/cashflow${toQuery(filterParams(filters))}`),
  financialRisks: (filters: FinanceQueryParams = {}) =>
    apiFetch<FinancialRisks>(
      `${BASE}/financial-risks${toQuery(filterParams(filters))}`,
    ),
  budgetVariance: (filters: FinanceQueryParams = {}) =>
    apiFetch<BudgetVariance>(
      `${BASE}/budget-variance${toQuery(filterParams(filters))}`,
    ),
};

export const financeQueryKeys = {
  all: ["finance"] as const,
  overview: (filters: FinanceQueryParams) =>
    [...financeQueryKeys.all, "overview", filters] as const,
  profitability: (filters: FinanceQueryParams) =>
    [...financeQueryKeys.all, "profitability", filters] as const,
  costs: (filters: FinanceQueryParams) =>
    [...financeQueryKeys.all, "costs", filters] as const,
  cashflow: (filters: FinanceQueryParams) =>
    [...financeQueryKeys.all, "cashflow", filters] as const,
  risks: (filters: FinanceQueryParams) =>
    [...financeQueryKeys.all, "risks", filters] as const,
  budget: (filters: FinanceQueryParams) =>
    [...financeQueryKeys.all, "budget", filters] as const,
};
