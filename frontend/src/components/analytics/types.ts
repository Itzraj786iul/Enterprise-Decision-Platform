/**
 * Shared contracts for the Analytics UI Framework.
 * Presentational only — no business API coupling.
 */

export type AnalyticsOption = {
  label: string;
  value: string;
  disabled?: boolean;
};

export type AnalyticsDateRange = {
  start: string;
  end: string;
};

export type AnalyticsFiltersState = {
  dateRange: AnalyticsDateRange;
  regionIds: string[];
  categoryIds: string[];
  customerIds: string[];
  productIds: string[];
  search: string;
};

export type AnalyticsViewMode = "chart" | "table" | "split";

export type AnalyticsMetricOption = {
  id: string;
  label: string;
  description?: string;
};

export type AnalyticsSelectionState = {
  selectedMetricIds: string[];
  selectedRowIds: string[];
  highlightedSeriesId: string | null;
  viewMode: AnalyticsViewMode;
};

export const DEFAULT_ANALYTICS_SELECTION: AnalyticsSelectionState = {
  selectedMetricIds: [],
  selectedRowIds: [],
  highlightedSeriesId: null,
  viewMode: "chart",
};

export type AnalyticsExportFormat = "csv" | "excel" | "pdf" | "png";

export type AnalyticsExportRequest = {
  format: AnalyticsExportFormat;
  filename?: string;
  /** Opaque payload prepared by the feature page (already shaped rows/series). */
  payload?: unknown;
};

export type AnalyticsExportResult = {
  format: AnalyticsExportFormat;
  status: "queued" | "unsupported" | "failed";
  message: string;
};

export const DEFAULT_ANALYTICS_FILTERS: AnalyticsFiltersState = {
  dateRange: { start: "", end: "" },
  regionIds: [],
  categoryIds: [],
  customerIds: [],
  productIds: [],
  search: "",
};
