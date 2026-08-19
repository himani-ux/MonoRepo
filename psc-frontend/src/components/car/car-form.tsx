/**
 * CAR Edit Form
 *
 * Per APP_FLOW.md Section 2.3 — Edit CAR screen layout.
 * Features: FEAT-CAR-002 (Edit CAR Draft), FEAT-CAR-011 (Add Corrective Action)
 *
 * Sections:
 * 1. Deficiency (read-only)
 * 2. Root Cause Analysis (CLC multi-select + summary)
 * 3. Corrective Actions (IMMEDIATE + LONG-TERM inline CRUD)
 * 4. Target Dates
 * 5. Evidence (display + upload trigger)
 * 6. Bottom action bar (Cancel / Save Draft / Submit)
 */

import {
  useState,
  useMemo,
  useCallback,
  useEffect,
  type MouseEvent,
  type FC,
} from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Plus,
  Trash2,
  Check,
  X,
  AlertTriangle,
  Search,
  Upload,
  FileText,
  Image,
  Loader2,
  ChevronRight,
  ChevronDown,
  Info,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/lib/api/client';
import {
  Card,
  CardContent,
  Badge,
  Button,
  Checkbox,
  Input,
  Label,
  Textarea,
} from '@/components/ui';
import { DatePicker, ConfirmDialog } from '@/components/shared';
import { useCLCHierarchy } from '@/hooks/use-masters';
import {
  useCreateAction,
  useUpdateAction,
  useDeleteAction,
  useDeleteEvidence,
} from '@/hooks/use-cars';
import {
  updateCarSchema,
  addActionSchema,
  validateCarSubmission,
  type UpdateCarFormData,
  type AddActionFormData,
  addActionDefaults,
} from '@/lib/validations/car';
import { ROOT_CAUSE_MIN_LENGTH, EVIDENCE_TYPES } from '@/lib/utils/constants';
import type {
  CARDetail,
  CorrectiveAction,
  Evidence,
  CLCHierarchy,
  CLCHierarchyCategory,
  ActionType,
} from '@/types';

// ============================================================================
// Props
// ============================================================================

export interface CARFormProps {
  /** CAR detail data */
  car: CARDetail;
  /** Save draft handler */
  onSaveDraft: (data: UpdateCarFormData) => Promise<void>;
  /** Submit CAR handler — undefined hides the submit button */
  onSubmit?: () => Promise<void>;
  /** Cancel handler */
  onCancel: () => void;
  /** Upload evidence trigger */
  onUploadEvidence?: (type: 'BEFORE' | 'AFTER' | 'EVIDENCE' | 'OTHER') => void;
  /** Whether save is in progress */
  isSaving?: boolean;
  /** Whether submit is in progress */
  isSubmitting?: boolean;
  /** Custom label for the submit button */
  submitLabel?: string;
  /** Custom description for the submit confirmation dialog */
  submitDescription?: string;
  /** Additional class names */
  className?: string;
}

// ============================================================================
// Helper Components
// ============================================================================

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function resolveEvidenceUrl(item: Evidence): string {
  const rawPath = item.preview_url || item.file_path;
  if (!rawPath) return '#';
  if (rawPath.startsWith('http://') || rawPath.startsWith('https://')) return rawPath;
  if (rawPath.startsWith('/')) return rawPath;
  return `/uploads/${rawPath.replace(/^\/+/, '')}`;
}

async function openEvidenceWithAuth(
  url: string,
  _fileName: string,
  mimeType: string
): Promise<void> {
  const previewTab = window.open('about:blank', '_blank');
  try {
    const response = await apiClient.get(url, { responseType: 'blob' });
    const typedBlob =
      response.data?.type || !mimeType
        ? response.data
        : new Blob([response.data], { type: mimeType });
    const blobUrl = URL.createObjectURL(typedBlob);

    if (previewTab && !previewTab.closed) {
      previewTab.location.href = blobUrl;
    } else {
      // Popup blocked: still show file in current tab.
      window.location.href = blobUrl;
    }
    setTimeout(() => URL.revokeObjectURL(blobUrl), 10 * 60_000);
  } catch {
    if (previewTab && !previewTab.closed) {
      previewTab.close();
    }
  }
}

// ============================================================================
// CLC Multi-Select Sub-Component
// ============================================================================

