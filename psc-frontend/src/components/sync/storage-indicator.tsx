/**
 * StorageIndicator component — shows IndexedDB storage usage.
 *
 * Displays a progress bar with usage vs 150MB limit,
 * plus a warning banner when < 10MB remaining.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3
 * Implements: PRD.md FEAT-SYNC-001
 * Flow: APP_FLOW.md Section 2.5
 */

import { type FC, useState, useEffect } from 'react';
import { HardDrive, AlertTriangle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import {
  getStorageEstimate,
  STORAGE_LIMIT_BYTES,
  STORAGE_WARNING_BYTES,
} from '@/lib/db';
import { cn } from '@/lib/utils';

export interface StorageIndicatorProps {
  /** Optional className for the card. */
  className?: string;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const StorageIndicator: FC<StorageIndicatorProps> = ({ className }) => {
  const [usage, setUsage] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function fetchStorage() {
      try {
        const estimate = await getStorageEstimate();
        if (mounted && estimate) {
          setUsage(estimate.usage);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchStorage();
    return () => { mounted = false; };
  }, []);

  const percentage = Math.min((usage / STORAGE_LIMIT_BYTES) * 100, 100);
  const remaining = STORAGE_LIMIT_BYTES - usage;
  const isNearlyFull = remaining < STORAGE_WARNING_BYTES;

  return (
    <Card className={className}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <HardDrive className="h-4 w-4 text-neutral-500" />
          <h3 className="text-sm font-medium text-neutral-900">Storage</h3>
        </div>

        {loading ? (
          <div className="h-4 w-full animate-pulse rounded bg-neutral-100" />
        ) : (
          <>
            {/* Progress bar */}
            <div className="h-3 w-full overflow-hidden rounded-full bg-neutral-100">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-300',
                  isNearlyFull ? 'bg-error-500' : percentage > 70 ? 'bg-warning-500' : 'bg-primary-500'
                )}
                style={{ width: `${percentage}%` }}
              />
            </div>
            <p className="mt-1.5 text-xs text-neutral-500">
              {formatBytes(usage)} / {formatBytes(STORAGE_LIMIT_BYTES)}
            </p>

            {/* Warning banner when < 10MB remaining */}
            {isNearlyFull && (
              <div className="mt-3 flex items-start gap-2 rounded-md bg-warning-50 p-3">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning-600" />
                <div>
                  <p className="text-xs font-medium text-warning-800">
                    Storage nearly full ({formatBytes(remaining)} remaining)
                  </p>
                  <p className="mt-0.5 text-xs text-warning-700">
                    Please connect to internet and sync to free up space.
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};
