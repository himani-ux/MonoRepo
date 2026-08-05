import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const phase5Mocks = vi.hoisted(() => ({
  createIncidentPhase5Cause: vi.fn(),
  getIncidentPhase5Workspace: vi.fn(),
  getNearMissCauseOptions: vi.fn(),
  navigate: vi.fn(),
  transitionIncident: vi.fn(),
  updateIncidentPhase5Cause: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: ReactNode; to: string }) => <a href={to}>{children}</a>,
  useNavigate: () => phase5Mocks.navigate,
  useParams: () => ({ id: 'incident-1' }),
}));

vi.mock('../../../lib/api/safety', () => ({
  safetyApi: {
    createIncidentPhase5Cause: phase5Mocks.createIncidentPhase5Cause,
    getIncidentPhase5Workspace: phase5Mocks.getIncidentPhase5Workspace,
    getNearMissCauseOptions: phase5Mocks.getNearMissCauseOptions,
    transitionIncident: phase5Mocks.transitionIncident,
    updateIncidentPhase5Cause: phase5Mocks.updateIncidentPhase5Cause,
  },
}));

import SafetyIncidentPhase5 from './phase-5-workspace';

describe('SafetyIncidentPhase5', () => {
  beforeEach(() => {
    phase5Mocks.createIncidentPhase5Cause.mockReset();
    phase5Mocks.getIncidentPhase5Workspace.mockReset();
    phase5Mocks.getNearMissCauseOptions.mockReset();
    phase5Mocks.navigate.mockReset();
    phase5Mocks.transitionIncident.mockReset();
    phase5Mocks.updateIncidentPhase5Cause.mockReset();
  });

  function buildWorkspace() {
    return {
      analysis_tools_used: [],
      assessment: null,
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
          cause_factor_label: 'Human',
          cause_option_id: 'cause-1',
          cause_option_text: 'Immediate procedure gap',
          cause_other_text: '',
          cause_stage: 'IMMEDIATE',
          id: 'cause-tag-1',
          mscat_description: '',
          mscat_subcode_id: 'OTHER',
          rationale: 'Direct cause selected from investigation.',
          source_fact_id: 'fact-1',
        },
        {
          analysis_tool: 'FACT_TREE',
          causal_layer: 'INTERMEDIATE',
          cause_factor: 'MANAGEMENT',
          cause_factor_label: 'Management',
          cause_option_id: 'cause-2',
          cause_option_text: 'Planning gap',
          cause_other_text: '',
          cause_stage: 'ROOT',
          id: 'cause-tag-2',
          mscat_description: '',
          mscat_subcode_id: 'OTHER',
          rationale: 'Deeper cause selected from investigation.',
          source_fact_id: 'fact-1',
        },
        {
          analysis_tool: 'FACT_TREE',
          causal_layer: 'ROOT',
          cause_factor: 'HUMAN',
          cause_factor_label: 'Human',
          cause_option_id: 'cause-3',
          cause_option_text: 'Procedure not followed',
          cause_other_text: '',
          cause_stage: 'ROOT',
          id: 'cause-tag-3',
          mscat_description: '',
          mscat_subcode_id: 'OTHER',
          rationale: 'Root cause selected from investigation.',
          source_fact_id: 'fact-1',
        },
      ],
      facts: [
        {
          confidence: 'MEDIUM',
          evidence_summary: 'Witness note',
          fact_text: 'Crew observed the event.',
          id: 'fact-1',
          sequence_index: 1,
          source_evidence_id: 'evidence-1',
        },
      ],
      incident_id: 'incident-1',
      investigation_depth: null,
      matrix_rows: [],
      minimum_tools_required: 2,
      safeguards: [],
      schema_version: 1,
    };
  }

  it('does not show the Evidence Notes summary card in the RCA workspace', async () => {
    phase5Mocks.getNearMissCauseOptions.mockResolvedValue([]);
    phase5Mocks.getIncidentPhase5Workspace.mockResolvedValue(buildWorkspace());

    render(<SafetyIncidentPhase5 />);

    await screen.findByLabelText('Type of cause');

    expect(screen.queryByText('Evidence Notes')).toBeNull();
  });

  it('only offers Immediate Cause and Root Cause in current RCA entry', async () => {
    phase5Mocks.getNearMissCauseOptions.mockResolvedValue([]);
    phase5Mocks.getIncidentPhase5Workspace.mockResolvedValue(buildWorkspace());

    render(<SafetyIncidentPhase5 />);

    await screen.findByLabelText('Type of cause');

    const causeType = screen.getByLabelText('Type of cause');
    expect(causeType).toHaveTextContent('Immediate Cause');
    expect(causeType).toHaveTextContent('Root Cause');
    expect(causeType).not.toHaveTextContent('Intermediate Cause');
    expect(screen.queryByText('INTERMEDIATE CAUSE')).toBeNull();
  });

  it('acknowledges saved RCA causes and scrolls to the causal layers', async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoView,
    });
    phase5Mocks.getNearMissCauseOptions.mockResolvedValue([
      {
        active: true,
        cause_stage: 'ROOT',
        display_order: 1,
        factor: 'HUMAN',
        id: 'cause-option-1',
        option_text: 'Procedure not followed',
      },
    ]);
    phase5Mocks.getIncidentPhase5Workspace.mockResolvedValue(buildWorkspace());
    phase5Mocks.createIncidentPhase5Cause.mockResolvedValue({});

    render(<SafetyIncidentPhase5 />);

    await screen.findByRole('option', { name: 'Procedure not followed' });

    fireEvent.change(screen.getByLabelText('Select cause'), {
      target: { value: 'cause-option-1' },
    });
    fireEvent.change(screen.getByLabelText('Why did you select this?'), {
      target: { value: 'Procedure was not followed during the job.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add Root Cause' }));

    await waitFor(() => {
      expect(phase5Mocks.createIncidentPhase5Cause).toHaveBeenCalledWith('incident-1', {
        analysis_tool: 'FACT_TREE',
        causal_layer: 'ROOT',
        cause_factor: 'HUMAN',
        cause_option_id: 'cause-option-1',
        cause_other_text: '',
        mscat_subcode_id: 'OTHER',
        rationale: 'Procedure was not followed during the job.',
      });
    });
    expect(await screen.findByRole('status')).toHaveTextContent('Root Cause saved. Review it under Causal Layers.');
    await waitFor(() => {
      expect(scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth', block: 'start' });
    });
  });

  it('edits an existing RCA cause instead of adding a duplicate cause', async () => {
    const scrollIntoView = vi.fn();
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      configurable: true,
      value: scrollIntoView,
    });
    phase5Mocks.getNearMissCauseOptions.mockResolvedValue([
      {
        active: true,
        cause_stage: 'ROOT',
        display_order: 1,
        factor: 'HUMAN',
        id: 'cause-3',
        option_text: 'Procedure not followed',
      },
    ]);
    phase5Mocks.getIncidentPhase5Workspace.mockResolvedValue(buildWorkspace());
    phase5Mocks.updateIncidentPhase5Cause.mockResolvedValue({});

    render(<SafetyIncidentPhase5 />);

    await screen.findByRole('button', { name: 'Edit Procedure not followed' });

    fireEvent.click(screen.getByRole('button', { name: 'Edit Procedure not followed' }));

    expect(await screen.findByRole('heading', { name: 'Edit Cause' })).toBeInTheDocument();
    expect(screen.getByLabelText('Why did you select this?')).toHaveValue(
      'Root cause selected from investigation.',
    );

    fireEvent.change(screen.getByLabelText('Why did you select this?'), {
      target: { value: 'Updated root cause reason after review.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Update Root Cause' }));

    await waitFor(() => {
      expect(phase5Mocks.updateIncidentPhase5Cause).toHaveBeenCalledWith('incident-1', 'cause-tag-3', {
        analysis_tool: 'FACT_TREE',
        causal_layer: 'ROOT',
        cause_factor: 'HUMAN',
        cause_option_id: 'cause-3',
        cause_other_text: '',
        mscat_subcode_id: 'OTHER',
        rationale: 'Updated root cause reason after review.',
      });
    });
    expect(phase5Mocks.createIncidentPhase5Cause).not.toHaveBeenCalled();
    expect(await screen.findByRole('status')).toHaveTextContent('Root Cause updated. Review it under Causal Layers.');
  });

  it('continues RCA to the corrective action phase target', async () => {
    phase5Mocks.getNearMissCauseOptions.mockResolvedValue([]);
    phase5Mocks.getIncidentPhase5Workspace.mockResolvedValue(buildWorkspace());
    phase5Mocks.transitionIncident.mockResolvedValue({});

    render(<SafetyIncidentPhase5 />);

    const continueButton = await screen.findByRole('button', { name: 'Continue to Corrective Action' });
    await waitFor(() => {
      expect(continueButton).toBeEnabled();
    });

    fireEvent.click(continueButton);

    await waitFor(() => {
      expect(phase5Mocks.transitionIncident).toHaveBeenCalledWith('incident-1', { target_phase: 6 });
    });
    expect(phase5Mocks.navigate).toHaveBeenCalledWith('/safety/incidents/incident-1/phase-3');
  });
});
