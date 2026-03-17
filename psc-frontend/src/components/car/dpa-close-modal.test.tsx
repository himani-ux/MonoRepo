/**
 * Tests for FEAT-CAR-007: DPA close modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-007
 * Validation Reference: Docs/VALIDATION_RULES.md Section 4.5
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const dpaCloseModalMocks = vi.hoisted(() => ({
  useDPAClose: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-cars', () => ({
  useDPAClose: (carId: string | number) => dpaCloseModalMocks.useDPAClose(carId),
}));

import { DPACloseModal } from './dpa-close-modal';

describe('DPACloseModal', () => {
  beforeEach(() => {
    dpaCloseModalMocks.useDPAClose.mockReset();
    dpaCloseModalMocks.mutateAsync.mockReset();

    dpaCloseModalMocks.mutateAsync.mockResolvedValue({});
    dpaCloseModalMocks.useDPAClose.mockReturnValue({
      mutateAsync: dpaCloseModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_car_007_happy_path_renders_comment_field_and_schedule_toggle', () => {
    render(
      <DPACloseModal
        open
        onOpenChange={vi.fn()}
        carId="car-3001"
        carNumber="PSC-2026-031"
      />
    );

    expect(screen.getByRole('heading', { name: 'DPA Close CAR' })).toBeInTheDocument();
    expect(screen.getByText('PSC-2026-031')).toBeInTheDocument();
    expect(screen.getByLabelText(/DPA Comments/i)).toBeInTheDocument();
    expect(
      screen.getByLabelText('Schedule Physical Verification')
    ).toBeInTheDocument();
  });

  it('test_feat_car_007_validation_blocks_submit_when_comment_too_short', async () => {
    render(
      <DPACloseModal
        open
        onOpenChange={vi.fn()}
        carId="car-3002"
        carNumber="PSC-2026-032"
      />
    );

    fireEvent.change(screen.getByLabelText(/DPA Comments/i), {
      target: { value: 'Too short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Close CAR' }));

    expect(
      await screen.findByText('DPA comment is required (minimum 10 characters)')
    ).toBeInTheDocument();
    expect(dpaCloseModalMocks.mutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_car_007_happy_path_submit_with_schedule_enabled_calls_mutation_and_success_true', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <DPACloseModal
        open
        onOpenChange={onOpenChange}
        carId="car-3003"
        carNumber="PSC-2026-033"
        onSuccess={onSuccess}
      />
    );

    fireEvent.change(screen.getByLabelText(/DPA Comments/i), {
      target: { value: 'DPA closure approved after review of evidence and actions.' },
    });
    fireEvent.click(screen.getByLabelText('Schedule Physical Verification'));
    fireEvent.click(screen.getByRole('button', { name: 'Close CAR' }));

    await waitFor(() => {
      expect(dpaCloseModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(dpaCloseModalMocks.useDPAClose).toHaveBeenCalledWith('car-3003');
    expect(dpaCloseModalMocks.mutateAsync).toHaveBeenCalledWith({
      comment: 'DPA closure approved after review of evidence and actions.',
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onSuccess).toHaveBeenCalledWith(true);
  });

  it('test_feat_car_007_error_state_shows_failure_banner', () => {
    dpaCloseModalMocks.useDPAClose.mockReturnValue({
      mutateAsync: dpaCloseModalMocks.mutateAsync,
      isPending: false,
      isError: true,
    });

    render(
      <DPACloseModal
        open
        onOpenChange={vi.fn()}
        carId="car-3004"
        carNumber="PSC-2026-034"
      />
    );

    expect(
      screen.getByText('Failed to close CAR. Please try again.')
    ).toBeInTheDocument();
  });
});
