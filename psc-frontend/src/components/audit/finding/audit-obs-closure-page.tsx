import { useEffect, useMemo, useState, type KeyboardEvent, type ReactNode } from 'react';
import { ArrowLeft, ArrowRight, Check, ClipboardList, FileSignature, Loader2, Save } from 'lucide-react';
import { Button, Badge, Card, CardContent, CardHeader, CardTitle, Input, Label, Textarea } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import { useAuditObsClosure, useUpdateAuditObsPart } from '@/hooks/audit/use-audit-finding';
import { getErrorMessage } from '@/lib/api/client';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import {
  OBS_ACCEPTANCE_DECISIONS,
  OBS_CLOSURE_STATUSES,
  OBS_VERIFICATION_METHODS,
  type AuditObsPartB,
  type AuditObsPartC,
  type AuditObsPartD,
  type AuditObsPartName,
  type AuditObsPartPayload,
} from '@/schemas/audit/obs-closure';
import { useObsWizardStore } from '@/stores/audit/use-obs-wizard-store';

interface AuditObsClosurePageProps {
  findingId: string;
}

function toInputDate(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : '';
}

function toInputDateTime(value: string | null | undefined): string {
  return value ? value.slice(0, 16) : '';
}

function fromInputDate(value: string): string | null {
  return value || null;
}

function fromInputDateTime(value: string): string | null {
  return value || null;
}

const obsWizardSteps = ['Responder', 'Action Plan', 'Master Close'] as const;

function suggestedObsStep(partB: AuditObsPartB): number {
  if (!partB.responded_by_name || !partB.responded_by_rank || !partB.target_closure_date) return 0;
  if (
    !partB.immediate_action_text ||
    !partB.root_cause_text ||
    !partB.corrective_action_text ||
    !partB.preventive_action_text
  ) return 1;
  return 2;
}

