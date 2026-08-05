import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const phase7Mocks = vi.hoisted(() => ({
  getIncidentPhase7Preflight: vi.fn(),
  hasProcess: vi.fn(),
  navigate: vi.fn(),
  role: 'PIC',
  user: {
    full_name: 'PIC Reviewer',
    id: 'pic-1',
    role: 'PIC',
  },
}));

vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
  useNavigate: () => phase7Mocks.navigate,
  useParams: () => ({ id: 'incident-1' }),
}));

vi.mock('../../../hooks/use-auth', () => ({
  useAuth: () => ({
    hasProcess: phase7Mocks.hasProcess,
    role: phase7Mocks.role,
    user: phase7Mocks.user,
  }),
}));

vi.mock('../../../lib/safety/digital-signature', () => ({
  getSafetyDeviceFingerprint: () => 'test-device',
  resolveSignatureTypedName: () => 'PIC Reviewer',
}));

vi.mock('../../../lib/api/safety', () => ({
  safetyApi: {
    acceptIncidentPhase7: vi.fn(),
    downloadIncidentPdf: vi.fn(),
    getIncidentFleetAlert: vi.fn(),
    getIncidentPhase7Preflight: phase7Mocks.getIncidentPhase7Preflight,
    issueIncidentFleetAlert: vi.fn(),
    sendBackIncidentPhase7: vi.fn(),
    signIncidentPhase7Hod: vi.fn(),
    transitionIncident: vi.fn(),
  },
}));

import { SafetyIncidentPhase7 } from './phase-7-workspace';
import { safetyApi } from '../../../lib/api/safety';

