# Frontend — Enterprise Decision Platform

Next.js 15 (App Router) + React 19 + TypeScript scaffold.

## Folder responsibilities

| Folder | Responsibility |
|--------|----------------|
| `src/app/` | App Router routes, layouts, and route handlers |
| `src/components/ui/` | Primitive shadcn/ui components |
| `src/components/charts/` | Shared Recharts wrappers (no domain logic) |
| `src/components/dashboard/` | Shared dashboard shell pieces |
| `src/components/tables/` | Data-table primitives |
| `src/components/layout/` | App chrome and providers |
| `src/components/forms/` | Shared form controls (RHF + Zod) |
| `src/components/feedback/` | Loading / empty / placeholder states |
| `src/features/*/` | Domain feature modules (compose UI + hooks + services) |
| `src/hooks/` | Cross-cutting React hooks |
| `src/lib/` | Pure utilities (`cn`, helpers) |
| `src/services/` | API transport clients |
| `src/store/` | Zustand global stores |
| `src/types/` | Shared TypeScript contracts |
| `src/styles/` | Extra tokens / shared CSS |
| `src/config/` | Env-backed public configuration |
| `public/` | Static assets |

## Scripts

```bash
npm run dev      # http://localhost:3000
npm run lint
npm run build
npm run start
npm run format
```

## Design system

Reusable UI lives under `src/components/` (`ui`, `layout`, `navigation`, `feedback`, `cards`, `tables`, `charts`, `forms`).

Tokens: `src/styles/tokens.ts`, `src/styles/tokens.css`, `src/app/globals.css`.

See `../docs/06_Design_System.md` for hierarchy, naming, and usage guidelines.

Copy `.env.local.example` → `.env.local` before running.
