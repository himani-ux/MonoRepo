import { useState, type FC } from 'react';
import {
  Ship,
  Calendar,
  MapPin,
  User,
  FileText,
  Download,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Clock,
} from 'lucide-react';
import { Card, CardContent } from '@/components/ui';
import { StatusBadge } from '@/components/shared';
import { DeficiencyList } from './deficiency-list';
import { cn } from '@/lib/utils';
import { API_BASE_URL, INSPECTION_TYPES, PSC_SUBTYPES } from '@/lib/utils/constants';
import type { InspectionDetail as InspectionDetailType, DeficiencyDetail } from '@/types';

/**
 * Props for InspectionDetail component
 */
export interface InspectionDetailProps {
  /** The inspection data to display */
  inspection: InspectionDetailType;
  /** Callback to add a new deficiency (only for DRAFT status) */
  onAddDeficiency?: () => void;
  /** Callback when a deficiency is clicked */
  onDeficiencyClick?: (deficiency: DeficiencyDetail) => void;
  /** Additional class names */
  className?: string;
  /** Enable bulk submission of APPROVED deficiencies (Master only) */
  bulkSubmitEnabled?: boolean;
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

/** Format datetime for display (e.g., "15 Jan 2026 10:30") */
function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Report row component used in grouped reports section */
function ReportRow({ report }: { report: InspectionDetailType['reports'][number] }) {
  const rawPath = report.file_url || report.file_path;
  const normalizedPath = (rawPath || '').replace(/^\/+/, '');
  const baseUrl = API_BASE_URL.replace(/\/+$/, '');
  const reportUrl = normalizedPath.startsWith('http://') || normalizedPath.startsWith('https://')
    ? normalizedPath
    : normalizedPath.startsWith('api/') || normalizedPath.startsWith('uploads/')
      ? `${baseUrl}/${normalizedPath}`
      : `${baseUrl}/uploads/${normalizedPath.replace(/^\/+/, '')}`;

  return (
    <div className="flex items-center justify-between gap-2 rounded-md bg-gray-50 p-3">
      <div className="flex items-center gap-2 min-w-0">
        <FileText className="h-5 w-5 flex-shrink-0 text-gray-400" />
        <div className="min-w-0">
          <p className="truncate font-medium text-gray-700">
            {report.file_name}
          </p>
          <p className="text-xs text-gray-500">
            {report.description && (
              <span className="mr-2">{report.description}</span>
            )}
            Uploaded: {formatDateTime(report.uploaded_at)}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <a
          href={reportUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700"
        >
          <ExternalLink className="h-4 w-4" />
          <span className="hidden sm:inline">View</span>
        </a>
        <a
          href={reportUrl}
          download
          className="inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700"
        >
          <Download className="h-4 w-4" />
          <span className="hidden sm:inline">Download</span>
        </a>
      </div>
    </div>
  );
}

/**
 * InspectionDetail displays the full details of an inspection.
 * Includes header, report section, deficiencies, and activity history.
 */
export const InspectionDetail: FC<InspectionDetailProps> = ({
  inspection,
  onAddDeficiency,
  onDeficiencyClick,
  className,
  bulkSubmitEnabled,
}) => {
  const [isActivityExpanded, setIsActivityExpanded] = useState(false);

  const {
    vessel_name,
    imo_number,
    inspection_type,
    psc_subtype,
    inspection_date,
    port = '',
    port_state = '',
    mou_code,
    authority,
    inspector_name,
    report_reference,
    is_detention,
    detention_reason,
    status,
    reports = [],
    deficiencies = [],
    activity_history = [],
  } = inspection;

  // Build type display string
  const typeDisplay =
    inspection_type === INSPECTION_TYPES.PSC && psc_subtype
      ? `PSC - ${pscSubtypeLabels[psc_subtype] || psc_subtype}`
      : inspection_type;

  // Build location display
  const locationDisplay = port_state ? `${port}, ${port_state}` : port;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header Card */}
      <Card>
        <CardContent className="p-4">
          {/* Vessel Name & Status */}
          <div className="mb-3 flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <Ship className="h-5 w-5 text-primary-500" />
              <h1 className="text-lg font-semibold text-gray-900">
                {vessel_name}
              </h1>
            </div>
            <StatusBadge status={inspection.operational_status || status} />
          </div>

          {/* IMO Number */}
          {imo_number && (
            <p className="mb-2 text-sm text-gray-500">IMO: {imo_number}</p>
          )}

          {/* Type, Date, Location Row */}
          <div className="mb-3 space-y-1 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <span className="font-medium">{typeDisplay}</span>
              <span className="text-gray-400">|</span>
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {formatDate(inspection_date)}
              </span>
              <span className="text-gray-400">|</span>
              <span className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {locationDisplay}
              </span>
            </div>
          </div>

          {/* MOU, Authority, Inspector */}
          <div className="space-y-1 text-sm text-gray-600">
            {mou_code && (
              <p>
                <span className="text-gray-500">MOU:</span> {mou_code}
              </p>
            )}
            {authority && (
              <p>
                <span className="text-gray-500">Authority:</span> {authority}
              </p>
            )}
            {inspector_name && (
              <p className="flex items-center gap-1">
                <User className="h-4 w-4 text-gray-400" />
                <span className="text-gray-500">Inspector:</span> {inspector_name}
              </p>
            )}
            {report_reference && (
              <p>
                <span className="text-gray-500">Report Ref:</span>{' '}
                {report_reference}
              </p>
            )}
          </div>

          {/* Deficiencies Reported */}
          <div className="mt-3 text-sm text-gray-600">
            <span className="text-gray-500">Deficiencies Reported:</span>{' '}
            <span className="font-medium">
              {inspection.def_reported === 'YES'
                ? 'Yes'
                : inspection.def_reported === 'NO'
                  ? 'No'
                  : 'N/A'}
            </span>
          </div>

          {/* Detention Badge */}
          {is_detention && (
            <div className="mt-3 flex items-center gap-2 rounded-md bg-error-50 p-2 text-error-700">
              <AlertTriangle className="h-5 w-5" />
              <div>
                <span className="font-semibold">DETENTION</span>
                {detention_reason && (
                  <p className="text-sm">{detention_reason}</p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Inspection Reports Section (grouped by type) */}
      <Card>
        <CardContent className="p-4">
          <h2 className="mb-3 text-base font-semibold text-gray-900">
            INSPECTION REPORTS
          </h2>
          {reports.length > 0 ? (
            <div className="space-y-4">
              {/* Original Reports */}
              {(() => {
                const originalReports = reports.filter(
                  (r) => !r.report_type || r.report_type === 'ORIGINAL'
                );
                const followUpReports = reports.filter(
                  (r) => r.report_type === 'FOLLOW_UP'
                );
                return (
                  <>
                    {originalReports.length > 0 && (
                      <div>
                        <h3 className="mb-2 text-sm font-medium text-gray-500">
                          Original Report{originalReports.length > 1 ? 's' : ''}
                        </h3>
                        <div className="space-y-2">
                          {originalReports.map((report) => (
                            <ReportRow key={report.id} report={report} />
                          ))}
                        </div>
                      </div>
                    )}
                    {followUpReports.length > 0 && (
                      <div>
                        <h3 className="mb-2 text-sm font-medium text-gray-500">
                          Follow-up Report{followUpReports.length > 1 ? 's' : ''}
                        </h3>
                        <div className="space-y-2">
                          {followUpReports.map((report) => (
                            <ReportRow key={report.id} report={report} />
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No report attached</p>
          )}
        </CardContent>
      </Card>

      {/* Deficiencies Section */}
      <Card>
        <CardContent className="p-4">
          <DeficiencyList
            deficiencies={deficiencies}
            onAddDeficiency={onAddDeficiency}
            onDeficiencyClick={onDeficiencyClick}
            bulkSubmitEnabled={bulkSubmitEnabled}
            inspectionId={String(inspection.id)}
          />
        </CardContent>
      </Card>

      {/* Activity History Section (Collapsible) */}
      <Card>
        <CardContent className="p-4">
          <button
            type="button"
            onClick={() => setIsActivityExpanded(!isActivityExpanded)}
            className="flex w-full items-center justify-between text-left"
          >
            <h2 className="text-base font-semibold text-gray-900">
              ACTIVITY HISTORY ({activity_history.length})
            </h2>
            {isActivityExpanded ? (
              <ChevronUp className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-400" />
            )}
          </button>

          {isActivityExpanded && activity_history.length > 0 && (
            <div className="mt-3 space-y-2">
              {activity_history.map((event) => (
                <div
                  key={event.id}
                  className="flex items-start gap-2 text-sm text-gray-600"
                >
                  <Clock className="h-4 w-4 flex-shrink-0 text-gray-400 mt-0.5" />
                  <div>
                    <span>{event.event_description}</span>
                    <span className="ml-2 text-xs text-gray-400">
                      {formatDateTime(event.performed_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {isActivityExpanded && activity_history.length === 0 && (
            <p className="mt-3 text-sm text-gray-500 italic">
              No activity recorded yet
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
