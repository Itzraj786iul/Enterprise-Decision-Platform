# Design System — Enterprise Decision Platform

Reusable UI foundation for the Decision Intelligence Platform.  
**This document covers components only** — no dashboard pages, analytics, or API wiring.

---

## Design principles

1. **Presentational first** — components accept formatted values and callbacks; they do not fetch data.
2. **Composition over pages** — features assemble layout + cards + tables; routes stay thin.
3. **Executive clarity** — navy primary, teal accent, cool neutrals; avoid decorative noise.
4. **Accessible by default** — labels, focus rings, ARIA, keyboard paths, skip link.
5. **Themeable** — light / dark via CSS variables + `next-themes`.

---

## Component hierarchy

```text
components/
├── ui/            Primitives (Button, Input, Dialog, Select, …)
├── layout/        App chrome (AppShell, Sidebar, PageHeader, …)
├── navigation/    Nav interactions (SidebarItem, UserMenu, ThemeToggle)
├── feedback/      System status (Spinner, Empty, Error, Toast)
├── cards/         KPI & insight surfaces (MetricCard, AlertCard, …)
├── tables/        Enterprise data grids (DataTable, LoadingTable)
├── charts/        Chart chrome only (ChartCard, Legend, Toolbar)
└── forms/         Filter & input composites (SearchBar, DateRangePicker)
```

**Dependency direction (never reverse):**

```text
features → layout/cards/tables/charts/forms/navigation/feedback → ui → tokens
```

---

## Naming conventions

| Pattern | Example | Rule |
|---------|---------|------|
| PascalCase files matching export | `metric-card.tsx` → `MetricCard` | One primary export per file when possible |
| Folder = responsibility | `cards/`, `tables/` | Do not put domain KPIs inside `ui/` |
| `…Card` | `InsightCard` | Bounded content surface |
| `…Field` | `TextField` | Labeled form control |
| `…State` | `EmptyState` | Full replacement for missing content |
| Aliases | `StatCard` ≈ `MetricCard` | Allowed for semantic clarity |

Avoid:

- Domain names in the design system (`SalesRevenueCard`)
- Fetching or hard-coded fake metrics inside shared components
- One-off page layouts living under `ui/`

---

## Design tokens

Source files:

- `src/styles/tokens.ts` — spacing, radius, motion, layout constants
- `src/styles/tokens.css` — animation utilities, container/grid helpers
- `src/app/globals.css` — color system + Tailwind `@theme` bridge

### Typography

| Token | Use |
|-------|-----|
| `font-sans` | Body, UI |
| `font-display` | Page titles |
| `font-mono` | IDs, codes, tabular debug |

Scale: `xs` → `4xl`. Prefer `text-sm` / `text-base` for dense enterprise UI; reserve `text-2xl+` for page headers and KPI values.

### Spacing / radius / shadow

Use the Tailwind spacing scale backed by token CSS variables.  
Radius: `--radius` (md default). Shadows: `--shadow-xs|sm|md|lg|focus`.

### Motion

| Duration | When |
|----------|------|
| 120ms | Hover / press |
| 200ms | Fade / tooltip |
| 280–320ms | Panel enter |
| Framer Motion | Toasts, intentional presence |

Respect reduced motion in future iterations; keep animations subtle.

### Layout

| Token | Value |
|-------|-------|
| Sidebar | `16rem` / collapsed `4.5rem` |
| Top navbar | `3.5rem` |
| Content max | `90rem` |
| Grid | 12 columns, `1.5rem` gutter |
| Breakpoints | sm 640 · md 768 · lg 1024 · xl 1280 · 2xl 1536 |

---

## Color system

Semantic CSS variables (light + `.dark`):

| Role | Light intent |
|------|----------------|
| **Primary** | Deep navy `#0B2A4A` — actions, focus |
| **Secondary** | Steel navy — secondary chrome |
| **Accent** | Teal `#0F766E` — highlights |
| **Success / Warning / Danger / Info** | Status only |
| **Neutral** | `--muted`, `--border`, `--foreground` |
| **Sidebar** | Dark navy rail (both themes) |

Charts use `--chart-1` … `--chart-5` — palette only; no sample series in the design system.

---

## When to use each component

### Layout

