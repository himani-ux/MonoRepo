/**
 * Evidence Upload Modal
 *
 * Per APP_FLOW.md Section 2.3 and IMPLEMENTATION_PLAN.md Step 5.5
 * Features:
 * - Evidence type selection (BEFORE, AFTER, EVIDENCE, OTHER)
 * - File upload with drag & drop (PDF/JPG/JPEG, 3MB max)
 * - Required description field (5-500 chars)
 * - Form validation per VALIDATION_RULES.md Section 6.1
 */

import { type FC, useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { FileUpload } from '@/components/shared';
import { useUploadEvidence } from '@/hooks/use-cars';
import type { EvidenceType } from '@/types';
import {
  evidenceSchema,
  evidenceDefaults,
  EVIDENCE_TYPE_OPTIONS,
  type EvidenceFormData,
} from '@/lib/validations/evidence';

// ============================================================================
// Types
// ============================================================================

export interface EvidenceUploadModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Handler to change open state */
  onOpenChange: (open: boolean) => void;
  /** CAR ID to upload evidence for */
  carId: string | number;
  /** Pre-selected evidence type (optional, defaults to BEFORE) */
  defaultType?: EvidenceType;
  /** Callback when evidence is successfully uploaded */
  onSuccess?: () => void;
  /** Additional class names */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export const EvidenceUploadModal: FC<EvidenceUploadModalProps> = ({
  open,
  onOpenChange,
  carId,
  defaultType,
  onSuccess,
  className,
}) => {
  // File state (handled separately from react-hook-form since File is not serializable)
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);

  // Upload mutation
  const uploadMutation = useUploadEvidence(carId);

  // Form setup
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<EvidenceFormData>({
    resolver: zodResolver(evidenceSchema),
    defaultValues: evidenceDefaults,
  });

  // Reset form and file when modal opens/closes
  useEffect(() => {
    if (open) {
      reset({
        ...evidenceDefaults,
        evidence_type: defaultType || evidenceDefaults.evidence_type,
      });
      setFile(null);
      setFileError(null);
    }
  }, [open, reset, defaultType]);

  // Handle form submission
  const onSubmit = async (data: EvidenceFormData) => {
    // Validate file is selected
    if (!file) {
      setFileError('Please select a file');
      return;
    }

    try {
      await uploadMutation.mutateAsync({
        file,
        evidence_type: data.evidence_type,
        description: data.description,
      });

      // Close modal and notify parent
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      // Error handling is done via mutation state
      console.error('Failed to upload evidence:', error);
    }
  };

  const handleFileChange = (selectedFile: File | null) => {
    setFile(selectedFile);
    if (selectedFile) {
      setFileError(null);
    }
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  const isPending = isSubmitting || uploadMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn('sm:max-w-lg', className)}>
        <DialogHeader>
          <DialogTitle>Upload Evidence</DialogTitle>
          <DialogDescription>
            Add evidence type, file, and a clear description for this CAR record.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Evidence Type */}
          <div className="space-y-2">
            <Label htmlFor="evidence_type" className="text-sm font-medium">
              Evidence Type <span className="text-error-500">*</span>
            </Label>
            <Controller
              name="evidence_type"
              control={control}
              render={({ field }) => (
                <Select
                  value={field.value}
                  onValueChange={field.onChange}
                  disabled={isPending}
                >
                  <SelectTrigger
                    id="evidence_type"
                    className={cn(
                      errors.evidence_type &&
                        'border-error-500 focus:border-error-500 focus:ring-error-100'
                    )}
                  >
                    <SelectValue placeholder="Select evidence type" />
                  </SelectTrigger>
                  <SelectContent>
                    {EVIDENCE_TYPE_OPTIONS.map((opt) => (
                      <SelectItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.evidence_type && (
              <p className="text-sm text-error-500">
                {errors.evidence_type.message}
              </p>
            )}
          </div>

          {/* File Upload */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">
              File <span className="text-error-500">*</span>
            </Label>
            <FileUpload
              value={file}
              onChange={handleFileChange}
              disabled={isPending}
              error={!!fileError}
              errorMessage={fileError || undefined}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-sm font-medium">
              Description <span className="text-error-500">*</span>
            </Label>
            <Controller
              name="description"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  id="description"
                  placeholder="Describe the evidence (e.g., photo showing deficiency before correction...)"
                  rows={3}
                  disabled={isPending}
                  className={cn(
                    errors.description &&
                      'border-error-500 focus:border-error-500 focus:ring-error-100'
                  )}
                />
              )}
            />
            {errors.description && (
              <p className="text-sm text-error-500">
                {errors.description.message}
              </p>
            )}
          </div>

          {/* Error Message */}
          {uploadMutation.isError && (
            <div className="rounded-lg bg-error-50 p-3 text-sm text-error-700">
              Failed to upload evidence. Please try again.
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
              Upload
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
