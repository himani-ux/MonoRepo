/**
 * Tests for FEAT-PV-001: Create Physical Verification modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.4 - FEAT-PV-001
 * Validation Reference: Docs/VALIDATION_RULES.md Section 7.1
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const pvCreateModalMocks = vi.hoisted(() => ({
  useCreatePV: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-cars', () => ({
  useCreatePV: (carId: string | number) => pvCreateModalMocks.useCreatePV(carId),
}));

vi.mock('@/components/shared', () => ({
  DatePicker: ({
    value,
    onChange,
  }: {
    value?: string;
    onChange?: (value: string) => void;
  }) => (
    <input
      data-testid="pv-create-date"
      type="date"
      value={value || ''}
      onChange={(e) => onChange?.(e.target.value)}
    />
  ),
}));

import { PVCreateModal } from './pv-create-modal';

describe('PVCreateModal', () => {
  beforeEach(() => {
    pvCreateModalMocks.useCreatePV.mockReset();
    pvCreateModalMocks.mutateAsync.mockReset();

    pvCreateModalMocks.mutateAsync.mockResolvedValue({});
    pvCreateModalMocks.useCreatePV.mockReturnValue({
      mutateAsync: pvCreateModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_pv_001_renders_modal_with_optional_fields', () => {
    render(
      <PVCreateModal
        open
        onOpenChange={vi.fn()}
        carId="car-501"
        carNumber="PSC-2026-501"
      />
    );

    expect(screen.getByRole('heading', { name: 'Schedule Physical Verification' })).toBeInTheDocument();
    expect(screen.getByText(/CAR PSC-2026-501/)).toBeInTheDocument();
    expect(screen.getByLabelText('Visit Port')).toBeInTheDocument();
    expect(screen.getByLabelText('Verifier ID')).toBeInTheDocument();
  });

  it('test_feat_pv_001_happy_path_blank_optional_values_submit_successfully', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <PVCreateModal
        open
        onOpenChange={onOpenChange}
        carId="car-502"
        carNumber="PSC-2026-502"
        onSuccess={onSuccess}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));

    await waitFor(() => {
      expect(pvCreateModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(pvCreateModalMocks.useCreatePV).toHaveBeenCalledWith('car-502');
    expect(pvCreateModalMocks.mutateAsync).toHaveBeenCalledWith({
      scheduled_date: null,
      visit_port: '',
      verifier_user_id: '',
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('test_feat_pv_001_validation_rejects_visit_port_over_200_chars', async () => {
    render(
      <PVCreateModal
        open
        onOpenChange={vi.fn()}
        carId="car-503"
        carNumber="PSC-2026-503"
      />
    );

    fireEvent.change(screen.getByLabelText('Visit Port'), {
      target: { value: 'A'.repeat(201) },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Schedule' }));

    expect(await screen.findByText('String must contain at most 200 character(s)')).toBeInTheDocument();
    expect(pvCreateModalMocks.mutateAsync).not.toHaveBeenCalled();
  });
});

