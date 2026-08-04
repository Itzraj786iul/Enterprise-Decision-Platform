# 11 — Analytics UI Framework

Reusable frontend infrastructure for every analytics module (Sales, Customer, Finance, Operations, AI, and future domains). This layer is presentational and stateful for **filters / view / export orchestration only**. It does not call business APIs and does not implement feature pages.

## Goals

- One composition pattern for analytics pages
- Shared filters, toolbar controls, section shells, and chart wrappers
- URL-synced + persisted filter/selection state
- Export contracts ready for later adapters (CSV / Excel / PDF / PNG)
- Accessibility and responsive layout by default

## Component hierarchy

```
AnalyticsPageLayout
├── AnalyticsHeader          (title, breadcrumbs, page actions)
├── AnalyticsToolbar         (metrics, view, refresh, export, last updated)
├── AnalyticsFilterBar
│   ├── DateRangeFilter
│   ├── RegionFilter
│   ├── CategoryFilter
│   ├── CustomerFilter
│   ├── ProductFilter
│   ├── SearchFilter
│   └── ResetFiltersButton
├── children (sections)
│   ├── AnalyticsKPIGrid
│   ├── AnalyticsTrendSection
│   ├── AnalyticsComparisonSection
│   ├── AnalyticsBreakdownSection
│   ├── AnalyticsTableSection
│   ├── AnalyticsInsightPanel
│   └── AnalyticsRecommendationPanel
└── AnalyticsFooter
```

Chart wrappers live under the same package and are dropped into section `children`:

| Wrapper | Role |
|---------|------|
| `AnalyticsLineChart` | Trends over time |
| `AnalyticsBarChart` | Comparisons |
| `AnalyticsAreaChart` | Cumulative / stacked trends |
| `AnalyticsPieChart` | Share / mix |
| `AnalyticsScatterChart` | Correlation |
| `AnalyticsTreemapChart` | Hierarchical magnitude |
| `AnalyticsComposedChart` | Mixed bar / line / area |
| `AnalyticsHeatmapPlaceholder` | Reserved slot (no lib yet) |

All chart wrappers compose existing design-system `ChartCard` and `ChartContainer`.

## Package layout

```
frontend/src/components/analytics/
  index.ts          # public barrel
  types.ts          # shared contracts
  layout.tsx        # page shell, header, toolbar, footer
  filters.tsx       # filter bar + dimension filters
  controls.tsx      # metric / view / refresh / export / last updated
  sections.tsx      # KPI + content section shells + insight panels
  charts.tsx        # Recharts wrappers
  export.ts         # exporter interface + unsupported stub

frontend/src/hooks/
  use-analytics-filters.ts
  use-analytics-refresh.ts
  use-analytics-export.ts
  use-analytics-selection.ts
```

Import from `@/components/analytics` and `@/hooks`.

## Reuse strategy

1. **Design system first** — Prefer `MetricCard`, `InsightCard`, `RecommendationCard`, `DataTable`, `PageHeader`, `SectionHeader`, form controls, and chart primitives. Analytics components wrap them; they do not fork them.
2. **Feature pages own data** — A Sales (or other) page fetches via its own service/hooks, maps responses into framework props (`items`, `data`, `columns`), and never embeds API clients inside `components/analytics`.
3. **Composition over configuration** — Layout slots (`header`, `toolbar`, `filters`, `children`, `footer`) accept React nodes so modules can omit unused filters/sections without forking the layout.
4. **No domain duplication** — Shared filter keys (`regionIds`, `categoryIds`, …) stay generic. Domain-specific option lists are passed in as `AnalyticsOption[]`.

## Filter architecture

Filters are controlled components. State lives in `useAnalyticsFilters({ scope })`:

| Filter | State field | URL param |
|--------|-------------|-----------|
| Date range | `dateRange.start` / `end` | `from`, `to` |
| Region | `regionIds` | `region` (comma-separated) |
| Category | `categoryIds` | `category` |
| Customer | `customerIds` | `customer` |
| Product | `productIds` | `product` |
| Search | `search` | `q` |

- **`scope`** isolates persistence per module (e.g. `"sales"`, `"finance"`).
- **URL sync** (`syncUrl`, default `true`) keeps shareable deep links.
- **Persistence** (`persist`, default `true`) stores last filters in `localStorage` under `edp-analytics-filters`.
- **`ResetFiltersButton`** calls `resetFilters()` to restore defaults and clear the scoped persist entry.

`AnalyticsFilterBar` is a responsive grid shell (`md: 2` / `xl: 3` columns) with an optional actions row for reset / apply controls.

## Controls

| Control | Purpose |
|---------|---------|
| `MetricSelector` | Primary metric id(s) for charts/tables |
| `ViewToggle` | `chart` \| `table` \| `split` |
| `RefreshButton` | Triggers feature refresh; supports `loading` |
| `ExportToolbar` | Format menu → `onExport(format)` |
| `LastUpdatedIndicator` | Polite live region for freshness |

Wire these into `AnalyticsToolbar` `leading` / `trailing` slots.

## State flow

```
URL query  ←→  useAnalyticsFilters / useAnalyticsSelection  ←→  localStorage (scoped)
                      ↓
              controlled filter/control UI
                      ↓
              feature data hooks (React Query, etc.)
                      ↓
              Analytics*Section / chart wrappers
```

