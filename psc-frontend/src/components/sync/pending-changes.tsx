/**
 * PendingChanges component — shows pending sync queue items and failed uploads.
 *
 * Displays pending mutations waiting to sync and failed items with retry.
 * Hidden sections when empty per APP_FLOW.md spec.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3
 * Implements: PRD.md FEAT-SYNC-001, FEAT-SYNC-003
 * Flow: APP_FLOW.md Section 2.5
 */

import { type FC, useState, useEffect, useCallback } from 'react';
import { Upload, AlertTriangle, RotateCw, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, Button } from '@/components/ui';
import { getPendingSyncQueue, getFailedSyncQueue } from '@/lib/db/sync-queue';
import type { SyncQueueItem } from '@/types';

export interface PendingChangesProps {
  /** Number of pending changes (from sync store). */
  pendingCount: number;
  /** Callback to retry failed items. */
  onRetryFailed?: () => void;
  /** Whether a retry/sync is currently in progress. */
  retryInProgress?: boolean;
}

function getEntityLabel(item: SyncQueueItem): string {
  const typeLabels: Record<string, string> = {
    INSPECTION: 'Inspection',
    CAR: 'CAR',
    DEFICIENCY: 'Deficiency',
    EVIDENCE: 'Evidence',
  };
  const opLabels: Record<string, string> = {
    CREATE: 'created',
    UPDATE: 'updated',
    DELETE: 'deleted',
  };
  const type = typeLabels[item.entity_type] ?? item.entity_type;
  const op = opLabels[item.operation] ?? item.operation.toLowerCase();
  return `${type} ${op}`;
}

export const PendingChanges: FC<PendingChangesProps> = ({
  pendingCount,
  onRetryFailed,
  retryInProgress = false,
}) => {
  const [pendingItems, setPendingItems] = useState<SyncQueueItem[]>([]);
  const [failedItems, setFailedItems] = useState<SyncQueueItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadItems = useCallback(async () => {
    try {
      const [pending, failed] = await Promise.all([
        getPendingSyncQueue(),
        getFailedSyncQueue(),
      ]);
      setPendingItems(pending);
      setFailedItems(failed);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadItems();
  }, [loadItems, pendingCount]);

  const hasPending = pendingItems.length > 0;
  const hasFailed = failedItems.length > 0;

  // All synced — show success state
  if (!loading && !hasPending && !hasFailed) {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Upload className="h-4 w-4 text-neutral-500" />
            <h3 className="text-sm font-medium text-neutral-900">Pending Changes</h3>
          </div>
          <div className="flex items-center gap-2 py-4 text-center justify-center">
            <CheckCircle2 className="h-5 w-5 text-success-500" />
            <p className="text-sm text-neutral-500">All changes synced</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {/* Pending changes */}
      {hasPending && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Upload className="h-4 w-4 text-neutral-500" />
              <h3 className="text-sm font-medium text-neutral-900">Pending Changes</h3>
            </div>
            <p className="mb-2 text-xs text-neutral-500">
              {pendingItems.length} change{pendingItems.length !== 1 ? 's' : ''} waiting to sync
            </p>
            <ul className="space-y-1.5">
              {pendingItems.map((item) => (
                <li
                  key={item.id}
                  className="flex items-center gap-2 text-xs text-neutral-700"
                >
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-primary-400" />
                  {getEntityLabel(item)}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Failed uploads */}
      {hasFailed && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-warning-500" />
                <h3 className="text-sm font-medium text-neutral-900">
                  Failed Uploads
                </h3>
              </div>
              {onRetryFailed && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRetryFailed}
                  disabled={retryInProgress}
                  className="h-7 text-xs"
                >
                  <RotateCw className={`mr-1 h-3 w-3 ${retryInProgress ? 'animate-spin' : ''}`} />
                  Retry
                </Button>
              )}
            </div>
            <p className="mb-2 text-xs text-warning-600">
              {failedItems.length} upload{failedItems.length !== 1 ? 's' : ''} failed
            </p>
            <ul className="space-y-1.5">
              {failedItems.map((item) => (
                <li
                  key={item.id}
                  className="flex items-start gap-2 text-xs"
                >
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-error-400" />
                  <div>
                    <span className="text-neutral-700">{getEntityLabel(item)}</span>
                    {item.error_message && (
                      <span className="ml-1 text-neutral-400">
                        — {item.error_message}
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
