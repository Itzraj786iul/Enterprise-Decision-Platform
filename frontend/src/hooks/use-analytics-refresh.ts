"use client";

import * as React from "react";

type UseAnalyticsRefreshOptions = {
  onRefresh?: () => void | Promise<void>;
};

/**
 * Shared refresh control state for analytics toolbars.
 */
export function useAnalyticsRefresh({ onRefresh }: UseAnalyticsRefreshOptions = {}) {
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [lastUpdated, setLastUpdated] = React.useState<Date | null>(null);

  const refresh = React.useCallback(async () => {
    setIsRefreshing(true);
    try {
      await onRefresh?.();
      setLastUpdated(new Date());
    } finally {
      setIsRefreshing(false);
    }
  }, [onRefresh]);

  const markUpdated = React.useCallback(() => {
    setLastUpdated(new Date());
  }, []);

  return {
    isRefreshing,
    lastUpdated,
    refresh,
    markUpdated,
  };
}
