/**
 * Follow-up Wizard — 5-step wizard for recording a PSC follow-up
 * on the SAME inspection (no new inspection record).
 *
 * Steps:
 * 1. Confirm Context (read-only inspection info)
 * 2. Open Deficiencies (show non-rectified, user selects)
 * 3. Update ActionCodes (reinspection date, bulk/per-row action code)
 * 4. Upload Follow-up Report (optional PDF)
 * 5. Confirm & Submit
 */

import { useState, useMemo, type FC, useCallback } from 'react';
import { Check, ChevronLeft, ChevronRight, Upload, X, Loader2 } from 'lucide-react';
import { Button, Card, CardContent, Input, Label, Textarea } from '@/components/ui';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui';
import { usePSCActionCodes } from '@/hooks/use-masters';
import { cn } from '@/lib/utils';
import type { InspectionDetail as InspectionDetailType, DeficiencyDetail, PSCActionCode } from '@/types';
import type { FollowUpFormData, DeficiencyUpdateFormData } from '@/lib/validations/follow-up';

// ============================================================================
// Types
// ============================================================================

export interface FollowUpWizardProps {
  /** Parent inspection data */
  inspection: InspectionDetailType;
  /** Called on successful submission */
  onSubmit: (data: FollowUpFormData) => Promise<void>;
  /** Called when user cancels/exits */
  onCancel: () => void;
  /** Whether submission is in progress */
  isSubmitting: boolean;
}

interface StepConfig {
  label: string;
  shortLabel: string;
}

const STEPS: StepConfig[] = [
  { label: 'Confirm Context', shortLabel: 'Context' },
  { label: 'Open Deficiencies', shortLabel: 'Deficiencies' },
  { label: 'Update Action Codes', shortLabel: 'Actions' },
  { label: 'Upload Report', shortLabel: 'Report' },
  { label: 'Confirm & Submit', shortLabel: 'Submit' },
];

// ============================================================================
// Helper: Format date
// ============================================================================

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

// ============================================================================
// Stepper UI
// ============================================================================

const Stepper: FC<{ currentStep: number; steps: StepConfig[] }> = ({ currentStep, steps }) => (
  <div className="flex items-center justify-between px-2 py-3">
    {steps.map((step, idx) => {
      const isActive = idx === currentStep;
      const isDone = idx < currentStep;
      return (
        <div key={step.label} className="flex flex-1 items-center">
          <div className="flex flex-col items-center flex-1">
            <div
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm font-medium transition-colors',
                isDone && 'border-primary-500 bg-primary-500 text-white',
                isActive && 'border-primary-500 bg-white text-primary-500',
                !isDone && !isActive && 'border-gray-300 bg-white text-gray-400',
              )}
            >
              {isDone ? <Check className="h-4 w-4" /> : idx + 1}
            </div>
            <span
              className={cn(
                'mt-1 text-xs text-center',
                isActive ? 'font-medium text-primary-600' : 'text-gray-400',
              )}
            >
              {step.shortLabel}
            </span>
          </div>
          {idx < steps.length - 1 && (
            <div
              className={cn(
                'mx-1 h-0.5 flex-1 -mt-4',
                idx < currentStep ? 'bg-primary-500' : 'bg-gray-200',
              )}
            />
          )}
        </div>
      );
    })}
  </div>
);

// ============================================================================
// Main Wizard Component
// ============================================================================

