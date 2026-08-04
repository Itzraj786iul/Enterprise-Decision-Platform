"use client";

import type { ReactNode } from "react";
import { RotateCcw } from "lucide-react";
import { DateRangePicker } from "@/components/forms/date-range-picker";
import { SearchBar } from "@/components/forms/search-bar";
import { SelectField, type SelectOption } from "@/components/forms/select-field";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { AnalyticsDateRange, AnalyticsOption } from "@/components/analytics/types";

type DateRangeFilterProps = {
  value: AnalyticsDateRange;
  onChange: (value: AnalyticsDateRange) => void;
  className?: string;
  id?: string;
};

export function DateRangeFilter({ value, onChange, className, id }: DateRangeFilterProps) {
  return (
    <DateRangePicker
      id={id ?? "analytics-date-range"}
      className={className}
      start={value.start}
      end={value.end}
      onStartChange={(start) => onChange({ ...value, start })}
      onEndChange={(end) => onChange({ ...value, end })}
      startLabel="From"
      endLabel="To"
    />
  );
}

type MultiSelectFilterProps = {
  label: string;
  options: AnalyticsOption[];
  value: string[];
  onChange: (value: string[]) => void;
  placeholder?: string;
  className?: string;
  id?: string;
};

/**
 * Compact multi-select using successive single selects + chips.
 * Keeps dependency surface small while remaining accessible.
 */
function MultiSelectFilter({
  label,
  options,
  value,
  onChange,
  placeholder = "Add…",
  className,
  id,
}: MultiSelectFilterProps) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  const available = options.filter((o) => !value.includes(o.value));

  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor={fieldId}>{label}</Label>
      <Select
        value=""
        onValueChange={(next) => {
          if (!next || value.includes(next)) return;
          onChange([...value, next]);
        }}
      >
        <SelectTrigger id={fieldId} aria-label={label}>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {available.length === 0 ? (
            <SelectItem value="__none" disabled>
              No more options
            </SelectItem>
          ) : (
            available.map((option) => (
              <SelectItem key={option.value} value={option.value} disabled={option.disabled}>
                {option.label}
              </SelectItem>
            ))
          )}
        </SelectContent>
      </Select>
      {value.length > 0 ? (
        <ul className="flex flex-wrap gap-1" aria-label={`${label} selected`}>
          {value.map((idValue) => {
            const option = options.find((o) => o.value === idValue);
            return (
              <li key={idValue}>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  className="h-7 px-2 text-xs"
                  onClick={() => onChange(value.filter((v) => v !== idValue))}
                  aria-label={`Remove ${option?.label ?? idValue}`}
                >
                  {option?.label ?? idValue} ×
                </Button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

type OptionFilterProps = {
  options: AnalyticsOption[];
  value: string[];
  onChange: (value: string[]) => void;
  className?: string;
  label?: string;
  placeholder?: string;
};

export function RegionFilter({
  label = "Region",
  placeholder = "Add region",
  ...props
}: OptionFilterProps) {
  return <MultiSelectFilter label={label} placeholder={placeholder} {...props} />;
}

export function CategoryFilter({
  label = "Category",
  placeholder = "Add category",
  ...props
}: OptionFilterProps) {
  return <MultiSelectFilter label={label} placeholder={placeholder} {...props} />;
}

export function CustomerFilter({
  label = "Customer",
  placeholder = "Add customer",
  ...props
}: OptionFilterProps) {
  return <MultiSelectFilter label={label} placeholder={placeholder} {...props} />;
}

export function ProductFilter({
  label = "Product",
  placeholder = "Add product",
  ...props
}: OptionFilterProps) {
  return <MultiSelectFilter label={label} placeholder={placeholder} {...props} />;
}

type SearchFilterProps = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
};

export function SearchFilter({
  value,
  onChange,
  placeholder = "Search analytics…",
  className,
}: SearchFilterProps) {
  return (
    <SearchBar
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className={cn("max-w-none", className)}
    />
  );
}

type ResetFiltersButtonProps = {
  onReset: () => void;
  disabled?: boolean;
  className?: string;
};

export function ResetFiltersButton({ onReset, disabled, className }: ResetFiltersButtonProps) {
  return (
    <Button
      type="button"
      variant="outline"
      size="sm"
      className={className}
      onClick={onReset}
      disabled={disabled}
      aria-label="Reset analytics filters"
    >
      <RotateCcw className="h-4 w-4" aria-hidden="true" />
      Reset
    </Button>
  );
}

type SingleSelectFilterProps = {
  label: string;
  value?: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  className?: string;
};

/** Convenience single-select for simple dimension filters. */
export function SingleDimensionFilter(props: SingleSelectFilterProps) {
  return <SelectField {...props} />;
}

type AnalyticsFilterBarProps = {
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
};

export function AnalyticsFilterBar({ children, actions, className }: AnalyticsFilterBarProps) {
  return (
    <section
      className={cn(
        "rounded-lg border border-border bg-card p-4 shadow-xs",
        className,
      )}
      aria-label="Analytics filters"
    >
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{children}</div>
      {actions ? (
        <div className="mt-4 flex flex-wrap items-center justify-end gap-2">{actions}</div>
      ) : null}
    </section>
  );
}
