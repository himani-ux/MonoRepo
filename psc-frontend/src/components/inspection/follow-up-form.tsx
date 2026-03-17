/**
 * PSC Follow-up form component
 *
 * Per APP_FLOW.md Section 2.2 - Register Follow-up layout
 * Per FEAT-DEF-002 - Register PSC Follow-up
 *
 * Features:
 * - Display parent inspection info (read-only)
 * - Form fields for follow-up details
 * - Deficiency selection with checkboxes
 * - Action code dropdown for selected deficiencies
 * - DefCode prominently displayed per LESSONS.md
 */

import { type FC, useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertCircle, Loader2, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Button,
  Input,
  Label,
  Checkbox,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Card,
} from '@/components/ui';
import { DatePicker } from '@/components/shared';
import { usePSCActionCodes } from '@/hooks/use-masters';
import {
  followUpFormSchema,
  followUpFormDefaults,
  type FollowUpSimpleFormData,
} from '@/lib/validations/follow-up';
import type { InspectionDetail, DeficiencyDetail } from '@/types';

// ============================================================================
// Constants
// ============================================================================

/** Action code for "Rectified" - clears the deficiency */
const RECTIFIED_ACTION_CODE = 10;

// ============================================================================
// Types
// ============================================================================

export interface FollowUpFormProps {
  /** Parent inspection data */
  parentInspection: InspectionDetail;
  /** Called when form is submitted */
  onSubmit: (data: FollowUpSimpleFormData) => void;
  /** Called when cancel is requested */
  onCancel: () => void;
  /** Loading state during submission */
  isSubmitting?: boolean;
  /** Additional class names */
  className?: string;
}

interface DeficiencySelection {
  deficiency: DeficiencyDetail;
  selected: boolean;
  actionCodeId: number;
}

// ============================================================================
// Component
// ============================================================================

