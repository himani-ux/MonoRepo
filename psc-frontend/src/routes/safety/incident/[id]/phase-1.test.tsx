import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const phase1RouteMocks = vi.hoisted(() => ({
  getIncidentPhase1: vi.fn(),
  toast: vi.fn(),
  updateIncidentPhase1: vi.fn(),
}));

vi.mock("../../../../components/safety/incident/incident-phase-switcher", () => ({
  default: () => <div data-testid="phase-switcher" />,
}));

vi.mock("../../../../components/safety/incident/phase1-form", () => ({
  SafetyIncidentPhase1Form: (props: {
    initialValues?: {
      activity_type?: string;
      narrative?: string;
      vessel_location_detail?: string;
    };
    onSaveDraft?: (values: Record<string, unknown>) => void | Promise<void>;
  }) => (
    <section>
      <p>{props.initialValues?.narrative ?? "no narrative"}</p>
      <p>{props.initialValues?.vessel_location_detail ?? "no vessel detail"}</p>
      <p>{props.initialValues?.activity_type ?? "no activity type"}</p>
      <button
        onClick={() =>
          props.onSaveDraft?.({
            awaiting_daily_report_match: false,
            external_party_injury: null,
            incident_type_id: null,
            latitude: null,
            longitude: null,
            loss_type_other: null,
            loss_type_primary_id: null,
            loss_type_secondary_id: null,
            loss_type_tertiary_id: null,
            activity_type: "Bunkering",
            narrative: "Saved edited narrative",
            occurred_at: "2026-06-24T08:00:00Z",
            office_notification_mode: null,
            office_notified: false,
            position_daily_report_id: null,
            position_source: null,
            reported_at: "2026-06-24T08:15:00Z",
            reporter_department: "Deck",
            reporter_device_fingerprint: "device-1",
            reporter_name: "Master One",
            reporter_rank: "MASTER",
            reporter_user_id: "master-1",
            permit_issued: "NA",
            risk_assessment_carried_out: "YES",
            risk_band: "GREEN",
            schema_version: 1,
            vessel_code: "ARY",
            vessel_id: "7",
            vessel_location: "In Port",
            vessel_location_detail: "Singapore",
            toolbox_meeting_carried_out: "NO",
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
        Save changes
      </button>
    </section>
  ),
}));

vi.mock("../../../../hooks/use-toast", () => ({
  useToast: () => ({ toast: phase1RouteMocks.toast }),
}));

vi.mock("../../../../lib/api/safety", () => ({
  safetyApi: {
    getIncidentPhase1: phase1RouteMocks.getIncidentPhase1,
    updateIncidentPhase1: phase1RouteMocks.updateIncidentPhase1,
  },
}));

import SafetyIncidentPhase1Route from "./phase-1";

describe("SafetyIncidentPhase1Route", () => {
  beforeEach(() => {
    phase1RouteMocks.getIncidentPhase1.mockResolvedValue({
      awaiting_daily_report_match: false,
      current_phase: 3,
      external_party_injury: {
        crew_rank: "Chief Officer",
        injured_person_type: "CREW",
      },
      id: "incident-123",
      incident_number: "ARY/2026/003",
      activity_type: "Bunkering",
      narrative: "Existing Phase 1 narrative",
      office_notified: false,
      reported_at: "2026-06-24T08:15:00Z",
      reporter_device_fingerprint: "device-1",
      reporter_name: "Master One",
      reporter_rank: "MASTER",
      reporter_user_id: "master-1",
      permit_issued: "NA",
      risk_assessment_carried_out: "YES",
      risk_band: "GREEN",
      schema_version: 1,
      state: "IN_PROGRESS",
      vessel_code: "ARY",
      vessel_id: "7",
      vessel_location: "In Port",
      vessel_location_detail: "Singapore",
      toolbox_meeting_carried_out: "NO",
    });
    phase1RouteMocks.updateIncidentPhase1.mockResolvedValue({ id: "incident-123" });
  });

  it("loads existing phase one values and saves edits without sending null injury", async () => {
    render(
      <MemoryRouter initialEntries={["/safety/incidents/incident-123/phase-1"]}>
        <Routes>
          <Route path="/safety/incidents/:id/phase-1" element={<SafetyIncidentPhase1Route />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Existing Phase 1 narrative")).toBeTruthy();
      expect(screen.getByText("Singapore")).toBeTruthy();
      expect(screen.getByText("Bunkering")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(phase1RouteMocks.updateIncidentPhase1).toHaveBeenCalledWith(
        "incident-123",
        expect.not.objectContaining({ external_party_injury: null }),
      );
      expect(phase1RouteMocks.updateIncidentPhase1.mock.calls[0][1]).not.toHaveProperty(
        "first_hour_checklist_done",
      );
      expect(phase1RouteMocks.updateIncidentPhase1.mock.calls[0][1]).toMatchObject({
        activity_type: "Bunkering",
        permit_issued: "NA",
        risk_assessment_carried_out: "YES",
        toolbox_meeting_carried_out: "NO",
        vessel_location: "In Port",
        vessel_location_detail: "Singapore",
      });
    });
  });
});
