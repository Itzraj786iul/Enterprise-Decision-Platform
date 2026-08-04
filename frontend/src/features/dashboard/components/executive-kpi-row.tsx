"use client";

import {
  DollarSign,
  HeartPulse,
  Percent,
  ShieldAlert,
  ShoppingBag,
  TrendingUp,
  Users,
  Warehouse,
  type LucideIcon,
} from "lucide-react";
import { MetricCard } from "@/components/cards";
import { ErrorState } from "@/components/feedback/empty-state";
import type { DashboardMetric } from "@/services/dashboard";
import type { TrendDirection } from "@/styles/tokens";

const ICONS: Record<string, LucideIcon> = {
  revenue: DollarSign,
  profit: DollarSign,
  profit_margin: Percent,
  revenue_growth: TrendingUp,
  active_customers: Users,
  inventory_health: Warehouse,
  dq_score: HeartPulse,
  overall_churn_risk: ShieldAlert,
};

function formatDelta(metric: DashboardMetric): string | undefined {
  if (metric.delta == null) return undefined;
  const pct = `${(metric.delta * 100).toFixed(1)}%`;
  const label = metric.delta_label ? ` ${metric.delta_label}` : "";
  return `${metric.delta > 0 ? "+" : ""}${pct}${label}`;
}

type Props = {
  metrics?: DashboardMetric[];
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
};

export function ExecutiveKpiRow({ metrics = [], loading, error, onRetry }: Props) {
  if (error) {
    return (
      <ErrorState
        title="Unable to load executive KPIs"
        description={error.message}
        onRetry={onRetry}
      />
    );
  }

  if (loading && metrics.length === 0) {
    return (
      <section aria-label="Executive KPIs" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <MetricCard key={`sk-${i}`} title="Loading" loading />
        ))}
      </section>
    );
  }

  return (
    <section aria-label="Executive KPIs" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((full) => {
        const Icon = ICONS[full.id] ?? ShoppingBag;
        const value =
          full.available && full.formatted_value
            ? full.formatted_value
            : full.available
              ? String(full.value ?? "—")
              : "Unavailable";
        return (
          <MetricCard
            key={full.id}
            title={full.label}
            value={value}
            delta={formatDelta(full)}
            trend={(full.trend as TrendDirection | null) ?? "flat"}
            icon={Icon}
            description={full.source ? `Source: ${full.source}` : undefined}
          />
        );
      })}
    </section>
  );
}
