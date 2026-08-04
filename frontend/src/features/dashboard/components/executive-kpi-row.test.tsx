import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ExecutiveKpiRow } from "@/features/dashboard/components/executive-kpi-row";

describe("ExecutiveKpiRow", () => {
  it("renders unavailable metrics without inventing values", () => {
    render(
      <ExecutiveKpiRow
        metrics={[
          {
            id: "dq_score",
            label: "DQ Score",
            value: null,
            formatted_value: null,
            unit: null,
            delta: null,
            delta_label: null,
            trend: null,
            format: "percent",
            available: false,
            source: "data_quality_summary",
          },
        ]}
      />,
    );
    expect(screen.getByText("DQ Score")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });

  it("renders formatted KPI values", () => {
    render(
      <ExecutiveKpiRow
        metrics={[
          {
            id: "revenue",
            label: "Revenue",
            value: 120000,
            formatted_value: "$120,000",
            unit: "USD",
            delta: 0.05,
            delta_label: "vs prior period",
            trend: "up",
            format: "currency",
            available: true,
            source: "executive_scorecard",
          },
        ]}
      />,
    );
    expect(screen.getByText("Revenue")).toBeInTheDocument();
    expect(screen.getByText("$120,000")).toBeInTheDocument();
  });
});