interface CLCMultiSelectProps {
  selectedCodes: string[];
  onAdd: (code: string) => void;
  onRemove: (code: string) => void;
}

// Build a flat lookup map from hierarchy: code → item name
function buildCodeNameMap(
  hierarchy: CLCHierarchy | undefined
): Record<string, string> {
  if (!hierarchy) return {};
  const map: Record<string, string> = {};
  const sections = [
    hierarchy.immediate_causes.actions,
    hierarchy.immediate_causes.conditions,
    hierarchy.root_causes.personal_factors,
    hierarchy.root_causes.job_factors,
  ];
  for (const section of sections) {
    for (const cat of Object.values(section)) {
      for (const [code, name] of Object.entries(cat.items)) {
        map[code] = name;
      }
    }
  }
  return map;
}

// Determine which category types the selected codes belong to
function getSelectedCategoryTypes(
  selectedCodes: string[],
  hierarchy: CLCHierarchy | undefined
): Set<string> {
  if (!hierarchy) return new Set();
  const types = new Set<string>();
  const codeSet = new Set(selectedCodes);

  const checkSection = (
    section: Record<string, CLCHierarchyCategory>,
    type: string
  ) => {
    for (const cat of Object.values(section)) {
      for (const code of Object.keys(cat.items)) {
        if (codeSet.has(code)) {
          types.add(type);
          return;
        }
      }
    }
  };

  checkSection(hierarchy.immediate_causes.actions, 'Immediate_Action');
  checkSection(hierarchy.immediate_causes.conditions, 'Immediate_Condition');
  checkSection(hierarchy.root_causes.personal_factors, 'Root_Personal');
  checkSection(hierarchy.root_causes.job_factors, 'Root_Job');

  return types;
}

// Improvement guidance mapping
const IMPROVEMENT_GUIDANCE: Record<string, string> = {
  Immediate_Action:
    'Procedure review/revision, toolbox talks, competency assessment',
  Immediate_Condition:
    'Equipment maintenance review, workplace safety audit, engineering controls',
  Root_Personal:
    'Targeted training programs, health/fitness assessments, behavioral safety programs',
  Root_Job:
    'Management system review, work procedure revision, resource allocation review',
};

