"use client";

import { Suspense, useMemo } from "react";
import {
  AnalyticsPageLayout,
  AnalyticsHeader,
  AnalyticsToolbar,
  AnalyticsFilterBar,
  AnalyticsFooter,
  AnalyticsKPIGrid,
  AnalyticsTrendSection,
  AnalyticsBreakdownSection,
  AnalyticsTableSection,
  AnalyticsInsightPanel,
  AnalyticsRecommendationPanel,
  AnalyticsLineChart,
  AnalyticsBarChart,
  AnalyticsPieChart,
  DateRangeFilter,
  RegionFilter,
  CategoryFilter,
  SearchFilter,
  ResetFiltersButton,
  RefreshButton,
  LastUpdatedIndicator,
  ViewToggle,
} from "@/components/analytics";
import {
  useAnalyticsFilters,
  useAnalyticsRefresh,
  useAnalyticsSelection,
} from "@/hooks";
import {
  useChurnRisk,
  useCustomerCohorts,
  useCustomerDistribution,
  useCustomerOverview,
  useRfmSegments,
  useTopCustomersDetail,
} from "@/features/customers/hooks/use-customers";
import type { CustomerMetric } from "@/services/customers";
import type { TrendDirection } from "@/styles/tokens";
import type { DataTableColumn } from "@/components/tables";

const REGION_OPTIONS = [
  { label: "West", value: "West" },
  { label: "East", value: "East" },
  { label: "North", value: "North" },
  { label: "South", value: "South" },
  { label: "Central", value: "Central" },
];

const SEGMENT_OPTIONS = [
  { label: "Champions", value: "Champions" },
  { label: "Loyal", value: "Loyal" },
  { label: "Promising New", value: "Promising New" },
  { label: "At Risk Loyal", value: "At Risk Loyal" },
  { label: "Hibernating", value: "Hibernating" },
  { label: "Need Attention", value: "Need Attention" },
];

function formatDelta(metric: CustomerMetric): string | undefined {
  if (metric.delta == null) return undefined;
  const pct = `${(metric.delta * 100).toFixed(1)}%`;
  const label = metric.delta_label ? ` ${metric.delta_label}` : "";
  return `${metric.delta > 0 ? "+" : ""}${pct}${label}`;
}

