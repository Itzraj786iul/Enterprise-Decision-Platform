/**
 * Analytics UI Framework — reusable layout, filters, controls, sections, charts, and export contracts.
 * Feature pages compose these primitives; they do not contain business API logic.
 */

export type {
  AnalyticsOption,
  AnalyticsDateRange,
  AnalyticsFiltersState,
  AnalyticsViewMode,
  AnalyticsMetricOption,
  AnalyticsSelectionState,
  AnalyticsExportFormat,
  AnalyticsExportRequest,
  AnalyticsExportResult,
} from "./types";

export {
  DEFAULT_ANALYTICS_FILTERS,
  DEFAULT_ANALYTICS_SELECTION,
} from "./types";

export {
  AnalyticsPageLayout,
  AnalyticsHeader,
  AnalyticsToolbar,
  AnalyticsFooter,
} from "./layout";

export {
  AnalyticsFilterBar,
  DateRangeFilter,
  RegionFilter,
  CategoryFilter,
  CustomerFilter,
  ProductFilter,
  SearchFilter,
  ResetFiltersButton,
  SingleDimensionFilter,
} from "./filters";

export {
  MetricSelector,
  ViewToggle,
  RefreshButton,
  ExportToolbar,
  LastUpdatedIndicator,
} from "./controls";

export {
  AnalyticsKPIGrid,
  AnalyticsTrendSection,
  AnalyticsComparisonSection,
  AnalyticsBreakdownSection,
  AnalyticsTableSection,
  AnalyticsInsightPanel,
  AnalyticsRecommendationPanel,
} from "./sections";

export type { AnalyticsChartSeries, AnalyticsChartPoint } from "./charts";

export {
  AnalyticsLineChart,
  AnalyticsBarChart,
  AnalyticsAreaChart,
  AnalyticsPieChart,
  AnalyticsScatterChart,
  AnalyticsTreemapChart,
  AnalyticsComposedChart,
  AnalyticsHeatmapPlaceholder,
} from "./charts";

export type { AnalyticsExporter } from "./export";
export { UnsupportedAnalyticsExporter, createAnalyticsExporter } from "./export";
