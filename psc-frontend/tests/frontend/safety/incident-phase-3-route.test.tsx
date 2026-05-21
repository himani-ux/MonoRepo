import type { ReactNode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useRoutes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

const safetyApiMocks = vi.hoisted(() => ({
  getIncidentPhase3ChainOfCustody: vi.fn(),
  getIncidentPhase3Evidence: vi.fn(),
  getIncidentPhase3EvidenceMatrix: vi.fn(),
  getIncidentPhase3Interviews: vi.fn(),
  getIncidentPhase4Facts: vi.fn(),
  transitionIncident: vi.fn(),
  updateIncidentPhase3Evidence: vi.fn(),
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
      getIncidentPhase3ChainOfCustody: safetyApiMocks.getIncidentPhase3ChainOfCustody,
      getIncidentPhase3Evidence: safetyApiMocks.getIncidentPhase3Evidence,
      getIncidentPhase3EvidenceMatrix: safetyApiMocks.getIncidentPhase3EvidenceMatrix,
      getIncidentPhase3Interviews: safetyApiMocks.getIncidentPhase3Interviews,
      getIncidentPhase4Facts: safetyApiMocks.getIncidentPhase4Facts,
      transitionIncident: safetyApiMocks.transitionIncident,
      updateIncidentPhase3Evidence: safetyApiMocks.updateIncidentPhase3Evidence,
    },
  };
});

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

function renderSafetyRoute(pathname: string) {
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
        <Routes>
          <Route path="/safety/*" element={<SafetyRoutesHarness />} />
        </Routes>
      </SafetyAuthProvider>
    </MemoryRouter>,
  );
}

