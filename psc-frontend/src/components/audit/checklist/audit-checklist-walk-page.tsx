import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { AlertCircle, ArrowLeft, CheckSquare, FilePlus2, ListChecks } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Label, Textarea } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import { useAuditChecklist } from '@/hooks/audit/use-audit-checklist';
import { useAuditDetail } from '@/hooks/audit/use-audit-registration';
import { useChecklistWalkStore } from '@/stores/audit/use-checklist-walk-store';
import type { AuditChecklist, AuditChecklistItem, AuditChecklistWalkStatus } from '@/schemas/audit/checklist';
import { ROUTES } from '@/lib/utils/constants';
import { cn } from '@/lib/utils';
import { AuditFindingCreateModal } from './audit-finding-create-modal';

interface AuditChecklistWalkPageProps {
  auditId: string;
}

const statusOptions: Array<{ value: AuditChecklistWalkStatus; label: string }> = [
  { value: 'NOT_REVIEWED', label: 'Not reviewed' },
  { value: 'COMPLIANT', label: 'Compliant' },
  { value: 'ADD_FINDING', label: 'Add Finding' },
];

export function AuditChecklistWalkPage({ auditId }: AuditChecklistWalkPageProps) {
  const { data, isLoading, error, refetch } = useAuditChecklist(auditId);
  const { data: auditDetail } = useAuditDetail(auditId);
  const { items: walkItems, resetForItems, setItemStatus, setItemRemarks } = useChecklistWalkStore();
  const [findingItem, setFindingItem] = useState<AuditChecklistItem | null>(null);
  const [findingModalOpen, setFindingModalOpen] = useState(false);

  useEffect(() => {
    if (!data) return;
    resetForItems(auditId, data.items.map((item) => item.id));
  }, [auditId, data, resetForItems]);

  const counts = useMemo(() => {
    const states = Object.values(walkItems);
    return {
      compliant: states.filter((item) => item.status === 'COMPLIANT').length,
      findings: states.filter((item) => item.status === 'ADD_FINDING').length,
      reviewed: states.filter((item) => item.status !== 'NOT_REVIEWED').length,
    };
  }, [walkItems]);
  const acceptsFindings = (auditDetail?.status ?? 'IN_PROGRESS') === 'IN_PROGRESS';

  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Audit Checklist" showBack backTo={`/audit/audits/${auditId}`} />
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
        <PageHeader title="Audit Checklist" showBack backTo={`/audit/audits/${auditId}`} />
        <ErrorState
          title="Checklist not available"
          message="The audit checklist could not be loaded."
          onRetry={() => refetch()}
        />
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <PageHeader
        title="Audit Checklist"
        showBack
        backTo={`/audit/audits/${auditId}`}
        actions={
          <Button asChild variant="outline" size="sm">
            <Link to={`/audit/audits/${auditId}`}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Audit Detail
            </Link>
          </Button>
        }
      />

      <div className="space-y-4 p-4">
        <ChecklistHeader data={data} counts={counts} />

        {!data.selected ? (
          <div className="rounded-md border border-warning-100 bg-warning-50 p-4 text-sm text-warning-700" role="status">
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-none" />
              <p>No active checklist matched this audit classification.</p>
            </div>
          </div>
        ) : null}
        {!acceptsFindings ? (
          <div className="rounded-md border border-neutral-200 bg-neutral-50 p-4 text-sm text-neutral-700" role="status">
            Findings are frozen for finalized audits. Late issues require a separate unscheduled audit.
          </div>
        ) : null}

        <Card data-eid="MOCKUP-CHECKLIST-03:checklist_walk.item_rows">
          <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle>Checklist Items</CardTitle>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <span className="text-sm text-neutral-500">{counts.reviewed}/{data.items.length} reviewed</span>
              {acceptsFindings ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setFindingItem(null);
                    setFindingModalOpen(true);
                  }}
                >
                  <FilePlus2 className="mr-2 h-4 w-4" />
                  Add Emergent Finding
                </Button>
              ) : null}
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.items.length ? (
              data.items.map((item) => (
                <ChecklistItemRow
                  key={item.id}
                  item={item}
                  status={walkItems[item.id]?.status ?? 'NOT_REVIEWED'}
                  remarks={walkItems[item.id]?.remarks ?? ''}
                  onStatusChange={(status) => setItemStatus(item.id, status)}
                  onRemarksChange={(remarks) => setItemRemarks(item.id, remarks)}
                  acceptsFindings={acceptsFindings}
                  onAddFinding={() => {
                    setFindingItem(item);
                    setFindingModalOpen(true);
                  }}
                />
              ))
            ) : (
              <div className="rounded-md border border-neutral-200 bg-neutral-50 p-6 text-center text-sm text-neutral-500">
                No checklist rows available.
              </div>
            )}
          </CardContent>
        </Card>
        <AuditFindingCreateModal
          auditId={auditId}
          open={findingModalOpen}
          checklistItem={findingItem}
          onOpenChange={setFindingModalOpen}
        />
      </div>
    </RootLayout>
  );
}

