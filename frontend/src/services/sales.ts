/**
 * Sales Intelligence API client.
 */

import { apiFetch } from "@/services/api-client";

export type SalesMetric = {
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

export type SalesOverview = {
  metrics: SalesMetric[];
  period_start: string | null;
  period_end: string | null;
  generated_at: string;
};

export type SalesTrendPoint = {
  period: string;
  revenue: number | null;
  orders: number | null;
  profit: number | null;
};

export type SalesTrends = {
  points: SalesTrendPoint[];
  grain: "daily" | "weekly" | "monthly";
  available: boolean;
};

export type CategoryPerformanceRow = {
  category: string;
  revenue: number | null;
  orders: number | null;
  growth: number | null;
  margin: number | null;
};

export type CategoryPerformance = {
  rows: CategoryPerformanceRow[];
  available: boolean;
};

export type ProductPerformanceRow = {
  product_id: string | null;
  product: string;
  sku: string | null;
  category: string | null;
  revenue: number | null;
  orders: number | null;
  units: number | null;
  margin: number | null;
  growth: number | null;
};

export type ProductPerformance = {
  rows: ProductPerformanceRow[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
  available: boolean;
};

export type RegionalSalesRow = {
  region: string;
  revenue: number | null;
  orders: number | null;
  growth: number | null;
};

export type RegionalSales = {
  rows: RegionalSalesRow[];
  available: boolean;
};

export type TopCustomerRow = {
  customer: string;
  customer_id: string | null;
  revenue: number | null;
  orders: number | null;
  lifetime_value: number | null;
  lifetime_value_available: boolean;
};

export type TopCustomers = {
  rows: TopCustomerRow[];
  available: boolean;
};

export type SalesQueryParams = {
  dateFrom?: string;
  dateTo?: string;
  regionIds?: string[];
  categoryIds?: string[];
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

function filterParams(filters: SalesQueryParams) {
  return {
    date_from: filters.dateFrom || undefined,
    date_to: filters.dateTo || undefined,
    region: filters.regionIds?.length ? filters.regionIds.join(",") : undefined,
    category: filters.categoryIds?.length ? filters.categoryIds.join(",") : undefined,
    search: filters.search || undefined,
  };
}

const BASE = "/api/v1/sales";

export const salesApi = {
  overview: (filters: SalesQueryParams = {}) =>
    apiFetch<SalesOverview>(`${BASE}/overview${toQuery(filterParams(filters))}`),
  trends: (grain: "daily" | "weekly" | "monthly", filters: SalesQueryParams = {}) =>
    apiFetch<SalesTrends>(
      `${BASE}/trends${toQuery({ ...filterParams(filters), grain })}`,
    ),
  categoryPerformance: (filters: SalesQueryParams = {}) =>
    apiFetch<CategoryPerformance>(
      `${BASE}/category-performance${toQuery(filterParams(filters))}`,
    ),
  productPerformance: (
    options: SalesQueryParams & {
      page?: number;
      pageSize?: number;
      sortBy?: string;
      sortDir?: "asc" | "desc";
    } = {},
  ) =>
    apiFetch<ProductPerformance>(
      `${BASE}/product-performance${toQuery({
        ...filterParams(options),
        page: options.page ?? 1,
        page_size: options.pageSize ?? 10,
        sort_by: options.sortBy ?? "revenue",
        sort_dir: options.sortDir ?? "desc",
      })}`,
    ),
  regionalPerformance: (filters: SalesQueryParams = {}) =>
    apiFetch<RegionalSales>(
      `${BASE}/regional-performance${toQuery(filterParams(filters))}`,
    ),
  topCustomers: (limit = 10, search?: string) =>
    apiFetch<TopCustomers>(
      `${BASE}/top-customers${toQuery({ limit, search: search || undefined })}`,
    ),
};

export const salesQueryKeys = {
  all: ["sales"] as const,
  overview: (filters: SalesQueryParams) =>
    [...salesQueryKeys.all, "overview", filters] as const,
  trends: (grain: string, filters: SalesQueryParams) =>
    [...salesQueryKeys.all, "trends", grain, filters] as const,
  category: (filters: SalesQueryParams) =>
    [...salesQueryKeys.all, "category", filters] as const,
  products: (filters: SalesQueryParams & { page?: number; search?: string }) =>
    [...salesQueryKeys.all, "products", filters] as const,
  regional: (filters: SalesQueryParams) =>
    [...salesQueryKeys.all, "regional", filters] as const,
  customers: (limit: number, search?: string) =>
    [...salesQueryKeys.all, "customers", limit, search] as const,
};
