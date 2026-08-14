import { useEffect, useMemo, useState, type Dispatch, type FormEvent, type SetStateAction } from 'react';
import { FilePlus2, Plus, Trash2 } from 'lucide-react';
import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
  Textarea,
} from '@/components/ui';
import { useCreateAuditFinding, useAuditClauseMaster } from '@/hooks/audit/use-audit-finding';
import { useToast } from '@/hooks/use-toast';
import type { AuditChecklistItem } from '@/schemas/audit/checklist';
import {
  FINDING_TYPES,
  FINDING_PRIORITIES,
  CERTIFICATE_IMPACTS,
  NC_CATEGORIES,
  OBSERVATION_CATEGORIES,
  RULE_BOOK_TYPES,
  auditFindingCreateSchema,
  findingDefaults,
  type AuditFindingCreateFormData,
} from '@/schemas/audit/finding';
import { cn } from '@/lib/utils';

interface AuditFindingCreateModalProps {
  auditId: string;
  open: boolean;
  checklistItem: AuditChecklistItem | null;
  onOpenChange: (open: boolean) => void;
}

export function AuditFindingCreateModal({
  auditId,
  open,
  checklistItem,
  onOpenChange,
}: AuditFindingCreateModalProps) {
  const [form, setForm] = useState<AuditFindingCreateFormData>(() => findingDefaults());
  const [error, setError] = useState<string | null>(null);
  const createFinding = useCreateAuditFinding(auditId);
  const { toast } = useToast();

  useEffect(() => {
    if (!open) return;
    setForm(findingDefaults(checklistItem?.id));
    setError(null);
  }, [checklistItem, open]);

  const primaryBook = form.clauses[0]?.rule_book_type;
  const secondaryBook = form.clauses[1]?.rule_book_type;
  const primaryClauses = useAuditClauseMaster(primaryBook);
  const secondaryClauses = useAuditClauseMaster(secondaryBook);

  const contextText = useMemo(() => {
    if (!checklistItem) return 'Emergent finding';
    return `${checklistItem.item_code} - ${checklistItem.question}`;
  }, [checklistItem]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const parsed = auditFindingCreateSchema.safeParse(form);
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message || 'Finding payload is incomplete.');
      return;
    }

    try {
      const result = await createFinding.mutateAsync(parsed.data);
      toast({ title: `Finding created: ${result.car_number}` });
      onOpenChange(false);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : 'Finding could not be created.';
      setError(message);
      toast({ title: 'Finding create failed', description: message, variant: 'destructive' });
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Create Audit Finding</DialogTitle>
          <DialogDescription>{contextText}</DialogDescription>
        </DialogHeader>

        <form className="space-y-4" onSubmit={handleSubmit}>
          {error ? (
            <div className="rounded-md border border-error-100 bg-error-50 p-3 text-sm text-error-700" role="alert">
              {error}
            </div>
          ) : null}

          <div className="grid gap-3 md:grid-cols-3">
            <SelectField
              id="finding_type"
              label="Finding Type"
              value={form.finding_type}
              options={FINDING_TYPES.map((value) => ({ value, label: value }))}
              onChange={(value) =>
                setForm((current) => ({
                  ...current,
                  finding_type: value as AuditFindingCreateFormData['finding_type'],
                  is_fleetwide_relevance: value === 'NC' ? current.is_fleetwide_relevance : false,
                }))
              }
            />
            {form.finding_type === 'NC' ? (
              <SelectField
                id="nc_category"
                label="NC Category"
                value={form.nc_category || ''}
                options={NC_CATEGORIES.map((value) => ({ value, label: value.replace('_', ' ') }))}
                onChange={(value) => setForm((current) => ({ ...current, nc_category: value as typeof NC_CATEGORIES[number] }))}
              />
            ) : (
              <SelectField
                id="observation_category"
                label="Observation Category"
                value={form.observation_category || ''}
                options={OBSERVATION_CATEGORIES.map((value) => ({ value, label: value.replaceAll('_', ' ') }))}
                onChange={(value) =>
                  setForm((current) => ({
                    ...current,
                    observation_category: value as typeof OBSERVATION_CATEGORIES[number],
                  }))
                }
              />
            )}
            <div className="space-y-2">
              <Label htmlFor="def_code_id">DefCode</Label>
              <Input
                id="def_code_id"
                maxLength={5}
                value={form.def_code_id}
                onChange={(event) => setForm((current) => ({ ...current, def_code_id: event.target.value }))}
              />
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3">
            <SelectField
              id="priority"
              label="Priority"
              value={form.priority || 'MEDIUM'}
              options={FINDING_PRIORITIES.map((value) => ({ value, label: value }))}
              onChange={(value) =>
                setForm((current) => ({
                  ...current,
                  priority: value as AuditFindingCreateFormData['priority'],
                }))
              }
            />
            <SelectField
              id="certificate_impact"
              label="Certificate Impact"
              value={form.certificate_impact || ''}
              options={[
                { value: '', label: 'Not set' },
                ...CERTIFICATE_IMPACTS.map((value) => ({ value, label: value.replaceAll('_', ' ') })),
              ]}
              onChange={(value) => setForm((current) => ({ ...current, certificate_impact: value as AuditFindingCreateFormData['certificate_impact'] }))}
            />
            {form.finding_type === 'NC' ? (
              <label className="flex min-h-10 items-center gap-3 rounded-md border border-neutral-200 px-3 py-2 text-sm text-neutral-800">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                  checked={Boolean(form.is_fleetwide_relevance)}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      is_fleetwide_relevance: event.target.checked,
                    }))
                  }
                />
                Fleet-wide relevance
              </label>
            ) : (
              <div className="rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-500">
                Fleet-wide Circular is NC only
              </div>
            )}
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                rows={5}
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="objective_evidence">Objective Evidence</Label>
              <Textarea
                id="objective_evidence"
                rows={5}
                value={form.objective_evidence}
                onChange={(event) => setForm((current) => ({ ...current, objective_evidence: event.target.value }))}
              />
            </div>
          </div>

          <div className="space-y-3 rounded-md border border-neutral-200 p-3">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-medium text-neutral-900">Clause References</p>
                <p className="text-xs text-neutral-500">One primary clause is required.</p>
              </div>
              {form.clauses.length < 2 ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setForm((current) => ({
                      ...current,
                      clauses: [
                        ...current.clauses,
                        {
                          rule_book_type: 'OTHER',
                          rule_clause_id: '',
                          clause_ref_text: '',
                          clause_subref_text: '',
                          is_primary: false,
                        },
                      ],
                    }))
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Clause
                </Button>
              ) : null}
            </div>

            <ClauseFields
              index={0}
              form={form}
              clauseStatus={primaryClauses}
              onChange={setForm}
              canRemove={false}
            />
            {form.clauses[1] ? (
              <ClauseFields
                index={1}
                form={form}
                clauseStatus={secondaryClauses}
                onChange={setForm}
                canRemove
              />
            ) : null}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createFinding.isPending}>
              <FilePlus2 className="mr-2 h-4 w-4" />
              {createFinding.isPending ? 'Saving...' : 'Save Finding'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ClauseFields({
  index,
  form,
  clauseStatus,
  onChange,
  canRemove,
}: {
  index: number;
  form: AuditFindingCreateFormData;
  clauseStatus: ReturnType<typeof useAuditClauseMaster>;
  onChange: Dispatch<SetStateAction<AuditFindingCreateFormData>>;
  canRemove: boolean;
}) {
  const clause = form.clauses[index];
  const textOnly = clause.rule_book_type === 'OTHER' || clause.rule_book_type === 'FLAG';
  const prefix = index === 0 ? 'Primary' : 'Secondary';

  return (
    <div className="grid gap-3 rounded-md border border-neutral-100 bg-neutral-50 p-3 md:grid-cols-[140px_minmax(0,1fr)_minmax(0,1fr)_auto]">
      <SelectField
        id={`rule_book_type_${index}`}
        label={`${prefix} Book`}
        value={clause.rule_book_type}
        options={RULE_BOOK_TYPES.map((value) => ({ value, label: value }))}
        onChange={(value) =>
          updateClause(onChange, index, {
            rule_book_type: value as typeof RULE_BOOK_TYPES[number],
            rule_clause_id: '',
            clause_ref_text: '',
          })
        }
      />
      {textOnly ? (
        <div className="space-y-2">
          <Label htmlFor={`clause_ref_text_${index}`}>Clause Text</Label>
          <Input
            id={`clause_ref_text_${index}`}
            value={clause.clause_ref_text}
            onChange={(event) => updateClause(onChange, index, { clause_ref_text: event.target.value })}
          />
        </div>
      ) : (
        <SelectField
          id={`rule_clause_id_${index}`}
          label="Seeded Clause"
          value={clause.rule_clause_id || ''}
          options={(clauseStatus.data?.clauses ?? []).map((row) => ({
            value: row.id,
            label: `${row.code} - ${row.title}`,
          }))}
          placeholder={clauseStatus.isLoading ? 'Loading clauses' : 'Select clause'}
          onChange={(value) => updateClause(onChange, index, { rule_clause_id: value })}
        />
      )}
      <div className="space-y-2">
        <Label htmlFor={`clause_subref_text_${index}`}>Sub Reference</Label>
        <Input
          id={`clause_subref_text_${index}`}
          value={clause.clause_subref_text}
          onChange={(event) => updateClause(onChange, index, { clause_subref_text: event.target.value })}
        />
      </div>
      <div className="flex items-end gap-2">
        <label className="flex h-10 items-center gap-2 text-sm text-neutral-700">
          <input
            type="radio"
            name="primary_clause"
            checked={clause.is_primary}
            onChange={() =>
              onChange((current) => ({
                ...current,
                clauses: current.clauses.map((candidate, candidateIndex) => ({
                  ...candidate,
                  is_primary: candidateIndex === index,
                })),
              }))
            }
          />
          Primary
        </label>
        {canRemove ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Remove secondary clause"
            onClick={() =>
              onChange((current) => ({
                ...current,
                clauses: current.clauses.filter((_, candidateIndex) => candidateIndex !== index),
              }))
            }
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function SelectField({
  id,
  label,
  value,
  options,
  placeholder,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        className={cn(
          'h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2'
        )}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {placeholder ? <option value="">{placeholder}</option> : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function updateClause(
  onChange: Dispatch<SetStateAction<AuditFindingCreateFormData>>,
  index: number,
  patch: Partial<AuditFindingCreateFormData['clauses'][number]>
) {
  onChange((current) => ({
    ...current,
    clauses: current.clauses.map((clause, candidateIndex) =>
      candidateIndex === index ? { ...clause, ...patch } : clause
    ),
  }));
}
