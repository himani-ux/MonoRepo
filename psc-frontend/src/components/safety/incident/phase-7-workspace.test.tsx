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
    getIncidentPhase7Preflight: phase7Mocks.getIncidentPhase7Preflight,
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
});
