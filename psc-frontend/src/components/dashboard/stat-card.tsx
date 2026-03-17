/**
 * StatCard — KPI card with icon, value, and label.
 */

import type { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import { cn } from '@/lib/utils';

export interface StatCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  variant?: 'default' | 'warning' | 'danger';
  onClick?: () => void;
  className?: string;
}

const variantStyles = {
  default: {
    icon: 'bg-primary-100 text-primary-600',
    value: 'text-gray-900',
  },
  warning: {
    icon: 'bg-amber-100 text-amber-600',
    value: 'text-amber-700',
  },
  danger: {
    icon: 'bg-red-100 text-red-600',
    value: 'text-red-700',
  },
} as const;

export function StatCard({
  label,
  value,
  icon: Icon,
  variant = 'default',
  onClick,
  className,
}: StatCardProps) {
  const styles = variantStyles[variant];
  const isClickable = typeof onClick === 'function';

  return (
    <Card
      clickable={isClickable}
      className={cn(
        'transition-shadow',
        isClickable &&
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 active:scale-[0.99]',
        className
      )}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={(event) => {
        if (!isClickable) return;
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onClick?.();
        }
      }}
    >
      <CardContent className="flex items-center gap-4 p-4">
        <div className={cn('rounded-lg p-2.5', styles.icon)}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className={cn('text-2xl font-bold', styles.value)}>{value}</p>
          <p className="text-sm text-gray-500 truncate">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}
