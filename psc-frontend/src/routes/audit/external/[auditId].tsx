import { useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, Loader2, Save } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Checkbox, Input, Label, Textarea } from '@/components/ui';
import {
  useAuditDetail,
  useConfirmExternalAuditCloseout,
  useEditExternalAuditCertLinks,
} from '@/hooks/audit/use-audit-registration';
import { useToast } from '@/hooks/use-toast';
import { getErrorMessage } from '@/lib/api/client';
import { formatEnumLabel, getStatusLabel } from '@/lib/utils/format-status';

const certificateImpacts = ['CERT_VALID', 'RENEWAL_AT_RISK', 'SUSPENDED', 'WITHDRAWN', 'NONE'] as const;

function splitCerts(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function ExternalAuditDetailRoute() {
  const { auditId } = useParams();
  return <ExternalAuditCloseoutPage auditId={auditId || ''} />;
}

export function ExternalAuditCloseoutPage({ auditId }: { auditId: string }) {
  const { toast } = useToast();
  const { data: audit, isLoading, error, refetch } = useAuditDetail(auditId);
  const closeout = useConfirmExternalAuditCloseout(auditId);
  const editLinks = useEditExternalAuditCertLinks(auditId);
  const [certificateImpact, setCertificateImpact] = useState<(typeof certificateImpacts)[number]>('CERT_VALID');
  const [typedCertNumber, setTypedCertNumber] = useState('');
  const [flagNotifiedTo, setFlagNotifiedTo] = useState('');
  const [flagNotificationRef, setFlagNotificationRef] = useState('');
  const [isCycleResetting, setIsCycleResetting] = useState(false);
  const [cycleResetReason, setCycleResetReason] = useState('');
  const [linkedCertText, setLinkedCertText] = useState('');
  const [linkReason, setLinkReason] = useState('');

  const initialCertText = useMemo(() => (audit?.linked_cert_ids || []).join(', '), [audit?.linked_cert_ids]);

  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader title="External Audit" showBack backTo="/audit/plans" />
        <div className="space-y-4 p-4">
          <SectionSkeleton />
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  if (error || !audit) {
    return (
      <RootLayout>
        <PageHeader title="External Audit" showBack backTo="/audit/plans" />
        <ErrorState title="External audit not found" message="The audit may have been deleted or inaccessible." onRetry={() => refetch()} />
      </RootLayout>
    );
  }

  const certText = linkedCertText || initialCertText;
  const suspended = certificateImpact === 'SUSPENDED';

  const confirmCloseout = async () => {
    try {
      await closeout.mutateAsync({
        certificate_impact: certificateImpact,
        typed_cert_number: typedCertNumber,
        flag_notified_to: flagNotifiedTo,
        flag_notification_ref: flagNotificationRef,
        is_cycle_resetting: isCycleResetting,
        cycle_reset_reason: cycleResetReason,
      });
      toast({ title: 'External closure confirmed' });
    } catch (closeoutError) {
      toast({
        variant: 'destructive',
        title: 'External closure not confirmed',
        description: getErrorMessage(closeoutError),
      });
    }
  };

  const saveCertLinks = async () => {
    try {
      await editLinks.mutateAsync({
        linked_cert_ids: splitCerts(certText),
        reason: linkReason,
      });
      toast({ title: 'Certificate links updated' });
    } catch (linkError) {
      toast({
        variant: 'destructive',
        title: 'Certificate links not updated',
        description: getErrorMessage(linkError),
      });
    }
  };

  return (
    <RootLayout>
      <PageHeader title="External Audit" showBack backTo="/audit/plans" />
      <div className="mx-auto max-w-5xl space-y-4 p-4">
        <Card>
          <CardContent className="grid gap-4 p-4 md:grid-cols-[1.4fr_1fr_1fr]">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-semibold text-neutral-900">External Audit Close-out</h1>
                <Badge variant={audit.status === 'DPA_CLOSED' ? 'success' : 'secondary'}>
                  {getStatusLabel(audit.external_closure_status || audit.status)}
                </Badge>
              </div>
              <p className="mt-1 text-sm text-neutral-500">
                {formatExternalAuditDefinition(audit)}
              </p>
            </div>
            <HeaderDatum label="Vessel" value={audit.inspection.vessel_id} />
            <HeaderDatum label="Report" value={audit.inspection.report_reference || '-'} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>External Audit Definition</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <ReadOnlyField label="External lead auditor" value={audit.external_lead_auditor_name || audit.lead_auditor_name} />
            <ReadOnlyField label="Auditor credential" value={audit.external_lead_auditor_credential || audit.lead_auditor_qual || '-'} />
            <ReadOnlyField label="Flag state" value={audit.flag_state_code || '-'} />
            <ReadOnlyField label="Linked certificates" value={initialCertText || '-'} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Close-out</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2" data-eid="MOCKUP-EXT-08:ext_close.cert_impact">
                <Label htmlFor="certificate_impact">Certificate impact</Label>
                <select
                  id="certificate_impact"
                  value={certificateImpact}
                  onChange={(event) => setCertificateImpact(event.target.value as (typeof certificateImpacts)[number])}
                  className="h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                >
                  {certificateImpacts.map((impact) => (
                    <option key={impact} value={impact}>{formatEnumLabel(impact)}</option>
                  ))}
                </select>
              </div>
              <ReadOnlyField label="External close-out letter" value={`Required attachment: ${formatEnumLabel('EXTERNAL_CLOSE_OUT_LETTER')}`} />
            </div>

            {suspended && (
              <div className="rounded-md border border-warning-100 bg-warning-50 p-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-warning-700">
                  <AlertTriangle className="h-4 w-4" />
                  Suspended requires cert confirmation and flag notification.
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  <Field label="Typed certificate number" value={typedCertNumber} onChange={setTypedCertNumber} />
                  <Field label="Flag notified to" value={flagNotifiedTo} onChange={setFlagNotifiedTo} />
                  <Field label="Flag notification ref" value={flagNotificationRef} onChange={setFlagNotificationRef} />
                </div>
              </div>
            )}

            <label className="flex items-center gap-2 text-sm text-neutral-700">
              <Checkbox checked={isCycleResetting} onCheckedChange={(checked) => setIsCycleResetting(Boolean(checked))} />
              Cycle-resetting external event
            </label>
            {isCycleResetting && (
              <div className="space-y-2">
                <Label htmlFor="cycle_reset_reason">Cycle reset reason</Label>
                <Textarea id="cycle_reset_reason" value={cycleResetReason} onChange={(event) => setCycleResetReason(event.target.value)} rows={4} />
                <p className={cycleResetReason.length >= 100 ? 'text-xs text-success-700' : 'text-xs text-neutral-500'}>
                  {cycleResetReason.length}/100 characters
                </p>
              </div>
            )}

            <div className="flex justify-end">
              <Button type="button" onClick={confirmCloseout} disabled={closeout.isPending}>
                {closeout.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-2 h-4 w-4" />}
                Confirm external closure
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Post-closure Certs Link Edit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Field label="Linked certificate UUIDs" value={certText} onChange={setLinkedCertText} />
            <div className="space-y-2">
              <Label htmlFor="link_reason">Edit reason</Label>
              <Textarea id="link_reason" value={linkReason} onChange={(event) => setLinkReason(event.target.value)} rows={3} />
              <p className={linkReason.length >= 50 ? 'text-xs text-success-700' : 'text-xs text-neutral-500'}>
                {linkReason.length}/50 characters
              </p>
            </div>
            <div className="flex justify-end">
              <Button type="button" variant="outline" onClick={saveCertLinks} disabled={editLinks.isPending}>
                {editLinks.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                Save Certs link edit
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </RootLayout>
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

function formatExternalAuditDefinition(audit: {
  external_audit_org_type?: string | null;
  external_audit_subtypes?: string[] | null;
  audit_subtype?: string | null;
}) {
  const orgType = formatEnumLabel(audit.external_audit_org_type) || 'External org';
  const subtypes = audit.external_audit_subtypes?.length
    ? audit.external_audit_subtypes.map(formatEnumLabel).join(', ')
    : formatEnumLabel(audit.audit_subtype);

  return [orgType, subtypes].filter(Boolean).join(' - ') || 'External audit';
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <div className="min-h-10 rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-800">
        {value || '-'}
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const id = label.toLowerCase().replace(/[^a-z0-9]+/g, '_');
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}
