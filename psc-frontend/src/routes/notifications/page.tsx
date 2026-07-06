/**
 * Notification Center page.
 *
 * Route: /notifications
 * Per APP_FLOW.md Section 2.6 and IMPLEMENTATION_PLAN.md Step 8.2
 *
 * Features:
 * - Paginated notification list grouped by date (TODAY / YESTERDAY / EARLIER)
 * - Mark All Read button
 * - Accumulated load-more pagination
 * - All authenticated users
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { NotificationList } from '@/components/notification/notification-list';
import { Button } from '@/components/ui/button';
import {
  useNotifications,
  useMarkRead,
  useMarkAllRead,
} from '@/hooks/use-notifications';
import { useToast } from '@/hooks/use-toast';
import type { Notification } from '@/types';

const PAGE_SIZE = 20;

export default function NotificationsPage() {
  const [searchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [accumulated, setAccumulated] = useState<Notification[]>([]);
  const prevDataRef = useRef<Notification[] | null>(null);
  const { toast } = useToast();

  const moduleFilter = searchParams.get('module') === 'certs' ? 'certs' : undefined;

  const { data, isLoading, isError, error, refetch } = useNotifications({
    page,
    pageSize: PAGE_SIZE,
    module: moduleFilter,
  });

  // Accumulate notifications across pages
  useEffect(() => {
    if (!data?.data || data.data === prevDataRef.current) return;
    prevDataRef.current = data.data;

    if (page === 1) {
      setAccumulated(data.data);
    } else {
      setAccumulated((prev) => {
        const existingIds = new Set(prev.map((n) => n.id));
        const newItems = data.data.filter((n) => !existingIds.has(n.id));
        return [...prev, ...newItems];
      });
    }
  }, [data, page]);

  const hasMore = data ? page < data.pagination.total_pages : false;

  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();

  const handleMarkRead = useCallback(
    (id: string) => {
      markRead.mutate([id]);
    },
    [markRead]
  );

  const handleMarkAllRead = () => {
    markAllRead.mutate(undefined, {
      onSuccess: (result) => {
        toast.success({
          title: 'All read',
          description: `${result.data.marked_count} notification(s) marked as read.`,
        });
      },
      onError: () => {
        toast.error({
          title: 'Error',
          description: 'Failed to mark notifications as read.',
        });
      },
    });
  };

  const handleLoadMore = () => {
    setPage((p) => p + 1);
  };

  const unreadCount = accumulated.filter((n) => !n.is_read).length;

  return (
    <RootLayout>
      <PageHeader
        title="Notifications"
        actions={
          unreadCount > 0 ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleMarkAllRead}
              disabled={markAllRead.isPending}
            >
              {markAllRead.isPending ? 'Marking...' : 'Mark All Read'}
            </Button>
          ) : undefined
        }
      />

      <div className="mx-auto max-w-2xl px-4 pb-20 pt-4">
        <NotificationList
          notifications={accumulated}
          isLoading={isLoading && page === 1}
          isError={isError}
          error={error}
          onRetry={() => refetch()}
          onMarkRead={handleMarkRead}
          hasMore={hasMore}
          onLoadMore={handleLoadMore}
          isLoadingMore={isLoading && page > 1}
        />
      </div>
    </RootLayout>
  );
}