// Collapsible category section within the accordion
const CLCCategorySection: FC<{
  categoryCode: string;
  category: CLCHierarchyCategory;
  selectedCodes: string[];
  onToggle: (code: string) => void;
  search: string;
}> = ({ categoryCode, category, selectedCodes, onToggle, search }) => {
  const [expanded, setExpanded] = useState(false);

  const filteredItems = useMemo(() => {
    const entries = Object.entries(category.items);
    if (!search) return entries;
    const q = search.toLowerCase();
    return entries.filter(
      ([code, name]) =>
        code.toLowerCase().includes(q) || name.toLowerCase().includes(q)
    );
  }, [category.items, search]);

  const selectedCount = useMemo(
    () =>
      Object.keys(category.items).filter((code) =>
        selectedCodes.includes(code)
      ).length,
    [category.items, selectedCodes]
  );

  // Auto-expand when search matches items in this category
  useEffect(() => {
    if (search && filteredItems.length > 0) {
      setExpanded(true);
    }
  }, [search, filteredItems.length]);

  if (search && filteredItems.length === 0) return null;

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-1.5 rounded px-2 py-1.5 text-left text-sm hover:bg-neutral-50"
      >
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-neutral-400" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-neutral-400" />
        )}
        <span className="font-mono text-xs text-neutral-400">
          {categoryCode}
        </span>
        <span className="flex-1 truncate font-medium text-neutral-700">
          {category.name}
        </span>
        {selectedCount > 0 && (
          <Badge className="ml-auto h-5 min-w-[20px] justify-center bg-primary-100 px-1.5 text-[10px] font-semibold text-primary-700">
            {selectedCount}
          </Badge>
        )}
      </button>

      {expanded && (
        <div className="ml-5 border-l border-neutral-100 pl-2">
          {filteredItems.map(([code, name]) => {
            const isSelected = selectedCodes.includes(code);
            return (
              <label
                key={code}
                className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 text-sm hover:bg-neutral-50"
              >
                <Checkbox
                  checked={isSelected}
                  onCheckedChange={() => onToggle(code)}
                />
                <span className="font-mono text-xs text-neutral-500">
                  {code}
                </span>
                <span className="flex-1 truncate text-neutral-700">
                  {name}
                </span>
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
};

const CLCMultiSelect: FC<CLCMultiSelectProps> = ({
  selectedCodes,
  onAdd,
  onRemove,
}) => {
  const [search, setSearch] = useState('');
  const { data: hierarchy, isLoading } = useCLCHierarchy();

  const codeNameMap = useMemo(() => buildCodeNameMap(hierarchy), [hierarchy]);

  const handleToggle = useCallback(
    (code: string) => {
      if (selectedCodes.includes(code)) {
        onRemove(code);
      } else {
        onAdd(code);
      }
    },
    [selectedCodes, onAdd, onRemove]
  );

  const renderSection = (
    label: string,
    categories: Record<string, CLCHierarchyCategory>
  ) => {
    const catEntries = Object.entries(categories);
    const hasSearchResults =
      !search ||
      catEntries.some(([, cat]) =>
        Object.entries(cat.items).some(
          ([code, name]) =>
            code.toLowerCase().includes(search.toLowerCase()) ||
            name.toLowerCase().includes(search.toLowerCase())
        )
      );
    if (!hasSearchResults) return null;

    return (
      <div>
        <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-neutral-400">
          {label}
        </div>
        {catEntries.map(([code, cat]) => (
          <CLCCategorySection
            key={code}
            categoryCode={code}
            category={cat}
            selectedCodes={selectedCodes}
            onToggle={handleToggle}
            search={search}
          />
        ))}
      </div>
    );
  };

  return (
    <div>
      {/* Selected chips */}
      {selectedCodes.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {selectedCodes.map((code) => (
            <span
              key={code}
              className="inline-flex items-center gap-1 rounded-full bg-primary-50 px-2.5 py-1 text-xs font-medium text-primary-700"
            >
              <span className="font-mono font-semibold">{code}</span>
              <span className="max-w-[150px] truncate">
                {codeNameMap[code] || code}
              </span>
              <button
                type="button"
                onClick={() => onRemove(code)}
                aria-label={`Remove CLC code ${code}`}
                className="ml-0.5 rounded-full p-0.5 hover:bg-primary-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search input */}
      <div className="mb-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search CLC codes"
            placeholder="Search CLC codes..."
            className="w-full rounded-md border border-neutral-300 bg-white py-1.5 pl-8 pr-3 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>
      </div>

      {/* Hierarchical list */}
      <div className="max-h-64 overflow-y-auto rounded-md border border-neutral-200 bg-white">
        {isLoading ? (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-neutral-400" />
          </div>
        ) : !hierarchy ? (
          <div className="py-4 text-center text-sm text-neutral-500">
            Failed to load CLC codes
          </div>
        ) : (
          <div className="divide-y divide-neutral-100 p-1">
            {renderSection('Immediate Causes — Actions', hierarchy.immediate_causes.actions)}
            {renderSection('Immediate Causes — Conditions', hierarchy.immediate_causes.conditions)}
            {renderSection('Root Causes — Personal Factors', hierarchy.root_causes.personal_factors)}
            {renderSection('Root Causes — Job Factors', hierarchy.root_causes.job_factors)}
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Add Action Inline Form
// ============================================================================

interface AddActionInlineProps {
  actionType: ActionType;
  carId: string | number;
  onAdded: () => void;
  onCancel: () => void;
}

const AddActionInline: FC<AddActionInlineProps> = ({
  actionType,
  carId,
  onAdded,
  onCancel,
}) => {
  const createAction = useCreateAction(carId);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AddActionFormData>({
    resolver: zodResolver(addActionSchema),
    defaultValues: {
      ...addActionDefaults,
      action_type: actionType,
    },
  });

  const onSubmitAction = async (data: AddActionFormData) => {
    await createAction.mutateAsync({
      action_type: data.action_type,
      description: data.description,
    });
    onAdded();
  };

  return (
    <div className="rounded-md border border-primary-200 bg-primary-50/30 p-3">
      <div className="space-y-3">
        <div>
          <Label className="text-sm">
            Description <span className="text-error-500">*</span>
          </Label>
          <Textarea
            {...register('description')}
            placeholder="Describe the corrective action..."
            rows={2}
            className={cn(errors.description && 'border-error-500')}
          />
          {errors.description && (
            <p className="mt-1 text-xs text-error-500">
              {errors.description.message}
            </p>
          )}
        </div>

        <div className="flex items-center justify-end gap-2">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onCancel}
          >
            Cancel
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={handleSubmit(onSubmitAction)}
            disabled={createAction.isPending}
          >
            {createAction.isPending ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            ) : (
              <Plus className="mr-1 h-4 w-4" />
            )}
            Add
          </Button>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Action Item Row (Editable)
// ============================================================================

interface ActionItemRowProps {
  action: CorrectiveAction;
  carId: string | number;
  canEdit: boolean;
}

const ActionItemRow: FC<ActionItemRowProps> = ({ action, carId, canEdit }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editDesc, setEditDesc] = useState(action.description);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const updateAction = useUpdateAction(carId);
  const deleteAction = useDeleteAction(carId);

  const handleSaveEdit = async () => {
    if (!editDesc.trim()) return;
    await updateAction.mutateAsync({
      actionId: action.id,
      data: {
        description: editDesc.trim(),
      },
    });
    setIsEditing(false);
  };

  const handleDelete = async () => {
    await deleteAction.mutateAsync(action.id);
    setConfirmDelete(false);
  };

  return (
    <>
      <div className="rounded-md border border-neutral-200 bg-white p-3">
        <div className="flex items-start gap-3">
          {/* Completed indicator */}
          <div className="mt-0.5 flex-shrink-0">
            {action.is_completed ? (
              <div className="flex h-5 w-5 items-center justify-center rounded-full bg-success-100">
                <Check className="h-3 w-3 text-success-600" />
              </div>
            ) : (
              <div className="h-5 w-5 rounded-full border-2 border-neutral-300" />
            )}
          </div>

          {/* Content */}
          <div className="min-w-0 flex-1">
            {isEditing ? (
              <div className="space-y-2">
                <Textarea
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  rows={2}
                  className="text-sm"
                />
                <div className="flex gap-2">
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleSaveEdit}
                    disabled={updateAction.isPending || !editDesc.trim()}
                  >
                    {updateAction.isPending ? (
                      <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                    ) : (
                      <Check className="mr-1 h-3 w-3" />
                    )}
                    Save
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setIsEditing(false);
                      setEditDesc(action.description);
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <p className="text-sm text-neutral-700">{action.description}</p>
                <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-neutral-500">
                  {action.owner_name && (
                    <span className="font-medium text-neutral-600">
                      {action.owner_name}
                    </span>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Actions */}
          {canEdit && !isEditing && (
            <div className="flex flex-shrink-0 gap-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setIsEditing(true)}
                className="text-xs"
              >
                Edit
              </Button>
              <button
                type="button"
                onClick={() => setConfirmDelete(true)}
                className="rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-error-500"
                aria-label="Delete action"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete Corrective Action"
        description="Are you sure you want to delete this corrective action? This cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        confirmDisabled={deleteAction.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
};

// ============================================================================
// Evidence Item (with delete)
// ============================================================================

interface EvidenceItemEditableProps {
  item: Evidence;
  carId: string | number;
  canDelete: boolean;
}

const EvidenceItemEditable: FC<EvidenceItemEditableProps> = ({
  item,
  carId,
  canDelete,
}) => {
  const deleteEvidence = useDeleteEvidence(carId);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const isImage = item.mime_type.startsWith('image/');
  const evidenceUrl = resolveEvidenceUrl(item);

  return (
    <>
      <div className="flex items-start gap-3 rounded-md border border-neutral-200 bg-white p-3">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded bg-neutral-100">
          {isImage ? (
            <Image className="h-5 w-5 text-primary-500" />
          ) : (
            <FileText className="h-5 w-5 text-error-500" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <a
            href={evidenceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="block truncate text-sm font-medium text-primary-600 hover:underline"
            onClick={(event: MouseEvent<HTMLAnchorElement>) => {
              event.preventDefault();
              void openEvidenceWithAuth(evidenceUrl, item.file_name, item.mime_type);
            }}
          >
            {item.file_name}
          </a>
          <p className="text-xs text-neutral-500">{item.description}</p>
          <p className="mt-0.5 text-xs text-neutral-400">
            {formatDate(item.uploaded_at)} &middot;{' '}
            {formatFileSize(item.file_size)}
          </p>
        </div>
        {canDelete && (
          <button
            type="button"
            onClick={() => setConfirmDelete(true)}
            aria-label={`Delete evidence ${item.file_name}`}
            className="flex-shrink-0 rounded p-1 text-neutral-400 hover:bg-neutral-100 hover:text-error-500"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </div>

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete Evidence"
        description={`Are you sure you want to delete "${item.file_name}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        confirmDisabled={deleteEvidence.isPending}
        onConfirm={async () => {
          await deleteEvidence.mutateAsync(item.id);
          setConfirmDelete(false);
        }}
      />
    </>
  );
};

// ============================================================================
// Main Form Component
// ============================================================================

export const CARForm: FC<CARFormProps> = ({
  car,
  onSaveDraft,
  onSubmit,
  onCancel,
  onUploadEvidence,
  isSaving = false,
  isSubmitting = false,
  submitLabel = 'Submit CAR',
  submitDescription = 'This will submit the CAR for PIC review. Continue?',
  className,
}) => {
  // ── State ──────────────────────────────────────────────────────────────────
  const [showAddImmediate, setShowAddImmediate] = useState(false);
  const [showAddLongTerm, setShowAddLongTerm] = useState(false);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  const [submitErrors, setSubmitErrors] = useState<string[]>([]);

  // ── Form ───────────────────────────────────────────────────────────────────

  // Auto-set target date to 7 days from CAR creation if not already set
  const defaultTargetDate = useMemo(() => {
    if (car.target_date) return car.target_date;
    const created = new Date(car.created_date);
    created.setDate(created.getDate() + 7);
    return created.toISOString().split('T')[0];
  }, [car.target_date, car.created_date]);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isDirty, dirtyFields },
  } = useForm<UpdateCarFormData>({
    resolver: zodResolver(updateCarSchema),
    defaultValues: {
      root_cause_summary: car.root_cause_summary || '',
      target_date: defaultTargetDate,
      clc_item_ids: car.clc_items.map((c) => c.clc_item_id),
      custom_cause_text: '',
    },
  });

  const watchedRootCause = watch('root_cause_summary') || '';
  const rawClcIds = watch('clc_item_ids');
  const watchedClcIds = useMemo(() => rawClcIds || [], [rawClcIds]);

  // ── CLC hierarchy for improvement guidance ────────────────────────────────
  const { data: clcHierarchy } = useCLCHierarchy();

  const improvementGuidance = useMemo(() => {
    if (watchedClcIds.length === 0 || !clcHierarchy) return [];
    const types = getSelectedCategoryTypes(watchedClcIds, clcHierarchy);
    return Array.from(types)
      .filter((t) => IMPROVEMENT_GUIDANCE[t])
      .map((t) => IMPROVEMENT_GUIDANCE[t]);
  }, [watchedClcIds, clcHierarchy]);

  // ── Derived data ───────────────────────────────────────────────────────────
  const immediateActions = useMemo(
    () =>
      car.corrective_actions.filter((a) => a.action_type === 'IMMEDIATE'),
    [car.corrective_actions]
  );

  const longTermActions = useMemo(
    () =>
      car.corrective_actions.filter((a) => a.action_type === 'LONG_TERM'),
    [car.corrective_actions]
  );

  const beforeEvidence = useMemo(
    () => car.evidence.filter((e) => e.evidence_type === EVIDENCE_TYPES.BEFORE),
    [car.evidence]
  );

  const afterEvidence = useMemo(
    () => car.evidence.filter((e) => e.evidence_type === EVIDENCE_TYPES.AFTER),
    [car.evidence]
  );

  const otherEvidence = useMemo(
    () => car.evidence.filter((e) => e.evidence_type === EVIDENCE_TYPES.OTHER),
    [car.evidence]
  );

  // ── Handlers ───────────────────────────────────────────────────────────────
  const handleSaveDraft = handleSubmit(async (data) => {
    await onSaveDraft(data);
  });

  const buildDirtyUpdatePayload = useCallback(
    (data: UpdateCarFormData): UpdateCarFormData => {
      const payload: UpdateCarFormData = {};

      if (dirtyFields.root_cause_summary) {
        payload.root_cause_summary = data.root_cause_summary;
      }
      if (dirtyFields.target_date) {
        payload.target_date = data.target_date;
      }
      if (dirtyFields.clc_item_ids) {
        payload.clc_item_ids = data.clc_item_ids;
      }
      if (dirtyFields.custom_cause_text) {
        payload.custom_cause_text = data.custom_cause_text;
      }

      return payload;
    },
    [dirtyFields]
  );

  const handleAddClcCode = useCallback(
    (code: string) => {
      const current = watchedClcIds;
      if (!current.includes(code)) {
        setValue('clc_item_ids', [...current, code], { shouldDirty: true });
      }
    },
    [watchedClcIds, setValue]
  );

  const handleRemoveClcCode = useCallback(
    (code: string) => {
      const current = watchedClcIds;
      setValue(
        'clc_item_ids',
        current.filter((c) => c !== code),
        { shouldDirty: true }
      );
    },
    [watchedClcIds, setValue]
  );

  const handleSubmitClick = () => {
    // Validate all submission preconditions
    const result = validateCarSubmission(
      watchedRootCause,
      watchedClcIds,
      watch('custom_cause_text'),
      car.corrective_actions,
      car.evidence
    );

    if (!result.valid) {
      setSubmitErrors(result.errors);
      setShowSubmitConfirm(true);
      return;
    }

    setSubmitErrors([]);
    setShowSubmitConfirm(true);
  };

  const handleConfirmSubmit = async () => {
    // Save only user-edited draft fields, then submit. This avoids resending
    // unchanged overdue target dates when PIC only starts review.
    const data = watch();
    if (isDirty) {
      await onSaveDraft(buildDirtyUpdatePayload(data));
    }
    if (onSubmit) {
      await onSubmit();
    }
    setShowSubmitConfirm(false);
  };

  const handleActionAdded = () => {
    setShowAddImmediate(false);
    setShowAddLongTerm(false);
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className={cn('space-y-4 pb-24', className)}>
      {/* ── Section 1: Deficiency (Read-only) ─────────────────────────────── */}
      <Card>
        <CardContent className="p-4">
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Deficiency
          </h2>
          {car.deficiency ? (
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge
                  variant="secondary"
                  className="font-mono text-sm font-bold"
                >
                  {car.deficiency.def_code}
                </Badge>
                {car.deficiency.action_code && (
                  <Badge className="bg-amber-50 text-amber-700 text-xs">
                    Action: {car.deficiency.action_code}
                  </Badge>
                )}
                {car.deficiency.is_cleared ? (
                  <Badge className="bg-success-100 text-success-700 text-xs">
                    Cleared
                    {car.deficiency.cleared_date &&
                      ` — ${formatDate(car.deficiency.cleared_date)}`}
                  </Badge>
                ) : (
                  <Badge className="bg-error-50 text-error-700 text-xs">
                    Open
                  </Badge>
                )}
              </div>
              <p className="mt-2 text-sm text-neutral-700">
                {car.deficiency.description}
              </p>
              {car.deficiency.target_date && (
                <p className="mt-1 text-xs text-neutral-500">
                  Deficiency target date:{' '}
                  <span className="font-medium text-neutral-700">
                    {formatDate(car.deficiency.target_date)}
                  </span>
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm italic text-neutral-500">
              No deficiency linked
            </p>
          )}
        </CardContent>
      </Card>

      {/* ── Section 2: Root Cause Analysis ─────────────────────────────────── */}
      <Card>
        <CardContent className="p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Root Cause Analysis
          </h2>

          {/* CLC Codes Multi-Select */}
          <div className="mb-4">
            <Label className="mb-1.5 block text-sm font-medium">
              CLC Codes
            </Label>
            <CLCMultiSelect
              selectedCodes={watchedClcIds}
              onAdd={handleAddClcCode}
              onRemove={handleRemoveClcCode}
            />
          </div>

          {/* Custom Cause Text */}
          <div className="mb-4">
            <Label className="mb-1.5 block text-sm font-medium">
              Custom Cause
            </Label>
            <Input
              {...register('custom_cause_text')}
              placeholder="Additional cause not in CLC codes (optional)"
            />
            {errors.custom_cause_text && (
              <p className="mt-1 text-xs text-error-500">
                {errors.custom_cause_text.message}
              </p>
            )}
          </div>

          {/* Root Cause Summary */}
          <div>
            <Label className="mb-1.5 block text-sm font-medium">
              Root Cause Summary{' '}
              <span className="text-error-500">*</span>
            </Label>
            <Textarea
              {...register('root_cause_summary')}
              placeholder="Describe the root cause analysis in detail (minimum 50 characters)..."
              rows={4}
              className={cn(errors.root_cause_summary && 'border-error-500')}
            />
            <div className="mt-1 flex items-center justify-between">
              {errors.root_cause_summary ? (
                <p className="text-xs text-error-500">
                  {errors.root_cause_summary.message}
                </p>
              ) : (
                <span />
              )}
              <span
                className={cn(
                  'text-xs',
                  watchedRootCause.length < ROOT_CAUSE_MIN_LENGTH
                    ? 'text-neutral-400'
                    : 'text-success-600'
                )}
              >
                {watchedRootCause.length}/{ROOT_CAUSE_MIN_LENGTH}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Section 3: Corrective Actions ──────────────────────────────────── */}
      <Card>
        <CardContent className="p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Corrective Actions
          </h2>

          {/* Immediate Actions */}
          <div className="mb-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-neutral-700">
                Immediate Actions{' '}
                <span className="text-error-500">*</span>
                <span className="ml-1 font-normal text-neutral-400">
                  ({immediateActions.length})
                </span>
              </h3>
            </div>

            {immediateActions.length === 0 && !showAddImmediate && (
              <p className="mb-2 text-sm italic text-neutral-500">
                No immediate actions yet
              </p>
            )}

            <div className="space-y-2">
              {immediateActions.map((action) => (
                <ActionItemRow
                  key={action.id}
                  action={action}
                  carId={car.id}
                  canEdit
                />
              ))}
            </div>

            {showAddImmediate ? (
              <div className="mt-2">
                <AddActionInline
                  actionType="IMMEDIATE"
                  carId={car.id}

                  onAdded={handleActionAdded}
                  onCancel={() => setShowAddImmediate(false)}
                />
              </div>
            ) : (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={() => setShowAddImmediate(true)}
              >
                <Plus className="mr-1 h-4 w-4" />
                Add Immediate Action
              </Button>
            )}
          </div>

          {/* Improvement Guidance */}
          {improvementGuidance.length > 0 && (
            <div className="mb-4 rounded-md border border-blue-200 bg-blue-50 p-3">
              <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-blue-700">
                <Info className="h-3.5 w-3.5" />
                Suggested areas of improvement based on selected causes:
              </div>
              <ul className="space-y-0.5 pl-5 text-xs text-blue-600">
                {improvementGuidance.map((hint) => (
                  <li key={hint} className="list-disc">
                    {hint}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Long-Term Actions */}
          <div>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-neutral-700">
                Long-term Actions{' '}
                <span className="text-error-500">*</span>
                <span className="ml-1 font-normal text-neutral-400">
                  ({longTermActions.length})
                </span>
              </h3>
            </div>

            {longTermActions.length === 0 && !showAddLongTerm && (
              <p className="mb-2 text-sm italic text-neutral-500">
                No long-term actions yet
              </p>
            )}

            <div className="space-y-2">
              {longTermActions.map((action) => (
                <ActionItemRow
                  key={action.id}
                  action={action}
                  carId={car.id}
                  canEdit
                />
              ))}
            </div>

            {showAddLongTerm ? (
              <div className="mt-2">
                <AddActionInline
                  actionType="LONG_TERM"
                  carId={car.id}

                  onAdded={handleActionAdded}
                  onCancel={() => setShowAddLongTerm(false)}
                />
              </div>
            ) : (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={() => setShowAddLongTerm(true)}
              >
                <Plus className="mr-1 h-4 w-4" />
                Add Long-term Action
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* ── Section 4: Target Dates ────────────────────────────────────────── */}
      <Card>
        <CardContent className="p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Target Date
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Label className="mb-1.5 block text-sm font-medium">
                Target Date
              </Label>
              <DatePicker
                value={watch('target_date') || ''}
                onChange={(val) =>
                  setValue('target_date', val || null, { shouldDirty: true })
                }
                disablePast
              />
              {errors.target_date && (
                <p className="mt-1 text-xs text-error-500">
                  {errors.target_date.message}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Section 5: Evidence ─────────────────────────────────────────────── */}
      <Card>
        <CardContent className="p-4">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            Evidence
          </h2>

          {/* Missing evidence warning */}
          {(beforeEvidence.length === 0 || afterEvidence.length === 0) && (
            <div className="mb-3 flex items-center gap-2 rounded-md bg-warning-50 p-2 text-sm text-warning-700">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <span>
                Missing{' '}
                {beforeEvidence.length === 0 && afterEvidence.length === 0
                  ? 'BEFORE and AFTER'
                  : beforeEvidence.length === 0
                    ? 'BEFORE'
                    : 'AFTER'}{' '}
                evidence (required for submission)
              </span>
            </div>
          )}

          {/* Before Evidence */}
          <div className="mb-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-neutral-700">
                BEFORE Evidence{' '}
                <span className="text-error-500">*</span>
                <span className="ml-1 font-normal text-neutral-400">
                  ({beforeEvidence.length})
                </span>
              </h3>
              {onUploadEvidence && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => onUploadEvidence('BEFORE')}
                >
                  <Upload className="mr-1 h-3 w-3" />
                  Upload
                </Button>
              )}
            </div>
            {beforeEvidence.length === 0 ? (
              <p className="text-sm italic text-neutral-500">
                No BEFORE evidence uploaded
              </p>
            ) : (
              <div className="space-y-2">
                {beforeEvidence.map((item) => (
                  <EvidenceItemEditable
                    key={item.id}
                    item={item}
                    carId={car.id}
                    canDelete
                  />
                ))}
              </div>
            )}
          </div>

          {/* After Evidence */}
          <div className="mb-4">
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-neutral-700">
                AFTER Evidence{' '}
                <span className="text-error-500">*</span>
                <span className="ml-1 font-normal text-neutral-400">
                  ({afterEvidence.length})
                </span>
              </h3>
              {onUploadEvidence && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => onUploadEvidence('AFTER')}
                >
                  <Upload className="mr-1 h-3 w-3" />
                  Upload
                </Button>
              )}
            </div>
            {afterEvidence.length === 0 ? (
              <p className="text-sm italic text-neutral-500">
                No AFTER evidence uploaded
              </p>
            ) : (
              <div className="space-y-2">
                {afterEvidence.map((item) => (
                  <EvidenceItemEditable
                    key={item.id}
                    item={item}
                    carId={car.id}
                    canDelete
                  />
                ))}
              </div>
            )}
          </div>

          {/* Other Evidence */}
          {otherEvidence.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-neutral-700">
                OTHER ({otherEvidence.length})
              </h3>
              <div className="space-y-2">
                {otherEvidence.map((item) => (
                  <EvidenceItemEditable
                    key={item.id}
                    item={item}
                    carId={car.id}
                    canDelete
                  />
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Sticky Bottom Action Bar ───────────────────────────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-neutral-200 bg-white p-4 shadow-lg">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              if (isDirty) {
                setShowCancelConfirm(true);
              } else {
                onCancel();
              }
            }}
          >
            Cancel
          </Button>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={handleSaveDraft}
              disabled={isSaving || isSubmitting}
            >
              {isSaving && <Loader2 className="mr-1 h-4 w-4 animate-spin" />}
              Save Draft
            </Button>

            {onSubmit && (
              <Button
                type="button"
                onClick={handleSubmitClick}
                disabled={isSaving || isSubmitting}
              >
                {isSubmitting && (
                  <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                )}
                {submitLabel}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* ── Dialogs ────────────────────────────────────────────────────────── */}
      <ConfirmDialog
        open={showCancelConfirm}
        onOpenChange={setShowCancelConfirm}
        title="Discard Changes?"
        description="You have unsaved changes. Are you sure you want to leave?"
        confirmLabel="Discard"
        variant="destructive"
        onConfirm={onCancel}
      />

      {/* Submit validation errors dialog */}
      {submitErrors.length > 0 && (
        <ConfirmDialog
          open={showSubmitConfirm}
          onOpenChange={setShowSubmitConfirm}
          title="Cannot Submit CAR"
          description="The following requirements must be met before submission:"
          confirmLabel="OK"
          onConfirm={() => setShowSubmitConfirm(false)}
        >
          <ul className="mt-2 space-y-1">
            {submitErrors.map((err, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-error-600">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
                {err}
              </li>
            ))}
          </ul>
        </ConfirmDialog>
      )}

      {/* Submit confirmation dialog */}
      {submitErrors.length === 0 && (
        <ConfirmDialog
          open={showSubmitConfirm}
          onOpenChange={setShowSubmitConfirm}
          title={submitLabel}
          description={submitDescription}
          confirmLabel="Confirm"
          confirmDisabled={isSubmitting}
          onConfirm={handleConfirmSubmit}
        />
      )}
    </div>
  );
};
