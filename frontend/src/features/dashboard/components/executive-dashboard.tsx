"use client";

import { PageHeader } from "@/components/layout/page-header";
import { Breadcrumbs } from "@/components/layout/breadcrumbs";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import {
  useDashboardOverview,
  useDashboardTrends,
  useOpportunities,
  useRegionalPerformance,
  useTopRisks,
} from "@/features/dashboard/hooks/use-dashboard";
import { ExecutiveKpiRow } from "@/features/dashboard/components/executive-kpi-row";
import { RevenueTrendChart } from "@/features/dashboard/components/revenue-trend-chart";
import { RegionalPerformanceTable } from "@/features/dashboard/components/regional-performance-table";
import {
  BusinessOpportunitiesPanel,
  BusinessRisksPanel,
  DqSummaryPanel,
} from "@/features/dashboard/components/risks-opportunities";

export function ExecutiveDashboard() {
  const overview = useDashboardOverview(30);
  const trends = useDashboardTrends(90);
  const regional = useRegionalPerformance(30);
  const risks = useTopRisks(8);
  const opportunities = useOpportunities(8);

  const refreshAll = () => {
    void overview.refetch();
    void trends.refetch();
    void regional.refetch();
    void risks.refetch();
    void opportunities.refetch();
  };

  const dqMetric = overview.data?.metrics.find((m) => m.id === "dq_score");

  return (
    <div className="space-y-8">
      <PageHeader
        breadcrumbs={
          <Breadcrumbs items={[{ label: "Home", href: "/" }, { label: "Dashboard" }]} />
        }
        title="Executive Dashboard"
        description="Enterprise performance, risk, and opportunity posture for leadership review."
        actions={
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={refreshAll}
            aria-label="Refresh dashboard data"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Refresh
          </Button>
        }
      />

      <ExecutiveKpiRow
        metrics={overview.data?.metrics}
        loading={overview.isLoading}
        error={overview.error}
        onRetry={() => void overview.refetch()}
      />

      <RevenueTrendChart
        points={trends.data?.points}
        loading={trends.isLoading}
        error={trends.error}
        onRetry={() => void trends.refetch()}
      />

      <RegionalPerformanceTable
        rows={regional.data?.rows}
        loading={regional.isLoading}
        error={regional.error}
        onRetry={() => void regional.refetch()}
      />

      <div className="grid gap-8 lg:grid-cols-2">
        <BusinessRisksPanel
          items={risks.data?.items}
          loading={risks.isLoading}
          error={risks.error}
          onRetry={() => void risks.refetch()}
        />
        <BusinessOpportunitiesPanel
          items={opportunities.data?.items}
          loading={opportunities.isLoading}
          error={opportunities.error}
          onRetry={() => void opportunities.refetch()}
        />
      </div>

      <DqSummaryPanel
        dqMetricLabel={dqMetric?.label}
        dqValue={dqMetric?.formatted_value}
        available={dqMetric?.available}
        loading={overview.isLoading}
      />
    </div>
  );
}
