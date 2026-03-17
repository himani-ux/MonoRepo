/**
 * Tests for confirmation dialog flows used by FEAT-INS-004/FEAT-CAR-004 actions.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-004
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-004
 */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

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
  DialogFooter: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
  DialogDescription: ({ children }: { children: React.ReactNode }) => <p>{children}</p>,
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
}));

import { ConfirmDialog, DeleteConfirmDialog } from './confirm-dialog';

describe('ConfirmDialog', () => {
  it('test_feat_ins_004_confirm_success_calls_handler_and_closes_dialog', async () => {
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    const onOpenChange = vi.fn();

    render(
      <ConfirmDialog
        open
        onOpenChange={onOpenChange}
        title="Submit for review"
        onConfirm={onConfirm}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it('test_feat_car_004_confirm_failure_keeps_dialog_open_for_retry', async () => {
    const onConfirm = vi.fn().mockRejectedValue(new Error('failed'));
    const onOpenChange = vi.fn();

    render(
      <ConfirmDialog
        open
        onOpenChange={onOpenChange}
        title="Submit CAR"
        onConfirm={onConfirm}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => {
      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(onOpenChange).not.toHaveBeenCalledWith(false);
    });
  });

  it('test_feat_ins_004_cancel_calls_optional_oncancel_and_closes_dialog', () => {
    const onCancel = vi.fn();
    const onOpenChange = vi.fn();

    render(
      <ConfirmDialog
        open
        onOpenChange={onOpenChange}
        title="Discard"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('test_feat_ins_004_delete_confirm_dialog_uses_destructive_copy', () => {
    render(
      <DeleteConfirmDialog
        open
        onOpenChange={vi.fn()}
        itemName="inspection draft"
        onConfirm={vi.fn()}
      />
    );

    expect(screen.getByText('Delete confirmation')).toBeInTheDocument();
    expect(
      screen.getByText('Are you sure you want to delete inspection draft? This action cannot be undone.')
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
  });
});

