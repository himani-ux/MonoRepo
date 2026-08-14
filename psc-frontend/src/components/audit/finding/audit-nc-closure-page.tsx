import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { ArrowLeft, FileSignature, Loader2, Save, Send } from 'lucide-react';
import { Button, Badge, Card, CardContent, CardHeader, CardTitle, Input, Label, Textarea } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import {
  useAuditFindingCarWorkflow,
  useAuditNcClosure,
  useDraftAuditNcForVessel,
  useUpdateAuditNcPart,
} from '@/hooks/audit/use-audit-finding';
import { getErrorMessage } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import {
  ACCEPTANCE_DECISIONS,
  CERTIFICATE_ENDORSEMENT_TYPES,
  CERTIFICATES_AT_RISK,
  EFFECTIVENESS_OUTCOMES,
  EFFECTIVENESS_REVIEW_METHODS,
  FINAL_CLOSURE_STATUSES,
  RCA_METHODS,
  ROOT_CAUSE_CATEGORIES,
  VERIFICATION_METHODS,
  type AuditNcPartB,
  type AuditNcPartC,
  type AuditNcPartD,
  type AuditNcPartE,
  type AuditNcPartF,
  type AuditNcPartG,
  type AuditNcPartName,
  type AuditNcPartPayload,
  type AuditNcWorkflowAction,
} from '@/schemas/audit/nc-closure';

