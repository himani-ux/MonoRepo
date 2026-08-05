import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import SafetyIncidentPhase2Page from "../../../src/routes/safety/incident/[id]/phase-2";

const navigateMock = vi.fn();
const toastMock = vi.fn();
const getIncidentPhase2Mock = vi.fn();

const authState = vi.hoisted(() => ({
  role: "2/E",
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../src/hooks/safety/use-auth", () => ({
  useSafetyAuth: () => ({
    formIds: ["SAF_F_001"],
    hasAnySafetyAccess: () => true,
    hasForm: () => true,
    hasProcess: () => true,
    isGlobal: false,
    processIds: ["SAF_P_002"],
    role: authState.role,
    user: null,
    vesselIds: ["7"],
  }),
}));

vi.mock("../../../src/hooks/use-toast", () => ({
  useToast: () => ({
    toast: toastMock,
  }),
}));

vi.mock("../../../src/lib/api/safety", () => ({
  safetyApi: {
    getIncidentPhase2: (...args: unknown[]) => getIncidentPhase2Mock(...args),
    submitIncidentPhase2: vi.fn(),
    updateIncidentPhase2: vi.fn(),
  },
}));

function renderRoute(initialEntries: Array<string | { pathname: string; state?: unknown }>) {
  render(
    <MemoryRouter initialEntries={initialEntries as any}>
      <Routes>
        <Route path="/safety/incidents/:id/phase-2" element={<SafetyIncidentPhase2Page />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("SafetyIncidentPhase2Page handoff", () => {
  it("shows the awaiting-resource-allocation state for 2/E after Phase 1 submit", async () => {
    authState.role = "2/E";
    getIncidentPhase2Mock.mockResolvedValue({
      current_phase: 2,
      dpa_notified_at: null,
      fm_notified_at: null,
      id: 42,
      incident_number: null,
      imo_classifier: null,
      latitude: "",
      longitude: "",
      notification_channel_count: 0,
      office_notified_at: null,
      office_notified: false,
      pic_user_id: null,
      resources_allocated: null,
      risk_band: "YELLOW",
      schema_version: 1,
      state: "SUBMITTED",
    });

    renderRoute([
      {
        pathname: "/safety/incidents/42/phase-2",
        state: {
          phase2Handoff: {
            authorized_roles: ["MASTER", "CO", "CE", "DPA", "FM"],
            can_edit_phase_2: false,
            message: "Phase 2 editing is restricted to Master, CO, CE, DPA, or FM. Awaiting resource allocation.",
            notifications_emitted: 5,
          },
        },
      },
    ]);

    expect(await screen.findByRole("heading", { name: "Office communication pending" })).toBeInTheDocument();
    expect(screen.getByText(/Users who can update/i)).toBeInTheDocument();
    expect(screen.getByText(/Notification fan-out sent: 5/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Tell Office" }),
    ).not.toBeInTheDocument();
  });

  it("still renders the editable Phase 2 workspace for authorized roles", async () => {
    authState.role = "MASTER";
    getIncidentPhase2Mock.mockResolvedValue({
      current_phase: 2,
      dpa_notified_at: null,
      fm_notified_at: null,
      id: 42,
      incident_number: null,
      imo_classifier: null,
      latitude: "",
      longitude: "",
      notification_channel_count: 0,
      office_notified_at: null,
      office_notified: false,
      pic_user_id: null,
      resources_allocated: null,
      risk_band: "YELLOW",
      schema_version: 1,
      state: "SUBMITTED",
    });

    renderRoute(["/safety/incidents/42/phase-2"]);

    expect(
      await screen.findByRole("heading", { name: "Tell Office" }),
    ).toBeInTheDocument();

    expect(screen.getByLabelText("Risk level")).toBeInTheDocument();
    expect(screen.getByLabelText("Was office informed?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument();
  });
});
