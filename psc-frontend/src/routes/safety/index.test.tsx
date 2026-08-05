import type { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { MemoryRouter, Route, Routes, useRoutes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  SafetyAuthProvider,
  type SafetyAuthUser,
} from '../../hooks/safety/use-auth';
import { useAuthStore } from '../../stores/auth-store';
import { safetyRoutes } from './index';

const safetyQueryMocks = vi.hoisted(() => ({
  useSafetyDashboardCaAging: vi.fn(),
  useSafetyDashboardComposite: vi.fn(),
  useSafetyDashboardHeinrich: vi.fn(),
  useSafetyDashboardPareto: vi.fn(),
  useSafetyDashboardRepeatRoot: vi.fn(),
  useSafetyDashboardSoiCompliance: vi.fn(),
  useSafetyIncidents: vi.fn(),
  useSafetyIncidentRegisterVessels: vi.fn(),
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
  downloadIncidentPdf: vi.fn(),
  exportAuditorBundle: vi.fn(),
  createIncidentPhase4Fact: vi.fn(),
  getIncidentPhase3ChainOfCustody: vi.fn(),
  getIncidentPhase3Evidence: vi.fn(),
  getIncidentPhase3EvidenceMatrix: vi.fn(),
  getIncidentPhase1: vi.fn(),
  getIncidentPhase2: vi.fn(),
  getIncidentPhase3Interviews: vi.fn(),
  getIncidentPhase4Facts: vi.fn(),
  getIncidentPhase5Workspace: vi.fn(),
  getIncidentPhase6Workspace: vi.fn(),
  getIncidentPhase7Preflight: vi.fn(),
  getIncidentRegisterVessels: vi.fn(),
  getNearMiss: vi.fn(),
  sendBackIncidentPhase7: vi.fn(),
  submitIncidentPhase2: vi.fn(),
  transitionIncident: vi.fn(),
  triageNearMiss: vi.fn(),
  updateIncidentPhase3AttachmentMetadata: vi.fn(),
  updateIncidentPhase3Evidence: vi.fn(),
  updateIncidentPhase3Interview: vi.fn(),
  updateIncidentPhase2: vi.fn(),
  uploadIncidentPhase3Attachment: vi.fn(),
}));

const mastersApiMocks = vi.hoisted(() => ({
  getVesselCrew: vi.fn(),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: ReactNode }) => (
    <div data-testid="root-layout">{children}</div>
  ),
}));

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>(
    '@tanstack/react-query'
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

vi.mock('../../lib/api/safety', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api/safety')>(
    '../../lib/api/safety'
  );
  return {
    ...actual,
    safetyApi: {
      ...actual.safetyApi,
      acceptIncidentPhase7: safetyApiMocks.acceptIncidentPhase7,
      createIncidentPhase3ChainOfCustody:
        safetyApiMocks.createIncidentPhase3ChainOfCustody,
      createIncidentPhase3EvidenceMatrixRow:
        safetyApiMocks.createIncidentPhase3EvidenceMatrixRow,
      createIncidentPhase3Interview:
        safetyApiMocks.createIncidentPhase3Interview,
      createIncidentPhase4Fact: safetyApiMocks.createIncidentPhase4Fact,
      downloadIncidentPdf: safetyApiMocks.downloadIncidentPdf,
      exportAuditorBundle: safetyApiMocks.exportAuditorBundle,
      getIncidentPhase3ChainOfCustody:
        safetyApiMocks.getIncidentPhase3ChainOfCustody,
      getIncidentPhase3Evidence: safetyApiMocks.getIncidentPhase3Evidence,
      getIncidentPhase3EvidenceMatrix:
        safetyApiMocks.getIncidentPhase3EvidenceMatrix,
      getIncidentPhase1: safetyApiMocks.getIncidentPhase1,
      getIncidentPhase2: safetyApiMocks.getIncidentPhase2,
      getIncidentPhase3Interviews: safetyApiMocks.getIncidentPhase3Interviews,
      getIncidentPhase4Facts: safetyApiMocks.getIncidentPhase4Facts,
      getIncidentPhase5Workspace: safetyApiMocks.getIncidentPhase5Workspace,
      getIncidentPhase6Workspace: safetyApiMocks.getIncidentPhase6Workspace,
      getIncidentPhase7Preflight: safetyApiMocks.getIncidentPhase7Preflight,
      getIncidentRegisterVessels: safetyApiMocks.getIncidentRegisterVessels,
      getNearMiss: safetyApiMocks.getNearMiss,
      sendBackIncidentPhase7: safetyApiMocks.sendBackIncidentPhase7,
      submitIncidentPhase2: safetyApiMocks.submitIncidentPhase2,
      transitionIncident: safetyApiMocks.transitionIncident,
      triageNearMiss: safetyApiMocks.triageNearMiss,
      updateIncidentPhase3AttachmentMetadata:
        safetyApiMocks.updateIncidentPhase3AttachmentMetadata,
      updateIncidentPhase3Evidence: safetyApiMocks.updateIncidentPhase3Evidence,
      updateIncidentPhase3Interview:
        safetyApiMocks.updateIncidentPhase3Interview,
      updateIncidentPhase2: safetyApiMocks.updateIncidentPhase2,
      uploadIncidentPhase3Attachment:
        safetyApiMocks.uploadIncidentPhase3Attachment,
    },
  };
});

vi.mock('../../lib/api/masters', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api/masters')>(
    '../../lib/api/masters'
  );
  return {
    ...actual,
    mastersApi: {
      ...actual.mastersApi,
      getVesselCrew: mastersApiMocks.getVesselCrew,
    },
  };
});

vi.mock('../../hooks/use-safety', () => ({
  useSafetyDashboardCaAging: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyDashboardCaAging(...args),
  useSafetyDashboardComposite: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyDashboardComposite(...args),
  useSafetyDashboardHeinrich: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyDashboardHeinrich(...args),
  useSafetyDashboardPareto: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyDashboardPareto(...args),
  useSafetyDashboardRepeatRoot: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyDashboardRepeatRoot(...args),
  useSafetyDashboardSoiCompliance: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyDashboardSoiCompliance(...args),
  useSafetyIncidents: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyIncidents(...args),
  useSafetyIncidentRegisterVessels: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyIncidentRegisterVessels(...args),
  useSafetyNearMisses: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyNearMisses(...args),
  useSafetyScmCreateAdhocConfig: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmCreateAdhocConfig(...args),
  useSafetyScmCreateRegularConfig: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmCreateRegularConfig(...args),
  useSafetyScmAgenda: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmAgenda(...args),
  useSafetyScmAutoFeed: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmAutoFeed(...args),
  useSafetyScmClosedSinceLast: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmClosedSinceLast(...args),
  useSafetyScmAttendance: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmAttendance(...args),
  useSafetyScmMeeting: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmMeeting(...args),
  useSafetyScmMeetings: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmMeetings(...args),
  useSafetyScmOpenFindings: (...args: unknown[]) =>
    safetyQueryMocks.useSafetyScmOpenFindings(...args),
  useSafetySearch: (...args: unknown[]) =>
    safetyQueryMocks.useSafetySearch(...args),
  useSafetySoiCompliance: (...args: unknown[]) =>
    safetyQueryMocks.useSafetySoiCompliance(...args),
  useSafetySoiInspections: (...args: unknown[]) =>
    safetyQueryMocks.useSafetySoiInspections(...args),
}));

let scrollIntoViewMock: ReturnType<typeof vi.fn>;

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
    </QueryClientProvider>
  );
}

function setOfficeAuthStore(processIds: string[] = ['SAF_P_004']) {
  useAuthStore.setState({
    isAuthenticated: true,
    isInitialized: true,
    isLoading: false,
    tokens: null,
    user: {
      form_ids: ['SAF_F_001'],
      full_name: 'dpa-1',
      id: 'dpa-1',
      process_ids: processIds,
      role: 'DPA',
      username: 'dpa-1',
      vessel_id: null,
    } as never,
  });
}