function currency(value: number | null | undefined): string {
  if (value == null) return "—";
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function percent(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function CustomerIntelligenceInner() {
  const { filters, patchFilters, resetFilters } = useAnalyticsFilters({
    scope: "customers",
  });
  const { selection, setViewMode } = useAnalyticsSelection({ scope: "customers" });

  const queryFilters = useMemo(
    () => ({
      dateFrom: filters.dateRange.start || undefined,
      dateTo: filters.dateRange.end || undefined,
      regionIds: filters.regionIds,
      segmentIds: filters.categoryIds,
      search: filters.search || undefined,
    }),
    [filters],
  );

  const overview = useCustomerOverview(queryFilters);
  const rfm = useRfmSegments(queryFilters);
  const cohorts = useCustomerCohorts(queryFilters);
  const distribution = useCustomerDistribution(queryFilters);
  const topCustomers = useTopCustomersDetail({
    ...queryFilters,
    page: 1,
    pageSize: 10,
  });
  const churn = useChurnRisk(queryFilters);

  const { isRefreshing, lastUpdated, refresh } = useAnalyticsRefresh({
    onRefresh: async () => {
      await Promise.all([
        overview.refetch(),
        rfm.refetch(),
        cohorts.refetch(),
        distribution.refetch(),
        topCustomers.refetch(),
        churn.refetch(),
      ]);
    },
  });

  const kpiItems = (overview.data?.metrics ?? []).map((metric) => ({
    id: metric.id,
    title: metric.label,
    value:
      metric.available && metric.formatted_value
        ? metric.formatted_value
        : metric.available
          ? String(metric.value ?? "—")
          : "Unavailable",
    delta: formatDelta(metric),
    trend: (metric.trend as TrendDirection | null) ?? "flat",
    description: metric.available
      ? undefined
      : "Metric unavailable from analytics views",
  }));

  const rfmPie = (rfm.data?.rows ?? []).map((r) => ({
    name: r.segment,
    value: r.customer_count ?? 0,
  }));

  const rfmBars = (rfm.data?.rows ?? []).map((r) => ({
    segment: r.segment,
    revenue: r.revenue ?? 0,
    customers: r.customer_count ?? 0,
  }));

  const cohortTrend = useMemo(() => {
    const latest = cohorts.data?.rows?.at(-1);
    if (!latest) return [];
    return latest.retentions.map((cell) => ({
      month: `M${cell.month_offset}`,
      retention: (cell.retention_pct ?? 0) * 100,
      customers: cell.customer_count ?? 0,
    }));
  }, [cohorts.data]);

  const regionalData = (distribution.data?.rows ?? []).map((r) => ({
    region: r.region,
    customers: r.customer_count ?? 0,
    revenue: r.revenue ?? 0,
  }));

  const churnData = (churn.data?.rows ?? []).map((r) => ({
    risk: r.risk_level,
    customers: r.customer_count ?? 0,
    revenueAtRisk: r.predicted_revenue_at_risk ?? 0,
  }));

  const customerColumns: DataTableColumn<{
    id: string;
    customer: string;
    segment: string;
    region: string;
    ltv: string;
    orders: string;
    status: string;
  }>[] = [
    { id: "customer", header: "Customer", accessor: (row) => row.customer },
    { id: "segment", header: "Segment", accessor: (row) => row.segment },
    { id: "region", header: "Region", accessor: (row) => row.region },
    { id: "ltv", header: "Lifetime Value", accessor: (row) => row.ltv, align: "right" },
    { id: "orders", header: "Orders", accessor: (row) => row.orders, align: "right" },
    { id: "status", header: "Lifecycle", accessor: (row) => row.status },
  ];

  const customerRows = (topCustomers.data?.rows ?? []).map((r) => ({
    id: r.customer_id ?? r.customer,
    customer: r.customer,
    segment: r.segment ?? "—",
    region: r.region ?? "—",
    ltv: currency(r.lifetime_value),
    orders: r.orders != null ? String(Math.round(r.orders)) : "—",
    status: r.lifecycle_status ?? "—",
  }));

  const cohortColumns: DataTableColumn<Record<string, string>>[] = [
    { id: "cohort", header: "Cohort", accessor: (row) => row.cohort },
    { id: "size", header: "Size", accessor: (row) => row.size, align: "right" },
    { id: "m0", header: "M0", accessor: (row) => row.m0, align: "right" },
    { id: "m1", header: "M1", accessor: (row) => row.m1, align: "right" },
    { id: "m2", header: "M2", accessor: (row) => row.m2, align: "right" },
    { id: "m3", header: "M3", accessor: (row) => row.m3, align: "right" },
  ];

  const cohortRows = (cohorts.data?.rows ?? []).map((row) => {
    const byOffset = Object.fromEntries(
      row.retentions.map((cell) => [cell.month_offset, cell.retention_pct]),
    );
    return {
      id: row.cohort,
      cohort: row.cohort,
      size: row.cohort_size != null ? String(Math.round(row.cohort_size)) : "—",
      m0: percent(byOffset[0] ?? null),
      m1: percent(byOffset[1] ?? null),
      m2: percent(byOffset[2] ?? null),
      m3: percent(byOffset[3] ?? null),
    };
  });

  const insights = useMemo(() => {
    const items: {
      id: string;
      title: string;
      body: string;
      tone: "info" | "success" | "warning" | "danger";
    }[] = [];
    const retention = overview.data?.metrics.find((m) => m.id === "retention_rate");
    if (retention?.available && retention.value != null) {
      items.push({
        id: "retention",
        title: "Retention posture",
        body: `Retention rate is ${percent(retention.value)} for customers acquired before the selected window.`,
        tone: retention.value >= 0.5 ? "success" : "warning",
      });
    }
    const topSegment = rfm.data?.rows[0];
    if (topSegment) {
      items.push({
        id: "rfm",
        title: `${topSegment.segment} leads RFM revenue`,
        body: `${topSegment.segment} represents ${Math.round(topSegment.customer_count ?? 0)} customers and ${currency(topSegment.revenue)} lifetime revenue.`,
        tone: "info",
      });
    }
    const high = churn.data?.rows.find((r) => r.risk_level === "High");
    if (high && (high.customer_count ?? 0) > 0) {
      items.push({
        id: "churn",
        title: "Elevated churn exposure",
        body: `${Math.round(high.customer_count ?? 0)} customers sit in High risk with ${currency(high.predicted_revenue_at_risk)} revenue at risk.`,
        tone: "danger",
      });
    }
    return items;
  }, [overview.data, rfm.data, churn.data]);

  const recommendations = useMemo(() => {
    const items: {
      id: string;
      title: string;
      summary: string;
      priority: "low" | "medium" | "high";
    }[] = [];
    const high = churn.data?.rows.find((r) => r.risk_level === "High");
    if (high && (high.customer_count ?? 0) > 0) {
      items.push({
        id: "save-high-risk",
        title: "Launch save offers for High risk",
        summary: "Prioritize outreach on High churn-risk customers before revenue attrition compounds.",
        priority: "high",
      });
    }
    const promising = rfm.data?.rows.find((r) =>
      r.segment.toLowerCase().includes("promising"),
    );
    if (promising) {
      items.push({
        id: "nurture-new",
        title: "Nurture Promising New buyers",
        summary: `Convert ${Math.round(promising.customer_count ?? 0)} promising customers into Loyal / Champions with early-life offers.`,
        priority: "medium",
      });
    }
    return items;
  }, [churn.data, rfm.data]);

  const showChart = selection.viewMode !== "table";

  return (
    <AnalyticsPageLayout
      header={
        <AnalyticsHeader
          title="Customer Intelligence"
          description="Lifecycle, RFM, retention cohorts, and churn risk for customer strategy."
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Customer Intelligence" },
          ]}
        />
      }
      toolbar={
        <AnalyticsToolbar
          leading={<ViewToggle value={selection.viewMode} onChange={setViewMode} />}
          trailing={
            <>
              <LastUpdatedIndicator value={lastUpdated} />
              <RefreshButton onRefresh={() => void refresh()} loading={isRefreshing} />
            </>
          }
        />
      }
      filters={
        <AnalyticsFilterBar actions={<ResetFiltersButton onReset={resetFilters} />}>
          <DateRangeFilter
            value={filters.dateRange}
            onChange={(dateRange) => patchFilters({ dateRange })}
          />
          <RegionFilter
            options={REGION_OPTIONS}
            value={filters.regionIds}
            onChange={(regionIds) => patchFilters({ regionIds })}
          />
          <CategoryFilter
            label="Customer Segment"
            placeholder="Add segment"
            options={SEGMENT_OPTIONS}
            value={filters.categoryIds}
            onChange={(categoryIds) => patchFilters({ categoryIds })}
          />
          <SearchFilter
            value={filters.search}
            onChange={(search) => patchFilters({ search })}
            placeholder="Search customers…"
          />
        </AnalyticsFilterBar>
      }
      footer={<AnalyticsFooter />}
    >
      <AnalyticsKPIGrid
        items={kpiItems}
        loading={overview.isLoading}
        error={overview.error}
        onRetry={() => void overview.refetch()}
      />

      {showChart ? (
        <AnalyticsBreakdownSection
          title="RFM distribution"
          description="Customer count and revenue contribution by RFM segment."
          loading={rfm.isLoading}
          error={rfm.error}
          empty={!rfm.data?.available || rfmPie.length === 0}
          onRetry={() => void rfm.refetch()}
        >
          <div className="grid gap-4 lg:grid-cols-2">
            <AnalyticsPieChart title="Customers by segment" data={rfmPie} />
            <AnalyticsBarChart
              title="Segment revenue"
              data={rfmBars}
              xKey="segment"
              series={[{ dataKey: "revenue", name: "Revenue" }]}
            />
          </div>
        </AnalyticsBreakdownSection>
      ) : null}

      <AnalyticsTrendSection
        title="Cohort retention"
        description="Monthly acquisition cohorts with retention by month offset."
        loading={cohorts.isLoading}
        error={cohorts.error}
        empty={!cohorts.data?.available || cohortTrend.length === 0}
        onRetry={() => void cohorts.refetch()}
      >
        {showChart ? (
          <AnalyticsLineChart
            title="Latest cohort retention curve"
            data={cohortTrend}
            xKey="month"
            series={[{ dataKey: "retention", name: "Retention %" }]}
          />
        ) : null}
      </AnalyticsTrendSection>

      <AnalyticsTableSection
        title="Cohort matrix"
        description="Retention percentages by cohort month (M0–M3)."
        columns={cohortColumns}
        data={cohortRows}
        rowKey={(row) => row.id}
        loading={cohorts.isLoading}
        error={cohorts.error}
        onRetry={() => void cohorts.refetch()}
      />

      {showChart ? (
        <AnalyticsBreakdownSection
          title="Regional distribution"
          description="Customer count and lifetime revenue by preferred-store region."
          loading={distribution.isLoading}
          error={distribution.error}
          empty={!distribution.data?.available || regionalData.length === 0}
          onRetry={() => void distribution.refetch()}
        >
          <AnalyticsBarChart
            title="Customers by region"
            data={regionalData}
            xKey="region"
            series={[
              { dataKey: "customers", name: "Customers" },
              { dataKey: "revenue", name: "Revenue" },
            ]}
          />
        </AnalyticsBreakdownSection>
      ) : null}

      {showChart ? (
        <AnalyticsBreakdownSection
          title="Churn risk"
          description="Risk tiers from ML predictions with lifecycle fallback."
          loading={churn.isLoading}
          error={churn.error}
          empty={!churn.data?.available || churnData.length === 0}
          onRetry={() => void churn.refetch()}
        >
          <AnalyticsBarChart
            title="Customers and revenue at risk"
            data={churnData}
            xKey="risk"
            series={[
              { dataKey: "customers", name: "Customers" },
              { dataKey: "revenueAtRisk", name: "Revenue at risk" },
            ]}
          />
        </AnalyticsBreakdownSection>
      ) : null}

      <AnalyticsTableSection
        title="Top customers"
        description="Highest lifetime value customers for the current filters."
        columns={customerColumns}
        data={customerRows}
        rowKey={(row) => row.id}
        loading={topCustomers.isLoading}
        error={topCustomers.error}
        onRetry={() => void topCustomers.refetch()}
      />

      <div className="grid gap-8 lg:grid-cols-2">
        <AnalyticsInsightPanel items={insights} />
        <AnalyticsRecommendationPanel items={recommendations} />
      </div>
    </AnalyticsPageLayout>
  );
}

export function CustomerIntelligencePage() {
  return (
    <Suspense
      fallback={
        <div className="p-6 text-sm text-muted-foreground" role="status">
          Loading customer intelligence…
        </div>
      }
    >
      <CustomerIntelligenceInner />
    </Suspense>
  );
}
