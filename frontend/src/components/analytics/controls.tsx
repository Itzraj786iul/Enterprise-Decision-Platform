"use client";

import type { ReactNode } from "react";
import { Download, LayoutGrid, RefreshCw, Table2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type {
  AnalyticsExportFormat,
  AnalyticsMetricOption,
  AnalyticsViewMode,
} from "@/components/analytics/types";

type MetricSelectorProps = {
  metrics: AnalyticsMetricOption[];
  value: string[];
  onChange: (metricIds: string[]) => void;
  className?: string;
  label?: string;
};

export function MetricSelector({
  metrics,
  value,
  onChange,
  className,
  label = "Metric",
}: MetricSelectorProps) {
  const primary = value[0] ?? metrics[0]?.id ?? "";
  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor="analytics-metric-selector">{label}</Label>
      <Select
        value={primary}
        onValueChange={(next) => onChange([next])}
      >
        <SelectTrigger id="analytics-metric-selector" aria-label={label}>
          <SelectValue placeholder="Select metric" />
        </SelectTrigger>
        <SelectContent>
          {metrics.map((metric) => (
            <SelectItem key={metric.id} value={metric.id}>
              {metric.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

type ViewToggleProps = {
  value: AnalyticsViewMode;
  onChange: (mode: AnalyticsViewMode) => void;
  className?: string;
};

export function ViewToggle({ value, onChange, className }: ViewToggleProps) {
  const modes: { id: AnalyticsViewMode; label: string; icon: ReactNode }[] = [
    { id: "chart", label: "Chart", icon: <LayoutGrid className="h-4 w-4" aria-hidden="true" /> },
    { id: "table", label: "Table", icon: <Table2 className="h-4 w-4" aria-hidden="true" /> },
    { id: "split", label: "Split", icon: <LayoutGrid className="h-4 w-4" aria-hidden="true" /> },
  ];

  return (
    <div
      className={cn("inline-flex rounded-md border border-border p-0.5", className)}
      role="group"
      aria-label="View mode"
    >
      {modes.map((mode) => (
        <Button
          key={mode.id}
          type="button"
          size="sm"
          variant={value === mode.id ? "secondary" : "ghost"}
          className="gap-1.5"
          aria-pressed={value === mode.id}
          onClick={() => onChange(mode.id)}
        >
          {mode.icon}
          {mode.label}
        </Button>
      ))}
    </div>
  );
}

type RefreshButtonProps = {
  onRefresh: () => void;
  loading?: boolean;
  className?: string;
};

export function RefreshButton({ onRefresh, loading, className }: RefreshButtonProps) {
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={className}
      onClick={onRefresh}
      disabled={loading}
      aria-label="Refresh analytics data"
      aria-busy={loading || undefined}
    >
      <RefreshCw className={cn("h-4 w-4", loading && "animate-edp-spin")} aria-hidden="true" />
      Refresh
    </Button>
  );
}

type ExportToolbarProps = {
  onExport: (format: AnalyticsExportFormat) => void;
  disabled?: boolean;
  formats?: AnalyticsExportFormat[];
  className?: string;
};

export function ExportToolbar({
  onExport,
  disabled,
  formats = ["csv", "excel", "pdf", "png"],
  className,
}: ExportToolbarProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className={className}
          disabled={disabled}
          aria-label="Export analytics"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Export format</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {formats.map((format) => (
          <DropdownMenuItem key={format} onSelect={() => onExport(format)}>
            {format.toUpperCase()}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

type LastUpdatedIndicatorProps = {
  value?: string | Date | null;
  className?: string;
};

export function LastUpdatedIndicator({ value, className }: LastUpdatedIndicatorProps) {
  const label = !value
    ? "Not updated yet"
    : `Updated ${typeof value === "string" ? value : new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(value)}`;

  return (
    <p className={cn("text-xs text-muted-foreground", className)} aria-live="polite">
      <time dateTime={typeof value === "string" ? value : value?.toISOString()}>{label}</time>
    </p>
  );
}
