import { memo, type FC } from 'react';
import { CheckCircle2, Clock, Calendar } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { CorrectiveAction } from '@/types';

export interface CorrectiveActionItemProps {
  action: CorrectiveAction;
  index: number;
  className?: string;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export const CorrectiveActionItem: FC<CorrectiveActionItemProps> = memo(function CorrectiveActionItem({
  action,
  index,
  className,
}) {
  const isOverdue =
    !action.is_completed &&
    action.due_date &&
    new Date(action.due_date) < new Date();

  return (
    <div
      className={cn(
        'rounded-md border bg-white p-3',
        isOverdue && 'border-error-300 bg-error-50',
        className
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2 min-w-0">
          <span className="mt-0.5 flex-shrink-0 text-sm font-medium text-gray-500">
            {index}.
          </span>
          <p className="text-sm text-gray-800">{action.description}</p>
        </div>
        {action.is_completed ? (
          <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-success-500" />
        ) : (
          <Clock
            className={cn(
              'h-5 w-5 flex-shrink-0',
              isOverdue ? 'text-error-500' : 'text-warning-500'
            )}
          />
        )}
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
        {action.due_date && (
          <span
            className={cn(
              'flex items-center gap-1',
              isOverdue && !action.is_completed && 'text-error-600 font-medium'
            )}
          >
            <Calendar className="h-3 w-3" />
            Due: {formatDate(action.due_date)}
          </span>
        )}
        {action.is_completed && (
          <span className="text-success-600">
            Completed {action.completed_at ? formatDate(action.completed_at) : ''}
          </span>
        )}
      </div>

      {action.completion_remarks && action.is_completed && (
        <p className="mt-1 text-xs text-gray-500 italic">
          {action.completion_remarks}
        </p>
      )}
    </div>
  );
});
