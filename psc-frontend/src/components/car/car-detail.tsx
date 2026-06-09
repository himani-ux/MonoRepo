import type { FC } from 'react';
import { Calendar, MapPin, Tag, AlertCircle, FileText } from 'lucide-react';
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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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
        carId={car.id}
        onUpload={onUploadEvidence}
      />

      {((car.follow_up_reports?.length ?? 0) > 0 ||
        (car.follow_up_action_updates?.length ?? 0) > 0) && (
        <Card>
          <CardContent className="p-4">
            <h2 className="mb-3 text-base font-semibold text-gray-900">
              FOLLOW-UP REPORTS
            </h2>

            {car.follow_up_summary?.reinspection_date && (
              <div className="mb-3 rounded-md bg-neutral-50 p-3 text-sm text-gray-700">
                <div>
                  Reinspection: {formatDate(car.follow_up_summary.reinspection_date)}
                </div>
                {car.follow_up_summary.notes && (
                  <div className="mt-1 whitespace-pre-wrap break-words">
                    {car.follow_up_summary.notes}
                  </div>
                )}
              </div>
            )}

            {car.follow_up_action_updates?.length > 0 && (
              <div className="mb-3 space-y-2">
                {car.follow_up_action_updates.map((update, index) => (
                  <div
                    key={`${update.changed_at}-${index}`}
                    className="rounded-md border border-neutral-200 bg-white p-3 text-sm"
                  >
                    <div className="font-medium text-gray-900">
                      Action Code: {update.from_action_code || '-'} to{' '}
                      {update.to_action_code || '-'}
                    </div>
                    {update.notes && (
                      <div className="mt-1 whitespace-pre-wrap break-words text-gray-600">
                        {update.notes}
                      </div>
                    )}
                    <div className="mt-1 text-xs text-gray-500">
                      {formatDate(update.changed_at)} &middot; {update.changed_by}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {car.follow_up_reports?.length > 0 ? (
              <div className="space-y-2">
                {car.follow_up_reports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-start gap-3 rounded-md border border-neutral-200 bg-white p-3"
                  >
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded bg-neutral-100">
                      <FileText className="h-5 w-5 text-error-500" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <a
                        href={report.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block truncate text-sm font-medium text-primary-600 hover:underline"
                      >
                        {report.file_name}
                      </a>
                      {report.description && (
                        <p className="text-xs text-gray-500">{report.description}</p>
                      )}
                      <p className="mt-1 text-xs text-gray-400">
                        {formatDate(report.uploaded_at)} &middot;{' '}
                        {formatFileSize(report.file_size)} &middot; {report.uploaded_by}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm italic text-gray-500">
                No follow-up report uploaded for this CAR.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Activity History (all users) */}
      <ActivityHistory events={car.activity_history} />

      {/* Audit Log (Office/DPA only) */}
      {isOfficeOrDPA && car.audit_log.length > 0 && (
        <AuditLog entries={car.audit_log} />
      )}
    </div>
  );
};
