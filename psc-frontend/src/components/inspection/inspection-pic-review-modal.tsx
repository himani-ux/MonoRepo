/**
 * Inspection PIC Review Modal.
 *
 * Implements: FEAT-INS-005
 * Validation: VALIDATION_RULES.md Section 2.3
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
import { usePICReviewInspection } from '@/hooks/use-inspections';

const PIC_COMMENT_MIN = 10;

const inspectionPICReviewSchema = z.object({
  comment: z
    .string({ required_error: 'PIC comment is required' })
    .min(PIC_COMMENT_MIN, `PIC comment is required (minimum ${PIC_COMMENT_MIN} characters)`),
});

type InspectionPICReviewFormData = z.infer<typeof inspectionPICReviewSchema>;

export interface InspectionPICReviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  inspectionId: string | number;
  onSuccess?: () => void;
}

export const InspectionPICReviewModal: FC<InspectionPICReviewModalProps> = ({
  open,
  onOpenChange,
  inspectionId,
  onSuccess,
}) => {
  const reviewMutation = usePICReviewInspection(inspectionId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InspectionPICReviewFormData>({
    resolver: zodResolver(inspectionPICReviewSchema),
    defaultValues: { comment: '' },
  });

  useEffect(() => {
    if (open) {
      reset({ comment: '' });
    }
  }, [open, reset]);

  const onSubmit = async (data: InspectionPICReviewFormData) => {
    try {
      await reviewMutation.mutateAsync({ comments: data.comment });
      onOpenChange(false);
      onSuccess?.();
    } catch {
      // Error is displayed using mutation state.
    }
  };

  const isPending = reviewMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>PIC Review Inspection</DialogTitle>
          <DialogDescription>
            Enter mandatory review comments before moving the inspection to PIC reviewed status.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="inspection-pic-comment" className="text-sm font-medium">
              PIC Comments <span className="text-error-500">*</span>
              <span className="ml-1 text-xs font-normal text-neutral-500">(minimum 10 characters)</span>
            </Label>
            <Textarea
              {...register('comment')}
              id="inspection-pic-comment"
              placeholder="Enter PIC review comments..."
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

          {reviewMutation.isError && (
            <div className="rounded-lg bg-error-50 p-3 text-sm text-error-700">
              Failed to review inspection. Please try again.
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
              Confirm Review
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

