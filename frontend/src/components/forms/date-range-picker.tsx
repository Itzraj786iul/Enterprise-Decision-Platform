"use client";

import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type DateRangePickerProps = {
  start: string;
  end: string;
  onStartChange: (value: string) => void;
  onEndChange: (value: string) => void;
  startLabel?: string;
  endLabel?: string;
  className?: string;
  id?: string;
};

/**
 * Accessible date range inputs (native).
 * Swap for a calendar popover later without changing the prop contract.
 */
export function DateRangePicker({
  start,
  end,
  onStartChange,
  onEndChange,
  startLabel = "Start date",
  endLabel = "End date",
  className,
  id = "date-range",
}: DateRangePickerProps) {
  return (
    <div className={cn("grid gap-3 sm:grid-cols-2", className)}>
      <div className="space-y-1.5">
        <Label htmlFor={`${id}-start`}>{startLabel}</Label>
        <Input
          id={`${id}-start`}
          type="date"
          value={start}
          onChange={(e) => onStartChange(e.target.value)}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor={`${id}-end`}>{endLabel}</Label>
        <Input
          id={`${id}-end`}
          type="date"
          value={end}
          onChange={(e) => onEndChange(e.target.value)}
        />
      </div>
    </div>
  );
}
