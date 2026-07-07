import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const phase8Mocks = vi.hoisted(() => ({
  closeIncidentPhase8: vi.fn(),
  getIncidentPhase8Workspace: vi.fn(),
  navigate: vi.fn(),
  saveIncidentPhase8LossEvaluation: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: ReactNode; to: string }) => <a href={to}>{children}</a>,
  useNavigate: () => phase8Mocks.navigate,
  useParams: () => ({ id: 'incident-1' }),
}));

vi.mock('../../../hooks/use-auth', () => ({
  useAuth: () => ({
    role: 'DPA',
    user: {
      id: 'dpa-1',
      role: 'DPA',
    },
  }),
}));

vi.mock('../../../lib/api/safety', () => ({
  safetyApi: {
    closeIncidentPhase8: phase8Mocks.closeIncidentPhase8,
    getIncidentPhase8Workspace: phase8Mocks.getIncidentPhase8Workspace,
    saveIncidentPhase8LossEvaluation: phase8Mocks.saveIncidentPhase8LossEvaluation,
  },
}));

import { SafetyIncidentPhase8 } from './phase-8-workspace';

describe('SafetyIncidentPhase8', () => {
  beforeEach(() => {
    Object.values(phase8Mocks).forEach((mock) => mock.mockReset());
  });

  function buildWorkspace(overrides: Record<string, unknown> = {}) {
    return {
      blocker_details: [
        {
          code: 'loss_evaluation_not_saved',
          message: 'Save Loss Evaluation before closing the incident.',
        },
      ],
      blockers: ['loss_evaluation_not_saved'],
      choices: {
        consequence: [
          { label: 'Minor', value: 'MINOR' },
          { label: 'Major', value: 'MAJOR' },
        ],
        likelihood: [
          { label: 'Remote', value: 'REMOTE' },
          { label: 'Possible', value: 'POSSIBLE' },
        ],
        repair_type: [
          { label: 'Temporary', value: 'TEMPORARY' },
          { label: 'Permanent', value: 'PERMANENT' },
        ],
        risk_level: [
          { label: 'Low', value: 'LOW' },
          { label: 'High', value: 'HIGH' },
        ],
        safe_working_practice: [
          { label: 'Code A', value: 'Code A' },
        ],
        yes_no: [
          { label: 'Yes', value: true },
          { label: 'No', value: false },
        ],
      },
      current_phase: 8,
      has_loss_evaluation: false,
      incident_id: 'incident-1',
      loss_evaluation: {
        consequence: null,
        likelihood: null,
        risk_level: null,
        name_of_master: null,
        name_of_chief_engineer: null,
        repair_type: null,
        repair_details: null,
        last_overhaul_maintenance_survey_details: null,
        safe_working_practice: null,
        man_hours_worked: null,
        hours_worked_previous_day: null,
        hours_rest_last_96_hours: null,
        delay_to_vessel: null,
        delay_reason: null,
        repair_man_hours_lost: null,
        materials_used_repairs_onboard: null,
        materials_specify_details: null,
        materials_reason: null,
        deviation: null,
        off_hire: null,
        injury_man_hours_lost: null,
        injury_reasons: null,
        repatriation: null,
        hospitalization: null,
        evacuation: null,
        estimated_cost_off_hire: null,
        estimated_cost_delay: null,
        estimated_cost_man_hours: null,
        estimated_cost_deviation: null,
        estimated_cost_materials: null,
        estimated_cost_miscellaneous: null,
        total_estimated_cost: null,
        miscellaneous_expenses_reason: null,
        cost_medicines_onboard: null,
        cost_doctor_visits: null,
        cost_repatriation: null,
        cost_evacuation: null,
        cost_injury_delay: null,
        cost_injury_man_hours: null,
        cost_injury_deviation: null,
        cost_injury_miscellaneous: null,
        injury_total_estimated_cost: null,
        injury_miscellaneous_expenses_reason: null,
        id: null,
        updated_date: null,
      },
      phase_title: 'Loss Evaluation',
      ready_for_close: false,
      report_type: 'INCIDENT',
      required_process_id: 'SAF_P_004',
      risk_band: 'YELLOW',
      state: 'IN_PROGRESS',
      ...overrides,
    };
  }

  it('loads loss evaluation before office approval', async () => {
    phase8Mocks.getIncidentPhase8Workspace.mockResolvedValue(buildWorkspace({
      current_phase: 7,
      incident_id: 'incident-1',
      state: 'IN_PROGRESS',
    }));

    render(<SafetyIncidentPhase8 />);

    expect(await screen.findByRole('heading', { name: 'Loss Evaluation' })).toBeInTheDocument();
    expect(screen.queryByText('Office approval required')).toBeNull();
    expect(phase8Mocks.getIncidentPhase8Workspace).toHaveBeenCalledWith('incident-1');
  });

  it('loads incident report loss-evaluation fields after office approval', async () => {
    phase8Mocks.getIncidentPhase8Workspace.mockResolvedValue(buildWorkspace());

    render(<SafetyIncidentPhase8 />);

    await waitFor(() => {
      expect(phase8Mocks.getIncidentPhase8Workspace).toHaveBeenCalledWith('incident-1');
    });
    expect(await screen.findByRole('heading', { name: 'Loss Evaluation' })).toBeInTheDocument();
    expect(screen.getByText('Incident Report')).toBeInTheDocument();
    expect(screen.getByLabelText('Type of Repairs')).toBeInTheDocument();
    expect(screen.getByLabelText('Estimated Cost for Off Hire')).toBeInTheDocument();
  });

  it('loads injury report specific fields', async () => {
    phase8Mocks.getIncidentPhase8Workspace.mockResolvedValue(buildWorkspace({ report_type: 'INJURY' }));

    render(<SafetyIncidentPhase8 />);

    expect(await screen.findByText('Injury Report')).toBeInTheDocument();
    expect(screen.getByLabelText('Code of Safe Working Practices to which the Incident relates')).toBeInTheDocument();
    expect(screen.getByLabelText('Repatriation')).toBeInTheDocument();
    expect(screen.getByLabelText('Cost for Medicines Given Onboard')).toBeInTheDocument();
  });

  it('saves loss evaluation and shows acknowledgement', async () => {
    const firstWorkspace = buildWorkspace();
    const savedWorkspace = buildWorkspace({
      has_loss_evaluation: true,
      ready_for_close: true,
      blockers: [],
      blocker_details: [],
    });
    phase8Mocks.getIncidentPhase8Workspace.mockResolvedValue(firstWorkspace);
    phase8Mocks.saveIncidentPhase8LossEvaluation.mockResolvedValue(savedWorkspace);

    render(<SafetyIncidentPhase8 />);

    fireEvent.change(await screen.findByLabelText('Consequence'), { target: { value: 'MAJOR' } });
    fireEvent.change(screen.getByLabelText('Likelihood'), { target: { value: 'POSSIBLE' } });
    fireEvent.change(screen.getByLabelText('Risk level'), { target: { value: 'HIGH' } });
    fireEvent.change(screen.getByLabelText('Estimated Cost for Off Hire'), { target: { value: '100' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save Loss Evaluation' }));

    await waitFor(() => {
      expect(phase8Mocks.saveIncidentPhase8LossEvaluation).toHaveBeenCalledWith(
        'incident-1',
        expect.objectContaining({
          consequence: 'MAJOR',
          likelihood: 'POSSIBLE',
          risk_level: 'HIGH',
          estimated_cost_off_hire: '100',
          total_estimated_cost: '100.00',
        }),
      );
    });
    expect(await screen.findByText('Loss Evaluation saved.')).toBeInTheDocument();
  });
});
