/**
 * SyncStatus component — displays connection status and last sync time.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3
 * Implements: PRD.md FEAT-SYNC-001
 * Flow: APP_FLOW.md Section 2.5
 */

import { type FC } from 'react';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import { cn } from '@/lib/utils';

export interface SyncStatusProps {
  /** Whether the device is currently online. */
  isOnline: boolean;
  /** ISO timestamp of last successful sync, or null. */
  lastSyncTime: string | null;
  /** Whether a sync is currently in progress. */
  syncInProgress: boolean;
  /** Last sync error message, if any. */
  lastSyncError: string | null;
}

function formatLastSync(isoTime: string | null): string {
  if (!isoTime) return 'Never synced';
  try {
    const date = new Date(isoTime);
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'Unknown';
  }
}

export const SyncStatus: FC<SyncStatusProps> = ({
  isOnline,
  lastSyncTime,
  syncInProgress,
  lastSyncError,
}) => {
  return (
    <Card>
      <CardContent className="p-4">
        {/* Connection status */}
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-full',
              isOnline ? 'bg-success-50 text-success-600' : 'bg-neutral-100 text-neutral-400'
            )}
          >
            {isOnline ? (
              <Wifi className="h-5 w-5" />
            ) : (
              <WifiOff className="h-5 w-5" />
            )}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'h-2.5 w-2.5 rounded-full',
                  isOnline ? 'bg-success-500' : 'bg-neutral-400'
                )}
              />
              <span className="text-sm font-medium text-neutral-900">
                Connection: {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-neutral-500">
              {syncInProgress
                ? 'Syncing...'
                : `Last Sync: ${formatLastSync(lastSyncTime)}`}
            </p>
          </div>
        </div>

        {/* Sync error */}
        {lastSyncError && (
          <div className="mt-3 flex items-start gap-2 rounded-md bg-error-50 p-3">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-error-500" />
            <p className="text-xs text-error-700">{lastSyncError}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
