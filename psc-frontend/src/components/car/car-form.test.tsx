/**
 * Tests for FEAT-CAR-002: Edit CAR (Draft) (CARForm behavior)
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-002
 * Validation Reference: Docs/VALIDATION_RULES.md Sections 4.1, 4.2, 5.1
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const carFormMocks = vi.hoisted(() => ({
  useCLCHierarchy: vi.fn(),
  createActionMutateAsync: vi.fn(),
  updateActionMutateAsync: vi.fn(),
  deleteActionMutateAsync: vi.fn(),
  completeActionMutateAsync: vi.fn(),
  deleteEvidenceMutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-masters', () => ({
  useCLCHierarchy: () => carFormMocks.useCLCHierarchy(),
}));

vi.mock('@/hooks/use-cars', () => ({
  useCreateAction: () => ({
    mutateAsync: carFormMocks.createActionMutateAsync,
    isPending: false,
  }),
  useUpdateAction: () => ({
    mutateAsync: carFormMocks.updateActionMutateAsync,
    isPending: false,
  }),
  useDeleteAction: () => ({
    mutateAsync: carFormMocks.deleteActionMutateAsync,
    isPending: false,
  }),
  useCompleteAction: () => ({
    mutateAsync: carFormMocks.completeActionMutateAsync,
    isPending: false,
  }),
  useDeleteEvidence: () => ({
    mutateAsync: carFormMocks.deleteEvidenceMutateAsync,
    isPending: false,
  }),
}));

vi.mock('@/components/shared', async () => ({
  DatePicker: ({
    value,
    onChange,
  }: {
    value?: string;
    onChange?: (value: string) => void;
  }) => (
    <input
      aria-label="Date Picker"
      type="date"
      value={value ?? ''}
      onChange={(event) => onChange?.(event.target.value)}
    />
  ),
  ConfirmDialog: ({
    open,
    title,
    description,
    confirmLabel = 'Confirm',
    confirmDisabled,
    onConfirm,
    onOpenChange,
    children,
  }: {
    open: boolean;
    title: string;
    description?: string;
    confirmLabel?: string;
    confirmDisabled?: boolean;
    onConfirm?: () => void;
    onOpenChange?: (open: boolean) => void;
    children?: React.ReactNode;
  }) =>
    open ? (
      <div>
        <h2>{title}</h2>
        {description ? <p>{description}</p> : null}
        {children}
        <button
          type="button"
          disabled={confirmDisabled}
          onClick={() => onConfirm?.()}
        >
          {confirmLabel}
        </button>
        <button type="button" onClick={() => onOpenChange?.(false)}>
          Close
        </button>
      </div>
    ) : null,
}));

import { CARForm } from './car-form';

function isoDateDaysOffset(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function buildCar(overrides: Record<string, unknown> = {}) {
  return {
    id: 101,
    car_number: 'PSC-2026-001',
    status: 'DRAFT',
    status_display: 'Draft',
    root_cause_summary:
      'Root cause summary for this CAR is detailed enough to satisfy minimum length checks.',
    target_date: isoDateDaysOffset(30),
    clc_items: [{ id: 1, clc_item_id: 'CLC001', custom_cause_text: '' }],
    corrective_actions: [
      {
        id: 11,
        action_type: 'IMMEDIATE',
        description:
          'Immediate corrective action executed onboard with detailed procedural steps and verification.',
        due_date: isoDateDaysOffset(7),
        is_completed: false,
        completed_at: null,
        completion_remarks: null,
      },
      {
        id: 12,
        action_type: 'LONG_TERM',
        description:
          'Long-term preventive action planned with assigned ownership, milestones, and follow-up controls.',
        due_date: isoDateDaysOffset(21),
        is_completed: false,
        completed_at: null,
        completion_remarks: null,
      },
    ],
    evidence: [
      {
        id: 'e-before',
        evidence_type: 'BEFORE',
        file_name: 'before.jpg',
        mime_type: 'image/jpeg',
        description: 'Before correction image',
        uploaded_at: '2026-02-08T09:00:00Z',
        file_size: 600000,
      },
      {
        id: 'e-after',
        evidence_type: 'AFTER',
        file_name: 'after.jpg',
        mime_type: 'image/jpeg',
        description: 'After correction image',
        uploaded_at: '2026-02-08T10:00:00Z',
        file_size: 610000,
      },
    ],
    deficiency: {
      id: 'def-1',
      def_code: '10101',
      description: 'Expired certificate found during inspection',
      is_cleared: false,
    },
    ...overrides,
  } as any;
}

describe('CARForm', () => {
  beforeEach(() => {
    carFormMocks.useCLCHierarchy.mockReset();
    carFormMocks.createActionMutateAsync.mockReset();
    carFormMocks.updateActionMutateAsync.mockReset();
    carFormMocks.deleteActionMutateAsync.mockReset();
    carFormMocks.completeActionMutateAsync.mockReset();
    carFormMocks.deleteEvidenceMutateAsync.mockReset();

    carFormMocks.useCLCHierarchy.mockReturnValue({
      data: {
        immediate_causes: {
          actions: {
            '1': { name: 'Following Procedures', items: { '1-1': 'Violation by individual' } },
          },
          conditions: {},
        },
        root_causes: {
          personal_factors: {
            P6: { name: 'Skill Level', items: { CLC001: 'Training' } },
          },
          job_factors: {},
        },
      },
      isLoading: false,
    });

    carFormMocks.createActionMutateAsync.mockResolvedValue({});
    carFormMocks.updateActionMutateAsync.mockResolvedValue({});
    carFormMocks.deleteActionMutateAsync.mockResolvedValue({});
    carFormMocks.completeActionMutateAsync.mockResolvedValue({});
    carFormMocks.deleteEvidenceMutateAsync.mockResolvedValue({});
  });

  it('test_feat_car_002_happy_path_save_draft_calls_handler_with_dirty_payload', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue(undefined);
    const updatedSummary =
      'Updated root cause summary remains detailed enough to save without resending unchanged target date.';

    render(
      <CARForm
        car={buildCar({ target_date: '2000-01-01' })}
        onSaveDraft={onSaveDraft}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
        onCancel={vi.fn()}
      />
    );

    fireEvent.change(
      screen.getByPlaceholderText(
        'Describe the root cause analysis in detail (minimum 50 characters)...'
      ),
      { target: { value: updatedSummary } }
    );
    fireEvent.click(screen.getByRole('button', { name: 'Save Draft' }));

    await waitFor(() => {
      expect(onSaveDraft).toHaveBeenCalledTimes(1);
    });
    expect(onSaveDraft).toHaveBeenCalledWith({
      root_cause_summary: updatedSummary,
    });
  });

  it('test_feat_car_002_validation_submit_with_missing_requirements_shows_error_dialog_and_blocks_submit', () => {
    const onSaveDraft = vi.fn().mockResolvedValue(undefined);
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <CARForm
        car={buildCar({
          root_cause_summary: 'too short',
          clc_items: [],
          corrective_actions: [],
          evidence: [],
        })}
        onSaveDraft={onSaveDraft}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Submit CAR' }));

    expect(screen.getByText('Cannot Submit CAR')).toBeInTheDocument();
    expect(
      screen.getByText('At least one immediate corrective action is required')
    ).toBeInTheDocument();
    expect(
      screen.getByText('At least one AFTER evidence is required')
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('test_feat_car_002_happy_path_submit_confirms_then_runs_save_and_submit_for_dirty_fields', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue(undefined);
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <CARForm
        car={buildCar()}
        onSaveDraft={onSaveDraft}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />
    );

    fireEvent.change(
      screen.getByPlaceholderText(
        'Describe the root cause analysis in detail (minimum 50 characters)...'
      ),
      {
        target: {
          value:
            'Updated root cause summary remains detailed enough to satisfy submission checks.',
        },
      }
    );
    fireEvent.click(screen.getByRole('button', { name: 'Submit CAR' }));

    expect(
      screen.getByRole('heading', { name: 'Submit CAR' })
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(onSaveDraft).toHaveBeenCalledTimes(1);
    });
    expect(onSaveDraft).toHaveBeenCalledWith({
      root_cause_summary:
        'Updated root cause summary remains detailed enough to satisfy submission checks.',
    });
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
  });

  it('test_feat_car_002_start_review_does_not_resave_unchanged_overdue_target_date', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue(undefined);
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <CARForm
        car={buildCar({ target_date: '2000-01-01' })}
        onSaveDraft={onSaveDraft}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        submitLabel="Start Review"
        submitDescription='This will perform "Start Review" on the CAR. Continue?'
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Start Review' }));
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(onSaveDraft).not.toHaveBeenCalled();
  });

  it('test_feat_car_002_evidence_upload_buttons_trigger_before_and_after_callbacks', () => {
    const onUploadEvidence = vi.fn();

    render(
      <CARForm
        car={buildCar()}
        onSaveDraft={vi.fn().mockResolvedValue(undefined)}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
        onCancel={vi.fn()}
        onUploadEvidence={onUploadEvidence}
      />
    );

    const uploadButtons = screen.getAllByRole('button', { name: 'Upload' });
    fireEvent.click(uploadButtons[0]);
    fireEvent.click(uploadButtons[1]);

    expect(onUploadEvidence).toHaveBeenNthCalledWith(1, 'BEFORE');
    expect(onUploadEvidence).toHaveBeenNthCalledWith(2, 'AFTER');
  });

  it('test_feat_car_002_corrective_actions_edit_in_place_without_completion_flow', async () => {
    render(
      <CARForm
        car={buildCar()}
        onSaveDraft={vi.fn().mockResolvedValue(undefined)}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
        onCancel={vi.fn()}
      />
    );

    expect(screen.queryByRole('button', { name: 'Done' })).not.toBeInTheDocument();

    fireEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0]);
    fireEvent.change(
      screen.getByDisplayValue(
        'Immediate corrective action executed onboard with detailed procedural steps and verification.'
      ),
      {
        target: {
          value:
            'Immediate corrective action updated with revised onboard procedure and follow-up notes.',
        },
      }
    );
    fireEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() => {
      expect(carFormMocks.updateActionMutateAsync).toHaveBeenCalledWith({
        actionId: 11,
        data: {
          description:
            'Immediate corrective action updated with revised onboard procedure and follow-up notes.',
        },
      });
    });
    expect(carFormMocks.completeActionMutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_car_002_completed_actions_hide_completion_date_and_remain_editable', () => {
    render(
      <CARForm
        car={buildCar({
          corrective_actions: [
            {
              id: 11,
              action_type: 'IMMEDIATE',
              description:
                'Immediate corrective action executed onboard with detailed procedural steps and verification.',
              due_date: '2026-02-12',
              is_completed: true,
              completed_at: '2026-02-13T09:30:00Z',
              completion_remarks: 'Completed by vessel crew',
            },
            {
              id: 12,
              action_type: 'LONG_TERM',
              description:
                'Long-term preventive action planned with assigned ownership, milestones, and follow-up controls.',
              due_date: '2026-02-28',
              is_completed: false,
              completed_at: null,
              completion_remarks: null,
            },
          ],
        })}
        onSaveDraft={vi.fn().mockResolvedValue(undefined)}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
        onCancel={vi.fn()}
      />
    );

    expect(screen.queryByText(/Completed:/)).not.toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Edit' })).toHaveLength(2);
  });

  it('test_feat_car_002_dirty_cancel_opens_discard_confirmation_and_calls_cancel_on_confirm', () => {
    const onCancel = vi.fn();

    render(
      <CARForm
        car={buildCar()}
        onSaveDraft={vi.fn().mockResolvedValue(undefined)}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
        onCancel={onCancel}
      />
    );

    fireEvent.change(
      screen.getByPlaceholderText(
        'Describe the root cause analysis in detail (minimum 50 characters)...'
      ),
      {
        target: { value: 'Updated root cause summary text to mark the form dirty.' },
      }
    );
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(screen.getByText('Discard Changes?')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Discard' }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('test_feat_car_002_evidence_filename_is_clickable_and_delete_triggers_mutation', async () => {
    render(
      <CARForm
        car={buildCar({
          evidence: [
            {
              id: 'e-before',
              evidence_type: 'BEFORE',
              file_name: 'before.jpg',
              file_path: '/uploads/before.jpg',
              mime_type: 'image/jpeg',
              description: 'Before correction image',
              uploaded_at: '2026-02-08T09:00:00Z',
              file_size: 600000,
            },
            {
              id: 'e-after',
              evidence_type: 'AFTER',
              file_name: 'after.jpg',
              file_path: '/uploads/after.jpg',
              mime_type: 'image/jpeg',
              description: 'After correction image',
              uploaded_at: '2026-02-08T10:00:00Z',
              file_size: 610000,
            },
          ],
        })}
        onSaveDraft={vi.fn().mockResolvedValue(undefined)}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
        onCancel={vi.fn()}
      />
    );

    const fileLink = screen.getByRole('link', { name: 'before.jpg' });
    expect(fileLink).toHaveAttribute('href', '/uploads/before.jpg');

    fireEvent.click(screen.getByLabelText('Delete evidence before.jpg'));
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(carFormMocks.deleteEvidenceMutateAsync).toHaveBeenCalledWith('e-before');
    });
  });
});
