/**
 * Export interfaces for analytics modules.
 * Implementations (CSV/Excel/PDF/PNG) are intentionally deferred.
 */

import type {
  AnalyticsExportFormat,
  AnalyticsExportRequest,
  AnalyticsExportResult,
} from "@/components/analytics/types";

export type AnalyticsExporter = {
  readonly formats: readonly AnalyticsExportFormat[];
  export: (request: AnalyticsExportRequest) => Promise<AnalyticsExportResult>;
  supports: (format: AnalyticsExportFormat) => boolean;
};

/**
 * No-op exporter used until real adapters are wired.
 * Feature pages can inject a concrete exporter later without changing UI controls.
 */
export class UnsupportedAnalyticsExporter implements AnalyticsExporter {
  readonly formats = ["csv", "excel", "pdf", "png"] as const;

  supports(format: AnalyticsExportFormat): boolean {
    return (this.formats as readonly string[]).includes(format);
  }

  async export(request: AnalyticsExportRequest): Promise<AnalyticsExportResult> {
    return {
      format: request.format,
      status: "unsupported",
      message: `${request.format.toUpperCase()} export is not implemented yet.`,
    };
  }
}

export function createAnalyticsExporter(): AnalyticsExporter {
  return new UnsupportedAnalyticsExporter();
}
