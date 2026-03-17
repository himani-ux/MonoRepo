/**
 * Tests for FEAT-CAR-003 evidence upload modal behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-003
 * Validation Reference: Docs/VALIDATION_RULES.md Section 6.1
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { forwardRef } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const evidenceModalMocks = vi.hoisted(() => ({
  useUploadEvidence: vi.fn(),
  mutateAsync: vi.fn(),
  currentFile: new File(['file'], 'evidence.pdf', { type: 'application/pdf' }),
}));

vi.mock('@/hooks/use-cars', () => ({
  useUploadEvidence: (carId: string | number) => evidenceModalMocks.useUploadEvidence(carId),
}));

vi.mock('@/components/ui', () => ({
  Dialog: ({
    open,
    children,
  }: {
    open: boolean;
    children: React.ReactNode;
  }) => (open ? <div>{children}</div> : null),
  DialogContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: React.ReactNode }) => <p>{children}</p>,
  DialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Button: ({
    children,
    onClick,
    ...rest
  }: {
    children: React.ReactNode;
    onClick?: () => void;
  }) => (
    <button onClick={onClick} {...rest}>
      {children}
    </button>
  ),
  Label: ({ children, htmlFor }: { children: React.ReactNode; htmlFor?: string }) => (
    <label htmlFor={htmlFor}>{children}</label>
  ),
  Textarea: (() => {
    const MockTextarea = forwardRef<
      HTMLTextAreaElement,
      React.TextareaHTMLAttributes<HTMLTextAreaElement>
    >(({ children, ...props }, ref) => (
      <textarea ref={ref} {...props}>
        {children}
      </textarea>
    ));
    MockTextarea.displayName = 'Textarea';
    return MockTextarea;
  })(),
  Select: ({
    value,
    onValueChange,
    children,
  }: {
    value?: string;
    onValueChange?: (value: string) => void;
    children: React.ReactNode;
  }) => (
    <select
      data-testid="evidence-type"
      value={value}
      onChange={(e) => onValueChange?.(e.target.value)}
    >
      {children}
    </select>
  ),
  SelectContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectItem: ({ value, children }: { value: string; children: React.ReactNode }) => (
    <option value={value}>{children}</option>
  ),
  SelectTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SelectValue: () => null,
}));

vi.mock('@/components/shared', () => ({
  FileUpload: ({
    onChange,
    errorMessage,
  }: {
    onChange?: (file: File | null) => void;
    errorMessage?: string;
  }) => (
    <div>
      <button type="button" onClick={() => onChange?.(evidenceModalMocks.currentFile)}>
        Set File
      </button>
      {errorMessage ? <p>{errorMessage}</p> : null}
    </div>
  ),
}));

import { EvidenceUploadModal } from './evidence-upload-modal';

describe('EvidenceUploadModal', () => {
  beforeEach(() => {
    evidenceModalMocks.useUploadEvidence.mockReset();
    evidenceModalMocks.mutateAsync.mockReset();

    evidenceModalMocks.mutateAsync.mockResolvedValue({});
    evidenceModalMocks.useUploadEvidence.mockReturnValue({
      mutateAsync: evidenceModalMocks.mutateAsync,
      isPending: false,
      isError: false,
    });
  });

  it('test_feat_car_003_submit_without_file_shows_required_file_error', async () => {
    render(
      <EvidenceUploadModal
        open
        onOpenChange={vi.fn()}
        carId="car-1"
      />
    );

    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: 'Before photo from engine room' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));

    expect(await screen.findByText('Please select a file')).toBeInTheDocument();
    expect(evidenceModalMocks.mutateAsync).not.toHaveBeenCalled();
  });

  it('test_feat_car_003_happy_path_upload_calls_api_and_closes_modal', async () => {
    const onOpenChange = vi.fn();
    const onSuccess = vi.fn();

    render(
      <EvidenceUploadModal
        open
        onOpenChange={onOpenChange}
        carId="car-2"
        onSuccess={onSuccess}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Set File' }));
    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: 'After rectification evidence image' },
    });
    fireEvent.change(screen.getByTestId('evidence-type'), {
      target: { value: 'AFTER' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() => {
      expect(evidenceModalMocks.mutateAsync).toHaveBeenCalledWith({
        file: evidenceModalMocks.currentFile,
        evidence_type: 'AFTER',
        description: 'After rectification evidence image',
      });
      expect(onOpenChange).toHaveBeenCalledWith(false);
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it('test_feat_car_003_upload_failure_does_not_close_modal', async () => {
    const onOpenChange = vi.fn();
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    evidenceModalMocks.mutateAsync.mockRejectedValueOnce(new Error('upload failed'));

    render(
      <EvidenceUploadModal
        open
        onOpenChange={onOpenChange}
        carId="car-3"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Set File' }));
    fireEvent.change(screen.getByLabelText(/Description/i), {
      target: { value: 'Supporting evidence photo' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Upload' }));

    await waitFor(() => {
      expect(evidenceModalMocks.mutateAsync).toHaveBeenCalledTimes(1);
    });
    expect(onOpenChange).not.toHaveBeenCalledWith(false);
    errorSpy.mockRestore();
  });

  it('test_feat_car_003_cancel_button_closes_modal', () => {
    const onOpenChange = vi.fn();
    render(
      <EvidenceUploadModal
        open
        onOpenChange={onOpenChange}
        carId="car-4"
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
