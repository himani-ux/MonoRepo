import { useEffect, useMemo, useState, type ChangeEvent } from 'react';
import { AlertCircle, ArrowLeft, CheckCircle2, ClipboardList, ExternalLink, Loader2, Save, Send } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button, Badge, Card, CardContent, CardHeader, CardTitle, Input, Label, Textarea } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import {
  AUDIT_SCORECARD_STATUSES,
  detailEditableFields,
  type AuditDetail,
  type AuditDetailEditableFields,
  type AuditScorecardRow,
  type AuditScorecardStatus,
} from '@/schemas/audit/detail';
import {
  useAcknowledgeAuditReport,
  useAuditDetail,
  useSubmitAuditReport,
  useUpdateAuditDetail,
  useUpdateAuditScorecard,
} from '@/hooks/audit/use-audit-registration';
import { useIssueAuditCircular } from '@/hooks/audit/use-audit-finding';
import { getErrorMessage } from '@/lib/api/client';
import { ROUTES } from '@/lib/utils/constants';
import { PROCESS_IDS } from '@/lib/utils/permission-ids';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface AuditDetailPageProps {
  auditId: string;
}

type SubmitGateErrors = Record<string, Record<string, string>>;

const verifyOptions = ['', 'YES', 'NO', 'NA'] as const;

function toInputDateTime(value: string | null | undefined): string {
  return value ? value.slice(0, 16) : '';
}

function fromInputDateTime(value: string): string | null {
  return value ? value : null;
}

function statusClass(status: string | null) {
  switch (status) {
    case 'SATISFACTORY':
      return 'bg-success-100 text-success-700';
    case 'NEEDS_IMPROVEMENT':
      return 'bg-warning-100 text-warning-700';
    case 'NC_RAISED':
      return 'bg-error-100 text-error-700';
    case 'N_A':
      return 'bg-neutral-100 text-neutral-500';
    default:
      return 'bg-neutral-100 text-neutral-500';
  }
}

function auditStatusVariant(status: string) {
  if (status === 'DPA_CLOSED') return 'success';
  if (status === 'CANCELLED') return 'destructive';
  if (status === 'IN_PROGRESS' || status === 'VESSEL_ACKNOWLEDGED') return 'warning';
  return 'secondary';
}

