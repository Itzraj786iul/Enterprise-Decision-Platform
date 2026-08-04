"use client";

import * as React from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import {
  DEFAULT_ANALYTICS_FILTERS,
  type AnalyticsFiltersState,
} from "@/components/analytics/types";

type PersistedFiltersState = {
  byScope: Record<string, AnalyticsFiltersState>;
  setScopeFilters: (scope: string, filters: AnalyticsFiltersState) => void;
  resetScopeFilters: (scope: string) => void;
};

const usePersistedAnalyticsFilters = create<PersistedFiltersState>()(
  persist(
    (set) => ({
      byScope: {},
      setScopeFilters: (scope, filters) =>
        set((state) => ({
          byScope: { ...state.byScope, [scope]: filters },
        })),
      resetScopeFilters: (scope) =>
        set((state) => {
          const next = { ...state.byScope };
          delete next[scope];
          return { byScope: next };
        }),
    }),
    {
      name: "edp-analytics-filters",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

function parseList(value: string | null): string[] {
  if (!value) return [];
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function serializeList(values: string[]): string | null {
  return values.length ? values.join(",") : null;
}

function filtersFromSearchParams(params: URLSearchParams): Partial<AnalyticsFiltersState> {
  return {
    dateRange: {
      start: params.get("from") ?? "",
      end: params.get("to") ?? "",
    },
    regionIds: parseList(params.get("region")),
    categoryIds: parseList(params.get("category")),
    customerIds: parseList(params.get("customer")),
    productIds: parseList(params.get("product")),
    search: params.get("q") ?? "",
  };
}

function writeFiltersToParams(filters: AnalyticsFiltersState, params: URLSearchParams) {
  const setOrDelete = (key: string, value: string | null) => {
    if (!value) params.delete(key);
    else params.set(key, value);
  };
  setOrDelete("from", filters.dateRange.start || null);
  setOrDelete("to", filters.dateRange.end || null);
  setOrDelete("region", serializeList(filters.regionIds));
  setOrDelete("category", serializeList(filters.categoryIds));
  setOrDelete("customer", serializeList(filters.customerIds));
  setOrDelete("product", serializeList(filters.productIds));
  setOrDelete("q", filters.search.trim() || null);
}

type UseAnalyticsFiltersOptions = {
  /** Persistence + URL scope key, e.g. "sales" | "customers". */
  scope: string;
  defaults?: Partial<AnalyticsFiltersState>;
  syncUrl?: boolean;
  persist?: boolean;
};

export function useAnalyticsFilters({
  scope,
  defaults,
  syncUrl = true,
  persist: enablePersist = true,
}: UseAnalyticsFiltersOptions) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const persisted = usePersistedAnalyticsFilters((s) => s.byScope[scope]);
  const setScopeFilters = usePersistedAnalyticsFilters((s) => s.setScopeFilters);
  const resetScopeFilters = usePersistedAnalyticsFilters((s) => s.resetScopeFilters);

  const initial = React.useMemo<AnalyticsFiltersState>(() => {
    const base = {
      ...DEFAULT_ANALYTICS_FILTERS,
      ...defaults,
      dateRange: {
        ...DEFAULT_ANALYTICS_FILTERS.dateRange,
        ...defaults?.dateRange,
      },
    };
    if (enablePersist && persisted) {
      return { ...base, ...persisted, dateRange: { ...base.dateRange, ...persisted.dateRange } };
    }
    return base;
  }, [defaults, enablePersist, persisted]);

  const [filters, setFiltersState] = React.useState<AnalyticsFiltersState>(() => {
    if (syncUrl) {
      return { ...initial, ...filtersFromSearchParams(new URLSearchParams(searchParams.toString())) };
    }
    return initial;
  });

  // Hydrate from URL when it changes externally (back/forward)
  React.useEffect(() => {
    if (!syncUrl) return;
    setFiltersState((prev) => ({
      ...prev,
      ...filtersFromSearchParams(new URLSearchParams(searchParams.toString())),
    }));
  }, [searchParams, syncUrl]);

  const setFilters = React.useCallback(
    (next: AnalyticsFiltersState | ((prev: AnalyticsFiltersState) => AnalyticsFiltersState)) => {
      setFiltersState((prev) => {
        const resolved = typeof next === "function" ? next(prev) : next;
        if (enablePersist) setScopeFilters(scope, resolved);
        if (syncUrl) {
          const params = new URLSearchParams(searchParams.toString());
          writeFiltersToParams(resolved, params);
          const query = params.toString();
          router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
        }
        return resolved;
      });
    },
    [enablePersist, pathname, router, scope, searchParams, setScopeFilters, syncUrl],
  );

  const patchFilters = React.useCallback(
    (patch: Partial<AnalyticsFiltersState>) => {
      setFilters((prev) => ({
        ...prev,
        ...patch,
        dateRange: { ...prev.dateRange, ...patch.dateRange },
      }));
    },
    [setFilters],
  );

  const resetFilters = React.useCallback(() => {
    const next = {
      ...DEFAULT_ANALYTICS_FILTERS,
      ...defaults,
      dateRange: {
        ...DEFAULT_ANALYTICS_FILTERS.dateRange,
        ...defaults?.dateRange,
      },
    };
    if (enablePersist) resetScopeFilters(scope);
    setFilters(next);
  }, [defaults, enablePersist, resetScopeFilters, scope, setFilters]);

  return {
    filters,
    setFilters,
    patchFilters,
    resetFilters,
  };
}
