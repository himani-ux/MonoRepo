/**
 * Reopen CAR Modal — DPA action to reopen a DPA-closed CAR.
 *
 * Source: APP_FLOW.md Section 2.4
 * Implements: PRD.md FEAT-CAR-008
 * Validation: VALIDATION_RULES.md Section 4.4
 */

import { type FC, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Label,
  Textarea,
} from '@/components/ui';
import { useReopenCAR } from '@/hooks/use-cars';

// ============================================================================
// Schema
// ============================================================================

const REOPEN_REASON_MIN_LENGTH = 10;

const reopenSchema = z.object({
  reason: z
    .string({ required_error: 'Reopen reason is required' })
    .min(
      REOPEN_REASON_MIN_LENGTH,
      `Reopen reason must be at least ${REOPEN_REASON_MIN_LENGTH} characters`
    ),
});

type ReopenFormData = z.infer<typeof reopenSchema>;

// ============================================================================
// Types
// ============================================================================

export interface ReopenModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  carId: string | number;
  carNumber: string;
  onSuccess?: () => void;
}

// ============================================================================
// Component
// ============================================================================

export const ReopenModal: FC<ReopenModalProps> = ({
  open,
  onOpenChange,
  carId,
  carNumber,
  onSuccess,
}) => {
  const reopenMutation = useReopenCAR(carId);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<ReopenFormData>({
    resolver: zodResolver(reopenSchema),
    defaultValues: { reason: '' },
  });

  const reasonValue = watch('reason');

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      reset({ reason: '' });
    }
  }, [open, reset]);

  const onSubmit = async (data: ReopenFormData) => {
    try {
      await reopenMutation.mutateAsync(data);
      onOpenChange(false);
      onSuccess?.();
    } catch {
      // Error handled via mutation state
    }
  };

  const isPending = reopenMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Reopen CAR</DialogTitle>
          <DialogDescription>
            Provide a reason for reopening the CAR so the vessel can revise and resubmit.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <p className="text-sm text-neutral-600">
            You are reopening CAR:{' '}
            <span className="font-semibold">{carNumber}</span>
          </p>

          {/* Reopen Reason */}
          <div className="space-y-2">
            <Label htmlFor="reopen-reason" className="text-sm font-medium">
              Reopen Reason <span className="text-error-500">*</span>
              <span className="ml-1 text-xs font-normal text-neutral-500">
                (minimum {REOPEN_REASON_MIN_LENGTH} characters)
              </span>
            </Label>
            <Textarea
              {...register('reason')}
              id="reopen-reason"
              placeholder="Explain why this CAR needs to be reopened..."
              rows={4}
              disabled={isPending}
              className={cn(
                errors.reason &&
                  'border-error-500 focus:border-error-500 focus:ring-error-100'
              )}
            />
            <div className="flex items-center justify-between">
              {errors.reason ? (
                <p className="text-sm text-error-500">{errors.reason.message}</p>
              ) : (
                <span />
              )}
              <span className="text-xs text-neutral-400">
                {reasonValue?.length || 0}/{REOPEN_REASON_MIN_LENGTH}
              </span>
            </div>
          </div>

          {/* Warning Notice */}
          <div className="flex items-start gap-2 rounded-lg bg-warning-50 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning-600" />
            <p className="text-sm text-warning-700">
              The CAR will be returned to DRAFT status for the vessel to revise and
              resubmit. The previous DPA close decision will be cleared.
            </p>
          </div>

          {/* API Error */}
          {reopenMutation.isError && (
            <div className="rounded-lg bg-error-50 p-3 text-sm text-error-700">
              Failed to reopen CAR. Please try again.
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Reopen CAR
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
