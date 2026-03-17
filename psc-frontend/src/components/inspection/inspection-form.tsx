/**
 * Inspection form component for create/edit.
 *
 * Per APP_FLOW.md Section 2.2 - Create Inspection layout
 * Per VALIDATION_RULES.md Section 2 - Inspection validation
 *
 * Features:
 * - Conditional PSC fields (subtype, MOU)
 * - Report upload section
 * - Mobile-first responsive layout
 * - react-hook-form with Zod validation
 */

import { type FC, useEffect, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertCircle, Loader2 } from 'lucide-react';
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
  Textarea,
} from '@/components/ui';
import { DatePicker, FileUpload } from '@/components/shared';
import { useMOUCodes } from '@/hooks/use-masters';
import {
  createInspectionSchema,
  createInspectionDefaults,
  validateInspectionReportFile,
  type CreateInspectionFormData,
} from '@/lib/validations/inspection';
import { INSPECTION_TYPES, PSC_SUBTYPES } from '@/lib/utils/constants';

// ============================================================================
// Types
// ============================================================================

export interface InspectionFormProps {
  /** Called when form is submitted */
  onSubmit: (data: CreateInspectionFormData, reportFile: File | null) => void;
  /** Called when cancel is requested */
  onCancel: () => void;
  /** Loading state during submission */
  isSubmitting?: boolean;
  /** Submit button text */
  submitLabel?: string;
  /** Initial form values for editing */
  initialValues?: Partial<CreateInspectionFormData>;
  /** Existing report file URL for editing */
  existingReportUrl?: string;
  /** Whether a report file is required (true for create, false for edit) */
  requireReport?: boolean;
  /** Allowed inspection types for the current user/context */
  allowedInspectionTypes?: Array<CreateInspectionFormData['inspection_type']>;
  /** Additional class names */
  className?: string;
}

// ============================================================================
// Constants
// ============================================================================

/** Inspection type options */
const inspectionTypeOptions = [
  { value: INSPECTION_TYPES.PSC, label: 'PSC' },
  { value: INSPECTION_TYPES.RS, label: 'RightShip' },
  { value: INSPECTION_TYPES.AUDIT, label: 'Audit' },
];

/** PSC subtype options */
const pscSubtypeOptions = [
  { value: PSC_SUBTYPES.INITIAL, label: 'Initial' },
  { value: PSC_SUBTYPES.EXPANDED, label: 'Expanded' },
  { value: PSC_SUBTYPES.CIC, label: 'CIC (Concentrated Inspection Campaign)' },
];

// ============================================================================
// Component
// ============================================================================

