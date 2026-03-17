/**
 * Tests for FEAT-INS-006: DPA close modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-006
 * Validation Reference: Docs/VALIDATION_RULES.md Section 2.4
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const inspectionDPACloseModalMocks = vi.hoisted(() => ({
  useDPACloseInspection: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-inspections', () => ({
  useDPACloseInspection: (inspectionId: string | number) =>
    inspectionDPACloseModalMocks.useDPACloseInspection(inspectionId),
}));

import { InspectionDPACloseModal } from './inspection-dpa-close-modal';

describe('InspectionDPACloseModal', () => {
  beforeEach(() => {
    inspectionDPACloseModalMocks.useDPACloseInspection.mockReset();
    inspectionDPACloseModalMocks.mutateAsync.mockReset();

    inspectionDPACloseModalMocks.mutateAsync.mockResolvedValue({});
    inspectionDPACloseModalMocks.useDPACloseInspection.mockReturnValue({
      mutateAsync: inspectionDPACloseModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_ins_006_validation_blocks_submit_when_comment_too_short', async () => {
    render(
      <InspectionDPACloseModal
        open
        onOpenChange={vi.fn()}
        inspectionId="ins-2001"
      />
    );

    fireEvent.change(screen.getByLabelText(/DPA Comments/i), {
      target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Close Inspection' }));

    expect(
      await screen.findByText('DPA comment is required (minimum 10 characters)')
    ).toBeInTheDocument();
    expect(inspectionDPACloseModalMocks.mutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_ins_006_happy_path_valid_submit_calls_mutation_with_comment', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <InspectionDPACloseModal
        open
        onOpenChange={onOpenChange}
        inspectionId="ins-2002"
        onSuccess={onSuccess}
      />
    );

    fireEvent.change(screen.getByLabelText(/DPA Comments/i), {
      target: { value: 'DPA closure approved after final review.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Close Inspection' }));

    await waitFor(() => {
      expect(inspectionDPACloseModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(inspectionDPACloseModalMocks.useDPACloseInspection).toHaveBeenCalledWith('ins-2002');
    expect(inspectionDPACloseModalMocks.mutateAsync).toHaveBeenCalledWith({
      comments: 'DPA closure approved after final review.',
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });
});