export function AuditObsClosurePage({ findingId }: AuditObsClosurePageProps) {
  const { toast } = useToast();
  const { data: closure, isLoading, error, refetch } = useAuditObsClosure(findingId);
  const updatePart = useUpdateAuditObsPart(findingId);
  const { stepIndex, resetForFinding, setStepIndex } = useObsWizardStore();
  const [partB, setPartB] = useState<AuditObsPartB | null>(null);
  const [partC, setPartC] = useState<AuditObsPartC | null>(null);
  const [partD, setPartD] = useState<AuditObsPartD | null>(null);
  const [wizardError, setWizardError] = useState('');

  useEffect(() => {
    if (!closure) return;
    const nextPartB = {
      ...closure.part_b,
      target_closure_date: toInputDate(closure.part_b.target_closure_date),
      actual_closure_date: toInputDate(closure.part_b.actual_closure_date),
      master_sign_at: toInputDateTime(closure.part_b.master_sign_at),
    };
    setPartB(nextPartB);
    setPartC({
      ...closure.part_c,
      acceptance_review_date: toInputDate(closure.part_c.acceptance_review_date),
      acceptance_signer_at: toInputDateTime(closure.part_c.acceptance_signer_at),
    });
    setPartD({
      ...closure.part_d,
      resubmit_by_date: toInputDate(closure.part_d.resubmit_by_date),
      auditor_verification_sign_at: toInputDateTime(closure.part_d.auditor_verification_sign_at),
    });
    resetForFinding(findingId, suggestedObsStep(nextPartB));
  }, [closure, findingId, resetForFinding]);

  const progress = useMemo(
    () => Math.round(((stepIndex + 1) / obsWizardSteps.length) * 100),
    [stepIndex]
  );

  const savePart = async (part: AuditObsPartName, data: AuditObsPartPayload) => {
    try {
      await updatePart.mutateAsync({ part, data });
      toast({ title: `Observation ${part.toUpperCase()} saved` });
    } catch (saveError) {
      toast({
        variant: 'destructive',
        title: `Observation ${part.toUpperCase()} not saved`,
        description: getErrorMessage(saveError),
      });
    }
  };

  const saveWizardStep = async () => {
    if (!partB) return false;
    setWizardError('');
    try {
      await updatePart.mutateAsync({
        part: 'part-b',
        data: {
          ...partB,
          target_closure_date: fromInputDate(partB.target_closure_date || ''),
          actual_closure_date: fromInputDate(partB.actual_closure_date || ''),
          master_sign_at: fromInputDateTime(partB.master_sign_at || ''),
        },
      });
      toast({ title: 'Observation draft saved' });
      return true;
    } catch (stepError) {
      const message = getErrorMessage(stepError);
      setWizardError(message);
      toast({
        variant: 'destructive',
        title: 'Observation draft not saved',
        description: message,
      });
      return false;
    }
  };

  const goNext = async () => {
    if (closure?.state === 'MASTER_CLOSED') return;
    const saved = await saveWizardStep();
    if (saved && stepIndex < obsWizardSteps.length - 1) {
      setStepIndex(stepIndex + 1);
    }
  };

  const goBack = () => {
    setWizardError('');
    setStepIndex(Math.max(0, stepIndex - 1));
  };

  const handleWizardKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    const tagName = (event.target as HTMLElement).tagName;
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
      event.preventDefault();
      void saveWizardStep();
      return;
    }
    if (event.key === 'Escape' && stepIndex > 0) {
      event.preventDefault();
      goBack();
      return;
    }
    if (event.key === 'Enter' && tagName !== 'TEXTAREA') {
      event.preventDefault();
      void goNext();
    }
  };

  if (error || (!isLoading && !closure)) {
    return (
      <RootLayout>
        <PageHeader title="Observation Closure" showBack backTo="/audit" />
        <ErrorState
          title="Observation closure not found"
          message="The finding may not be an Observation, or you may not have access."
          onRetry={() => refetch()}
        />
      </RootLayout>
    );
  }

  if (isLoading || !closure || !partB || !partC || !partD) {
    return (
      <RootLayout>
        <PageHeader title="Observation Closure" showBack backTo="/audit" />
        <div className="space-y-4 p-4">
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <PageHeader
        title="Observation Closure"
        showBack
        backTo="/audit"
        actions={
          <Button variant="outline" size="sm" onClick={() => window.history.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        }
      />
      <div className="space-y-4 p-4">
        <Card>
          <CardContent className="grid gap-4 p-4 lg:grid-cols-[1.4fr_1fr_1fr_auto]">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-semibold text-neutral-900" data-eid="MOCKUP-OBS-06:obs_partA.ref_no">
                  {closure.part_a.observation_reference_no}
                </h1>
                <Badge variant="secondary">{closure.part_a.observation_category || 'OBSERVATION'}</Badge>
                <Badge variant={closure.state === 'MASTER_CLOSED' ? 'success' : 'outline'}>{closure.state}</Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">{closure.part_a.description}</p>
            </div>
            <HeaderDatum label="Vessel / Port" value={`${closure.part_a.vessel_id} / ${closure.part_a.port_place}`} />
            <HeaderDatum label="Target" value={closure.part_a.required_closure_deadline || '-'} />
            <HeaderDatum label="CAR" value={closure.car.status} />
          </CardContent>
        </Card>

        <div
          className="grid gap-4 lg:grid-cols-[3fr_2fr]"
          data-testid="obs-wizard-layout"
          onKeyDown={handleWizardKeyDown}
        >
          <main className="space-y-4">
            <Card>
              <CardContent className="space-y-3 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary">KSM-F-OBS-001</Badge>
                  <Badge variant={closure.state === 'MASTER_CLOSED' ? 'success' : 'outline'}>{closure.state}</Badge>
                </div>
                <div>
                  <p className="text-sm font-medium text-neutral-500">
                    Step {stepIndex + 1} of {obsWizardSteps.length}
                  </p>
                  <h2 className="mt-1 text-xl font-semibold text-neutral-900">{obsWizardSteps[stepIndex]}</h2>
                </div>
                <div className="h-2 rounded-full bg-neutral-100" aria-label="Observation wizard progress">
                  <div className="h-2 rounded-full bg-primary-500" style={{ width: `${progress}%` }} />
                </div>
              </CardContent>
            </Card>

            {wizardError && (
              <div className="rounded-md border border-error-200 bg-error-50 p-3 text-sm text-error-700" role="alert">
                {wizardError}
              </div>
            )}

            <ObsWizardStep
              stepIndex={stepIndex}
              partB={partB}
              terminal={closure.state === 'MASTER_CLOSED'}
              onPartBChange={setPartB}
            />

            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between">
              <Button type="button" variant="outline" onClick={goBack} disabled={stepIndex === 0 || updatePart.isPending}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back
              </Button>
              <div className="flex flex-col gap-2 sm:flex-row">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void saveWizardStep()}
                  disabled={updatePart.isPending || closure.state === 'MASTER_CLOSED'}
                >
                  {updatePart.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                  Save Draft
                </Button>
                <Button
                  type="button"
                  onClick={() => void goNext()}
                  disabled={updatePart.isPending || closure.state === 'MASTER_CLOSED'}
                >
                  {stepIndex === obsWizardSteps.length - 1 ? <Check className="mr-2 h-4 w-4" /> : <ArrowRight className="mr-2 h-4 w-4" />}
                  {stepIndex === obsWizardSteps.length - 1 ? 'Master Close' : 'Save and Continue'}
                </Button>
              </div>
            </div>
          </main>

          <aside className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <ClipboardList className="h-4 w-4" />
                  Observation Context
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <ContextRow label="Reference" value={closure.part_a.observation_reference_no} />
                <ContextRow label="Deadline" value={closure.part_a.required_closure_deadline || '-'} />
                <ContextRow label="Clause" value={closure.part_a.clause_ref_text || closure.part_a.rule_book_type || '-'} />
                <ContextRow label="Evidence" value={closure.part_a.objective_evidence || '-'} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Saved Answers</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <ContextRow label="Responder" value={[partB.responded_by_name, partB.responded_by_rank].filter(Boolean).join(' / ') || '-'} />
                <ContextRow label="Target Date" value={partB.target_closure_date || '-'} />
                <ContextRow label="Action Taken" value={partB.immediate_action_text || '-'} />
                <ContextRow label="Root Cause" value={partB.root_cause_text || '-'} />
                <ContextRow label="Master Signer" value={partB.master_sign_name || '-'} />
              </CardContent>
            </Card>
          </aside>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Part A - Auditor Issuance</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 lg:grid-cols-2">
            <ReadOnlyDatum label="Auditor" value={`${closure.part_a.auditor_name} / ${closure.part_a.auditor_organisation}`} eid="MOCKUP-OBS-06:obs_partA.auditor" />
            <ReadOnlyDatum label="Clause" value={closure.part_a.clause_ref_text || closure.part_a.rule_book_type || '-'} eid="MOCKUP-OBS-06:obs_partA.ref" />
            <ReadOnlyDatum label="Objective Evidence" value={closure.part_a.objective_evidence || '-'} />
            <ReadOnlyDatum label="Issued Date" value={closure.part_a.observation_issued_date || '-'} />
          </CardContent>
        </Card>

        <SectionCard title="Part B - Master / HOD Response">
          <FieldInput id="responded_by_name" label="Responded By Name" value={partB.responded_by_name} onChange={(value) => setPartB({ ...partB, responded_by_name: value })} eid="MOCKUP-OBS-06:obs_wizard_step1.responder" />
          <FieldInput id="responded_by_rank" label="Responded By Rank" value={partB.responded_by_rank} onChange={(value) => setPartB({ ...partB, responded_by_rank: value })} />
          <FieldInput id="target_closure_date" label="Target Closure Date" type="date" value={partB.target_closure_date || ''} onChange={(value) => setPartB({ ...partB, target_closure_date: value })} eid="MOCKUP-OBS-06:obs_wizard_step1.target_date" />
          <FieldInput id="actual_closure_date" label="Actual Closure Date" type="date" value={partB.actual_closure_date || ''} onChange={(value) => setPartB({ ...partB, actual_closure_date: value })} />
          <FieldTextarea id="immediate_action_text" label="Immediate Action" value={partB.immediate_action_text} onChange={(value) => setPartB({ ...partB, immediate_action_text: value })} eid="MOCKUP-OBS-06:obs_wizard_step2.fields" />
          <FieldTextarea id="root_cause_text" label="Root Cause" value={partB.root_cause_text} onChange={(value) => setPartB({ ...partB, root_cause_text: value })} />
          <FieldTextarea id="corrective_action_text" label="Corrective Action" value={partB.corrective_action_text} onChange={(value) => setPartB({ ...partB, corrective_action_text: value })} />
          <FieldTextarea id="preventive_action_text" label="Preventive Action" value={partB.preventive_action_text} onChange={(value) => setPartB({ ...partB, preventive_action_text: value })} />
          <label className="flex items-center gap-2 text-sm text-neutral-700">
            <input
              type="checkbox"
              checked={partB.sms_amendment_required}
              onChange={(event) => setPartB({ ...partB, sms_amendment_required: event.target.checked })}
              className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
            />
            SMS amendment required
          </label>
          <FieldInput id="sms_amendment_doc_ref" label="SMS Amendment Reference" value={partB.sms_amendment_doc_ref} onChange={(value) => setPartB({ ...partB, sms_amendment_doc_ref: value })} />
          <FieldInput id="master_sign_name" label="Master Signer" value={partB.master_sign_name} onChange={(value) => setPartB({ ...partB, master_sign_name: value })} eid="MOCKUP-OBS-06:obs_partB.master_sign" />
          <FieldInput id="master_sign_at" label="Master Signature Time" type="datetime-local" value={partB.master_sign_at || ''} onChange={(value) => setPartB({ ...partB, master_sign_at: value })} />
          <SaveRow
            pending={updatePart.isPending}
            terminal={closure.state === 'MASTER_CLOSED'}
            onSave={() => savePart('part-b', {
              ...partB,
              target_closure_date: fromInputDate(partB.target_closure_date || ''),
              actual_closure_date: fromInputDate(partB.actual_closure_date || ''),
              master_sign_at: fromInputDateTime(partB.master_sign_at || ''),
            })}
          />
        </SectionCard>

        <SectionCard title="Part C - DPA Review">
          <ReadOnlyNote>Part C records audit-trail review only. It does not gate or reopen the Observation state.</ReadOnlyNote>
          <FieldInput id="acceptance_review_date" label="Review Date" type="date" value={partC.acceptance_review_date || ''} onChange={(value) => setPartC({ ...partC, acceptance_review_date: value })} eid="MOCKUP-OBS-06:obs_partC.dpa_review" />
          <SelectField id="acceptance_decision" label="Decision" value={partC.acceptance_decision} options={OBS_ACCEPTANCE_DECISIONS} onChange={(value) => setPartC({ ...partC, acceptance_decision: value })} />
          <FieldTextarea id="acceptance_adequacy_text" label="Adequacy Review" value={partC.acceptance_adequacy_text} onChange={(value) => setPartC({ ...partC, acceptance_adequacy_text: value })} />
          <FieldTextarea id="acceptance_return_reason" label="Return Reason" value={partC.acceptance_return_reason} onChange={(value) => setPartC({ ...partC, acceptance_return_reason: value })} />
          <FieldInput id="acceptance_signer_name" label="Reviewed By" value={partC.acceptance_signer_name} onChange={(value) => setPartC({ ...partC, acceptance_signer_name: value })} />
          <FieldInput id="acceptance_signer_at" label="Review Time" type="datetime-local" value={partC.acceptance_signer_at || ''} onChange={(value) => setPartC({ ...partC, acceptance_signer_at: value })} />
          <SaveRow pending={updatePart.isPending} onSave={() => savePart('part-c', {
            ...partC,
            acceptance_review_date: fromInputDate(partC.acceptance_review_date || ''),
            acceptance_signer_at: fromInputDateTime(partC.acceptance_signer_at || ''),
          })} />
        </SectionCard>

        <SectionCard title="Part D - Auditor Verification">
          <ReadOnlyNote>Part D is recorded after Master closure and does not change the terminal state.</ReadOnlyNote>
          <FieldInput id="verifying_auditor_name" label="Verifying Auditor" value={partD.verifying_auditor_name} onChange={(value) => setPartD({ ...partD, verifying_auditor_name: value })} eid="MOCKUP-OBS-06:obs_partD.verification" />
          <FieldInput id="verifying_authority_org" label="Authority / Org" value={partD.verifying_authority_org} onChange={(value) => setPartD({ ...partD, verifying_authority_org: value })} />
          <SelectField id="verification_method" label="Verification Method" value={partD.verification_method} options={OBS_VERIFICATION_METHODS} onChange={(value) => setPartD({ ...partD, verification_method: value })} />
          <FieldTextarea id="auditor_remarks_text" label="Auditor Remarks" value={partD.auditor_remarks_text} onChange={(value) => setPartD({ ...partD, auditor_remarks_text: value })} />
          <SelectField id="closure_status" label="Closure Status" value={partD.closure_status} options={OBS_CLOSURE_STATUSES} onChange={(value) => setPartD({ ...partD, closure_status: value })} />
          <FieldInput id="resubmit_by_date" label="Resubmit By" type="date" value={partD.resubmit_by_date || ''} onChange={(value) => setPartD({ ...partD, resubmit_by_date: value })} />
          <FieldInput id="auditor_verification_sign_at" label="Verification Time" type="datetime-local" value={partD.auditor_verification_sign_at || ''} onChange={(value) => setPartD({ ...partD, auditor_verification_sign_at: value })} />
          <SaveRow pending={updatePart.isPending} onSave={() => savePart('part-d', {
            ...partD,
            resubmit_by_date: fromInputDate(partD.resubmit_by_date || ''),
            auditor_verification_sign_at: fromInputDateTime(partD.auditor_verification_sign_at || ''),
          })} />
        </SectionCard>
      </div>
    </RootLayout>
  );
}

function ObsWizardStep({
  stepIndex,
  partB,
  terminal,
  onPartBChange,
}: {
  stepIndex: number;
  partB: AuditObsPartB;
  terminal: boolean;
  onPartBChange: (partB: AuditObsPartB) => void;
}) {
  if (stepIndex === 0) {
    return (
      <PromptCard
        label="Who is answering this Observation, and when will it be closed?"
        hint="Enter the name, rank, and target date agreed on board."
      >
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2" data-eid="MOCKUP-OBS-06:obs_wizard_step1.responder">
            <Label htmlFor="obs_wizard_responded_by_name">Responder Name</Label>
            <Input
              id="obs_wizard_responded_by_name"
              aria-label="Responder name"
              value={partB.responded_by_name}
              disabled={terminal}
              onChange={(event) => onPartBChange({ ...partB, responded_by_name: event.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="obs_wizard_responded_by_rank">Responder Rank</Label>
            <Input
              id="obs_wizard_responded_by_rank"
              aria-label="Responder rank"
              value={partB.responded_by_rank}
              disabled={terminal}
              onChange={(event) => onPartBChange({ ...partB, responded_by_rank: event.target.value })}
            />
          </div>
          <div className="space-y-2 sm:col-span-2" data-eid="MOCKUP-OBS-06:obs_wizard_step1.target_date">
            <Label htmlFor="obs_wizard_target_closure_date">Target Closure Date</Label>
            <Input
              id="obs_wizard_target_closure_date"
              aria-label="Target closure date"
              type="date"
              value={partB.target_closure_date || ''}
              disabled={terminal}
              onChange={(event) => onPartBChange({ ...partB, target_closure_date: event.target.value })}
            />
          </div>
        </div>
      </PromptCard>
    );
  }

  if (stepIndex === 1) {
    return (
      <PromptCard
        label="What did the vessel or department do to close this Observation?"
        hint="Use short facts. Include the immediate action, why it happened, and what prevents repeat."
      >
        <div className="grid gap-3" data-eid="MOCKUP-OBS-06:obs_wizard_step2.fields">
          <WizardTextarea
            label="Immediate action"
            value={partB.immediate_action_text}
            disabled={terminal}
            onChange={(value) => onPartBChange({ ...partB, immediate_action_text: value })}
          />
          <WizardTextarea
            label="Root cause"
            value={partB.root_cause_text}
            disabled={terminal}
            onChange={(value) => onPartBChange({ ...partB, root_cause_text: value })}
          />
          <WizardTextarea
            label="Corrective action"
            value={partB.corrective_action_text}
            disabled={terminal}
            onChange={(value) => onPartBChange({ ...partB, corrective_action_text: value })}
          />
          <WizardTextarea
            label="Preventive action"
            value={partB.preventive_action_text}
            disabled={terminal}
            onChange={(value) => onPartBChange({ ...partB, preventive_action_text: value })}
          />
          <label className="flex items-center gap-2 text-sm text-neutral-700">
            <input
              type="checkbox"
              checked={partB.sms_amendment_required}
              disabled={terminal}
              onChange={(event) => onPartBChange({ ...partB, sms_amendment_required: event.target.checked })}
              className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
            />
            SMS amendment required
          </label>
          {partB.sms_amendment_required && (
            <Input
              aria-label="SMS amendment reference"
              value={partB.sms_amendment_doc_ref}
              disabled={terminal}
              onChange={(event) => onPartBChange({ ...partB, sms_amendment_doc_ref: event.target.value })}
            />
          )}
        </div>
      </PromptCard>
    );
  }

  return (
    <PromptCard
      label="Confirm closure and record the Master signature."
      hint="This signature makes the Observation MASTER_CLOSED. Parts C and D stay audit-trail only."
    >
      <div className="grid gap-3 sm:grid-cols-2" data-eid="MOCKUP-OBS-06:obs_partB.master_sign">
        <div className="space-y-2">
          <Label htmlFor="obs_wizard_actual_closure_date">Closure Date for Signature</Label>
          <Input
            id="obs_wizard_actual_closure_date"
            aria-label="Wizard actual closure date"
            type="date"
            value={partB.actual_closure_date || ''}
            disabled={terminal}
            onChange={(event) => onPartBChange({ ...partB, actual_closure_date: event.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="obs_wizard_master_sign_name">Master Signer for Closure</Label>
          <Input
            id="obs_wizard_master_sign_name"
            aria-label="Wizard master signer"
            value={partB.master_sign_name}
            disabled={terminal}
            onChange={(event) => onPartBChange({ ...partB, master_sign_name: event.target.value })}
          />
        </div>
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="obs_wizard_master_sign_at">Signature Time</Label>
          <Input
            id="obs_wizard_master_sign_at"
            aria-label="Wizard master signature time"
            type="datetime-local"
            value={partB.master_sign_at || ''}
            disabled={terminal}
            onChange={(event) => onPartBChange({ ...partB, master_sign_at: event.target.value })}
          />
        </div>
      </div>
    </PromptCard>
  );
}

function PromptCard({ label, hint, children }: { label: string; hint: string; children: ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{label}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-neutral-500">{hint}</p>
        {children}
      </CardContent>
    </Card>
  );
}

function WizardTextarea({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  const id = `obs_wizard_${label.toLowerCase().replace(/\s+/g, '_')}`;
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Textarea
        id={id}
        aria-label={label}
        value={value}
        disabled={disabled}
        rows={4}
        onChange={(event) => onChange(event.target.value)}
      />
      <p className={cn('text-xs', value.length >= 20 ? 'text-success-700' : 'text-neutral-500')}>
        {value.length} characters
      </p>
    </div>
  );
}

function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-2">{children}</CardContent>
    </Card>
  );
}

function SaveRow({ onSave, pending, terminal = false }: { onSave: () => void; pending: boolean; terminal?: boolean }) {
  return (
    <div className="flex justify-end lg:col-span-2">
      <Button onClick={onSave} disabled={pending || terminal}>
        {pending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : terminal ? <FileSignature className="mr-2 h-4 w-4" /> : <Save className="mr-2 h-4 w-4" />}
        {terminal ? 'Master Closed' : 'Save Section'}
      </Button>
    </div>
  );
}

function HeaderDatum({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase text-neutral-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-neutral-800">{value || '-'}</p>
    </div>
  );
}

function ContextRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase text-neutral-500">{label}</p>
      <p className="mt-1 whitespace-pre-wrap text-neutral-800">{value}</p>
    </div>
  );
}

function ReadOnlyDatum({ label, value, eid }: { label: string; value: string; eid?: string }) {
  return (
    <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3" data-eid={eid}>
      <p className="text-xs font-medium uppercase text-neutral-500">{label}</p>
      <p className="mt-1 whitespace-pre-wrap text-sm text-neutral-800">{value}</p>
    </div>
  );
}

function ReadOnlyNote({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-md border border-primary-100 bg-primary-50 p-3 text-sm text-neutral-600 lg:col-span-2">
      {children}
    </p>
  );
}

function FieldInput({
  id,
  label,
  value,
  onChange,
  type = 'text',
  eid,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  eid?: string;
}) {
  return (
    <div className="space-y-2" data-eid={eid}>
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function FieldTextarea({
  id,
  label,
  value,
  onChange,
  eid,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  eid?: string;
}) {
  return (
    <div className="space-y-2" data-eid={eid}>
      <Label htmlFor={id}>{label}</Label>
      <Textarea id={id} value={value} onChange={(event) => onChange(event.target.value)} rows={4} />
    </div>
  );
}

function SelectField<T extends readonly string[]>({
  id,
  label,
  value,
  options,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: T;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        value={value || ''}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
      >
        <option value="">Not set</option>
        {options.map((option) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
    </div>
  );
}
