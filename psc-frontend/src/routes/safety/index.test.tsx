import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useRoutes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SafetyAuthProvider, type SafetyAuthUser } from "../../hooks/safety/use-auth";
import { safetyRoutes } from "./index";

const safetyQueryMocks = vi.hoisted(() => ({
  useSafetyDashboardCaAging: vi.fn(),
  useSafetyDashboardComposite: vi.fn(),
  useSafetyDashboardHeinrich: vi.fn(),
  useSafetyDashboardPareto: vi.fn(),
  useSafetyDashboardRepeatRoot: vi.fn(),
  useSafetyDashboardSoiCompliance: vi.fn(),
  useSafetyIncidents: vi.fn(),
  useSafetyNearMisses: vi.fn(),
  useSafetyScmCreateAdhocConfig: vi.fn(),
  useSafetyScmCreateRegularConfig: vi.fn(),
  useSafetyScmAgenda: vi.fn(),
  useSafetyScmAutoFeed: vi.fn(),
  useSafetyScmClosedSinceLast: vi.fn(),
  useSafetyScmAttendance: vi.fn(),
  useSafetyScmMeeting: vi.fn(),
  useSafetyScmMeetings: vi.fn(),
  useSafetyScmOpenFindings: vi.fn(),
  useSafetySearch: vi.fn(),
  useSafetySoiCompliance: vi.fn(),
  useSafetySoiInspections: vi.fn(),
}));

const safetyApiMocks = vi.hoisted(() => ({
  acceptIncidentPhase7: vi.fn(),
  createIncidentPhase3ChainOfCustody: vi.fn(),
  createIncidentPhase3EvidenceMatrixRow: vi.fn(),
  createIncidentPhase3Interview: vi.fn(),
  exportAuditorBundle: vi.fn(),
  getIncidentPhase3ChainOfCustody: vi.fn(),
  getIncidentPhase3Evidence: vi.fn(),
  getIncidentPhase3EvidenceMatrix: vi.fn(),
  getIncidentPhase2: vi.fn(),
  getIncidentPhase3Interviews: vi.fn(),
  getIncidentPhase7Preflight: vi.fn(),
  getNearMiss: vi.fn(),
  submitIncidentPhase2: vi.fn(),
  triageNearMiss: vi.fn(),
  updateIncidentPhase3Evidence: vi.fn(),
  updateIncidentPhase2: vi.fn(),
}));

vi.mock("@/components/layout/root-layout", () => ({
  RootLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="root-layout">{children}</div>
  ),
}));

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-query")>(
    "@tanstack/react-query",
  );
  return {
    ...actual,
    useMutation: () => ({
      error: null,
      isError: false,
      mutate: vi.fn(),
    }),
  };
});

vi.mock("../../lib/api/safety", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api/safety")>(
    "../../lib/api/safety",
  );
  return {
    ...actual,
    safetyApi: {
      ...actual.safetyApi,
      acceptIncidentPhase7: safetyApiMocks.acceptIncidentPhase7,
      createIncidentPhase3ChainOfCustody: safetyApiMocks.createIncidentPhase3ChainOfCustody,
      createIncidentPhase3EvidenceMatrixRow: safetyApiMocks.createIncidentPhase3EvidenceMatrixRow,
      createIncidentPhase3Interview: safetyApiMocks.createIncidentPhase3Interview,
      exportAuditorBundle: safetyApiMocks.exportAuditorBundle,
      getIncidentPhase3ChainOfCustody: safetyApiMocks.getIncidentPhase3ChainOfCustody,
      getIncidentPhase3Evidence: safetyApiMocks.getIncidentPhase3Evidence,
      getIncidentPhase3EvidenceMatrix: safetyApiMocks.getIncidentPhase3EvidenceMatrix,
      getIncidentPhase2: safetyApiMocks.getIncidentPhase2,
      getIncidentPhase3Interviews: safetyApiMocks.getIncidentPhase3Interviews,
      getIncidentPhase7Preflight: safetyApiMocks.getIncidentPhase7Preflight,
      getNearMiss: safetyApiMocks.getNearMiss,
      submitIncidentPhase2: safetyApiMocks.submitIncidentPhase2,
      triageNearMiss: safetyApiMocks.triageNearMiss,
      updateIncidentPhase3Evidence: safetyApiMocks.updateIncidentPhase3Evidence,
      updateIncidentPhase2: safetyApiMocks.updateIncidentPhase2,
    },
  };
});

