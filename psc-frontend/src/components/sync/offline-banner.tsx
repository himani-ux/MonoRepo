/**
 * OfflineBanner component — shown in root layout when device is offline.
 *
 * Displays "Offline - Showing cached data" with last sync time.
 * Per APP_FLOW.md Section 2.2 offline indicator spec.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3
 * Implements: PRD.md FEAT-SYNC-001
 * Flow: APP_FLOW.md Section 2.2
 */

import { type FC } from 'react';
import { WifiOff } from 'lucide-react';

export interface OfflineBannerProps {
  /** Whether the device is currently online. */
  isOnline: boolean;
  /** ISO timestamp of last successful sync, or null. */
  lastSyncTime: string | null;
}

function formatShortTime(isoTime: string | null): string {
  if (!isoTime) return '';
  try {
    const date = new Date(isoTime);
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

export const OfflineBanner: FC<OfflineBannerProps> = ({
  isOnline,
  lastSyncTime,
}) => {
  if (isOnline) return null;

  const timeStr = formatShortTime(lastSyncTime);

  return (
    <div className="flex items-center justify-center gap-2 bg-warning-500 px-4 py-1.5 text-white">
      <WifiOff className="h-3.5 w-3.5" />
      <span className="text-xs font-medium">
        Offline — Showing cached data
        {timeStr && (
          <span className="ml-1 font-normal opacity-90">
            (Last sync: {timeStr})
          </span>
        )}
      </span>
    </div>
  );
};
