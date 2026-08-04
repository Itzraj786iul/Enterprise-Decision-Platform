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
  AnalyticsComparisonSection,
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
  useCategoryPerformance,
  useProductPerformance,
  useRegionalSales,
  useSalesOverview,
  useSalesTrends,
  useTopCustomers,
} from "@/features/sales/hooks/use-sales";
import type { SalesMetric } from "@/services/sales";
import type { TrendDirection } from "@/styles/tokens";
import type { DataTableColumn } from "@/components/tables";

const REGION_OPTIONS = [
  { label: "West", value: "West" },
  { label: "East", value: "East" },
  { label: "North", value: "North" },
  { label: "South", value: "South" },
  { label: "Central", value: "Central" },
];

const CATEGORY_OPTIONS = [
  { label: "Electronics", value: "Electronics" },
  { label: "Home", value: "Home" },
  { label: "Apparel", value: "Apparel" },
  { label: "Grocery", value: "Grocery" },
  { label: "Beauty", value: "Beauty" },
];

function formatDelta(metric: SalesMetric): string | undefined {
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

function SalesIntelligenceInner() {
  const { filters, patchFilters, resetFilters } = useAnalyticsFilters({
    scope: "sales",
  });
  const { selection, setViewMode } = useAnalyticsSelection({ scope: "sales" });

  const queryFilters = useMemo(
    () => ({
      dateFrom: filters.dateRange.start || undefined,
      dateTo: filters.dateRange.end || undefined,
      regionIds: filters.regionIds,
      categoryIds: filters.categoryIds,
      search: filters.search || undefined,
    }),
    [filters],
  );

  const overview = useSalesOverview(queryFilters);
  const trends = useSalesTrends("daily", queryFilters);
  const regional = useRegionalSales(queryFilters);
  const category = useCategoryPerformance(queryFilters);
  const products = useProductPerformance({ ...queryFilters, page: 1, pageSize: 8 });
  const customers = useTopCustomers(8, queryFilters.search);

  const { isRefreshing, lastUpdated, refresh } = useAnalyticsRefresh({
    onRefresh: async () => {
      await Promise.all([
        overview.refetch(),
        trends.refetch(),
        regional.refetch(),
        category.refetch(),
        products.refetch(),
        customers.refetch(),
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
    description: metric.available ? undefined : "Metric unavailable from analytics views",
  }));

  const trendData = (trends.data?.points ?? []).map((p) => ({
    period: p.period,
    revenue: p.revenue ?? 0,
    orders: p.orders ?? 0,
    profit: p.profit ?? 0,
  }));

  const regionalData = (regional.data?.rows ?? []).map((r) => ({
    region: r.region,
    revenue: r.revenue ?? 0,
    orders: r.orders ?? 0,
  }));

  const categoryPie = (category.data?.rows ?? []).map((r) => ({
    name: r.category,
    value: r.revenue ?? 0,
  }));

  const productColumns: DataTableColumn<{
    id: string;
    product: string;
    category: string;
    revenue: string;
    orders: string;
    margin: string;
  }>[] = [
    { id: "product", header: "Product", accessor: (row) => row.product },
    { id: "category", header: "Category", accessor: (row) => row.category },
    { id: "revenue", header: "Revenue", accessor: (row) => row.revenue, align: "right" },
    { id: "orders", header: "Orders", accessor: (row) => row.orders, align: "right" },
    { id: "margin", header: "Margin", accessor: (row) => row.margin, align: "right" },
  ];

  const productRows = (products.data?.rows ?? []).map((r) => ({
    id: r.product_id ?? r.product,
    product: r.product,
    category: r.category ?? "—",
    revenue: currency(r.revenue),
    orders: r.orders != null ? String(Math.round(r.orders)) : "—",
    margin: percent(r.margin),
  }));

  const customerColumns: DataTableColumn<{
    id: string;
    customer: string;
    revenue: string;
    orders: string;
    ltv: string;
  }>[] = [
    { id: "customer", header: "Customer", accessor: (row) => row.customer },
    { id: "revenue", header: "Revenue", accessor: (row) => row.revenue, align: "right" },
    { id: "orders", header: "Orders", accessor: (row) => row.orders, align: "right" },
    { id: "ltv", header: "Lifetime Value", accessor: (row) => row.ltv, align: "right" },
  ];

  const customerRows = (customers.data?.rows ?? []).map((r) => ({
    id: r.customer_id ?? r.customer,
    customer: r.customer,
    revenue: currency(r.revenue),
    orders: r.orders != null ? String(Math.round(r.orders)) : "—",
    ltv: r.lifetime_value_available ? currency(r.lifetime_value) : "Unavailable",
  }));

  const insights = useMemo(() => {
    const items: { id: string; title: string; body: string; tone: "info" | "success" | "warning" }[] =
      [];
    const growth = overview.data?.metrics.find((m) => m.id === "growth");
    if (growth?.available && growth.value != null) {
      items.push({
        id: "growth",
        title: growth.value >= 0 ? "Revenue growth positive" : "Revenue contraction",
        body: `Period growth is ${percent(growth.value)} versus the prior comparable window.`,
        tone: growth.value >= 0 ? "success" : "warning",
      });
    }
    const topRegion = regional.data?.rows[0];
    if (topRegion) {
      items.push({
        id: "region",
        title: `${topRegion.region} leads regional revenue`,
        body: `${topRegion.region} contributes ${currency(topRegion.revenue)} with ${percent(topRegion.growth)} growth.`,
        tone: "info",
      });
    }
    if (category.data && !category.data.available) {
      items.push({
        id: "category-unavailable",
        title: "Category contribution unavailable",
        body: "Product category mart views are not published; category charts remain empty.",
        tone: "warning",
      });
    }
    return items;
  }, [overview.data, regional.data, category.data]);

  const recommendations = useMemo(() => {
    const items: {
      id: string;
      title: string;
      summary: string;
      priority: "low" | "medium" | "high";
    }[] = [];
    const weak = [...(regional.data?.rows ?? [])]
      .filter((r) => r.growth != null && r.growth < 0)
      .sort((a, b) => (a.growth ?? 0) - (b.growth ?? 0))[0];
    if (weak) {
      items.push({
        id: "focus-region",
        title: `Stabilize ${weak.region}`,
        summary: `${weak.region} shows ${percent(weak.growth)} growth. Review assortment and promo mix.`,
        priority: "high",
      });
    }
    const topCat = category.data?.rows[0];
    if (topCat && category.data?.available) {
      items.push({
        id: "scale-category",
        title: `Scale ${topCat.category}`,
        summary: `${topCat.category} is the largest category contributor at ${currency(topCat.revenue)}.`,
        priority: "medium",
      });
    }
    return items;
  }, [regional.data, category.data]);

  const showChart = selection.viewMode !== "table";
  const showTable = selection.viewMode !== "chart";

  return (
    <AnalyticsPageLayout
      header={
        <AnalyticsHeader
          title="Sales Intelligence"
          description="Commercial performance across revenue, products, regions, and customers."
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Sales Intelligence" },
          ]}
        />
      }
      toolbar={
        <AnalyticsToolbar
          leading={
            <ViewToggle value={selection.viewMode} onChange={setViewMode} />
          }
          trailing={
            <>
              <LastUpdatedIndicator value={lastUpdated} />
              <RefreshButton
                onRefresh={() => void refresh()}
                loading={isRefreshing}
              />
            </>
          }
        />
      }
      filters={
        <AnalyticsFilterBar
          actions={<ResetFiltersButton onReset={resetFilters} />}
        >
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
            options={CATEGORY_OPTIONS}
            value={filters.categoryIds}
            onChange={(categoryIds) => patchFilters({ categoryIds })}
          />
          <SearchFilter
            value={filters.search}
            onChange={(search) => patchFilters({ search })}
            placeholder="Search stores, products, customers…"
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
        <AnalyticsTrendSection
          title="Revenue & orders trend"
          description="Daily commercial trajectory for the selected filters."
          loading={trends.isLoading}
          error={trends.error}
          empty={!trends.data?.available || trendData.length === 0}
          onRetry={() => void trends.refetch()}
        >
          <div className="grid gap-4 lg:grid-cols-2">
            <AnalyticsLineChart
              title="Revenue trend"
              data={trendData}
              xKey="period"
              series={[{ dataKey: "revenue", name: "Revenue" }]}
            />
            <AnalyticsLineChart
              title="Orders trend"
              data={trendData}
              xKey="period"
              series={[{ dataKey: "orders", name: "Orders" }]}
            />
          </div>
        </AnalyticsTrendSection>
      ) : null}

      {showChart ? (
        <AnalyticsComparisonSection
          title="Regional comparison"
          description="Revenue and order volume by region."
          loading={regional.isLoading}
          error={regional.error}
          empty={!regional.data?.available || regionalData.length === 0}
          onRetry={() => void regional.refetch()}
        >
          <AnalyticsBarChart
            title="Regional revenue"
            data={regionalData}
            xKey="region"
            series={[
              { dataKey: "revenue", name: "Revenue" },
              { dataKey: "orders", name: "Orders" },
            ]}
          />
        </AnalyticsComparisonSection>
      ) : null}

      {showChart ? (
        <AnalyticsBreakdownSection
          title="Category contribution"
          description="Share of revenue by product category."
          loading={category.isLoading}
          error={category.error}
          empty={!category.data?.available || categoryPie.length === 0}
          onRetry={() => void category.refetch()}
        >
          <AnalyticsPieChart title="Category mix" data={categoryPie} />
        </AnalyticsBreakdownSection>
      ) : null}

      {showTable || selection.viewMode === "split" || showChart ? (
        <AnalyticsTableSection
          title="Top products"
          description="Highest-revenue products for the current filters."
          columns={productColumns}
          data={productRows}
          rowKey={(row) => row.id}
          loading={products.isLoading}
          error={products.error}
          onRetry={() => void products.refetch()}
        />
      ) : null}

      <AnalyticsTableSection
        title="Top customers"
        description="Highest lifetime value customers from customer 360."
        columns={customerColumns}
        data={customerRows}
        rowKey={(row) => row.id}
        loading={customers.isLoading}
        error={customers.error}
        onRetry={() => void customers.refetch()}
      />

      <div className="grid gap-8 lg:grid-cols-2">
        <AnalyticsInsightPanel items={insights} />
        <AnalyticsRecommendationPanel items={recommendations} />
      </div>
    </AnalyticsPageLayout>
  );
}

export function SalesIntelligencePage() {
  return (
    <Suspense
      fallback={
        <div className="p-6 text-sm text-muted-foreground" role="status">
          Loading sales intelligence…
        </div>
      }
    >
      <SalesIntelligenceInner />
    </Suspense>
  );
}
