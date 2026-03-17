/**
 * Individual notification item component.
 *
 * Per APP_FLOW.md Section 2.6:
 * - Blue dot (🔵) for unread notifications
 * - Title + timestamp layout
 * - Clickable to navigate to related entity
 */

import { memo, type FC } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileWarning,
  FileCheck,
  AlertTriangle,
  Clock,
  Shield,
  RefreshCw,
  Send,
  CheckCircle2,
  ClipboardCheck,
  UserCheck,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/utils/constants';
import type { Notification, NotificationType } from '@/types';
import { format, parseISO } from 'date-fns';

// ============================================================================
// Icon + Color Mapping
// ============================================================================

interface NotificationStyle {
  icon: LucideIcon;
  iconColor: string;
}

const NOTIFICATION_STYLES: Record<NotificationType, NotificationStyle> = {
  CAR_CREATED: { icon: FileWarning, iconColor: 'text-primary-500' },
  CAR_SUBMITTED: { icon: Send, iconColor: 'text-primary-500' },
  CAR_PIC_ACCEPTED: { icon: CheckCircle2, iconColor: 'text-success-500' },
  CAR_REWORK_REQUESTED: { icon: RefreshCw, iconColor: 'text-warning-500' },
  CAR_DPA_CLOSED: { icon: FileCheck, iconColor: 'text-success-500' },
  ACTION_OVERDUE_WARNING: { icon: Clock, iconColor: 'text-warning-500' },
  ACTION_OVERDUE: { icon: AlertTriangle, iconColor: 'text-danger-500' },
  PSC_FOLLOW_UP_RECORDED: { icon: ClipboardCheck, iconColor: 'text-primary-500' },
  CONFLICT_DETECTED: { icon: AlertTriangle, iconColor: 'text-warning-500' },
  CONFLICT_RESOLVED: { icon: Shield, iconColor: 'text-success-500' },
  PHYSICAL_VERIFICATION_CREATED: { icon: ClipboardCheck, iconColor: 'text-primary-500' },
  DEF_ASSIGNED: { icon: UserCheck, iconColor: 'text-primary-500' },
};

// ============================================================================
// Component
// ============================================================================

export interface NotificationItemProps {
  notification: Notification;
  onMarkRead?: (id: string) => void;
}

export const NotificationItem: FC<NotificationItemProps> = memo(function NotificationItem({
  notification,
  onMarkRead,
}) {
  const navigate = useNavigate();
  const style = NOTIFICATION_STYLES[notification.notification_type] || {
    icon: FileWarning,
    iconColor: 'text-neutral-500',
  };
  const Icon = style.icon;

  const handleClick = () => {
    // Mark as read when clicked
    if (!notification.is_read && onMarkRead) {
      onMarkRead(notification.id);
    }

    // Navigate to entity if available
    if (notification.entity_type && notification.entity_id) {
      if (notification.entity_type === 'CAR') {
        navigate(ROUTES.CAR_DETAIL(notification.entity_id));
      } else if (notification.entity_type === 'INSPECTION') {
        navigate(ROUTES.INSPECTION_DETAIL(notification.entity_id));
      } else if (notification.entity_type === 'DEFICIENCY') {
        navigate(ROUTES.DEFICIENCIES);
      }
    }
  };

  const formattedTime = (() => {
    try {
      return format(parseISO(notification.created_date), 'dd MMM yyyy HH:mm');
    } catch {
      return notification.created_date;
    }
  })();

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={`${notification.is_read ? '' : 'Unread: '}${notification.title}, ${formattedTime}`}
      className={cn(
        'flex w-full items-start gap-3 rounded-lg border px-4 py-3 text-left transition-colors',
        notification.is_read
          ? 'border-neutral-200 bg-white hover:bg-neutral-50'
          : 'border-primary-100 bg-primary-50/30 hover:bg-primary-50/50'
      )}
    >
      {/* Unread indicator */}
      <div className="mt-1 flex-shrink-0" aria-hidden="true">
        {!notification.is_read ? (
          <div className="h-2.5 w-2.5 rounded-full bg-primary-500" />
        ) : (
          <div className="h-2.5 w-2.5" />
        )}
      </div>

      {/* Icon */}
      <div className="mt-0.5 flex-shrink-0">
        <Icon className={cn('h-5 w-5', style.iconColor)} />
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            'text-sm leading-snug',
            notification.is_read
              ? 'text-neutral-600'
              : 'font-medium text-neutral-800'
          )}
        >
          {notification.title}
        </p>
        {notification.message && notification.message !== notification.title && (
          <p className="mt-0.5 text-xs text-neutral-500 line-clamp-2">
            {notification.message}
          </p>
        )}
        <p className="mt-1 text-xs text-neutral-400">{formattedTime}</p>
      </div>
    </button>
  );
});
