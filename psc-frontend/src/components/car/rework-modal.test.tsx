/**
 * Tests for FEAT-CAR-006: Rework request modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-006
 * Validation Reference: Docs/VALIDATION_RULES.md Section 4.4
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const reworkModalMocks = vi.hoisted(() => ({
  useRequestRework: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-cars', () => ({
  useRequestRework: (carId: string | number) => reworkModalMocks.useRequestRework(carId),
}));

import { ReworkModal } from './rework-modal';

describe('ReworkModal', () => {
  beforeEach(() => {
    reworkModalMocks.useRequestRework.mockReset();
    reworkModalMocks.mutateAsync.mockReset();

    reworkModalMocks.mutateAsync.mockResolvedValue({});
    reworkModalMocks.useRequestRework.mockReturnValue({
      mutateAsync: reworkModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_car_006_happy_path_renders_warning_and_reason_counter', () => {
    render(
      <ReworkModal
        open
        onOpenChange={vi.fn()}
        carId="car-2001"
        carNumber="PSC-2026-021"
      />
    );

    expect(screen.getByRole('heading', { name: 'Request Rework' })).toBeInTheDocument();
    expect(
      screen.getByText(
        'The CAR will be returned to DRAFT status for the vessel to revise and resubmit.'
      )
    ).toBeInTheDocument();
    expect(screen.getByText('0/20')).toBeInTheDocument();
  });

  it('test_feat_car_006_validation_blocks_submit_when_reason_too_short', async () => {
    render(
      <ReworkModal
        open
        onOpenChange={vi.fn()}
        carId="car-2002"
        carNumber="PSC-2026-022"
      />
    );

    fireEvent.change(screen.getByLabelText(/Rework Reason/i), {
      target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Request Rework' }));

    expect(
      await screen.findByText('Rework reason must be at least 20 characters')
    ).toBeInTheDocument();
    expect(screen.getByText('5/20')).toBeInTheDocument();
    expect(reworkModalMocks.mutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_car_006_happy_path_valid_submit_calls_mutation_closes_modal_and_triggers_success', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <ReworkModal
        open
        onOpenChange={onOpenChange}
        carId="car-2003"
        carNumber="PSC-2026-023"
        onSuccess={onSuccess}
      />
    );

    fireEvent.change(screen.getByLabelText(/Rework Reason/i), {
      target: {
        value: 'Please provide clearer AFTER evidence and update due-date ownership.',
      },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Request Rework' }));

    await waitFor(() => {
      expect(reworkModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(reworkModalMocks.useRequestRework).toHaveBeenCalledWith('car-2003');
    expect(reworkModalMocks.mutateAsync).toHaveBeenCalledWith({
      reason: 'Please provide clearer AFTER evidence and update due-date ownership.',
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('test_feat_car_006_error_state_shows_failure_banner', () => {
    reworkModalMocks.useRequestRework.mockReturnValue({
      mutateAsync: reworkModalMocks.mutateAsync,
      isPending: false,
      isError: true,
    });

    render(
      <ReworkModal
        open
        onOpenChange={vi.fn()}
        carId="car-2004"
        carNumber="PSC-2026-024"
      />
    );

    expect(
      screen.getByText('Failed to request rework. Please try again.')
    ).toBeInTheDocument();
  });
});
