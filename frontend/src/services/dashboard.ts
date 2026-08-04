/**
 * Executive dashboard API client.
 */

import { apiFetch } from "@/services/api-client";

export type DashboardMetric = {
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

export type DashboardOverview = {
  metrics: DashboardMetric[];
  period_start: string | null;
  period_end: string | null;
  generated_at: string;
};

export type DashboardTrendPoint = {
  date: string;
  revenue: number | null;
  profit: number | null;
  orders: number | null;
};

export type DashboardTrends = {
  points: DashboardTrendPoint[];
  grain: string;
};

export type RegionalPerformanceRow = {
  region: string;
  revenue: number | null;
  profit: number | null;
  growth: number | null;
  order_count: number | null;
};

export type RegionalPerformance = {
  rows: RegionalPerformanceRow[];
};

export type RiskItem = {
  id: string;
  title: string;
  description: string | null;
  priority: "low" | "medium" | "high" | "critical";
  impact: string | null;
  owner: string | null;
  source: string | null;
};

export type TopRisks = {
  items: RiskItem[];
};

export type OpportunityItem = {
  id: string;
  title: string;
  description: string | null;
  estimated_impact: string | null;
  priority: "low" | "medium" | "high";
  source: string | null;
};

export type Opportunities = {
  items: OpportunityItem[];
};

const BASE = "/api/v1/dashboard";

export const dashboardApi = {
  overview: (days = 30) =>
    apiFetch<DashboardOverview>(`${BASE}/overview?days=${days}`),
  trends: (days = 90) =>
    apiFetch<DashboardTrends>(`${BASE}/trends?days=${days}`),
  regionalPerformance: (days = 30) =>
    apiFetch<RegionalPerformance>(`${BASE}/regional-performance?days=${days}`),
  topRisks: (limit = 10) =>
    apiFetch<TopRisks>(`${BASE}/top-risks?limit=${limit}`),
  opportunities: (limit = 10) =>
    apiFetch<Opportunities>(`${BASE}/opportunities?limit=${limit}`),
};

export const dashboardQueryKeys = {
  all: ["dashboard"] as const,
  overview: (days: number) => [...dashboardQueryKeys.all, "overview", days] as const,
  trends: (days: number) => [...dashboardQueryKeys.all, "trends", days] as const,
  regional: (days: number) => [...dashboardQueryKeys.all, "regional", days] as const,
  risks: (limit: number) => [...dashboardQueryKeys.all, "risks", limit] as const,
  opportunities: (limit: number) =>
    [...dashboardQueryKeys.all, "opportunities", limit] as const,
};
