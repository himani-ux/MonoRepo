import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useRoutes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

const safetyApiMocks = vi.hoisted(() => ({
  getIncidentPhase6Workspace: vi.fn(),
  getIncidentPhase7Preflight: vi.fn(),
  transitionIncident: vi.fn(),
}));

vi.mock("@/components/layout/root-layout", () => ({
  RootLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="root-layout">{children}</div>
  ),
}));

vi.mock("../../../src/lib/api/safety", async () => {
  const actual = await vi.importActual<typeof import("../../../src/lib/api/safety")>(
    "../../../src/lib/api/safety",
  );
  return {
    ...actual,
    safetyApi: {
      ...actual.safetyApi,
      getIncidentPhase6Workspace: safetyApiMocks.getIncidentPhase6Workspace,
      getIncidentPhase7Preflight: safetyApiMocks.getIncidentPhase7Preflight,
      transitionIncident: safetyApiMocks.transitionIncident,
    },
  };
});

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

describe("Safety action phase route", () => {
  it("redirects the removed Lessons Learned route to Office Review", async () => {
    safetyApiMocks.getIncidentPhase6Workspace.mockResolvedValue({
      alarp_complete: true,
      bias_guards_complete: true,
      blame_evaluation: {
        all_root_personal_factors: false,
        blocked: false,
        has_lack_of_control: false,
        override_by: null,
        trigger_terms: [],
      },
      corrective_actions: [],
      gate_blockers: [],
      incident_id: "42",
      missing_tiers: [],
      recommendations: {
        CORRECTIVE: [],
        LESSONS_LEARNT: [],
        PREVENTIVE: [],
      },
      schema_version: 1,
      themes: [],
      threshold_hint: null,
      tier_counts: {},
      tolerable_failure_allowed: false,
    });
    safetyApiMocks.getIncidentPhase7Preflight.mockResolvedValue({
      blockers: [],
      closer_role: "DPA",
      current_phase: 7,
      generated_at: "2026-07-03T00:00:00Z",
      incident_id: 42,
      office_comment: "",
      pdf_preview: {
        available: true,
        download_path: "/api/safety/export/incident/42/pdf/",
        expected_sections: 9,
        incident_id: 42,
        message: "PDF ready.",
        status: "READY",
      },
      ready_for_acceptance: true,
      recommendation_tier_count: {
        CORRECTIVE: 1,
        PREVENTIVE: 1,
      },
      required_process_id: "SAF_P_004",
      risk_band: "YELLOW",
      root_count: 1,
      signature_chain_status: {
        dpa: { present: false, required: true },
        fm: { present: false, required: false },
        hod: { present: true, required: true },
        master: { present: true, required: true },
        pic: { present: false, required: false },
        reporter: { present: true, required: true },
      },
    });
    safetyApiMocks.transitionIncident.mockResolvedValue({
      incident_id: 42,
      phase_from: 6,
      phase_to: 7,
      transition_type: "FORWARD",
    });
    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-3/lessons"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Office Review", {}, { timeout: 7000 })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Add Lesson Learned" })).not.toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase6Workspace).not.toHaveBeenCalled();
    expect(safetyApiMocks.getIncidentPhase7Preflight).toHaveBeenCalledWith("42");
    expect(safetyApiMocks.transitionIncident).not.toHaveBeenCalled();
  });
});
