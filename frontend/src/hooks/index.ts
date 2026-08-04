export function useIsClient() {
  return typeof window !== "undefined";
}

export { useShellShortcuts } from "./use-shell-shortcuts";
export { useAnalyticsFilters } from "./use-analytics-filters";
export { useAnalyticsRefresh } from "./use-analytics-refresh";
export { useAnalyticsExport } from "./use-analytics-export";
export { useAnalyticsSelection } from "./use-analytics-selection";