export const FollowUpForm: FC<FollowUpFormProps> = ({
  parentInspection,
  onSubmit,
  onCancel,
  isSubmitting = false,
  className,
}) => {
  // Fetch action codes for dropdown
  const { data: actionCodes, isLoading: isActionCodesLoading } = usePSCActionCodes();

  // Track deficiency selections separately from form (for complex UI state)
  const [deficiencySelections, setDeficiencySelections] = useState<DeficiencySelection[]>([]);

  // Initialize deficiency selections from parent inspection
  useEffect(() => {
    if (parentInspection.deficiencies) {
      const selections = parentInspection.deficiencies
        .filter((d) => !d.is_cleared) // Only show open deficiencies
        .map((d) => ({
          deficiency: d,
          selected: false,
          actionCodeId: RECTIFIED_ACTION_CODE, // Default to rectified
        }));
      setDeficiencySelections(selections);
    }
  }, [parentInspection.deficiencies]);

  // Initialize form
  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FollowUpSimpleFormData>({
    resolver: zodResolver(followUpFormSchema),
    defaultValues: {
      ...followUpFormDefaults,
      // Pre-fill port from parent inspection
      port_place: parentInspection.port || '',
      country: parentInspection.port_state || '',
      authority: parentInspection.authority || '',
    },
  });

  // Handle deficiency selection toggle
  const handleDeficiencyToggle = (deficiencyId: number, checked: boolean) => {
    setDeficiencySelections((prev) =>
      prev.map((s) =>
        s.deficiency.id === deficiencyId
          ? { ...s, selected: checked }
          : s
      )
    );
  };

  // Handle action code change for a deficiency
  const handleActionCodeChange = (deficiencyId: number, actionCodeId: number) => {
    setDeficiencySelections((prev) =>
      prev.map((s) =>
        s.deficiency.id === deficiencyId
          ? { ...s, actionCodeId }
          : s
      )
    );
  };

  // Handle form submission
  const handleFormSubmit = (data: FollowUpSimpleFormData) => {
    // Build deficiency updates from selections
    const deficiencyUpdates = deficiencySelections
      .filter((s) => s.selected)
      .map((s) => ({
        deficiency_id: s.deficiency.id,
        action_code_id: s.actionCodeId,
      }));

    onSubmit({
      ...data,
      deficiency_updates: deficiencyUpdates,
    });
  };

  const selectedCount = deficiencySelections.filter((s) => s.selected).length;
  const openDeficiencyCount = deficiencySelections.length;

  return (
    <form
      onSubmit={handleSubmit(handleFormSubmit)}
      className={cn('space-y-6', className)}
      noValidate
    >
      {/* Section: Parent Inspection Info (Read-only) */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium uppercase tracking-wide text-neutral-500">
          Original Inspection
        </h2>
        <Card className="bg-neutral-50 p-4">
          <div className="grid gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-neutral-500">Type</span>
              <span className="font-medium">
                {parentInspection.inspection_type}
                {parentInspection.psc_subtype && ` - ${parentInspection.psc_subtype}`}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Date</span>
              <span className="font-medium">{parentInspection.inspection_date}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Port</span>
              <span className="font-medium">{parentInspection.port}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-neutral-500">Open Deficiencies</span>
              <span className="font-medium">{openDeficiencyCount}</span>
            </div>
          </div>
        </Card>
      </section>

      {/* Section: Follow-up Details */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-neutral-900">
          Follow-up Details
        </h2>

        {/* Follow-up Date */}
        <div className="space-y-2">
          <Label htmlFor="inspection_date">
            Follow-up Date <span className="text-error-500">*</span>
          </Label>
          <Controller
            name="inspection_date"
            control={control}
            render={({ field }) => (
              <DatePicker
                id="inspection_date"
                value={field.value}
                onChange={field.onChange}
                disableFuture
                disabled={isSubmitting}
                error={!!errors.inspection_date}
              />
            )}
          />
          {errors.inspection_date && (
            <p className="text-sm text-error-500">
              {errors.inspection_date.message}
            </p>
          )}
        </div>

        {/* Port/Place */}
        <div className="space-y-2">
          <Label htmlFor="port_place">
            Port/Place <span className="text-error-500">*</span>
          </Label>
          <Input
            id="port_place"
            type="text"
            placeholder="Enter port or place"
            disabled={isSubmitting}
            {...register('port_place')}
            className={cn(errors.port_place && 'border-error-500')}
          />
          {errors.port_place && (
            <p className="text-sm text-error-500">{errors.port_place.message}</p>
          )}
        </div>

        {/* Country */}
        <div className="space-y-2">
          <Label htmlFor="country">Country</Label>
          <Input
            id="country"
            type="text"
            placeholder="Enter country"
            disabled={isSubmitting}
            {...register('country')}
          />
        </div>

        {/* Authority */}
        <div className="space-y-2">
          <Label htmlFor="authority">Authority</Label>
          <Input
            id="authority"
            type="text"
            placeholder="Enter inspecting authority"
            disabled={isSubmitting}
            {...register('authority')}
          />
        </div>
      </section>

      {/* Section: Deficiency Status Updates */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-neutral-900">
            Deficiency Status Updates
          </h2>
          {selectedCount > 0 && (
            <span className="text-sm text-primary-600">
              {selectedCount} selected
            </span>
          )}
        </div>

        {openDeficiencyCount === 0 ? (
          <div className="flex items-center gap-2 rounded-lg bg-neutral-100 p-4 text-sm text-neutral-600">
            <Info className="h-4 w-4 flex-shrink-0" />
            <p>No open deficiencies to update.</p>
          </div>
        ) : (
          <>
            <p className="text-sm text-neutral-500">
              Select deficiencies cleared by this follow-up and choose the new action code:
            </p>

            <div className="space-y-3">
              {deficiencySelections.map((selection) => (
                <Card
                  key={selection.deficiency.id}
                  className={cn(
                    'p-4 transition-colors',
                    selection.selected && 'border-primary-300 bg-primary-50'
                  )}
                >
                  <div className="flex items-start gap-3">
                    {/* Checkbox */}
                    <Checkbox
                      id={`def-${selection.deficiency.id}`}
                      checked={selection.selected}
                      onCheckedChange={(checked) =>
                        handleDeficiencyToggle(selection.deficiency.id, !!checked)
                      }
                      disabled={isSubmitting}
                      className="mt-1"
                    />

                    <div className="flex-1 space-y-2">
                      {/* DefCode - PROMINENT per LESSONS.md */}
                      <label
                        htmlFor={`def-${selection.deficiency.id}`}
                        className="flex cursor-pointer items-center gap-2"
                      >
                        <span className="inline-flex items-center rounded bg-neutral-800 px-2 py-1 font-mono text-sm font-bold text-white">
                          {selection.deficiency.def_code}
                        </span>
                        <span className="text-sm font-medium text-neutral-700">
                          {selection.deficiency.def_code_description}
                        </span>
                      </label>

                      {/* Current action code */}
                      <p className="text-sm text-neutral-500">
                        Current: {selection.deficiency.action_code} -{' '}
                        {selection.deficiency.action_code_description}
                      </p>

                      {/* New action code dropdown (only when selected) */}
                      {selection.selected && (
                        <div className="mt-3 flex items-center gap-2">
                          <span className="text-sm text-neutral-600">New:</span>
                          <Select
                            value={selection.actionCodeId.toString()}
                            onValueChange={(value) =>
                              handleActionCodeChange(
                                selection.deficiency.id,
                                parseInt(value, 10)
                              )
                            }
                            disabled={isSubmitting || isActionCodesLoading}
                          >
                            <SelectTrigger className="w-[300px]">
                              <SelectValue placeholder="Select action code" />
                            </SelectTrigger>
                            <SelectContent>
                              {actionCodes?.map((code) => (
                                <SelectItem
                                  key={code.action_code}
                                  value={String(code.action_code)}
                                >
                                  {code.action_code} - {code.description}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </>
        )}
      </section>

      {/* Info notice */}
      <div className="flex items-start gap-2 rounded-lg bg-primary-50 p-3 text-sm text-primary-700">
        <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
        <p>
          A new follow-up inspection will be created and linked to the original inspection.
          Selected deficiencies will be updated with the new action codes.
          Deficiencies set to code 10 (Rectified) will be marked as cleared.
        </p>
      </div>

      {/* Form Actions */}
      <div className="flex flex-col-reverse gap-3 border-t border-neutral-200 pt-6 sm:flex-row sm:justify-end">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Registering...
            </>
          ) : (
            'Register Follow-up'
          )}
        </Button>
      </div>
    </form>
  );
};
