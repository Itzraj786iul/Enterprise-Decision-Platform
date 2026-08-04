"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartCard, ChartContainer, ChartTooltip } from "@/components/charts";
import { ErrorState, EmptyState } from "@/components/feedback/empty-state";
import { LoadingSpinner } from "@/components/feedback/loading-spinner";
import type { DashboardTrendPoint } from "@/services/dashboard";

type Props = {
  points?: DashboardTrendPoint[];
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
};

function formatDay(value: string) {
  try {
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(
      new Date(value),
    );
  } catch {
    return value;
  }
}

export function RevenueTrendChart({ points = [], loading, error, onRetry }: Props) {
  if (error) {
    return (
      <ErrorState title="Unable to load trends" description={error.message} onRetry={onRetry} />
    );
  }

  return (
    <ChartCard
      title="Revenue, Profit & Orders"
      description="Daily executive scorecard trends"
    >
      {loading && points.length === 0 ? (
        <div className="flex h-[280px] items-center justify-center">
          <LoadingSpinner label="Loading trends" />
        </div>
      ) : points.length === 0 ? (
        <EmptyState
          title="No trend data"
          description="Executive scorecard returned no dated rows for this window."
        />
      ) : (
        <ChartContainer label="Revenue profit and orders trend chart" minHeight={280}>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={points} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDay}
                tick={{ fontSize: 12 }}
                stroke="currentColor"
                className="text-muted-foreground"
              />
              <YAxis
                yAxisId="money"
                tick={{ fontSize: 12 }}
                stroke="currentColor"
                className="text-muted-foreground"
                tickFormatter={(v) => `$${Number(v).toLocaleString()}`}
              />
              <YAxis
                yAxisId="orders"
                orientation="right"
                tick={{ fontSize: 12 }}
                stroke="currentColor"
                className="text-muted-foreground"
              />
              <Tooltip
                content={({ active, label, payload }) => {
                  if (!active || !payload?.length) return null;
                  return (
                    <ChartTooltip label={label ? formatDay(String(label)) : undefined}>
                      <ul className="space-y-1">
                        {payload.map((item) => (
                          <li key={String(item.dataKey)} className="flex justify-between gap-4">
                            <span>{item.name}</span>
                            <span className="font-medium tabular-nums">
                              {item.dataKey === "orders"
                                ? Number(item.value).toLocaleString()
                                : `$${Number(item.value).toLocaleString()}`}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </ChartTooltip>
                  );
                }}
              />
              <Legend />
              <Line
                yAxisId="money"
                type="monotone"
                dataKey="revenue"
                name="Revenue"
                stroke="var(--chart-1)"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                yAxisId="money"
                type="monotone"
                dataKey="profit"
                name="Profit"
                stroke="var(--chart-2)"
                strokeWidth={2}
                dot={false}
              />
              <Line
                yAxisId="orders"
                type="monotone"
                dataKey="orders"
                name="Orders"
                stroke="var(--chart-3)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </ChartContainer>
      )}
    </ChartCard>
  );
}