| Hook | Responsibility |
|------|----------------|
| `useAnalyticsFilters` | Filter state, URL sync, persistence, `resetFilters` |
| `useAnalyticsSelection` | Metrics, view mode, row/series highlight; URL `view` + `metrics`; persist `edp-analytics-selection` |
| `useAnalyticsRefresh` | `isRefreshing`, `lastUpdated`, `refresh()` |
| `useAnalyticsExport` | Calls `AnalyticsExporter`; default is unsupported stub |

Export formats are declared in types and the exporter interface. **No CSV/Excel/PDF/PNG implementation yet** — `UnsupportedAnalyticsExporter` returns `status: "unsupported"`. Feature teams inject a real exporter later without changing `ExportToolbar`.

## Accessibility

- Toolbar uses `role="toolbar"`; view toggle uses `role="group"` + `aria-pressed`.
- Filters associate labels with controls; chip remove buttons expose `aria-label`.
- Sections expose `aria-label` from their titles; charts use `ChartContainer` labels.
- Refresh uses `aria-busy`; last updated uses `aria-live="polite"`.
- Layout stacks on small screens (`flex-col` → `sm:flex-row`); filter grid is responsive.

Keyboard: native buttons/selects/menu items from the design system remain focusable; do not replace them with non-interactive divs in feature pages.

## How future analytics pages should use this

Minimal pattern (no business APIs shown):

```tsx
"use client";

import {
  AnalyticsPageLayout,
  AnalyticsHeader,
  AnalyticsToolbar,
  AnalyticsFilterBar,
  AnalyticsFooter,
  DateRangeFilter,
  RegionFilter,
  ResetFiltersButton,
  MetricSelector,
  ViewToggle,
  RefreshButton,
  ExportToolbar,
  LastUpdatedIndicator,
  AnalyticsKPIGrid,
  AnalyticsTrendSection,
  AnalyticsLineChart,
} from "@/components/analytics";
import {
  useAnalyticsFilters,
  useAnalyticsSelection,
  useAnalyticsRefresh,
  useAnalyticsExport,
} from "@/hooks";

export function ExampleAnalyticsPage() {
  const { filters, patchFilters, resetFilters } = useAnalyticsFilters({ scope: "example" });
  const { selection, setViewMode, setMetricIds } = useAnalyticsSelection({ scope: "example" });
  const { isRefreshing, lastUpdated, refresh } = useAnalyticsRefresh({
    onRefresh: async () => {
      /* feature: invalidate queries */
    },
  });
  const { exportFormat, isExporting } = useAnalyticsExport();

  return (
    <AnalyticsPageLayout
      header={
        <AnalyticsHeader
          title="Example Analytics"
          description="Compose the framework; wire your own data."
        />
      }
      toolbar={
        <AnalyticsToolbar
          leading={
            <>
              <MetricSelector
                metrics={[{ id: "revenue", label: "Revenue" }]}
                value={selection.selectedMetricIds}
                onChange={setMetricIds}
              />
              <ViewToggle value={selection.viewMode} onChange={setViewMode} />
            </>
          }
          trailing={
            <>
              <LastUpdatedIndicator value={lastUpdated} />
              <RefreshButton onRefresh={refresh} loading={isRefreshing} />
              <ExportToolbar
                disabled={isExporting}
                onExport={(format) => exportFormat(format)}
              />
            </>
          }
        />
      }
      filters={
        <AnalyticsFilterBar
          actions={<ResetFiltersButton onReset={resetFilters} />}
        >
          <DateRangeFilter
            value={filters.dateRange}
            onChange={(dateRange) => patchFilters({ dateRange })}
          />
          <RegionFilter
            options={[]} /* feature supplies options */
            value={filters.regionIds}
            onChange={(regionIds) => patchFilters({ regionIds })}
          />
        </AnalyticsFilterBar>
      }
      footer={<AnalyticsFooter />}
    >
      <AnalyticsKPIGrid items={[]} />
      <AnalyticsTrendSection title="Trend">
        <AnalyticsLineChart title="Trend" data={[]} xKey="period" series={[]} />
      </AnalyticsTrendSection>
    </AnalyticsPageLayout>
  );
}
```

### Checklist for a new analytics module

1. Create a feature folder (`features/<domain>/`), not new primitives under `components/analytics`, unless a gap is truly shared.
2. Use `AnalyticsPageLayout` and only the sections/charts needed.
3. Scope hooks with a stable string (`"sales"`, `"customers"`, …).
4. Map API DTOs → framework props in the feature layer.
5. Pass option lists into filters; do not hardcode domain enums in the framework.
6. Inject a real `AnalyticsExporter` when export adapters exist.
7. Keep Executive Dashboard and other vertical slices free of duplicated layout/filter code — migrate them to this framework when convenient.

## Out of scope (by design)

- Sales / Customer / Finance / Operations / AI page implementations
- Business or analytics HTTP clients inside this package
- Concrete CSV / Excel / PDF / PNG exporters
- Heatmap rendering (placeholder only)
- Duplicating Executive Dashboard behavior

## Related docs

- `docs/06_Design_System.md` — base UI primitives
- `docs/07_Application_Shell.md` — app chrome / routing
- `docs/10_Executive_Dashboard.md` — first vertical slice (consumes services; may adopt this framework later)