| Component | Use when |
|-----------|----------|
| `AppShell` | Authenticated app chrome (sidebar + navbar + main) |
| `Sidebar` | Primary navigation rail content |
| `TopNavbar` | Global actions, search, user menu |
| `Breadcrumbs` | Hierarchy deeper than one level |
| `PageHeader` | Start of every feature page |
| `SectionHeader` | Sub-regions within a page |
| `ContentContainer` | Consistent horizontal padding / max width |

### Cards (KPI standards)

| Component | Use when |
|-----------|----------|
| `MetricCard` / `StatCard` | Single KPI: title, value, delta, trend, icon, sparkline slot, loading |
| `TrendCard` | KPI with explicit period label |
| `InsightCard` | Narrative insight with tone badge |
| `RecommendationCard` | Actionable recommendation + priority |
| `AlertCard` | Operational alert needing attention |

**KPI contract:** pass already-formatted `value` / `delta` strings. Loading uses skeletons — never empty numbers.

### Tables

| Component | Use when |
|-----------|----------|
| `DataTable` / `SortableTable` | Enterprise grids needing sort, filter, pagination, sticky header, column visibility, export slot |
| `LoadingTable` | Skeleton-only table placeholder |
| `EmptyState` (table) | Zero rows after load |

### Charts

| Component | Use when |
|-----------|----------|
| `ChartContainer` | Accessible `role="img"` wrapper around Recharts |
| `ChartCard` | Titled chart surface |
| `ChartLegend` / `ChartTooltip` / `ChartToolbar` | Shared chrome — not data |

### Navigation

| Component | Use when |
|-----------|----------|
| `SidebarItem` / `SidebarGroup` | Primary nav links |
| `UserMenu` / `ProfileMenu` | Account actions |
| `ThemeToggle` | Light / dark switch |

### Forms

| Component | Use when |
|-----------|----------|
| `SearchBar` | Global or panel search |
| `FilterPanel` | Side/stacked filter groups |
| `DateRangePicker` | Inclusive start/end dates |
| `SelectField` / `TextField` | Labeled controls with helper/error text |

### Feedback

| Component | Use when |
|-----------|----------|
| `LoadingSpinner` | Inline async wait |
| `Skeleton` | Content-shaped loading |
| `EmptyState` / `NoData` | Legitimate empty results |
| `ErrorState` | Recoverable failure + retry |
| `SuccessBanner` | Persistent success message |
| `ToastProvider` / `useToast` | Transient notifications |

### UI primitives

Use `Button`, `Badge`, `Dialog`, `Select`, `DropdownMenu`, etc. for low-level building blocks. Prefer composites (`TextField`) in features over raw `Input` + `Label` pairs.

---

## Accessibility checklist

- Skip link to `#main-content` in root layout
- Visible `:focus-visible` rings on interactive controls
- Icon-only buttons always have `aria-label`
- Tables use `<th scope="col">`; sort controls announce purpose
- Toasts use `aria-live="polite"`
- Contrast: navy/teal on light surfaces; elevated primary on dark
- Dialogs / menus / selects rely on Radix focus traps & Escape

---

## Responsive behavior

| Viewport | Expectations |
|----------|----------------|
| **Desktop (≥1024)** | Persistent sidebar, multi-column KPI grids |
| **Tablet** | Collapsible / hidden sidebar; stack headers |
| **Mobile** | Navbar menu trigger; single-column cards; horizontal table scroll |

`AppShell` hides the sidebar below `md`; use `TopNavbar` `onMenuClick` for a mobile drawer in a later feature (not included here).

---

## Usage example (composition only)

```tsx
import { PageHeader, ContentContainer } from "@/components/layout";
import { MetricCard } from "@/components/cards";
import { DataTable } from "@/components/tables";

export function ExampleScaffold() {
  return (
    <ContentContainer>
      <PageHeader title="Example" description="Design-system composition only." />
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Metric" value="—" loading />
      </div>
      <div className="mt-8">
        <DataTable columns={[]} data={[]} rowKey={() => "id"} loading />
      </div>
    </ContentContainer>
  );
}
```

Do **not** wire this into dashboard routes until the dashboard implementation phase.

---

## Out of scope

- Dashboard / analytics pages
- API fetching or React Query domain hooks
- Fake KPI datasets or chart series
- Auth flows

Next phases compose these primitives into real product surfaces.