function ChecklistHeader({
  data,
  counts,
}: {
  data: AuditChecklist;
  counts: { compliant: number; findings: number; reviewed: number };
}) {
  return (
    <Card>
      <CardContent className="grid gap-4 p-4 lg:grid-cols-[1.5fr_auto_auto_auto]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold text-neutral-900">
              {data.checklist?.name ?? 'Checklist not selected'}
            </h1>
            {data.checklist ? <Badge variant="secondary">{data.checklist.source_form_ref}</Badge> : null}
          </div>
          <p className="mt-1 text-sm text-neutral-500">
            {data.checklist?.checklist_code ?? 'No checklist'} - {data.checklist?.code_version ?? 'version not recorded'}
          </p>
          {data.item_filter_applied ? (
            <p className="mt-1 text-sm text-neutral-500">Ship type: {data.ship_type_filter}</p>
          ) : null}
        </div>
        <HeaderCount icon={<ListChecks className="h-4 w-4" />} label="Rows" value={String(data.items.length)} />
        <HeaderCount icon={<CheckSquare className="h-4 w-4" />} label="Compliant" value={String(counts.compliant)} />
        <HeaderCount icon={<FilePlus2 className="h-4 w-4" />} label="Findings Marked" value={String(counts.findings)} />
      </CardContent>
    </Card>
  );
}

function HeaderCount({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2">
      <div className="flex items-center gap-2 text-sm font-medium text-neutral-800">
        {icon}
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold text-neutral-900">{value}</div>
    </div>
  );
}

function ChecklistItemRow({
  item,
  status,
  remarks,
  onStatusChange,
  onRemarksChange,
  acceptsFindings,
  onAddFinding,
}: {
  item: AuditChecklistItem;
  status: AuditChecklistWalkStatus;
  remarks: string;
  onStatusChange: (status: AuditChecklistWalkStatus) => void;
  onRemarksChange: (remarks: string) => void;
  acceptsFindings: boolean;
  onAddFinding: () => void;
}) {
  const statusId = `checklist-status-${item.id}`;
  const remarksId = `checklist-remarks-${item.id}`;
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px]">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-neutral-500">
            <span className="font-mono">{item.sequence_no}</span>
            {item.location_code ? <span>{item.location_code}</span> : null}
            <span>{item.item_code}</span>
            {item.ship_type ? <Badge variant="secondary">{item.ship_type}</Badge> : null}
          </div>
          <p className="mt-2 text-sm font-medium text-neutral-900">{item.question}</p>
          {item.guideline ? <p className="mt-2 text-sm text-neutral-600">{item.guideline}</p> : null}
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-neutral-500">
            {item.regulation_ref ? <span>{item.regulation_ref}</span> : null}
            {item.ksm_sms_ref ? <span>{item.ksm_sms_ref}</span> : null}
          </div>
        </div>
        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor={statusId}>Item status</Label>
            <select
              id={statusId}
              aria-label={`${item.item_code} status`}
              className={cn(
                'h-10 w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm text-neutral-800',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2'
              )}
              value={status}
              onChange={(event) => onStatusChange(event.target.value as AuditChecklistWalkStatus)}
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor={remarksId}>Remarks</Label>
            <Textarea
              id={remarksId}
              aria-label={`${item.item_code} remarks`}
              value={remarks}
              rows={3}
              onChange={(event) => onRemarksChange(event.target.value)}
            />
          </div>
          <Button
            type="button"
            variant="outline"
            className="w-full"
            disabled={!acceptsFindings || status !== 'ADD_FINDING'}
            onClick={onAddFinding}
          >
            <FilePlus2 className="mr-2 h-4 w-4" />
            Add Finding
          </Button>
        </div>
      </div>
    </div>
  );
}
