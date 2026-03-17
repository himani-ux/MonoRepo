/**
 * Add Deficiency Modal
 *
 * Per APP_FLOW.md Section 2.2 and IMPLEMENTATION_PLAN.md Step 4.6
 * Features:
 * - DefCode search select (code displayed prominently per LESSONS.md)
 * - CAR auto-creation notice
 * - Form validation per VALIDATION_RULES.md Section 3.1
 */

import { type FC, useEffect, useMemo } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Info, Loader2, UserCheck } from 'lucide-react';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { DefCodeSelect, DatePicker } from '@/components/shared';
import { usePSCActionCodes, useVesselCrew } from '@/hooks/use-masters';
import { useCreateDeficiency } from '@/hooks/use-inspections';
import {
  addDeficiencySchema,
  addDeficiencyDefaults,
  type AddDeficiencyFormData,
} from '@/lib/validations/deficiency';

// ============================================================================
// Types
// ============================================================================

export interface DeficiencyModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Handler to change open state */
  onOpenChange: (open: boolean) => void;
  /** Inspection ID to add deficiency to */
  inspectionId: number | string;
  /** Vessel ID for crew member lookup */
  vesselId?: string;
  /** Callback when deficiency is successfully created */
  onSuccess?: () => void;
  /** Additional class names */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export const DeficiencyModal: FC<DeficiencyModalProps> = ({
  open,
  onOpenChange,
  inspectionId,
  vesselId,
  onSuccess,
  className,
}) => {
  // Fetch action codes for dropdown
  const { data: actionCodes = [], isLoading: isLoadingActionCodes } =
    usePSCActionCodes();

  // Fetch crew members for assignment dropdown
  const { data: crewMembers = [], isLoading: isLoadingCrew } =
    useVesselCrew(vesselId);
  console.log('crew members:', crewMembers)

  // Create deficiency mutation
  const createDeficiencyMutation = useCreateDeficiency(inspectionId);

  // Form setup
  const {
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<AddDeficiencyFormData>({
    resolver: zodResolver(addDeficiencySchema),
    defaultValues: addDeficiencyDefaults,
  });

  // Watch selected crew to show reviewer preview
  const selectedCrewId = watch('assigned_crew_id');

  // Compute the auto-reviewer preview from selected crew's rank
  const reviewerPreview = useMemo(() => {
    if (!selectedCrewId || crewMembers.length === 0) return null;
    const selected = crewMembers.find((c) => c.crew_id === selectedCrewId);
    if (!selected) return null;

    const rankLower = (selected.rank_name || '').toLowerCase();

    // Determine reviewer rank based on owner rank
    let targetRanks: string[] = [];
    if (rankLower.includes('second engineer') || rankLower.includes('2nd engineer') || rankLower.includes('2/e')) {
      targetRanks = ['chief engineer', 'c/e'];
    } else if (
      rankLower.includes('chief engineer') || rankLower.includes('c/e') ||
      rankLower.includes('chief officer') || rankLower.includes('chief mate') || rankLower.includes('c/o')
    ) {
      targetRanks = ['master', 'captain'];
    }

    if (targetRanks.length === 0) return null;

    const reviewer = crewMembers.find((c) =>
      c.rank_name && targetRanks.some((kw) => c.rank_name.toLowerCase().includes(kw))
    );

    return reviewer
      ? `${reviewer.rank_name} - ${reviewer.display_name}`
      : 'No matching reviewer found on vessel';
  }, [selectedCrewId, crewMembers]);

  // Reset form when modal closes
  useEffect(() => {
    if (!open) {
      reset(addDeficiencyDefaults);
    }
  }, [open, reset]);

  // Handle form submission
  const onSubmit = async (data: AddDeficiencyFormData) => {
    try {
      await createDeficiencyMutation.mutateAsync({
        def_code: data.def_code,
        def_text: data.def_text,
        action_code: data.action_code,
        target_date: data.target_date || undefined,
        assigned_crew_id: data.assigned_crew_id || undefined,
      });

      // Close modal and notify parent
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      // Error handling is done via mutation state
      console.error('Failed to create deficiency:', error);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  const isPending = isSubmitting || createDeficiencyMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn('sm:max-w-lg', className)}>
        <DialogHeader>
          <DialogTitle>Add Deficiency</DialogTitle>
          <DialogDescription>
            Complete the fields to record a deficiency and auto-create a CAR.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* DefCode Select - PROMINENTLY DISPLAYED */}
          <div className="space-y-2">
            <Label htmlFor="def_code" className="text-sm font-medium">
              DefCode <span className="text-error-500">*</span>
            </Label>
            <Controller
              name="def_code"
              control={control}
              render={({ field }) => (
                <DefCodeSelect
                  value={field.value}
                  onChange={(code) => field.onChange(code)}
                  placeholder="Search or select deficiency code..."
                  error={!!errors.def_code}
                  disabled={isPending}
                />
              )}
            />
            {errors.def_code && (
              <p className="text-sm text-error-500">{errors.def_code.message}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="def_text" className="text-sm font-medium">
              Description <span className="text-error-500">*</span>
            </Label>
            <Controller
              name="def_text"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  id="def_text"
                  placeholder="Describe the deficiency found during inspection..."
                  rows={4}
                  disabled={isPending}
                  className={cn(
                    errors.def_text &&
                    'border-error-500 focus:border-error-500 focus:ring-error-100'
                  )}
                />
              )}
            />
            {errors.def_text && (
              <p className="text-sm text-error-500">{errors.def_text.message}</p>
            )}
          </div>

          {/* Action Code - Required */}
          <div className="space-y-2">
            <Label htmlFor="action_code" className="text-sm font-medium">
              Action Code <span className="text-error-500">*</span>
            </Label>
            <Controller
              name="action_code"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value ? String(field.value) : ''}
                  onValueChange={(value) => field.onChange(value)}
                  disabled={isPending || isLoadingActionCodes}
                >
                  <SelectTrigger
                    id="action_code"
                    className={cn(
                      errors.action_code &&
                      'border-error-500 focus:border-error-500 focus:ring-error-100'
                    )}
                  >
                    <SelectValue placeholder="Select action code" />
                  </SelectTrigger>
                  <SelectContent>
                    {actionCodes.map((ac) => (
                      <SelectItem
                        key={String(ac.action_code)}
                        value={String(ac.action_code)}
                      >
                        <span className="font-mono font-medium">
                          {ac.action_code}
                        </span>
                        <span className="ml-2 text-neutral-600">
                          - {ac.definition}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.action_code && (
              <p className="text-sm text-error-500">
                {errors.action_code.message}
              </p>
            )}
          </div>

          {/* Target Date - Optional */}
          <div className="space-y-2">
            <Label htmlFor="target_date" className="text-sm font-medium">
              Target Date
            </Label>
            <Controller
              name="target_date"
              control={control}
              render={({ field }) => (
                <DatePicker
                  value={field.value || ''}
                  onChange={(value) => field.onChange(value || null)}
                  disablePast
                  disabled={isPending}
                  error={!!errors.target_date}
                />
              )}
            />
            {errors.target_date && (
              <p className="text-sm text-error-500">
                {errors.target_date.message}
              </p>
            )}
          </div>

          {/* Assign To (Crew Member) - Optional */}
          {vesselId && (

            <div className="space-y-2">
              <Label htmlFor="assigned_crew_id" className="text-sm font-medium">
                Assign To
              </Label>
              <Controller
                name="assigned_crew_id"
                control={control}
                render={({ field }) => (
                  <Select
                    value={field.value || ''}
                    onValueChange={(value) => field.onChange(value)}
                    disabled={isPending || isLoadingCrew}
                  >
                    <SelectTrigger id="assigned_crew_id">
                      <SelectValue placeholder="Select crew member..." />
                    </SelectTrigger>
                    <SelectContent>
                      {crewMembers
                        .filter((crew) =>
                          [
                            "CHIEF ENGINEER",
                            "CHIEF OFFICER",
                            "SECOND ENGINEER",
                            "MASTER",
                          ].includes(crew.rank_name?.toUpperCase())
                        )
                        .map((crew) => (
                          <SelectItem key={crew.id} value={crew.crew_id}>
                            {crew.display_name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                )}
              />

              {/* Reviewer preview */}
              {reviewerPreview && (
                <div className="flex items-start gap-2 rounded-md bg-neutral-50 p-2 text-xs text-neutral-600">
                  <UserCheck className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>Auto-reviewer: {reviewerPreview}</span>
                </div>
              )}
            </div>
          )}

          {/* CAR Auto-Creation Notice */}
          <div className="flex items-start gap-2 rounded-lg bg-info-50 p-3 text-sm text-info-700">
            <Info className="mt-0.5 h-4 w-4 shrink-0" />
            <span>
              A CAR (Corrective Action Report) will be automatically created for
              this deficiency.
            </span>
          </div>

          {/* Error Message */}
          {createDeficiencyMutation.isError && (
            <div className="rounded-lg bg-error-50 p-3 text-sm text-error-700">
              Failed to add deficiency. Please try again.
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Add Deficiency
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
