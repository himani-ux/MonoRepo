import { useState } from 'react';
import { CheckCircle2, Loader2, RefreshCw, RotateCcw } from 'lucide-react';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Label, Textarea } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import { useToast } from '@/hooks/use-toast';
import {
  useAuditScanValidationAction,
  useAuditScanValidationQueue,
} from '@/hooks/audit/use-audit-scan-validation';
import { getErrorMessage } from '@/lib/api/client';
import {
  AUDIT_SCAN_ACCEPT_REASON_MIN,
  type AuditScanValidationAttachment,
} from '@/schemas/audit/scan-validation';

function statusVariant(status: string | null) {
  if (status === 'MISMATCH_VESSEL' || status === 'UNREADABLE') return 'destructive';
  if (status === 'MISMATCH_FINDING' || status === 'MISMATCH_VERSION') return 'warning';
  return 'outline';
}

export function AuditScanValidationQueue() {
  const { toast } = useToast();
  const { data, isLoading, error, refetch } = useAuditScanValidationQueue();
  const scanAction = useAuditScanValidationAction();
  const [selectedRow, setSelectedRow] = useState<AuditScanValidationAttachment | null>(null);
  const [actionMode, setActionMode] = useState<'ACCEPT_WITH_REASON' | 'REJECT_RESCAN' | null>(null);
  const [reason, setReason] = useState('');
  const [reasonError, setReasonError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Scan Validation Queue" />
        <div className="space-y-4 p-4">
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  if (error || !data) {
    return (
      <RootLayout>
        <PageHeader title="Scan Validation Queue" />
        <ErrorState
          title="Scan validation queue not available"
          message="The scan-validation queue may be unavailable or you may not have access."
          onRetry={() => refetch()}
        />
      </RootLayout>
    );
  }

  const startAction = (
    row: AuditScanValidationAttachment,
    mode: 'ACCEPT_WITH_REASON' | 'REJECT_RESCAN'
  ) => {
    setSelectedRow(row);
    setActionMode(mode);
    setReason('');
    setReasonError(null);
  };

  const submitAction = async () => {
    if (!selectedRow || !actionMode) return;
    const trimmedReason = reason.trim();
    if (actionMode === 'ACCEPT_WITH_REASON' && trimmedReason.length < AUDIT_SCAN_ACCEPT_REASON_MIN) {
      setReasonError(`Accept reason must be at least ${AUDIT_SCAN_ACCEPT_REASON_MIN} characters.`);
      return;
    }
    try {
      await scanAction.mutateAsync({
        id: selectedRow.id,
        data: { action: actionMode, reason: trimmedReason },
      });
      toast({
        title: actionMode === 'ACCEPT_WITH_REASON' ? 'Scan mismatch accepted' : 'Rescan requested',
      });
      setSelectedRow(null);
      setActionMode(null);
      setReason('');
      setReasonError(null);
    } catch (actionError) {
      toast({
        variant: 'destructive',
        title: 'Scan validation action not saved',
        description: getErrorMessage(actionError),
      });
    }
  };

  return (
    <RootLayout>
      <PageHeader title="Scan Validation Queue" />
      <div className="space-y-4 p-4" data-eid="MOCKUP-DPA-09:dpa_scan.rows">
        <Card>
          <CardHeader>
            <CardTitle>Scan-validation queue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-2">
                <p className="text-xs font-medium uppercase text-neutral-500">Queue rows</p>
                <p className="text-xl font-semibold text-neutral-900">{data.count}</p>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>

            <div className="overflow-x-auto rounded-lg border border-neutral-200">
              <table className="min-w-full divide-y divide-neutral-200 text-sm">
                <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                  <tr>
                    <th className="px-3 py-2">Uploaded scan</th>
                    <th className="px-3 py-2">Finding</th>
                    <th className="px-3 py-2">QR / hash status</th>
                    <th className="px-3 py-2">Validator message</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 bg-white">
                  {data.results.length ? (
                    data.results.map((row) => (
                      <tr key={row.id}>
                        <td className="px-3 py-2">
                          <div className="font-medium text-neutral-900">{row.file_name}</div>
                          <div className="font-mono text-xs text-neutral-500">{row.category}</div>
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">
                          {row.audit_finding_id || row.audit_detail_id}
                        </td>
                        <td className="px-3 py-2">
                          <Badge variant={statusVariant(row.pdf_hash_validation_status)}>
                            {row.pdf_hash_validation_status || 'UNVALIDATED'}
                          </Badge>
                        </td>
                        <td className="px-3 py-2 text-xs text-neutral-600">
                          {row.validator_message || '-'}
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => startAction(row, 'ACCEPT_WITH_REASON')}
                              disabled={scanAction.isPending}
                            >
                              <CheckCircle2 className="mr-2 h-4 w-4" />
                              Accept w/ reason
                            </Button>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => startAction(row, 'REJECT_RESCAN')}
                              disabled={scanAction.isPending}
                            >
                              <RotateCcw className="mr-2 h-4 w-4" />
                              Reject - rescan
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="px-3 py-6 text-center text-neutral-500">
                        No scan mismatches or unreadable uploads.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {selectedRow && actionMode && (
          <Card>
            <CardHeader>
              <CardTitle>
                {actionMode === 'ACCEPT_WITH_REASON' ? 'Accept scan mismatch' : 'Reject and request rescan'}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 text-sm text-neutral-700 sm:grid-cols-3">
                <div>
                  <p className="text-xs font-medium uppercase text-neutral-500">Uploaded scan</p>
                  <p className="font-medium text-neutral-900">{selectedRow.file_name}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-neutral-500">Status</p>
                  <p>{selectedRow.pdf_hash_validation_status || 'UNVALIDATED'}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-neutral-500">Uploaded by</p>
                  <p className="font-mono text-xs">{selectedRow.uploaded_by}</p>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="scan-validation-reason">DPA reason</Label>
                <Textarea
                  id="scan-validation-reason"
                  rows={4}
                  value={reason}
                  onChange={(event) => {
                    setReason(event.target.value);
                    setReasonError(null);
                  }}
                />
                {reasonError && <p className="text-sm text-error-700">{reasonError}</p>}
              </div>
              <div className="flex flex-wrap justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setSelectedRow(null)}>
                  Cancel
                </Button>
                <Button type="button" onClick={submitAction} disabled={scanAction.isPending}>
                  {scanAction.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {actionMode === 'ACCEPT_WITH_REASON' ? 'Save acceptance' : 'Request rescan'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </RootLayout>
  );
}
