import { memo, type FC } from 'react';
import { useNavigate } from 'react-router-dom';
import { Ship, Calendar, MapPin, AlertTriangle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import { StatusBadge } from '@/components/shared';
import { cn } from '@/lib/utils';
import { ROUTES, INSPECTION_TYPES, PSC_SUBTYPES } from '@/lib/utils/constants';
import type { InspectionStatus } from '@/types';

/**
 * Inspection card component per APP_FLOW.md Section 2.2
 *
 * Displays inspection summary in list view with:
 * - Vessel name, type, subtype
 * - Date, port, MOU
 * - Deficiency count, status
 * - Detention highlighting
 */

export interface InspectionCardProps {
  /** Inspection ID */
  id: number;
  /** Vessel name */
  vesselName: string;
  /** Inspection type (PSC, RS, AUDIT) */
  inspectionType: string;
  /** PSC subtype (INITIAL, FOLLOW_UP, etc.) - only for PSC */
  pscSubtype?: string | null;
  /** Inspection date (ISO format) */
  inspectionDate: string;
  /** Port of inspection */
  port: string;
  /** Port state/country */
  portState: string;
  /** MOU code (for PSC inspections) */
  mouCode?: string | null;
  /** Whether vessel was detained */
  isDetention: boolean;
  /** Current status */
  status: InspectionStatus;
  /** Total deficiency count */
  deficiencyCount: number;
  /** Open (unclosed) deficiency count */
  openDeficiencyCount?: number;
  /** Additional class names */
  className?: string;
}

/** Map PSC subtype codes to display labels */
const pscSubtypeLabels: Record<string, string> = {
  [PSC_SUBTYPES.INITIAL]: 'Initial',
  [PSC_SUBTYPES.EXPANDED]: 'Expanded',
  [PSC_SUBTYPES.CIC]: 'CIC',
  [PSC_SUBTYPES.FOLLOW_UP]: 'Follow-up',
};

/** Format date for display (e.g., "15 Jan 2026") */
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export const InspectionCard: FC<InspectionCardProps> = memo(function InspectionCard({
  id,
  vesselName,
  inspectionType,
  pscSubtype,
  inspectionDate,
  port,
  portState,
  mouCode,
  isDetention,
  status,
  deficiencyCount,
  openDeficiencyCount,
  className,
}) {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(ROUTES.INSPECTION_DETAIL(id));
  };

  // Build type display string
  const typeDisplay =
    inspectionType === INSPECTION_TYPES.PSC && pscSubtype
      ? `PSC - ${pscSubtypeLabels[pscSubtype] || pscSubtype}`
      : inspectionType;

  // Build location display
  const locationDisplay = portState ? `${port}, ${portState}` : port;

  // Build deficiency display
  const deficiencyDisplay =
    openDeficiencyCount !== undefined
      ? `${deficiencyCount} (${openDeficiencyCount} open)`
      : deficiencyCount.toString();

  return (
    <Card
      className={cn(
        'cursor-pointer transition-shadow hover:shadow-md',
        isDetention && 'border-l-4 border-l-error-500',
        className
      )}
      onClick={handleClick}
    >
      <CardContent className="p-4">
        {/* Header row: Vessel name, Type, Date */}
        <div className="mb-2 flex items-start justify-between gap-2">
          <div className="flex min-w-0 flex-1 items-center gap-2">
            <Ship className="h-5 w-5 flex-shrink-0 text-primary-500" />
            <span className="truncate font-medium text-neutral-900">
              {vesselName}
            </span>
          </div>
          <div className="flex flex-shrink-0 items-center gap-2 text-sm text-neutral-500">
            <span className="hidden sm:inline">{typeDisplay}</span>
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {formatDate(inspectionDate)}
            </span>
          </div>
        </div>

        {/* Mobile: Type row */}
        <div className="mb-2 text-sm text-neutral-600 sm:hidden">
          {typeDisplay}
        </div>

        {/* Location row */}
        <div className="mb-3 flex items-center gap-1 text-sm text-neutral-600">
          <MapPin className="h-4 w-4 flex-shrink-0" />
          <span className="truncate">{locationDisplay}</span>
          {mouCode && (
            <>
              <span className="text-neutral-400">|</span>
              <span className="flex-shrink-0">{mouCode} MOU</span>
            </>
          )}
        </div>

        {/* Footer row: Deficiencies, Status, Detention */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-sm text-neutral-600">
            <span className="font-medium">Deficiencies:</span> {deficiencyDisplay}
          </div>
          <div className="flex items-center gap-2">
            {isDetention && (
              <div className="flex items-center gap-1 text-sm font-medium text-error-600">
                <AlertTriangle className="h-4 w-4" />
                <span className="hidden xs:inline">Detention</span>
              </div>
            )}
            <StatusBadge status={status} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
});