interface AuditNcClosurePageProps {
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

function splitCsv(value: string | null | undefined): string[] {
  return (value || '').split(',').map((item) => item.trim()).filter(Boolean);
}

export function AuditNcClosurePage({ findingId }: AuditNcClosurePageProps) {
  const { toast } = useToast();
  const { data: closure, isLoading, error, refetch } = useAuditNcClosure(findingId);
  const updatePart = useUpdateAuditNcPart(findingId);
  const draftForVessel = useDraftAuditNcForVessel(findingId);
  const carWorkflow = useAuditFindingCarWorkflow(findingId);
  const [partB, setPartB] = useState<AuditNcPartB | null>(null);
  const [partC, setPartC] = useState<AuditNcPartC | null>(null);
  const [partD, setPartD] = useState<AuditNcPartD | null>(null);
  const [partE, setPartE] = useState<AuditNcPartE | null>(null);
  const [partF, setPartF] = useState<AuditNcPartF | null>(null);
  const [partG, setPartG] = useState<AuditNcPartG | null>(null);

  useEffect(() => {
    if (!closure) return;
    const certificates = splitCsv(closure.part_a.certificates_at_risk);
    setPartB({
      ...closure.part_b,
      immediate_action_completed_at: toInputDate(closure.part_b.immediate_action_completed_at),
      master_immediate_sign_at: toInputDateTime(closure.part_b.master_immediate_sign_at),
    });
    setPartC(closure.part_c);
    setPartD({
      ...closure.part_d,
      target_completion_date: toInputDate(closure.part_d.target_completion_date),
      actual_completion_date: toInputDate(closure.part_d.actual_completion_date),
    });
    setPartE({
      ...closure.part_e,
      certificates_at_risk: certificates,
      effectiveness_review_date: toInputDate(closure.part_e.effectiveness_review_date),
      effectiveness_signer_at: toInputDateTime(closure.part_e.effectiveness_signer_at),
    });
    setPartF({
      ...closure.part_f,
      certificates_at_risk: certificates,
      acceptance_review_date: toInputDate(closure.part_f.acceptance_review_date),
      acceptance_signer_at: toInputDateTime(closure.part_f.acceptance_signer_at),
    });
    setPartG({
      ...closure.part_g,
      resubmit_by_date: toInputDate(closure.part_g.resubmit_by_date),
      auditor_verification_sign_at: toInputDateTime(closure.part_g.auditor_verification_sign_at),
    });
  }, [closure]);

  const summaryLength = partC?.root_cause_summary.length || 0;

  const savePart = async (part: AuditNcPartName, data: AuditNcPartPayload) => {
    try {
      await updatePart.mutateAsync({ part, data });
      toast({ title: `NC ${part.toUpperCase()} saved` });
    } catch (saveError) {
      toast({
        variant: 'destructive',
        title: `NC ${part.toUpperCase()} not saved`,
        description: getErrorMessage(saveError),
      });
    }
  };

  const draftCurrentPartBAndC = async () => {
    if (!partB || !partC) return;
    try {
      await draftForVessel.mutateAsync({
        ...partB,
        ...partC,
        immediate_action_completed_at: fromInputDate(partB.immediate_action_completed_at || ''),
        master_immediate_sign_at: fromInputDateTime(partB.master_immediate_sign_at || ''),
        comment: 'Office drafted KSM-F-NC-001 Parts B/C for vessel review.',
      });
      toast({ title: 'NC drafted for vessel review' });
    } catch (draftError) {
      toast({
        variant: 'destructive',
        title: 'NC draft not saved',
        description: getErrorMessage(draftError),
      });
    }
  };

  const runWorkflowAction = async (action: AuditNcWorkflowAction, comment?: string) => {
    try {
      await carWorkflow.mutateAsync({ action, comment });
      toast({ title: `CAR ${action.replaceAll('_', ' ').toLowerCase()} complete` });
    } catch (workflowError) {
      toast({
        variant: 'destructive',
        title: 'CAR transition blocked',
        description: getErrorMessage(workflowError),
      });
    }
  };

  if (error || (!isLoading && !closure)) {
    return (
      <RootLayout>
        <PageHeader title="NC Closure" showBack backTo="/audit" />
        <ErrorState
          title="NC closure not found"
          message="The finding may not be an NC, or you may not have access."
          onRetry={() => refetch()}
        />
      </RootLayout>
    );
  }

  if (isLoading || !closure || !partB || !partC || !partD || !partE || !partF || !partG) {
    return (
      <RootLayout>
        <PageHeader title="NC Closure" showBack backTo="/audit" />
        <div className="space-y-4 p-4">
          <SectionSkeleton />
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <PageHeader
        title="NC Closure"
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
                <h1 className="text-xl font-semibold text-neutral-900" data-eid="MOCKUP-NC-04:nc_partA.ref_no">
                  {closure.part_a.nc_reference_no}
                </h1>
                <Badge variant={closure.part_a.nc_classification === 'MAJOR_NC' ? 'destructive' : 'warning'}>
                  {closure.part_a.nc_classification || 'NC'}
                </Badge>
                <Badge variant="secondary">{closure.car.status}</Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">{closure.part_a.description}</p>
            </div>
            <HeaderDatum label="Vessel / Port" value={`${closure.part_a.vessel_id} / ${closure.part_a.port_place}`} eid="MOCKUP-NC-04:nc_partA.audit_meta" />
            <HeaderDatum label="Deadline" value={closure.part_a.required_closure_deadline || '-'} eid="MOCKUP-NC-04:nc_partA.due_date" />
            <HeaderDatum label="Certificates" value={closure.part_a.certificates_at_risk || 'NONE'} eid="MOCKUP-NC-04:nc_partA.cert_at_risk" />
          </CardContent>
        </Card>

        <Card data-eid="MOCKUP-NC-04:nc_partA.objective_evidence">
          <CardHeader>
            <CardTitle>Part A - Auditor Issuance</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 lg:grid-cols-2">
            <ReadOnlyDatum label="Auditor" value={`${closure.part_a.auditor_name} / ${closure.part_a.auditor_organisation}`} eid="MOCKUP-NC-04:nc_partA.auditor" />
            <ReadOnlyDatum label="Clause" value={closure.part_a.clause_ref_text || closure.part_a.rule_book_type || '-'} eid="MOCKUP-NC-04:nc_partA.clause_ref" />
            <ReadOnlyDatum label="Issued Date" value={closure.part_a.nc_issued_date || '-'} eid="MOCKUP-NC-04:nc_partA.issued_date" />
            <ReadOnlyDatum label="Objective Evidence" value={closure.part_a.objective_evidence || '-'} eid="MOCKUP-NC-04:nc_partA.objective_evidence" />
          </CardContent>
        </Card>

        <WorkflowActionPanel
          status={closure.car.status}
          effRevDate={partE.effectiveness_review_date}
          effRevOverdue={partE.effectiveness_overdue}
          pending={draftForVessel.isPending || carWorkflow.isPending}
          onDraftForVessel={draftCurrentPartBAndC}
          onWorkflowAction={runWorkflowAction}
        />

        <SectionCard title="Part B - Immediate / Containment Action">
          <FieldTextarea
            id="immediate_action_text"
            label="Immediate Action"
            value={partB.immediate_action_text}
            onChange={(value) => setPartB({ ...partB, immediate_action_text: value })}
            eid="MOCKUP-NC-WIZ-05:nc_wizard_step1.immediate_action"
          />
          <FieldInput
            id="immediate_action_completed_at"
            label="Date Completed"
            type="date"
            value={partB.immediate_action_completed_at || ''}
            onChange={(value) => setPartB({ ...partB, immediate_action_completed_at: value })}
            eid="MOCKUP-NC-WIZ-05:nc_wizard_step1.completed_at"
          />
          <FieldInput
            id="master_immediate_sign_name"
            label="Master / HoD Signer"
            value={partB.master_immediate_sign_name}
            onChange={(value) => setPartB({ ...partB, master_immediate_sign_name: value })}
            eid="MOCKUP-NC-04:nc_partB.master_sign"
          />
          <FieldInput
            id="master_immediate_sign_at"
            label="Signature Time"
            type="datetime-local"
            value={partB.master_immediate_sign_at || ''}
            onChange={(value) => setPartB({ ...partB, master_immediate_sign_at: value })}
            eid="MOCKUP-NC-04:nc_partB.master_sign"
          />
          {partB.drafted_by_user_id && (
            <p className="rounded-md border border-primary-100 bg-primary-50 p-3 text-sm text-neutral-600" data-eid="MOCKUP-NC-04:nc_partB.drafter_footer">
              Drafted by office: {partB.drafted_by_user_id}
            </p>
          )}
          <SaveRow onSave={() => savePart('part-b', {
            ...partB,
            immediate_action_completed_at: fromInputDate(partB.immediate_action_completed_at || ''),
            master_immediate_sign_at: fromInputDateTime(partB.master_immediate_sign_at || ''),
          })} pending={updatePart.isPending} />
        </SectionCard>

        <SectionCard title="Part C - Root Cause Analysis">
          <SelectField
            id="rca_method"
            label="RCA Method"
            value={partC.rca_method}
            options={RCA_METHODS}
            onChange={(value) => setPartC({ ...partC, rca_method: value })}
            eid="MOCKUP-NC-WIZ-05:nc_wizard_step2.rca_method"
          />
          <FieldInput id="rca_method_other" label="RCA Method Other" value={partC.rca_method_other} onChange={(value) => setPartC({ ...partC, rca_method_other: value })} />
          <FieldTextarea id="problem_statement" label="Problem Statement" value={partC.problem_statement} onChange={(value) => setPartC({ ...partC, problem_statement: value })} />
          <FieldTextarea id="why_1" label="Why 1" value={partC.why_1} onChange={(value) => setPartC({ ...partC, why_1: value })} eid="MOCKUP-NC-WIZ-05:nc_wizard_step3.why_inputs" />
          <FieldTextarea id="why_2" label="Why 2" value={partC.why_2} onChange={(value) => setPartC({ ...partC, why_2: value })} />
          <FieldTextarea id="why_3" label="Why 3" value={partC.why_3} onChange={(value) => setPartC({ ...partC, why_3: value })} />
          <CheckboxGroup
            label="Root Cause Categories"
            values={partC.root_cause_categories}
            options={ROOT_CAUSE_CATEGORIES}
            onChange={(values) => setPartC({ ...partC, root_cause_categories: values })}
            eid="MOCKUP-NC-WIZ-05:nc_wizard_step3.rc_categories"
          />
          <FieldTextarea
            id="root_cause_summary"
            label="Root Cause Summary"
            value={partC.root_cause_summary}
            onChange={(value) => setPartC({ ...partC, root_cause_summary: value })}
            eid="MOCKUP-NC-WIZ-05:nc_wizard_step3.rca_input"
          />
          <p className={cn('text-xs', summaryLength >= 50 ? 'text-success-700' : 'text-neutral-500')}>
            {summaryLength}/50 characters
          </p>
          <SaveRow onSave={() => savePart('part-c', partC)} pending={updatePart.isPending} />
        </SectionCard>

        <SectionCard title="Part D - Corrective / Preventive Action">
          <FieldTextarea id="corrective_action_text" label="Corrective Action" value={partD.corrective_action_text} onChange={(value) => setPartD({ ...partD, corrective_action_text: value })} eid="MOCKUP-NC-04:nc_partD.corrective_action" />
          <FieldTextarea id="preventive_action_text" label="Preventive Action" value={partD.preventive_action_text} onChange={(value) => setPartD({ ...partD, preventive_action_text: value })} eid="MOCKUP-NC-04:nc_partD.preventive_action" />
          <FieldInput id="target_completion_date" label="Target Completion Date" type="date" value={partD.target_completion_date || ''} onChange={(value) => setPartD({ ...partD, target_completion_date: value })} eid="MOCKUP-NC-04:nc_partD.dates" />
          <FieldInput id="actual_completion_date" label="Actual Completion Date" type="date" value={partD.actual_completion_date || ''} onChange={(value) => setPartD({ ...partD, actual_completion_date: value })} eid="MOCKUP-NC-04:nc_partD.dates" />
          <label className="flex items-center gap-2 text-sm text-neutral-700" data-eid="MOCKUP-NC-04:nc_partD.sms_amendment">
            <input
              type="checkbox"
              checked={partD.sms_amendment_required}
              onChange={(event) => setPartD({ ...partD, sms_amendment_required: event.target.checked })}
              className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
            />
            SMS amendment required
          </label>
          <FieldInput id="sms_amendment_doc_ref" label="SMS Amendment Reference" value={partD.sms_amendment_doc_ref} onChange={(value) => setPartD({ ...partD, sms_amendment_doc_ref: value })} />
          <SaveRow onSave={() => savePart('part-d', {
            ...partD,
            target_completion_date: fromInputDate(partD.target_completion_date || ''),
            actual_completion_date: fromInputDate(partD.actual_completion_date || ''),
          })} pending={updatePart.isPending} />
        </SectionCard>

        <SectionCard title="Part E - Effectiveness Review">
          <CheckboxGroup label="Certificates at Risk" values={partE.certificates_at_risk || []} options={CERTIFICATES_AT_RISK} onChange={(values) => setPartE({ ...partE, certificates_at_risk: values })} />
          <FieldInput id="effectiveness_review_date" label="Review Date" type="date" value={partE.effectiveness_review_date || ''} onChange={(value) => setPartE({ ...partE, effectiveness_review_date: value })} eid="MOCKUP-NC-04:nc_partE.effrev" />
          <SelectField id="effectiveness_review_method" label="Review Method" value={partE.effectiveness_review_method} options={EFFECTIVENESS_REVIEW_METHODS} onChange={(value) => setPartE({ ...partE, effectiveness_review_method: value })} />
          <SelectField id="effectiveness_outcome" label="Outcome" value={partE.effectiveness_outcome} options={EFFECTIVENESS_OUTCOMES} onChange={(value) => setPartE({ ...partE, effectiveness_outcome: value })} />
          <FieldTextarea id="effectiveness_assessment_text" label="Assessment" value={partE.effectiveness_assessment_text} onChange={(value) => setPartE({ ...partE, effectiveness_assessment_text: value })} />
          <FieldTextarea id="effectiveness_further_action_text" label="Further Action" value={partE.effectiveness_further_action_text} onChange={(value) => setPartE({ ...partE, effectiveness_further_action_text: value })} eid="MOCKUP-NC-04:nc_partE.further_action" />
          <FieldInput id="effectiveness_signer_name" label="Signer" value={partE.effectiveness_signer_name} onChange={(value) => setPartE({ ...partE, effectiveness_signer_name: value })} eid="MOCKUP-NC-04:nc_partE.signer" />
          <FieldInput id="effectiveness_signer_at" label="Signer Time" type="datetime-local" value={partE.effectiveness_signer_at || ''} onChange={(value) => setPartE({ ...partE, effectiveness_signer_at: value })} />
          <SaveRow onSave={() => savePart('part-e', {
            ...partE,
            effectiveness_review_date: fromInputDate(partE.effectiveness_review_date || ''),
            effectiveness_signer_at: fromInputDateTime(partE.effectiveness_signer_at || ''),
          })} pending={updatePart.isPending} />
        </SectionCard>

        <SectionCard title="Part F - Closure Acceptance">
          <CheckboxGroup label="Certificates at Risk" values={partF.certificates_at_risk || []} options={CERTIFICATES_AT_RISK} onChange={(values) => setPartF({ ...partF, certificates_at_risk: values })} />
          <FieldInput id="acceptance_review_date" label="Review Date" type="date" value={partF.acceptance_review_date || ''} onChange={(value) => setPartF({ ...partF, acceptance_review_date: value })} eid="MOCKUP-NC-04:nc_partF.acceptance" />
          <SelectField id="acceptance_decision" label="Decision" value={partF.acceptance_decision} options={ACCEPTANCE_DECISIONS} onChange={(value) => setPartF({ ...partF, acceptance_decision: value })} />
          <FieldTextarea id="acceptance_rca_adequacy_text" label="RCA Adequacy" value={partF.acceptance_rca_adequacy_text} onChange={(value) => setPartF({ ...partF, acceptance_rca_adequacy_text: value })} />
          <FieldTextarea id="acceptance_return_reason" label="Return Reason" value={partF.acceptance_return_reason} onChange={(value) => setPartF({ ...partF, acceptance_return_reason: value })} />
          <FieldInput id="acceptance_signer_name" label="Reviewed By" value={partF.acceptance_signer_name} onChange={(value) => setPartF({ ...partF, acceptance_signer_name: value })} />
          <FieldInput id="acceptance_signer_at" label="Signer Time" type="datetime-local" value={partF.acceptance_signer_at || ''} onChange={(value) => setPartF({ ...partF, acceptance_signer_at: value })} />
          <SaveRow onSave={() => savePart('part-f', {
            ...partF,
            acceptance_review_date: fromInputDate(partF.acceptance_review_date || ''),
            acceptance_signer_at: fromInputDateTime(partF.acceptance_signer_at || ''),
          })} pending={updatePart.isPending} />
        </SectionCard>

        <SectionCard title="Part G - Auditor Verification">
          <FieldInput id="verifying_auditor_name" label="Verifying Auditor" value={partG.verifying_auditor_name} onChange={(value) => setPartG({ ...partG, verifying_auditor_name: value })} eid="MOCKUP-NC-04:nc_partG.verification" />
          <FieldInput id="verifying_authority_org" label="Authority / Org" value={partG.verifying_authority_org} onChange={(value) => setPartG({ ...partG, verifying_authority_org: value })} />
          <SelectField id="verification_method" label="Verification Method" value={partG.verification_method} options={VERIFICATION_METHODS} onChange={(value) => setPartG({ ...partG, verification_method: value })} />
          <SelectField id="certificate_endorsement_type" label="Certificate Endorsement" value={partG.certificate_endorsement_type} options={CERTIFICATE_ENDORSEMENT_TYPES} onChange={(value) => setPartG({ ...partG, certificate_endorsement_type: value })} eid="MOCKUP-NC-04:nc_partG.cert_endorsement" />
          <FieldInput id="certificate_endorsement_ref" label="Endorsement Reference" value={partG.certificate_endorsement_ref} onChange={(value) => setPartG({ ...partG, certificate_endorsement_ref: value })} />
          <FieldTextarea id="auditor_assessment_text" label="Auditor Assessment" value={partG.auditor_assessment_text} onChange={(value) => setPartG({ ...partG, auditor_assessment_text: value })} />
          <SelectField id="final_closure_status" label="Final Closure Status" value={partG.final_closure_status} options={FINAL_CLOSURE_STATUSES} onChange={(value) => setPartG({ ...partG, final_closure_status: value })} eid="MOCKUP-NC-04:nc_partG.closure_status" />
          <FieldInput id="resubmit_by_date" label="Resubmit By" type="date" value={partG.resubmit_by_date || ''} onChange={(value) => setPartG({ ...partG, resubmit_by_date: value })} />
          <SaveRow onSave={() => savePart('part-g', {
            ...partG,
            resubmit_by_date: fromInputDate(partG.resubmit_by_date || ''),
            auditor_verification_sign_at: fromInputDateTime(partG.auditor_verification_sign_at || ''),
          })} pending={updatePart.isPending} />
        </SectionCard>
      </div>
    </RootLayout>
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

function SaveRow({ onSave, pending }: { onSave: () => void; pending: boolean }) {
  return (
    <div className="flex justify-end lg:col-span-2">
      <Button onClick={onSave} disabled={pending}>
        {pending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
        Save Section
      </Button>
    </div>
  );
}

function WorkflowActionPanel({
  status,
  effRevDate,
  effRevOverdue,
  pending,
  onDraftForVessel,
  onWorkflowAction,
}: {
  status: string;
  effRevDate: string | null;
  effRevOverdue: boolean;
  pending: boolean;
  onDraftForVessel: () => void;
  onWorkflowAction: (action: AuditNcWorkflowAction, comment?: string) => void;
}) {
  const canDraft = status === 'ALLOTTED' || status === 'IN_PROGRESS';
  const canSubmitToPic = status === 'IN_PROGRESS' || status === 'OFFICE_DRAFTED';
  const canStartPic = status === 'SUBMITTED_TO_PIC';
  const canSubmitLead = status === 'PIC_REVIEW';
  const canLeadClose = status === 'SUBMITTED_TO_LEAD_AUDITOR';

  return (
    <Card>
      <CardHeader>
        <CardTitle>Workflow Actions</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap items-center gap-2 text-sm text-neutral-600">
          <Badge variant="secondary">{status}</Badge>
          {effRevDate && (
            <Badge variant={effRevOverdue ? 'destructive' : 'outline'}>
              EffRev due {effRevDate}
            </Badge>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {canDraft && (
            <Button variant="outline" onClick={onDraftForVessel} disabled={pending}>
              {pending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileSignature className="mr-2 h-4 w-4" />}
              Draft for Vessel
            </Button>
          )}
          {canSubmitToPic && (
            <Button
              variant="outline"
              onClick={() => onWorkflowAction('SUBMIT_TO_PIC')}
              disabled={pending}
            >
              <Send className="mr-2 h-4 w-4" />
              Submit to PIC
            </Button>
          )}
          {canStartPic && (
            <Button
              variant="outline"
              onClick={() => onWorkflowAction('START_PIC_REVIEW', 'PIC review started.')}
              disabled={pending}
            >
              <Send className="mr-2 h-4 w-4" />
              Start PIC Review
            </Button>
          )}
          {canSubmitLead && (
            <Button
              variant="outline"
              onClick={() => onWorkflowAction('SUBMIT_TO_LEAD_AUDITOR', 'PIC review accepted for Lead Auditor closure.')}
              disabled={pending}
            >
              <Send className="mr-2 h-4 w-4" />
              Submit to Lead Auditor
            </Button>
          )}
          {canLeadClose && (
            <Button
              onClick={() => onWorkflowAction('LEAD_AUDITOR_CLOSE', 'Part F accepted by Lead Auditor.')}
              disabled={pending}
            >
              <FileSignature className="mr-2 h-4 w-4" />
              Lead Auditor Close
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function HeaderDatum({ label, value, eid }: { label: string; value: string; eid?: string }) {
  return (
    <div data-eid={eid}>
      <p className="text-xs font-medium uppercase text-neutral-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-neutral-800">{value || '-'}</p>
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
  eid,
}: {
  id: string;
  label: string;
  value: string;
  options: T;
  onChange: (value: string) => void;
  eid?: string;
}) {
  return (
    <div className="space-y-2" data-eid={eid}>
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

function CheckboxGroup<T extends readonly string[]>({
  label,
  values,
  options,
  onChange,
  eid,
}: {
  label: string;
  values: string[];
  options: T;
  onChange: (values: string[]) => void;
  eid?: string;
}) {
  const selected = useMemo(() => new Set(values), [values]);
  return (
    <fieldset className="space-y-2 rounded-md border border-neutral-200 p-3" data-eid={eid}>
      <legend className="px-1 text-sm font-medium text-neutral-700">{label}</legend>
      <div className="grid gap-2 sm:grid-cols-2">
        {options.map((option) => (
          <label key={option} className="flex items-center gap-2 text-sm text-neutral-700">
            <input
              type="checkbox"
              checked={selected.has(option)}
              onChange={(event) => {
                if (event.target.checked) {
                  onChange([...values, option]);
                } else {
                  onChange(values.filter((value) => value !== option));
                }
              }}
              className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
            />
            {option}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
