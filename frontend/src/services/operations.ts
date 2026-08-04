/**
 * Operations Intelligence API client.
 */

import { apiFetch } from "@/services/api-client";

export type OperationsMetric = {
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

export type OperationsOverview = {
  metrics: OperationsMetric[];
  period_start: string | null;
  period_end: string | null;
  generated_at: string;
};

export type InventoryRow = {
  product: string;
  product_id: string | null;
  sku: string | null;
  category: string | null;
  stock: number | null;
  safety_stock: number | null;
  turnover: number | null;
  inventory_value: number | null;
  stock_status: string | null;
};

export type InventoryPage = {
  rows: InventoryRow[];
  pagination: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
  };
  available: boolean;
};

export type SupplierPerformanceRow = {
  supplier: string;
  supplier_id: string | null;
  on_time_pct: number | null;
  quality_score: number | null;
  lead_time: number | null;
  purchase_volume: number | null;
  risk_level: string | null;
};

export type SupplierPerformance = {
  rows: SupplierPerformanceRow[];
  available: boolean;
};

export type ReturnsRow = {
  category: string;
  return_count: number | null;
  return_pct: number | null;
  return_cost: number | null;
  trend: "up" | "down" | "flat" | null;
};

export type Returns = {
  rows: ReturnsRow[];
  available: boolean;
};

export type WarehousePerformanceRow = {
  warehouse: string;
  inventory: number | null;
  fulfillment: number | null;
  stockouts: number | null;
  average_processing_time: number | null;
};

export type WarehousePerformance = {
  rows: WarehousePerformanceRow[];
  available: boolean;
};

export type OperationalRiskRow = {
  risk: string;
  severity: "low" | "medium" | "high" | "critical";
  owner: string | null;
  recommendation: string | null;
};

export type OperationalRisks = {
  rows: OperationalRiskRow[];
  available: boolean;
};

export type OperationsQueryParams = {
  dateFrom?: string;
  dateTo?: string;
  regionIds?: string[];
  categoryIds?: string[];
  supplierIds?: string[];
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

function filterParams(filters: OperationsQueryParams) {
  return {
    date_from: filters.dateFrom || undefined,
    date_to: filters.dateTo || undefined,
    region: filters.regionIds?.length ? filters.regionIds.join(",") : undefined,
    category: filters.categoryIds?.length ? filters.categoryIds.join(",") : undefined,
    supplier: filters.supplierIds?.length ? filters.supplierIds.join(",") : undefined,
    search: filters.search || undefined,
  };
}

const BASE = "/api/v1/operations";

export const operationsApi = {
  overview: (filters: OperationsQueryParams = {}) =>
    apiFetch<OperationsOverview>(`${BASE}/overview${toQuery(filterParams(filters))}`),
  inventory: (
    options: OperationsQueryParams & {
      page?: number;
      pageSize?: number;
      sortBy?: string;
      sortDir?: "asc" | "desc";
    } = {},
  ) =>
    apiFetch<InventoryPage>(
      `${BASE}/inventory${toQuery({
        ...filterParams(options),
        page: options.page ?? 1,
        page_size: options.pageSize ?? 10,
        sort_by: options.sortBy ?? "inventory_value",
        sort_dir: options.sortDir ?? "desc",
      })}`,
    ),
  supplierPerformance: (filters: OperationsQueryParams = {}) =>
    apiFetch<SupplierPerformance>(
      `${BASE}/supplier-performance${toQuery(filterParams(filters))}`,
    ),
  returns: (filters: OperationsQueryParams = {}) =>
    apiFetch<Returns>(`${BASE}/returns${toQuery(filterParams(filters))}`),
  warehousePerformance: (filters: OperationsQueryParams = {}) =>
    apiFetch<WarehousePerformance>(
      `${BASE}/warehouse-performance${toQuery(filterParams(filters))}`,
    ),
  operationalRisks: (filters: OperationsQueryParams = {}) =>
    apiFetch<OperationalRisks>(
      `${BASE}/operational-risks${toQuery(filterParams(filters))}`,
    ),
};

export const operationsQueryKeys = {
  all: ["operations"] as const,
  overview: (filters: OperationsQueryParams) =>
    [...operationsQueryKeys.all, "overview", filters] as const,
  inventory: (filters: OperationsQueryParams & { page?: number }) =>
    [...operationsQueryKeys.all, "inventory", filters] as const,
  suppliers: (filters: OperationsQueryParams) =>
    [...operationsQueryKeys.all, "suppliers", filters] as const,
  returns: (filters: OperationsQueryParams) =>
    [...operationsQueryKeys.all, "returns", filters] as const,
  warehouse: (filters: OperationsQueryParams) =>
    [...operationsQueryKeys.all, "warehouse", filters] as const,
  risks: (filters: OperationsQueryParams) =>
    [...operationsQueryKeys.all, "risks", filters] as const,
};
