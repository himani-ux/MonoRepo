import type { ReactNode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useRoutes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider } from "../../../src/hooks/safety/use-auth";
import { safetyRoutes } from "../../../src/routes/safety";

const safetyApiMocks = vi.hoisted(() => ({
  createIncidentPhase4Fact: vi.fn(),
  getIncidentPhase4EvidenceSources: vi.fn(),
  getIncidentPhase4Facts: vi.fn(),
  getIncidentPhase4Gate: vi.fn(),
  getIncidentPhase5Workspace: vi.fn(),
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
      createIncidentPhase4Fact: safetyApiMocks.createIncidentPhase4Fact,
      getIncidentPhase4EvidenceSources: safetyApiMocks.getIncidentPhase4EvidenceSources,
      getIncidentPhase4Facts: safetyApiMocks.getIncidentPhase4Facts,
      getIncidentPhase4Gate: safetyApiMocks.getIncidentPhase4Gate,
      getIncidentPhase5Workspace: safetyApiMocks.getIncidentPhase5Workspace,
      transitionIncident: safetyApiMocks.transitionIncident,
    },
  };
});

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

describe("Safety Phase 4 route", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    safetyApiMocks.getIncidentPhase4Gate.mockResolvedValue({
      blockers: [],
      can_continue: true,
      covered_tabs: ["POSITION", "PEOPLE", "PARTS", "PAPER", "ELECTRONIC"],
      facts_count: 1,
      missing_tabs: [],
    });
  });

  it("creates a fact through the Phase 4 workspace form", async () => {
    const user = userEvent.setup();
    safetyApiMocks.getIncidentPhase4Facts
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            confidence: "HIGH",
            evidence_summary: "Bridge wing photo",
            fact_text: "Helm order to port 10 was logged before impact.",
            id: 11,
            sequence_index: 1,
            source_evidence_id: 7,
          },
        ],
      });
    safetyApiMocks.getIncidentPhase4EvidenceSources.mockResolvedValue([
      {
        detail: "Photo set from bridge wing.",
        id: 7,
        label: "Bridge wing photo",
        source_type: "PHYSICAL",
      },
    ]);
    safetyApiMocks.createIncidentPhase4Fact.mockResolvedValue({
      confidence: "HIGH",
      evidence_summary: "Bridge wing photo",
      fact_text: "Helm order to port 10 was logged before impact.",
      id: 11,
      sequence_index: 1,
      source_evidence_id: 7,
    });

    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-4"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Phase 4 Facts and Sequence" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Backend payload")).not.toBeInTheDocument();
    await screen.findByRole("option", { name: "PHYSICAL: Bridge wing photo" });

    await user.type(screen.getByLabelText("Fact"), "Helm order to port 10 was logged before impact.");
    await user.selectOptions(screen.getByLabelText("Source evidence"), "7");
    await user.selectOptions(screen.getByLabelText("Confidence"), "HIGH");
    await waitFor(() => expect(screen.getByRole("button", { name: "Add fact" })).toBeEnabled());
    await user.click(screen.getByRole("button", { name: "Add fact" }));

    expect(safetyApiMocks.createIncidentPhase4Fact).toHaveBeenCalledWith("42", {
      confidence: "HIGH",
      fact_text: "Helm order to port 10 was logged before impact.",
      source_evidence_id: 7,
    });
    expect(
      await screen.findByText("Helm order to port 10 was logged before impact."),
    ).toBeInTheDocument();
  });

  it("blocks fact creation until a source evidence record is available", async () => {
    safetyApiMocks.getIncidentPhase4Facts.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase4EvidenceSources.mockResolvedValue([]);

    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-4"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByText(/Add Phase 3 evidence, matrix rows, interviews, or chain-of-custody items/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add fact" })).toBeDisabled();
    expect(safetyApiMocks.createIncidentPhase4Fact).not.toHaveBeenCalled();
  });

  it("shows Phase 5 blockers before posting the transition", async () => {
    safetyApiMocks.getIncidentPhase4Facts.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase4EvidenceSources.mockResolvedValue([
      {
        detail: "Photo set from bridge wing.",
        id: 7,
        label: "Bridge wing photo",
        source_type: "PHYSICAL",
      },
    ]);
    safetyApiMocks.getIncidentPhase4Gate.mockResolvedValue({
      blockers: ["Complete or mark N/A for evidence tabs: POSITION, PEOPLE, PARTS, ELECTRONIC."],
      can_continue: false,
      covered_tabs: ["PAPER"],
      facts_count: 1,
      missing_tabs: ["POSITION", "PEOPLE", "PARTS", "ELECTRONIC"],
    });

    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-4"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByText(/Complete or mark N\/A for evidence tabs: POSITION, PEOPLE, PARTS, ELECTRONIC/),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continue to Phase 5" })).toBeDisabled();
    expect(safetyApiMocks.transitionIncident).not.toHaveBeenCalled();
  });

  it("renders Phase 4 and advances through the transition API", async () => {
    const user = userEvent.setup();
    safetyApiMocks.getIncidentPhase4Facts.mockResolvedValue([]);
    safetyApiMocks.getIncidentPhase4EvidenceSources.mockResolvedValue([
      {
        detail: "Photo set from bridge wing.",
        id: 7,
        label: "Bridge wing photo",
        source_type: "PHYSICAL",
      },
    ]);
    safetyApiMocks.getIncidentPhase5Workspace.mockResolvedValue({});
    safetyApiMocks.transitionIncident.mockResolvedValue({
      incident_id: 42,
      phase_from: 4,
      phase_to: 5,
      transition_type: "FORWARD",
    });
    render(
      <MemoryRouter initialEntries={["/safety/incidents/42/phase-4"]}>
        <SafetyAuthProvider value={{ formIds: ["SAF_F_001"] }}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: "Phase 4 Facts and Sequence" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue to Phase 5" }));

    expect(safetyApiMocks.transitionIncident).toHaveBeenCalledWith("42", { target_phase: 5 });
    expect(
      await screen.findByRole("heading", { name: "Phase 5 Causal Analysis" }),
    ).toBeInTheDocument();
  });
});
