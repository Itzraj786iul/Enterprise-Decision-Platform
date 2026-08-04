"use client";

import type { ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  Cell,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  Treemap,
  XAxis,
  YAxis,
} from "recharts";
import { ChartCard, ChartContainer, ChartTooltip } from "@/components/charts";
import { EmptyState } from "@/components/feedback/empty-state";

export type AnalyticsChartSeries = {
  dataKey: string;
  name: string;
  color?: string;
};

export type AnalyticsChartPoint = Record<string, string | number | null | undefined>;

type BaseChartProps = {
  title: string;
  description?: string;
  data: AnalyticsChartPoint[];
  xKey: string;
  series: AnalyticsChartSeries[];
  height?: number;
  toolbar?: ReactNode;
  emptyTitle?: string;
  className?: string;
};

const DEFAULT_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

function ChartShell({
  title,
  description,
  toolbar,
  className,
  label,
  height = 280,
  empty,
  children,
}: {
  title: string;
  description?: string;
  toolbar?: ReactNode;
  className?: string;
  label: string;
  height?: number;
  empty: boolean;
  children: ReactNode;
}) {
  return (
    <ChartCard title={title} description={description} toolbar={toolbar} className={className}>
      {empty ? (
        <EmptyState title="No chart data" description="Provide series data to render this chart." />
      ) : (
        <ChartContainer label={label} minHeight={height}>
          <ResponsiveContainer width="100%" height={height}>
            {children}
          </ResponsiveContainer>
        </ChartContainer>
      )}
    </ChartCard>
  );
}

function DefaultTooltip({
  active,
  label,
  payload,
}: {
  active?: boolean;
  label?: string | number;
  payload?: Array<{ name?: string; value?: number | string; color?: string }>;
}) {
  if (!active || !payload?.length) return null;
  return (
    <ChartTooltip label={label != null ? String(label) : undefined}>
      <ul className="space-y-1">
        {payload.map((item) => (
          <li key={String(item.name)} className="flex justify-between gap-4">
            <span style={{ color: item.color }}>{item.name}</span>
            <span className="font-medium tabular-nums">{item.value}</span>
          </li>
        ))}
      </ul>
    </ChartTooltip>
  );
}

