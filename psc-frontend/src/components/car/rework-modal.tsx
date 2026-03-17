/**
 * Rework Request Modal — Office/DPA action to request rework on a CAR.
 *
 * Source: APP_FLOW.md Section 2.4 — Rework Layout
 * Implements: PRD.md FEAT-CAR-006
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
import { useRequestRework } from '@/hooks/use-cars';
import { REWORK_REASON_MIN_LENGTH } from '@/lib/utils/constants';

// ============================================================================
// Schema
// ============================================================================

const reworkSchema = z.object({
  reason: z
    .string({ required_error: 'Rework reason is required' })
    .min(
      REWORK_REASON_MIN_LENGTH,
      `Rework reason must be at least ${REWORK_REASON_MIN_LENGTH} characters`
    ),
});

type ReworkFormData = z.infer<typeof reworkSchema>;

// ============================================================================
// Types
// ============================================================================

export interface ReworkModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  carId: string | number;
  carNumber: string;
  onSuccess?: () => void;
}

// ============================================================================
// Component
// ============================================================================

export const ReworkModal: FC<ReworkModalProps> = ({
  open,
  onOpenChange,
  carId,
  carNumber,
  onSuccess,
}) => {
  const reworkMutation = useRequestRework(carId);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<ReworkFormData>({
    resolver: zodResolver(reworkSchema),
    defaultValues: { reason: '' },
  });

  const reasonValue = watch('reason');

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      reset({ reason: '' });
    }
  }, [open, reset]);

  const onSubmit = async (data: ReworkFormData) => {
    try {
      await reworkMutation.mutateAsync(data);
      onOpenChange(false);
      onSuccess?.();
    } catch {
      // Error handled via mutation state
    }
  };

  const isPending = reworkMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Request Rework</DialogTitle>
          <DialogDescription>
            Explain the required revisions so the vessel can update and resubmit the CAR.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <p className="text-sm text-neutral-600">
            You are requesting rework for CAR:{' '}
            <span className="font-semibold">{carNumber}</span>
          </p>

          {/* Rework Reason */}
          <div className="space-y-2">
            <Label htmlFor="rework-reason" className="text-sm font-medium">
              Rework Reason <span className="text-error-500">*</span>
              <span className="ml-1 text-xs font-normal text-neutral-500">
                (minimum {REWORK_REASON_MIN_LENGTH} characters)
              </span>
            </Label>
            <Textarea
              {...register('reason')}
              id="rework-reason"
              placeholder="Explain what needs to be revised..."
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
                {reasonValue?.length || 0}/{REWORK_REASON_MIN_LENGTH}
              </span>
            </div>
          </div>

          {/* Warning Notice */}
          <div className="flex items-start gap-2 rounded-lg bg-warning-50 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning-600" />
            <p className="text-sm text-warning-700">
              The CAR will be returned to DRAFT status for the vessel to revise and
              resubmit.
            </p>
          </div>

          {/* API Error */}
          {reworkMutation.isError && (
            <div className="rounded-lg bg-error-50 p-3 text-sm text-error-700">
              Failed to request rework. Please try again.
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
            <Button type="submit" variant="destructive" disabled={isPending}>
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Request Rework
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
