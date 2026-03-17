/**
 * DPA Close Modal — DPA action to close a CAR.
 *
 * Source: APP_FLOW.md Section 2.4 — DPA Close Layout
 * Implements: PRD.md FEAT-CAR-007
 * Validation: VALIDATION_RULES.md Section 4.5
 */

import { type FC, useEffect, useState } from 'react';
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
import { useDPAClose } from '@/hooks/use-cars';

// ============================================================================
// Constants & Schema
// ============================================================================

const DPA_COMMENT_MIN = 10;

const dpaCloseSchema = z.object({
  comment: z
    .string({ required_error: 'DPA comment is required' })
    .min(DPA_COMMENT_MIN, `DPA comment is required (minimum ${DPA_COMMENT_MIN} characters)`),
});

type DPACloseFormData = z.infer<typeof dpaCloseSchema>;

// ============================================================================
// Types
// ============================================================================

export interface DPACloseModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  carId: string | number;
  carNumber: string;
  onSuccess?: (schedulePV: boolean) => void;
}

// ============================================================================
// Component
// ============================================================================

export const DPACloseModal: FC<DPACloseModalProps> = ({
  open,
  onOpenChange,
  carId,
  carNumber,
  onSuccess,
}) => {
  const closeMutation = useDPAClose(carId);
  const [schedulePV, setSchedulePV] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<DPACloseFormData>({
    resolver: zodResolver(dpaCloseSchema),
    defaultValues: { comment: '' },
  });

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      reset({ comment: '' });
      setSchedulePV(false);
    }
  }, [open, reset]);

  const onSubmit = async (data: DPACloseFormData) => {
    try {
      await closeMutation.mutateAsync(data);
      onOpenChange(false);
      onSuccess?.(schedulePV);
    } catch {
      // Error handled via mutation state
    }
  };

  const isPending = closeMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>DPA Close CAR</DialogTitle>
          <DialogDescription>
            Provide final DPA comments and optionally schedule physical verification.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <p className="text-sm text-neutral-600">
            You are closing CAR: <span className="font-semibold">{carNumber}</span>
          </p>

          {/* DPA Comment */}
          <div className="space-y-2">
            <Label htmlFor="dpa-comment" className="text-sm font-medium">
              DPA Comments <span className="text-error-500">*</span>
              <span className="ml-1 text-xs font-normal text-neutral-500">(mandatory)</span>
            </Label>
            <Textarea
              {...register('comment')}
              id="dpa-comment"
              placeholder="Enter your closing comments..."
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

          {/* Schedule Physical Verification */}
          <label className="flex cursor-pointer items-center gap-3">
            <input
              type="checkbox"
              checked={schedulePV}
              onChange={(e) => setSchedulePV(e.target.checked)}
              disabled={isPending}
              className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-neutral-700">
              Schedule Physical Verification
            </span>
          </label>

          {/* API Error */}
          {closeMutation.isError && (
            <div className="rounded-lg bg-error-50 p-3 text-sm text-error-700">
              Failed to close CAR. Please try again.
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
              Close CAR
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
