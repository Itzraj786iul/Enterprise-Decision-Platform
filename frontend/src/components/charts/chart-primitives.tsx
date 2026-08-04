import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Maximize2, RefreshCw } from "lucide-react";

type ChartContainerProps = {
  children: React.ReactNode;
  className?: string;
  minHeight?: number;
  label?: string;
};

/**
 * Accessible chart wrapper. Put Recharts (or any chart) as children.
 * No chart data lives here.
 */
export function ChartContainer({
  children,
  className,
  minHeight = 280,
  label = "Chart",
}: ChartContainerProps) {
  return (
    <div
      className={cn("relative w-full", className)}
      style={{ minHeight }}
      role="img"
      aria-label={label}
    >
      {children}
    </div>
  );
}

type ChartCardProps = {
  title: string;
  description?: string;
  children: React.ReactNode;
  toolbar?: React.ReactNode;
  legend?: React.ReactNode;
  className?: string;
};

export function ChartCard({
  title,
  description,
  children,
  toolbar,
  legend,
  className,
}: ChartCardProps) {
  return (
    <Card className={className}>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <CardTitle>{title}</CardTitle>
          {description ? <CardDescription>{description}</CardDescription> : null}
        </div>
        {toolbar}
      </CardHeader>
      <CardContent className="space-y-4">
        {children}
        {legend}
      </CardContent>
    </Card>
  );
}

type ChartLegendItem = {
  label: string;
  color: string;
};

type ChartLegendProps = {
  items: ChartLegendItem[];
  className?: string;
};

export function ChartLegend({ items, className }: ChartLegendProps) {
  return (
    <ul className={cn("flex flex-wrap gap-4", className)} aria-label="Chart legend">
      {items.map((item) => (
        <li key={item.label} className="inline-flex items-center gap-2 text-xs text-muted-foreground">
          <span
            className="h-2.5 w-2.5 rounded-sm"
            style={{ backgroundColor: item.color }}
            aria-hidden="true"
          />
          {item.label}
        </li>
      ))}
    </ul>
  );
}

type ChartTooltipFrameProps = {
  label?: string;
  children: React.ReactNode;
  className?: string;
};

/** Presentational tooltip chrome for custom Recharts tooltips. */
export function ChartTooltip({ label, children, className }: ChartTooltipFrameProps) {
  return (
    <div
      className={cn(
        "rounded-md border border-border bg-popover px-3 py-2 text-xs text-popover-foreground shadow-md",
        className,
      )}
    >
      {label ? <p className="mb-1 font-medium">{label}</p> : null}
      {children}
    </div>
  );
}

type ChartToolbarProps = {
  onRefresh?: () => void;
  onExport?: () => void;
  onExpand?: () => void;
  children?: React.ReactNode;
  className?: string;
};

export function ChartToolbar({
  onRefresh,
  onExport,
  onExpand,
  children,
  className,
}: ChartToolbarProps) {
  return (
    <div className={cn("flex flex-wrap items-center gap-1", className)}>
      {children}
      {onRefresh ? (
        <Button variant="ghost" size="icon" aria-label="Refresh chart" onClick={onRefresh}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      ) : null}
      {onExport ? (
        <Button variant="ghost" size="icon" aria-label="Export chart" onClick={onExport}>
          <Download className="h-4 w-4" />
        </Button>
      ) : null}
      {onExpand ? (
        <Button variant="ghost" size="icon" aria-label="Expand chart" onClick={onExpand}>
          <Maximize2 className="h-4 w-4" />
        </Button>
      ) : null}
    </div>
  );
}