export function AuditDetailPage({ auditId }: AuditDetailPageProps) {
  const { toast } = useToast();
  const { data: audit, isLoading, error, refetch } = useAuditDetail(auditId);
  const submitAudit = useSubmitAuditReport(auditId);
  const acknowledgeAudit = useAcknowledgeAuditReport(auditId);
  const updateDetail = useUpdateAuditDetail(auditId);
  const updateScorecard = useUpdateAuditScorecard(auditId);
  const issueCircular = useIssueAuditCircular(auditId);
  const [fields, setFields] = useState<AuditDetailEditableFields | null>(null);
  const [scorecardRows, setScorecardRows] = useState<AuditScorecardRow[]>([]);
  const [submitGateErrors, setSubmitGateErrors] = useState<SubmitGateErrors | null>(null);

  useEffect(() => {
    if (!audit) return;
    setFields({
      ...detailEditableFields(audit),
      opening_meeting_at: toInputDateTime(audit.opening_meeting_at),
      closing_meeting_at: toInputDateTime(audit.closing_meeting_at),
    });
    setScorecardRows(audit.scorecard);
  }, [audit]);

  const completeScorecardCount = useMemo(
    () => scorecardRows.filter((row) => Boolean(row.status)).length,
    [scorecardRows]
  );

  if (isLoading || !fields) {
    return (
      <RootLayout>
        <PageHeader title="Audit Detail" showBack backTo={ROUTES.INSPECTIONS} />
        <div className="space-y-4 p-4">
          <SectionSkeleton />
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  if (error || !audit) {
    return (
      <RootLayout>
        <PageHeader title="Audit Detail" showBack backTo={ROUTES.INSPECTIONS} />
        <ErrorState
          title="Audit not found"
          message="The audit may have been deleted or you don't have access."
          onRetry={() => refetch()}
        />
      </RootLayout>
    );
  }

  const setField = (fieldName: keyof AuditDetailEditableFields, value: string) => {
    setFields((current) => current ? { ...current, [fieldName]: value } : current);
  };

  const saveDetail = async () => {
    try {
      await updateDetail.mutateAsync({
        ...fields,
        opening_meeting_at: fromInputDateTime(String(fields.opening_meeting_at || '')),
        closing_meeting_at: fromInputDateTime(String(fields.closing_meeting_at || '')),
      });
      toast({ title: 'Audit detail saved' });
    } catch (saveError) {
      toast({
        variant: 'destructive',
        title: 'Audit detail not saved',
        description: getErrorMessage(saveError),
      });
    }
  };

  const saveScorecard = async () => {
    try {
      await updateScorecard.mutateAsync(
        scorecardRows
          .filter((row) => row.status)
          .map((row) => ({
            area_code: row.area_code,
            status: row.status,
            remarks: row.remarks || '',
          }))
      );
      toast({ title: 'Scorecard saved' });
    } catch (saveError) {
      toast({
        variant: 'destructive',
        title: 'Scorecard not saved',
        description: getErrorMessage(saveError),
      });
    }
  };

  const submitReport = async () => {
    setSubmitGateErrors(null);
    try {
      await submitAudit.mutateAsync();
      toast({ title: 'Audit report finalized' });
    } catch (submitError) {
      const gates = gateErrorsFromApiError(submitError);
      if (gates) {
        setSubmitGateErrors(gates);
      }
      toast({
        variant: 'destructive',
        title: 'Audit report not finalized',
        description: getErrorMessage(submitError),
      });
    }
  };

  const acknowledgeReport = async () => {
    try {
      await acknowledgeAudit.mutateAsync();
      toast({ title: 'Audit report acknowledged' });
    } catch (acknowledgeError) {
      toast({
        variant: 'destructive',
        title: 'Audit report not acknowledged',
        description: getErrorMessage(acknowledgeError),
      });
    }
  };

  const issueCircularForFinding = async (findingId: string) => {
    try {
      const result = await issueCircular.mutateAsync(findingId);
      toast({
        title: result.status === 'ALREADY_LINKED' ? 'Circular already linked' : 'Circular draft created',
      });
      if (result.detail_url) {
        window.location.href = result.detail_url;
      }
    } catch (issueError) {
      toast({
        variant: 'destructive',
        title: 'Issue Circular failed',
        description: getErrorMessage(issueError),
      });
    }
  };

  const effectivePermissions = new Set(audit.effective_permissions ?? []);
  const canEditAudit = effectivePermissions.has(PROCESS_IDS.AUDIT_EDIT);
  const canConductAudit = effectivePermissions.has(PROCESS_IDS.AUDIT_CONDUCT);
  const canAcknowledgeAudit = effectivePermissions.has(PROCESS_IDS.AUDIT_ACKNOWLEDGE_REPORT);

  return (
    <RootLayout>
      <PageHeader
        title="Audit Detail"
        showBack
        backTo={ROUTES.INSPECTIONS}
        actions={
          <Button variant="outline" size="sm" onClick={() => window.history.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        }
      />

      <div className="space-y-4 p-4">
        <AuditHeader audit={audit} />
        {submitGateErrors && <SubmitGateFailureBanner gates={submitGateErrors} />}

        <Card>
          <CardHeader>
            <CardTitle>Report Actions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-800">Current status: {audit.status}</p>
              <p className="text-sm text-neutral-500">
                Submit runs the four D-071 gates; acknowledgement starts the vessel-received status chain.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {audit.status === 'IN_PROGRESS' && canConductAudit && (
                <Button asChild variant="outline">
                  <Link to={`/audit/audits/${audit.id}/checklist`}>
                    <ClipboardList className="mr-2 h-4 w-4" />
                    Walk Checklist
                  </Link>
                </Button>
              )}
              {audit.status === 'IN_PROGRESS' && canConductAudit && (
                <Button onClick={submitReport} disabled={submitAudit.isPending}>
                  {submitAudit.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                  Submit Report
                </Button>
              )}
              {audit.status === 'REPORT_FINALIZED' && canAcknowledgeAudit && (
                <Button onClick={acknowledgeReport} disabled={acknowledgeAudit.isPending}>
                  {acknowledgeAudit.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-2 h-4 w-4" />}
                  Vessel Acknowledge Audit Report
                </Button>
              )}
              {audit.status === 'VESSEL_ACKNOWLEDGED' && (
                <Badge variant="warning">Vessel acknowledged</Badge>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>F602 Detail</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-2" data-eid="MOCKUP-AUDIT-02:detail.scope">
                <Label htmlFor="audit_scope">Audit Objectives / Scope</Label>
                <Textarea
                  id="audit_scope"
                  value={fields.audit_scope}
                  onChange={(event) => setField('audit_scope', event.target.value)}
                  rows={4}
                />
              </div>
              <div className="space-y-2" data-eid="MOCKUP-AUDIT-02:detail.tor">
                <Label htmlFor="terms_of_reference">Terms of Reference</Label>
                <Textarea
                  id="terms_of_reference"
                  value={fields.terms_of_reference}
                  onChange={(event) => setField('terms_of_reference', event.target.value)}
                  rows={4}
                />
              </div>
              <div className="space-y-2" data-eid="MOCKUP-AUDIT-02:detail.opening_meeting">
                <Label htmlFor="opening_meeting_at">Opening Meeting</Label>
                <Input
                  id="opening_meeting_at"
                  type="datetime-local"
                  value={String(fields.opening_meeting_at || '')}
                  onChange={(event) => setField('opening_meeting_at', event.target.value)}
                />
              </div>
              <div className="space-y-2" data-eid="MOCKUP-AUDIT-02:detail.closing_meeting">
                <Label htmlFor="closing_meeting_at">Closing Meeting</Label>
                <Input
                  id="closing_meeting_at"
                  type="datetime-local"
                  value={String(fields.closing_meeting_at || '')}
                  onChange={(event) => setField('closing_meeting_at', event.target.value)}
                />
              </div>
              <VerifySelect
                id="prev_internal_ca_verified"
                label="Prev Internal CA Verified"
                value={fields.prev_internal_ca_verified || ''}
                onChange={(value) => setField('prev_internal_ca_verified', value)}
                eid="MOCKUP-AUDIT-02:detail.prev_internal_ca"
              />
              <VerifySelect
                id="prev_external_ca_verified"
                label="Prev External CA Verified"
                value={fields.prev_external_ca_verified || ''}
                onChange={(value) => setField('prev_external_ca_verified', value)}
                eid="MOCKUP-AUDIT-02:detail.prev_external_ca"
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={saveDetail} disabled={updateDetail.isPending || !canEditAudit}>
                {updateDetail.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                Save Detail
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card data-eid="MOCKUP-AUDIT-02:detail.scorecard_grid">
          <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>14-Area Inspection Summary</CardTitle>
            <span className="text-sm text-neutral-500">{completeScorecardCount}/14 populated</span>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 lg:grid-cols-2">
              {scorecardRows.map((row, index) => (
                <ScorecardEditorRow
                  key={row.area_code}
                  row={row}
                  onChange={(nextRow) => {
                    setScorecardRows((current) => current.map((item, itemIndex) => itemIndex === index ? nextRow : item));
                  }}
                />
              ))}
            </div>
            <div className="flex justify-end">
              <Button onClick={saveScorecard} disabled={updateScorecard.isPending || !canConductAudit}>
                {updateScorecard.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                Save Scorecard
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Findings</CardTitle>
          </CardHeader>
          <CardContent data-eid="MOCKUP-AUDIT-02:detail.findings_table">
            <FindingCounts audit={audit} />
            <div className="mt-4 overflow-x-auto rounded-lg border border-neutral-200">
              <table className="min-w-full divide-y divide-neutral-200 text-sm">
                <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                  <tr>
                    <th className="px-3 py-2">Type</th>
                    <th className="px-3 py-2">Description</th>
                    <th className="px-3 py-2">Clause</th>
                    <th className="px-3 py-2">Priority</th>
                    <th className="px-3 py-2">CAR</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Closure</th>
                    <th className="px-3 py-2">Circular</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 bg-white">
                  {audit.findings.length ? (
                    audit.findings.map((finding) => (
                      <tr key={finding.id}>
                        <td className="px-3 py-2">{finding.finding_type}</td>
                        <td className="px-3 py-2 text-neutral-800">{finding.description}</td>
                        <td className="px-3 py-2">{finding.clause_ref_text || finding.standard_code || '-'}</td>
                        <td className="px-3 py-2">
                          <Badge variant={finding.priority === 'CRITICAL' ? 'destructive' : 'secondary'}>
                            {finding.priority}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">{finding.car_number || '-'}</td>
                        <td className="px-3 py-2">{finding.car_status || '-'}</td>
                        <td className="px-3 py-2">
                          {finding.finding_type === 'NC' ? (
                            <div className="flex flex-wrap gap-2">
                              <Button asChild variant="outline" size="sm">
                                <Link to={`/audit/findings/${finding.id}/nc`}>
                                  <ClipboardList className="mr-2 h-4 w-4" />
                                  Dense
                                </Link>
                              </Button>
                              <Button asChild variant="outline" size="sm">
                                <Link to={`/audit/findings/${finding.id}/nc/wizard`}>
                                  <ClipboardList className="mr-2 h-4 w-4" />
                                  Wizard
                                </Link>
                              </Button>
                            </div>
                          ) : finding.finding_type === 'OBSERVATION' ? (
                            <Button asChild variant="outline" size="sm">
                              <Link to={`/audit/findings/${finding.id}/obs`}>
                                <ClipboardList className="mr-2 h-4 w-4" />
                                Observation
                              </Link>
                            </Button>
                          ) : (
                            <span className="text-xs text-neutral-500">-</span>
                          )}
                        </td>
                        <td className="px-3 py-2">
                          {finding.linked_circular_id ? (
                            <span className="text-xs font-medium text-success-700">Linked</span>
                          ) : finding.finding_type === 'NC' && finding.is_fleetwide_relevance ? (
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              disabled={issueCircular.isPending}
                              onClick={() => issueCircularForFinding(finding.id)}
                            >
                              <ExternalLink className="mr-2 h-4 w-4" />
                              Issue Circular
                            </Button>
                          ) : (
                            <span className="text-xs text-neutral-500">-</span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="px-3 py-6 text-center text-neutral-500">
                        No findings recorded.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Summary & Equipment</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2" data-eid="MOCKUP-AUDIT-02:detail.summary">
              <Label htmlFor="audit_summary">Summary of Audit</Label>
              <Textarea
                id="audit_summary"
                value={fields.audit_summary}
                onChange={(event) => setField('audit_summary', event.target.value)}
                rows={5}
              />
              <p className={cn('text-xs', fields.audit_summary.length >= 100 ? 'text-success-700' : 'text-neutral-500')}>
                {fields.audit_summary.length}/100 characters for submit gate.
              </p>
            </div>
            <div className="space-y-2" data-eid="MOCKUP-AUDIT-02:detail.equipment_tested">
              <Label htmlFor="equipment_tested">Equipment Tested Successfully</Label>
              <Textarea
                id="equipment_tested"
                value={fields.equipment_tested}
                onChange={(event) => setField('equipment_tested', event.target.value)}
                rows={4}
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={saveDetail} disabled={updateDetail.isPending}>
                {updateDetail.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                Save Summary
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </RootLayout>
  );
}

function AuditHeader({ audit }: { audit: AuditDetail }) {
  const entity = audit.auditee_type === 'OFFICE_DEPT'
    ? audit.auditee_office_dept || 'Office department'
    : audit.inspection.vessel_id;
  const dates = audit.audit_end_date
    ? `${audit.audit_start_date} to ${audit.audit_end_date}`
    : audit.audit_start_date;

  return (
    <Card>
      <CardContent className="grid gap-4 p-4 lg:grid-cols-[1.4fr_1fr_1fr_auto]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold text-neutral-900" data-eid="MOCKUP-AUDIT-02:detail_header.entity">
              {entity}
            </h1>
            <Badge variant={auditStatusVariant(audit.status)}>{audit.status}</Badge>
          </div>
          <p className="mt-1 text-sm text-neutral-500">
            {audit.audit_classification} - {audit.standards.join('/')} - Lead Auditor {audit.lead_auditor_name}
          </p>
          <p className="mt-1 text-sm text-neutral-500" data-eid="MOCKUP-AUDIT-02:detail.auditors">
            Team: {audit.team_members.map((member) => member.member_name).join(', ') || 'Lead auditor only'}
          </p>
        </div>
        <HeaderDatum label="Location / Port" value={audit.inspection.port_place} eid="MOCKUP-AUDIT-02:detail_header.port" />
        <HeaderDatum label="Audit Dates" value={dates} eid="MOCKUP-AUDIT-02:detail_header.dates" />
        <div className="rounded-md border border-warning-100 bg-warning-50 px-3 py-2 text-sm text-warning-700">
          <div className="flex items-center gap-2 font-medium">
            <AlertCircle className="h-4 w-4" />
            D-071 gated submit
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SubmitGateFailureBanner({ gates }: { gates: SubmitGateErrors }) {
  return (
    <div className="rounded-md border border-error-200 bg-error-50 p-4 text-sm text-error-700" role="alert">
      <div className="flex items-start gap-2">
        <AlertCircle className="mt-0.5 h-4 w-4 flex-none" />
        <div>
          <p className="font-semibold">Submit gates blocked finalization</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {Object.entries(gates).flatMap(([gateName, fields]) =>
              Object.entries(fields).map(([fieldName, message]) => (
                <li key={`${gateName}-${fieldName}`}>
                  <span className="font-medium">{gateName.replace(/_/g, ' ')}:</span> {message}
                </li>
              ))
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}

function gateErrorsFromApiError(error: unknown): SubmitGateErrors | null {
  const data = (error as { response?: { data?: { gates?: unknown } } })?.response?.data;
  if (!data || !data.gates || typeof data.gates !== 'object' || Array.isArray(data.gates)) {
    return null;
  }
  return data.gates as SubmitGateErrors;
}

function HeaderDatum({ label, value, eid }: { label: string; value: string; eid: string }) {
  return (
    <div data-eid={eid}>
      <p className="text-xs font-medium uppercase text-neutral-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-neutral-800">{value || '-'}</p>
    </div>
  );
}

function VerifySelect({
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
  eid: string;
}) {
  return (
    <div className="space-y-2" data-eid={eid}>
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
      >
        {verifyOptions.map((option) => (
          <option key={option || 'blank'} value={option}>
            {option || 'Not set'}
          </option>
        ))}
      </select>
    </div>
  );
}

function ScorecardEditorRow({
  row,
  onChange,
}: {
  row: AuditScorecardRow;
  onChange: (row: AuditScorecardRow) => void;
}) {
  const handleStatusChange = (event: ChangeEvent<HTMLSelectElement>) => {
    onChange({
      ...row,
      status: event.target.value ? event.target.value as AuditScorecardStatus : null,
    });
  };

  return (
    <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-neutral-800">{row.sequence_no}. {row.display_name}</p>
          {row.is_vessel_only && <p className="text-xs text-neutral-500">Vessel-only area</p>}
        </div>
        <span className={cn('rounded-sm px-2 py-1 text-xs font-semibold', statusClass(row.status))}>
          {row.status || 'BLANK'}
        </span>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-[220px_1fr]">
        <select
          aria-label={`${row.display_name} status`}
          value={row.status || ''}
          onChange={handleStatusChange}
          className="h-10 rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          <option value="">Select status</option>
          {AUDIT_SCORECARD_STATUSES.map((status) => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
        <Input
          aria-label={`${row.display_name} remarks`}
          value={row.remarks}
          onChange={(event) => onChange({ ...row, remarks: event.target.value })}
          placeholder="Remarks"
        />
      </div>
    </div>
  );
}

function FindingCounts({ audit }: { audit: AuditDetail }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3" data-eid="MOCKUP-AUDIT-02:detail.nc_count">
        <p className="text-xs font-medium uppercase text-neutral-500">NCs Raised</p>
        <p className="mt-1 text-2xl font-semibold text-neutral-900">{audit.counts.nc}</p>
      </div>
      <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3" data-eid="MOCKUP-AUDIT-02:detail.obs_count">
        <p className="text-xs font-medium uppercase text-neutral-500">Observations Raised</p>
        <p className="mt-1 text-2xl font-semibold text-neutral-900">{audit.counts.observations}</p>
      </div>
      <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
        <p className="text-xs font-medium uppercase text-neutral-500">Total Findings</p>
        <p className="mt-1 text-2xl font-semibold text-neutral-900">{audit.counts.total_findings}</p>
      </div>
    </div>
  );
}
