"use client";

import type { ReactNode } from "react";
import { SectionHeader } from "@/components/layout/section-header";
import { MetricCard } from "@/components/cards";
import { InsightCard, RecommendationCard } from "@/components/cards";
import { DataTable, type DataTableColumn } from "@/components/tables";
import { EmptyState, ErrorState } from "@/components/feedback/empty-state";
import { LoadingSpinner } from "@/components/feedback/loading-spinner";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";
import type { TrendDirection } from "@/styles/tokens";

type AnalyticsKPIGridItem = {
  id: string;
  title: string;
  value?: ReactNode;
  delta?: string;
  trend?: TrendDirection;
  icon?: LucideIcon;
  description?: string;
};

type AnalyticsKPIGridProps = {
  items: AnalyticsKPIGridItem[];
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  className?: string;
};

export function AnalyticsKPIGrid({
  items,
  loading,
  error,
  onRetry,
  className,
}: AnalyticsKPIGridProps) {
  if (error) {
    return <ErrorState title="Unable to load KPIs" description={error.message} onRetry={onRetry} />;
  }
  if (loading && items.length === 0) {
    return (
      <div className={cn("grid gap-4 sm:grid-cols-2 xl:grid-cols-4", className)}>
        {Array.from({ length: 4 }).map((_, i) => (
          <MetricCard key={i} title="Loading" loading />
        ))}
      </div>
    );
  }
  return (
    <section
      aria-label="Analytics KPIs"
      className={cn("grid gap-4 sm:grid-cols-2 xl:grid-cols-4", className)}
    >
      {items.map((item) => (
        <MetricCard
          key={item.id}
          title={item.title}
          value={item.value}
          delta={item.delta}
          trend={item.trend}
          icon={item.icon}
          description={item.description}
          loading={loading}
        />
      ))}
    </section>
  );
}

type SectionShellProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  loading?: boolean;
  error?: Error | null;
  empty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  onRetry?: () => void;
  className?: string;
};

function SectionShell({
  title,
  description,
  actions,
  children,
  loading,
  error,
  empty,
  emptyTitle = "No data",
  emptyDescription = "Nothing to display for the current filters.",
  onRetry,
  className,
}: SectionShellProps) {
  return (
    <section className={cn("space-y-4", className)} aria-label={title}>
      <SectionHeader title={title} description={description} actions={actions} />
      {error ? (
        <ErrorState title={`Unable to load ${title}`} description={error.message} onRetry={onRetry} />
      ) : loading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner label={`Loading ${title}`} />
        </div>
      ) : empty ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : (
        children
      )}
    </section>
  );
}

type AnalyticsTrendSectionProps = Omit<SectionShellProps, "emptyTitle"> & {
  emptyTitle?: string;
};

export function AnalyticsTrendSection(props: AnalyticsTrendSectionProps) {
  return (
    <SectionShell
      emptyTitle={props.emptyTitle ?? "No trend data"}
      emptyDescription={props.emptyDescription ?? "Adjust filters to see trend series."}
      {...props}
    />
  );
}

export function AnalyticsComparisonSection(props: AnalyticsTrendSectionProps) {
  return (
    <SectionShell
      emptyTitle={props.emptyTitle ?? "No comparison data"}
      emptyDescription={
        props.emptyDescription ?? "Select dimensions to compare performance."
      }
      {...props}
    />
  );
}

export function AnalyticsBreakdownSection(props: AnalyticsTrendSectionProps) {
  return (
    <SectionShell
      emptyTitle={props.emptyTitle ?? "No breakdown data"}
      emptyDescription={
        props.emptyDescription ?? "No categorical breakdown is available."
      }
      {...props}
    />
  );
}

type AnalyticsTableSectionProps<T> = {
  title: string;
  description?: string;
  actions?: ReactNode;
  columns: DataTableColumn<T>[];
  data: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  className?: string;
};

export function AnalyticsTableSection<T>({
  title,
  description,
  actions,
  columns,
  data,
  rowKey,
  loading,
  error,
  onRetry,
  className,
}: AnalyticsTableSectionProps<T>) {
  return (
    <section className={cn("space-y-4", className)} aria-label={title}>
      <SectionHeader title={title} description={description} actions={actions} />
      {error ? (
        <ErrorState title={`Unable to load ${title}`} description={error.message} onRetry={onRetry} />
      ) : (
        <DataTable
          columns={columns}
          data={data}
          rowKey={rowKey}
          loading={loading}
          emptyTitle="No rows"
          emptyDescription="No tabular results for the current filters."
        />
      )}
    </section>
  );
}

type InsightItem = {
  id: string;
  title: string;
  body: string;
  tone?: "info" | "success" | "warning" | "danger";
};

type AnalyticsInsightPanelProps = {
  title?: string;
  description?: string;
  items: InsightItem[];
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  className?: string;
};

export function AnalyticsInsightPanel({
  title = "Insights",
  description,
  items,
  loading,
  error,
  onRetry,
  className,
}: AnalyticsInsightPanelProps) {
  return (
    <SectionShell
      title={title}
      description={description}
      loading={loading}
      error={error}
      onRetry={onRetry}
      empty={items.length === 0}
      emptyTitle="No insights"
      emptyDescription="Insights will appear here when available."
      className={className}
    >
      <div className="grid gap-3">
        {items.map((item) => (
          <InsightCard
            key={item.id}
            title={item.title}
            body={item.body}
            tone={item.tone ?? "info"}
          />
        ))}
      </div>
    </SectionShell>
  );
}

type RecommendationItem = {
  id: string;
  title: string;
  summary: string;
  priority?: "low" | "medium" | "high";
  actions?: ReactNode;
};

type AnalyticsRecommendationPanelProps = {
  title?: string;
  description?: string;
  items: RecommendationItem[];
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  className?: string;
};

export function AnalyticsRecommendationPanel({
  title = "Recommendations",
  description,
  items,
  loading,
  error,
  onRetry,
  className,
}: AnalyticsRecommendationPanelProps) {
  return (
    <SectionShell
      title={title}
      description={description}
      loading={loading}
      error={error}
      onRetry={onRetry}
      empty={items.length === 0}
      emptyTitle="No recommendations"
      emptyDescription="Recommendations will appear here when available."
      className={className}
    >
      <div className="grid gap-3">
        {items.map((item) => (
          <RecommendationCard
            key={item.id}
            title={item.title}
            summary={item.summary}
            priority={item.priority}
            actions={item.actions}
          />
        ))}
      </div>
    </SectionShell>
  );
}
