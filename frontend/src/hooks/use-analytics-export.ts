"use client";

import * as React from "react";
import {
  createAnalyticsExporter,
  type AnalyticsExporter,
} from "@/components/analytics/export";
import type {
  AnalyticsExportFormat,
  AnalyticsExportRequest,
  AnalyticsExportResult,
} from "@/components/analytics/types";

type UseAnalyticsExportOptions = {
  exporter?: AnalyticsExporter;
  onResult?: (result: AnalyticsExportResult) => void;
};

/**
 * Export orchestration hook. Uses unsupported exporter by default.
 */
export function useAnalyticsExport({
  exporter = createAnalyticsExporter(),
  onResult,
}: UseAnalyticsExportOptions = {}) {
  const [isExporting, setIsExporting] = React.useState(false);
  const [lastResult, setLastResult] = React.useState<AnalyticsExportResult | null>(null);

  const exportData = React.useCallback(
    async (request: AnalyticsExportRequest) => {
      setIsExporting(true);
      try {
        const result = await exporter.export(request);
        setLastResult(result);
        onResult?.(result);
        return result;
      } finally {
        setIsExporting(false);
      }
    },
    [exporter, onResult],
  );

  const exportFormat = React.useCallback(
    (format: AnalyticsExportFormat, payload?: unknown, filename?: string) =>
      exportData({ format, payload, filename }),
    [exportData],
  );

  return {
    isExporting,
    lastResult,
    exportData,
    exportFormat,
    supports: exporter.supports.bind(exporter),
    formats: exporter.formats,
  };
}
