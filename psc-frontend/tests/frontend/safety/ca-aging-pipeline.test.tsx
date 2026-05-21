import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import SafetyCaAgingPipeline from "../../../src/components/safety/dashboard/ca-aging-pipeline";

describe("Safety CA aging pipeline panel", () => {
  it("renders all four CA aging buckets and the creation-date note", () => {
    render(
      <SafetyCaAgingPipeline
        buckets={[
          { bucket: "0-15", count: 2, label: "0-15 days" },
          { bucket: "15-30", count: 1, label: "15-30 days" },
          { bucket: "30-45", count: 0, label: "30-45 days" },
          { bucket: "45+", count: 3, label: "45+ days" },
        ]}
        label="CA Aging Pipeline"
        note="Clock starts at CA creation date; reopened actions keep the original aging clock."
        oldestAgeDays={63}
        openActionCount={6}
      />,
    );

    expect(screen.getByText("CA Aging Pipeline")).toBeInTheDocument();
    expect(screen.getByText("Corrective action pressure by age band")).toBeInTheDocument();
    expect(screen.getByText("0-15 days")).toBeInTheDocument();
    expect(screen.getByText("15-30 days")).toBeInTheDocument();
    expect(screen.getByText("30-45 days")).toBeInTheDocument();
    expect(screen.getByText("45+ days")).toBeInTheDocument();
    expect(screen.getByText(/oldest aging at 63 days/i)).toBeInTheDocument();
  });
});
