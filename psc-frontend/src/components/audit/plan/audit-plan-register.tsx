import { useEffect, useMemo, useState } from 'react';
import { Ban, Bell, CheckCircle2, ChevronDown, Edit2, FilePlus2, Filter, Loader2, Plus, Save } from 'lucide-react';
import { Button, Badge, Card, CardContent, CardHeader, CardTitle, Input, Label, Textarea } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import { getErrorMessage } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { reloadAuditPlanRegisterPage } from '@/lib/audit/reload';
import { formatDisplayDate } from '@/lib/utils/format-date';
import { formatEnumLabel, getStatusLabel } from '@/lib/utils/format-status';
import {
  AUDIT_PLAN_WRITABLE_STATUSES,
  auditPlanFormFromPlan,
  emptyAuditPlanAdditional,
  emptyAuditPlanCancel,
  emptyAuditPlanExtensionDecision,
  emptyAuditPlanExtensionRequest,
  emptyAuditPlanFlagNotification,
  emptyAuditPlanForm,
  type AuditPlan,
  type AuditPlanAdditionalData,
  type AuditPlanCancelData,
  type AuditPlanExtensionDecisionData,
  type AuditPlanExtensionRequestData,
  type AuditPlanFlagNotificationData,
  type AuditPlanFormData,
} from '@/schemas/audit/plan';
import {
  useAuditPlans,
  useCancelAuditPlan,
  useCreateAdditionalAuditPlan,
  useCreateAuditPlan,
  useAuditQualifiedAuditors,
  useDecideAuditPlanExtension,
  useRecordAuditPlanFlagNotification,
  useRequestAuditPlanExtension,
  useUpdateAuditPlan,
} from '@/hooks/audit/use-audit-plan';
import { useAuditVessels } from '@/hooks/audit/use-audit-registration';
import type { AuditVesselOption } from '@/lib/api/audit';
import type { AuditQualifiedAuditor } from '@/lib/api/audit';

const officeDepartments = ['', 'CREW', 'TECH', 'PURCHASE', 'IT', 'MARINE', 'SEQ', 'OTHER'] as const;
const auditStandardOptions = ['ISM', 'ISPS', 'MLC', 'EMS'] as const;
const triggerTypes = ['PSC_INSPECTION', 'DETENTION_NOTICE', 'FLAG_LETTER', 'INCIDENT_REPORT', 'MGMT_DIRECTIVE', 'OTHER'] as const;
type AuditStandardOption = (typeof auditStandardOptions)[number];
type WorkflowMode = 'extension' | 'decision' | 'flag' | 'cancel' | null;

function statusVariant(status: string) {
  const normalized = String(status || '').toUpperCase();
  if (normalized === 'COMPLETED') return 'success';
  if (normalized === 'IN_PROGRESS' || normalized === 'OVERDUE' || normalized === 'EXTENDED' || normalized === 'EXTENSION_REQUESTED') return 'warning';
  if (normalized === 'CRITICAL_OVERDUE' || normalized === 'CANCELLED') return 'destructive';
  return 'secondary';
}

function formatOpmF713(plan: AuditPlan): string {
  const reference = plan.extension_form_ref || '';
  const extendedTo = formatDisplayDate(plan.extended_due_date);

  if (reference && extendedTo) {
    return `${reference} | Extended to ${extendedTo}`;
  }
  if (reference) {
    return reference;
  }
  if (extendedTo) {
    return `Extended to ${extendedTo}`;
  }
  return '-';
}