export const FollowUpWizard: FC<FollowUpWizardProps> = ({
  inspection,
  onSubmit,
  onCancel,
  isSubmitting,
}) => {
  const [step, setStep] = useState(0);

  // Fetch action codes for dropdown
  const { data: actionCodes = [] } = usePSCActionCodes();

  // Step 2 state: selected deficiency IDs
  const openDeficiencies = useMemo(
    () =>
      (inspection.deficiencies || []).filter(
        (d) => d.action_code === null || d.action_code === undefined || Number(d.action_code) !== 10,
      ),
    [inspection.deficiencies],
  );
  const [selectedDefIds, setSelectedDefIds] = useState<Set<string>>(() =>
    new Set(openDeficiencies.map((d) => String(d.id))),
  );

  // Step 3 state: reinspection date + per-deficiency action codes + notes
  const todayStr = useMemo(() => new Date().toISOString().split('T')[0], []);
  const [reinspectionDate, setReinspectionDate] = useState(todayStr);
  const [defActions, setDefActions] = useState<Record<string, number>>(() => {
    const init: Record<string, number> = {};
    openDeficiencies.forEach((d) => {
      init[String(d.id)] = 10; // Default: Rectified
    });
    return init;
  });
  const [defNotes, setDefNotes] = useState<Record<string, string>>({});

  // Step 4 state: optional report
  const [reportFile, setReportFile] = useState<File | null>(null);
  const [reportDescription, setReportDescription] = useState('');

  // Step 3 validation errors
  const [dateError, setDateError] = useState('');

  // Derived
  const selectedDefs = useMemo(
    () => openDeficiencies.filter((d) => selectedDefIds.has(String(d.id))),
    [openDeficiencies, selectedDefIds],
  );
  const noOpenDefs = openDeficiencies.length === 0;

  // ---- Step navigation ----

  const canGoNext = useMemo(() => {
    switch (step) {
      case 0:
        return true; // context is read-only
      case 1:
        return selectedDefIds.size > 0; // need at least one selected
      case 2: {
        // Need valid reinspection date
        if (!reinspectionDate) return false;
        const d = new Date(reinspectionDate);
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        if (d > today) return false;
        if (d < new Date(inspection.inspection_date)) return false;
        return true;
      }
      case 3:
        // Report is optional; if file provided, description required
        if (reportFile && !reportDescription.trim()) return false;
        return true;
      case 4:
        return true;
      default:
        return false;
    }
  }, [step, selectedDefIds, reinspectionDate, inspection.inspection_date, reportFile, reportDescription]);

  const handleNext = useCallback(() => {
    if (step === 2) {
      // Validate reinspection date
      const d = new Date(reinspectionDate);
      const today = new Date();
      today.setHours(23, 59, 59, 999);
      if (d > today) {
        setDateError('Reinspection date cannot be in the future');
        return;
      }
      if (d < new Date(inspection.inspection_date)) {
        setDateError('Reinspection date cannot be before the inspection date');
        return;
      }
      setDateError('');
    }
    // If step 1 and no open defs, skip to end (only exit)
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    }
  }, [step, reinspectionDate, inspection.inspection_date]);

  const handleBack = useCallback(() => {
    if (step > 0) setStep((s) => s - 1);
  }, [step]);

  const handleSubmit = useCallback(async () => {
    const updates: DeficiencyUpdateFormData[] = selectedDefs.map((d) => ({
      deficiency_id: String(d.id),
      action_code_id: defActions[String(d.id)] ?? 10,
      notes: defNotes[String(d.id)] || '',
    }));

    const data: FollowUpFormData = {
      reinspection_date: reinspectionDate,
      notes: '',
      deficiency_updates: updates,
      report_file: reportFile,
      report_description: reportDescription,
    };

    await onSubmit(data);
  }, [selectedDefs, defActions, defNotes, reinspectionDate, reportFile, reportDescription, onSubmit]);

  // ---- Toggle deficiency selection ----

  const toggleDef = useCallback((defId: string) => {
    setSelectedDefIds((prev) => {
      const next = new Set(prev);
      if (next.has(defId)) next.delete(defId);
      else next.add(defId);
      return next;
    });
  }, []);

  const toggleAll = useCallback(() => {
    if (selectedDefIds.size === openDeficiencies.length) {
      setSelectedDefIds(new Set());
    } else {
      setSelectedDefIds(new Set(openDeficiencies.map((d) => String(d.id))));
    }
  }, [selectedDefIds, openDeficiencies]);

  // ============================================================================
  // Render Steps
  // ============================================================================

  const renderStep = () => {
    switch (step) {
      case 0:
        return <Step1Context inspection={inspection} />;
      case 1:
        if (noOpenDefs) {
          return (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Check className="mb-3 h-12 w-12 text-success-500" />
              <h3 className="text-lg font-semibold text-gray-900">All Deficiencies Rectified</h3>
              <p className="mt-1 text-sm text-gray-500">
                All deficiencies on this inspection already have action code 10 (Rectified).
                No follow-up is required.
              </p>
            </div>
          );
        }
        return (
          <Step2Deficiencies
            deficiencies={openDeficiencies}
            selectedIds={selectedDefIds}
            onToggle={toggleDef}
            onToggleAll={toggleAll}
          />
        );
      case 2:
        return (
          <Step3ActionCodes
            deficiencies={selectedDefs}
            actionCodes={actionCodes}
            defActions={defActions}
            onActionChange={(defId, code) =>
              setDefActions((prev) => ({ ...prev, [defId]: code }))
            }
            defNotes={defNotes}
            onNotesChange={(defId, notes) =>
              setDefNotes((prev) => ({ ...prev, [defId]: notes }))
            }
            reinspectionDate={reinspectionDate}
            onDateChange={(val) => {
              setReinspectionDate(val);
              setDateError('');
            }}
            minDate={inspection.inspection_date}
            maxDate={todayStr}
            dateError={dateError}
          />
        );
      case 3:
        return (
          <Step4Report
            file={reportFile}
            description={reportDescription}
            onFileChange={setReportFile}
            onDescriptionChange={setReportDescription}
          />
        );
      case 4:
        return (
          <Step5Summary
            inspection={inspection}
            selectedDefs={selectedDefs}
            defActions={defActions}
            actionCodes={actionCodes}
            reinspectionDate={reinspectionDate}
            reportFile={reportFile}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-8rem)]">
      {/* Stepper bar */}
      <Stepper currentStep={step} steps={STEPS} />

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-1 py-3">
        {renderStep()}
      </div>

      {/* Sticky bottom buttons */}
      <div className="flex-shrink-0 border-t bg-white px-4 py-3">
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={step === 0 ? onCancel : handleBack}
            disabled={isSubmitting}
          >
            <ChevronLeft className="mr-1 h-4 w-4" />
            {step === 0 ? 'Cancel' : 'Back'}
          </Button>

          {noOpenDefs && step === 1 ? (
            <Button variant="outline" onClick={onCancel}>
              Exit
            </Button>
          ) : step === STEPS.length - 1 ? (
            <Button onClick={handleSubmit} disabled={isSubmitting || !canGoNext}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Confirm & Submit'
              )}
            </Button>
          ) : (
            <Button onClick={handleNext} disabled={!canGoNext}>
              Next
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Step 1 — Confirm Context
// ============================================================================

const Step1Context: FC<{ inspection: InspectionDetailType }> = ({ inspection }) => (
  <Card>
    <CardContent className="p-4 space-y-3">
      <h3 className="text-base font-semibold text-gray-900">Inspection Context</h3>
      <p className="text-sm text-gray-500">
        This follow-up will update deficiency status for this inspection.
      </p>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <InfoRow label="Inspection Date" value={formatDate(inspection.inspection_date)} />
        <InfoRow label="Port" value={inspection.port || ''} />
        <InfoRow label="Authority" value={inspection.authority || '-'} />
        <InfoRow label="MOU" value={inspection.mou_code || '-'} />
        <InfoRow label="Report Ref" value={inspection.report_reference || '-'} />
        <InfoRow label="Deficiencies" value={String(inspection.deficiencies?.length ?? 0)} />
      </div>
    </CardContent>
  </Card>
);

const InfoRow: FC<{ label: string; value: string }> = ({ label, value }) => (
  <div>
    <span className="text-gray-500">{label}:</span>{' '}
    <span className="font-medium text-gray-900">{value}</span>
  </div>
);

// ============================================================================
// Step 2 — Open Deficiencies (selection)
// ============================================================================

interface Step2Props {
  deficiencies: DeficiencyDetail[];
  selectedIds: Set<string>;
  onToggle: (id: string) => void;
  onToggleAll: () => void;
}

const Step2Deficiencies: FC<Step2Props> = ({ deficiencies, selectedIds, onToggle, onToggleAll }) => (
  <div className="space-y-3">
    <div className="flex items-center justify-between">
      <h3 className="text-base font-semibold text-gray-900">
        Open Deficiencies ({deficiencies.length})
      </h3>
      <Button variant="ghost" size="sm" onClick={onToggleAll}>
        {selectedIds.size === deficiencies.length ? 'Deselect All' : 'Select All'}
      </Button>
    </div>
    <p className="text-sm text-gray-500">
      Select deficiencies to update in this follow-up.
    </p>
    <div className="space-y-2">
      {deficiencies.map((def) => {
        const id = String(def.id);
        const selected = selectedIds.has(id);
        return (
          <div
            key={id}
            className={cn(
              'flex items-start gap-3 rounded-lg border p-3 cursor-pointer transition-colors',
              selected ? 'border-primary-300 bg-primary-50' : 'border-gray-200 hover:bg-gray-50',
            )}
            onClick={() => onToggle(id)}
          >
            <input
              type="checkbox"
              checked={selected}
              readOnly
              className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600"
            />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="rounded bg-gray-800 px-2 py-0.5 text-xs font-bold text-white">
                  {def.def_code}
                </span>
                {def.action_code && (
                  <span className="text-xs text-gray-500">
                    Current: Code {def.action_code}
                  </span>
                )}
              </div>
              <p className="mt-1 text-sm text-gray-700 line-clamp-2">
                {def.description || def.def_code_description || '-'}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  </div>
);

// ============================================================================
// Step 3 — Update Action Codes
// ============================================================================

interface Step3Props {
  deficiencies: DeficiencyDetail[];
  actionCodes: PSCActionCode[];
  defActions: Record<string, number>;
  onActionChange: (defId: string, code: number) => void;
  defNotes: Record<string, string>;
  onNotesChange: (defId: string, notes: string) => void;
  reinspectionDate: string;
  onDateChange: (val: string) => void;
  minDate: string;
  maxDate: string;
  dateError: string;
}

const Step3ActionCodes: FC<Step3Props> = ({
  deficiencies,
  actionCodes,
  defActions,
  onActionChange,
  defNotes,
  onNotesChange,
  reinspectionDate,
  onDateChange,
  minDate,
  maxDate,
  dateError,
}) => (
  <div className="space-y-4">
    <h3 className="text-base font-semibold text-gray-900">Update Action Codes</h3>

    {/* Reinspection Date */}
    <div className="space-y-1">
      <Label htmlFor="reinspection-date">
        Reinspection Date <span className="text-error-500">*</span>
      </Label>
      <Input
        id="reinspection-date"
        type="date"
        value={reinspectionDate}
        onChange={(e) => onDateChange(e.target.value)}
        min={minDate}
        max={maxDate}
      />
      {dateError && <p className="text-sm text-error-500">{dateError}</p>}
    </div>

    {/* Per-deficiency action code */}
    <div className="space-y-3">
      {deficiencies.map((def) => {
        const id = String(def.id);
        return (
          <Card key={id}>
            <CardContent className="p-3 space-y-2">
              <div className="flex items-center gap-2">
                <span className="rounded bg-gray-800 px-2 py-0.5 text-xs font-bold text-white">
                  {def.def_code}
                </span>
                <span className="text-sm text-gray-600 truncate flex-1">
                  {def.description || def.def_code_description || '-'}
                </span>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                <div className="flex-1">
                  <Label className="text-xs text-gray-500">New Action Code</Label>
                  <Select
                    value={String(defActions[id] ?? 10)}
                    onValueChange={(val) => onActionChange(id, Number(val))}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {actionCodes.map((ac) => (
                        <SelectItem key={ac.action_code} value={String(ac.action_code)}>
                          {ac.action_code} - {ac.definition}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex-1">
                  <Label className="text-xs text-gray-500">Notes (optional)</Label>
                  <Input
                    placeholder="e.g. Rectified at port"
                    value={defNotes[id] || ''}
                    onChange={(e) => onNotesChange(id, e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  </div>
);

// ============================================================================
// Step 4 — Upload Report (optional)
// ============================================================================

interface Step4Props {
  file: File | null;
  description: string;
  onFileChange: (file: File | null) => void;
  onDescriptionChange: (desc: string) => void;
}

const Step4Report: FC<Step4Props> = ({ file, description, onFileChange, onDescriptionChange }) => (
  <div className="space-y-4">
    <h3 className="text-base font-semibold text-gray-900">Upload Follow-up Report</h3>
    <p className="text-sm text-gray-500">
      Optionally attach a follow-up inspection report (PDF only, max 5MB).
      You can skip this step if no report is available.
    </p>

    {/* File input */}
    <div className="space-y-1">
      <Label>Report File (PDF)</Label>
      {file ? (
        <div className="flex items-center gap-2 rounded-md border border-primary-200 bg-primary-50 p-3">
          <Upload className="h-5 w-5 text-primary-500" />
          <span className="flex-1 truncate text-sm font-medium text-primary-700">
            {file.name}
          </span>
          <span className="text-xs text-gray-500">
            {(file.size / 1024 / 1024).toFixed(2)} MB
          </span>
          <Button variant="ghost" size="sm" onClick={() => onFileChange(null)}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      ) : (
        <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 p-6 transition-colors hover:border-primary-400 hover:bg-primary-50">
          <Upload className="h-6 w-6 text-gray-400" />
          <span className="text-sm text-gray-500">Click to select PDF file</span>
          <input
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              if (f && f.size > 5 * 1024 * 1024) {
                alert('File exceeds 5MB limit');
                return;
              }
              onFileChange(f);
            }}
          />
        </label>
      )}
    </div>

    {/* Description (required if file present) */}
    {file && (
      <div className="space-y-1">
        <Label htmlFor="report-desc">
          Description <span className="text-error-500">*</span>
        </Label>
        <Textarea
          id="report-desc"
          placeholder="Describe the follow-up report..."
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
          rows={3}
        />
        {!description.trim() && (
          <p className="text-sm text-error-500">Description is required when uploading a report</p>
        )}
      </div>
    )}
  </div>
);

// ============================================================================
// Step 5 — Summary & Confirm
// ============================================================================

interface Step5Props {
  inspection: InspectionDetailType;
  selectedDefs: DeficiencyDetail[];
  defActions: Record<string, number>;
  actionCodes: PSCActionCode[];
  reinspectionDate: string;
  reportFile: File | null;
}

const Step5Summary: FC<Step5Props> = ({
  inspection,
  selectedDefs,
  defActions,
  actionCodes,
  reinspectionDate,
  reportFile,
}) => {
  const actionCodeMap = useMemo(() => {
    const map: Record<number, string> = {};
    actionCodes.forEach((ac) => {
      map[ac.action_code] = `${ac.action_code} - ${ac.definition}`;
    });
    return map;
  }, [actionCodes]);

  return (
    <div className="space-y-4">
      <h3 className="text-base font-semibold text-gray-900">Confirm Follow-up</h3>
      <p className="text-sm text-gray-500">Review the changes before submitting.</p>

      <Card>
        <CardContent className="p-4 space-y-3">
          <InfoRow label="Inspection" value={`${inspection.port || ''} — ${formatDate(inspection.inspection_date)}`} />
          <InfoRow label="Reinspection Date" value={formatDate(reinspectionDate)} />
          <InfoRow label="Deficiencies Updated" value={String(selectedDefs.length)} />
          <InfoRow label="Report Attached" value={reportFile ? 'Yes' : 'No'} />
        </CardContent>
      </Card>

      {/* Deficiency summary */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700">Deficiency Updates</h4>
        {selectedDefs.map((def) => {
          const id = String(def.id);
          const code = defActions[id] ?? 10;
          return (
            <div
              key={id}
              className="flex items-center gap-2 rounded border border-gray-200 p-2 text-sm"
            >
              <span className="rounded bg-gray-800 px-2 py-0.5 text-xs font-bold text-white">
                {def.def_code}
              </span>
              <span className="text-gray-400">→</span>
              <span className="font-medium text-gray-700">
                {actionCodeMap[code] || `Code ${code}`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
