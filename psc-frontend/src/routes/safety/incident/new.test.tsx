import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const incidentCreateMocks = vi.hoisted(() => ({
  createIncident: vi.fn(),
  navigate: vi.fn(),
  submitIncidentPhase1: vi.fn(),
  toast: vi.fn(),
  updateIncidentPhase2: vi.fn(),
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>(
    "react-router-dom"
  );
  return {
    ...actual,
    useNavigate: () => incidentCreateMocks.navigate,
  };
});

vi.mock("../../../components/safety/incident/phase1-form", () => ({
  SafetyIncidentPhase1Form: (props: {
    onSubmitPhase?: (values: Record<string, unknown>) => void | Promise<void>;
  }) => (
    <button
      onClick={() =>
        props.onSubmitPhase?.({
          activity_type: "Bunkering",
          awaiting_daily_report_match: false,
          conflict_acknowledged: false,
          external_party_injury: null,
          incident_type_id: null,
          latitude: null,
          longitude: null,
          loss_type_other: null,
          loss_type_primary_id: null,
          loss_type_secondary_id: null,
          loss_type_tertiary_id: null,
          narrative: "Incident narrative with enough detail for test submission.",
          occurred_at: "2026-07-13T08:00:00Z",
          office_notification_mode: null,
          office_notified: false,
          onboard_location: "Main deck",
          permit_issued: "YES",
          pic_candidate_id: "pic-1",
          position_daily_report_id: null,
          position_source: null,
          reported_at: "2026-07-13T08:10:00Z",
          reporter_department: "Deck",
          reporter_device_fingerprint: "device-1",
          reporter_name: "Master One",
          reporter_rank: "MASTER",
          reporter_user_id: "master-1",
          risk_assessment_carried_out: "YES",
          risk_band: "GREEN",
          schema_version: 1,
          shore_assistance_required: false,
          toolbox_meeting_carried_out: "YES",
          vessel_code: "YCF",
          vessel_condition: "LOADED",
          vessel_id: "7",
          vessel_location: "In Port",
          vessel_location_detail: "Singapore",
          weather_ambient_temperature_c: null,
          weather_current_direction_id: null,
          weather_current_strength_knots: null,
          weather_ice_condition_at_sea_id: null,
          weather_ice_condition_onboard_id: null,
          weather_light_condition_id: null,
          weather_lighting_source_id: null,
          weather_precipitation_id: null,
          weather_sea_state_id: null,
          weather_visibility_id: null,
          weather_wind_direction_id: null,
          weather_wind_scale_id: null,
        })
      }
      type="button"
    >
      Submit report
    </button>
  ),
}));

vi.mock("../../../hooks/use-toast", () => ({
  useToast: () => ({ toast: incidentCreateMocks.toast }),
}));

vi.mock("../../../lib/api/safety", () => ({
  safetyApi: {
    createIncident: incidentCreateMocks.createIncident,
    submitIncidentPhase1: incidentCreateMocks.submitIncidentPhase1,
    updateIncidentPhase2: incidentCreateMocks.updateIncidentPhase2,
  },
}));

import SafetyIncidentCreatePage from "./new";

describe("SafetyIncidentCreatePage", () => {
  beforeEach(() => {
    incidentCreateMocks.createIncident.mockResolvedValue({
      id: "incident-123",
      incident_number: "YCF/2026/001",
    });
    incidentCreateMocks.submitIncidentPhase1.mockResolvedValue({
      id: "incident-123",
      incident_number: "YCF/2026/001",
      phase_2_handoff: {
        can_edit_phase_2: false,
        message: "Office needs to confirm communication next.",
      },
    });
    incidentCreateMocks.updateIncidentPhase2.mockResolvedValue({});
    incidentCreateMocks.navigate.mockClear();
    incidentCreateMocks.toast.mockClear();
  });

  it("sends Phase 1 operational fields in the create payload", async () => {
    render(
      <MemoryRouter>
        <SafetyIncidentCreatePage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Submit report" }));

    await waitFor(() => {
      expect(incidentCreateMocks.createIncident).toHaveBeenCalledWith(
        expect.objectContaining({
          activity_type: "Bunkering",
          permit_issued: "YES",
          risk_assessment_carried_out: "YES",
          toolbox_meeting_carried_out: "YES",
          vessel_location: "In Port",
          vessel_location_detail: "Singapore",
        })
      );
    });
  });
});
