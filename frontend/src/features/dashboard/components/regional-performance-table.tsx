"use client";

import { DataTable, type DataTableColumn } from "@/components/tables";
import { ErrorState } from "@/components/feedback/empty-state";
import { SectionHeader } from "@/components/layout/section-header";
import type { RegionalPerformanceRow } from "@/services/dashboard";

type Props = {
  rows?: RegionalPerformanceRow[];
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
};

const columns: DataTableColumn<RegionalPerformanceRow>[] = [
  {
    id: "region",
    header: "Region",
    accessor: (row) => row.region,
    sortable: true,
  },
  {
    id: "revenue",
    header: "Revenue",
    align: "right",
    accessor: (row) =>
      row.revenue == null ? "—" : `$${row.revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
    sortable: true,
  },
  {
    id: "profit",
    header: "Profit",
    align: "right",
    accessor: (row) =>
      row.profit == null ? "—" : `$${row.profit.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
    sortable: true,
  },
  {
    id: "growth",
    header: "Growth",
    align: "right",
    accessor: (row) =>
      row.growth == null ? "—" : `${(row.growth * 100).toFixed(1)}%`,
    sortable: true,
  },
];

export function RegionalPerformanceTable({ rows = [], loading, error, onRetry }: Props) {
  if (error) {
    return (
      <ErrorState
        title="Unable to load regional performance"
        description={error.message}
        onRetry={onRetry}
      />
    );
  }

  return (
    <section aria-label="Regional performance">
      <SectionHeader
        title="Regional Performance"
        description="Revenue, profit, and growth by region"
      />
      <DataTable
        columns={columns}
        data={rows}
        rowKey={(row) => row.region}
        loading={loading}
        emptyTitle="No regional rows"
        emptyDescription="No regional sales detail was available from analytics views."
        enableColumnVisibility={false}
        sortComparator={(a, b, sort) => {
          const av = a[sort.id as keyof RegionalPerformanceRow];
          const bv = b[sort.id as keyof RegionalPerformanceRow];
          if (av == null && bv == null) return 0;
          if (av == null) return 1;
          if (bv == null) return -1;
          if (av < bv) return sort.direction === "asc" ? -1 : 1;
          if (av > bv) return sort.direction === "asc" ? 1 : -1;
          return 0;
        }}
      />
    </section>
  );
}