describe("Safety Phase 3 routes", () => {
  it("renders the Phase 3 people route for users with SAF_F_001", async () => {
    safetyApiMocks.getIncidentPhase3Evidence.mockResolvedValue({
      deadline_tasks: [],
      paper: {
        entry_count: 1,
        status_chip: "COMPLETE",
        structured_data: { checklist_complete: true },
        summary: "Marine documents checked",
        tab_code: "PAPER",
      },
      people: {
        entry_count: 1,
        status_chip: "IN_PROGRESS",
        summary: "Backend Phase 3 people evidence",
        tab_code: "PEOPLE",
      },
    });
    safetyApiMocks.getIncidentPhase3ChainOfCustody.mockResolvedValue([
      {
        collection_timestamp: "2026-05-08T00:00:00Z",
        collector_name: "DPA One",
        collector_signature: "DPA One",
        current_holder: "DPA One",
        description: "Bridge wing photo",
        handover_log: [],
        id: 1,
        storage_location: "Evidence locker",
        witness_signature: "Witness One",
      },
    ]);
    safetyApiMocks.getIncidentPhase3EvidenceMatrix.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase3Interviews.mockResolvedValue([]);

    renderSafetyRoute("/safety/incidents/42/phase-3/people");

    expect(
      await screen.findByRole("heading", { name: "Phase 3 Evidence Workspace" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "People" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Evidence Matrix" })).toBeInTheDocument();
    expect(screen.queryByText("Backend payload")).not.toBeInTheDocument();
    expect(document.querySelector("pre")).not.toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase3Evidence).toHaveBeenCalledWith("42");
  });

  it("renders the bare Phase 3 route as the default people workspace", async () => {
    safetyApiMocks.getIncidentPhase3Evidence.mockResolvedValue({
      deadline_tasks: [],
      paper: {
        entry_count: 1,
        status_chip: "COMPLETE",
        structured_data: { checklist_complete: true },
        summary: "Marine documents checked",
        tab_code: "PAPER",
      },
      people: {
        entry_count: 1,
        status_chip: "IN_PROGRESS",
        summary: "Backend Phase 3 people evidence",
        tab_code: "PEOPLE",
      },
    });
    safetyApiMocks.getIncidentPhase3ChainOfCustody.mockResolvedValue([
      {
        collection_timestamp: "2026-05-08T00:00:00Z",
        collector_name: "DPA One",
        collector_signature: "DPA One",
        current_holder: "DPA One",
        description: "Bridge wing photo",
        handover_log: [],
        id: 1,
        storage_location: "Evidence locker",
        witness_signature: "Witness One",
      },
    ]);
    safetyApiMocks.getIncidentPhase3EvidenceMatrix.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase3Interviews.mockResolvedValue([]);

    renderSafetyRoute("/safety/incidents/42/phase-3");

    expect(
      await screen.findByRole("heading", { name: "Phase 3 Evidence Workspace" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Evidence Summary")).toBeInTheDocument();
    expect(screen.queryByText("Backend payload")).not.toBeInTheDocument();
    expect(document.querySelector("pre")).not.toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase3Evidence).toHaveBeenCalledWith("42");
  });

  it("transitions the incident before opening Phase 4", async () => {
    const user = userEvent.setup();
    safetyApiMocks.getIncidentPhase3Evidence.mockResolvedValue({
      deadline_tasks: [],
      paper: {
        entry_count: 1,
        status_chip: "COMPLETE",
        structured_data: { checklist_complete: true },
        summary: "Marine documents checked",
        tab_code: "PAPER",
      },
      people: {
        entry_count: 1,
        status_chip: "IN_PROGRESS",
        summary: "Backend Phase 3 people evidence",
        tab_code: "PEOPLE",
      },
    });
    safetyApiMocks.getIncidentPhase3ChainOfCustody.mockResolvedValue([
      {
        collection_timestamp: "2026-05-08T00:00:00Z",
        collector_name: "DPA One",
        collector_signature: "DPA One",
        current_holder: "DPA One",
        description: "Bridge wing photo",
        handover_log: [],
        id: 1,
        storage_location: "Evidence locker",
        witness_signature: "Witness One",
      },
    ]);
    safetyApiMocks.getIncidentPhase3EvidenceMatrix.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase3Interviews.mockResolvedValue([]);
    safetyApiMocks.transitionIncident.mockResolvedValue({
      incident_id: 42,
      phase_from: 3,
      phase_to: 4,
      transition_type: "FORWARD",
    });
    safetyApiMocks.getIncidentPhase4Facts.mockResolvedValue([]);

    renderSafetyRoute("/safety/incidents/42/phase-3");

    const continueButton = await screen.findByRole("button", { name: "Continue to Phase 4" });
    await waitFor(() => expect(continueButton).toBeEnabled());
    await user.click(continueButton);

    expect(safetyApiMocks.transitionIncident).toHaveBeenCalledWith("42", { target_phase: 4 });
    expect(
      await screen.findByRole("heading", { name: "Phase 4 Facts and Sequence" }),
    ).toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase4Facts).toHaveBeenCalledWith("42");
  });

  it("shows Phase 4 blockers instead of calling transition when preservation is incomplete", async () => {
    safetyApiMocks.getIncidentPhase3Evidence.mockResolvedValue({
      deadline_tasks: [],
      people: {
        entry_count: 1,
        status_chip: "IN_PROGRESS",
        summary: "Backend Phase 3 people evidence",
        tab_code: "PEOPLE",
      },
    });
    safetyApiMocks.getIncidentPhase3ChainOfCustody.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase3EvidenceMatrix.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase3Interviews.mockResolvedValue([]);

    renderSafetyRoute("/safety/incidents/42/phase-3");

    expect(
      await screen.findByText(/Before Phase 4, add at least one chain-of-custody item/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue to Phase 4" })).toBeDisabled();
    expect(safetyApiMocks.transitionIncident).not.toHaveBeenCalled();
  });

  it("saves the marine document checklist completion flag from the Paper tab", async () => {
    const user = userEvent.setup();
    safetyApiMocks.getIncidentPhase3Evidence.mockResolvedValue({
      deadline_tasks: [],
      paper: {
        entry_count: 0,
        status_chip: "IN_PROGRESS",
        structured_data: {},
        summary: "Marine documents in review",
        tab_code: "PAPER",
      },
    });
    safetyApiMocks.getIncidentPhase3ChainOfCustody.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase3EvidenceMatrix.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase3Interviews.mockResolvedValue([]);
    safetyApiMocks.updateIncidentPhase3Evidence.mockResolvedValue({
      paper: {
        entry_count: 0,
        status_chip: "IN_PROGRESS",
        structured_data: { checklist_complete: true },
        summary: "Marine documents in review",
        tab_code: "PAPER",
      },
    });

    renderSafetyRoute("/safety/incidents/42/phase-3/paper");

    await user.click(
      await screen.findByRole("checkbox", { name: /Marine document checklist complete/ }),
    );
    await user.click(screen.getByRole("button", { name: "Save evidence source" }));

    await waitFor(() => {
      expect(safetyApiMocks.updateIncidentPhase3Evidence).toHaveBeenCalledWith(
        "42",
        expect.objectContaining({
          paper: expect.objectContaining({
            structured_data: expect.objectContaining({ checklist_complete: true }),
          }),
        }),
      );
    });
  });
});
