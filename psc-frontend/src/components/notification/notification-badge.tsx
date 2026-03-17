/**
 * Notification badge component.
 *
 * Shows unread notification count.
 * Used in the header bell icon.
 */

import type { FC } from 'react';
import { cn } from '@/lib/utils';

export interface NotificationBadgeProps {
  count: number;
  className?: string;
}

export const NotificationBadge: FC<NotificationBadgeProps> = ({
  count,
  className,
}) => {
  if (count <= 0) return null;

  return (
    <span
      className={cn(
        'absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-xs font-medium text-white',
        className
      )}
    >
      {count > 99 ? '99+' : count}
    </span>
  );
};
