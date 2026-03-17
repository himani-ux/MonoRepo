/**
 * Notification list component with date grouping.
 *
 * Per APP_FLOW.md Section 2.6:
 * - Groups by TODAY / YESTERDAY / EARLIER
 * - Handles loading, empty, and error states
 * - Supports pagination via "Load more"
 */

import type { FC } from 'react';
import { isToday, isYesterday, parseISO } from 'date-fns';
import type { Notification } from '@/types';
import { NotificationItem } from './notification-item';
import { EmptyStateNotifications } from '@/components/shared/empty-state';
import { ErrorState } from '@/components/shared/error-state';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';

// ============================================================================
// Date Grouping Logic
// ============================================================================

interface NotificationGroup {
  label: string;
  notifications: Notification[];
}

function groupByDate(notifications: Notification[]): NotificationGroup[] {
  const today: Notification[] = [];
  const yesterday: Notification[] = [];
  const earlier: Notification[] = [];

  for (const n of notifications) {
    try {
      const date = parseISO(n.created_date);
      if (isToday(date)) {
        today.push(n);
      } else if (isYesterday(date)) {
        yesterday.push(n);
      } else {
        earlier.push(n);
      }
    } catch {
      earlier.push(n);
    }
  }

  const groups: NotificationGroup[] = [];
  if (today.length > 0) groups.push({ label: 'Today', notifications: today });
  if (yesterday.length > 0) groups.push({ label: 'Yesterday', notifications: yesterday });
  if (earlier.length > 0) groups.push({ label: 'Earlier', notifications: earlier });

  return groups;
}

// ============================================================================
// Component
// ============================================================================

export interface NotificationListProps {
  notifications: Notification[];
  isLoading: boolean;
  isError: boolean;
  error?: Error | null;
  onRetry?: () => void;
  onMarkRead?: (id: string) => void;
  hasMore?: boolean;
  onLoadMore?: () => void;
  isLoadingMore?: boolean;
}

export const NotificationList: FC<NotificationListProps> = ({
  notifications,
  isLoading,
  isError,
  error,
  onRetry,
  onMarkRead,
  hasMore,
  onLoadMore,
  isLoadingMore,
}) => {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <ErrorState
        title="Failed to load notifications"
        message={error?.message || 'An error occurred while loading notifications.'}
        onRetry={onRetry}
      />
    );
  }

  if (notifications.length === 0) {
    return <EmptyStateNotifications />;
  }

  const groups = groupByDate(notifications);

  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <div key={group.label}>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
            {group.label}
          </h3>
          <div className="space-y-2">
            {group.notifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onMarkRead={onMarkRead}
              />
            ))}
          </div>
        </div>
      ))}

      {hasMore && onLoadMore && (
        <div className="flex justify-center pt-2">
          <Button
            variant="outline"
            onClick={onLoadMore}
            disabled={isLoadingMore}
          >
            {isLoadingMore ? 'Loading...' : 'Load more'}
          </Button>
        </div>
      )}
    </div>
  );
};
