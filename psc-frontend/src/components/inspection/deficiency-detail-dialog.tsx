/**
 * Deficiency Detail Dialog
 *
 * Shows full deficiency details in a dialog with workflow action buttons
 * in the footer. This ensures the master reads through details before
 * taking workflow actions.
 */

import { Link } from 'react-router-dom';
import { Calendar, FileText, User, UserCheck, Hash } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui';
import { StatusBadge } from '@/components/shared';
import { DeficiencyWorkflowActions } from './deficiency-workflow-actions';
import type { DeficiencyDetail } from '@/types';

export interface DeficiencyDetailDialogProps {
  deficiency: DeficiencyDetail | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeficiencyDetailDialog({
  deficiency,
  open,
  onOpenChange,
}: DeficiencyDetailDialogProps) {
  if (!deficiency) return null;

  const {
    def_code,
    def_code_description,
    description,
    action_code,
    action_code_description,
    target_date,
    is_cleared,
    owner_name,
    owner_rank,
    reviewer_name,
    reviewer_rank,
    car,
  } = deficiency;

  const formattedTargetDate = target_date
    ? new Date(target_date).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      })
    : null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="font-mono text-primary-600">[{def_code}]</span>
            <span className="text-base font-normal text-gray-500">Deficiency Detail</span>
          </DialogTitle>
        </DialogHeader>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto space-y-4 py-2">
          {/* Status + Target Date row */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {car?.status && <StatusBadge status={car.status} />}
              {is_cleared && (
                <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                  Cleared
                </span>
              )}
            </div>
            {formattedTargetDate && (
              <span className="flex items-center gap-1 text-sm text-gray-500">
                <Calendar className="h-4 w-4" />
                Target: {formattedTargetDate}
              </span>
            )}
          </div>

          {/* DefCode description */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wide">
              Deficiency Code
            </h4>
            <p className="mt-1 text-sm text-gray-700">
              {def_code} — {def_code_description}
            </p>
          </div>

          {/* Full description */}
          <div>
            <h4 className="text-xs font-medium text-gray-400 uppercase tracking-wide">
              Description
            </h4>
            <p className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
              {description}
            </p>
          </div>

          {/* Owner */}
          {owner_name && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <User className="h-4 w-4 text-gray-400" />
              <span>
                <span className="font-medium">Owner:</span>{' '}
                {owner_rank ? `${owner_rank} - ` : ''}
                {owner_name}
              </span>
            </div>
          )}

          {/* Reviewer */}
          {reviewer_name && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <UserCheck className="h-4 w-4 text-gray-400" />
              <span>
                <span className="font-medium">Reviewer:</span>{' '}
                {reviewer_rank ? `${reviewer_rank} - ` : ''}
                {reviewer_name}
              </span>
            </div>
          )}

          {/* Linked CAR */}
          {car && (
            <div className="rounded-lg border bg-gray-50 p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="font-medium text-gray-700">
                    CAR: {car.car_number}
                  </span>
                  <StatusBadge status={car.status} className="text-xs" />
                </div>
                <Link
                  to={`/cars/${car.id}`}
                  className="text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline"
                  onClick={() => onOpenChange(false)}
                >
                  View CAR
                </Link>
              </div>
            </div>
          )}

          {/* Action Code */}
          {action_code && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Hash className="h-4 w-4 text-gray-400" />
              <span>
                <span className="font-medium">Action Code:</span>{' '}
                {action_code}
                {action_code_description ? ` — ${action_code_description}` : ''}
              </span>
            </div>
          )}
        </div>

        {/* Footer with workflow actions */}
        <DialogFooter className="border-t pt-3">
          <DeficiencyWorkflowActions
            deficiency={deficiency}
            onTransitioned={() => onOpenChange(false)}
          />
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
