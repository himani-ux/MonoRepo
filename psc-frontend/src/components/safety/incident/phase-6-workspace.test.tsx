import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const phase6Mocks = vi.hoisted(() => ({
  createIncidentRecommendation: vi.fn(),
  getIncidentPhase6Workspace: vi.fn(),
  navigate: vi.fn(),
  updateIncidentRecommendation: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
  useNavigate: () => phase6Mocks.navigate,
  useParams: () => ({ id: 'incident-1' }),
}));

vi.mock('../../../lib/api/safety', () => ({
  safetyApi: {
    createIncidentRecommendation: phase6Mocks.createIncidentRecommendation,
    getIncidentPhase6Workspace: phase6Mocks.getIncidentPhase6Workspace,
    updateIncidentRecommendation: phase6Mocks.updateIncidentRecommendation,
  },
}));

vi.mock('../../../hooks/use-auth', () => ({
  useAuth: () => ({
    user: {
      id: 'user-1',
      username: 'current-user',
    },
  }),
}));

import SafetyIncidentPhase6 from './phase-6-workspace';

describe('SafetyIncidentPhase6', () => {
  beforeEach(() => {
    phase6Mocks.createIncidentRecommendation.mockReset();
    phase6Mocks.getIncidentPhase6Workspace.mockReset();
    phase6Mocks.navigate.mockReset();
    phase6Mocks.updateIncidentRecommendation.mockReset();
  });

  function buildWorkspace() {
    return {
      alarp_complete: false,
      bias_guards_complete: true,
      blame_evaluation: {
        all_root_personal_factors: false,
        blocked: false,
        has_lack_of_control: false,
        override_by: null,
        trigger_terms: [],
      },
      corrective_actions: [],
      gate_blockers: [],
      incident_id: 'incident-1',
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
    };
  }

  it('does not show title or why-needed fields', async () => {
    phase6Mocks.getIncidentPhase6Workspace.mockResolvedValue(buildWorkspace());

    render(<SafetyIncidentPhase6 />);

    await waitFor(() => {
      expect(screen.getByText('Add Action')).toBeTruthy();
    });

    expect(screen.getByLabelText('Type')).toBeTruthy();
    expect(screen.queryByLabelText('Title')).toBeNull();
    expect(screen.getByLabelText('Description')).toBeTruthy();
    expect(screen.queryByLabelText('Why is this needed?')).toBeNull();

    expect(screen.queryByLabelText('Why is this needed?')).toBeNull();
  });

  it('saves preventive action without sending rationale', async () => {
    phase6Mocks.getIncidentPhase6Workspace.mockResolvedValue({
      ...buildWorkspace(),
      themes: [{ code: 'training', label: 'Training' }],
    });
    phase6Mocks.createIncidentRecommendation.mockResolvedValue({});

    render(<SafetyIncidentPhase6 />);

    await screen.findByText('Add Action');

    fireEvent.change(screen.getByLabelText('Type'), {
      target: { value: 'PREVENTIVE' },
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Update toolbox talk before this activity.' },
    });
    fireEvent.change(screen.getByLabelText('Due date'), {
      target: { value: '2026-07-20' },
    });
    fireEvent.change(screen.getByLabelText('How much will this reduce risk?'), {
      target: { value: 'LOW' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save action' }));

    await waitFor(() => {
      expect(phase6Mocks.createIncidentRecommendation).toHaveBeenCalledWith(
        'incident-1',
        {
          alarp_attested: true,
          corrective_action: {
            due_date: '2026-07-20',
            verifier_user_id: 'current-user',
          },
          description: 'Update toolbox talk before this activity.',
          estimated_effort: null,
          estimated_likelihood_reduction: 'LOW',
          residual_risk_statement: 'Update toolbox talk before this activity.',
          theme_code: null,
          tier: 'PREVENTIVE',
          title: 'Update toolbox talk before this activity.',
        }
      );
    });
  });

  it('does not show row count wording in the action summary', async () => {
    phase6Mocks.getIncidentPhase6Workspace.mockResolvedValue({
      ...buildWorkspace(),
      recommendations: {
        CORRECTIVE: [
          {
            alarp_attested: false,
            corrective_actions: [],
            description: 'Replace damaged safety guard.',
            id: 'rec-1',
            rationale: 'The existing guard is damaged.',
            tier: 'CORRECTIVE',
            title: 'Replace damaged safety guard.',
            tolerable_failure_filter: false,
          },
        ],
        LESSONS_LEARNT: [],
        PREVENTIVE: [],
      },
      tier_counts: { CORRECTIVE: 1, LESSONS_LEARNT: 0, PREVENTIVE: 0 },
    });

    render(<SafetyIncidentPhase6 />);

    await screen.findByText('Replace damaged safety guard.');

    expect(screen.queryByText('1 row')).toBeNull();
    expect(screen.queryByText('0 rows')).toBeNull();
  });

  it('acknowledges saved preventive actions and scrolls to saved actions', async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoView,
    });
    phase6Mocks.getIncidentPhase6Workspace.mockResolvedValue({
      ...buildWorkspace(),
      themes: [{ code: 'training', label: 'Training' }],
    });
    phase6Mocks.createIncidentRecommendation.mockResolvedValue({});

    render(<SafetyIncidentPhase6 />);

    await screen.findByText('Add Action');

    fireEvent.change(screen.getByLabelText('Type'), {
      target: { value: 'PREVENTIVE' },
    });
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Update toolbox talk before this activity.' },
    });
    fireEvent.change(screen.getByLabelText('Due date'), {
      target: { value: '2026-07-20' },
    });
    fireEvent.change(screen.getByLabelText('How much will this reduce risk?'), {
      target: { value: 'MED' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save action' }));

    await waitFor(() => {
      expect(phase6Mocks.createIncidentRecommendation).toHaveBeenCalledWith(
        'incident-1',
        {
          alarp_attested: true,
          corrective_action: {
            due_date: '2026-07-20',
            verifier_user_id: 'current-user',
          },
          description: 'Update toolbox talk before this activity.',
          estimated_effort: null,
          estimated_likelihood_reduction: 'MED',
          residual_risk_statement: 'Update toolbox talk before this activity.',
          theme_code: null,
          tier: 'PREVENTIVE',
          title: 'Update toolbox talk before this activity.',
        }
      );
    });
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Preventive saved. Review it under saved actions.'
    );
    await waitFor(() => {
      expect(scrollIntoView).toHaveBeenCalledWith({
        behavior: 'smooth',
        block: 'start',
      });
    });
  });

  it('keeps corrective action as a separate due-date-only phase', async () => {
    phase6Mocks.getIncidentPhase6Workspace.mockResolvedValue(buildWorkspace());
    phase6Mocks.createIncidentRecommendation.mockResolvedValue({});

    render(<SafetyIncidentPhase6 fixedTier="CORRECTIVE" />);

    await screen.findByText('Add Corrective Action');

    expect(screen.queryByLabelText('Type')).toBeNull();
    expect(screen.queryByText('Who Will Do and Check This?')).toBeNull();
    expect(screen.queryByLabelText('Crew assigned')).toBeNull();
    expect(screen.queryByLabelText('Checker')).toBeNull();

    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Replace the damaged guard.' },
    });
    fireEvent.change(screen.getByLabelText('Due date'), {
      target: { value: '2026-07-15' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save corrective' }));

    await waitFor(() => {
      expect(phase6Mocks.createIncidentRecommendation).toHaveBeenCalledWith(
        'incident-1',
        {
          corrective_action: {
            due_date: '2026-07-15',
            verifier_user_id: 'current-user',
          },
          description: 'Replace the damaged guard.',
          tier: 'CORRECTIVE',
          title: 'Replace the damaged guard.',
        }
      );
    });
  });

  it('edits an existing corrective action instead of adding a duplicate', async () => {
    phase6Mocks.getIncidentPhase6Workspace.mockResolvedValue({
      ...buildWorkspace(),
      corrective_actions: [
        {
          description: 'Replace damaged guard.',
          due_date: '2026-07-15',
          id: 'ca-1',
          status: 'OPEN',
          title: 'Replace damaged guard.',
          verifier_user_id: 'current-user',
        },
      ],
      recommendations: {
        CORRECTIVE: [
          {
            alarp_attested: false,
            corrective_actions: [
              {
                description: 'Replace damaged guard.',
                due_date: '2026-07-15',
                id: 'ca-1',
                status: 'OPEN',
                title: 'Replace damaged guard.',
                verifier_user_id: 'current-user',
              },
            ],
            description: 'Replace damaged guard.',
            id: 'rec-1',
            rationale: '',
            tier: 'CORRECTIVE',
            title: 'Replace damaged guard.',
            tolerable_failure_filter: false,
          },
        ],
        LESSONS_LEARNT: [],
        PREVENTIVE: [],
      },
      tier_counts: { CORRECTIVE: 1, LESSONS_LEARNT: 0, PREVENTIVE: 0 },
    });
    phase6Mocks.updateIncidentRecommendation.mockResolvedValue({});

    render(<SafetyIncidentPhase6 fixedTier="CORRECTIVE" />);

    const editButton = await screen.findByRole('button', {
      name: 'Edit Replace damaged guard.',
    });
    fireEvent.click(editButton);
    expect(await screen.findByText('Edit Corrective')).toBeTruthy();
    expect(screen.getByLabelText('Description')).toHaveValue(
      'Replace damaged guard.'
    );
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Replace damaged guard and inspect mounting.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Update corrective' }));

    await waitFor(() => {
      expect(phase6Mocks.updateIncidentRecommendation).toHaveBeenCalledWith(
        'incident-1',
        'rec-1',
        {
          corrective_action: {
            due_date: '2026-07-15',
            verifier_user_id: 'current-user',
          },
          description: 'Replace damaged guard and inspect mounting.',
          tier: 'CORRECTIVE',
          title: 'Replace damaged guard and inspect mounting.',
        }
      );
    });
    expect(phase6Mocks.createIncidentRecommendation).not.toHaveBeenCalled();
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Corrective updated. Review it under saved actions.'
    );
  });

  it('keeps preventive action separate without remaining-risk or confirmation fields', async () => {
    phase6Mocks.getIncidentPhase6Workspace.mockResolvedValue({
      ...buildWorkspace(),
      themes: [{ code: 'training', label: 'Training' }],
    });
    phase6Mocks.createIncidentRecommendation.mockResolvedValue({});

    render(<SafetyIncidentPhase6 fixedTier="PREVENTIVE" />);

    await screen.findByText('Add Preventive Action');

    expect(screen.queryByLabelText('Type')).toBeNull();
    expect(screen.queryByLabelText('Remaining risk')).toBeNull();
    expect(screen.queryByText('I confirm this will reduce risk')).toBeNull();
    expect(screen.queryByText('Prevent It Happening Again')).toBeNull();
    expect(screen.queryByLabelText('Theme')).toBeNull();
    expect(screen.queryByLabelText('Work needed')).toBeNull();

    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'Add a toolbox talk before the task.' },
    });
    fireEvent.change(screen.getByLabelText('Due date'), {
      target: { value: '2026-07-21' },
    });
    fireEvent.change(screen.getByLabelText('How much will this reduce risk?'), {
      target: { value: 'HIGH' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save preventive' }));

    await waitFor(() => {
      expect(phase6Mocks.createIncidentRecommendation).toHaveBeenCalledWith(
        'incident-1',
        {
          alarp_attested: true,
          corrective_action: {
            due_date: '2026-07-21',
            verifier_user_id: 'current-user',
          },
          description: 'Add a toolbox talk before the task.',
          estimated_effort: null,
          estimated_likelihood_reduction: 'HIGH',
          residual_risk_statement: 'Add a toolbox talk before the task.',
          theme_code: null,
          tier: 'PREVENTIVE',
          title: 'Add a toolbox talk before the task.',
        }
      );
    });
  });

  it('shows one shared risk-reduction answer for saved preventive actions', async () => {
    phase6Mocks.getIncidentPhase6Workspace.mockResolvedValue({
      ...buildWorkspace(),
      recommendations: {
        CORRECTIVE: [],
        LESSONS_LEARNT: [],
        PREVENTIVE: [
          {
            alarp_attested: true,
            corrective_actions: [
              {
                description: 'Add toolbox talk.',
                due_date: '2026-07-21',
                id: 'ca-1',
                status: 'OPEN',
                title: 'Add toolbox talk.',
                verifier_user_id: 'current-user',
              },
            ],
            description: 'Add toolbox talk.',
            estimated_likelihood_reduction: 'LOW',
            id: 'rec-1',
            rationale: '',
            tier: 'PREVENTIVE',
            title: 'Add toolbox talk.',
            tolerable_failure_filter: false,
          },
          {
            alarp_attested: true,
            corrective_actions: [
              {
                description: 'Revise checklist.',
                due_date: '2026-07-22',
                id: 'ca-2',
                status: 'OPEN',
                title: 'Revise checklist.',
                verifier_user_id: 'current-user',
              },
            ],
            description: 'Revise checklist.',
            estimated_likelihood_reduction: 'LOW',
            id: 'rec-2',
            rationale: '',
            tier: 'PREVENTIVE',
            title: 'Revise checklist.',
            tolerable_failure_filter: false,
          },
        ],
      },
      tier_counts: { CORRECTIVE: 0, LESSONS_LEARNT: 0, PREVENTIVE: 2 },
    });

    render(<SafetyIncidentPhase6 fixedTier="PREVENTIVE" />);

    const riskReductionFields = await screen.findAllByLabelText(
      'How much will this reduce risk?'
    );

    expect(riskReductionFields).toHaveLength(1);
    expect(riskReductionFields[0]).toHaveValue('LOW');
    expect(screen.queryByText('Risk reduction:')).toBeNull();
  });
});
