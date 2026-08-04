# Application Shell — Enterprise Decision Platform

Premium enterprise SaaS chrome for the Decision Intelligence Platform.  
**Framework only** — no analytics pages, KPI mock data, or API calls.

---

## Architecture

```text
RootLayout (providers, fonts, skip link)
└── (app)/layout → ApplicationShell
    ├── AppSidebar (desktop, collapsible)
    ├── AppTopNav (breadcrumbs, search, notifications, theme, user, workspace, date)
    ├── ContentContainer → page placeholders
    ├── MobileNavDrawer (overlay + slide-in)
    ├── CommandPalette (Ctrl/Cmd+K)
    └── GlobalSearch (/)
```

| Layer | Responsibility |
|-------|----------------|
| `components/shell/*` | Orchestrated shell features |
| `components/layout/*` | Presentational chrome primitives |
| `components/navigation/*` | Nav atoms (theme, user menu) |
| `config/navigation.ts` | Nav IA, workspaces, breadcrumbs |
| `store/*` | Persisted shell state (Zustand) |

**Dependency rule:** pages stay thin placeholders; shell owns navigation UX.

---

## Component hierarchy

```text
ApplicationShell
├── AppShell
│   ├── AppSidebar
│   │   └── ShellNavItem (icon, active, badge, nested, collapsed tooltips)
│   ├── AppTopNav
│   │   ├── Breadcrumbs
│   │   ├── WorkspaceSelector
│   │   ├── Current date
│   │   ├── GlobalSearchTrigger
│   │   ├── NotificationCenter
│   │   ├── ThemeToggle
│   │   └── UserMenu
│   └── main#main-content → children
├── MobileNavDrawer
├── CommandPalette
└── GlobalSearch
```

---

## Navigation

### Sections

**MAIN** — Dashboard, Sales / Customer / Finance / Operations Intelligence, Analytics, AI Predictions, Business Recommendations, Reports  

**SYSTEM** — Settings (nested General / Help center), Help, About, Support

### Behaviors

| Feature | Behavior |
|---------|----------|
| Active state | Path match (`pathname === href` or nested prefix) |
| Collapsed | Icon rail + tooltips; width `4.5rem` |
| Expanded | Labels, badges, nested chevrons |
| Nested items | Animated expand/collapse; keyboard-focusable controls |
| Mobile | Hamburger → drawer + dimmed overlay; closes on navigate |
| Brand | Links to `/dashboard` |

Routing uses the Next.js App Router group `(app)` so every placeholder page inherits the shell automatically. `api/health` stays outside the shell.

---

## State (Zustand + persist)

| Store | Key | Persisted fields |
|-------|-----|------------------|
| `useShellStore` | `edp-shell` | `sidebarCollapsed`, `workspaceId` |
| `useSearchStore` | `edp-search` | `recentSearches` |
| `useNotificationStore` | `edp-notifications` | `notifications` (empty by default) |
| `useThemePreferenceStore` | `edp-theme` | `preference` (`light` \| `dark` \| `system`) |
| `next-themes` | `edp-next-theme` | Applied theme class |

Transient (not persisted): `mobileNavOpen`, `commandPaletteOpen`, `globalSearchOpen`.

Notifications start **empty** (empty state UI). The store exposes `addNotification` for future system events — do not seed fake business alerts.

---

## Global search

- Opens via **/** (when not typing in an input) or the search trigger
- Recent searches (persisted) + suggested pages from nav config
- Arrow keys + Enter to navigate results
- **No backend** — filters local page catalog only

---

## Command palette

- **Ctrl+K** / **Cmd+K**
- Groups: Pages, Actions, Reports & settings
- Placeholder group for future customers/products search
- Actions: open search, toggle sidebar, theme modes, jump to settings/reports
- Focus trapped by Radix Dialog; Esc closes

---

## Notifications

Dropdown with:

- Unread indicator / count badge
- Tones: success, warning, error, info
- Mark read, mark all read, dismiss, clear all
- Empty state when the list is empty

---

## Accessibility

- Skip link to `#main-content`
- Sidebar `aria-label`, `aria-current="page"`, expand `aria-expanded` / `aria-controls`
- Icon buttons labeled (`aria-label`)
- Mobile drawer `role="dialog"` + `aria-modal`
- Command palette / search dialog titles for screen readers
- Focus rings via design-system `:focus-visible`
- Radix focus trap on dialogs and dropdowns

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Toggle command palette |
| `/` | Open global search (when focus is not in a field) |
| `Esc` | Close mobile drawer / dialogs |
| `↑` / `↓` + `Enter` | Move through search results |
| Tab | Standard focus order through chrome |

---

## Responsive behavior

| Viewport | Shell behavior |
|----------|----------------|
| Desktop (`md+`) | Persistent collapsible sidebar |
| Tablet | Same breakpoint; collapse sidebar for space |
| Mobile | Sidebar hidden; menu opens overlay drawer with Framer Motion slide |

Animations are intentionally light: sidebar width transition, drawer slide/fade, nested nav height, notification list enter/exit, command/search dialog presence.

---

## Out of scope

- Dashboard / analytics implementations
- API fetching
- Fake KPI cards or business notification copy
- Auth (user menu is shell chrome with placeholder identity)

Next phases compose feature modules inside `main` without rewriting the shell.
