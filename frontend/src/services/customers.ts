/**
 * Customer Intelligence API client.
 */

import { apiFetch } from "@/services/api-client";

export type CustomerMetric = {
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

export type CustomerOverview = {
  metrics: CustomerMetric[];
  period_start: string | null;
  period_end: string | null;
  generated_at: string;
};

export type RfmSegmentRow = {
  segment: string;
  customer_count: number | null;
  revenue: number | null;
  average_order_value: number | null;
  growth: number | null;
};

export type RfmSegments = {
  rows: RfmSegmentRow[];
  available: boolean;
};

export type CohortRetentionCell = {
  month_offset: number;
  retention_pct: number | null;
  customer_count: number | null;
};

export type CohortRow = {
  cohort: string;
  cohort_size: number | null;
  retentions: CohortRetentionCell[];
};

export type Cohorts = {
  rows: CohortRow[];
  available: boolean;
};

export type CustomerDistributionRow = {
  region: string;
  customer_count: number | null;
  revenue: number | null;
  growth: number | null;
};

export type CustomerDistribution = {
  rows: CustomerDistributionRow[];
  available: boolean;
};

export type TopCustomerDetailRow = {
  customer_id: string | null;
  customer: string;
  segment: string | null;
  region: string | null;
  lifetime_value: number | null;
  orders: number | null;
  average_order_value: number | null;
  lifecycle_status: string | null;
  last_order_date: string | null;
};

export type TopCustomersDetail = {
  rows: TopCustomerDetailRow[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
  available: boolean;
};

export type ChurnRiskRow = {
  risk_level: string;
  customer_count: number | null;
  predicted_revenue_at_risk: number | null;
  confidence: number | null;
  confidence_available: boolean;
};

export type ChurnRisk = {
  rows: ChurnRiskRow[];
  available: boolean;
  source: string | null;
};

export type CustomerQueryParams = {
  dateFrom?: string;
  dateTo?: string;
  regionIds?: string[];
  segmentIds?: string[];
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

function filterParams(filters: CustomerQueryParams) {
  return {
    date_from: filters.dateFrom || undefined,
    date_to: filters.dateTo || undefined,
    region: filters.regionIds?.length ? filters.regionIds.join(",") : undefined,
    segment: filters.segmentIds?.length ? filters.segmentIds.join(",") : undefined,
    search: filters.search || undefined,
  };
}

const BASE = "/api/v1/customers";

export const customersApi = {
  overview: (filters: CustomerQueryParams = {}) =>
    apiFetch<CustomerOverview>(`${BASE}/overview${toQuery(filterParams(filters))}`),
  rfmSegments: (filters: CustomerQueryParams = {}) =>
    apiFetch<RfmSegments>(`${BASE}/rfm-segments${toQuery(filterParams(filters))}`),
  cohorts: (filters: CustomerQueryParams = {}) =>
    apiFetch<Cohorts>(`${BASE}/cohorts${toQuery(filterParams(filters))}`),
  distribution: (filters: CustomerQueryParams = {}) =>
    apiFetch<CustomerDistribution>(
      `${BASE}/customer-distribution${toQuery(filterParams(filters))}`,
    ),
  topCustomers: (
    options: CustomerQueryParams & {
      page?: number;
      pageSize?: number;
      sortBy?: string;
      sortDir?: "asc" | "desc";
    } = {},
  ) =>
    apiFetch<TopCustomersDetail>(
      `${BASE}/top-customers${toQuery({
        ...filterParams(options),
        page: options.page ?? 1,
        page_size: options.pageSize ?? 10,
        sort_by: options.sortBy ?? "lifetime_value",
        sort_dir: options.sortDir ?? "desc",
      })}`,
    ),
  churnRisk: (filters: CustomerQueryParams = {}) =>
    apiFetch<ChurnRisk>(`${BASE}/churn-risk${toQuery(filterParams(filters))}`),
};

export const customersQueryKeys = {
  all: ["customers"] as const,
  overview: (filters: CustomerQueryParams) =>
    [...customersQueryKeys.all, "overview", filters] as const,
  rfm: (filters: CustomerQueryParams) =>
    [...customersQueryKeys.all, "rfm", filters] as const,
  cohorts: (filters: CustomerQueryParams) =>
    [...customersQueryKeys.all, "cohorts", filters] as const,
  distribution: (filters: CustomerQueryParams) =>
    [...customersQueryKeys.all, "distribution", filters] as const,
  top: (filters: CustomerQueryParams & { page?: number }) =>
    [...customersQueryKeys.all, "top", filters] as const,
  churn: (filters: CustomerQueryParams) =>
    [...customersQueryKeys.all, "churn", filters] as const,
};
