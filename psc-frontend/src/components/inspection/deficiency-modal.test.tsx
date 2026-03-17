/**
 * Tests for FEAT-INS-003: Add Deficiency (DeficiencyModal behavior)
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-003
 * Validation Reference: Docs/VALIDATION_RULES.md Section 3.1
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const deficiencyModalMocks = vi.hoisted(() => ({
  usePSCActionCodes: vi.fn(),
  useVesselCrew: vi.fn(),
  useCreateDeficiency: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-masters', () => ({
  usePSCActionCodes: () => deficiencyModalMocks.usePSCActionCodes(),
  useVesselCrew: () => deficiencyModalMocks.useVesselCrew(),
}));

vi.mock('@/hooks/use-inspections', () => ({
  useCreateDeficiency: (inspectionId: string | number) =>
    deficiencyModalMocks.useCreateDeficiency(inspectionId),
}));

// Mock Radix Select as a native <select> for testability
vi.mock('@/components/ui', async (importOriginal) => {
  const actual = (await importOriginal()) as Record<string, unknown>;
  return {
    ...actual,
    Select: ({
      value,
      onValueChange,
      disabled,
      children,
    }: {
      value?: string;
      onValueChange?: (value: string) => void;
      disabled?: boolean;
      children?: React.ReactNode;
    }) => (
      <select
        data-testid="action-code-select"
        value={value ?? ''}
        disabled={disabled}
        onChange={(e) => onValueChange?.(e.target.value)}
      >
        <option value="">Select action code</option>
        {children}
      </select>
    ),
    SelectTrigger: ({ children }: { children?: React.ReactNode }) => <>{children}</>,
    SelectValue: () => null,
    SelectContent: ({ children }: { children?: React.ReactNode }) => <>{children}</>,
    SelectItem: ({
      value,
      children,
    }: {
      value: string;
      children?: React.ReactNode;
    }) => <option value={value}>{children}</option>,
  };
});

vi.mock('@/components/shared', async () => ({
  DefCodeSelect: ({
    value,
    onChange,
    disabled,
  }: {
    value?: string;
    onChange?: (value: string) => void;
    disabled?: boolean;
  }) => (
    <input
      id="def_code"
      aria-label="DefCode"
      value={value ?? ''}
      disabled={disabled}
      onChange={(event) => onChange?.(event.target.value)}
    />
  ),
  DatePicker: ({
    value,
    onChange,
    disabled,
  }: {
    value?: string;
    onChange?: (value: string) => void;
    disabled?: boolean;
  }) => (
    <input
      aria-label="Target Date"
      type="date"
      value={value ?? ''}
      disabled={disabled}
      onChange={(event) => onChange?.(event.target.value)}
    />
  ),
}));

import { DeficiencyModal } from './deficiency-modal';

if (!globalThis.ResizeObserver) {
  vi.stubGlobal(
    'ResizeObserver',
    class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  );
}

describe('DeficiencyModal', () => {
  beforeEach(() => {
    deficiencyModalMocks.usePSCActionCodes.mockReset();
    deficiencyModalMocks.useVesselCrew.mockReset();
    deficiencyModalMocks.useCreateDeficiency.mockReset();
    deficiencyModalMocks.mutateAsync.mockReset();

    deficiencyModalMocks.usePSCActionCodes.mockReturnValue({
      data: [
        { action_code: '10', definition: 'Deficiency rectified' },
        { action_code: '30', definition: 'To be rectified' },
      ],
      isLoading: false,
    });
    deficiencyModalMocks.useVesselCrew.mockReturnValue({
      data: [],
      isLoading: false,
    });

    deficiencyModalMocks.mutateAsync.mockResolvedValue({});
    deficiencyModalMocks.useCreateDeficiency.mockReturnValue({
      mutateAsync: deficiencyModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_ins_003_happy_path_renders_modal_fields_and_car_autocreate_notice', () => {
    render(
      <DeficiencyModal
        open
        onOpenChange={vi.fn()}
        inspectionId="ins-1001"
      />
    );

    expect(
      screen.getByRole('heading', { name: 'Add Deficiency' })
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        'Complete the fields to record a deficiency and auto-create a CAR.'
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        'A CAR (Corrective Action Report) will be automatically created for this deficiency.'
      )
    ).toBeInTheDocument();
    const dialog = screen.getByRole('dialog');
    const describedById = dialog.getAttribute('aria-describedby');
    expect(describedById).toBeTruthy();
    expect(
      document.getElementById(describedById as string)
    ).toHaveTextContent(
      'Complete the fields to record a deficiency and auto-create a CAR.'
    );
    expect(screen.getByLabelText('DefCode')).toBeInTheDocument();
    expect(screen.getByLabelText('Target Date')).toBeInTheDocument();
  });

  it('test_feat_ins_003_validation_required_fields_block_submit_and_show_errors', async () => {
    render(
      <DeficiencyModal
        open
        onOpenChange={vi.fn()}
        inspectionId="ins-1001"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Add Deficiency' }));

    expect(
      await screen.findByText('Deficiency code (DefCode) is required')
    ).toBeInTheDocument();
    expect(
      screen.getByText('Description is required (10-4000 characters)')
    ).toBeInTheDocument();
    expect(deficiencyModalMocks.mutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_ins_003_happy_path_valid_submit_calls_create_and_closes_modal', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <DeficiencyModal
        open
        onOpenChange={onOpenChange}
        inspectionId="ins-2002"
        onSuccess={onSuccess}
      />
    );

    fireEvent.change(screen.getByLabelText('DefCode'), {
      target: { value: '10101' },
    });
    fireEvent.change(
      screen.getByPlaceholderText(
        'Describe the deficiency found during inspection...'
      ),
      {
        target: {
          value: 'Engine room fire damper found inoperative during inspection.',
        },
      }
    );
    // Select action code (required)
    fireEvent.change(screen.getByTestId('action-code-select'), {
      target: { value: '10' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Add Deficiency' }));

    await waitFor(() => {
      expect(deficiencyModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(deficiencyModalMocks.useCreateDeficiency).toHaveBeenCalledWith(
      'ins-2002'
    );
    expect(deficiencyModalMocks.mutateAsync).toHaveBeenCalledWith({
      def_code: '10101',
      def_text: 'Engine room fire damper found inoperative during inspection.',
      action_code: '10',
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('test_feat_ins_003_error_state_shows_failure_banner', () => {
    deficiencyModalMocks.useCreateDeficiency.mockReturnValue({
      mutateAsync: deficiencyModalMocks.mutateAsync,
      isPending: false,
      isError: true,
    });

    render(
      <DeficiencyModal
        open
        onOpenChange={vi.fn()}
        inspectionId="ins-3003"
      />
    );

    expect(
      screen.getByText('Failed to add deficiency. Please try again.')
    ).toBeInTheDocument();
  });

  it('test_feat_ins_003_cancel_closes_modal_without_submit', () => {
    const onOpenChange = vi.fn();

    render(
      <DeficiencyModal
        open
        onOpenChange={onOpenChange}
        inspectionId="ins-4004"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(deficiencyModalMocks.mutateAsync).not.toHaveBeenCalled();
  });
});
