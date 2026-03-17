import { useState, type FC, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Button,
} from '@/components/ui';
import { cn } from '@/lib/utils';

/**
 * Confirmation dialog component per DESIGN_SYSTEM.md Section 11.5
 * Used for confirming destructive or important actions
 */

export interface ConfirmDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Handler when dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Dialog title */
  title: string;
  /** Dialog description */
  description?: string;
  /** Custom content to render in the dialog body */
  children?: ReactNode;
  /** Confirm button label (default: "Confirm") */
  confirmLabel?: string;
  /** Cancel button label (default: "Cancel") */
  cancelLabel?: string;
  /** Confirm handler */
  onConfirm: () => void | Promise<void>;
  /** Cancel handler */
  onCancel?: () => void;
  /** Whether this is a destructive action (shows red button) */
  variant?: 'default' | 'destructive';
  /** Show warning icon */
  showIcon?: boolean;
  /** Disable confirm button */
  confirmDisabled?: boolean;
}

export const ConfirmDialog: FC<ConfirmDialogProps> = ({
  open,
  onOpenChange,
  title,
  description,
  children,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  variant = 'default',
  showIcon = false,
  confirmDisabled = false,
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } catch {
      // Error handling should be done in onConfirm
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    onCancel?.();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-start gap-3">
            {showIcon && variant === 'destructive' && (
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-error-100">
                <AlertTriangle className="h-5 w-5 text-error-600" />
              </div>
            )}
            <div className="flex-1">
              <DialogTitle
                className={cn(
                  variant === 'destructive' && showIcon && 'mt-0.5'
                )}
              >
                {title}
              </DialogTitle>
              {description && (
                <DialogDescription className="mt-1">
                  {description}
                </DialogDescription>
              )}
            </div>
          </div>
        </DialogHeader>

        {children && <div className="py-2">{children}</div>}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant={variant === 'destructive' ? 'destructive' : 'default'}
            onClick={handleConfirm}
            disabled={isLoading || confirmDisabled}
          >
            {isLoading ? 'Please wait...' : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// ============================================================================
// Pre-configured Confirm Dialogs
// ============================================================================

export interface DeleteConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  itemName?: string;
  onConfirm: () => void | Promise<void>;
}

export const DeleteConfirmDialog: FC<DeleteConfirmDialogProps> = ({
  open,
  onOpenChange,
  itemName = 'this item',
  onConfirm,
}) => (
  <ConfirmDialog
    open={open}
    onOpenChange={onOpenChange}
    title="Delete confirmation"
    description={`Are you sure you want to delete ${itemName}? This action cannot be undone.`}
    confirmLabel="Delete"
    variant="destructive"
    showIcon
    onConfirm={onConfirm}
  />
);

export interface DiscardChangesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void | Promise<void>;
}

export const DiscardChangesDialog: FC<DiscardChangesDialogProps> = ({
  open,
  onOpenChange,
  onConfirm,
}) => (
  <ConfirmDialog
    open={open}
    onOpenChange={onOpenChange}
    title="Discard changes?"
    description="You have unsaved changes. Are you sure you want to leave? Your changes will be lost."
    confirmLabel="Discard"
    variant="destructive"
    onConfirm={onConfirm}
  />
);

export interface SubmitConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  entityName?: string;
  onConfirm: () => void | Promise<void>;
}

export const SubmitConfirmDialog: FC<SubmitConfirmDialogProps> = ({
  open,
  onOpenChange,
  entityName = 'this item',
  onConfirm,
}) => (
  <ConfirmDialog
    open={open}
    onOpenChange={onOpenChange}
    title="Submit for review"
    description={`Are you sure you want to submit ${entityName}? You won't be able to make changes after submission.`}
    confirmLabel="Submit"
    onConfirm={onConfirm}
  />
);
