/**
 * Tests for FEAT-INS-005: PIC review modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-005
 * Validation Reference: Docs/VALIDATION_RULES.md Section 2.3
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const inspectionPICReviewModalMocks = vi.hoisted(() => ({
  usePICReviewInspection: vi.fn(),
  mutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-inspections', () => ({
  usePICReviewInspection: (inspectionId: string | number) =>
    inspectionPICReviewModalMocks.usePICReviewInspection(inspectionId),
}));

import { InspectionPICReviewModal } from './inspection-pic-review-modal';

describe('InspectionPICReviewModal', () => {
  beforeEach(() => {
    inspectionPICReviewModalMocks.usePICReviewInspection.mockReset();
    inspectionPICReviewModalMocks.mutateAsync.mockReset();

    inspectionPICReviewModalMocks.mutateAsync.mockResolvedValue({});
    inspectionPICReviewModalMocks.usePICReviewInspection.mockReturnValue({
      mutateAsync: inspectionPICReviewModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_ins_005_validation_blocks_submit_when_comment_too_short', async () => {
    render(
      <InspectionPICReviewModal
        open
        onOpenChange={vi.fn()}
        inspectionId="ins-1001"
      />
    );

    fireEvent.change(screen.getByLabelText(/PIC Comments/i), {
      target: { value: 'short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Review' }));

    expect(
      await screen.findByText('PIC comment is required (minimum 10 characters)')
    ).toBeInTheDocument();
    expect(inspectionPICReviewModalMocks.mutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_ins_005_happy_path_valid_submit_calls_mutation_with_comment', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <InspectionPICReviewModal
        open
        onOpenChange={onOpenChange}
        inspectionId="ins-1002"
        onSuccess={onSuccess}
      />
    );

    fireEvent.change(screen.getByLabelText(/PIC Comments/i), {
      target: { value: 'PIC review completed with sufficient evidence.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Review' }));

    await waitFor(() => {
      expect(inspectionPICReviewModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(inspectionPICReviewModalMocks.usePICReviewInspection).toHaveBeenCalledWith('ins-1002');
    expect(inspectionPICReviewModalMocks.mutateAsync).toHaveBeenCalledWith({
      comments: 'PIC review completed with sufficient evidence.',
    });
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });
});

