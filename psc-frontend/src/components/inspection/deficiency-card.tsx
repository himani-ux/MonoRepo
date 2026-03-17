import { memo, type FC } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, FileText, User, UserCheck } from 'lucide-react';
import { Card, CardContent, Checkbox } from '@/components/ui';
import { StatusBadge } from '@/components/shared';
import { cn } from '@/lib/utils';
import type { DeficiencyDetail } from '@/types';

/**
 * Props for DeficiencyCard component
 */
export interface DeficiencyCardProps {
  /** The deficiency data to display */
  deficiency: DeficiencyDetail;
  /** Optional click handler for the card */
  onClick?: () => void;
  /** Slot for workflow action buttons */
  actions?: React.ReactNode;
  /** Additional class names */
  className?: string;
  /** Show selection checkbox */
  selectable?: boolean;
  /** Whether the card is selected */
  selected?: boolean;
  /** Selection change handler */
  onSelectChange?: (selected: boolean) => void;
}

/**
 * DeficiencyCard displays a single deficiency with its CAR and workflow information.
 * DefCode is prominently displayed per LESSONS.md business rules.
 */
export const DeficiencyCard: FC<DeficiencyCardProps> = memo(function DeficiencyCard({
  deficiency,
  onClick,
  actions,
  className,
  selectable,
  selected,
  onSelectChange,
}) {
  const {
    def_code,
    def_code_description,
    description,
    action_code,
    target_date,
    is_cleared,
    assigned_crew_name,
    owner_name,
    owner_rank,
    reviewer_name,
    reviewer_rank,
    car,
  } = deficiency;

  // Format target date for display
  const formattedTargetDate = target_date
    ? new Date(target_date).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : null;

  return (
    <Card
      className={cn(
        'transition-colors',
        onClick && 'cursor-pointer hover:bg-gray-50',
        is_cleared && 'opacity-60',
        className
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className={cn(selectable && 'flex gap-3')}>
          {selectable && (
            <div className="pt-1 shrink-0" onClick={(e) => e.stopPropagation()}>
              <Checkbox
                checked={selected}
                onCheckedChange={(checked) => onSelectChange?.(!!checked)}
              />
            </div>
          )}
          <div className="flex-1 min-w-0">
        {/* Header: DefCode (prominent) + DEF Status + Action Code */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            {/* DefCode - PROMINENT per LESSONS.md */}
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-lg font-bold text-primary-600">
                [{def_code}]
              </span>
              <span className="text-sm text-gray-700 truncate">
                {def_code_description}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {/* CAR workflow status (primary) */}
            {car?.status && (
              <StatusBadge status={car.status} className="text-xs" />
            )}
            {/* Action Code */}
            {action_code && (
              <div className="text-xs text-gray-500 whitespace-nowrap">
                Action: {action_code}
              </div>
            )}
          </div>
        </div>

        {/* Description - truncated */}
        <p className="mt-2 text-sm text-gray-600 line-clamp-2">{description}</p>

        {/* Owner / Reviewer row */}
        {(owner_name || reviewer_name) && (
          <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
            {owner_name && (
              <span className="flex items-center gap-1">
                <User className="h-3.5 w-3.5" />
                Owner: {owner_rank ? `${owner_rank} - ` : ''}{owner_name}
              </span>
            )}
            {reviewer_name && (
              <span className="flex items-center gap-1">
                <UserCheck className="h-3.5 w-3.5" />
                Reviewer: {reviewer_rank ? `${reviewer_rank} - ` : ''}{reviewer_name}
              </span>
            )}
          </div>
        )}

        {/* CAR info row */}
        {car && (
          <div className="mt-3 flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2 text-sm">
              <FileText className="h-4 w-4 text-gray-400" />
              <span className="text-gray-600">CAR: {car.car_number}</span>
              <StatusBadge status={car.status} className="text-xs" />
            </div>

            {/* View CAR link */}
            <Link
              to={`/cars/${car.id}`}
              onClick={(e) => e.stopPropagation()}
              className="text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline"
            >
              View CAR
            </Link>
          </div>
        )}

        {/* Assigned crew + Target date */}
        {(assigned_crew_name || formattedTargetDate) && (
          <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
            {assigned_crew_name && !owner_name && (
              <span className="font-medium text-gray-600">
                Assigned: {assigned_crew_name}
              </span>
            )}
            {formattedTargetDate && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                Target: {formattedTargetDate}
              </span>
            )}
          </div>
        )}

        {/* Cleared indicator */}
        {is_cleared && (
          <div className="mt-2">
            <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
              Cleared
            </span>
          </div>
        )}

        {/* Workflow action buttons slot */}
        {actions && (
          <div className="mt-3 flex items-center gap-2 border-t pt-3">
            {actions}
          </div>
        )}
          </div>{/* end flex-1 wrapper */}
        </div>{/* end selectable flex row */}
      </CardContent>
    </Card>
  );
});
