"use client";

import * as React from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import {
  DEFAULT_ANALYTICS_SELECTION,
  type AnalyticsSelectionState,
  type AnalyticsViewMode,
} from "@/components/analytics/types";

type PersistedSelectionState = {
  byScope: Record<string, AnalyticsSelectionState>;
  setScopeSelection: (scope: string, selection: AnalyticsSelectionState) => void;
};

const usePersistedAnalyticsSelection = create<PersistedSelectionState>()(
  persist(
    (set) => ({
      byScope: {},
      setScopeSelection: (scope, selection) =>
        set((state) => ({
          byScope: { ...state.byScope, [scope]: selection },
        })),
    }),
    {
      name: "edp-analytics-selection",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

function parseViewMode(value: string | null, fallback: AnalyticsViewMode): AnalyticsViewMode {
  return value === "table" || value === "chart" || value === "split" ? value : fallback;
}

type UseAnalyticsSelectionOptions = {
  scope: string;
  defaults?: Partial<AnalyticsSelectionState>;
  syncUrl?: boolean;
  persist?: boolean;
};

export function useAnalyticsSelection({
  scope,
  defaults,
  syncUrl = true,
  persist: enablePersist = true,
}: UseAnalyticsSelectionOptions) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const persisted = usePersistedAnalyticsSelection((s) => s.byScope[scope]);
  const setScopeSelection = usePersistedAnalyticsSelection((s) => s.setScopeSelection);

  const initial = React.useMemo<AnalyticsSelectionState>(() => {
    const base = { ...DEFAULT_ANALYTICS_SELECTION, ...defaults };
    if (enablePersist && persisted) return { ...base, ...persisted };
    return base;
  }, [defaults, enablePersist, persisted]);

  const [selection, setSelectionState] = React.useState<AnalyticsSelectionState>(() => {
    if (!syncUrl) return initial;
    const params = new URLSearchParams(searchParams.toString());
    const metrics = params.get("metrics");
    return {
      ...initial,
      viewMode: parseViewMode(params.get("view"), initial.viewMode),
      selectedMetricIds: metrics
        ? metrics.split(",").filter(Boolean)
        : initial.selectedMetricIds,
    };
  });

  React.useEffect(() => {
    if (!syncUrl) return;
    const params = new URLSearchParams(searchParams.toString());
    const metrics = params.get("metrics");
    setSelectionState((prev) => ({
      ...prev,
      viewMode: parseViewMode(params.get("view"), prev.viewMode),
      selectedMetricIds: metrics
        ? metrics.split(",").filter(Boolean)
        : prev.selectedMetricIds,
    }));
  }, [searchParams, syncUrl]);

  const setSelection = React.useCallback(
    (
      next:
        | AnalyticsSelectionState
        | ((prev: AnalyticsSelectionState) => AnalyticsSelectionState),
    ) => {
      setSelectionState((prev) => {
        const resolved = typeof next === "function" ? next(prev) : next;
        if (enablePersist) setScopeSelection(scope, resolved);
        if (syncUrl) {
          const params = new URLSearchParams(searchParams.toString());
          params.set("view", resolved.viewMode);
          if (resolved.selectedMetricIds.length) {
            params.set("metrics", resolved.selectedMetricIds.join(","));
          } else {
            params.delete("metrics");
          }
          const query = params.toString();
          router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
        }
        return resolved;
      });
    },
    [enablePersist, pathname, router, scope, searchParams, setScopeSelection, syncUrl],
  );

  const patchSelection = React.useCallback(
    (patch: Partial<AnalyticsSelectionState>) => {
      setSelection((prev) => ({ ...prev, ...patch }));
    },
    [setSelection],
  );

  const setViewMode = React.useCallback(
    (viewMode: AnalyticsViewMode) => patchSelection({ viewMode }),
    [patchSelection],
  );

  const setMetricIds = React.useCallback(
    (selectedMetricIds: string[]) => patchSelection({ selectedMetricIds }),
    [patchSelection],
  );

  return {
    selection,
    setSelection,
    patchSelection,
    setViewMode,
    setMetricIds,
  };
}
