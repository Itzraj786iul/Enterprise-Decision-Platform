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
  AnalyticsLineChart,
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
  useBudgetVariance,
  useCashflow,
  useCostBreakdown,
  useFinanceOverview,
  useFinancialRisks,
  useProfitability,
} from "@/features/finance/hooks/use-finance";
import type { FinanceMetric } from "@/services/finance";
import type { TrendDirection } from "@/styles/tokens";
import type { DataTableColumn } from "@/components/tables";

const REGION_OPTIONS = [
  { label: "West", value: "West" },
  { label: "East", value: "East" },
  { label: "North", value: "North" },
  { label: "South", value: "South" },
  { label: "Central", value: "Central" },
];

const DEPARTMENT_OPTIONS = [
  { label: "Brand", value: "Brand" },
  { label: "Performance", value: "Performance" },
  { label: "Retention", value: "Retention" },
];

const COST_CATEGORY_OPTIONS = [
  { label: "COGS", value: "COGS" },
  { label: "Discounts", value: "Discounts" },
  { label: "Refunds", value: "Refunds" },
];

function formatDelta(metric: FinanceMetric): string | undefined {
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

function FinanceIntelligenceInner() {
  const { filters, patchFilters, resetFilters } = useAnalyticsFilters({
    scope: "finance",
  });
  const { selection, setViewMode } = useAnalyticsSelection({ scope: "finance" });

  const queryFilters = useMemo(
    () => ({
      dateFrom: filters.dateRange.start || undefined,
      dateTo: filters.dateRange.end || undefined,
      regionIds: filters.regionIds,
      departmentIds: filters.productIds,
      costCategoryIds: filters.categoryIds,
      search: filters.search || undefined,
    }),
    [filters],
  );

  const overview = useFinanceOverview(queryFilters);
  const profitability = useProfitability(queryFilters);
  const costs = useCostBreakdown(queryFilters);
  const cashflow = useCashflow(queryFilters);
  const risks = useFinancialRisks(queryFilters);
  const budget = useBudgetVariance(queryFilters);

  const { isRefreshing, lastUpdated, refresh } = useAnalyticsRefresh({
    onRefresh: async () => {
      await Promise.all([
        overview.refetch(),
        profitability.refetch(),
        costs.refetch(),
        cashflow.refetch(),
        risks.refetch(),
        budget.refetch(),
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

  const trendData = (cashflow.data?.rows ?? []).map((r) => ({
    period: r.period,
    profit: r.profit ?? 0,
    margin: (r.margin ?? 0) * 100,
    inflows: r.inflows ?? 0,
    outflows: r.outflows ?? 0,
    net: r.net_cashflow ?? 0,
  }));

  const regionalData = (profitability.data?.rows ?? []).map((r) => ({
    region: r.region,
    revenue: r.revenue ?? 0,
    profit: r.profit ?? 0,
    margin: (r.margin ?? 0) * 100,
  }));

  const costPie = (costs.data?.rows ?? []).map((r) => ({
    name: r.cost_category,
    value: r.amount ?? 0,
  }));

  const budgetBars = (budget.data?.rows ?? []).map((r) => ({
    department: r.department,
    budget: r.budget ?? 0,
    actual: r.actual ?? 0,
    variance: r.variance ?? 0,
  }));

  const riskColumns: DataTableColumn<{
    id: string;
    risk: string;
    severity: string;
    impact: string;
    owner: string;
    recommendation: string;
  }>[] = [
    { id: "risk", header: "Risk", accessor: (row) => row.risk },
    { id: "severity", header: "Severity", accessor: (row) => row.severity },
    { id: "impact", header: "Est. Impact", accessor: (row) => row.impact, align: "right" },
    { id: "owner", header: "Owner", accessor: (row) => row.owner },
    { id: "recommendation", header: "Recommendation", accessor: (row) => row.recommendation },
  ];

  const riskRows = (risks.data?.rows ?? []).map((r, idx) => ({
    id: `${r.risk}-${idx}`,
    risk: r.risk,
    severity: r.severity,
    impact: currency(r.estimated_impact),
    owner: r.owner ?? "—",
    recommendation: r.recommendation ?? "—",
  }));

  const budgetColumns: DataTableColumn<{
    id: string;
    department: string;
    budget: string;
    actual: string;
    variance: string;
    variancePct: string;
  }>[] = [
    { id: "department", header: "Department", accessor: (row) => row.department },
    { id: "budget", header: "Budget", accessor: (row) => row.budget, align: "right" },
    { id: "actual", header: "Actual", accessor: (row) => row.actual, align: "right" },
    { id: "variance", header: "Variance", accessor: (row) => row.variance, align: "right" },
    { id: "variancePct", header: "Variance %", accessor: (row) => row.variancePct, align: "right" },
  ];

  const budgetRows = (budget.data?.rows ?? []).map((r) => ({
    id: r.department,
    department: r.department,
    budget: currency(r.budget),
    actual: currency(r.actual),
    variance: currency(r.variance),
    variancePct: percent(r.variance_pct),
  }));

  const insights = useMemo(() => {
    const items: {
      id: string;
      title: string;
      body: string;
      tone: "info" | "success" | "warning" | "danger";
    }[] = [];
    const margin = overview.data?.metrics.find((m) => m.id === "profit_margin");
    if (margin?.available && margin.value != null) {
      items.push({
        id: "margin",
        title: "Margin posture",
        body: `Gross profit margin is ${percent(margin.value)}.`,
        tone: margin.value >= 0.25 ? "success" : "warning",
      });
    }
    const topRegion = profitability.data?.rows[0];
    if (topRegion) {
      items.push({
        id: "region",
        title: `${topRegion.region} leads profitability`,
        body: `${topRegion.region} contributes ${currency(topRegion.profit)} profit at ${percent(topRegion.margin)} margin.`,
        tone: "info",
      });
    }
    if (risks.data?.rows.length) {
      items.push({
        id: "risks",
        title: "Financial risks open",
        body: `${risks.data.rows.length} risk items require finance owner follow-up.`,
        tone: "danger",
      });
    }
    return items;
  }, [overview.data, profitability.data, risks.data]);

  const recommendations = useMemo(() => {
    const items: {
      id: string;
      title: string;
      summary: string;
      priority: "low" | "medium" | "high";
    }[] = [];
    const overrun = budget.data?.rows.find((r) => (r.variance_pct ?? 0) > 0.1);
    if (overrun) {
      items.push({
        id: "budget",
        title: `Contain ${overrun.department} spend`,
        summary: "Budget variance exceeds 10% — re-forecast and tighten approval controls.",
        priority: "high",
      });
    }
    const risingCost = costs.data?.rows.find((r) => r.trend === "up");
    if (risingCost) {
      items.push({
        id: "cost",
        title: `Stabilize ${risingCost.cost_category}`,
        summary: `${risingCost.cost_category} is trending up at ${currency(risingCost.amount)}.`,
        priority: "medium",
      });
    }
    return items;
  }, [budget.data, costs.data]);

  const showChart = selection.viewMode !== "table";

  return (
    <AnalyticsPageLayout
      header={
        <AnalyticsHeader
          title="Finance Intelligence"
          description="Profitability, costs, cashflow, budget variance, and financial risk."
          breadcrumbs={[
            { label: "Home", href: "/" },
            { label: "Finance Intelligence" },
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
          <ProductFilter
            label="Department"
            placeholder="Add department"
            options={DEPARTMENT_OPTIONS}
            value={filters.productIds}
            onChange={(productIds) => patchFilters({ productIds })}
          />
          <CategoryFilter
            label="Cost Category"
            placeholder="Add cost category"
            options={COST_CATEGORY_OPTIONS}
            value={filters.categoryIds}
            onChange={(categoryIds) => patchFilters({ categoryIds })}
          />
          <SearchFilter
            value={filters.search}
            onChange={(search) => patchFilters({ search })}
            placeholder="Search regions, departments…"
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
          title="Profit & margin trend"
          description="Monthly profit and margin from commercial finance views."
          loading={cashflow.isLoading}
          error={cashflow.error}
          empty={!cashflow.data?.available || trendData.length === 0}
          onRetry={() => void cashflow.refetch()}
        >
          <div className="grid gap-4 lg:grid-cols-2">
            <AnalyticsLineChart
              title="Profit trend"
              data={trendData}
              xKey="period"
              series={[{ dataKey: "profit", name: "Profit" }]}
            />
            <AnalyticsLineChart
              title="Margin trend"
              data={trendData}
              xKey="period"
              series={[{ dataKey: "margin", name: "Margin %" }]}
            />
          </div>
        </AnalyticsTrendSection>
      ) : null}

      {showChart ? (
        <AnalyticsComparisonSection
          title="Regional profitability"
          description="Revenue, profit, and margin by region."
          loading={profitability.isLoading}
          error={profitability.error}
          empty={!profitability.data?.available || regionalData.length === 0}
          onRetry={() => void profitability.refetch()}
        >
          <AnalyticsBarChart
            title="Regional profit"
            data={regionalData}
            xKey="region"
            series={[
              { dataKey: "revenue", name: "Revenue" },
              { dataKey: "profit", name: "Profit" },
            ]}
          />
        </AnalyticsComparisonSection>
      ) : null}

      {showChart ? (
        <AnalyticsBreakdownSection
          title="Cost composition"
          description="Share of COGS, discounts, and refunds."
          loading={costs.isLoading}
          error={costs.error}
          empty={!costs.data?.available || costPie.length === 0}
          onRetry={() => void costs.refetch()}
        >
          <AnalyticsPieChart title="Cost mix" data={costPie} />
        </AnalyticsBreakdownSection>
      ) : null}

      {showChart ? (
        <AnalyticsTrendSection
          title="Cashflow trend"
          description="Monthly inflows, outflows, and net cashflow."
          loading={cashflow.isLoading}
          error={cashflow.error}
          empty={!cashflow.data?.available || trendData.length === 0}
          onRetry={() => void cashflow.refetch()}
        >
          <AnalyticsLineChart
            title="Cashflow"
            data={trendData}
            xKey="period"
            series={[
              { dataKey: "inflows", name: "Inflows" },
              { dataKey: "outflows", name: "Outflows" },
              { dataKey: "net", name: "Net cashflow" },
            ]}
          />
        </AnalyticsTrendSection>
      ) : null}

      {showChart ? (
        <AnalyticsComparisonSection
          title="Budget variance"
          description="Budget versus actual spend by department (campaign type)."
          loading={budget.isLoading}
          error={budget.error}
          empty={!budget.data?.available || budgetBars.length === 0}
          onRetry={() => void budget.refetch()}
        >
          <AnalyticsBarChart
            title="Budget vs actual"
            data={budgetBars}
            xKey="department"
            series={[
              { dataKey: "budget", name: "Budget" },
              { dataKey: "actual", name: "Actual" },
            ]}
          />
        </AnalyticsComparisonSection>
      ) : null}

      <AnalyticsTableSection
        title="Budget variance detail"
        columns={budgetColumns}
        data={budgetRows}
        rowKey={(row) => row.id}
        loading={budget.isLoading}
        error={budget.error}
        onRetry={() => void budget.refetch()}
      />

      <AnalyticsTableSection
        title="Financial risks"
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

export function FinanceIntelligencePage() {
  return (
    <Suspense
      fallback={
        <div className="p-6 text-sm text-muted-foreground" role="status">
          Loading finance intelligence…
        </div>
      }
    >
      <FinanceIntelligenceInner />
    </Suspense>
  );
}
