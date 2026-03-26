/**
 * Tests for FEAT-CAR-003: Upload CAR Evidence (EvidenceSection behavior)
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-003
 * Validation Reference: Docs/VALIDATION_RULES.md Section 6.1
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const evidenceSectionMocks = vi.hoisted(() => ({
  deleteEvidenceMutateAsync: vi.fn(),
}));

vi.mock('@/hooks/use-cars', () => ({
  useDeleteEvidence: () => ({
    mutateAsync: evidenceSectionMocks.deleteEvidenceMutateAsync,
    isPending: false,
  }),
}));

vi.mock('@/components/shared', () => ({
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

import { EvidenceSection } from './evidence-section';

function buildEvidence(overrides: Record<string, unknown> = {}) {
  return {
    id: crypto.randomUUID(),
    evidence_type: 'BEFORE',
    file_name: 'evidence.jpg',
    file_path: '/uploads/evidence.jpg',
    file_size: 600_000,
    mime_type: 'image/jpeg',
    description: 'Evidence attachment',
    uploaded_at: '2026-02-08T09:30:00Z',
    ...overrides,
  } as any;
}

describe('EvidenceSection', () => {
  beforeEach(() => {
    evidenceSectionMocks.deleteEvidenceMutateAsync.mockReset();
    evidenceSectionMocks.deleteEvidenceMutateAsync.mockResolvedValue(undefined);
  });

  it('test_feat_car_003_empty_state_shows_missing_before_and_after_warning_and_upload_trigger', () => {
    const onUpload = vi.fn();

    render(<EvidenceSection evidence={[]} onUpload={onUpload} />);

    expect(
      screen.getByText('Missing BEFORE and AFTER evidence (required for submission)')
    ).toBeInTheDocument();
    expect(screen.getByText('No evidence uploaded yet')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));
    expect(onUpload).toHaveBeenCalledTimes(1);
  });

  it('test_feat_car_003_warning_message_indicates_missing_after_only_when_before_exists', () => {
    render(<EvidenceSection evidence={[buildEvidence({ evidence_type: 'BEFORE' })]} />);

    expect(
      screen.getByText('Missing AFTER evidence (required for submission)')
    ).toBeInTheDocument();
    expect(screen.queryByText('Missing BEFORE evidence (required for submission)')).not.toBeInTheDocument();
  });

  it('test_feat_car_003_warning_message_indicates_missing_before_only_when_after_exists', () => {
    render(<EvidenceSection evidence={[buildEvidence({ evidence_type: 'AFTER' })]} />);

    expect(
      screen.getByText('Missing BEFORE evidence (required for submission)')
    ).toBeInTheDocument();
    expect(screen.queryByText('Missing AFTER evidence (required for submission)')).not.toBeInTheDocument();
  });

  it('test_feat_car_003_happy_path_groups_before_after_and_other_sections_without_missing_warning', () => {
    render(
      <EvidenceSection
        evidence={[
          buildEvidence({
            id: 'ev-before',
            evidence_type: 'BEFORE',
            file_name: 'before.jpg',
          }),
          buildEvidence({
            id: 'ev-after',
            evidence_type: 'AFTER',
            file_name: 'after.jpg',
          }),
          buildEvidence({
            id: 'ev-other',
            evidence_type: 'OTHER',
            file_name: 'report.pdf',
            mime_type: 'application/pdf',
            file_size: 1_500_000,
          }),
        ]}
      />
    );

    expect(screen.getByText('BEFORE (1)')).toBeInTheDocument();
    expect(screen.getByText('AFTER (1)')).toBeInTheDocument();
    expect(screen.getByText('OTHER (1)')).toBeInTheDocument();
    expect(screen.getByText('before.jpg')).toBeInTheDocument();
    expect(screen.getByText('after.jpg')).toBeInTheDocument();
    expect(screen.getByText('report.pdf')).toBeInTheDocument();
    expect(screen.queryByText(/Missing .* evidence/)).not.toBeInTheDocument();
  });

  it('test_feat_car_003_delete_button_deletes_evidence_when_car_id_is_available', async () => {
    render(
      <EvidenceSection
        carId="car-1"
        evidence={[buildEvidence({ id: 'ev-before', file_name: 'before.jpg' })]}
      />
    );

    fireEvent.click(screen.getByLabelText('Delete evidence before.jpg'));
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(evidenceSectionMocks.deleteEvidenceMutateAsync).toHaveBeenCalledWith('ev-before');
    });
  });
});