export function AnalyticsLineChart({
  title,
  description,
  data,
  xKey,
  series,
  height,
  toolbar,
  className,
}: BaseChartProps) {
  return (
    <ChartShell
      title={title}
      description={description}
      toolbar={toolbar}
      className={className}
      label={`${title} line chart`}
      height={height}
      empty={data.length === 0 || series.length === 0}
    >
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip content={<DefaultTooltip />} />
        <Legend />
        {series.map((s, index) => (
          <Line
            key={s.dataKey}
            type="monotone"
            dataKey={s.dataKey}
            name={s.name}
            stroke={s.color ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ChartShell>
  );
}

export function AnalyticsBarChart(props: BaseChartProps) {
  const { title, description, data, xKey, series, height, toolbar, className } = props;
  return (
    <ChartShell
      title={title}
      description={description}
      toolbar={toolbar}
      className={className}
      label={`${title} bar chart`}
      height={height}
      empty={data.length === 0 || series.length === 0}
    >
      <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip content={<DefaultTooltip />} />
        <Legend />
        {series.map((s, index) => (
          <Bar
            key={s.dataKey}
            dataKey={s.dataKey}
            name={s.name}
            fill={s.color ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ChartShell>
  );
}

export function AnalyticsAreaChart(props: BaseChartProps) {
  const { title, description, data, xKey, series, height, toolbar, className } = props;
  return (
    <ChartShell
      title={title}
      description={description}
      toolbar={toolbar}
      className={className}
      label={`${title} area chart`}
      height={height}
      empty={data.length === 0 || series.length === 0}
    >
      <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip content={<DefaultTooltip />} />
        <Legend />
        {series.map((s, index) => (
          <Area
            key={s.dataKey}
            type="monotone"
            dataKey={s.dataKey}
            name={s.name}
            stroke={s.color ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
            fill={s.color ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
            fillOpacity={0.2}
          />
        ))}
      </AreaChart>
    </ChartShell>
  );
}

type PieChartProps = {
  title: string;
  description?: string;
  data: Array<{ name: string; value: number }>;
  height?: number;
  toolbar?: ReactNode;
  className?: string;
  nameKey?: string;
  valueKey?: string;
};

export function AnalyticsPieChart({
  title,
  description,
  data,
  height = 280,
  toolbar,
  className,
  nameKey = "name",
  valueKey = "value",
}: PieChartProps) {
  return (
    <ChartShell
      title={title}
      description={description}
      toolbar={toolbar}
      className={className}
      label={`${title} pie chart`}
      height={height}
      empty={data.length === 0}
    >
      <PieChart>
        <Pie
          data={data}
          dataKey={valueKey}
          nameKey={nameKey}
          cx="50%"
          cy="50%"
          outerRadius={90}
          label
        >
          {data.map((_, index) => (
            <Cell key={index} fill={DEFAULT_COLORS[index % DEFAULT_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<DefaultTooltip />} />
        <Legend />
      </PieChart>
    </ChartShell>
  );
}

type ScatterChartProps = {
  title: string;
  description?: string;
  data: AnalyticsChartPoint[];
  xKey: string;
  yKey: string;
  name?: string;
  height?: number;
  toolbar?: ReactNode;
  className?: string;
  color?: string;
};

export function AnalyticsScatterChart({
  title,
  description,
  data,
  xKey,
  yKey,
  name = "Series",
  height,
  toolbar,
  className,
  color = DEFAULT_COLORS[0],
}: ScatterChartProps) {
  return (
    <ChartShell
      title={title}
      description={description}
      toolbar={toolbar}
      className={className}
      label={`${title} scatter chart`}
      height={height}
      empty={data.length === 0}
    >
      <ScatterChart margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey={xKey} name={xKey} tick={{ fontSize: 12 }} />
        <YAxis dataKey={yKey} name={yKey} tick={{ fontSize: 12 }} />
        <Tooltip content={<DefaultTooltip />} cursor={{ strokeDasharray: "3 3" }} />
        <Scatter name={name} data={data} fill={color} />
      </ScatterChart>
    </ChartShell>
  );
}

type TreemapProps = {
  title: string;
  description?: string;
  data: Array<{ name: string; size: number }>;
  height?: number;
  toolbar?: ReactNode;
  className?: string;
};

export function AnalyticsTreemapChart({
  title,
  description,
  data,
  height = 280,
  toolbar,
  className,
}: TreemapProps) {
  return (
    <ChartShell
      title={title}
      description={description}
      toolbar={toolbar}
      className={className}
      label={`${title} treemap`}
      height={height}
      empty={data.length === 0}
    >
      <Treemap
        data={data}
        dataKey="size"
        nameKey="name"
        stroke="var(--border)"
        fill={DEFAULT_COLORS[1]}
      />
    </ChartShell>
  );
}

type ComposedChartProps = BaseChartProps & {
  barKeys?: string[];
  lineKeys?: string[];
  areaKeys?: string[];
};

export function AnalyticsComposedChart({
  title,
  description,
  data,
  xKey,
  series,
  height,
  toolbar,
  className,
  barKeys = [],
  lineKeys = [],
  areaKeys = [],
}: ComposedChartProps) {
  return (
    <ChartShell
      title={title}
      description={description}
      toolbar={toolbar}
      className={className}
      label={`${title} composed chart`}
      height={height}
      empty={data.length === 0 || series.length === 0}
    >
      <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip content={<DefaultTooltip />} />
        <Legend />
        {series.map((s, index) => {
          const color = s.color ?? DEFAULT_COLORS[index % DEFAULT_COLORS.length];
          if (barKeys.includes(s.dataKey)) {
            return <Bar key={s.dataKey} dataKey={s.dataKey} name={s.name} fill={color} />;
          }
          if (areaKeys.includes(s.dataKey)) {
            return (
              <Area
                key={s.dataKey}
                type="monotone"
                dataKey={s.dataKey}
                name={s.name}
                fill={color}
                stroke={color}
                fillOpacity={0.2}
              />
            );
          }
          if (lineKeys.includes(s.dataKey) || (!barKeys.length && !areaKeys.length)) {
            return (
              <Line
                key={s.dataKey}
                type="monotone"
                dataKey={s.dataKey}
                name={s.name}
                stroke={color}
                strokeWidth={2}
                dot={false}
              />
            );
          }
          return (
            <Line
              key={s.dataKey}
              type="monotone"
              dataKey={s.dataKey}
              name={s.name}
              stroke={color}
              strokeWidth={2}
              dot={false}
            />
          );
        })}
      </ComposedChart>
    </ChartShell>
  );
}

type HeatmapPlaceholderProps = {
  title?: string;
  description?: string;
  className?: string;
};

/** Placeholder until a production heatmap library is selected. */
export function AnalyticsHeatmapPlaceholder({
  title = "Heatmap",
  description = "Heatmap visualization will be enabled in a later release.",
  className,
}: HeatmapPlaceholderProps) {
  return (
    <ChartCard title={title} description={description} className={className}>
      <EmptyState
        title="Heatmap coming soon"
        description="This slot is reserved for a reusable heatmap wrapper."
      />
    </ChartCard>
  );
}
