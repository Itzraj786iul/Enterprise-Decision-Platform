"use client";

import { Filter } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

type FilterPanelProps = {
  title?: string;
  children: React.ReactNode;
  onApply?: () => void;
  onReset?: () => void;
  className?: string;
};

export function FilterPanel({
  title = "Filters",
  children,
  onApply,
  onReset,
  className,
}: FilterPanelProps) {
  return (
    <aside
      className={cn(
        "flex w-full flex-col gap-4 rounded-lg border border-border bg-card p-4 shadow-xs",
        className,
      )}
      aria-label={title}
    >
      <div className="flex items-center gap-2">
        <Filter className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        <p className="text-sm font-semibold">{title}</p>
      </div>
      <Separator />
      <div className="space-y-4">{children}</div>
      <div className="mt-auto flex gap-2 pt-2">
        {onReset ? (
          <Button type="button" variant="outline" className="flex-1" onClick={onReset}>
            Reset
          </Button>
        ) : null}
        {onApply ? (
          <Button type="button" className="flex-1" onClick={onApply}>
            Apply
          </Button>
        ) : null}
      </div>
    </aside>
  );
}
