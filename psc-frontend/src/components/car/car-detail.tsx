import type { FC } from 'react';
import { Calendar, MapPin, Tag, AlertCircle } from 'lucide-react';
import { Card, CardContent, Badge } from '@/components/ui';
import { StatusBadge } from '@/components/shared';
import { RootCauseSection } from './root-cause-section';
import { CorrectiveActionList } from './corrective-action-list';
import { EvidenceSection } from './evidence-section';
import { ActivityHistory } from './activity-history';
import { AuditLog } from './audit-log';
import { cn } from '@/lib/utils';
import { CAR_STATUS } from '@/lib/utils/constants';
import type { CARDetail as CARDetailType } from '@/types';

export interface CARDetailProps {
  car: CARDetailType;
  isOfficeOrDPA?: boolean;
  onUploadEvidence?: () => void;
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

export const CARDetail: FC<CARDetailProps> = ({
  car,
  isOfficeOrDPA = false,
  onUploadEvidence,
  className,
}) => {
  const isReworked = car.status === CAR_STATUS.RETURNED_FOR_REWORK;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header Card */}
      <Card>
        <CardContent className="p-4">
          {/* CAR Number & Status */}
          <div className="mb-3 flex items-start justify-between gap-2">
            <h1 className="text-lg font-semibold text-gray-900">
              {car.car_number}
            </h1>
            <StatusBadge status={car.status} />
          </div>

          {/* Dates */}
          <div className="mb-3 space-y-1 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <span>Created: {formatDate(car.created_date)}</span>
            </div>
            {car.target_date && (
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-gray-400" />
                <span>Target: {formatDate(car.target_date)}</span>
              </div>
            )}
          </div>

          {/* Rework reason banner */}
          {isReworked && car.rework_reason && (
            <div className="mt-2 rounded-md bg-warning-50 p-3 text-sm">
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-warning-600" />
                <div>
                  <p className="font-medium text-warning-800">
                    Rework Requested (#{car.rework_count})
                  </p>
                  <p className="mt-1 text-warning-700">{car.rework_reason}</p>
                </div>
              </div>
            </div>
          )}

          {/* PIC comment */}
          {car.pic_comment && (
            <div className="mt-2 min-w-0 rounded-md bg-primary-50 p-3 text-sm">
              <p className="font-medium text-primary-800">PIC Comment:</p>
              <p className="mt-1 whitespace-pre-wrap break-words text-primary-700">
                {car.pic_comment}
              </p>
            </div>
          )}

          {/* DPA comment */}
          {car.dpa_comment && (
            <div className="mt-2 min-w-0 rounded-md bg-success-50 p-3 text-sm">
              <p className="font-medium text-success-800">DPA Comment:</p>
              <p className="mt-1 whitespace-pre-wrap break-words text-success-700">
                {car.dpa_comment}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Deficiency Section */}
      {car.deficiency && (
        <Card>
          <CardContent className="p-4">
            <h2 className="mb-3 text-base font-semibold text-gray-900">
              DEFICIENCY
            </h2>
            <div className="space-y-2">
              {/* DefCode - PROMINENT per business rules */}
              <div className="flex items-center gap-2">
                <Badge
                  variant="outline"
                  className="bg-primary-50 text-primary-700 border-primary-200 font-mono text-sm font-semibold"
                >
                  <Tag className="mr-1 h-3 w-3" />
                  {car.deficiency.def_code}
                </Badge>
                {car.deficiency.action_code && (
                  <span className="text-sm text-gray-500">
                    Action Code: {car.deficiency.action_code}
                  </span>
                )}
              </div>

              {/* Description */}
              <p className="text-sm text-gray-700">
                {car.deficiency.description}
              </p>

              {/* Inspection link info */}
              {car.inspection && (
                <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                  <span>{car.inspection.inspection_type}</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(car.inspection.inspection_date)}
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3 w-3" />
                    {car.inspection.port_place}
                  </span>
                  {car.inspection.vessel_name && (
                    <span>{car.inspection.vessel_name}</span>
                  )}
                </div>
              )}

              {/* Cleared status */}
              {car.deficiency.is_cleared && (
                <div className="mt-1 inline-flex items-center rounded bg-success-50 px-2 py-1 text-xs font-medium text-success-700">
                  Cleared
                  {car.deficiency.cleared_date &&
                    ` on ${formatDate(car.deficiency.cleared_date)}`}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Root Cause Analysis */}
      <RootCauseSection
        rootCauseSummary={car.root_cause_summary}
        clcItems={car.clc_items}
      />

      {/* Corrective Actions */}
      <CorrectiveActionList actions={car.corrective_actions} />

      {/* Evidence */}
      <EvidenceSection
        evidence={car.evidence}
        onUpload={onUploadEvidence}
      />

      {/* Activity History (all users) */}
      <ActivityHistory events={car.activity_history} />

      {/* Audit Log (Office/DPA only) */}
      {isOfficeOrDPA && car.audit_log.length > 0 && (
        <AuditLog entries={car.audit_log} />
      )}
    </div>
  );
};