vi.mock("../../hooks/use-safety", () => ({
  useSafetyDashboardCaAging: (...args: unknown[]) => safetyQueryMocks.useSafetyDashboardCaAging(...args),
  useSafetyDashboardComposite: (...args: unknown[]) => safetyQueryMocks.useSafetyDashboardComposite(...args),
  useSafetyDashboardHeinrich: (...args: unknown[]) => safetyQueryMocks.useSafetyDashboardHeinrich(...args),
  useSafetyDashboardPareto: (...args: unknown[]) => safetyQueryMocks.useSafetyDashboardPareto(...args),
  useSafetyDashboardRepeatRoot: (...args: unknown[]) => safetyQueryMocks.useSafetyDashboardRepeatRoot(...args),
  useSafetyDashboardSoiCompliance: (...args: unknown[]) => safetyQueryMocks.useSafetyDashboardSoiCompliance(...args),
  useSafetyIncidents: (...args: unknown[]) => safetyQueryMocks.useSafetyIncidents(...args),
  useSafetyNearMisses: (...args: unknown[]) => safetyQueryMocks.useSafetyNearMisses(...args),
  useSafetyScmCreateAdhocConfig: (...args: unknown[]) => safetyQueryMocks.useSafetyScmCreateAdhocConfig(...args),
  useSafetyScmCreateRegularConfig: (...args: unknown[]) => safetyQueryMocks.useSafetyScmCreateRegularConfig(...args),
  useSafetyScmAgenda: (...args: unknown[]) => safetyQueryMocks.useSafetyScmAgenda(...args),
  useSafetyScmAutoFeed: (...args: unknown[]) => safetyQueryMocks.useSafetyScmAutoFeed(...args),
  useSafetyScmClosedSinceLast: (...args: unknown[]) => safetyQueryMocks.useSafetyScmClosedSinceLast(...args),
  useSafetyScmAttendance: (...args: unknown[]) => safetyQueryMocks.useSafetyScmAttendance(...args),
  useSafetyScmMeeting: (...args: unknown[]) => safetyQueryMocks.useSafetyScmMeeting(...args),
  useSafetyScmMeetings: (...args: unknown[]) => safetyQueryMocks.useSafetyScmMeetings(...args),
  useSafetyScmOpenFindings: (...args: unknown[]) => safetyQueryMocks.useSafetyScmOpenFindings(...args),
  useSafetySearch: (...args: unknown[]) => safetyQueryMocks.useSafetySearch(...args),
  useSafetySoiCompliance: (...args: unknown[]) => safetyQueryMocks.useSafetySoiCompliance(...args),
  useSafetySoiInspections: (...args: unknown[]) => safetyQueryMocks.useSafetySoiInspections(...args),
}));

function SafetyRoutesHarness() {
  return useRoutes(safetyRoutes);
}

