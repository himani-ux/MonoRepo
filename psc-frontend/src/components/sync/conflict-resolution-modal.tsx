/**
 * ConflictResolutionModal — side-by-side comparison of vessel vs server data.
 *
 * Shows conflicting fields highlighted, with 3 resolution options:
 * KEEP_SERVER, KEEP_VESSEL, REOPEN_FOR_MERGE.
 * Only available to Office/DPA users.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3
 * Implements: PRD.md FEAT-SYNC-005
 * Flow: APP_FLOW.md Section 2.5
 */

import { type FC, useState } from 'react';
import { AlertOctagon } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Badge,
  Label,
  Textarea,
} from '@/components/ui';
import { cn } from '@/lib/utils';
import type { SyncConflict } from '@/types';

export interface ConflictResolutionModalProps {
  /** Whether the modal is open. */
  open: boolean;
  /** Handler when modal open state changes. */
  onOpenChange: (open: boolean) => void;
  /** The conflict to resolve. */
  conflict: SyncConflict | null;
  /** Handler when resolution is submitted. */
  onResolve: (
    conflictId: string,
    resolution: 'KEEP_SERVER' | 'KEEP_VESSEL' | 'REOPEN_FOR_MERGE',
    notes?: string
  ) => void | Promise<void>;
  /** Whether resolution is in progress. */
  resolving?: boolean;
}

type ResolutionOption = 'KEEP_SERVER' | 'KEEP_VESSEL' | 'REOPEN_FOR_MERGE';

const RESOLUTION_OPTIONS: {
  value: ResolutionOption;
  label: string;
  description: string;
}[] = [
  {
    value: 'KEEP_SERVER',
    label: 'Keep Server Version',
    description: 'Discard vessel changes and use the server version.',
  },
  {
    value: 'KEEP_VESSEL',
    label: 'Keep Vessel Version',
    description: 'Override server with the vessel version.',
  },
  {
    value: 'REOPEN_FOR_MERGE',
    label: 'Reopen for Merge',
    description: 'Reopen the record so the vessel can manually reconcile.',
  },
];

function formatFieldName(field: string): string {
  return field
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatFieldValue(value: unknown): string {
  if (value === null || value === undefined) return '(empty)';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export const ConflictResolutionModal: FC<ConflictResolutionModalProps> = ({
  open,
  onOpenChange,
  conflict,
  onResolve,
  resolving = false,
}) => {
  const [selectedResolution, setSelectedResolution] =
    useState<ResolutionOption | null>(null);
  const [notes, setNotes] = useState('');

  if (!conflict) return null;

  const handleSubmit = () => {
    if (!selectedResolution) return;
    onResolve(conflict.id, selectedResolution, notes || undefined);
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setSelectedResolution(null);
      setNotes('');
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertOctagon className="h-5 w-5 text-error-500" />
            Resolve Conflict
          </DialogTitle>
          <DialogDescription>
            {conflict.entity_type} #{conflict.entity_id} has conflicting changes.
          </DialogDescription>
        </DialogHeader>

        {/* Conflicting fields comparison */}
        <div className="max-h-64 space-y-2 overflow-y-auto" role="table" aria-label="Conflicting fields comparison">
          <div className="grid grid-cols-3 gap-2 text-xs font-medium text-neutral-500" role="row">
            <span role="columnheader">Field</span>
            <span role="columnheader">Vessel</span>
            <span role="columnheader">Server</span>
          </div>
          {conflict.conflicting_fields.map((field) => {
            const vesselVal = conflict.vessel_data[field];
            const serverVal = conflict.server_data[field];
            return (
              <div
                key={field}
                role="row"
                className="grid grid-cols-3 gap-2 rounded-md bg-error-50 p-2 text-xs"
              >
                <span role="rowheader" className="font-medium text-neutral-700">
                  {formatFieldName(field)}
                </span>
                <span role="cell" className="break-words text-neutral-600">
                  {formatFieldValue(vesselVal)}
                </span>
                <span role="cell" className="break-words text-neutral-600">
                  {formatFieldValue(serverVal)}
                </span>
              </div>
            );
          })}
        </div>

        {/* Resolution options */}
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Resolution</legend>
          <div role="radiogroup" aria-label="Resolution strategy" className="space-y-2">
            {RESOLUTION_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                role="radio"
                aria-checked={selectedResolution === option.value}
                onClick={() => setSelectedResolution(option.value)}
                className={cn(
                  'w-full rounded-md border p-3 text-left transition-colors',
                  selectedResolution === option.value
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-neutral-200 bg-white hover:border-neutral-300'
                )}
              >
                <div className="flex items-center gap-2">
                  <div
                    aria-hidden="true"
                    className={cn(
                      'h-4 w-4 rounded-full border-2',
                      selectedResolution === option.value
                        ? 'border-primary-500 bg-primary-500'
                        : 'border-neutral-300'
                    )}
                  >
                    {selectedResolution === option.value && (
                      <div className="flex h-full items-center justify-center">
                        <div className="h-1.5 w-1.5 rounded-full bg-white" />
                      </div>
                    )}
                  </div>
                  <span className="text-sm font-medium text-neutral-900">
                    {option.label}
                  </span>
                </div>
                <p className="ml-6 mt-0.5 text-xs text-neutral-500">
                  {option.description}
                </p>
              </button>
            ))}
          </div>
        </fieldset>

        {/* Notes */}
        <div className="space-y-1.5">
          <Label htmlFor="resolution-notes" className="text-sm">
            Notes <Badge variant="outline" className="ml-1 text-xs">Optional</Badge>
          </Label>
          <Textarea
            id="resolution-notes"
            placeholder="Add any notes about this resolution..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className="text-sm"
          />
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={resolving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedResolution || resolving}
          >
            {resolving ? 'Resolving...' : 'Apply Resolution'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
