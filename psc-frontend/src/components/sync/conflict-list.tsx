/**
 * ConflictList component — displays unresolved sync conflicts.
 *
 * Shows detected conflicts with entity info and status.
 * Vessel users see "Waiting for office to resolve".
 * Office/DPA users see a "Resolve" button.
 * Hidden when no conflicts per APP_FLOW.md spec.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3
 * Implements: PRD.md FEAT-SYNC-004, FEAT-SYNC-005
 * Flow: APP_FLOW.md Section 2.5
 */

import { type FC } from 'react';
import { AlertOctagon } from 'lucide-react';
import { Card, CardContent, Button, Badge } from '@/components/ui';
import type { SyncConflict } from '@/types';

export interface ConflictListProps {
  /** List of unresolved conflicts. */
  conflicts: SyncConflict[];
  /** Whether the current user is Office/DPA (can resolve). */
  canResolve: boolean;
  /** Handler when "Resolve" is clicked for a conflict. */
  onResolve?: (conflict: SyncConflict) => void;
}

function getEntityTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    INSPECTION: 'Inspection',
    CAR: 'CAR',
    DEFICIENCY: 'Deficiency',
  };
  return labels[type] ?? type;
}

export const ConflictList: FC<ConflictListProps> = ({
  conflicts,
  canResolve,
  onResolve,
}) => {
  // Hidden when no conflicts
  if (conflicts.length === 0) return null;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <AlertOctagon className="h-4 w-4 text-error-500" />
          <h3 className="text-sm font-medium text-neutral-900">Conflicts</h3>
          <Badge variant="destructive" className="ml-auto text-xs">
            {conflicts.length}
          </Badge>
        </div>

        <p className="mb-3 text-xs text-error-600">
          {conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} detected
        </p>

        <ul className="space-y-3">
          {conflicts.map((conflict) => (
            <li
              key={conflict.id}
              className="rounded-md border border-error-100 bg-error-50 p-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-neutral-900">
                    {getEntityTypeLabel(conflict.entity_type)} #{conflict.entity_id}
                  </p>
                  <p className="mt-0.5 text-xs text-neutral-500">
                    {conflict.conflicting_fields.length} conflicting field{conflict.conflicting_fields.length !== 1 ? 's' : ''}:{' '}
                    {conflict.conflicting_fields.join(', ')}
                  </p>
                  {!canResolve && (
                    <p className="mt-1 text-xs italic text-neutral-400">
                      Waiting for office to resolve
                    </p>
                  )}
                </div>
                {canResolve && onResolve && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onResolve(conflict)}
                    className="h-7 shrink-0 text-xs"
                  >
                    Resolve
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
};
