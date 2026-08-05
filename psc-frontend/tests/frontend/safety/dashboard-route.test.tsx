import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import SafetyDashboardRoute from "../../../src/routes/safety/dashboard";
import { useSafetyDashboardPeriodStore } from "../../../src/stores/safety/dashboard-period-store";

vi.mock("../../../src/hooks/use-safety", () => ({
  useSafetyDashboardCaAging: () => ({
    data: {
      buckets: [
        { bucket: "0_15", count: 1, label: "0-15 days" },
        { bucket: "16_30", count: 0, label: "16-30 days" },
      ],
      label: "Action age",
      note: "Open action age by band.",
      oldest_age_days: 12,
      open_action_count: 1,
    },
    error: null,
    isLoading: false,
  }),
  useSafetyDashboardComposite: () => ({
    data: {
      available_vessels: [],
      component_scores: {
        open_findings: 90,
        open_incidents: 80,
        open_near_misses: 95,
        overdue_corrective_actions: 70,
        soi_compliance: 88,
      },
      composite_score: 86,
      metrics: {
        open_findings: 2,
        open_incidents: 1,
        open_near_misses: 3,
        overdue_corrective_actions: 1,
        soi_compliance_display: "88%",
        soi_compliance_label: "SOI Compliance %",
      },
      scope_id: "",
      scope_type: "FLEET",
      score_status: "GREEN",
      window_end: "2026-07-13",
      window_start: "2026-04-14",
    },
    error: null,
    isLoading: false,
  }),
  useSafetyDashboardHeinrich: () => ({
    data: {
      confidence: {
        incident_count_12m: 4,
        near_miss_count_12m: 12,
        reason: "Enough recent data for review.",
        status: "AMBER",
        tooltip: "Review reporting pattern.",
      },
      layers: [
        { actual: 12, benchmark: 20, key: "near_miss", label: "Near miss", variance: -8 },
      ],
      reporting_culture_gap: {
        is_gap: false,
        message: "",
      },
      window_end: "2026-07-13",
      window_start: "2023-07-14",
    },
    error: null,
    isLoading: false,
  }),
  useSafetyDashboardPareto: () => ({
    data: {
      entries: [
        {
          category_name: "Work planning",
          cumulative_percent: 50,
          description: "Permit planning weakness",
          occurrences: 2,
          rank: 1,
          share_percent: 50,
          subcode_id: "10.1",
          vessel_code: "MV01",
          vessel_display_name: "MV Atlas",
          vessel_id: "vessel-1",
          vessel_name: "Atlas",
          within_80_cutoff: true,
        },
      ],
      top_n: 5,
      total_occurrences: 2,
    },
    error: null,
    isLoading: false,
  }),
  useSafetyDashboardRepeatRoot: () => ({
    data: {
      fleet: [
        {
          category_name: "Work planning",
          description: "Permit planning weakness",
          occurrences: 3,
          relative_strength: 80,
          subcode_id: "10.1",
          vessel_count: 2,
        },
      ],
      minimum_repeat_count: 3,
      vessel: [],
    },
    error: null,
    isLoading: false,
  }),
  useSafetyDashboardSoiCompliance: () => ({
    data: {
      current_vessel: {
        applicable_area_count: 13,
        display_value: "88%",
        inspected_area_count: 11,
        overdue_area_count: 1,
        status: "AMBER",
      },
      fleet_average: {
        display_value: "84%",
        note: "Average across active vessels.",
        vessel_count: 5,
      },
      label: "SOI Compliance %",
    },
    error: null,
    isLoading: false,
  }),
}));

function renderDashboard(role = "DPA", processIds: string[] = []) {
  return render(
    <SafetyAuthProvider
      value={{
        formIds: ["SAF_F_015"],
        id: "user-1",
        processIds,
        role,
        vesselIds: ["vessel-1"],
      }}
    >
      <SafetyDashboardRoute />
    </SafetyAuthProvider>,
  );
}

describe("Safety dashboard route", () => {
  it("keeps advanced dashboard cards hidden until the user asks for them", () => {
    useSafetyDashboardPeriodStore.getState().reset();

    renderDashboard();

    expect(screen.getByRole("heading", { name: "Safety Dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Safety score")).toBeInTheDocument();
    expect(screen.getByText("0 to 100 scale. Higher is better.")).toBeInTheDocument();
    expect(screen.queryByText("80 / 100")).not.toBeInTheDocument();
    expect(screen.queryByText("Reporting trend")).not.toBeInTheDocument();
    expect(screen.queryByText("SOI check status")).not.toBeInTheDocument();
    expect(screen.queryByText("Recurring safety issues")).not.toBeInTheDocument();
    expect(screen.queryByText("Top repeat issues over the last 12 months")).not.toBeInTheDocument();
    expect(screen.queryByText("Open actions by age")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show dashboard details" }));

    expect(screen.getByText("Recurring safety issues")).toBeInTheDocument();
    expect(screen.getByText("Top repeat issues over the last 12 months")).toBeInTheDocument();
    expect(screen.getByText("Open actions by age")).toBeInTheDocument();
    expect(screen.getAllByText("Reporting trend").length).toBeGreaterThan(0);
    expect(screen.getByText("SOI check status")).toBeInTheDocument();
    expect(screen.getAllByText("SOI Compliance %").length).toBeGreaterThan(0);
  });

  it("switches the persisted period selector without leaving the route", () => {
    useSafetyDashboardPeriodStore.getState().reset();

    renderDashboard();

    fireEvent.click(screen.getByRole("button", { name: "12M" }));

    expect(screen.getByRole("button", { name: "12M" })).toHaveAttribute("aria-pressed", "true");
  });

  it("enables dashboard export only for DPA users with export process access", () => {
    useSafetyDashboardPeriodStore.getState().reset();

    renderDashboard("DPA", ["SAF_P_023"]);
    expect(screen.getByRole("button", { name: "Download PDF" })).toBeEnabled();
    expect(screen.queryByText("Export is available for your login.")).not.toBeInTheDocument();
  });

  it("keeps dashboard export disabled for FM readers", () => {
    useSafetyDashboardPeriodStore.getState().reset();

    renderDashboard("FM", ["SAF_P_023"]);
    expect(screen.getByRole("button", { name: "Download PDF" })).toBeDisabled();
    expect(screen.getByText("Export is limited to authorized office users.")).toBeInTheDocument();
  });
});
