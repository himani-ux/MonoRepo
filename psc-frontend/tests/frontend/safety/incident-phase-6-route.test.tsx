import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

describe("Safety Phase 6 route", () => {
  it("renders Phase 6 and advances through the transition API", async () => {
    const user = userEvent.setup();
    safetyApiMocks.getIncidentPhase6Workspace.mockResolvedValue({});
    safetyApiMocks.getIncidentPhase7Preflight.mockResolvedValue({
      blockers: [],
      current_phase: 7,
      incident_id: 42,
      ready_for_acceptance: true,
      risk_band: "YELLOW",
    });
    safetyApiMocks.transitionIncident.mockResolvedValue({
      incident_id: 42,
      phase_from: 6,
      phase_to: 7,
      transition_type: "FORWARD",
    });
    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-6"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Phase 6 Recommendations and ALARP" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue to Phase 7" }));

    expect(safetyApiMocks.transitionIncident).toHaveBeenCalledWith("42", { target_phase: 7 });
    expect(
      await screen.findByRole("heading", { name: "Phase 7 Acceptance and Closure Authority" }),
    ).toBeInTheDocument();
  });
});
