/**
 * Physical Verification section for CAR detail page.
 *
 * Shows PV status, dates, verifier, and action buttons.
 * Only rendered when CAR is DPA_CLOSED or has an existing PV.
 *
 * Source: FRONTEND_GUIDELINES.md Section 3
 * Implements: PRD.md FEAT-PV-001, FEAT-PV-002
 * Flow: APP_FLOW.md Section 2.3
 */

import { type FC } from 'react';
import { Calendar, MapPin, User, CheckCircle, Plus } from 'lucide-react';
import { Card, CardContent, Badge, Button } from '@/components/ui';
import type { PhysicalVerification } from '@/types';

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export interface PhysicalVerificationSectionProps {
  physicalVerification: PhysicalVerification | null;
  isDPAClosed: boolean;
  canCreatePV: boolean;
  canClosePV: boolean;
  onCreatePV?: () => void;
  onClosePV?: () => void;
}

export const PhysicalVerificationSection: FC<PhysicalVerificationSectionProps> = ({
  physicalVerification,
  isDPAClosed,
  canCreatePV,
  canClosePV,
  onCreatePV,
  onClosePV,
}) => {
  // Only show if CAR is DPA_CLOSED or PV exists
  if (!isDPAClosed && !physicalVerification) {
    return null;
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            Physical Verification
          </h2>
          {physicalVerification && (
            <Badge variant={physicalVerification.status === 'CLOSED' ? 'default' : 'secondary'}>
              {physicalVerification.status}
            </Badge>
          )}
        </div>

        {physicalVerification ? (
          <div className="space-y-3">
            {/* PV Details */}
            <div className="space-y-2 text-sm">
              {physicalVerification.scheduled_date && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span>
                    Scheduled: {formatDate(physicalVerification.scheduled_date)}
                  </span>
                </div>
              )}

              {physicalVerification.visit_date && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span>
                    Visit Date: {formatDate(physicalVerification.visit_date)}
                  </span>
                </div>
              )}

              {physicalVerification.visit_port && (
                <div className="flex items-center gap-2 text-gray-600">
                  <MapPin className="h-4 w-4 text-gray-400" />
                  <span>{physicalVerification.visit_port}</span>
                </div>
              )}

              {physicalVerification.verifier_user_id && (
                <div className="flex items-center gap-2 text-gray-600">
                  <User className="h-4 w-4 text-gray-400" />
                  <span>
                    Verifier: {physicalVerification.verifier_user_id}
                  </span>
                </div>
              )}
            </div>

            {/* Comments */}
            {physicalVerification.comments && (
              <div className="rounded-md bg-gray-50 p-3 text-sm text-gray-700">
                <p className="font-medium text-gray-800 mb-1">Comments:</p>
                <p>{physicalVerification.comments}</p>
              </div>
            )}

            {/* Closed info */}
            {physicalVerification.status === 'CLOSED' && physicalVerification.closed_at && (
              <div className="flex items-center gap-2 text-sm text-success-600">
                <CheckCircle className="h-4 w-4" />
                <span>
                  Closed on {formatDate(physicalVerification.closed_at)}
                </span>
              </div>
            )}

            {/* Close PV button */}
            {canClosePV && physicalVerification.status === 'OPEN' && (
              <Button
                size="sm"
                variant="outline"
                onClick={onClosePV}
                className="mt-2"
              >
                <CheckCircle className="mr-2 h-4 w-4" />
                Close Verification
              </Button>
            )}
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-gray-500 mb-3">
              No physical verification scheduled for this CAR.
            </p>
            {canCreatePV && (
              <Button size="sm" variant="outline" onClick={onCreatePV}>
                <Plus className="mr-2 h-4 w-4" />
                Schedule Verification
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