describe('safety routes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuthStore.setState({
      isAuthenticated: false,
      isInitialized: false,
      isLoading: false,
      tokens: null,
      user: null,
    });

    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn(() => 'blob:safety-export'),
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      value: vi.fn(),
    });
    HTMLAnchorElement.prototype.click = vi.fn();
    scrollIntoViewMock = vi.fn();
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoViewMock,
    });

    safetyApiMocks.getIncidentPhase1.mockResolvedValue({
      id: '42',
      incident_number: 'INC-42',
      narrative: 'Incident narrative',
      record_type: 'INCIDENT',
      state: 'PHASE_4',
      vessel_id: 'VESSEL-42',
    });
    mastersApiMocks.getVesselCrew.mockResolvedValue([
      {
        crew_id: 'CRW001',
        department_name: 'Deck',
        display_name: 'AB - AB Kumar',
        first_name: 'Kumar',
        id: 'crew-row-1',
        rank_name: 'AB',
        surname: '',
      },
      {
        crew_id: 'CRW002',
        department_name: 'Engine',
        display_name: 'Oiler Singh',
        first_name: 'Singh',
        id: 'crew-row-2',
        rank_name: 'Oiler',
        surname: '',
      },
    ]);

    safetyApiMocks.getIncidentPhase2.mockResolvedValue({
      advisory_band: 'YELLOW',
      created_by: 'co-1',
      created_date: '2026-05-08T00:00:00Z',
      current_phase: 2,
      draft_reference: null,
      dpa_notified_at: null,
      fm_notified_at: null,
      id: 42,
      imo_classifier: 'MI',
      incident_number: 'INC-42',
      latitude: '1.0',
      longitude: '2.0',
      notification_channel_count: 0,
      office_notified_at: null,
      pic_user_id: 'pic-1',
      resources_allocated: null,
      risk_band: 'YELLOW',
      schema_version: 1,
      state: 'PHASE_2',
      updated_by: null,
      updated_date: null,
    });
    safetyApiMocks.updateIncidentPhase2.mockResolvedValue({
      id: 42,
      state: 'PHASE_2',
    });
    safetyApiMocks.submitIncidentPhase2.mockResolvedValue({
      advisory_band: 'YELLOW',
      created_by: 'co-1',
      created_date: '2026-05-08T00:00:00Z',
      current_phase: 3,
      deadline_tasks_created: 0,
      draft_reference: null,
      dpa_notified_at: '2026-05-08T00:00:00Z',
      fm_notified_at: null,
      id: 42,
      imo_classifier: 'MI',
      incident_number: 'INC-42',
      latitude: '1.0',
      longitude: '2.0',
      notification_channel_count: 1,
      notifications_emitted: 1,
      office_notified_at: '2026-05-08T00:00:00Z',
      pic_user_id: 'pic-1',
      resources_allocated: 'DPA assigned',
      risk_band: 'YELLOW',
      schema_version: 1,
      state: 'PHASE_3',
      transition: {
        incident_id: 42,
        occurred_at: '2026-05-08T00:00:00Z',
        phase_from: 2,
        phase_to: 3,
        transition_type: 'FORWARD',
      },
      updated_by: 'dpa-1',
      updated_date: '2026-05-08T00:00:00Z',
    });
    safetyApiMocks.getIncidentPhase3Evidence.mockResolvedValue({
      chain_of_custody: [],
      deadline_tasks: [],
      evidence_matrix: [],
      people: {
        entry_count: 1,
        na_justification: null,
        status_chip: 'IN_PROGRESS',
        structured_data: {},
        summary: 'Witness interview loaded from backend',
        tab_code: 'PEOPLE',
      },
      paper: {
        entry_count: 1,
        na_justification: null,
        status_chip: '1 attachment',
        structured_data: {
          attachments: [
            {
              attachment_path: 'incidents/42/phase-3/paper/engine-log.pdf',
              byte_size: 1234,
              content_type: 'application/pdf',
              description:
                'Deck and engine log pages relevant to the incident.',
              file_name: 'engine-log.pdf',
              original_name: 'engine-log.pdf',
              tab_key: 'paper',
              title: 'Engine log extract',
              uploaded_at: '2026-05-08T00:00:00Z',
            },
          ],
        },
        summary: '',
        tab_code: 'PAPER',
      },
      witness_interviews: [
        {
          id: '7',
          interview_status: 'DONE',
          witness_name: 'Backend Witness',
        },
      ],
    });
    safetyApiMocks.getIncidentPhase3ChainOfCustody.mockResolvedValue([
      {
        collection_timestamp: '2026-05-08T00:00:00Z',
        collector_name: 'DPA One',
        collector_signature: 'DPA One',
        current_holder: 'DPA One',
        description: 'Sealed valve sample',
        handover_log: [],
        id: '3',
        storage_location: 'Evidence locker A',
        witness_signature: 'Witness One',
      },
    ]);
    safetyApiMocks.getIncidentPhase3EvidenceMatrix.mockResolvedValue([
      {
        comments: 'Contradiction review started',
        con_evidence: 'Alarm timeline conflicts with first statement',
        finding: 'Valve isolation delayed',
        id: '4',
        pro_evidence: 'Witness interview loaded from backend',
        source_label: 'People tab',
      },
    ]);
    safetyApiMocks.getIncidentPhase3Interviews.mockResolvedValue([
      {
        copy_to_witness_recorded: true,
        conclusion_notes: 'Read back and closed.',
        id: '7',
        interview_type: 'FORMAL',
        is_final: true,
        meeting_notes: 'Interview notes loaded from backend',
        phase_count: 4,
        read_back_confirmed: true,
        witness_name: 'Backend Witness',
        witness_signature: 'Backend Witness',
      },
    ]);
    safetyApiMocks.getIncidentPhase5Workspace.mockResolvedValue({
      analysis_tools_used: ['FACT_TREE'],
      assessment: {
        analysis_tools_used: ['FACT_TREE'],
        confirmation_override_reason: null,
        human_factors_payload: {},
        monocausal_justification: null,
        people_contribution_text: '',
        plant_failure_text: '',
        process_gap_text: '',
      },
      bias_guards: [],
      blame_evaluation: {
        all_root_personal_factors: false,
        blocked: false,
        has_lack_of_control: false,
        override_by: null,
        trigger_terms: [],
      },
      causes: [
        {
          analysis_tool: 'FACT_TREE',
          causal_layer: 'IMMEDIATE',
          cause_factor: 'HUMAN',
          cause_factor_label: 'Human Factor',
          cause_option_id: 'cause-1',
          cause_option_text: 'Procedure not followed',
          cause_other_text: '',
          cause_stage: '',
          mscat_subcode_id: 'M-1',
          rationale: 'Direct reason recorded',
          source_fact_id: 'fact-1',
        },
        {
          analysis_tool: 'FACT_TREE',
          causal_layer: 'INTERMEDIATE',
          cause_factor: 'MANAGEMENT',
          cause_factor_label: 'Management Factor',
          cause_option_id: 'cause-2',
          cause_option_text: 'Supervision gap',
          cause_other_text: '',
          cause_stage: '',
          mscat_subcode_id: 'M-2',
          rationale: 'Deeper reason recorded',
          source_fact_id: 'fact-2',
        },
        {
          analysis_tool: 'FACT_TREE',
          causal_layer: 'ROOT',
          cause_factor: 'VESSEL',
          cause_factor_label: 'Vessel Factor',
          cause_option_id: 'cause-3',
          cause_option_text: 'Equipment design issue',
          cause_other_text: '',
          cause_stage: '',
          mscat_subcode_id: 'M-3',
          rationale: 'Root reason recorded',
          source_fact_id: 'fact-3',
        },
      ],
      facts: [],
      incident_id: '42',
      investigation_depth: 'STANDARD',
      matrix_rows: [],
      minimum_tools_required: 1,
      safeguards: [],
      schema_version: 1,
    });
    safetyApiMocks.getIncidentPhase6Workspace.mockResolvedValue({
      alarp_complete: false,
      bias_guards_complete: true,
      blame_evaluation: {
        all_root_personal_factors: false,
        blocked: false,
        has_lack_of_control: true,
        override_by: null,
        trigger_terms: [],
      },
      corrective_actions: [],
      gate_blockers: [],
      incident_id: '42',
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
    safetyApiMocks.transitionIncident.mockResolvedValue({
      current_phase: 4,
      id: 42,
      state: 'PHASE_4',
    });
    safetyApiMocks.downloadIncidentPdf.mockResolvedValue({
      blob: new Blob(['pdf'], { type: 'application/pdf' }),
      fileName: 'incident-42.pdf',
    });
    safetyApiMocks.updateIncidentPhase3Evidence.mockResolvedValue({
      people: {
        entry_count: 1,
        status_chip: 'IN_PROGRESS',
        summary: 'Updated backend people evidence',
        tab_code: 'PEOPLE',
      },
    });
    safetyApiMocks.uploadIncidentPhase3Attachment.mockResolvedValue({
      attachment: {
        attachment_path: 'incidents/42/phase-3/paper/pump-photo.png',
        description: 'Photo showing the saved pump condition.',
        file_name: 'pump-photo.png',
        original_name: 'pump-photo.png',
        tab_key: 'paper',
        title: 'Pump photo',
        uploaded_at: '2026-05-08T00:05:00Z',
      },
      workspace: {
        deadline_tasks: [],
        paper: {
          entry_count: 2,
          na_justification: null,
          status_chip: '2 attachments',
          structured_data: {
            attachments: [
              {
                attachment_path: 'incidents/42/phase-3/paper/pump-photo.png',
                description: 'Photo showing the saved pump condition.',
                file_name: 'pump-photo.png',
                original_name: 'pump-photo.png',
                tab_key: 'paper',
                title: 'Pump photo',
                uploaded_at: '2026-05-08T00:05:00Z',
              },
            ],
          },
          summary: '',
          tab_code: 'PAPER',
        },
      },
    });
    safetyApiMocks.updateIncidentPhase3AttachmentMetadata.mockResolvedValue({
      attachment: {
        attachment_path: 'incidents/42/phase-3/paper/engine-log.pdf',
        description: 'Updated engine log description.',
        file_name: 'engine-log.pdf',
        original_name: 'engine-log.pdf',
        tab_key: 'paper',
        title: 'Engine log extract',
        uploaded_at: '2026-05-08T00:00:00Z',
      },
      workspace: {
        deadline_tasks: [],
        paper: {
          entry_count: 1,
          na_justification: null,
          status_chip: '1 attachment',
          structured_data: {
            attachments: [
              {
                attachment_path: 'incidents/42/phase-3/paper/engine-log.pdf',
                description: 'Updated engine log description.',
                file_name: 'engine-log.pdf',
                original_name: 'engine-log.pdf',
                tab_key: 'paper',
                title: 'Engine log extract',
                uploaded_at: '2026-05-08T00:00:00Z',
              },
            ],
          },
          summary: '',
          tab_code: 'PAPER',
        },
      },
    });
    safetyApiMocks.updateIncidentPhase3Interview.mockResolvedValue({
      conclusion_notes: 'Updated witness remark.',
      id: '7',
      interview_type: 'INFORMAL',
      meeting_notes: 'Interview notes loaded from backend',
      witness_name: 'Backend Witness',
      witness_signature: 'Backend Witness',
    });
    safetyApiMocks.getIncidentPhase7Preflight.mockResolvedValue({
      bias_guards_resolved: true,
      blockers: [],
      closer_role: 'DPA',
      current_phase: 7,
      generated_at: '2026-05-08T00:00:00Z',
      incident_id: 42,
      pdf_preview: {
        available: true,
        download_path: 'http://localhost:8000/api/safety/export/incident/42/pdf/',
      },
      ready_for_acceptance: true,
      recommendation_tier_count: {
        corrective: 1,
        lessons_learnt: 1,
        preventive: 1,
      },
      required_process_id: 'SAF_P_004',
      risk_band: 'YELLOW',
      root_count: 2,
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
      state: 'PHASE_8',
    });
    safetyApiMocks.sendBackIncidentPhase7.mockResolvedValue({
      current_phase: 6,
      id: 42,
      state: 'SENT_BACK',
    });
    safetyApiMocks.getNearMiss.mockResolvedValue({
      id: 99,
      incident_number: 'NM-BACKEND-0099',
      near_miss_priority: 'LOW',
      reporter_name: null,
      state: 'SUBMITTED',
      vessel_id: 'vessel-1',
      visibility_rule:
        'Reporter identity is masked by backend serializer policy.',
    });
    safetyApiMocks.triageNearMiss.mockResolvedValue({
      id: 99,
      incident_number: 'NM-BACKEND-0099',
      near_miss_priority: 'HIGH',
      state: 'OFFICE_COMMENTS_COMPLETED',
      office_comments_phase_log: {
        transition_type: 'FORWARD',
      },
    });
    safetyApiMocks.exportAuditorBundle.mockResolvedValue({
      blob: new Blob(['zip'], { type: 'application/zip' }),
      fileName: 'safety-auditor-bundle.zip',
    });
    safetyApiMocks.getIncidentRegisterVessels.mockResolvedValue([
      {
        id: 'vessel-1',
        vessel_code: 'YCF',
        vessel_name: 'Yellow Chief',
      },
    ]);

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
          soi_compliance_display: '100%',
          soi_compliance_label: 'SOI Compliance %',
          soi_compliance_percent: 100,
        },
        period_code: '3Y',
        scope_id: 'vessel-1',
        scope_type: 'VESSEL',
        score_status: 'GREEN',
        window_end: '2026-05-06',
        window_start: '2023-05-08',
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardHeinrich.mockReturnValue({
      data: {
        confidence: {
          incident_count_12m: 0,
          near_miss_count_12m: 0,
          reason: 'Insufficient data',
          status: 'RED',
          tooltip: 'Insufficient data',
        },
        layers: [],
        reporting_culture_gap: {
          is_gap: false,
          message: 'Reporting layers are present.',
        },
        scope_id: 'vessel-1',
        scope_type: 'VESSEL',
        window_end: '2026-05-06',
        window_start: '2023-05-08',
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardRepeatRoot.mockReturnValue({
      data: {
        fleet: [],
        minimum_repeat_count: 3,
        scope_id: 'vessel-1',
        scope_type: 'VESSEL',
        vessel: [],
        window_end: '2026-05-06',
        window_start: '2025-11-05',
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardPareto.mockReturnValue({
      data: {
        entries: [],
        scope_id: 'vessel-1',
        scope_type: 'VESSEL',
        top_n: 10,
        total_occurrences: 0,
        window_end: '2026-05-06',
        window_start: '2025-05-07',
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardSoiCompliance.mockReturnValue({
      data: {
        current_vessel: {
          applicable_area_count: 0,
          compliance_percent: null,
          display_value: 'N/A - awaiting first cycle',
          inspected_area_count: 0,
          overdue_area_count: 0,
          status: 'NA',
          vessel_id: 'vessel-1',
        },
        fleet_average: {
          compliance_percent: null,
          display_value: 'N/A - awaiting first cycle',
          note: 'Awaiting data.',
          vessel_count: 0,
        },
        label: 'SOI Compliance %',
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyDashboardCaAging.mockReturnValue({
      data: {
        buckets: [],
        label: 'CA Aging Pipeline',
        note: 'Clock starts at CA creation date.',
        oldest_age_days: 0,
        open_action_count: 0,
        scope_id: 'vessel-1',
        scope_type: 'VESSEL',
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
        chair_crew_id: 'master-7',
        created_by: 'co-7',
        created_date: '2026-05-08T00:00:00Z',
        id: 2,
        location: 'Bridge',
        master_signed_off_at: null,
        master_signed_off_by: null,
        meeting_date: '2026-05-08',
        meeting_time_local: '10:00:00',
        meeting_type: 'REGULAR',
        office_comment: null,
        prepared_by_crew_id: 'co-7',
        schema_version: 1,
        scm_number: 'SCM-002',
        sections: [
          {
            agenda_item_number: 1,
            auto_populated: false,
            content: 'Monthly safety review notes.',
            decision: 'Continue weekly toolbox talks.',
            id: 501,
            section_label: 'Structured Review',
          },
        ],
        state: 'DRAFT',
        updated_by: null,
        updated_date: null,
        vessel_id: 'vessel-7',
        voyage_no: null,
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmAgenda.mockReturnValue({
      data: {
        carried_forward_items: [],
        meeting_date: '2026-05-08',
        meeting_id: 2,
        meeting_state: 'DRAFT',
        meeting_type: 'REGULAR',
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
        empty_message: 'Nothing closed since last SCM.',
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
          answer: 'NO',
          applicable_area_count: 0,
          coverage_percent: 0,
          inspected_area_count: 0,
          inspection_count: 0,
          summary_text: 'No reported SOI inspections yet.',
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
        meeting_date: '2026-05-08',
        meeting_id: 42,
        meeting_state: 'DRAFT',
        rows: [
          {
            absence_reason: null,
            crew_id: 'co-7',
            display_name: 'Chief Officer Seven',
            present: true,
            rank_name: 'CO',
            remarks: null,
            schema_version: 1,
            wrh_data_available: true,
            wrh_flag: 'GREEN',
            wrh_non_compliance_flag: false,
            wrh_rest_hours_24h: '10.50',
            wrh_rest_hours_7d: '80.00',
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
            crew_id: 'co-7',
            department: 'DECK',
            display_name: 'Chief Officer Seven',
            present: true,
            rank_name: 'CO',
            remarks: '',
            schema_version: 1,
            warning_codes: [],
            warnings: [],
            wrh_data_available: true,
            wrh_flag: 'GREEN',
            wrh_non_compliance_flag: false,
            wrh_rest_hours_24h: 10,
            wrh_rest_hours_7d: 80,
          },
        ],
        cadence_status: {
          days_since_last_regular_closure: 12,
          is_overdue: false,
          last_regular_closed_at: '2026-04-26T00:00:00Z',
          next_due_date: '2026-05-26',
        },
        cadence_warning: null,
        chair: {
          crew_id: 'master-7',
          crew_name: 'Master Seven',
          department: 'DECK',
          rank: 'MASTER',
        },
        closed_since_last: {
          cutoff: null,
          empty_message: 'Nothing closed since last SCM.',
          items: [],
          meeting_id: null,
          summary: {
            corrective_action_count: 0,
            incident_count: 0,
            near_miss_count: 0,
            soi_finding_count: 0,
            total_count: 0,
          },
          upper_bound_at: '2026-05-08T00:00:00Z',
          vessel_id: 'vessel-1',
        },
        generated_at: '2026-05-08T00:00:00Z',
        meeting_date_default: '2026-05-08',
        meeting_type: 'REGULAR',
        overdue_soi_areas: [],
        prepared_by: {
          crew_id: 'co-7',
          crew_name: 'Chief Officer Seven',
          department: 'DECK',
          rank: 'CO',
        },
        sections: [],
        unresolved_previous_actions: [],
        vessel: {
          id: 'vessel-1',
          vessel_code: 'MV01',
          vessel_name: 'Atlas',
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
          crew_id: 'master-7',
          crew_name: 'Master Seven',
          department: 'DECK',
          rank: 'MASTER',
        },
        closed_since_last: {
          cutoff: null,
          empty_message: 'Nothing closed since last SCM.',
          items: [],
          meeting_id: null,
          summary: {
            corrective_action_count: 0,
            incident_count: 0,
            near_miss_count: 0,
            soi_finding_count: 0,
            total_count: 0,
          },
          upper_bound_at: '2026-05-08T00:00:00Z',
          vessel_id: 'vessel-1',
        },
        generated_at: '2026-05-08T00:00:00Z',
        meeting_date_default: '2026-05-08',
        meeting_type: 'AD_HOC',
        overdue_soi_areas: [],
        prepared_by: {
          crew_id: 'master-7',
          crew_name: 'Master Seven',
          department: 'DECK',
          rank: 'MASTER',
        },
        sections: [],
        unresolved_previous_actions: [],
        vessel: {
          id: 'vessel-1',
          vessel_code: 'MV01',
          vessel_name: 'Atlas',
        },
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyScmOpenFindings.mockReturnValue({
      data: {
        carried_forward_findings: [],
        cutoff: null,
        empty_message: 'Nothing closed since last SCM.',
        meeting_id: null,
        new_findings: [],
        section8: {
          answer: 'NO',
          applicable_area_count: 0,
          coverage_percent: 0,
          inspected_area_count: 0,
          inspection_count: 0,
          summary_text: 'No reported SOI inspections yet.',
        },
        summary: {
          carried_forward_count: 0,
          new_count: 0,
          total_count: 0,
        },
        vessel_id: 'vessel-1',
      },
      error: null,
      isLoading: false,
    });
    safetyQueryMocks.useSafetyIncidents.mockReturnValue(successState);
    safetyQueryMocks.useSafetyIncidentRegisterVessels.mockReturnValue(successState);
    safetyQueryMocks.useSafetyNearMisses.mockReturnValue(successState);
    safetyQueryMocks.useSafetySoiCompliance.mockReturnValue({
      data: {
        amber_area_count: 0,
        applicable_area_count: 0,
        areas: [],
        calculated_at: '2026-05-06T00:00:00Z',
        compliance_percent: null,
        display_value: 'N/A - awaiting first cycle',
        inspected_area_count: 0,
        label: 'SOI Compliance %',
        overdue_area_count: 0,
        status: 'NA',
        vessel_id: 'vessel-1',
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

  it('renders_dashboard_route_inside_safety_layout', async () => {
    renderSafetyRoute('/safety/dashboard', {
      formIds: ['SAF_F_015'],
      id: 'user-1',
      isGlobal: false,
      processIds: [],
      role: 'DPA',
      vesselIds: ['vessel-1'],
    });

    expect(
      await screen.findByText('Safety Dashboard')
    ).toBeInTheDocument();
    expect(screen.getByTestId('safety-layout')).toBeInTheDocument();
  });

  it('wires_vessel_selector_for_global_dashboard_scope', async () => {
    safetyQueryMocks.useSafetyDashboardComposite.mockImplementation(
      (_period: unknown, vesselId?: string | null) => ({
        data: {
          available_vessels: [
            { id: 'vessel-1', vessel_code: 'MV01', vessel_name: 'Atlas' },
            { id: 'vessel-2', vessel_code: 'MV02', vessel_name: 'Beacon' },
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
            soi_compliance_display: '100%',
            soi_compliance_label: 'SOI Compliance %',
            soi_compliance_percent: 100,
          },
          period_code: '3Y',
          scope_id: vesselId || '',
          scope_type: vesselId ? 'VESSEL' : 'FLEET',
          score_status: 'GREEN',
          window_end: '2026-05-06',
          window_start: '2023-05-08',
        },
        error: null,
        isLoading: false,
      })
    );

    renderSafetyRoute('/safety/dashboard', {
      formIds: ['SAF_F_015'],
      id: 'user-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    await screen.findByText('Safety Dashboard');
    expect(screen.getByLabelText('Choose vessel')).toBeInTheDocument();
    expect(screen.getByText('Scope: Fleet scope')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Choose vessel'), {
      target: { value: 'vessel-2' },
    });

    await waitFor(() => {
      expect(
        safetyQueryMocks.useSafetyDashboardHeinrich
      ).toHaveBeenLastCalledWith('vessel-2');
    });
    expect(screen.getByText('Scope: MV02 - Beacon')).toBeInTheDocument();
  });

  it('redirects_safety_index_to_first_available_route', async () => {
    safetyQueryMocks.useSafetyScmMeetings.mockReturnValue({
      data: [
        {
          cadence_warning: null,
          chair_crew_id: 'master-1',
          created_by: null,
          created_date: '2026-05-06T00:00:00Z',
          id: 1,
          location: 'Bridge',
          master_signed_off_at: null,
          master_signed_off_by: null,
          meeting_date: '2026-05-06',
          meeting_time_local: null,
          meeting_type: 'REGULAR',
          office_comment: null,
          prepared_by_crew_id: 'co-1',
          schema_version: 1,
          scm_number: 'SCM-001',
          sections: [],
          state: 'DRAFT',
          updated_by: null,
          updated_date: '2026-05-06T00:00:00Z',
          vessel_id: 'vessel-7',
          voyage_no: null,
          ad_hoc_trigger_reason: null,
        },
      ],
      error: null,
      isLoading: false,
    });
    renderSafetyRoute('/safety', {
      formIds: ['SAF_F_003'],
      id: 'user-2',
      isGlobal: false,
      processIds: [],
      role: 'MASTER',
      vesselIds: ['vessel-7'],
    });

    expect(
      await screen.findByText('Safety Committee Meetings')
    ).toBeInTheDocument();
  });

  it('fetches_incident_register_with_incident_record_type_filter', async () => {
    renderSafetyRoute('/safety/incidents', {
      formIds: ['SAF_F_001'],
      id: 'dpa-register',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    await screen.findByText('Safety Incidents');
    expect(safetyQueryMocks.useSafetyIncidents).toHaveBeenLastCalledWith({
      record_type: 'INCIDENT',
      risk_band: undefined,
      state: undefined,
      vessel_id: undefined,
    });
  });

  it('filters_the_incident_register_by_selected_vessel_and_uses_current_labels', async () => {
    safetyQueryMocks.useSafetyIncidentRegisterVessels.mockReturnValue({
      data: [
        {
          id: 'vessel-ycf',
          vessel_code: 'YCF',
          vessel_name: 'YC FORTITUDE',
        },
        {
          id: 'vessel-eat',
          vessel_code: 'EAT',
          vessel_name: 'EAST AYUTTHAYA',
        },
      ],
      error: null,
      isLoading: false,
    });

    renderSafetyRoute('/safety/incidents', {
      formIds: ['SAF_F_001'],
      id: 'dpa-register',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    await screen.findByText('Safety Incidents');

    expect(screen.getByText('risk_band')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Vessel'), {
      target: { value: 'vessel-ycf' },
    });

    await waitFor(() => {
      expect(safetyQueryMocks.useSafetyIncidents).toHaveBeenLastCalledWith({
        record_type: 'INCIDENT',
        risk_band: undefined,
        state: undefined,
        vessel_id: 'vessel-ycf',
      });
    });
  });

  it('does_not_show_the_current_scope_card_on_the_incident_register', async () => {
    renderSafetyRoute('/safety/incidents', {
      formIds: ['SAF_F_001'],
      id: 'dpa-register',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    await screen.findByText('Safety Incidents');

    expect(screen.queryByText('Current Scope')).toBeNull();
    expect(
      screen.queryByText('Records are shown for your current vessel scope.')
    ).toBeNull();
  });

  it('links_phase_4_incidents_to_the_documents_evidence_route', async () => {
    safetyQueryMocks.useSafetyIncidents.mockReturnValue({
      data: [
        {
          current_phase: 4,
          draft_reference: null,
          id: 42,
          incident_number: 'INC-42',
          occurred_at: '2026-05-08T00:00:00Z',
          reported_at: '2026-05-08T00:00:00Z',
          risk_band: 'YELLOW',
          state: 'PHASE_4',
          vessel_id: 'MV01',
        },
      ],
      error: null,
      isLoading: false,
    });

    renderSafetyRoute('/safety/incidents', {
      formIds: ['SAF_F_001'],
      id: 'pic-register',
      isGlobal: true,
      processIds: [],
      role: 'PIC',
      vesselIds: [],
    });

    const link = await screen.findByRole('link', { name: 'INC-42' });
    expect(link).toHaveAttribute('href', '/safety/incidents/42/phase-4/paper');
  });

  it('renders_scm_register_when_sections_are_missing_from_backend_row', async () => {
    safetyQueryMocks.useSafetyScmMeetings.mockReturnValue({
      data: [
        {
          cadence_warning: null,
          chair_crew_id: 'master-1',
          created_by: null,
          created_date: '2026-05-06T00:00:00Z',
          id: 7,
          location: 'Bridge',
          master_signed_off_at: null,
          master_signed_off_by: null,
          meeting_date: '2026-05-06',
          meeting_time_local: null,
          meeting_type: 'REGULAR',
          office_comment: null,
          prepared_by_crew_id: 'co-1',
          schema_version: 1,
          scm_number: 'SCM-007',
          state: 'DRAFT',
          updated_by: null,
          updated_date: '2026-05-06T00:00:00Z',
          vessel_id: 'vessel-7',
          voyage_no: null,
          ad_hoc_trigger_reason: null,
        },
      ],
      error: null,
      isLoading: false,
    });

    renderSafetyRoute('/safety/scm', {
      formIds: ['SAF_F_003'],
      id: 'dpa-scm',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(await screen.findAllByText('SCM-007')).toHaveLength(2);
    expect(screen.getByText('0 section(s)')).toBeInTheDocument();
  });

  it('renders_scm_detail_for_office_user_without_signoff_action', async () => {
    renderSafetyRoute('/safety/scm/2', {
      formIds: ['SAF_F_003'],
      id: 'office-pic',
      isGlobal: false,
      processIds: [],
      role: 'OFFICE_PIC',
      vesselIds: ['vessel-7'],
    });

    expect(await screen.findByText('SCM Detail')).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Open attendance' })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Edit Meeting' })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Open closed-since-last route' })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Open sign-off route' })
    ).not.toBeInTheDocument();
  });

  it('shows_edit_meeting_action_for_vessel_meeting_hosts_before_office_review', async () => {
    renderSafetyRoute('/safety/scm/2', {
      formIds: ['SAF_F_003'],
      id: 'co-scm',
      isGlobal: false,
      processIds: ['SAF_P_002'],
      role: 'CO',
      vesselIds: ['vessel-7'],
    });

    expect(await screen.findByText('SCM Detail')).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Edit Meeting' })
    ).toBeInTheDocument();
  });

  it('passes_scoped_vessel_into_regular_scm_create_queries', async () => {
    renderSafetyRoute('/safety/scm/create-regular', {
      formIds: ['SAF_F_003'],
      id: 'user-4',
      isGlobal: false,
      processIds: ['SAF_P_001'],
      role: 'CO',
      vesselIds: ['EF9029C2-A192-EF11-A9F2-933342524037'],
    });

    await screen.findByText('Create Regular SCM');
    expect(
      safetyQueryMocks.useSafetyScmCreateRegularConfig
    ).toHaveBeenLastCalledWith('EF9029C2-A192-EF11-A9F2-933342524037');
    expect(safetyQueryMocks.useSafetyScmOpenFindings).toHaveBeenLastCalledWith(
      'EF9029C2-A192-EF11-A9F2-933342524037'
    );
  });

  it('allows_master_to_open_regular_scm_create_route', async () => {
    renderSafetyRoute('/safety/scm/create-regular', {
      formIds: ['SAF_F_003'],
      id: 'master-regular',
      isGlobal: false,
      processIds: ['SAF_P_001'],
      role: 'MASTER',
      vesselIds: ['vessel-1'],
    });

    expect(await screen.findByText('Create Regular SCM')).toBeInTheDocument();
    expect(
      screen.queryByText('Your role cannot open this page.')
    ).not.toBeInTheDocument();
  });

  it('allows_co_to_open_adhoc_scm_create_route', async () => {
    renderSafetyRoute('/safety/scm/create-adhoc', {
      formIds: ['SAF_F_003'],
      id: 'co-adhoc',
      isGlobal: false,
      processIds: ['SAF_P_001'],
      role: 'CO',
      vesselIds: ['vessel-1'],
    });

    expect(await screen.findByText('Create Ad-Hoc SCM')).toBeInTheDocument();
    expect(
      screen.queryByText('Your role cannot open this page.')
    ).not.toBeInTheDocument();
  });

  it('renders_auto_filled_regular_scm_context', async () => {
    renderSafetyRoute('/safety/scm/create-regular', {
      formIds: ['SAF_F_003'],
      id: 'user-5',
      isGlobal: false,
      processIds: ['SAF_P_001'],
      role: 'CO',
      vesselIds: ['vessel-1'],
    });

    await screen.findByText('Create Regular SCM');
    expect(screen.getByText('MV01 - Atlas')).toBeInTheDocument();
    expect(screen.getByText('Crew attendance sheet')).toBeInTheDocument();
    expect(
      screen.getByText('Closed since previous SCM sign-off')
    ).toBeInTheDocument();
    expect(screen.getByText('Open previous action items')).toBeInTheDocument();
  });

  it('renders_scm_attendance_when_rest_hours_arrive_as_strings', async () => {
    renderSafetyRoute('/safety/scm/42/attendance', {
      formIds: ['SAF_F_003'],
      id: 'user-6',
      isGlobal: false,
      processIds: [],
      role: 'MASTER',
      vesselIds: ['vessel-1'],
    });

    await screen.findByText('SCM Attendance');
    expect(screen.getByText('10.5 h')).toBeInTheDocument();
    expect(screen.getByText('80.0 h')).toBeInTheDocument();
  });

  it('routes_phase_2_submit_to_phase_3_corrective_action', async () => {
    renderSafetyRoute('/safety/incidents/42/phase-2', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    await screen.findByLabelText('Type of cause');
    const continueButton = screen.getByRole('button', {
      name: 'Continue to Corrective Action',
    });
    await waitFor(() => expect(continueButton).toBeEnabled());
    fireEvent.click(continueButton);

    expect(
      await screen.findByRole(
        'heading',
        { name: 'Add Corrective Action' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Save corrective' })
    ).toBeInTheDocument();
    expect(screen.queryByText('Final Record')).not.toBeInTheDocument();
    expect(safetyApiMocks.transitionIncident).toHaveBeenCalledWith('42', {
      target_phase: 6,
    });
    expect(safetyApiMocks.getIncidentPhase6Workspace).toHaveBeenCalledWith(
      '42'
    );
    expect(
      screen.queryByRole('button', { name: 'Continue to Phase 4' })
    ).not.toBeInTheDocument();
    expect(screen.queryByText('Backend payload')).not.toBeInTheDocument();
    expect(document.querySelector('pre')).not.toBeInTheDocument();
  });

  it('routes_split_action_phase_urls_to_preventive_and_redirects_removed_lessons_screen', async () => {
    const preventive = renderSafetyRoute(
      '/safety/incidents/42/phase-3/preventive',
      {
        formIds: ['SAF_F_001'],
        id: 'dpa-1',
        isGlobal: true,
        processIds: [],
        role: 'DPA',
        vesselIds: [],
      }
    );

    expect(
      await screen.findByRole(
        'heading',
        { name: 'Add Preventive Action' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    expect(screen.queryByLabelText('Type')).not.toBeInTheDocument();
    expect(screen.queryByText('Final Record')).not.toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Continue to Office Review' })
    ).toBeInTheDocument();
    preventive.unmount();

    renderSafetyRoute('/safety/incidents/42/phase-3/lessons', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByText('Office Review', {}, { timeout: 7000 })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Add Lesson Learned' })
    ).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Type')).not.toBeInTheDocument();
    expect(screen.queryByText('Final Record')).not.toBeInTheDocument();
  });

  it('loads_live_incident_phase_7_preflight_from_backend', async () => {
    setOfficeAuthStore(['SAF_P_006']);
    renderSafetyRoute('/safety/incidents/42/phase-5', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByRole('heading', { name: 'PDF Options' })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Office Check' })
    ).not.toBeInTheDocument();
    expect(screen.getByText('Office Review')).toBeInTheDocument();
    expect(
      screen.getByLabelText('Office Comments/lesson learnt')
    ).toBeInTheDocument();
    expect(
      screen.getByRole('checkbox', { name: 'Print Loss Evaluation' })
    ).not.toBeChecked();
    expect(screen.queryByText('Select PDF content')).not.toBeInTheDocument();
    expect(screen.queryByRole('checkbox', { name: 'Summary' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Download PDF' })).toBeEnabled();
    expect(safetyApiMocks.getIncidentPhase7Preflight).toHaveBeenCalledWith(
      '42'
    );
    expect(screen.queryByText('KSM-INC-2026-0042')).not.toBeInTheDocument();
    expect(
      screen.queryByText('PIC / DPA / FM by band')
    ).not.toBeInTheDocument();
  });

  it('moves_backend_phase_6_to_phase_7_before_office_acceptance', async () => {
    safetyApiMocks.getIncidentPhase7Preflight.mockResolvedValueOnce({
      bias_guards_resolved: true,
      blockers: [],
      closer_role: 'DPA',
      current_phase: 6,
      generated_at: '2026-05-08T00:00:00Z',
      incident_id: 42,
      pdf_preview: {
        available: true,
        download_path: 'http://localhost:8000/api/safety/export/incident/42/pdf/',
      },
      ready_for_acceptance: true,
      recommendation_tier_count: {
        corrective: 1,
        lessons_learnt: 1,
        preventive: 1,
      },
      required_process_id: 'SAF_P_004',
      risk_band: 'YELLOW',
      root_count: 2,
      signature_chain_status: {
        dpa: { present: false, required: true },
        fm: { present: false, required: false },
        hod: { present: true, required: true },
        master: { present: true, required: true },
        pic: { present: false, required: false },
        reporter: { present: true, required: true },
      },
    });
    safetyApiMocks.transitionIncident.mockResolvedValueOnce({
      current_phase: 7,
      id: 42,
      state: 'PHASE_7',
    });
    safetyApiMocks.acceptIncidentPhase7.mockResolvedValueOnce({
      current_phase: 7,
      id: 42,
      state: 'PHASE_7',
    });
    useAuthStore.setState({
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
      tokens: null,
      user: {
        form_ids: ['SAF_F_001'],
        full_name: 'dpa-1',
        id: 'dpa-1',
        process_ids: ['SAF_P_004'],
        role: 'DPA',
        username: 'dpa-1',
        vessel_id: null,
      } as never,
    });

    const rendered = renderSafetyRoute('/safety/incidents/42/phase-5', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: ['SAF_P_004'],
      role: 'DPA',
      vesselIds: [],
    });

    try {
      const acceptButton = await screen.findByRole(
        'button',
        { name: 'Accept / Close' },
        { timeout: 7000 }
      );
      await waitFor(() => expect(acceptButton).toBeEnabled());
      await act(async () => {
        fireEvent.click(acceptButton);
      });

      await waitFor(() =>
        expect(safetyApiMocks.transitionIncident).toHaveBeenCalledWith('42', {
          target_phase: 7,
        })
      );
      await waitFor(() =>
        expect(safetyApiMocks.acceptIncidentPhase7).toHaveBeenCalledWith(
          '42',
          expect.objectContaining({ typed_name: 'dpa-1' })
        )
      );
      const transitionOrder =
        safetyApiMocks.transitionIncident.mock.invocationCallOrder.at(-1) ?? 0;
      const acceptOrder =
        safetyApiMocks.acceptIncidentPhase7.mock.invocationCallOrder.at(-1) ??
        0;
      expect(transitionOrder).toBeLessThan(acceptOrder);
      expect(
        await screen.findByText(/Signature captured/i)
      ).toBeInTheDocument();
      expect(
        screen.queryByText(/Office review actions require current_phase = 7/i)
      ).not.toBeInTheDocument();
    } finally {
      rendered.unmount();
      useAuthStore.setState({
        isAuthenticated: false,
        isInitialized: false,
        isLoading: false,
        tokens: null,
        user: null,
      });
    }
  });

  it('sends_incident_back_to_action_rework_without_phase_picker', async () => {
    setOfficeAuthStore(['SAF_P_003']);
    renderSafetyRoute('/safety/incidents/42/phase-5', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: ['SAF_P_003'],
      role: 'DPA',
      vesselIds: [],
    });

    await screen.findByRole(
      'heading',
      { name: 'Send for rework' },
      { timeout: 7000 }
    );
    expect(screen.queryByLabelText('Send back to')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Comment'), {
      target: { value: 'Add named action owner before office acceptance.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send for rework' }));

    await waitFor(() =>
      expect(safetyApiMocks.sendBackIncidentPhase7).toHaveBeenCalledWith('42', {
        reason: 'Add named action owner before office acceptance.',
        target_phase: 6,
      })
    );
    expect(
      await screen.findByRole(
        'heading',
        { name: 'Add Corrective Action' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase6Workspace).toHaveBeenCalledWith(
      '42'
    );
  });

  it('loads_live_incident_phase_4_evidence_from_backend', async () => {
    renderSafetyRoute('/safety/incidents/42/phase-4/paper', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByRole(
        'heading',
        { name: 'New document' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Title')).toBeInTheDocument();
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
    expect(screen.getByLabelText('Attachment')).toBeInTheDocument();
    expect(screen.getByText('Engine log extract')).toBeInTheDocument();
    expect(
      screen.getByText('Deck and engine log pages relevant to the incident.')
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'People' })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Evidence check' })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('link', { name: 'Open Witness Statement' })
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole('link', {
        name: /Witness Statement.*Record or edit witness remarks/i,
      })
    ).toHaveAttribute('href', '/safety/incidents/42/phase-4/interviews');
    expect(
      screen.queryByRole('heading', { name: 'Check the Evidence' })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Witness interview loaded from backend/)
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/Backend Witness/)).not.toBeInTheDocument();
    expect(
      screen.queryByText('Health / Fatigue Evidence')
    ).not.toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase3Evidence).toHaveBeenCalledWith('42');
    expect(safetyApiMocks.getIncidentPhase3ChainOfCustody).toHaveBeenCalledWith(
      '42'
    );
    expect(
      safetyApiMocks.getIncidentPhase3EvidenceMatrix
    ).not.toHaveBeenCalled();
    expect(safetyApiMocks.getIncidentPhase3Interviews).toHaveBeenCalledWith(
      '42'
    );
    expect(screen.queryByText('AB Kumar')).not.toBeInTheDocument();
    expect(screen.queryByText('Ship clinic note')).not.toBeInTheDocument();
    expect(screen.queryByText('Backend payload')).not.toBeInTheDocument();
    expect(document.querySelector('pre')).not.toBeInTheDocument();
  });

  it('continues_phase_4_documents_when_backend_is_already_at_action_phase', async () => {
    safetyApiMocks.getIncidentPhase4Facts.mockResolvedValue([]);
    safetyApiMocks.transitionIncident.mockRejectedValueOnce(
      new Error('Illegal incident phase transition from Phase 6 to Phase 5.')
    );

    renderSafetyRoute('/safety/incidents/42/phase-4/paper', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: ['SAF_P_002'],
      role: 'DPA',
      vesselIds: [],
    });

    const continueButton = await screen.findByRole(
      'button',
      { name: 'Save and Continue' },
      { timeout: 7000 }
    );
    await waitFor(() => expect(continueButton).toBeEnabled());
    fireEvent.click(continueButton);

    await waitFor(() =>
      expect(safetyApiMocks.transitionIncident).toHaveBeenCalledWith('42', {
        target_phase: 5,
      })
    );
    expect(safetyApiMocks.transitionIncident).not.toHaveBeenCalledWith('42', {
      target_phase: 6,
    });
    expect(
      await screen.findByRole(
        'heading',
        { name: 'Add Corrective Action' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        /Illegal incident phase transition from Phase 6 to Phase 5/i
      )
    ).not.toBeInTheDocument();
  });

  it('acknowledges_document_save_and_scrolls_to_saved_documents', async () => {
    renderSafetyRoute('/safety/incidents/42/phase-4/paper', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByRole(
        'heading',
        { name: 'New document' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    const attachment = new File(['photo'], 'pump-photo.png', {
      type: 'image/png',
    });

    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'Pump photo' },
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Photo showing the saved pump condition.' },
    });
    fireEvent.change(screen.getByLabelText('Attachment'), {
      target: { files: [attachment] },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add document' }));

    await waitFor(() =>
      expect(
        safetyApiMocks.uploadIncidentPhase3Attachment
      ).toHaveBeenCalledWith('42', 'paper', attachment, {
        description: 'Photo showing the saved pump condition.',
        title: 'Pump photo',
      })
    );
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Document saved. Review it under Saved documents.'
    );
    expect(screen.getByText('Pump photo')).toBeInTheDocument();
    await waitFor(() =>
      expect(scrollIntoViewMock).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'start',
      })
    );
  });

  it('edits_phase_4_document_metadata_without_reuploading_attachment', async () => {
    renderSafetyRoute('/safety/incidents/42/phase-4/paper', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByRole(
        'heading',
        { name: 'New document' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole('button', { name: 'Edit Engine log extract' })
    );

    expect(
      await screen.findByRole('heading', { name: 'Edit document' })
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Title')).toHaveValue('Engine log extract');
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Updated engine log description.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Update document' }));

    await waitFor(() =>
      expect(
        safetyApiMocks.updateIncidentPhase3AttachmentMetadata
      ).toHaveBeenCalledWith(
        '42',
        'incidents/42/phase-3/paper/engine-log.pdf',
        {
          description: 'Updated engine log description.',
          title: 'Engine log extract',
        }
      )
    );
    expect(
      safetyApiMocks.uploadIncidentPhase3Attachment
    ).not.toHaveBeenCalled();
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Document updated. Review it under Saved documents.'
    );
  });

  it('captures_phase_4_witness_statement_with_crew_or_other_name_and_signature', async () => {
    renderSafetyRoute('/safety/incidents/42/phase-4/interviews', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByRole(
        'heading',
        { name: 'Add Witness Statement' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(mastersApiMocks.getVesselCrew).toHaveBeenCalledWith('VESSEL-42')
    );
    expect(screen.getByLabelText('Witness name')).toHaveTextContent(
      'AB - AB Kumar'
    );
    expect(screen.getByLabelText('Witness name')).not.toHaveTextContent(
      'AB - AB - AB Kumar'
    );
    expect(
      screen.getByRole('heading', { name: 'Saved Witness Statements' })
    ).toBeInTheDocument();
    expect(screen.getAllByText('Remark').length).toBeGreaterThan(0);
    expect(screen.getByText('Witness statement uploaded.')).toBeInTheDocument();
    expect(
      screen.queryByLabelText('What the witness said')
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText('Remark')).toBeInTheDocument();
    expect(
      screen.getByLabelText('Upload witness statement')
    ).toBeInTheDocument();
    expect(screen.queryByLabelText('Note type')).not.toBeInTheDocument();
    expect(
      screen.queryByText('Formal statement details')
    ).not.toBeInTheDocument();
    expect(screen.queryByText('Opening notes')).not.toBeInTheDocument();
    expect(screen.queryByText('Context given')).not.toBeInTheDocument();
    expect(screen.queryByText('Read back to witness')).not.toBeInTheDocument();
    expect(
      screen.queryByText('Copy given or recorded')
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText('Why formal statement is not needed')
    ).not.toBeInTheDocument();

    const saveButton = screen.getByRole('button', {
      name: 'Save witness statement',
    });
    expect(saveButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Witness name'), {
      target: { value: 'OTHER' },
    });
    fireEvent.change(screen.getByLabelText('Specify witness name'), {
      target: { value: 'Port engineer Rao' },
    });
    fireEvent.change(screen.getByLabelText('Remark'), {
      target: { value: 'Statement recorded and closed.' },
    });
    fireEvent.change(screen.getByLabelText('Upload witness statement'), {
      target: {
        files: [
          new File(['signature'], 'witness-signature.png', {
            type: 'image/png',
          }),
        ],
      },
    });
    expect(
      await screen.findByText(
        'Witness statement selected: witness-signature.png'
      )
    ).toBeInTheDocument();
    await waitFor(() => expect(saveButton).toBeEnabled());
    fireEvent.click(saveButton);

    await waitFor(() =>
      expect(safetyApiMocks.createIncidentPhase3Interview).toHaveBeenCalledWith(
        '42',
        {
          conclusion_notes: 'Statement recorded and closed.',
          copy_to_witness_recorded: false,
          interview_type: 'INFORMAL',
          introduction_notes: '',
          make_acquaintance_notes: '',
          meeting_notes: '',
          question_rows: [],
          read_back_confirmed: false,
          reason_formal_impossible:
            'Simplified witness statement recorded from Phase 4.',
          witness_signature: expect.stringMatching(/^data:image\/png;base64,/),
          witness_name: 'Port engineer Rao',
        }
      )
    );
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Witness statement saved. Review it under Saved Witness Statements.'
    );
    await waitFor(() =>
      expect(scrollIntoViewMock).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'start',
      })
    );
  });

  it('edits_phase_4_witness_statement_without_creating_a_duplicate', async () => {
    renderSafetyRoute('/safety/incidents/42/phase-4/interviews', {
      formIds: ['SAF_F_001'],
      id: 'dpa-1',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByRole(
        'heading',
        { name: 'Add Witness Statement' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole('button', { name: 'Edit Backend Witness' })
    );

    expect(
      await screen.findByRole('heading', { name: 'Edit Witness Statement' })
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Specify witness name')).toHaveValue(
      'Backend Witness'
    );
    fireEvent.change(screen.getByLabelText('Remark'), {
      target: { value: 'Updated witness remark.' },
    });
    fireEvent.click(
      screen.getByRole('button', { name: 'Update witness statement' })
    );

    await waitFor(() =>
      expect(safetyApiMocks.updateIncidentPhase3Interview).toHaveBeenCalledWith(
        '42',
        '7',
        {
          conclusion_notes: 'Updated witness remark.',
          copy_to_witness_recorded: false,
          interview_type: 'INFORMAL',
          introduction_notes: '',
          make_acquaintance_notes: '',
          meeting_notes: '',
          question_rows: [],
          read_back_confirmed: false,
          reason_formal_impossible:
            'Simplified witness statement recorded from Phase 4.',
          witness_signature: 'Backend Witness',
          witness_name: 'Backend Witness',
        }
      )
    );
    expect(safetyApiMocks.createIncidentPhase3Interview).not.toHaveBeenCalled();
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Witness statement updated. Review it under Saved Witness Statements.'
    );
  });

  it('renders_bare_phase_3_incident_route_as_corrective_action', async () => {
    renderSafetyRoute('/safety/incidents/42/phase-3', {
      formIds: ['SAF_F_001'],
      id: 'pic-1',
      isGlobal: true,
      processIds: [],
      role: 'PIC',
      vesselIds: [],
    });

    expect(
      await screen.findByRole(
        'heading',
        { name: 'Add Corrective Action' },
        { timeout: 7000 }
      )
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Save corrective' })
    ).toBeInTheDocument();
    expect(safetyApiMocks.getIncidentPhase6Workspace).toHaveBeenCalledWith(
      '42'
    );
    expect(screen.queryByText('Backend payload')).not.toBeInTheDocument();
    expect(document.querySelector('pre')).not.toBeInTheDocument();
  });

  it('loads_live_near_miss_office_comments_route_from_backend', async () => {
    renderSafetyRoute('/safety/near-miss/99/office-comments', {
      formIds: ['SAF_F_002'],
      id: 'dpa-2',
      isGlobal: true,
      processIds: ['SAF_P_002'],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByText('Near Miss Office Comments')
    ).toBeInTheDocument();
    expect(await screen.findByText(/NM-BACKEND-0099/)).toBeInTheDocument();
    expect(
      await screen.findByRole('button', { name: 'Accept' })
    ).toBeInTheDocument();
    expect(safetyApiMocks.getNearMiss).toHaveBeenCalledWith('99');
    expect(screen.queryByText('DRAFT-ABC/2026/T014')).not.toBeInTheDocument();
  });

  it('loads_live_near_miss_export_route_with_backend_masking_note', async () => {
    renderSafetyRoute('/safety/near-miss/99/pdf', {
      formIds: ['SAF_F_002'],
      id: 'dpa-3',
      isGlobal: true,
      processIds: ['SAF_P_023'],
      role: 'DPA',
      vesselIds: [],
    });

    expect(await screen.findByText('Near Miss PDF Export')).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Download near-miss PDF' })
    ).toBeInTheDocument();
    expect(safetyApiMocks.getNearMiss).toHaveBeenCalledWith('99');
    expect(screen.queryByText('Reporter visible')).not.toBeInTheDocument();
  });

  it('submits_live_auditor_export_request_to_backend', async () => {
    renderSafetyRoute('/safety/admin/auditor-export', {
      formIds: ['SAF_F_020'],
      id: 'dpa-4',
      isGlobal: true,
      processIds: [],
      role: 'DPA',
      vesselIds: [],
    });

    expect(
      await screen.findByText('Auditor Bundle Export')
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole('button', { name: 'Build auditor bundle' })
    );

    await waitFor(() => {
      expect(safetyApiMocks.exportAuditorBundle).toHaveBeenCalledWith(
        expect.objectContaining({
          record_types: expect.arrayContaining([
            'INCIDENT',
            'NEAR_MISS',
            'SOI',
            'SCM',
          ]),
          vessel_id: null,
        })
      );
    });
    expect(
      await screen.findByText('Export prepared: safety-auditor-bundle.zip')
    ).toBeInTheDocument();
    expect(
      screen.queryByText('Build Demo Bundle Plan')
    ).not.toBeInTheDocument();
    expect(screen.queryByText('Demo Payload')).not.toBeInTheDocument();
  });

  it('shows_permission_fallback_instead_of_blank_screen', async () => {
    renderSafetyRoute('/safety/dashboard', {
      formIds: ['SAF_F_003'],
      id: 'user-3',
      isGlobal: false,
      processIds: [],
      role: 'MASTER',
      vesselIds: ['vessel-9'],
    });

    expect(
      await screen.findByText('Form access is not available for this page.')
    ).toBeInTheDocument();
  });
});