export const InspectionForm: FC<InspectionFormProps> = ({
  onSubmit,
  onCancel,
  isSubmitting = false,
  submitLabel = 'Create Draft',
  initialValues,
  existingReportUrl,
  requireReport = false,
  allowedInspectionTypes = [
    INSPECTION_TYPES.PSC,
    INSPECTION_TYPES.RS,
    INSPECTION_TYPES.AUDIT,
  ],
  className,
}) => {
  // Fetch MOU codes for dropdown
  const { data: mouCodes, isLoading: isMOULoading } = useMOUCodes();

  // Initialize form
  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CreateInspectionFormData>({
    resolver: zodResolver(createInspectionSchema),
    defaultValues: {
      ...createInspectionDefaults,
      ...initialValues,
    },
  });

  // Watch values for conditional logic
  const inspectionType = watch('inspection_type');
  const isDetention = watch('is_detention');
  const isPSC = inspectionType === INSPECTION_TYPES.PSC;
  const availableInspectionTypeOptions = inspectionTypeOptions.filter((option) =>
    allowedInspectionTypes.includes(option.value)
  );

  // Keep selected type within allowed list.
  useEffect(() => {
    if (!allowedInspectionTypes.length) return;
    if (!inspectionType || !allowedInspectionTypes.includes(inspectionType)) {
      setValue('inspection_type', allowedInspectionTypes[0], {
        shouldValidate: true,
      });
    }
  }, [allowedInspectionTypes, inspectionType, setValue]);

  // Clear PSC-specific fields when type changes from PSC
  useEffect(() => {
    if (!isPSC) {
      setValue('psc_subtype', null);
      setValue('mou_code', null);
    }
  }, [isPSC, setValue]);

  // Report file state (not part of form data)
  const [reportFile, setReportFile] = useState<File | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  const handleReportChange = (file: File | null) => {
    if (file) {
      const validation = validateInspectionReportFile(file);
      if (!validation.valid) {
        setReportError(validation.error || 'Invalid file');
        return;
      }
    }
    setReportError(null);
    setReportFile(file);
  };

  const handleFormSubmit = (data: CreateInspectionFormData) => {
    if (requireReport && !reportFile && !existingReportUrl) {
      setReportError('Inspection report is required');
      return;
    }
    onSubmit(data, reportFile);
  };

  return (
    <form
      onSubmit={handleSubmit(handleFormSubmit)}
      className={cn('space-y-6', className)}
      noValidate
    >
      {/* Section: Inspection Details */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-neutral-900">
          Inspection Details
        </h2>

        {/* Inspection Type */}
        <div className="space-y-2">
          <Label htmlFor="inspection_type">
            Inspection Type <span className="text-error-500">*</span>
          </Label>
          <Controller
            name="inspection_type"
            control={control}
            render={({ field }) => (
              <Select
                value={field.value || ''}
                onValueChange={field.onChange}
                disabled={isSubmitting}
              >
                <SelectTrigger
                  id="inspection_type"
                  error={!!errors.inspection_type}
                >
                  <SelectValue placeholder="Select inspection type" />
                </SelectTrigger>
                <SelectContent>
                  {availableInspectionTypeOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
          {errors.inspection_type && (
            <p className="text-sm text-error-500">
              {errors.inspection_type.message}
            </p>
          )}
        </div>

        {/* PSC Subtype - Only shown for PSC inspections */}
        {isPSC && (
          <div className="space-y-2">
            <Label htmlFor="psc_subtype">
              PSC Subtype <span className="text-error-500">*</span>
            </Label>
            <Controller
              name="psc_subtype"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value || ''}
                  onValueChange={field.onChange}
                  disabled={isSubmitting}
                >
                  <SelectTrigger
                    id="psc_subtype"
                    error={!!errors.psc_subtype}
                  >
                    <SelectValue placeholder="Select PSC subtype" />
                  </SelectTrigger>
                  <SelectContent>
                    {pscSubtypeOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.psc_subtype && (
              <p className="text-sm text-error-500">
                {errors.psc_subtype.message}
              </p>
            )}
          </div>
        )}

        {/* Inspection Date */}
        <div className="space-y-2">
          <Label htmlFor="inspection_date">
            Inspection Date <span className="text-error-500">*</span>
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
          <Label htmlFor="port">
            Port/Place <span className="text-error-500">*</span>
          </Label>
          <Input
            id="port"
            type="text"
            placeholder="Enter port or place of inspection"
            disabled={isSubmitting}
            {...register('port')}
            className={cn(errors.port && 'border-error-500')}
          />
          {errors.port && (
            <p className="text-sm text-error-500">{errors.port.message}</p>
          )}
        </div>

        {/* Country / Port State */}
        <div className="space-y-2">
          <Label htmlFor="port_state">Country</Label>
          <Input
            id="port_state"
            type="text"
            placeholder="Enter country"
            disabled={isSubmitting}
            {...register('port_state')}
            className={cn(errors.port_state && 'border-error-500')}
          />
          {errors.port_state && (
            <p className="text-sm text-error-500">{errors.port_state.message}</p>
          )}
        </div>

        {/* MOU - Only shown for PSC inspections */}
        {isPSC && (
          <div className="space-y-2">
            <Label htmlFor="mou_code">
              MOU <span className="text-error-500">*</span>
            </Label>
            <Controller
              name="mou_code"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value || ''}
                  onValueChange={field.onChange}
                  disabled={isSubmitting || isMOULoading}
                >
                  <SelectTrigger
                    id="mou_code"
                    error={!!errors.mou_code}
                  >
                    <SelectValue
                      placeholder={isMOULoading ? 'Loading...' : 'Select MOU'}
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {mouCodes?.map((mou) => (
                      <SelectItem key={mou.mou_code} value={mou.mou_code}>
                        {mou.mou_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.mou_code && (
              <p className="text-sm text-error-500">{errors.mou_code.message}</p>
            )}
          </div>
        )}

        {/* Authority */}
        <div className="space-y-2">
          <Label htmlFor="authority">Authority</Label>
          <Input
            id="authority"
            type="text"
            placeholder="Enter inspecting authority"
            disabled={isSubmitting}
            {...register('authority')}
            className={cn(errors.authority && 'border-error-500')}
          />
          {errors.authority && (
            <p className="text-sm text-error-500">{errors.authority.message}</p>
          )}
        </div>

        {/* Inspector Name */}
        <div className="space-y-2">
          <Label htmlFor="inspector_name">Inspector Name</Label>
          <Input
            id="inspector_name"
            type="text"
            placeholder="Enter inspector name"
            disabled={isSubmitting}
            {...register('inspector_name')}
            className={cn(errors.inspector_name && 'border-error-500')}
          />
          {errors.inspector_name && (
            <p className="text-sm text-error-500">
              {errors.inspector_name.message}
            </p>
          )}
        </div>

        {/* Report Reference - auto-generated by backend */}

        {/* Detention Checkbox */}
        <div className="flex items-center space-x-3">
          <Controller
            name="is_detention"
            control={control}
            render={({ field }) => (
              <Checkbox
                id="is_detention"
                checked={field.value}
                onCheckedChange={field.onChange}
                disabled={isSubmitting}
              />
            )}
          />
          <Label htmlFor="is_detention" className="cursor-pointer font-normal">
            Detention
          </Label>
        </div>

        {/* Detention Reason - Only shown when detention is checked */}
        {isDetention && (
          <div className="space-y-2">
            <Label htmlFor="detention_reason">Detention Reason</Label>
            <Textarea
              id="detention_reason"
              placeholder="Enter reason for detention"
              disabled={isSubmitting}
              {...register('detention_reason')}
              className={cn(errors.detention_reason && 'border-error-500')}
              rows={3}
            />
            {errors.detention_reason && (
              <p className="text-sm text-error-500">
                {errors.detention_reason.message}
              </p>
            )}
          </div>
        )}

        {/* Deficiencies Reported */}
        <div className="space-y-2">
          <Label>
            Deficiencies Reported <span className="text-error-500">*</span>
          </Label>
          <Controller
            name="def_reported"
            control={control}
            render={({ field }) => (
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="def_reported"
                    value="YES"
                    checked={field.value === 'YES'}
                    onChange={() => field.onChange('YES')}
                    disabled={isSubmitting}
                    className="h-4 w-4 text-primary-600 border-neutral-300 focus:ring-primary-500"
                  />
                  <span className="text-sm text-neutral-700">Yes</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="def_reported"
                    value="NO"
                    checked={field.value === 'NO'}
                    onChange={() => field.onChange('NO')}
                    disabled={isSubmitting}
                    className="h-4 w-4 text-primary-600 border-neutral-300 focus:ring-primary-500"
                  />
                  <span className="text-sm text-neutral-700">No</span>
                </label>
              </div>
            )}
          />
          {errors.def_reported && (
            <p className="text-sm text-error-500">
              {errors.def_reported.message}
            </p>
          )}
        </div>
      </section>

      {/* Section: Inspection Report */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-neutral-900">
          Inspection Report
        </h2>

        {existingReportUrl ? (
          <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4">
            <p className="text-sm text-neutral-600">
              Report already uploaded.{' '}
              <a
                href={existingReportUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary-500 hover:underline"
              >
                View report
              </a>
            </p>
            <p className="mt-2 text-xs text-neutral-500">
              Upload a new file to replace the existing report.
            </p>
          </div>
        ) : null}

        <FileUpload
          value={reportFile}
          onChange={handleReportChange}
          error={!!reportError}
          errorMessage={reportError || undefined}
          disabled={isSubmitting}
          placeholder="Drag & drop inspection report or click to browse"
        />

        <div className="flex items-start gap-2 rounded-lg bg-primary-50 p-3 text-sm text-primary-700">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <p>
            Upload the inspection report to submit this inspection for review.
            Accepted formats: PDF, JPG, JPEG (max 3MB).
          </p>
        </div>
      </section>

      {/* Section: Deficiencies (Placeholder for Step 4.6) */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-neutral-900">Deficiencies</h2>

        <div className="rounded-lg border-2 border-dashed border-neutral-200 bg-neutral-50 p-6 text-center">
          <p className="text-sm text-neutral-500">
            Deficiencies can be added after creating the inspection.
          </p>
        </div>
      </section>

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
              Saving...
            </>
          ) : (
            submitLabel
          )}
        </Button>
      </div>
    </form>
  );
};
