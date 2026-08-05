import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import SafetySoiCompliancePanel from "../../../src/components/safety/dashboard/soi-compliance-panel";

describe("Safety SOI compliance panel", () => {
  it("keeps the literal SOI Compliance % label and new-vessel copy", () => {
    render(
      <SafetySoiCompliancePanel
        currentVessel={{
          applicableAreaCount: 13,
          displayValue: "N/A - awaiting first cycle",
          inspectedAreaCount: 0,
          overdueAreaCount: 0,
          status: "NA",
          vesselLabel: "Current vessel",
        }}
        fleetAverage={{
          displayValue: "74%",
          note: "Average across 4 vessels with completed SOI cycles.",
          vesselCount: 4,
        }}
        label="SOI Compliance %"
      />,
    );

    expect(screen.getAllByText("SOI Compliance %").length).toBeGreaterThan(0);
    expect(screen.getByText("SOI check status")).toBeInTheDocument();
    expect(screen.getAllByText("N/A - awaiting first cycle").length).toBeGreaterThan(0);
    expect(screen.getByText(/Average across 4 vessels/i)).toBeInTheDocument();
  });
});
