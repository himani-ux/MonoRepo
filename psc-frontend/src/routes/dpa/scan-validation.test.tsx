import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type {
  AuditScanValidationAttachment,
  AuditScanValidationQueue,
} from '@/schemas/audit/scan-validation';

const scanValidationMocks = vi.hoisted(() => ({
  useAuditScanValidationQueue: vi.fn(),
  useAuditScanValidationAction: vi.fn(),
  scanAction: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('@/hooks/audit/use-audit-scan-validation', () => ({
  useAuditScanValidationQueue: () => scanValidationMocks.useAuditScanValidationQueue(),
  useAuditScanValidationAction: () => scanValidationMocks.useAuditScanValidationAction(),
}));

vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({ toast: scanValidationMocks.toast }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => (
    <header>
      <h1>{title}</h1>
    </header>
  ),
}));

vi.mock('@/components/shared', () => ({
  ErrorState: ({ title, onRetry }: { title: string; onRetry: () => void }) => (
    <div>
      <div>{title}</div>
      <button type="button" onClick={onRetry}>Retry load</button>
    </div>
  ),
}));

vi.mock('@/components/shared/loading-skeleton', () => ({
  SectionSkeleton: () => <div>Section Skeleton</div>,
}));

import AuditScanValidationQueueRoute from './scan-validation';

function sampleScan(overrides: Partial<AuditScanValidationAttachment> = {}): AuditScanValidationAttachment {
  return {
    id: '11111111-1111-4111-8111-111111111111',
    audit_detail_id: '22222222-2222-4222-8222-222222222222',
    audit_finding_id: '33333333-3333-4333-8333-333333333333',
    file_name: 'NC-B-signed.pdf',
    file_path: '/uploads/audit/NC-B-signed.pdf',
    mime_type: 'application/pdf',
    category: 'SIGNED_NC_SCAN',
    attachment_version: 'FINAL',
    linked_pdf_generation_id: '44444444-4444-4444-8444-444444444444',
    pdf_hash_validation_status: 'MISMATCH_VERSION',
    validated_at: '2026-08-10T09:00:00+05:30',
    validator_message: 'QR payload does not match the active PDF version/hash.',
    uploaded_by: 'master-1',
    uploaded_at: '2026-08-10T08:55:00+05:30',
    ...overrides,
  };
}

function sampleQueue(results: AuditScanValidationAttachment[] = [sampleScan()]): AuditScanValidationQueue {
  return {
    count: results.length,
    results,
  };
}

describe('AuditScanValidationQueueRoute', () => {
  beforeEach(() => {
    scanValidationMocks.useAuditScanValidationQueue.mockReset();
    scanValidationMocks.useAuditScanValidationAction.mockReset();
    scanValidationMocks.scanAction.mockReset();
    scanValidationMocks.toast.mockReset();

    scanValidationMocks.scanAction.mockResolvedValue(sampleScan());
    scanValidationMocks.useAuditScanValidationAction.mockReturnValue({
      mutateAsync: scanValidationMocks.scanAction,
      isPending: false,
    });
  });

  it('renders scan-validation queue rows with DPA actions', async () => {
    scanValidationMocks.useAuditScanValidationQueue.mockReturnValue({
      data: sampleQueue([
        sampleScan(),
        sampleScan({
          id: '55555555-5555-4555-8555-555555555555',
          file_name: 'F602-signed.pdf',
          pdf_hash_validation_status: 'MISMATCH_VESSEL',
        }),
      ]),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditScanValidationQueueRoute />);

    expect(await screen.findByRole('heading', { name: 'Scan Validation Queue' })).toBeInTheDocument();
    expect(screen.getByText('NC-B-signed.pdf')).toBeInTheDocument();
    expect(screen.getByText('F602-signed.pdf')).toBeInTheDocument();
    expect(screen.getByText('MISMATCH_VERSION')).toBeInTheDocument();
    expect(screen.getByText('MISMATCH_VESSEL')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /accept w\/ reason/i })).toHaveLength(2);
    expect(screen.getAllByRole('button', { name: /reject - rescan/i })).toHaveLength(2);
  });

  it('validates the accept reason minimum before submitting', async () => {
    scanValidationMocks.useAuditScanValidationQueue.mockReturnValue({
      data: sampleQueue(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditScanValidationQueueRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /accept w\/ reason/i }));
    fireEvent.change(screen.getByLabelText('DPA reason'), { target: { value: 'too short' } });
    fireEvent.click(screen.getByRole('button', { name: /save acceptance/i }));

    expect(await screen.findByText('Accept reason must be at least 50 characters.')).toBeInTheDocument();
    expect(scanValidationMocks.scanAction).not.toHaveBeenCalled();
  });

  it('accepts a mismatch with reason', async () => {
    scanValidationMocks.useAuditScanValidationQueue.mockReturnValue({
      data: sampleQueue(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditScanValidationQueueRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /accept w\/ reason/i }));
    fireEvent.change(screen.getByLabelText('DPA reason'), {
      target: { value: 'DPA reviewed the scan and accepts the version mismatch for documented reasons.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save acceptance/i }));

    await waitFor(() => {
      expect(scanValidationMocks.scanAction).toHaveBeenCalledWith({
        id: '11111111-1111-4111-8111-111111111111',
        data: {
          action: 'ACCEPT_WITH_REASON',
          reason: 'DPA reviewed the scan and accepts the version mismatch for documented reasons.',
        },
      });
      expect(scanValidationMocks.toast).toHaveBeenCalledWith({ title: 'Scan mismatch accepted' });
    });
  });

  it('rejects a scan and requests rescan', async () => {
    scanValidationMocks.useAuditScanValidationQueue.mockReturnValue({
      data: sampleQueue(),
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<AuditScanValidationQueueRoute />);

    fireEvent.click(await screen.findByRole('button', { name: /reject - rescan/i }));
    fireEvent.change(screen.getByLabelText('DPA reason'), {
      target: { value: 'Request a clean signed scan from the vessel.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /request rescan/i }));

    await waitFor(() => {
      expect(scanValidationMocks.scanAction).toHaveBeenCalledWith({
        id: '11111111-1111-4111-8111-111111111111',
        data: {
          action: 'REJECT_RESCAN',
          reason: 'Request a clean signed scan from the vessel.',
        },
      });
      expect(scanValidationMocks.toast).toHaveBeenCalledWith({ title: 'Rescan requested' });
    });
  });

  it('shows an error state when the queue query fails', () => {
    const refetch = vi.fn();
    scanValidationMocks.useAuditScanValidationQueue.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Forbidden'),
      refetch,
    });

    render(<AuditScanValidationQueueRoute />);

    expect(screen.getByText('Scan validation queue not available')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /retry load/i }));
    expect(refetch).toHaveBeenCalled();
  });
});
