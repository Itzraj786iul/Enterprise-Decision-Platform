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
  AnalyticsBarChart,
  AnalyticsPieChart,
  DateRangeFilter,
  RegionFilter,
  CategoryFilter,
  ProductFilter,
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
  useOperationalRisks,
  useOperationsInventory,
  useOperationsOverview,
  useOperationsReturns,
  useSupplierPerformance,
  useWarehousePerformance,
} from "@/features/operations/hooks/use-operations";
import type { OperationsMetric } from "@/services/operations";
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
];

const SUPPLIER_OPTIONS = [
  { label: "Acme Supply", value: "Acme Supply" },
  { label: "Late Co", value: "Late Co" },
  { label: "Northwind Parts", value: "Northwind Parts" },
];

function formatDelta(metric: OperationsMetric): string | undefined {
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

function OperationsIntelligenceInner() {
  const { filters, patchFilters, resetFilters } = useAnalyticsFilters({
    scope: "operations",
  });
  const { selection, setViewMode } = useAnalyticsSelection({ scope: "operations" });

  const queryFilters = useMemo(
    () => ({
      dateFrom: filters.dateRange.start || undefined,
      dateTo: filters.dateRange.end || undefined,
      regionIds: filters.regionIds,
      categoryIds: filters.categoryIds,
      supplierIds: filters.productIds,
      search: filters.search || undefined,
    }),
    [filters],
  );

  const overview = useOperationsOverview(queryFilters);
  const inventory = useOperationsInventory({ ...queryFilters, page: 1, pageSize: 10 });
  const suppliers = useSupplierPerformance(queryFilters);
  const returns = useOperationsReturns(queryFilters);
  const warehouse = useWarehousePerformance(queryFilters);
  const risks = useOperationalRisks(queryFilters);

  const { isRefreshing, lastUpdated, refresh } = useAnalyticsRefresh({
    onRefresh: async () => {
      await Promise.all([
        overview.refetch(),
        inventory.refetch(),
        suppliers.refetch(),
        returns.refetch(),
        warehouse.refetch(),
        risks.refetch(),
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

  const inventoryPie = (inventory.data?.rows ?? []).map((r) => ({
    name: r.category ?? r.product,
    value: r.inventory_value ?? 0,
  }));

  // Aggregate pie by category
  const inventoryByCategory = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of inventory.data?.rows ?? []) {
      const key = row.category ?? "Uncategorized";
      map.set(key, (map.get(key) ?? 0) + (row.inventory_value ?? 0));
    }
    return [...map.entries()].map(([name, value]) => ({ name, value }));
  }, [inventory.data]);

  const supplierBars = (suppliers.data?.rows ?? []).map((r) => ({
    supplier: r.supplier,
    onTime: (r.on_time_pct ?? 0) * 100,
    quality: (r.quality_score ?? 0) * 100,
  }));

  const returnsTrend = (returns.data?.rows ?? []).map((r) => ({
    category: r.category,
    returns: r.return_count ?? 0,
    cost: r.return_cost ?? 0,
  }));

  const warehouseBars = (warehouse.data?.rows ?? []).map((r) => ({
    warehouse: r.warehouse,
    inventory: r.inventory ?? 0,
    fulfillment: (r.fulfillment ?? 0) * 100,
    stockouts: r.stockouts ?? 0,
  }));

  const inventoryColumns: DataTableColumn<{
    id: string;
    product: string;
    category: string;
    stock: string;
    safety: string;
    turnover: string;
    value: string;
  }>[] = [
    { id: "product", header: "Product", accessor: (row) => row.product },
    { id: "category", header: "Category", accessor: (row) => row.category },
    { id: "stock", header: "Stock", accessor: (row) => row.stock, align: "right" },
    { id: "safety", header: "Safety Stock", accessor: (row) => row.safety, align: "right" },
    { id: "turnover", header: "Turnover", accessor: (row) => row.turnover, align: "right" },
    { id: "value", header: "Inventory Value", accessor: (row) => row.value, align: "right" },
  ];

  const inventoryRows = (inventory.data?.rows ?? []).map((r) => ({
    id: r.product_id ?? r.product,
    product: r.product,
    category: r.category ?? "—",
    stock: r.stock != null ? String(Math.round(r.stock)) : "—",
    safety: r.safety_stock != null ? String(Math.round(r.safety_stock)) : "—",
    turnover: r.turnover != null ? r.turnover.toFixed(2) : "—",
    value: currency(r.inventory_value),
  }));

  const riskColumns: DataTableColumn<{
    id: string;
    risk: string;
    severity: string;
    owner: string;
    recommendation: string;
  }>[] = [
    { id: "risk", header: "Risk", accessor: (row) => row.risk },
    { id: "severity", header: "Severity", accessor: (row) => row.severity },
    { id: "owner", header: "Owner", accessor: (row) => row.owner },
    { id: "recommendation", header: "Recommendation", accessor: (row) => row.recommendation },
  ];

  const riskRows = (risks.data?.rows ?? []).map((r, idx) => ({
    id: `${r.risk}-${idx}`,
    risk: r.risk,
    severity: r.severity,
    owner: r.owner ?? "—",
    recommendation: r.recommendation ?? "—",
  }));

  const insights = useMemo(() => {
    const items: {
      id: string;
      title: string;
      body: string;
      tone: "info" | "success" | "warning" | "danger";
    }[] = [];
    const health = overview.data?.metrics.find((m) => m.id === "inventory_health");
    if (health?.available && health.value != null) {
      items.push({
        id: "health",
        title: "Inventory health",
        body: `Healthy stock positions are at ${percent(health.value)}.`,
        tone: health.value >= 0.7 ? "success" : "warning",
      });
    }
    const fulfillment = overview.data?.metrics.find((m) => m.id === "fulfillment_rate");
    if (fulfillment?.available && fulfillment.value != null) {
      items.push({
        id: "fulfillment",
        title: "Fulfillment performance",
        body: `Fulfillment rate is ${percent(fulfillment.value)} across warehouse shipments.`,
        tone: fulfillment.value >= 0.8 ? "success" : "warning",
      });
    }
    if (risks.data?.rows.length) {
      items.push({
        id: "risks",
        title: "Operational risks detected",
        body: `${risks.data.rows.length} risk items require owner follow-up.`,
        tone: "danger",
      });
    }
    return items;
  }, [overview.data, risks.data]);

  const recommendations = useMemo(() => {
    const items: {
      id: string;
      title: string;
      summary: string;
      priority: "low" | "medium" | "high";
    }[] = [];
    const late = suppliers.data?.rows.find((r) => (r.on_time_pct ?? 1) < 0.7);
    if (late) {
      items.push({
        id: "supplier",
        title: `Recover ${late.supplier} lead times`,
        summary: "On-time rate is below target — review PO planning and dual-sourcing options.",
        priority: "high",
      });
    }
    const rising = returns.data?.rows.find((r) => r.trend === "up");
    if (rising) {
      items.push({
        id: "returns",
        title: `Contain returns in ${rising.category}`,
        summary: "Return volume is trending up — inspect quality and CX reasons for the category.",
        priority: "medium",
      });
    }
    return items;
  }, [suppliers.data, returns.data]);

  const showChart = selection.viewMode !== "table";

  return (
    <AnalyticsPageLayout
      header={
        <AnalyticsHeader
          title="Operations Intelligence"
          description="Inventory, suppliers, returns, warehouses, and operational risk."
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Operations Intelligence" },
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
            options={CATEGORY_OPTIONS}
            value={filters.categoryIds}
            onChange={(categoryIds) => patchFilters({ categoryIds })}
          />
          <ProductFilter
            label="Supplier"
            placeholder="Add supplier"
            options={SUPPLIER_OPTIONS}
            value={filters.productIds}
            onChange={(productIds) => patchFilters({ productIds })}
          />
          <SearchFilter
            value={filters.search}
            onChange={(search) => patchFilters({ search })}
            placeholder="Search products, suppliers, warehouses…"
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
          title="Inventory distribution"
          description="Inventory value mix by category for the current filters."
          loading={inventory.isLoading}
          error={inventory.error}
          empty={!inventory.data?.available || inventoryByCategory.length === 0}
          onRetry={() => void inventory.refetch()}
        >
          <AnalyticsPieChart
            title="Inventory value by category"
            data={inventoryByCategory.length ? inventoryByCategory : inventoryPie}
          />
        </AnalyticsBreakdownSection>
      ) : null}

      {showChart ? (
        <AnalyticsComparisonSection
          title="Supplier comparison"
          description="On-time delivery and quality score by supplier."
          loading={suppliers.isLoading}
          error={suppliers.error}
          empty={!suppliers.data?.available || supplierBars.length === 0}
          onRetry={() => void suppliers.refetch()}
        >
          <AnalyticsBarChart
            title="Supplier on-time vs quality"
            data={supplierBars}
            xKey="supplier"
            series={[
              { dataKey: "onTime", name: "On-time %" },
              { dataKey: "quality", name: "Quality %" },
            ]}
          />
        </AnalyticsComparisonSection>
      ) : null}

      {showChart ? (
        <AnalyticsTrendSection
          title="Returns trend"
          description="Return counts and cost by category."
          loading={returns.isLoading}
          error={returns.error}
          empty={!returns.data?.available || returnsTrend.length === 0}
          onRetry={() => void returns.refetch()}
        >
          <AnalyticsBarChart
            title="Returns by category"
            data={returnsTrend}
            xKey="category"
            series={[
              { dataKey: "returns", name: "Return count" },
              { dataKey: "cost", name: "Return cost" },
            ]}
          />
        </AnalyticsTrendSection>
      ) : null}

      {showChart ? (
        <AnalyticsBreakdownSection
          title="Warehouse performance"
          description="Inventory value, fulfillment, and stockouts by warehouse."
          loading={warehouse.isLoading}
          error={warehouse.error}
          empty={!warehouse.data?.available || warehouseBars.length === 0}
          onRetry={() => void warehouse.refetch()}
        >
          <AnalyticsBarChart
            title="Warehouse KPIs"
            data={warehouseBars}
            xKey="warehouse"
            series={[
              { dataKey: "inventory", name: "Inventory value" },
              { dataKey: "fulfillment", name: "Fulfillment %" },
              { dataKey: "stockouts", name: "Stockouts" },
            ]}
          />
        </AnalyticsBreakdownSection>
      ) : null}

      <AnalyticsTableSection
        title="Inventory detail"
        description="Product-level stock, safety stock, turnover, and value."
        columns={inventoryColumns}
        data={inventoryRows}
        rowKey={(row) => row.id}
        loading={inventory.isLoading}
        error={inventory.error}
        onRetry={() => void inventory.refetch()}
      />

      <AnalyticsTableSection
        title="Operational risks"
        description="Severity-ranked risks with owners and recommendations."
        columns={riskColumns}
        data={riskRows}
        rowKey={(row) => row.id}
        loading={risks.isLoading}
        error={risks.error}
        onRetry={() => void risks.refetch()}
      />

      <div className="grid gap-8 lg:grid-cols-2">
        <AnalyticsInsightPanel items={insights} />
        <AnalyticsRecommendationPanel items={recommendations} />
      </div>
    </AnalyticsPageLayout>
  );
}

export function OperationsIntelligencePage() {
  return (
    <Suspense
      fallback={
        <div className="p-6 text-sm text-muted-foreground" role="status">
          Loading operations intelligence…
        </div>
      }
    >
      <OperationsIntelligenceInner />
    </Suspense>
  );
}
