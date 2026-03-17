/**
 * Create Physical Verification modal.
 *
 * Allows scheduling a physical verification for a DPA-closed CAR.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3.2
 * Implements: PRD.md FEAT-PV-001
 * Flow: APP_FLOW.md Section 2.3
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
  Input,
  Label,
} from '@/components/ui';
import { DatePicker } from '@/components/shared';
import { useCreatePV } from '@/hooks/use-cars';

const createPVSchema = z.object({
  scheduled_date: z.string().optional(),
  visit_port: z.string().max(200).optional(),
  verifier_user_id: z.string().max(100).optional(),
});

type CreatePVFormData = z.infer<typeof createPVSchema>;

export interface PVCreateModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  carId: string;
  carNumber: string;
  onSuccess?: () => void;
}

export const PVCreateModal: FC<PVCreateModalProps> = ({
  open,
  onOpenChange,
  carId,
  carNumber,
  onSuccess,
}) => {
  const createPVMutation = useCreatePV(carId);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreatePVFormData>({
    resolver: zodResolver(createPVSchema),
    defaultValues: {
      scheduled_date: '',
      visit_port: '',
      verifier_user_id: '',
    },
  });

  const onSubmit = async (data: CreatePVFormData) => {
    try {
      await createPVMutation.mutateAsync({
        scheduled_date: data.scheduled_date || null,
        visit_port: data.visit_port || '',
        verifier_user_id: data.verifier_user_id || '',
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
          <DialogTitle>Schedule Physical Verification</DialogTitle>
          <DialogDescription>
            Schedule a physical verification for CAR {carNumber}.
            All fields are optional and can be updated later.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Scheduled Date */}
          <div className="space-y-2">
            <Label htmlFor="scheduled_date">Scheduled Date</Label>
            <DatePicker
              value={watch('scheduled_date') || ''}
              onChange={(val) => setValue('scheduled_date', val)}
              placeholder="Select date..."
            />
          </div>

          {/* Visit Port */}
          <div className="space-y-2">
            <Label htmlFor="visit_port">Visit Port</Label>
            <Input
              id="visit_port"
              placeholder="Enter port name..."
              {...register('visit_port')}
            />
            {errors.visit_port && (
              <p className="text-sm text-destructive">{errors.visit_port.message}</p>
            )}
          </div>

          {/* Verifier */}
          <div className="space-y-2">
            <Label htmlFor="verifier_user_id">Verifier ID</Label>
            <Input
              id="verifier_user_id"
              placeholder="Enter verifier employee ID..."
              {...register('verifier_user_id')}
            />
            {errors.verifier_user_id && (
              <p className="text-sm text-destructive">{errors.verifier_user_id.message}</p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={createPVMutation.isPending}>
              {createPVMutation.isPending ? 'Creating...' : 'Schedule'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
