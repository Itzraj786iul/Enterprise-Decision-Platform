import { ArrowDownRight, ArrowRight, ArrowUpRight, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import type { TrendDirection } from "@/styles/tokens";

type MetricCardProps = {
  title: string;
  value?: React.ReactNode;
  delta?: string;
  trend?: TrendDirection;
  icon?: LucideIcon;
  sparkline?: React.ReactNode;
  loading?: boolean;
  description?: string;
  className?: string;
};

const trendIcon = {
  up: ArrowUpRight,
  down: ArrowDownRight,
  flat: ArrowRight,
} as const;

const trendTone = {
  up: "text-success",
  down: "text-danger",
  flat: "text-muted-foreground",
} as const;

/**
 * Standard KPI / metric card.
 * Presentational only — pass formatted values from the feature layer.
 */
export function MetricCard({
  title,
  value,
  delta,
  trend = "flat",
  icon: Icon,
  sparkline,
  loading = false,
  description,
  className,
}: MetricCardProps) {
  const TrendIcon = trendIcon[trend];

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {description ? (
            <p className="text-xs text-muted-foreground/80">{description}</p>
          ) : null}
        </div>
        {Icon ? (
          <span className="rounded-md bg-muted p-2 text-muted-foreground">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          <>
            <Skeleton className="h-8 w-28" />
            <Skeleton className="h-4 w-20" />
          </>
        ) : (
          <>
            <p className="text-2xl font-semibold tracking-tight tabular-nums">{value}</p>
            <div className="flex items-center justify-between gap-3">
              {delta ? (
                <p className={cn("inline-flex items-center gap-1 text-xs font-medium", trendTone[trend])}>
                  <TrendIcon className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>{delta}</span>
                  <span className="sr-only">Trend {trend}</span>
                </p>
              ) : (
                <span />
              )}
              {sparkline ? (
                <div className="h-8 w-24 shrink-0" aria-hidden="true">
                  {sparkline}
                </div>
              ) : null}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export function StatCard(props: MetricCardProps) {
  return <MetricCard {...props} />;
}

type TrendCardProps = MetricCardProps & {
  periodLabel?: string;
};

export function TrendCard({ periodLabel, ...props }: TrendCardProps) {
  return (
    <MetricCard
      {...props}
      description={props.description ?? periodLabel}
    />
  );
}

type InsightCardProps = {
  title: string;
  body: string;
  tone?: "info" | "success" | "warning" | "danger";
  action?: React.ReactNode;
  className?: string;
};

export function InsightCard({
  title,
  body,
  tone = "info",
  action,
  className,
}: InsightCardProps) {
  return (
    <Card className={cn(className)} style={{ borderLeft: `4px solid var(--${tone})` }}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold">{title}</p>
          <Badge variant={tone === "danger" ? "danger" : tone}>{tone}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{body}</p>
        {action}
      </CardContent>
    </Card>
  );
}

type RecommendationCardProps = {
  title: string;
  summary: string;
  priority?: "low" | "medium" | "high";
  actions?: React.ReactNode;
  className?: string;
};

const priorityVariant = {
  low: "muted" as const,
  medium: "warning" as const,
  high: "danger" as const,
};

export function RecommendationCard({
  title,
  summary,
  priority = "medium",
  actions,
  className,
}: RecommendationCardProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold">{title}</p>
          <Badge variant={priorityVariant[priority]}>{priority} priority</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{summary}</p>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </CardContent>
    </Card>
  );
}

type AlertCardProps = {
  title: string;
  description?: string;
  severity?: "info" | "warning" | "danger" | "success";
  action?: React.ReactNode;
  className?: string;
};

export function AlertCard({
  title,
  description,
  severity = "warning",
  action,
  className,
}: AlertCardProps) {
  return (
    <Card
      className={cn("bg-card", className)}
      role="status"
      style={{ boxShadow: `inset 3px 0 0 var(--${severity})` }}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-semibold">{title}</p>
          <Badge variant={severity === "danger" ? "danger" : severity}>{severity}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
        {action}
      </CardContent>
    </Card>
  );
}
