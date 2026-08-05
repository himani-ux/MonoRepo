import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SafetyIncidentPhase1Form } from "../../../src/components/safety/incident/phase1-form";

const phase1FormMocks = vi.hoisted(() => ({
  getIncidentWeatherOptions: vi.fn(),
  getInjuryDropdownOptions: vi.fn(),
  getReferenceIncidentTypes: vi.fn(),
  getReferenceLossTypes: vi.fn(),
  toast: vi.fn(),
}));

vi.mock("../../../src/hooks/use-auth", () => ({
  useAuth: () => ({
    isVessel: true,
    user: {
      crew_id: "master-7",
      full_name: "Master Seven",
      rank: "MASTER",
      role: "VESSEL_MASTER",
      vessel_code: "ARY",
      vessel_id: "7",
      vessel_name: "ARYA",
      vessel_ids: ["7"],
      vessel_names: ["ARYA"],
    },
  }),
}));

vi.mock("../../../src/hooks/use-toast", () => ({
  useToast: () => ({ toast: phase1FormMocks.toast }),
}));

vi.mock("../../../src/hooks/safety/use-draft-autosave", () => ({
  useDraftAutosave: () => ({
    lastSavedAt: null,
    saveDraftNow: vi.fn().mockResolvedValue({
      updatedAt: "2026-06-23T00:00:00Z",
    }),
    status: "ready",
  }),
}));

vi.mock("../../../src/hooks/safety/use-msc-mepc3-position", () => ({
  toUtcIsoTimestamp: (value: string | null | undefined) =>
    value ? "2026-04-20T10:00:00.000Z" : null,
}));

vi.mock("../../../src/lib/safety/digital-signature", () => ({
  getSafetyDeviceFingerprint: () => "test-device",
}));

vi.mock("../../../src/lib/api/safety", () => ({
  safetyApi: {
    getIncidentWeatherOptions: phase1FormMocks.getIncidentWeatherOptions,
    getInjuryDropdownOptions: phase1FormMocks.getInjuryDropdownOptions,
    getReferenceIncidentTypes: phase1FormMocks.getReferenceIncidentTypes,
    getReferenceLossTypes: phase1FormMocks.getReferenceLossTypes,
  },
}));

describe("SafetyIncidentPhase1Form", () => {
  beforeEach(() => {
    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.toast.mockClear();
  });

  it("renders the current Phase 1 heading and submit action", async () => {
    render(<SafetyIncidentPhase1Form mode="create" />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Tell Us What Happened" }),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByRole("button", { name: "Submit report" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "Intake + Scene Control" }),
    ).not.toBeInTheDocument();
  });

  it("uses the current field labels and keeps retired labels hidden", async () => {
    render(<SafetyIncidentPhase1Form mode="create" />);

    await waitFor(() => {
      expect(screen.getByLabelText("Vessel")).toBeInTheDocument();
    });

    expect(screen.getByLabelText("What happened")).toBeInTheDocument();
    expect(screen.getByLabelText("Person in charge")).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Was office informed?" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Report time")).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Shore Assistance Required" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Latitude")).toBeInTheDocument();
    expect(screen.getByLabelText("Longitude")).toBeInTheDocument();

    expect(screen.queryByLabelText("Vessel ID")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Checklist complete")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Narrative")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Was office told?")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Last Port")).not.toBeInTheDocument();
  });
});
