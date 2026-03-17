/**
 * Tests for FEAT-CAR-005: PIC Accept modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-005
 * Validation Reference: Docs/VALIDATION_RULES.md Section 4.3
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const picAcceptModalMocks = vi.hoisted(() => ({
  usePICAccept: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-cars', () => ({
  usePICAccept: (carId: string | number) => picAcceptModalMocks.usePICAccept(carId),
}));

import { PICAcceptModal } from './pic-accept-modal';

describe('PICAcceptModal', () => {
  beforeEach(() => {
    picAcceptModalMocks.usePICAccept.mockReset();
    picAcceptModalMocks.mutateAsync.mockReset();

    picAcceptModalMocks.mutateAsync.mockResolvedValue({});
    picAcceptModalMocks.usePICAccept.mockReturnValue({
      mutateAsync: picAcceptModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_car_005_happy_path_renders_modal_and_required_comment_field', () => {
    render(
      <PICAcceptModal
        open
        onOpenChange={vi.fn()}
        carId="car-1001"
        carNumber="PSC-2026-001"
      />
    );

    expect(screen.getByRole('heading', { name: 'Accept CAR' })).toBeInTheDocument();
    expect(screen.getByText('PSC-2026-001')).toBeInTheDocument();
    expect(screen.getByLabelText(/PIC Comments/i)).toBeInTheDocument();
  });

  it('test_feat_car_005_validation_blocks_submit_when_comment_too_short', async () => {
    render(
      <PICAcceptModal
        open
        onOpenChange={vi.fn()}
        carId="car-1002"
        carNumber="PSC-2026-002"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));

    expect(
      await screen.findByText('PIC comment is required (minimum 10 characters)')
    ).toBeInTheDocument();
    expect(picAcceptModalMocks.mutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_car_005_happy_path_valid_submit_calls_mutation_closes_modal_and_triggers_success', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <PICAcceptModal
        open
        onOpenChange={onOpenChange}
        carId="car-1003"
        carNumber="PSC-2026-003"
        onSuccess={onSuccess}
      />
    );

    fireEvent.change(screen.getByLabelText(/PIC Comments/i), {
      target: { value: 'PIC review completed and evidence quality is acceptable.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Accept' }));

    await waitFor(() => {
      expect(picAcceptModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(picAcceptModalMocks.usePICAccept).toHaveBeenCalledWith('car-1003');
    expect(picAcceptModalMocks.mutateAsync).toHaveBeenCalledWith({
      comment: 'PIC review completed and evidence quality is acceptable.',
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it('test_feat_car_005_error_state_shows_failure_banner', () => {
    picAcceptModalMocks.usePICAccept.mockReturnValue({
      mutateAsync: picAcceptModalMocks.mutateAsync,
      isPending: false,
      isError: true,
    });

    render(
      <PICAcceptModal
        open
        onOpenChange={vi.fn()}
        carId="car-1004"
        carNumber="PSC-2026-004"
      />
    );

    expect(
      screen.getByText('Failed to accept CAR. Please try again.')
    ).toBeInTheDocument();
  });
});
