import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useRoutes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

const safetyApiMocks = vi.hoisted(() => ({
  getIncidentPhase5Workspace: vi.fn(),
  getIncidentPhase6Workspace: vi.fn(),
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
      getIncidentPhase5Workspace: safetyApiMocks.getIncidentPhase5Workspace,
      getIncidentPhase6Workspace: safetyApiMocks.getIncidentPhase6Workspace,
      transitionIncident: safetyApiMocks.transitionIncident,
    },
  };
});

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

describe("Safety Phase 5 route", () => {
  it("renders Phase 5 and advances through the transition API", async () => {
    const user = userEvent.setup();
    safetyApiMocks.getIncidentPhase5Workspace.mockResolvedValue({});
    safetyApiMocks.getIncidentPhase6Workspace.mockResolvedValue({});
    safetyApiMocks.transitionIncident.mockResolvedValue({
      incident_id: 42,
      phase_from: 5,
      phase_to: 6,
      transition_type: "FORWARD",
    });
    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-5"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Phase 5 Causal Analysis" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue to Phase 6" }));

    expect(safetyApiMocks.transitionIncident).toHaveBeenCalledWith("42", { target_phase: 6 });
    expect(
      await screen.findByRole("heading", { name: "Phase 6 Recommendations and ALARP" }),
    ).toBeInTheDocument();
  });
});
