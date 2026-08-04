"use client";

import * as React from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Download,
  Settings2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/feedback/empty-state";

export type DataTableColumn<T> = {
  id: string;
  header: string;
  accessor: (row: T) => React.ReactNode;
  sortable?: boolean;
  className?: string;
  align?: "left" | "center" | "right";
};

type SortState = { id: string; direction: "asc" | "desc" } | null;

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  data: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  filterPlaceholder?: string;
  filterValue?: string;
  onFilterChange?: (value: string) => void;
  page?: number;
  pageSize?: number;
  totalRows?: number;
  onPageChange?: (page: number) => void;
  stickyHeader?: boolean;
  enableColumnVisibility?: boolean;
  exportSlot?: React.ReactNode;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
  /** Optional client-side sort comparator when sort is uncontrolled. */
  sortComparator?: (a: T, b: T, sort: NonNullable<SortState>) => number;
};

export function DataTable<T>({
  columns,
  data,
  rowKey,
  loading = false,
  filterPlaceholder = "Filter…",
  filterValue,
  onFilterChange,
  page = 1,
  pageSize = 10,
  totalRows,
  onPageChange,
  stickyHeader = true,
  enableColumnVisibility = true,
  exportSlot,
  emptyTitle = "No rows",
  emptyDescription = "Adjust filters or try a different query.",
  className,
  sortComparator,
}: DataTableProps<T>) {
  const [sort, setSort] = React.useState<SortState>(null);
  const [visible, setVisible] = React.useState<Record<string, boolean>>(
    () => Object.fromEntries(columns.map((c) => [c.id, true])),
  );

  const visibleColumns = columns.filter((c) => visible[c.id] !== false);

  const sortedData = React.useMemo(() => {
    if (!sort || !sortComparator) return data;
    return [...data].sort((a, b) => sortComparator(a, b, sort));
  }, [data, sort, sortComparator]);

  const total = totalRows ?? sortedData.length;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(page, pageCount);

  const toggleSort = (id: string) => {
    setSort((prev) => {
      if (!prev || prev.id !== id) return { id, direction: "asc" };
      if (prev.direction === "asc") return { id, direction: "desc" };
      return null;
    });
  };

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        {onFilterChange ? (
          <Input
            value={filterValue}
            onChange={(e) => onFilterChange(e.target.value)}
            placeholder={filterPlaceholder}
            className="max-w-sm"
            aria-label="Filter table"
          />
        ) : (
          <div />
        )}
        <div className="flex items-center gap-2">
          {exportSlot ?? (
            <Button variant="outline" size="sm" type="button" disabled>
              <Download className="h-4 w-4" aria-hidden="true" />
              Export
            </Button>
          )}
          {enableColumnVisibility ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" aria-label="Toggle column visibility">
                  <Settings2 className="h-4 w-4" />
                  Columns
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Visible columns</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {columns.map((column) => (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    checked={visible[column.id] !== false}
                    onCheckedChange={(checked) =>
                      setVisible((prev) => ({ ...prev, [column.id]: Boolean(checked) }))
                    }
                  >
                    {column.header}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          ) : null}
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-card shadow-xs">
        <div className="relative w-full overflow-auto">
          <table className="w-full caption-bottom text-sm">
            <thead
              className={cn(
                "bg-muted/60 text-muted-foreground",
                stickyHeader && "sticky top-0 z-10 backdrop-blur",
              )}
            >
              <tr className="border-b border-border">
                {visibleColumns.map((column) => {
                  const align =
                    column.align === "right"
                      ? "text-right"
                      : column.align === "center"
                        ? "text-center"
                        : "text-left";
                  const isSorted = sort?.id === column.id;
                  return (
                    <th
                      key={column.id}
                      scope="col"
                      className={cn(
                        "h-11 px-4 font-medium",
                        align,
                        column.className,
                      )}
                    >
                      {column.sortable ? (
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 rounded-sm hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          onClick={() => toggleSort(column.id)}
                          aria-label={`Sort by ${column.header}`}
                        >
                          {column.header}
                          {isSorted ? (
                            sort.direction === "asc" ? (
                              <ArrowUp className="h-3.5 w-3.5" aria-hidden="true" />
                            ) : (
                              <ArrowDown className="h-3.5 w-3.5" aria-hidden="true" />
                            )
                          ) : (
                            <ArrowUpDown className="h-3.5 w-3.5 opacity-50" aria-hidden="true" />
                          )}
                        </button>
                      ) : (
                        column.header
                      )}
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={`sk-${i}`} className="border-b border-border">
                    {visibleColumns.map((column) => (
                      <td key={column.id} className="px-4 py-3">
                        <Skeleton className="h-4 w-full" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : sortedData.length === 0 ? (
                <tr>
                  <td colSpan={visibleColumns.length} className="p-0">
                    <EmptyState title={emptyTitle} description={emptyDescription} className="border-0" />
                  </td>
                </tr>
              ) : (
                sortedData.map((row) => (
                  <tr
                    key={rowKey(row)}
                    className="border-b border-border transition-colors hover:bg-muted/40"
                  >
                    {visibleColumns.map((column) => {
                      const align =
                        column.align === "right"
                          ? "text-right"
                          : column.align === "center"
                            ? "text-center"
                            : "text-left";
                      return (
                        <td key={column.id} className={cn("px-4 py-3 align-middle", align, column.className)}>
                          {column.accessor(row)}
                        </td>
                      );
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">
          Page {currentPage} of {pageCount} · {total} rows
        </p>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage <= 1 || !onPageChange}
            onClick={() => onPageChange?.(currentPage - 1)}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage >= pageCount || !onPageChange}
            onClick={() => onPageChange?.(currentPage + 1)}
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

/** Alias with explicit sorting emphasis. */
export function SortableTable<T>(props: DataTableProps<T>) {
  return <DataTable {...props} />;
}

export function LoadingTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50">
            {Array.from({ length: cols }).map((_, i) => (
              <th key={i} className="px-4 py-3 text-left">
                <Skeleton className="h-4 w-20" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, r) => (
            <tr key={r} className="border-b border-border">
              {Array.from({ length: cols }).map((_, c) => (
                <td key={c} className="px-4 py-3">
                  <Skeleton className="h-4 w-full" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { EmptyState as TableEmptyState };