export function AuditPlanRegister() {
  const { hasProcess } = useAuth();
  const { toast } = useToast();
  const [showAdditionalOnly, setShowAdditionalOnly] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<AuditPlan | null>(null);
  const [workflowPlan, setWorkflowPlan] = useState<AuditPlan | null>(null);
  const [workflowMode, setWorkflowMode] = useState<WorkflowMode>(null);
  const [form, setForm] = useState<AuditPlanFormData>(emptyAuditPlanForm);
  const [extensionForm, setExtensionForm] = useState<AuditPlanExtensionRequestData>(emptyAuditPlanExtensionRequest);
  const [decisionForm, setDecisionForm] = useState<AuditPlanExtensionDecisionData>(emptyAuditPlanExtensionDecision);
  const [flagForm, setFlagForm] = useState<AuditPlanFlagNotificationData>(emptyAuditPlanFlagNotification);
  const [cancelForm, setCancelForm] = useState<AuditPlanCancelData>(emptyAuditPlanCancel);
  const [additionalForm, setAdditionalForm] = useState<AuditPlanAdditionalData>(emptyAuditPlanAdditional);
  const { data, isLoading, error, refetch } = useAuditPlans(showAdditionalOnly ? true : undefined);
  const createPlan = useCreateAuditPlan();
  const updatePlan = useUpdateAuditPlan(selectedPlan?.id);
  const requestExtension = useRequestAuditPlanExtension(workflowPlan?.id);
  const decideExtension = useDecideAuditPlanExtension(workflowPlan?.id);
  const recordFlag = useRecordAuditPlanFlagNotification(workflowPlan?.id);
  const cancelPlan = useCancelAuditPlan(workflowPlan?.id);
  const createAdditional = useCreateAdditionalAuditPlan();
  const vesselQuery = useAuditVessels();
  const canCreatePlan = hasProcess(PROCESS_IDS.AUDIT_CREATE);
  const canEditPlan = hasProcess(PROCESS_IDS.AUDIT_CREATE) || hasProcess(PROCESS_IDS.AUDIT_EDIT);
  const canApproveExtension = hasProcess(PROCESS_IDS.AUDIT_APPROVE_EXTENSION);
  const canCancelPlan = hasProcess(PROCESS_IDS.AUDIT_CANCEL_PLAN);

  useEffect(() => {
    if (!selectedPlan) {
      setForm(emptyAuditPlanForm);
      return;
    }
    setForm(auditPlanFormFromPlan(selectedPlan));
  }, [selectedPlan]);

  const additionalCount = useMemo(
    () => data?.results.filter((plan) => plan.is_additional).length ?? 0,
    [data]
  );

  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Audit Plan Register" />
        <div className="space-y-4 p-4">
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  if (error || !data) {
    return (
      <RootLayout>
        <PageHeader title="Audit Plan Register" />
        <ErrorState
          title="Audit plan register not available"
          message="The plan register may be unavailable or you may not have access."
          onRetry={() => refetch()}
        />
      </RootLayout>
    );
  }

  const setField = (fieldName: keyof AuditPlanFormData, value: string) => {
    setForm((current) => setTargetExclusive(current, fieldName, value));
  };

  const setAdditionalField = (fieldName: keyof AuditPlanAdditionalData, value: string) => {
    setAdditionalForm((current) => setTargetExclusive(current, fieldName, value));
  };

  const openWorkflow = (plan: AuditPlan, mode: WorkflowMode) => {
    setWorkflowPlan(plan);
    setWorkflowMode(mode);
    setExtensionForm(emptyAuditPlanExtensionRequest);
    setDecisionForm(emptyAuditPlanExtensionDecision);
    setFlagForm(emptyAuditPlanFlagNotification);
    setCancelForm(emptyAuditPlanCancel);
  };

  const savePlan = async () => {
    try {
      if (selectedPlan) {
        await updatePlan.mutateAsync(form);
        toast({ title: 'Audit plan updated' });
      } else {
        await createPlan.mutateAsync(form);
        toast({ title: 'Audit plan created' });
      }
      setSelectedPlan(null);
      setForm(emptyAuditPlanForm);
      reloadAuditPlanRegisterPage();
    } catch (saveError) {
      toast({
        variant: 'destructive',
        title: selectedPlan ? 'Audit plan not updated' : 'Audit plan not created',
        description: getErrorMessage(saveError),
      });
    }
  };

  const submitWorkflow = async () => {
    if (!workflowPlan || !workflowMode) return;
    try {
      if (workflowMode === 'extension') {
        await requestExtension.mutateAsync(extensionForm);
        toast({ title: 'Extension requested' });
      } else if (workflowMode === 'decision') {
        await decideExtension.mutateAsync(decisionForm);
        toast({ title: decisionForm.decision === 'APPROVE' ? 'Extension approved' : 'Extension rejected' });
      } else if (workflowMode === 'flag') {
        await recordFlag.mutateAsync(flagForm);
        toast({ title: 'Flag notification recorded' });
      } else if (workflowMode === 'cancel') {
        await cancelPlan.mutateAsync(cancelForm);
        toast({ title: 'Audit plan cancelled' });
      }
      setWorkflowPlan(null);
      setWorkflowMode(null);
    } catch (workflowError) {
      toast({
        variant: 'destructive',
        title: 'Plan workflow not saved',
        description: getErrorMessage(workflowError),
      });
    }
  };

  const saveAdditionalPlan = async () => {
    try {
      await createAdditional.mutateAsync(additionalForm);
      toast({ title: 'Additional audit created' });
      setAdditionalForm(emptyAuditPlanAdditional);
    } catch (saveError) {
      toast({
        variant: 'destructive',
        title: 'Additional audit not created',
        description: getErrorMessage(saveError),
      });
    }
  };

  return (
    <RootLayout>
      <PageHeader title="Audit Plan Register" />
      <div className="space-y-4 p-4">
        <Card>
          <CardContent className="grid gap-3 p-4 sm:grid-cols-3">
            <RegisterMetric label="Register rows" value={data.count} />
            <RegisterMetric label="Additional audits" value={additionalCount} />
            <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3">
              <p className="text-xs font-medium uppercase text-neutral-500">Filter</p>
              <Button
                type="button"
                variant={showAdditionalOnly ? 'default' : 'outline'}
                size="sm"
                className="mt-2"
                onClick={() => setShowAdditionalOnly((current) => !current)}
              >
                <Filter className="mr-2 h-4 w-4" />
                {showAdditionalOnly ? 'Showing additional' : 'All routine + additional'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Planned & in-flight audits</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-lg border border-neutral-200">
              <table className="min-w-full divide-y divide-neutral-200 text-sm">
                <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                  <tr>
                    <th className="px-3 py-2">Target</th>
                    <th className="px-3 py-2">Standards</th>
                    <th className="px-3 py-2" data-eid="MOCKUP-PLAN-07:plan_register.window">Window</th>
                    <th className="px-3 py-2">OPM F 713</th>
                    <th className="px-3 py-2" data-eid="MOCKUP-PLAN-07:plan_register.status_chip">Status</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 bg-white">
                  {data.results.length ? (
                    data.results.map((plan) => (
                      <tr key={plan.id}>
                        <td className="px-3 py-2">
                          <div className="font-medium text-neutral-900">{plan.target_label}</div>
                          {plan.is_additional && (
                            <Badge variant="secondary" className="mt-1">Additional</Badge>
                          )}
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">{plan.audit_standards_csv}</td>
                        <td className="px-3 py-2 font-mono text-xs">
                          <div>{plan.window_label}</div>
                          {plan.extended_due_date && (
                            <div className="mt-1 text-amber-700">Extended to {formatDisplayDate(plan.extended_due_date)}</div>
                          )}
                        </td>
                        <td className="px-3 py-2 text-xs">{formatOpmF713(plan)}</td>
                        <td className="px-3 py-2">
                          <Badge variant={statusVariant(plan.status)}>{getStatusLabel(plan.status)}</Badge>
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-2">
                            {canEditPlan && !plan.is_additional && plan.status !== 'CANCELLED' && (
                              <Button type="button" variant="outline" size="sm" onClick={() => setSelectedPlan(plan)}>
                                <Edit2 className="mr-2 h-4 w-4" />
                                Edit
                              </Button>
                            )}
                            {canCreatePlan && !plan.is_additional && plan.status !== 'CANCELLED' && (
                              <Button type="button" variant="outline" size="sm" onClick={() => openWorkflow(plan, 'extension')}>
                                <FilePlus2 className="mr-2 h-4 w-4" />
                                Extension
                              </Button>
                            )}
                            {canApproveExtension && plan.status === 'EXTENSION_REQUESTED' && (
                              <Button type="button" variant="outline" size="sm" onClick={() => openWorkflow(plan, 'decision')}>
                                <CheckCircle2 className="mr-2 h-4 w-4" />
                                Decide
                              </Button>
                            )}
                            {canApproveExtension && plan.status === 'EXTENDED' && (
                              <Button type="button" variant="outline" size="sm" onClick={() => openWorkflow(plan, 'flag')}>
                                <Bell className="mr-2 h-4 w-4" />
                                Flag
                              </Button>
                            )}
                            {canCancelPlan && plan.status !== 'CANCELLED' && (
                              <Button type="button" variant="outline" size="sm" onClick={() => openWorkflow(plan, 'cancel')}>
                                <Ban className="mr-2 h-4 w-4" />
                                Cancel
                              </Button>
                            )}
                            {(!canEditPlan || plan.is_additional || plan.status === 'CANCELLED') && (
                              <span className="text-xs text-neutral-500">Read only</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="px-3 py-6 text-center text-neutral-500">
                        No audit plan entries found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {workflowPlan && workflowMode && (
          <Card>
            <CardHeader>
              <CardTitle>{workflowTitle(workflowMode)}: {workflowPlan.target_label}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {workflowMode === 'extension' && (
                <div className="grid gap-4 lg:grid-cols-2" data-eid="MOCKUP-PLAN-07:plan.extension_form">
                  <FieldTextarea
                    id="extension_requested_reason"
                    label="Reason for delay"
                    value={extensionForm.extension_requested_reason}
                    onChange={(value) => setExtensionForm((current) => ({ ...current, extension_requested_reason: value }))}
                  />
                  <FieldInput
                    id="proposed_new_target_date"
                    label="Proposed new target date"
                    type="date"
                    value={extensionForm.proposed_new_target_date}
                    onChange={(value) => setExtensionForm((current) => ({ ...current, proposed_new_target_date: value }))}
                  />
                </div>
              )}
              {workflowMode === 'decision' && (
                <div className="grid gap-4 lg:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="extension_decision">Decision</Label>
                    <select
                      id="extension_decision"
                      value={decisionForm.decision}
                      onChange={(event) => setDecisionForm((current) => ({ ...current, decision: event.target.value as 'APPROVE' | 'REJECT' }))}
                      className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                    >
                      <option value="APPROVE">{formatEnumLabel('APPROVE')}</option>
                      <option value="REJECT">{formatEnumLabel('REJECT')}</option>
                    </select>
                  </div>
                  <FieldTextarea
                    id="extension_approved_reason"
                    label="DPA reason"
                    value={decisionForm.extension_approved_reason}
                    onChange={(value) => setDecisionForm((current) => ({ ...current, extension_approved_reason: value }))}
                  />
                </div>
              )}
              {workflowMode === 'flag' && (
                <div className="grid gap-4 lg:grid-cols-3" data-eid="MOCKUP-PLAN-07:plan.flag_notify">
                  <FieldInput
                    id="flag_notification_date"
                    label="Flag notification date"
                    type="date"
                    value={flagForm.flag_notification_date}
                    onChange={(value) => setFlagForm((current) => ({ ...current, flag_notification_date: value }))}
                  />
                  <FieldInput
                    id="flag_notification_ref"
                    label="Flag notification ref"
                    value={flagForm.flag_notification_ref}
                    onChange={(value) => setFlagForm((current) => ({ ...current, flag_notification_ref: value }))}
                  />
                  <FieldInput
                    id="flag_notification_attachment"
                    label="Flag attachment ref"
                    value={flagForm.flag_notification_attachment}
                    onChange={(value) => setFlagForm((current) => ({ ...current, flag_notification_attachment: value }))}
                  />
                </div>
              )}
              {workflowMode === 'cancel' && (
                <div className="grid gap-4 lg:grid-cols-2" data-eid="MOCKUP-PLAN-07:plan.cancel_form">
                  <FieldTextarea
                    id="cancellation_reason"
                    label="Cancellation reason"
                    value={cancelForm.cancellation_reason}
                    onChange={(value) => setCancelForm((current) => ({ ...current, cancellation_reason: value }))}
                  />
                  <FieldInput
                    id="next_planned_date"
                    label="Next planned date"
                    type="date"
                    value={cancelForm.next_planned_date}
                    onChange={(value) => setCancelForm((current) => ({ ...current, next_planned_date: value }))}
                  />
                </div>
              )}
              <div className="flex flex-wrap justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setWorkflowPlan(null)}>Close</Button>
                <Button type="button" onClick={submitWorkflow} disabled={workflowPending(requestExtension, decideExtension, recordFlag, cancelPlan)}>
                  {workflowPending(requestExtension, decideExtension, recordFlag, cancelPlan) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Save workflow
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {(canCreatePlan || selectedPlan) && (
          <Card>
            <CardHeader>
              <CardTitle>{selectedPlan ? 'Edit routine plan entry' : 'Create routine plan entry'}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <PlanFields
                form={form}
                setField={setField}
                idPrefix="routine_"
                vesselOptions={vesselQuery.data ?? []}
                vesselsLoading={vesselQuery.isLoading}
              />
              <div className="flex flex-wrap justify-end gap-2">
                {selectedPlan && (
                  <Button type="button" variant="outline" onClick={() => setSelectedPlan(null)}>
                    Cancel edit
                  </Button>
                )}
                <Button
                  type="button"
                  onClick={savePlan}
                  disabled={createPlan.isPending || updatePlan.isPending}
                  className={cn(!selectedPlan && !canCreatePlan && 'hidden')}
                >
                  {createPlan.isPending || updatePlan.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : selectedPlan ? (
                    <Save className="mr-2 h-4 w-4" />
                  ) : (
                    <Plus className="mr-2 h-4 w-4" />
                  )}
                  {selectedPlan ? 'Save plan' : 'New plan entry'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {canCreatePlan && (
          <Card>
            <CardHeader>
              <CardTitle>Create additional audit</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4" data-eid="MOCKUP-PLAN-07:plan.additional_form">
              <PlanFields
                form={additionalForm}
                setField={setAdditionalField}
                idPrefix="additional_"
                vesselOptions={vesselQuery.data ?? []}
                vesselsLoading={vesselQuery.isLoading}
                statusDisabled
              />
              <div className="grid gap-4 lg:grid-cols-3" data-eid="MOCKUP-PLAN-07:plan.trigger_picker">
                <div className="space-y-2">
                  <Label htmlFor="trigger_event_type">Trigger type</Label>
                  <select
                    id="trigger_event_type"
                    value={additionalForm.trigger_event_type}
                    onChange={(event) => setAdditionalField('trigger_event_type', event.target.value)}
                    className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                  >
                    {triggerTypes.map((triggerType) => (
                      <option key={triggerType} value={triggerType}>{formatEnumLabel(triggerType)}</option>
                    ))}
                  </select>
                </div>
                <FieldInput
                  id="trigger_event_ref"
                  label="Trigger reference"
                  value={additionalForm.trigger_event_ref}
                  onChange={(value) => setAdditionalField('trigger_event_ref', value)}
                />
                <FieldTextarea
                  id="additional_reason"
                  label="Additional reason"
                  value={additionalForm.additional_reason}
                  onChange={(value) => setAdditionalField('additional_reason', value)}
                />
              </div>
              <div className="flex justify-end">
                <Button type="button" onClick={saveAdditionalPlan} disabled={createAdditional.isPending}>
                  {createAdditional.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                  Additional audit
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </RootLayout>
  );
}

function PlanFields({
  form,
  setField,
  idPrefix,
  vesselOptions,
  vesselsLoading,
  statusDisabled = false,
}: {
  form: AuditPlanFormData;
  setField: (fieldName: keyof AuditPlanFormData, value: string) => void;
  idPrefix: string;
  vesselOptions: AuditVesselOption[];
  vesselsLoading: boolean;
  statusDisabled?: boolean;
}) {
  const qualifiedAuditors = useAuditQualifiedAuditors(form.audit_standards_csv, form.target_office_dept);
  const auditorOptions = qualifiedAuditors.data?.results ?? [];

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="space-y-2" data-eid="MOCKUP-PLAN-07:plan_form.target">
        <Label htmlFor={`${idPrefix}target_vessel_id`}>Target vessel</Label>
        <select
          id={`${idPrefix}target_vessel_id`}
          value={form.target_vessel_id}
          onChange={(event) => setField('target_vessel_id', event.target.value)}
          disabled={vesselsLoading}
          className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:bg-neutral-100"
        >
          <option value="">{vesselsLoading ? 'Loading vessels...' : 'Not a vessel audit'}</option>
          {vesselOptions.map((vessel) => (
            <option key={vessel.id} value={vessel.id}>
              {formatVesselOption(vessel)}
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}target_office_dept`}>Target office department</Label>
        <select
          id={`${idPrefix}target_office_dept`}
          value={form.target_office_dept}
          onChange={(event) => setField('target_office_dept', event.target.value)}
          className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          {officeDepartments.map((department) => (
            <option key={department || 'blank'} value={department}>
              {department || 'Not an office audit'}
            </option>
          ))}
        </select>
      </div>
      <StandardsDropdown
        id={`${idPrefix}audit_standards_csv`}
        value={form.audit_standards_csv}
        onChange={(value) => setField('audit_standards_csv', value)}
      />
      <LeadAuditorSelect
        id={`${idPrefix}lead_auditor_user_id`}
        value={form.lead_auditor_user_id}
        auditors={auditorOptions}
        loading={qualifiedAuditors.isLoading}
        onChange={(value) => setField('lead_auditor_user_id', value)}
      />
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}status`}>Status</Label>
        <select
          id={`${idPrefix}status`}
          value={form.status}
          disabled={statusDisabled}
          onChange={(event) => setField('status', event.target.value)}
          className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:bg-neutral-100"
        >
          {AUDIT_PLAN_WRITABLE_STATUSES.map((status) => (
            <option key={status} value={status}>{getStatusLabel(status)}</option>
          ))}
        </select>
      </div>
      <FieldInput
        id={`${idPrefix}planned_window_start`}
        label="Planned window start"
        type="date"
        value={form.planned_window_start}
        onChange={(value) => setField('planned_window_start', value)}
      />
      <FieldInput
        id={`${idPrefix}planned_window_end`}
        label="Planned window end"
        type="date"
        value={form.planned_window_end}
        onChange={(value) => setField('planned_window_end', value)}
      />
    </div>
  );
}

function StandardsDropdown({
  id,
  value,
  onChange,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const selectedStandards = parseStandardsCsv(value);
  const selectedKnownStandards = selectedStandards.filter(isAuditStandardOption);
  const displayValue = selectedStandards.length ? selectedStandards.join(', ') : 'Select standards';

  const toggleStandard = (standard: AuditStandardOption, checked: boolean) => {
    const selected = new Set(selectedStandards);
    if (checked) {
      selected.add(standard);
    } else {
      selected.delete(standard);
    }
    const orderedKnown = auditStandardOptions.filter((option) => selected.has(option));
    const otherValues = selectedStandards.filter((option) => !isAuditStandardOption(option) && selected.has(option));
    onChange([...orderedKnown, ...otherValues].join(','));
  };

  return (
    <div className="relative space-y-2">
      <Label htmlFor={id}>Standards</Label>
      <button
        id={id}
        type="button"
        aria-expanded={open}
        className="flex h-10 w-full items-center justify-between rounded-md border border-neutral-300 bg-white px-3 py-2 text-left text-sm text-neutral-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        onClick={() => setOpen((current) => !current)}
      >
        <span className={cn('truncate', selectedStandards.length ? 'text-neutral-900' : 'text-neutral-500')}>
          {displayValue}
        </span>
        <ChevronDown className={cn('ml-2 h-4 w-4 shrink-0 text-neutral-500 transition-transform', open && 'rotate-180')} />
      </button>
      {open ? (
        <div className="absolute z-30 w-full rounded-md border border-neutral-200 bg-white p-2 shadow-lg">
          <div className="grid gap-2 sm:grid-cols-2">
            {auditStandardOptions.map((standard) => (
              <label
                key={standard}
                className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 text-sm text-neutral-700 hover:bg-neutral-50"
              >
                <input
                  type="checkbox"
                  checked={selectedKnownStandards.includes(standard)}
                  onChange={(event) => toggleStandard(standard, event.target.checked)}
                  className="h-4 w-4 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                />
                {standard}
              </label>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function LeadAuditorSelect({
  id,
  value,
  auditors,
  loading,
  onChange,
}: {
  id: string;
  value: string;
  auditors: AuditQualifiedAuditor[];
  loading: boolean;
  onChange: (value: string) => void;
}) {
  const placeholder = loading
    ? 'Loading qualified auditors...'
    : auditors.length
      ? 'Select lead auditor'
      : 'No qualified auditors found';

  return (
    <div className="space-y-2">
      <Label htmlFor={id}>Lead auditor</Label>
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={loading}
        className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:bg-neutral-100"
      >
        <option value="" disabled={!loading && auditors.length === 0}>{placeholder}</option>
        {auditors.map((auditor) => (
          <option key={auditor.id} value={auditor.user_id}>
            {formatAuditorOption(auditor)}
          </option>
        ))}
      </select>
    </div>
  );
}

function formatAuditorOption(auditor: AuditQualifiedAuditor): string {
  const details = [auditor.designation, auditor.qualification_text, `valid until ${auditor.expiry_date}`]
    .filter(Boolean)
    .join(' - ');
  return details ? `${auditor.display_name} (${details})` : auditor.display_name || auditor.user_id;
}

function FieldInput({
  id,
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
  eid,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  eid?: string;
}) {
  return (
    <div className="space-y-2" data-eid={eid}>
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

function FieldTextarea({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Textarea id={id} value={value} rows={4} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function RegisterMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3">
      <p className="text-xs font-medium uppercase text-neutral-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-neutral-900">{value}</p>
    </div>
  );
}

function parseStandardsCsv(value: string): string[] {
  return value
    .split(',')
    .map((part) => part.trim().toUpperCase())
    .filter(Boolean);
}

function isAuditStandardOption(value: string): value is AuditStandardOption {
  return auditStandardOptions.includes(value as AuditStandardOption);
}

function workflowTitle(mode: WorkflowMode) {
  if (mode === 'extension') return 'Request OPM F 713';
  if (mode === 'decision') return 'DPA extension decision';
  if (mode === 'flag') return 'Flag notification';
  if (mode === 'cancel') return 'Cancel audit';
  return 'Plan workflow';
}

function workflowPending(...mutations: { isPending?: boolean }[]) {
  return mutations.some((mutation) => Boolean(mutation.isPending));
}

function setTargetExclusive<T extends AuditPlanFormData>(
  current: T,
  fieldName: keyof T,
  value: string
): T {
  if (fieldName === 'target_vessel_id' && value) {
    return { ...current, target_vessel_id: value, target_office_dept: '' };
  }
  if (fieldName === 'target_office_dept' && value) {
    return { ...current, target_office_dept: value, target_vessel_id: '' };
  }
  return { ...current, [fieldName]: value };
}

function formatVesselOption(vessel: AuditVesselOption): string {
  if (vessel.vessel_code && vessel.vessel_name) {
    return `${vessel.vessel_code} - ${vessel.vessel_name}`;
  }
  return vessel.vessel_name || vessel.vessel_code || vessel.id;
}
