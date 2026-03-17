/**
 * Close Physical Verification modal.
 *
 * Requires visit_date and comments (min 10 chars).
 *
 * Source: FRONTEND_GUIDELINES.md Section 3.2
 * Implements: PRD.md FEAT-PV-002
 * Flow: APP_FLOW.md Section 2.3
 * Validation: VALIDATION_RULES.md (comments min 10 chars)
 */

import { type FC } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Button,
  Label,
  Textarea,
} from '@/components/ui';
import { DatePicker } from '@/components/shared';
import { useClosePV } from '@/hooks/use-cars';

const closePVSchema = z.object({
  visit_date: z.string().min(1, 'Visit date is required'),
  comments: z
    .string()
    .min(10, 'Comments must be at least 10 characters')
    .max(2000, 'Comments must not exceed 2000 characters'),
});

type ClosePVFormData = z.infer<typeof closePVSchema>;

export interface PVCloseModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  carId: string;
  pvId: string | number;
  onSuccess?: () => void;
}

export const PVCloseModal: FC<PVCloseModalProps> = ({
  open,
  onOpenChange,
  carId,
  pvId,
  onSuccess,
}) => {
  const closePVMutation = useClosePV(carId);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ClosePVFormData>({
    resolver: zodResolver(closePVSchema),
    defaultValues: {
      visit_date: '',
      comments: '',
    },
  });

  const commentsValue = watch('comments');

  const onSubmit = async (data: ClosePVFormData) => {
    try {
      await closePVMutation.mutateAsync({
        pvId,
        visit_date: data.visit_date,
        comments: data.comments,
      });
      reset();
      onOpenChange(false);
      onSuccess?.();
    } catch {
      // Error handled by mutation
    }
  };

  const handleClose = () => {
    reset();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Close Physical Verification</DialogTitle>
          <DialogDescription>
            Record the visit date and verification findings to close
            this physical verification.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Visit Date (required) */}
          <div className="space-y-2">
            <Label htmlFor="visit_date">
              Visit Date <span className="text-destructive">*</span>
            </Label>
            <DatePicker
              value={watch('visit_date') || ''}
              onChange={(val) => setValue('visit_date', val)}
              placeholder="Select visit date..."
            />
            {errors.visit_date && (
              <p className="text-sm text-destructive">{errors.visit_date.message}</p>
            )}
          </div>

          {/* Comments (required, min 10) */}
          <div className="space-y-2">
            <Label htmlFor="comments">
              Verification Comments <span className="text-destructive">*</span>
            </Label>
            <Textarea
              id="comments"
              placeholder="Enter verification findings and comments..."
              rows={4}
              {...register('comments')}
            />
            <div className="flex justify-between text-xs text-gray-500">
              {errors.comments ? (
                <p className="text-destructive">{errors.comments.message}</p>
              ) : (
                <span>Minimum 10 characters</span>
              )}
              <span>{commentsValue?.length || 0} / 2000</span>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={closePVMutation.isPending}>
              {closePVMutation.isPending ? 'Closing...' : 'Close Verification'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
