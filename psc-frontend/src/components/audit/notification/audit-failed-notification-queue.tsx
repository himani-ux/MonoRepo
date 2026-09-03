import { useState } from 'react';
import { CheckCircle2, Loader2, RefreshCw } from 'lucide-react';
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Label, Textarea } from '@/components/ui';
import { PageHeader } from '@/components/layout/page-header';
import { RootLayout } from '@/components/layout/root-layout';
import { ErrorState } from '@/components/shared';
import { SectionSkeleton } from '@/components/shared/loading-skeleton';
import { useToast } from '@/hooks/use-toast';
import {
  useFailedAuditNotifications,
  useMarkAuditNotificationOffline,
  useRetryAuditNotification,
} from '@/hooks/audit/use-audit-notification';
import { getErrorMessage } from '@/lib/api/client';
import { formatEnumLabel } from '@/lib/utils/format-status';
import {
  AUDIT_NOTIFICATION_OFFLINE_REASON_MIN,
  type AuditNotificationDelivery,
} from '@/schemas/audit/notification';

function channelVariant(channel: string) {
  if (channel === 'EMAIL') return 'secondary';
  if (channel === 'SLACK') return 'warning';
  return 'outline';
}

export function AuditFailedNotificationQueue() {
  const { toast } = useToast();
  const { data, isLoading, error, refetch } = useFailedAuditNotifications();
  const retryNotification = useRetryAuditNotification();
  const markOffline = useMarkAuditNotificationOffline();
  const [offlineRow, setOfflineRow] = useState<AuditNotificationDelivery | null>(null);
  const [offlineReason, setOfflineReason] = useState('');
  const [reasonError, setReasonError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Failed Notifications" />
        <div className="space-y-4 p-4">
          <SectionSkeleton />
        </div>
      </RootLayout>
    );
  }

  if (error || !data) {
    return (
      <RootLayout>
        <PageHeader title="Failed Notifications" />
        <ErrorState
          title="Failed notifications not available"
          message="The failed-notification queue may be unavailable or you may not have access."
          onRetry={() => refetch()}
        />
      </RootLayout>
    );
  }

  const retryRow = async (row: AuditNotificationDelivery) => {
    try {
      await retryNotification.mutateAsync(row.id);
      toast({ title: 'Notification queued for retry' });
      if (offlineRow?.id === row.id) {
        setOfflineRow(null);
        setOfflineReason('');
      }
    } catch (retryError) {
      toast({
        variant: 'destructive',
        title: 'Notification retry not queued',
        description: getErrorMessage(retryError),
      });
    }
  };

  const startOfflineResolution = (row: AuditNotificationDelivery) => {
    setOfflineRow(row);
    setOfflineReason('');
    setReasonError(null);
  };

  const submitOfflineResolution = async () => {
    if (!offlineRow) return;
    const trimmedReason = offlineReason.trim();
    if (trimmedReason.length < AUDIT_NOTIFICATION_OFFLINE_REASON_MIN) {
      setReasonError(`Reason must be at least ${AUDIT_NOTIFICATION_OFFLINE_REASON_MIN} characters.`);
      return;
    }
    try {
      await markOffline.mutateAsync({ id: offlineRow.id, data: { reason: trimmedReason } });
      toast({ title: 'Notification marked notified offline' });
      setOfflineRow(null);
      setOfflineReason('');
      setReasonError(null);
    } catch (offlineError) {
      toast({
        variant: 'destructive',
        title: 'Offline resolution not saved',
        description: getErrorMessage(offlineError),
      });
    }
  };

  return (
    <RootLayout>
      <PageHeader title="Failed Notifications" />
      <div className="space-y-4 p-4" data-eid="MOCKUP-DPA-09:dpa_failed.rows">
        <Card>
          <CardHeader>
            <CardTitle>Failed notifications</CardTitle>
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
                    <th className="px-3 py-2">Notification</th>
                    <th className="px-3 py-2">Channel</th>
                    <th className="px-3 py-2">Recipient</th>
                    <th className="px-3 py-2">Last error</th>
                    <th className="px-3 py-2">Attempts</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100 bg-white">
                  {data.results.length ? (
                    data.results.map((row) => (
                      <tr key={row.id}>
                        <td className="px-3 py-2">
                          <div className="font-medium text-neutral-900">{formatEnumLabel(row.notification_type || 'AUDIT_NOTIFICATION')}</div>
                          <div className="text-xs text-neutral-500">{row.title || formatEnumLabel(row.entity_type) || row.psc_notification_id}</div>
                        </td>
                        <td className="px-3 py-2">
                          <Badge variant={channelVariant(row.channel)}>{formatEnumLabel(row.channel)}</Badge>
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">
                          {row.recipient_address || row.recipient_id || '-'}
                        </td>
                        <td className="px-3 py-2">
                          <span className="font-mono text-xs text-error-700">{row.last_error || '-'}</span>
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">{row.attempt_count}</td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-2">
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => retryRow(row)}
                              disabled={retryNotification.isPending}
                            >
                              {retryNotification.isPending ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              ) : (
                                <RefreshCw className="mr-2 h-4 w-4" />
                              )}
                              Retry
                            </Button>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              onClick={() => startOfflineResolution(row)}
                              disabled={markOffline.isPending}
                            >
                              <CheckCircle2 className="mr-2 h-4 w-4" />
                              Mark notified offline
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="px-3 py-6 text-center text-neutral-500">
                        No failed notifications.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {offlineRow && (
          <Card>
            <CardHeader>
              <CardTitle>Offline notification resolution</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 text-sm text-neutral-700 sm:grid-cols-3">
                <div>
                  <p className="text-xs font-medium uppercase text-neutral-500">Notification</p>
                  <p className="font-medium text-neutral-900">{formatEnumLabel(offlineRow.notification_type || 'AUDIT_NOTIFICATION')}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-neutral-500">Channel</p>
                  <p>{formatEnumLabel(offlineRow.channel)}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase text-neutral-500">Recipient</p>
                  <p className="font-mono text-xs">{offlineRow.recipient_address || offlineRow.recipient_id || '-'}</p>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="offline-resolution-reason">Offline resolution reason</Label>
                <Textarea
                  id="offline-resolution-reason"
                  rows={4}
                  value={offlineReason}
                  onChange={(event) => {
                    setOfflineReason(event.target.value);
                    setReasonError(null);
                  }}
                />
                {reasonError && <p className="text-sm text-error-700">{reasonError}</p>}
              </div>
              <div className="flex flex-wrap justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setOfflineRow(null)}>
                  Cancel
                </Button>
                <Button type="button" onClick={submitOfflineResolution} disabled={markOffline.isPending}>
                  {markOffline.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Save offline resolution
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </RootLayout>
  );
}
