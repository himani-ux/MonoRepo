import type { FC } from 'react';
import { Badge } from '@/components/ui';
import { cn } from '@/lib/utils';
import {
  type StatusType,
  getStatusVariant,
  getStatusLabel,
} from '@/lib/utils/format-status';

/**
 * Status badge component that maps inspection/CAR status to badge variants
 * per DESIGN_SYSTEM.md Section 1.4
 */

export type { StatusType };

export interface StatusBadgeProps {
  /** The status value to display */
  status: StatusType;
  /** Override the default label */
  label?: string;
  /** Show indicator dot (for special statuses like detention/overdue) */
  showIndicator?: boolean;
  /** Additional class names */
  className?: string;
}

export const StatusBadge: FC<StatusBadgeProps> = ({
  status,
  label,
  showIndicator = false,
  className,
}) => {
  const variant = getStatusVariant(status);
  const displayLabel = label || getStatusLabel(status);

  return (
    <Badge variant={variant} className={cn('gap-1', className)}>
      {showIndicator && (status === 'DETENTION' || status === 'OVERDUE') && (
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
      )}
      {displayLabel}
    </Badge>
  );
};