function renderSafetyRoute(pathname: string, authValue: SafetyAuthUser) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[pathname]}>
        <SafetyAuthProvider value={authValue}>
          <Routes>
            <Route path="/safety/*" element={<SafetyRoutesHarness />} />
          </Routes>
        </SafetyAuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("safety routes", () => {
  beforeEach(() => {
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:safety-export"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });
    HTMLAnchorElement.prototype.click = vi.fn();

    safetyApiMocks.getIncidentPhase2.mockResolvedValue({
      advisory_band: "YELLOW",
      created_by: "co-1",
      created_date: "2026-05-08T00:00:00Z",
      current_phase: 2,
      draft_reference: null,
      dpa_notified_at: null,
      fm_notified_at: null,
      id: 42,
      imo_classifier: "MI",
      incident_number: "INC-42",
      latitude: "1.0",
      longitude: "2.0",
      notification_channel_count: 0,
      office_notified_at: null,
      pic_user_id: "pic-1",
      resources_allocated: null,
      risk_band: "YELLOW",
      schema_version: 1,
      state: "PHASE_2",
      updated_by: null,
      updated_date: null,
    });
    safetyApiMocks.updateIncidentPhase2.mockResolvedValue({
      id: 42,
      state: "PHASE_2",
    });
    safetyApiMocks.submitIncidentPhase2.mockResolvedValue({
      advisory_band: "YELLOW",
      created_by: "co-1",
      created_date: "2026-05-08T00:00:00Z",
      current_phase: 3,
      deadline_tasks_created: 0,
      draft_reference: null,
      dpa_notified_at: "2026-05-08T00:00:00Z",
      fm_notified_at: null,
      id: 42,
      imo_classifier: "MI",
      incident_number: "INC-42",
      latitude: "1.0",
      longitude: "2.0",
      notification_channel_count: 1,
      notifications_emitted: 1,
      office_notified_at: "2026-05-08T00:00:00Z",
      pic_user_id: "pic-1",
      resources_allocated: "DPA assigned",
      risk_band: "YELLOW",
      schema_version: 1,
      state: "PHASE_3",
      transition: {
        incident_id: 42,
        occurred_at: "2026-05-08T00:00:00Z",
        phase_from: 2,
        phase_to: 3,
        transition_type: "FORWARD",
      },
      updated_by: "dpa-1",
      updated_date: "2026-05-08T00:00:00Z",
    });
    safetyApiMocks.getIncidentPhase3Evidence.mockResolvedValue({
      chain_of_custody: [],
      deadline_tasks: [],
      evidence_matrix: [],
      people: {
        entry_count: 1,
        na_justification: null,
        status_chip: "IN_PROGRESS",
        structured_data: {},
        summary: "Witness interview loaded from backend",
        tab_code: "PEOPLE",
      },
      witness_interviews: [
        {
          id: 7,
          interview_status: "DONE",
          witness_name: "Backend Witness",
        },
      ],
    });
    safetyApiMocks.getIncidentPhase3ChainOfCustody.mockResolvedValue([
      {
        collection_timestamp: "2026-05-08T00:00:00Z",
        collector_name: "DPA One",
        collector_signature: "DPA One",
        current_holder: "DPA One",
        description: "Sealed valve sample",
        handover_log: [],
        id: 3,
        storage_location: "Evidence locker A",
        witness_signature: "Witness One",
      },
    ]);
    safetyApiMocks.getIncidentPhase3EvidenceMatrix.mockResolvedValue([
      {
        comments: "Contradiction review started",
        con_evidence: "Alarm timeline conflicts with first statement",
        finding: "Valve isolation delayed",
        id: 4,
        pro_evidence: "Witness interview loaded from backend",
        source_label: "People tab",
      },
    ]);
    safetyApiMocks.getIncidentPhase3Interviews.mockResolvedValue([
      {
        copy_to_witness_recorded: true,
        id: 7,
        interview_type: "FORMAL",
        is_final: true,
        meeting_notes: "Interview notes loaded from backend",
        phase_count: 4,
        read_back_confirmed: true,
        witness_name: "Backend Witness",
        witness_signature: "Backend Witness",
      },
    ]);
    safetyApiMocks.updateIncidentPhase3Evidence.mockResolvedValue({
      people: {
        entry_count: 1,
        status_chip: "IN_PROGRESS",
        summary: "Updated backend people evidence",
        tab_code: "PEOPLE",
      },
    });
    safetyApiMocks.getIncidentPhase7Preflight.mockResolvedValue({
      bias_guards_resolved: true,
      blockers: [],
      closer_role: "DPA",
      current_phase: 7,
      generated_at: "2026-05-08T00:00:00Z",
      incident_id: 42,
      pdf_preview: {
        available: true,
        download_path: "/api/safety/export/incident/42/pdf/",
      },
      ready_for_acceptance: true,
      required_process_id: "SAF_P_004",
      risk_band: "YELLOW",
      signature_chain_status: {
        dpa: { present: false, required: true },
        fm: { present: false, required: false },
        hod: { present: true, required: true },
        master: { present: true, required: true },
        pic: { present: false, required: false },
        reporter: { present: true, required: true },
      },
    });
    safetyApiMocks.acceptIncidentPhase7.mockResolvedValue({
      current_phase: 8,
      id: 42,
      state: "PHASE_8",
    });
    safetyApiMocks.getNearMiss.mockResolvedValue({
      id: 99,
      incident_number: "NM-BACKEND-0099",
      near_miss_priority: "LOW",
      reporter_name: null,
      state: "SUBMITTED",
      vessel_id: "vessel-1",
      visibility_rule: "Reporter identity is masked by backend serializer policy.",
    });
    safetyApiMocks.triageNearMiss.mockResolvedValue({
      id: 99,
      incident_number: "NM-BACKEND-0099",
      near_miss_priority: "HIGH",
      state: "OFFICE_COMMENTS_COMPLETED",
      office_comments_phase_log: {
        transition_type: "FORWARD",
      },
    });
    safetyApiMocks.exportAuditorBundle.mockResolvedValue({
      blob: new Blob(["zip"], { type: "application/zip" }),
      fileName: "safety-auditor-bundle.zip",
    });

    const successState = { data: [], error: null, isLoading: false };
    safetyQueryMocks.useSafetyDashboardComposite.mockReturnValue({
      data: {
        available_vessels: [],
        component_scores: {
          open_findings: 100,
          open_incidents: 100,
          open_near_misses: 100,
          overdue_corrective_actions: 100,
          soi_compliance: 100,
        },
        composite_score: 100,
        metrics: {
          open_findings: 0,
          open_incidents: 0,
          open_near_misses: 0,
          overdue_corrective_actions: 0,
          soi_compliance_display: "100%",
          soi_compliance_label: "SOI Compliance %",
          soi_compliance_percent: 100,
        },
        period_code: "3Y",
        scope_id: "vessel-1",
        scope_type: "VESSEL",
        score_status: "GREEN",
        window_end: "2026-05-06",
        window_start: "2023-05-08",
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardHeinrich.mockReturnValue({
      data: {
        confidence: {
          incident_count_12m: 0,
          near_miss_count_12m: 0,
          reason: "Insufficient data",
          status: "RED",
          tooltip: "Insufficient data",
        },
        layers: [],
        reporting_culture_gap: { is_gap: false, message: "Reporting layers are present." },
        scope_id: "vessel-1",
        scope_type: "VESSEL",
        window_end: "2026-05-06",
        window_start: "2023-05-08",
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardRepeatRoot.mockReturnValue({
      data: {
        fleet: [],
        minimum_repeat_count: 3,
        scope_id: "vessel-1",
        scope_type: "VESSEL",
        vessel: [],
        window_end: "2026-05-06",
        window_start: "2025-11-05",
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardPareto.mockReturnValue({
      data: {
        entries: [],
        scope_id: "vessel-1",
        scope_type: "VESSEL",
        top_n: 10,
        total_occurrences: 0,
        window_end: "2026-05-06",
        window_start: "2025-05-07",
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardSoiCompliance.mockReturnValue({
      data: {
        current_vessel: {
          applicable_area_count: 0,
          compliance_percent: null,
          display_value: "N/A - awaiting first cycle",
          inspected_area_count: 0,
          overdue_area_count: 0,
          status: "NA",
          vessel_id: "vessel-1",
        },
        fleet_average: {
          compliance_percent: null,
          display_value: "N/A - awaiting first cycle",
          note: "Awaiting data.",
          vessel_count: 0,
        },
        label: "SOI Compliance %",
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardCaAging.mockReturnValue({
      data: {
        buckets: [],
        label: "CA Aging Pipeline",
        note: "Clock starts at CA creation date.",
        oldest_age_days: 0,
        open_action_count: 0,
        scope_id: "vessel-1",
        scope_type: "VESSEL",
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmMeetings.mockReturnValue({
      data: [],
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmMeeting.mockReturnValue({
      data: {
        ad_hoc_trigger_reason: null,
        cadence_warning: null,
        chair_crew_id: "master-7",
        created_by: "co-7",
        created_date: "2026-05-08T00:00:00Z",
        id: 2,
        location: "Bridge",
        master_signed_off_at: null,
        master_signed_off_by: null,
        meeting_date: "2026-05-08",
        meeting_time_local: "10:00:00",
        meeting_type: "REGULAR",
        office_comment: null,
        prepared_by_crew_id: "co-7",
        schema_version: 1,
        scm_number: "SCM-002",
        sections: [
          {
            agenda_item_number: 1,
            auto_populated: false,
            content: "Monthly safety review notes.",
            decision: "Continue weekly toolbox talks.",
            id: 501,
            section_label: "Structured Review",
          },
        ],
        state: "DRAFT",
        updated_by: null,
        updated_date: null,
        vessel_id: "vessel-7",
        voyage_no: null,
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmAgenda.mockReturnValue({
      data: {
        carried_forward_items: [],
        meeting_date: "2026-05-08",
        meeting_id: 2,
        meeting_state: "DRAFT",
        meeting_type: "REGULAR",
        rows: [],
        summary: {
          carried_forward_count: 0,
          current_action_item_count: 0,
          open_action_item_count: 0,
        },
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmClosedSinceLast.mockReturnValue({
      data: {
        cutoff: null,
        empty_message: "Nothing closed since last SCM.",
        items: [],
        summary: {
          corrective_action_count: 0,
          incident_count: 0,
          near_miss_count: 0,
          soi_finding_count: 0,
          total_count: 0,
        },
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmAutoFeed.mockReturnValue({
      data: {
        carried_forward_findings: [],
        new_findings: [],
        section8: {
          answer: "NO",
          applicable_area_count: 0,
          coverage_percent: 0,
          inspected_area_count: 0,
          inspection_count: 0,
          summary_text: "No reported SOI inspections yet.",
        },
        summary: {
          carried_forward_count: 0,
          new_count: 0,
          total_count: 0,
        },
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmAttendance.mockReturnValue({
      data: {
        meeting_date: "2026-05-08",
        meeting_id: 42,
        meeting_state: "DRAFT",
        rows: [
          {
            absence_reason: null,
            crew_id: "co-7",
            display_name: "Chief Officer Seven",
            present: true,
            rank_name: "CO",
            remarks: null,
            schema_version: 1,
            wrh_data_available: true,
            wrh_flag: "GREEN",
            wrh_non_compliance_flag: false,
            wrh_rest_hours_24h: "10.50",
            wrh_rest_hours_7d: "80.00",
          },
        ],
        timezone_offset_minutes: 330,
        warnings: [],
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmCreateRegularConfig.mockReturnValue({
      data: {
        attendee_rows: [
          {
            absence_reason: null,
            crew_id: "co-7",
            department: "DECK",
            display_name: "Chief Officer Seven",
            present: true,
            rank_name: "CO",
            remarks: "",
            schema_version: 1,
            warning_codes: [],
            warnings: [],
            wrh_data_available: true,
            wrh_flag: "GREEN",
            wrh_non_compliance_flag: false,
            wrh_rest_hours_24h: 10,
            wrh_rest_hours_7d: 80,
          },
        ],
        cadence_status: {
          days_since_last_regular_closure: 12,
          is_overdue: false,
          last_regular_closed_at: "2026-04-26T00:00:00Z",
          next_due_date: "2026-05-26",
        },
        cadence_warning: null,
        chair: {
          crew_id: "master-7",
          crew_name: "Master Seven",
          department: "DECK",
          rank: "MASTER",
        },
        closed_since_last: {
          cutoff: null,
          empty_message: "Nothing closed since last SCM.",
          items: [],
          meeting_id: null,
          summary: {
            corrective_action_count: 0,
            incident_count: 0,
            near_miss_count: 0,
            soi_finding_count: 0,
            total_count: 0,
          },
          upper_bound_at: "2026-05-08T00:00:00Z",
          vessel_id: "vessel-1",
        },
        generated_at: "2026-05-08T00:00:00Z",
        meeting_date_default: "2026-05-08",
        meeting_type: "REGULAR",
        overdue_soi_areas: [],
        prepared_by: {
          crew_id: "co-7",
          crew_name: "Chief Officer Seven",
          department: "DECK",
          rank: "CO",
        },
        sections: [],
        unresolved_previous_actions: [],
        vessel: {
          id: "vessel-1",
          vessel_code: "MV01",
          vessel_name: "Atlas",
        },
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmCreateAdhocConfig.mockReturnValue({
      data: {
        attendee_rows: [],
        cadence_status: {
          days_since_last_regular_closure: null,
          is_overdue: false,
          last_regular_closed_at: null,
          next_due_date: null,
        },
        cadence_warning: null,
        chair: {
          crew_id: "master-7",
          crew_name: "Master Seven",
          department: "DECK",
          rank: "MASTER",
        },
        closed_since_last: {
          cutoff: null,
          empty_message: "Nothing closed since last SCM.",
          items: [],
          meeting_id: null,
          summary: {
            corrective_action_count: 0,
            incident_count: 0,
            near_miss_count: 0,
            soi_finding_count: 0,
            total_count: 0,
          },
          upper_bound_at: "2026-05-08T00:00:00Z",
          vessel_id: "vessel-1",
        },
        generated_at: "2026-05-08T00:00:00Z",
        meeting_date_default: "2026-05-08",
        meeting_type: "AD_HOC",
        overdue_soi_areas: [],
        prepared_by: {
          crew_id: "master-7",
          crew_name: "Master Seven",
          department: "DECK",
          rank: "MASTER",
        },
        sections: [],
        unresolved_previous_actions: [],
        vessel: {
          id: "vessel-1",
          vessel_code: "MV01",
          vessel_name: "Atlas",
        },
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmOpenFindings.mockReturnValue({
      data: {
        carried_forward_findings: [],
        cutoff: null,
        empty_message: "Nothing closed since last SCM.",
        meeting_id: null,
        new_findings: [],
        section8: {
          answer: "NO",
          applicable_area_count: 0,
          coverage_percent: 0,
          inspected_area_count: 0,
          inspection_count: 0,
          summary_text: "No reported SOI inspections yet.",
        },
        summary: {
          carried_forward_count: 0,
          new_count: 0,
          total_count: 0,
        },
        vessel_id: "vessel-1",
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyIncidents.mockReturnValue(successState);
    safetyQueryMocks.useSafetyNearMisses.mockReturnValue(successState);
    safetyQueryMocks.useSafetySoiCompliance.mockReturnValue({
      data: {
        amber_area_count: 0,
        applicable_area_count: 0,
        areas: [],
        calculated_at: "2026-05-06T00:00:00Z",
        compliance_percent: null,
        display_value: "N/A - awaiting first cycle",
        inspected_area_count: 0,
        label: "SOI Compliance %",
        overdue_area_count: 0,
        status: "NA",
        vessel_id: "vessel-1",
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetySoiInspections.mockReturnValue(successState);
    safetyQueryMocks.useSafetySearch.mockReturnValue({
      data: null,
      error: null,
      isLoading: false,
    });
  });

  it("renders_dashboard_route_inside_safety_layout", async () => {
    renderSafetyRoute("/safety/dashboard", {
      formIds: ["SAF_F_015"],
      id: "user-1",
      isGlobal: false,
      processIds: [],
      role: "DPA",
      vesselIds: ["vessel-1"],
    });

    expect(await screen.findByText("Safety Intelligence Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("safety-layout")).toBeInTheDocument();
  });

  it("wires_vessel_selector_for_global_dashboard_scope", async () => {
    safetyQueryMocks.useSafetyDashboardComposite.mockImplementation(
      (_period: unknown, vesselId?: string | null) => ({
        data: {
          available_vessels: [
            { id: "vessel-1", vessel_code: "MV01", vessel_name: "Atlas" },
            { id: "vessel-2", vessel_code: "MV02", vessel_name: "Beacon" },
          ],
          component_scores: {
            open_findings: 100,
            open_incidents: 100,
            open_near_misses: 100,
            overdue_corrective_actions: 100,
            soi_compliance: 100,
          },
          composite_score: 100,
          metrics: {
            open_findings: 0,
            open_incidents: 0,
            open_near_misses: 0,
            overdue_corrective_actions: 0,
            soi_compliance_display: "100%",
            soi_compliance_label: "SOI Compliance %",
            soi_compliance_percent: 100,
          },
          period_code: "3Y",
          scope_id: vesselId || "",
          scope_type: vesselId ? "VESSEL" : "FLEET",
          score_status: "GREEN",
          window_end: "2026-05-06",
          window_start: "2023-05-08",
        },
        error: null,
        isLoading: false,
      }),
    );

    renderSafetyRoute("/safety/dashboard", {
      formIds: ["SAF_F_015"],
      id: "user-1",
      isGlobal: true,
      processIds: [],
      role: "DPA",
      vesselIds: [],
    });

    await screen.findByText("Safety Intelligence Dashboard");
    expect(screen.getByLabelText("Select vessel drill-down")).toBeInTheDocument();
    expect(screen.getByText("Scope: Fleet scope")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Select vessel drill-down"), {
      target: { value: "vessel-2" },
    });

    await waitFor(() => {
      expect(safetyQueryMocks.useSafetyDashboardHeinrich).toHaveBeenLastCalledWith("vessel-2");
    });
    expect(screen.getByText("Scope: MV02 - Beacon")).toBeInTheDocument();
  });

  it("redirects_safety_index_to_first_available_route", async () => {
    safetyQueryMocks.useSafetyScmMeetings.mockReturnValue({
      data: [
        {
          cadence_warning: null,
          chair_crew_id: "master-1",
          created_by: null,
          created_date: "2026-05-06T00:00:00Z",
          id: 1,
          location: "Bridge",
          master_signed_off_at: null,
          master_signed_off_by: null,
          meeting_date: "2026-05-06",
          meeting_time_local: null,
          meeting_type: "REGULAR",
          office_comment: null,
          prepared_by_crew_id: "co-1",
          schema_version: 1,
          scm_number: "SCM-001",
          sections: [],
          state: "DRAFT",
          updated_by: null,
          updated_date: "2026-05-06T00:00:00Z",
          vessel_id: "vessel-7",
          voyage_no: null,
          ad_hoc_trigger_reason: null,
        },
      ],
      error: null,
      isLoading: false,
    });
    renderSafetyRoute("/safety", {
      formIds: ["SAF_F_003"],
      id: "user-2",
      isGlobal: false,
      processIds: [],
      role: "MASTER",
      vesselIds: ["vessel-7"],
    });

    expect(await screen.findByText("Safety Committee Meetings")).toBeInTheDocument();
  });

  it("fetches_incident_register_with_incident_record_type_filter", async () => {
    renderSafetyRoute("/safety/incidents", {
      formIds: ["SAF_F_001"],
      id: "dpa-register",
      isGlobal: true,
      processIds: [],
      role: "DPA",
      vesselIds: [],
    });

    await screen.findByText("Safety Incidents");
    expect(safetyQueryMocks.useSafetyIncidents).toHaveBeenLastCalledWith({
      record_type: "INCIDENT",
      risk_band: undefined,
      state: undefined,
      vessel_id: undefined,
    });
  });

  it("links_phase_3_incidents_to_the_default_people_tab", async () => {
    safetyQueryMocks.useSafetyIncidents.mockReturnValue({
      data: [
        {
          current_phase: 3,
          draft_reference: null,
          id: 42,
          incident_number: "INC-42",
          occurred_at: "2026-05-08T00:00:00Z",
          reported_at: "2026-05-08T00:00:00Z",
          risk_band: "YELLOW",
          state: "PHASE_3",
          vessel_id: "MV01",
        },
      ],
      error: null,
      isLoading: false,
    });

    renderSafetyRoute("/safety/incidents", {
      formIds: ["SAF_F_001"],
      id: "pic-register",
      isGlobal: true,
      processIds: [],
      role: "PIC",
      vesselIds: [],
    });

    const link = await screen.findByRole("link", { name: "INC-42" });
    expect(link).toHaveAttribute("href", "/safety/incidents/42/phase-3/people");
  });

  it("renders_scm_register_when_sections_are_missing_from_backend_row", async () => {
    safetyQueryMocks.useSafetyScmMeetings.mockReturnValue({
      data: [
        {
          cadence_warning: null,
          chair_crew_id: "master-1",
          created_by: null,
          created_date: "2026-05-06T00:00:00Z",
          id: 7,
          location: "Bridge",
          master_signed_off_at: null,
          master_signed_off_by: null,
          meeting_date: "2026-05-06",
          meeting_time_local: null,
          meeting_type: "REGULAR",
          office_comment: null,
          prepared_by_crew_id: "co-1",
          schema_version: 1,
          scm_number: "SCM-007",
          state: "DRAFT",
          updated_by: null,
          updated_date: "2026-05-06T00:00:00Z",
          vessel_id: "vessel-7",
          voyage_no: null,
          ad_hoc_trigger_reason: null,
        },
      ],
      error: null,
      isLoading: false,
    });

    renderSafetyRoute("/safety/scm", {
      formIds: ["SAF_F_003"],
      id: "dpa-scm",
      isGlobal: true,
      processIds: [],
      role: "DPA",
      vesselIds: [],
    });

    expect(await screen.findAllByText("SCM-007")).toHaveLength(2);
    expect(screen.getByText("0 section(s)")).toBeInTheDocument();
  });

  it("renders_scm_detail_for_office_user_without_signoff_action", async () => {
    renderSafetyRoute("/safety/scm/2", {
      formIds: ["SAF_F_003"],
      id: "office-pic",
      isGlobal: false,
      processIds: [],
      role: "OFFICE_PIC",
      vesselIds: ["vessel-7"],
    });

    expect(await screen.findByText("SCM Detail")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open attendance" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Edit Meeting" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open closed-since-last route" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Open sign-off route" })).not.toBeInTheDocument();
  });

  it("shows_edit_meeting_action_for_vessel_meeting_hosts_before_office_review", async () => {
    renderSafetyRoute("/safety/scm/2", {
      formIds: ["SAF_F_003"],
      id: "co-scm",
      isGlobal: false,
      processIds: ["SAF_P_002"],
      role: "CO",
      vesselIds: ["vessel-7"],
    });

    expect(await screen.findByText("SCM Detail")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Edit Meeting" })).toBeInTheDocument();
  });

  it("passes_scoped_vessel_into_regular_scm_create_queries", async () => {
    renderSafetyRoute("/safety/scm/create-regular", {
      formIds: ["SAF_F_003"],
      id: "user-4",
      isGlobal: false,
      processIds: ["SAF_P_001"],
      role: "CO",
      vesselIds: ["EF9029C2-A192-EF11-A9F2-933342524037"],
    });

    await screen.findByText("Create Regular SCM");
    expect(safetyQueryMocks.useSafetyScmCreateRegularConfig).toHaveBeenLastCalledWith(
      "EF9029C2-A192-EF11-A9F2-933342524037",
    );
    expect(safetyQueryMocks.useSafetyScmOpenFindings).toHaveBeenLastCalledWith(
      "EF9029C2-A192-EF11-A9F2-933342524037",
    );
  });

  it("allows_master_to_open_regular_scm_create_route", async () => {
    renderSafetyRoute("/safety/scm/create-regular", {
      formIds: ["SAF_F_003"],
      id: "master-regular",
      isGlobal: false,
      processIds: ["SAF_P_001"],
      role: "MASTER",
      vesselIds: ["vessel-1"],
    });

    expect(await screen.findByText("Create Regular SCM")).toBeInTheDocument();
    expect(screen.queryByText("Your role cannot open this page.")).not.toBeInTheDocument();
  });

  it("allows_co_to_open_adhoc_scm_create_route", async () => {
    renderSafetyRoute("/safety/scm/create-adhoc", {
      formIds: ["SAF_F_003"],
      id: "co-adhoc",
      isGlobal: false,
      processIds: ["SAF_P_001"],
      role: "CO",
      vesselIds: ["vessel-1"],
    });

    expect(await screen.findByText("Create Ad-Hoc SCM")).toBeInTheDocument();
    expect(screen.queryByText("Your role cannot open this page.")).not.toBeInTheDocument();
  });

  it("renders_auto_filled_regular_scm_context", async () => {
    renderSafetyRoute("/safety/scm/create-regular", {
      formIds: ["SAF_F_003"],
      id: "user-5",
      isGlobal: false,
      processIds: ["SAF_P_001"],
      role: "CO",
      vesselIds: ["vessel-1"],
    });

    await screen.findByText("Create Regular SCM");
    expect(screen.getByText("MV01 - Atlas")).toBeInTheDocument();
    expect(screen.getByText("Crew attendance sheet")).toBeInTheDocument();
    expect(screen.getByText("Closed since previous SCM sign-off")).toBeInTheDocument();
    expect(screen.getByText("Open previous action items")).toBeInTheDocument();
  });

  it("renders_scm_attendance_when_rest_hours_arrive_as_strings", async () => {
    renderSafetyRoute("/safety/scm/42/attendance", {
      formIds: ["SAF_F_003"],
      id: "user-6",
      isGlobal: false,
      processIds: [],
      role: "MASTER",
      vesselIds: ["vessel-1"],
    });

    await screen.findByText("SCM Attendance");
    expect(screen.getByText("10.5 h")).toBeInTheDocument();
    expect(screen.getByText("80.0 h")).toBeInTheDocument();
  });

  it("routes_phase_2_submit_to_live_phase_3_evidence", async () => {
    renderSafetyRoute("/safety/incidents/42/phase-2", {
      formIds: ["SAF_F_001"],
      id: "dpa-1",
      isGlobal: true,
      processIds: [],
      role: "DPA",
      vesselIds: [],
    });

    await screen.findByText("Notifications + Resource Allocation");
    fireEvent.click(screen.getByRole("button", { name: "Submit to office" }));

    expect(await screen.findByText("Phase 3 Evidence Workspace")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "People" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Chain of Custody" })).toBeInTheDocument();
    expect(safetyApiMocks.updateIncidentPhase2).toHaveBeenCalledWith(
      "42",
      expect.objectContaining({
        imo_classifier: "MI",
        risk_band: "YELLOW",
      }),
    );
    expect(safetyApiMocks.submitIncidentPhase2).toHaveBeenCalledWith("42");
    expect(safetyApiMocks.getIncidentPhase3Evidence).toHaveBeenCalledWith("42");
    expect(safetyApiMocks.getIncidentPhase3ChainOfCustody).toHaveBeenCalledWith("42");
    expect(safetyApiMocks.getIncidentPhase3EvidenceMatrix).toHaveBeenCalledWith("42");
    expect(safetyApiMocks.getIncidentPhase3Interviews).toHaveBeenCalledWith("42");
    expect(screen.queryByText("Phase 3 people evidence is not live yet")).not.toBeInTheDocument();
    expect(screen.queryByText("Backend payload")).not.toBeInTheDocument();
    expect(document.querySelector("pre")).not.toBeInTheDocument();
  });

  it("loads_live_incident_phase_7_preflight_from_backend", async () => {
    renderSafetyRoute("/safety/incidents/42/phase-7", {
      formIds: ["SAF_F_001"],
      id: "dpa-1",
      isGlobal: true,
      processIds: [],
      role: "DPA",
      vesselIds: [],
    });

    expect(await screen.findByRole("heading", { name: "Acceptance and Report Issue" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "DPA Acceptance / Report Issued" })).toBeInTheDocument();
    expect(screen.getByText("Required closer:")).toBeInTheDocument();
    expect(screen.getAllByText("DPA").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "PDF Preview" })).toHaveAttribute(
      "href",
      "/api/safety/export/incident/42/pdf/",
    );
    expect(safetyApiMocks.getIncidentPhase7Preflight).toHaveBeenCalledWith("42");
    expect(screen.queryByText("KSM-INC-2026-0042")).not.toBeInTheDocument();
    expect(screen.queryByText("PIC / DPA / FM by band")).not.toBeInTheDocument();
  });

  it("loads_live_incident_phase_3_evidence_from_backend", async () => {
    renderSafetyRoute("/safety/incidents/42/phase-3/people", {
      formIds: ["SAF_F_001"],
      id: "dpa-1",
      isGlobal: true,
      processIds: [],
      role: "DPA",
      vesselIds: [],
    });

    expect(await screen.findByText("Phase 3 Evidence Workspace")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "People" })).toBeInTheDocument();
    expect(screen.getByText("Evidence-Preservation Deadlines")).toBeInTheDocument();
    expect(screen.getAllByText(/Witness interview loaded from backend/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Backend Witness/)).toBeInTheDocument();
    expect(screen.getByText("Health / Fatigue Evidence")).toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase3Evidence).toHaveBeenCalledWith("42");
    expect(safetyApiMocks.getIncidentPhase3ChainOfCustody).toHaveBeenCalledWith("42");
    expect(safetyApiMocks.getIncidentPhase3EvidenceMatrix).toHaveBeenCalledWith("42");
    expect(safetyApiMocks.getIncidentPhase3Interviews).toHaveBeenCalledWith("42");
    expect(screen.queryByText("AB Kumar")).not.toBeInTheDocument();
    expect(screen.queryByText("Ship clinic note")).not.toBeInTheDocument();
    expect(screen.queryByText("Backend payload")).not.toBeInTheDocument();
    expect(document.querySelector("pre")).not.toBeInTheDocument();
  });

  it("renders_bare_phase_3_incident_route_as_people_workspace", async () => {
    renderSafetyRoute("/safety/incidents/42/phase-3", {
      formIds: ["SAF_F_001"],
      id: "pic-1",
      isGlobal: true,
      processIds: [],
      role: "PIC",
      vesselIds: [],
    });

    expect(await screen.findByText("Phase 3 Evidence Workspace")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Evidence Matrix" })).toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase3Evidence).toHaveBeenCalledWith("42");
    expect(screen.queryByText("Backend payload")).not.toBeInTheDocument();
    expect(document.querySelector("pre")).not.toBeInTheDocument();
  });

  it("loads_live_near_miss_office_comments_route_from_backend", async () => {
    renderSafetyRoute("/safety/near-miss/99/office-comments", {
      formIds: ["SAF_F_002"],
      id: "dpa-2",
      isGlobal: true,
      processIds: ["SAF_P_002"],
      role: "DPA",
      vesselIds: [],
    });

    expect(await screen.findByText("Near Miss Office Comments")).toBeInTheDocument();
    expect(await screen.findByText(/NM-BACKEND-0099/)).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Accept" })).toBeInTheDocument();
    expect(safetyApiMocks.getNearMiss).toHaveBeenCalledWith("99");
    expect(screen.queryByText("DRAFT-ABC/2026/T014")).not.toBeInTheDocument();
  });

  it("loads_live_near_miss_export_route_with_backend_masking_note", async () => {
    renderSafetyRoute("/safety/near-miss/99/pdf", {
      formIds: ["SAF_F_002"],
      id: "dpa-3",
      isGlobal: true,
      processIds: ["SAF_P_023"],
      role: "DPA",
      vesselIds: [],
    });

    expect(await screen.findByText("Near Miss PDF Export")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download near-miss PDF" })).toBeInTheDocument();
    expect(safetyApiMocks.getNearMiss).toHaveBeenCalledWith("99");
    expect(screen.queryByText("Reporter visible")).not.toBeInTheDocument();
  });

  it("submits_live_auditor_export_request_to_backend", async () => {
    renderSafetyRoute("/safety/admin/auditor-export", {
      formIds: ["SAF_F_020"],
      id: "dpa-4",
      isGlobal: true,
      processIds: [],
      role: "DPA",
      vesselIds: [],
    });

    expect(await screen.findByText("Auditor Bundle Export")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Build auditor bundle" }));

    await waitFor(() => {
      expect(safetyApiMocks.exportAuditorBundle).toHaveBeenCalledWith(
        expect.objectContaining({
          record_types: expect.arrayContaining(["INCIDENT", "NEAR_MISS", "SOI", "SCM"]),
          vessel_id: null,
        }),
      );
    });
    expect(await screen.findByText("Export prepared: safety-auditor-bundle.zip")).toBeInTheDocument();
    expect(screen.queryByText("Build Demo Bundle Plan")).not.toBeInTheDocument();
    expect(screen.queryByText("Demo Payload")).not.toBeInTheDocument();
  });

  it("shows_permission_fallback_instead_of_blank_screen", async () => {
    renderSafetyRoute("/safety/dashboard", {
      formIds: ["SAF_F_003"],
      id: "user-3",
      isGlobal: false,
      processIds: [],
      role: "MASTER",
      vesselIds: ["vessel-9"],
    });

    expect(
      await screen.findByText("Form access is not available for this page."),
    ).toBeInTheDocument();
  });
});
