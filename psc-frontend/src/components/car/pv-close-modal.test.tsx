/**
 * Tests for FEAT-PV-002: Close Physical Verification modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.4 - FEAT-PV-002
 * Validation Reference: Docs/VALIDATION_RULES.md Section 7.2
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const pvCloseModalMocks = vi.hoisted(() => ({
  useClosePV: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-cars', () => ({
  useClosePV: (carId: string | number) => pvCloseModalMocks.useClosePV(carId),
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
      data-testid="pv-close-date"
      type="date"
      value={value || ''}
      onChange={(e) => onChange?.(e.target.value)}
    />
  ),
}));

import { PVCloseModal } from './pv-close-modal';

describe('PVCloseModal', () => {
  beforeEach(() => {
    pvCloseModalMocks.useClosePV.mockReset();
    pvCloseModalMocks.mutateAsync.mockReset();

    pvCloseModalMocks.mutateAsync.mockResolvedValue({});
    pvCloseModalMocks.useClosePV.mockReturnValue({
      mutateAsync: pvCloseModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_pv_002_validation_requires_visit_date_and_comment_minimum', async () => {
    render(
      <PVCloseModal
        open
        onOpenChange={vi.fn()}
        carId="car-601"
        pvId="pv-601"
      />
    );

    fireEvent.change(screen.getByLabelText(/Verification Comments/i), {
      target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Close Verification' }));

    expect(await screen.findByText('Visit date is required')).toBeInTheDocument();
    expect(await screen.findByText('Comments must be at least 10 characters')).toBeInTheDocument();
    expect(pvCloseModalMocks.mutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_pv_002_happy_path_valid_submit_calls_close_mutation_and_callbacks', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <PVCloseModal
        open
        onOpenChange={onOpenChange}
        carId="car-602"
        pvId="pv-602"
        onSuccess={onSuccess}
      />
    );

    fireEvent.change(screen.getByTestId('pv-close-date'), {
      target: { value: '2026-02-15' },
    });
    fireEvent.change(screen.getByLabelText(/Verification Comments/i), {
      target: { value: 'Verified onboard and found satisfactory.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Close Verification' }));

    await waitFor(() => {
      expect(pvCloseModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(pvCloseModalMocks.useClosePV).toHaveBeenCalledWith('car-602');
    expect(pvCloseModalMocks.mutateAsync).toHaveBeenCalledWith({
      pvId: 'pv-602',
      visit_date: '2026-02-15',
      comments: 'Verified onboard and found satisfactory.',
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('test_feat_pv_002_comment_counter_updates_with_input_length', () => {
    render(
      <PVCloseModal
        open
        onOpenChange={vi.fn()}
        carId="car-603"
        pvId="pv-603"
      />
    );

    expect(screen.getByText('0 / 2000')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Verification Comments/i), {
      target: { value: '1234567890' },
    });
    expect(screen.getByText('10 / 2000')).toBeInTheDocument();
  });

  it('test_feat_pv_002_cancel_closes_modal_without_submitting', () => {
    const onOpenChange = vi.fn();

    render(
      <PVCloseModal
        open
        onOpenChange={onOpenChange}
        carId="car-604"
        pvId="pv-604"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(pvCloseModalMocks.mutateAsync).not.toHaveBeenCalled();
  });
});
