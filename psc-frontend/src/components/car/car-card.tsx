import { memo, type FC } from 'react';
import { useNavigate } from 'react-router-dom';
import { Ship, Calendar, AlertTriangle, AlertCircle } from 'lucide-react';
import { Badge, Card, CardContent } from '@/components/ui';
import { StatusBadge } from '@/components/shared';
import { cn } from '@/lib/utils';
import { ROUTES } from '@/lib/utils/constants';
import type { CARStatus } from '@/types';

/**
 * CAR card component per APP_FLOW.md Section 2.3
 *
 * Displays CAR summary in list view with:
 * - CAR number, DefCode (prominent), description
 * - Vessel name, target date
 * - Status badge
 * - Overdue highlighting (red border + text)
 * - Missing evidence warning
 */

export interface CARCardProps {
  /** CAR ID */
  id: number;
  /** CAR number (e.g., PSC-2026-001) */
  carNumber: string;
  /** Deficiency code (e.g., 10101) — must be prominent */
  defCode: string;
  /** Deficiency description */
  deficiencyDescription: string;
  /** Vessel name */
  vesselName: string;
  /** Current CAR status */
  status: CARStatus;
  /** Target completion date (ISO format) */
  targetDate: string | null;
  /** Whether this CAR is overdue */
  isOverdue: boolean;
  /** Whether this CAR is missing required evidence */
  hasMissingEvidence: boolean;
  /** Whether this CAR has an OPEN physical verification due */
  pvDue?: boolean;
  /** Inspection type (PSC, RS, AUDIT) */
  inspectionType: string;
  /** Additional class names */
  className?: string;
}

/** Format date for display (e.g., "15 Jan 2026") */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export const CARCard: FC<CARCardProps> = memo(function CARCard({
  id,
  carNumber,
  defCode,
  deficiencyDescription,
  vesselName,
  status,
  targetDate,
  isOverdue,
  hasMissingEvidence,
  pvDue = false,
  inspectionType,
  className,
}) {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(ROUTES.CAR_DETAIL(id));
  };

  return (
    <Card
      className={cn(
        'cursor-pointer transition-shadow hover:shadow-md',
        isOverdue && 'border-l-4 border-l-error-500',
        className
      )}
      onClick={handleClick}
    >
      <CardContent className="p-4">
        {/* Header row: CAR number + Status */}
        <div className="mb-2 flex items-start justify-between gap-2">
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <span className="font-medium text-neutral-900">{carNumber}</span>
            <span className="text-xs text-neutral-400">{inspectionType}</span>
          </div>
          <StatusBadge status={status} />
        </div>

        {/* DefCode row — prominently displayed per LESSONS.md */}
        <div className="mb-2 flex items-center gap-2">
          <span className="inline-flex items-center rounded bg-primary-50 px-2 py-0.5 text-sm font-semibold text-primary-700">
            [{defCode}]
          </span>
          <span className="truncate text-sm text-neutral-700">
            {deficiencyDescription}
          </span>
        </div>

        {/* Info row: Vessel + Target date */}
        <div className="mb-1 flex items-center gap-3 text-sm text-neutral-600">
          <span className="flex items-center gap-1 truncate">
            <Ship className="h-4 w-4 flex-shrink-0" />
            {vesselName}
          </span>
          {targetDate && (
            <span className="flex flex-shrink-0 items-center gap-1">
              <Calendar className="h-4 w-4" />
              Target: {formatDate(targetDate)}
            </span>
          )}
        </div>

        {/* Indicators row: Overdue + Missing evidence */}
        {(isOverdue || hasMissingEvidence || pvDue) && (
          <div className="mt-2 flex flex-wrap items-center gap-3">
            {pvDue && (
              <Badge variant="secondary" className="font-medium">
                PV Due
              </Badge>
            )}
            {isOverdue && (
              <span className="flex items-center gap-1 text-sm font-medium text-error-600">
                <AlertTriangle className="h-4 w-4" />
                OVERDUE
              </span>
            )}
            {hasMissingEvidence && (
              <span className="flex items-center gap-1 text-sm text-warning-600">
                <AlertCircle className="h-4 w-4" />
                Missing evidence
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
});
