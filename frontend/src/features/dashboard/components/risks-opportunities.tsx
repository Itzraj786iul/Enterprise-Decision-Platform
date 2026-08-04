"use client";

import { AlertCard, InsightCard, RecommendationCard } from "@/components/cards";
import { ErrorState, EmptyState } from "@/components/feedback/empty-state";
import { LoadingSpinner } from "@/components/feedback/loading-spinner";
import { SectionHeader } from "@/components/layout/section-header";
import type { OpportunityItem, RiskItem } from "@/services/dashboard";

type RisksProps = {
  items?: RiskItem[];
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
};

export function BusinessRisksPanel({ items = [], loading, error, onRetry }: RisksProps) {
  return (
    <section aria-label="Business risks" className="space-y-4">
      <SectionHeader title="Business Risks" description="Priority risks from DQ and ML signals" />
      {error ? (
        <ErrorState title="Unable to load risks" description={error.message} onRetry={onRetry} />
      ) : loading && items.length === 0 ? (
        <div className="flex justify-center py-10">
          <LoadingSpinner label="Loading risks" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          title="No material risks"
          description="No high-priority DQ or ML risk signals are currently available."
        />
      ) : (
        <div className="grid gap-3">
          {items.map((item) => (
            <AlertCard
              key={item.id}
              title={item.title}
              description={[item.description, item.impact ? `Impact: ${item.impact}` : null, item.owner ? `Owner: ${item.owner}` : null]
                .filter(Boolean)
                .join(" · ")}
              severity={
                item.priority === "critical" || item.priority === "high"
                  ? "danger"
                  : item.priority === "medium"
                    ? "warning"
                    : "info"
              }
            />
          ))}
        </div>
      )}
    </section>
  );
}

type OppProps = {
  items?: OpportunityItem[];
  loading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
};

export function BusinessOpportunitiesPanel({ items = [], loading, error, onRetry }: OppProps) {
  return (
    <section aria-label="Business opportunities" className="space-y-4">
      <SectionHeader
        title="Business Opportunities"
        description="Growth signals from prediction outputs and scorecard trajectory"
      />
      {error ? (
        <ErrorState
          title="Unable to load opportunities"
          description={error.message}
          onRetry={onRetry}
        />
      ) : loading && items.length === 0 ? (
        <div className="flex justify-center py-10">
          <LoadingSpinner label="Loading opportunities" />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          title="No opportunities surfaced"
          description="No opportunity-classified prediction rows were returned."
        />
      ) : (
        <div className="grid gap-3">
          {items.map((item) => (
            <RecommendationCard
              key={item.id}
              title={item.title}
              summary={[item.description, item.estimated_impact ? `Est. impact: ${item.estimated_impact}` : null]
                .filter(Boolean)
                .join(" · ")}
              priority={item.priority}
            />
          ))}
        </div>
      )}
    </section>
  );
}

type DqProps = {
  dqMetricLabel?: string;
  dqValue?: string | null;
  loading?: boolean;
  available?: boolean;
};

export function DqSummaryPanel({ dqMetricLabel, dqValue, loading, available }: DqProps) {
  return (
    <section aria-label="Data quality summary">
      <SectionHeader title="DQ Summary" description="Platform data quality posture" />
      {loading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner label="Loading data quality" />
        </div>
      ) : (
        <InsightCard
          title={dqMetricLabel ?? "Data Quality Score"}
          body={
            available && dqValue
              ? `Current DQ score is ${dqValue}, sourced from the analytics data quality summary view.`
              : "DQ score is unavailable. Publish analytics.vw_data_quality_summary to enable this signal."
          }
          tone={available ? "info" : "warning"}
        />
      )}
    </section>
  );
}
