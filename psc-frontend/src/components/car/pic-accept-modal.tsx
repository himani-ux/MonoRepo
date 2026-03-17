/**
 * PIC Accept Modal — Office action to accept a submitted CAR.
 *
 * Source: APP_FLOW.md Section 2.4 — Accept Layout
 * Implements: PRD.md FEAT-CAR-005
 * Validation: VALIDATION_RULES.md Section 4.3
 */

import { type FC, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2 } from 'lucide-react';
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
import { usePICAccept } from '@/hooks/use-cars';

// ============================================================================
// Constants & Schema
// ============================================================================

const PIC_COMMENT_MIN = 10;

const picAcceptSchema = z.object({
  comment: z
    .string({ required_error: 'PIC comment is required' })
    .min(PIC_COMMENT_MIN, `PIC comment is required (minimum ${PIC_COMMENT_MIN} characters)`),
});

type PICAcceptFormData = z.infer<typeof picAcceptSchema>;

// ============================================================================
// Types
// ============================================================================

export interface PICAcceptModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  carId: string | number;
  carNumber: string;
  onSuccess?: () => void;
}

// ============================================================================
// Component
// ============================================================================

export const PICAcceptModal: FC<PICAcceptModalProps> = ({
  open,
  onOpenChange,
  carId,
  carNumber,
  onSuccess,
}) => {
  const acceptMutation = usePICAccept(carId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<PICAcceptFormData>({
    resolver: zodResolver(picAcceptSchema),
    defaultValues: { comment: '' },
  });

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      reset({ comment: '' });
    }
  }, [open, reset]);

  const onSubmit = async (data: PICAcceptFormData) => {
    try {
      await acceptMutation.mutateAsync(data);
      onOpenChange(false);
      onSuccess?.();
    } catch {
      // Error handled via mutation state
    }
  };

  const isPending = acceptMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Accept CAR</DialogTitle>
          <DialogDescription>
            Confirm acceptance by adding mandatory PIC review comments.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <p className="text-sm text-neutral-600">
            You are accepting CAR: <span className="font-semibold">{carNumber}</span>
          </p>

          {/* PIC Comment */}
          <div className="space-y-2">
            <Label htmlFor="pic-comment" className="text-sm font-medium">
              PIC Comments <span className="text-error-500">*</span>
              <span className="ml-1 text-xs font-normal text-neutral-500">(mandatory)</span>
            </Label>
            <Textarea
              {...register('comment')}
              id="pic-comment"
              placeholder="Enter your review comments..."
              rows={4}
              disabled={isPending}
              className={cn(
                errors.comment &&
                  'border-error-500 focus:border-error-500 focus:ring-error-100'
              )}
            />
            {errors.comment && (
              <p className="text-sm text-error-500">{errors.comment.message}</p>
            )}
          </div>

          {/* API Error */}
          {acceptMutation.isError && (
            <div className="rounded-lg bg-error-50 p-3 text-sm text-error-700">
              Failed to accept CAR. Please try again.
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
              Accept
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