describe('SafetyIncidentPhase7', () => {
  beforeEach(() => {
    phase7Mocks.getIncidentPhase7Preflight.mockReset();
    phase7Mocks.hasProcess.mockReset();
    phase7Mocks.navigate.mockReset();
    phase7Mocks.role = 'PIC';
    phase7Mocks.user = {
      full_name: 'PIC Reviewer',
      id: 'pic-1',
      role: 'PIC',
    };
    phase7Mocks.hasProcess.mockImplementation(
      (processId: string) => processId === 'SAF_P_006'
    );
    vi.mocked(safetyApi.sendBackIncidentPhase7).mockReset();
    vi.mocked(safetyApi.transitionIncident).mockReset();
    vi.mocked(safetyApi.getIncidentFleetAlert).mockReset();
    vi.mocked(safetyApi.issueIncidentFleetAlert).mockReset();
    vi.mocked(safetyApi.downloadIncidentPdf).mockReset();
    vi.mocked(safetyApi.downloadIncidentPdf).mockResolvedValue({
      blob: new Blob(['pdf'], { type: 'application/pdf' }),
      fileName: 'incident-1.pdf',
    });
    Object.defineProperty(URL, 'createObjectURL', {
      configurable: true,
      value: vi.fn(() => 'blob:incident-1'),
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      configurable: true,
      value: vi.fn(),
    });
    Object.defineProperty(HTMLAnchorElement.prototype, 'click', {
      configurable: true,
      value: vi.fn(),
    });
  });

  function buildPreflight(overrides = {}) {
    return {
      alarp_complete: true,
      authority: {
        allowed_process_ids: ['SAF_P_004', 'SAF_P_006'],
        allowed_role_codes: ['DPA', 'PIC', 'OFFICE_PIC'],
        assigned_pic_user_id: 'pic-1',
        message:
          'PIC or DPA can accept, close, or send this incident back for rework for any risk band.',
        required_process_id: 'SAF_P_004',
      },
      bias_guards_resolved: true,
      blockers: [],
      closer_role: 'DPA',
      current_phase: 7,
      generated_at: '2026-07-06T00:00:00Z',
      incident_id: 1,
      office_comment: '',
      pdf_preview: {
        available: false,
        expected_sections: 10,
        incident_id: 1,
        message: '',
        status: 'NOT_AVAILABLE',
      },
      ready_for_acceptance: true,
      recommendation_tier_count: { CORRECTIVE: 1, PREVENTIVE: 1 },
      required_process_id: 'SAF_P_004',
      rework_summary: null,
      risk_band: 'RED',
      root_count: 1,
      signature_chain_status: {
        dpa: { present: false, required: true },
        fm: { present: false, required: false },
        hod: { present: true, required: true },
        master: { present: true, required: true },
        pic: { present: false, required: false },
        reporter: { present: true, required: true },
      },
      ...overrides,
    };
  }

  it('allows PIC to accept or close a RED incident when preflight allows PIC or DPA', async () => {
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({
        pdf_preview: {
          available: false,
          expected_sections: 10,
          incident_id: 1,
          message:
            'Formal incident PDF export is available after Phase 7 acceptance.',
          status: 'NOT_AVAILABLE',
        },
      })
    );

    render(<SafetyIncidentPhase7 />);

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: 'Accept / Close' })
      ).toBeEnabled();
    });
    expect(screen.queryByText(/cannot approve this incident/i)).toBeNull();
    expect(screen.getByLabelText('Office Comments/lesson learnt')).toBeTruthy();
    expect(screen.queryByText(/PIC or DPA can accept, close/i)).toBeNull();
    expect(screen.queryByText(/Who can approve/i)).toBeNull();
    expect(screen.queryByText('Root Causes')).toBeNull();
    expect(screen.queryByText('Actions')).toBeNull();
    expect(screen.queryByText('Before Office Review Approval')).toBeNull();
    expect(screen.queryByLabelText('Send back to')).toBeNull();
    expect(
      screen.queryByText(
        'Formal incident PDF export is available after Phase 7 acceptance.'
      )
    ).toBeNull();
  });

  it('sends rework to the fixed action phase without asking for a target phase', async () => {
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(buildPreflight());
    vi.mocked(safetyApi.sendBackIncidentPhase7).mockResolvedValue({
      current_phase: 6,
    });

    render(<SafetyIncidentPhase7 />);

    const comment = await screen.findByLabelText('Comment');
    fireEvent.change(comment, {
      target: { value: 'Please update the corrective action details.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send for rework' }));

    await waitFor(() => {
      expect(safetyApi.sendBackIncidentPhase7).toHaveBeenCalledWith(
        'incident-1',
        {
          reason: 'Please update the corrective action details.',
          target_phase: 6,
        }
      );
    });
  });

  it('shows only office comments to ship-side users', async () => {
    phase7Mocks.role = 'VESSEL_MASTER';
    phase7Mocks.user = {
      full_name: 'Vessel Master',
      id: 'master-1',
      role: 'VESSEL_MASTER',
    };
    phase7Mocks.hasProcess.mockReturnValue(false);
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({
        office_comment: 'Improve toolbox discussion before the next job.',
      })
    );

    render(<SafetyIncidentPhase7 />);

    expect(
      await screen.findByText('Office Comments/lesson learnt')
    ).toBeTruthy();
    expect(
      screen.getByText('Improve toolbox discussion before the next job.')
    ).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Accept / Close' })).toBeNull();
    expect(
      screen.queryByRole('button', { name: 'Send for rework' })
    ).toBeNull();
  });

  it('shows the latest rework summary from the office textbox and lets ship users mark it done', async () => {
    phase7Mocks.role = 'VESSEL_MASTER';
    phase7Mocks.user = {
      full_name: 'Vessel Master',
      id: 'master-1',
      role: 'VESSEL_MASTER',
    };
    phase7Mocks.hasProcess.mockReturnValue(false);
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValueOnce(
      buildPreflight({
        current_phase: 6,
        rework_summary: {
          comment:
            'Update the action description and attach the revised evidence.',
          requested_at: '2026-07-13T10:00:00Z',
          requested_by: 'dpa-1',
          requested_by_role: 'DPA',
        },
      })
    );
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValueOnce(
      buildPreflight({ current_phase: 7, rework_summary: null })
    );
    vi.mocked(safetyApi.transitionIncident).mockResolvedValue({
      current_phase: 7,
      state: 'UNDER_REVIEW',
    });

    render(<SafetyIncidentPhase7 />);

    expect(await screen.findByText('Rework summary')).toBeTruthy();
    expect(
      screen.getByText(
        'Update the action description and attach the revised evidence.'
      )
    ).toBeTruthy();
    expect(screen.queryByLabelText('Send back to')).toBeNull();
    expect(
      screen.queryByRole('button', { name: 'Send for rework' })
    ).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Rework Done' }));

    await waitFor(() => {
      expect(safetyApi.transitionIncident).toHaveBeenCalledWith(
        'incident-1',
        { target_phase: 7 }
      );
    });
    expect(await screen.findByText('Rework marked done.')).toBeTruthy();
  });

  it('shows the highlighted rework done action to office users', async () => {
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({
        current_phase: 6,
        rework_summary: {
          comment: 'Recheck the evidence attachment before closure.',
          requested_at: '2026-07-13T10:00:00Z',
          requested_by: 'dpa-1',
          requested_by_role: 'DPA',
        },
      })
    );

    render(<SafetyIncidentPhase7 />);

    expect(await screen.findByText('Rework summary')).toBeTruthy();
    expect(screen.getByText('Recheck the evidence attachment before closure.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Rework Done' })).toBeEnabled();
    expect(screen.queryByLabelText('Send back to')).toBeNull();
  });

  it('shows a pending office comment message to ship-side users when no comment exists', async () => {
    phase7Mocks.role = 'VESSEL_MASTER';
    phase7Mocks.user = {
      full_name: 'Vessel Master',
      id: 'master-1',
      role: 'VESSEL_MASTER',
    };
    phase7Mocks.hasProcess.mockReturnValue(false);
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({ office_comment: '' })
    );

    render(<SafetyIncidentPhase7 />);

    expect(
      await screen.findByText('Office Comments/lesson learnt')
    ).toBeTruthy();
    expect(screen.getByText('Office comment is not added yet.')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Accept / Close' })).toBeNull();
    expect(
      screen.queryByRole('button', { name: 'Send for rework' })
    ).toBeNull();
  });

  it('lets office users send an incident Fleet Alert to selected ships only', async () => {
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({ current_phase: 6 })
    );
    vi.mocked(safetyApi.transitionIncident).mockResolvedValue({
      current_phase: 7,
    });
    vi.mocked(safetyApi.getIncidentFleetAlert).mockResolvedValue({
      recipient_vessels: [
        {
          display_name: 'ALP - Vessel Alpha',
          has_email: true,
          vessel_id: '11111111-1111-1111-1111-111111111111',
        },
        {
          display_name: 'BRV - Vessel Bravo',
          has_email: true,
          vessel_id: '22222222-2222-2222-2222-222222222222',
        },
        {
          display_name: 'CHR - Vessel Charlie',
          has_email: true,
          vessel_id: '33333333-3333-3333-3333-333333333333',
        },
      ],
    });
    vi.mocked(safetyApi.issueIncidentFleetAlert).mockResolvedValue({
      emails_sent: 2,
      recipient_vessel_ids: [
        '11111111-1111-1111-1111-111111111111',
        '33333333-3333-3333-3333-333333333333',
      ],
    });

    render(<SafetyIncidentPhase7 />);

    fireEvent.click(await screen.findByRole('button', { name: 'Fleet Alert' }));
    expect(
      await screen.findByRole('dialog', {
        name: 'Select vessels for Fleet Alert',
      })
    ).toBeTruthy();
    expect(screen.queryByLabelText('Select ships for Fleet Alert')).toBeNull();
    fireEvent.click(screen.getByLabelText('ALP - Vessel Alpha'));
    fireEvent.click(screen.getByLabelText('CHR - Vessel Charlie'));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    expect(safetyApi.transitionIncident).toHaveBeenCalledWith('incident-1', {
      target_phase: 7,
    });
    expect(
      safetyApi.transitionIncident.mock.invocationCallOrder.at(-1) ?? 0
    ).toBeLessThan(
      safetyApi.getIncidentFleetAlert.mock.invocationCallOrder.at(-1) ?? 0
    );
    await waitFor(() => {
      expect(safetyApi.issueIncidentFleetAlert).toHaveBeenCalledWith(
        'incident-1',
        {
          recipient_vessel_ids: [
            '11111111-1111-1111-1111-111111111111',
            '33333333-3333-3333-3333-333333333333',
          ],
        }
      );
      });
      expect(
        await screen.findByText(
          'Fleet alert sent to 2 selected ship(s). Email batch addressed to 2 vessel(s).'
        )
      ).toBeTruthy();
  });

  it('selects every vessel in the Fleet Alert popup when select all vessels is ticked', async () => {
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({ current_phase: 7 })
    );
    vi.mocked(safetyApi.getIncidentFleetAlert).mockResolvedValue({
      recipient_vessels: [
        {
          display_name: 'ALP - Vessel Alpha',
          has_email: true,
          vessel_id: '11111111-1111-1111-1111-111111111111',
        },
        {
          display_name: 'BRV - Vessel Bravo',
          has_email: true,
          vessel_id: '22222222-2222-2222-2222-222222222222',
        },
      ],
    });
    vi.mocked(safetyApi.issueIncidentFleetAlert).mockResolvedValue({
      emails_sent: 2,
      recipient_vessel_ids: [
        '11111111-1111-1111-1111-111111111111',
        '22222222-2222-2222-2222-222222222222',
      ],
    });

    render(<SafetyIncidentPhase7 />);

    fireEvent.click(await screen.findByRole('button', { name: 'Fleet Alert' }));
    const selectAll = await screen.findByLabelText('Select all vessels');
    fireEvent.click(selectAll);
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(safetyApi.issueIncidentFleetAlert).toHaveBeenCalledWith(
        'incident-1',
        {
          recipient_vessel_ids: [
            '11111111-1111-1111-1111-111111111111',
            '22222222-2222-2222-2222-222222222222',
          ],
        }
      );
    });
  });

  it('shows only the Loss Evaluation PDF option and downloads the compulsory sections by default', async () => {
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({
        pdf_preview: {
          available: true,
          download_path: 'http://localhost:8000/api/safety/incidents/1/pdf/',
          expected_sections: 10,
          incident_id: 1,
          message: '',
          status: 'AVAILABLE',
        },
      })
    );

    render(<SafetyIncidentPhase7 />);

    expect(
      await screen.findByRole('checkbox', { name: 'Print Loss Evaluation' })
    ).not.toBeChecked();
    expect(screen.queryByText('Select PDF content')).toBeNull();
    expect(screen.queryByLabelText('Summary')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Download PDF' }));

    await waitFor(() => {
      expect(safetyApi.downloadIncidentPdf).toHaveBeenCalledWith(
        'incident-1',
        [
          'summary',
          'reporter_details',
          'injury_details',
          'root_cause',
          'evidence_documents',
          'corrective_preventive_actions',
          'signature',
        ]
      );
    });
  });

  it('adds Loss Evaluation to the PDF download when the checkbox is selected', async () => {
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({
        pdf_preview: {
          available: true,
          download_path: 'http://localhost:8000/api/safety/incidents/1/pdf/',
          expected_sections: 10,
          incident_id: 1,
          message: '',
          status: 'AVAILABLE',
        },
      })
    );

    render(<SafetyIncidentPhase7 />);

    fireEvent.click(
      await screen.findByRole('checkbox', { name: 'Print Loss Evaluation' })
    );
    fireEvent.click(screen.getByRole('button', { name: 'Download PDF' }));

    await waitFor(() => {
      expect(safetyApi.downloadIncidentPdf).toHaveBeenCalledWith(
        'incident-1',
        [
          'summary',
          'reporter_details',
          'injury_details',
          'root_cause',
          'evidence_documents',
          'corrective_preventive_actions',
          'signature',
          'estimated_cost',
        ]
      );
    });
  });

  it('shows the PDF download controls to ship-side users', async () => {
    phase7Mocks.role = 'VESSEL_MASTER';
    phase7Mocks.user = {
      full_name: 'Vessel Master',
      id: 'master-1',
      role: 'VESSEL_MASTER',
    };
    phase7Mocks.hasProcess.mockReturnValue(false);
    phase7Mocks.getIncidentPhase7Preflight.mockResolvedValue(
      buildPreflight({
        pdf_preview: {
          available: true,
          download_path: 'http://localhost:8000/api/safety/incidents/1/pdf/',
          expected_sections: 10,
          incident_id: 1,
          message: '',
          status: 'AVAILABLE',
        },
      })
    );

    render(<SafetyIncidentPhase7 />);

    expect(
      await screen.findByRole('checkbox', { name: 'Print Loss Evaluation' })
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Download PDF' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Fleet Alert' })).toBeNull();
  });
});
