/**
 * Inspection DPA Close Modal.
 *
 * Implements: FEAT-INS-006
 * Validation: VALIDATION_RULES.md Section 2.4
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
import { useDPACloseInspection } from '@/hooks/use-inspections';

const DPA_COMMENT_MIN = 10;

const inspectionDPACloseSchema = z.object({
  comment: z
    .string({ required_error: 'DPA comment is required' })
    .min(DPA_COMMENT_MIN, `DPA comment is required (minimum ${DPA_COMMENT_MIN} characters)`),
});

type InspectionDPACloseFormData = z.infer<typeof inspectionDPACloseSchema>;

export interface InspectionDPACloseModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  inspectionId: string | number;
  onSuccess?: () => void;
}

export const InspectionDPACloseModal: FC<InspectionDPACloseModalProps> = ({
  open,
  onOpenChange,
  inspectionId,
  onSuccess,
}) => {
  const closeMutation = useDPACloseInspection(inspectionId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<InspectionDPACloseFormData>({
    resolver: zodResolver(inspectionDPACloseSchema),
    defaultValues: { comment: '' },
  });

  useEffect(() => {
    if (open) {
      reset({ comment: '' });
    }
  }, [open, reset]);

  const onSubmit = async (data: InspectionDPACloseFormData) => {
    try {
      await closeMutation.mutateAsync({ comments: data.comment });
      onOpenChange(false);
      onSuccess?.();
    } catch {
      // Error is displayed using mutation state.
    }
  };

  const isPending = closeMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>DPA Close Inspection</DialogTitle>
          <DialogDescription>
            Enter mandatory closure comments before finalizing this inspection.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="inspection-dpa-comment" className="text-sm font-medium">
              DPA Comments <span className="text-error-500">*</span>
              <span className="ml-1 text-xs font-normal text-neutral-500">(minimum 10 characters)</span>
            </Label>
            <Textarea
              {...register('comment')}
              id="inspection-dpa-comment"
              placeholder="Enter DPA closure comments..."
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

          {closeMutation.isError && (
            <div className="rounded-lg bg-error-50 p-3 text-sm text-error-700">
              Failed to close inspection. Please try again.
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
              Close Inspection
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

