import { type FormEvent, type ReactNode, useEffect, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
  ArchiveX,
  Activity,
  AlertTriangle,
  CornerDownRight,
  Download,
  Eye,
  FileCheck2,
  FileText,
  History,
  ListFilter,
  Plus,
  Printer,
  RotateCw,
  Save,
  Search,
  Share2,
  ShieldAlert,
  SlidersHorizontal,
  Trash2,
  UploadCloud,
  CheckCircle2,
} from 'lucide-react';

import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Checkbox,
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Textarea,
} from '@/components/ui';
import { useAuth } from '@/hooks/use-auth';
import { useCertsPermission, useHasAnyCertsForm } from '@/hooks/certs/use-certs-permission';
import {
  useCatalogRow,
  useCatalogRowAuditHistory,
  useCatalogRows,
  useCatalogRowsLazy,
  useCatalogSections,
  useBulkSoftDeleteCatalogRows,
  useCreateCatalogRow,
  useDeprecateCatalogRow,
  useUpdateCatalogRow,
} from '@/hooks/certs/use-catalog';
import { useAuditLog, useExportAuditLog } from '@/hooks/certs/use-audit-log';
import {
  useAuditorAccessGrants,
  useAuditorAccessGrant,
  useAuditorCert,
  useAuditorSignup,
  useAuditorVesselCerts,
  useAuditorVessels,
  useCreateAuditorAccessGrant,
  useGenerateAuditorPrint,
  useUpdateAuditorAccessGrantExpiry,
} from '@/hooks/certs/use-auditor-access';
import {
  useCreateOnboardingBatch,
  useCoverageOverride,
  useFmSignoff,
  useCommitOnboardingBatch,
  useOnboardingBatchGapFill,
  useOnboardingHub,
  useOnboardingWizardState,
  usePreviewOnboardingBatch,
  useRollbackOnboarding,
  useSaveOnboardingProfile,
} from '@/hooks/certs/use-onboarding';
import {
  useGeneratePrintArtifact,
  useGenerateShareBundle,
  usePrintArtifacts,
} from '@/hooks/certs/use-print';
import {
  useAddClassCodeMappingForFlag,
  useAcknowledgeMasterReconciliationMessage,
  useClassSnapshots,
  useMasterReconciliationMessages,
  useMarkReconciliationFlagReviewed,
  useNotifyMasterForReconciliationFlag,
  useReconciliationRun,
  useReconciliationRuns,
  useUploadClassSnapshot,
  useReparseClassSnapshot,
} from '@/hooks/certs/use-reconciliation';
import {
  useApproveTrackedItem,
  useRemoveTrackedItemPdf,
  useRejectTrackedItem,
  useReparseTrackedItemPdf,
  useSubmitTrackedItem,
  useTrackedItems,
  useTrackedItemDetail,
  useUpdateTrackedItemMetadata,
  useUploadTrackedItemPdf,
} from '@/hooks/certs/use-tracked-item';
import {
  useDecommissionVessel,
  useInitiateSaleHandover,
  useRecordClassChange,
  useRecordFlagChange,
  useFleetDashboard,
  useVesselDashboard,
  useVesselProfile,
} from '@/hooks/certs/use-vessel-dashboard';
import { useCertSettings, useUpdateCertSettings } from '@/hooks/certs/use-settings';
import {
  certsApi,
  type CertCatalogAuditEntry,
  type CertCatalogSection,
  type CertAuditLogEntry,
  type CertAuditLogFilters,
  type CertAuditorAccessGrant,
  type CertCatalogInlinePromotionContext,
  type CertCatalogRow,
  type CertClassSnapshot,
  type CertGapFillFieldState,
  type CertGapFillPdf,
  type CertOnboardingBatch,
  type CertOnboardingHubRow,
  type CertMasterReconciliationMessage,
  type CertReconciliationAnomalyBreach,
  type CertReconciliationFlag,
  type CertReconciliationRun,
  type CertReconciliationRunDetail,
  type CertTrackedItemAuditEvent,
  type CertTrackedItemDetail,
  type CertTrackedItemFilters,
  type CertTrackedItem,
  type CertPrintArtifact,
  type CertPrintDownloadKind,
  type CertValidationEntry,
  type CertFleetDashboardVessel,
  type CertFleetDashboardResponse,
  type CertVesselLifecycleResponse,
  type CertVesselDashboardResponse,
  type CertVesselDashboardSection,
  type CertAlertConfig,
  type CertSettingsResponse,
  type CertSlackRoute,
} from '@/lib/api/certs';
import { getCertsHomeRoute, getCertsVesselIdentifier } from '@/lib/certs/navigation';
import { ROUTES } from '@/lib/utils/constants';
import { FORM_IDS, PROCESS_IDS } from '@/lib/utils/permission-ids';
import { getErrorMessage } from '@/lib/api/client';

import './certs-theme.css';

const CATALOG_WRITER_ROLES = new Set(['DPA', 'SEQ MANAGER', 'ADMIN', 'SUPER ADMIN', 'SYSTEM ADMIN']);
const PARSER_OPS_DEV_ENABLED = import.meta.env.DEV && import.meta.env.VITE_CERTS_PARSER_OPS_ENABLED !== 'false';
const SHIP_TYPE_OPTIONS = [
  { value: 'all', label: 'All ships' },
  { value: 'bulk_carrier', label: 'Bulk carrier' },
  { value: 'tanker', label: 'Tanker' },
  { value: 'container', label: 'Container' },
  { value: 'gas_carrier', label: 'Gas carrier' },
  { value: 'chemical_tanker', label: 'Chemical tanker' },
] as const;
const SPECIFIC_SHIP_TYPE_OPTIONS = SHIP_TYPE_OPTIONS.filter((option) => option.value !== 'all');
const APPLICABILITY_MODE_OPTIONS = [
  { value: 'all_matching_type', label: 'All matching ship type' },
  { value: 'specific_vessel_ids', label: 'Specific vessels' },
] as const;
const CATALOG_VALIDITY_TYPE_OPTIONS = [
  { value: 'full', label: 'Full' },
  { value: 'conditional', label: 'Conditional' },
  { value: 'short_term', label: 'Short term' },
  { value: 'permanent', label: 'Permanent' },
] as const;
const CATALOG_ISSUING_AUTHORITY_TYPE_OPTIONS = [
  { value: 'flag', label: 'Flag' },
  { value: 'class', label: 'Class' },
  { value: 'RO', label: 'Recognized organization' },
  { value: 'manufacturer', label: 'Manufacturer' },
  { value: 'company', label: 'Company' },
  { value: 'ko_other', label: 'Other' },
] as const;
const CATALOG_SUBMISSION_SCOPE_OPTIONS = [
  { value: 'all_ranks_with_approval', label: 'All ranks with approval' },
] as const;
const CLASS_MAPPING_KIND_OPTIONS = [
  { value: 'renewal', label: 'Renewal' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'annual', label: 'Annual' },
  { value: 'periodic', label: 'Periodic' },
  { value: 'n/a', label: 'N/A' },
] as const;
const ROLLUP_ROW_TOKENS = [
  'PORTABLE-FIRE-EXTINGUISHER',
  'PORTABLE-EXTINGUISHER',
  'EXTINGUISHER-ANNUAL',
  'LIFEBUOY',
  'LIFEBUOYS',
  'LIFE-JACKET',
  'LIFE-JACKETS',
  'LIFEJACKET',
  'LIFEJACKETS',
  'HATCH-COVER',
  'HATCH-COVERS',
] as const;
const ACTION_STATUSES = new Set([
  'overdue',
  'expired',
  'window_open',
  'window_closing',
  'pending_first_upload',
  'expired_at_onboarding',
  'invalid_due_to_reflag',
  'pending_supersession',
]);
const RECONCILIATION_BUCKET_TABS = [
  { bucket: 'match', label: 'Match', countKey: 'matchesCount' },
  { bucket: 'mismatch', label: 'Different', countKey: 'mismatchesCount' },
  { bucket: 'missing_in_catalog', label: 'Add to VIMS', countKey: 'missingInCatalogCount' },
  { bucket: 'conditional_stc', label: 'Short term', countKey: 'conditionalStcDetectedCount' },
  { bucket: 'extended_postponed', label: 'Extension or postponement', countKey: 'extendedPostponedDetectedCount' },
  { bucket: 'conditions_of_class', label: 'Conditions of class', countKey: null },
  { bucket: 'unmapped_low_confidence', label: 'Check report item', countKey: 'unmappedLowConfidenceCount' },
] as const;
const RECONCILIATION_HIDE_WHEN_EMPTY_BUCKETS = new Set(['extended_postponed', 'unmapped_low_confidence']);

type CertAuthContext = {
  role?: unknown;
  hasForm?: (formId: string) => boolean;
  vesselId?: string | null;
  user?: {
    role_name?: unknown;
    safety_role_name?: unknown;
    vessel_id?: string | null;
    vessel_code?: string | null;
  } | null;
};

function normalizeAuthRole(auth: CertAuthContext): string {
  return String(auth.role ?? auth.user?.role_name ?? auth.user?.safety_role_name ?? '').trim().toUpperCase();
}

function isParserOpsRole(role: string): boolean {
  return [
    'TECHNICAL SUPERINTENDENT',
    "TECH SUP'TT",
    'TECH SUPT',
    'TECHNICAL SUPT',
  ].some((marker) => role.includes(marker));
}

function isFleetManagerRole(role: string): boolean {
  return role === 'FM' || role === 'FLEET MANAGER' || role.includes('FLEET MANAGER');
}

function isDpaRole(role: string): boolean {
  return ['DPA', 'SEQ MANAGER', 'ADMIN', 'SUPER ADMIN', 'SYSTEM ADMIN'].includes(role);
}

function isDpaApprovalRole(role: string): boolean {
  return ['DPA', 'SEQ MANAGER'].includes(role) || role.includes('DESIGNATED PERSON');
}

function isPicRole(role: string): boolean {
  return ['PIC', 'OFFICE_PIC', 'OFFICE PIC'].includes(role) || role.includes('PERSON IN CHARGE');
}

function isMasterRole(role: string): boolean {
  return role.includes('MASTER') || role.includes('CAPTAIN');
}

function canDecideCertApproval(auth: ReturnType<typeof useAuth>): boolean {
  const role = normalizeAuthRole(auth);
  return isMasterRole(role) || (auth.isOffice && (isDpaApprovalRole(role) || isPicRole(role)));
}

function canOpenCertApprovalQueue(auth: ReturnType<typeof useAuth>): boolean {
  const role = normalizeAuthRole(auth);
  return auth.hasForm?.(FORM_IDS.CERTS_TRACKED_ITEMS) === true && (auth.isOffice || isMasterRole(role));
}

function CertsPermissionDenied() {
  return (
    <RootLayout>
      <section className="flex min-h-[60vh] items-center justify-center">
        <Card className="w-full max-w-xl">
          <CardContent className="space-y-5 p-6 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-red-50 text-red-600">
              <ShieldAlert className="h-6 w-6" aria-hidden="true" />
            </div>
            <div className="space-y-2">
              <h1 className="text-xl font-semibold text-neutral-900">
                You don&apos;t have access to this page.
              </h1>
            </div>
            <Button asChild>
              <Link to={ROUTES.DASHBOARD}>Back to Fleet Dashboard</Link>
            </Button>
          </CardContent>
        </Card>
      </section>
    </RootLayout>
  );
}

function CertsInlineError({ title, message, onRetry }: { title: string; message: string; onRetry?: () => void }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" aria-hidden="true" />
        <div className="min-w-0 flex-1 space-y-2">
          <p className="font-semibold">{title}</p>
          <p className="text-red-700">{message}</p>
          {onRetry ? (
            <Button type="button" size="sm" variant="outline" onClick={onRetry}>
              Try again
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function CertsLandingStub() {
  const auth = useAuth();
  const role = normalizeAuthRole(auth);
  const canReadCatalog = auth.hasForm?.(FORM_IDS.CERTS_CATALOG) === true;
  const canReadTrackedItems = auth.hasForm?.(FORM_IDS.CERTS_TRACKED_ITEMS) === true;
  const canReadReconciliation = auth.hasForm?.(FORM_IDS.CERTS_RECONCILIATION) === true;
  const vesselDashboardIdentifier = getCertsVesselIdentifier(auth);
  const showOfficeVesselList = canReadTrackedItems && !vesselDashboardIdentifier;
  const showHighVolumePrintCard = isFleetManagerRole(role) && auth.hasForm?.(FORM_IDS.CERTS_PRINT_EXPORT);
  const showBouncingEmailCard = isDpaRole(role) && auth.hasForm?.(FORM_IDS.CERTS_TRACKED_ITEMS);
  const showHeartbeatCard = isDpaRole(role) && auth.hasForm?.(FORM_IDS.CERTS_TRACKED_ITEMS);
  const showApprovalQueue = canOpenCertApprovalQueue(auth);

  return (
    <RootLayout>
      <PageHeader title="Certificates" />
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-6">
        <div className="certs-landing-header flex flex-col gap-4 rounded-lg border border-neutral-200 bg-white px-5 py-5 sm:flex-row sm:items-center sm:justify-between md:px-6">
          <div className="flex items-center gap-3">
            <div className="certs-icon-tile flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
              <FileCheck2 className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-neutral-900">Certificate Register</h2>
              <p className="mt-1 text-sm text-neutral-500">Vessel certificates, renewals and reminders in one place.</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 sm:justify-end">
            {canReadCatalog ? (
              <Button asChild variant="outline">
                <Link to={ROUTES.CERTS_CATALOG}>Open catalog</Link>
              </Button>
            ) : null}
            {canReadReconciliation ? (
              <Button asChild variant="outline">
                <Link to={ROUTES.CERTS_RECONCILIATION}>Class reconciliation</Link>
              </Button>
            ) : null}
            {canReadTrackedItems && vesselDashboardIdentifier ? (
              <Button asChild>
                <Link to={ROUTES.CERTS_VESSEL_DASHBOARD(vesselDashboardIdentifier)}>Open vessel certificates</Link>
              </Button>
            ) : null}
            {showApprovalQueue ? (
              <Button asChild variant="outline">
                <Link to={ROUTES.CERTS_APPROVALS}>Pending approvals</Link>
              </Button>
            ) : null}
          </div>
        </div>
        {showApprovalQueue ? <CertApprovalQueueSummaryCard /> : null}
        {canReadReconciliation ? <CertClassReconciliationEntryCard /> : null}
        {showOfficeVesselList ? <CertOfficeVesselListCard /> : null}
        {showHeartbeatCard ? <CertFleetCadenceHeartbeatCard /> : null}
        {showBouncingEmailCard ? <CertFleetBouncingEmailCard /> : null}
        {showHighVolumePrintCard ? <CertFleetHighVolumePrintCard /> : null}
      </section>
    </RootLayout>
  );
}

function CertClassReconciliationEntryCard() {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-sky-50 text-sky-700">
            <Activity className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-neutral-900">Class Reconciliation</h2>
            <p className="text-sm text-neutral-600">
              Upload class status PDFs and review mismatches, STC, extensions, and postponed items.
            </p>
          </div>
        </div>
        <Button asChild variant="outline">
          <Link to={ROUTES.CERTS_RECONCILIATION}>Open Class Reconciliation</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

function CertApprovalQueueSummaryCard() {
  const pending = useTrackedItems({ approvalState: 'pending_master_approval', page: 1, pageSize: 1 });
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-amber-50 text-amber-700">
            <CheckCircle2 className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-neutral-900">Pending approval</h2>
            <p className="text-sm text-neutral-600">
              {pending.isLoading ? 'Checking uploaded certificates...' : `${pending.data?.count ?? 0} upload request${(pending.data?.count ?? 0) === 1 ? '' : 's'} waiting.`}
            </p>
          </div>
        </div>
        <Button asChild>
          <Link to={ROUTES.CERTS_APPROVALS}>Open approval queue</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

function CertOfficeVesselListCard() {
  const dashboard = useFleetDashboard();
  const vessels = dashboard.data?.onboardedVessels ?? [];

  return (
    <Card className="overflow-hidden">
      <CardHeader className="certs-section-header border-b border-neutral-200 bg-neutral-50/70 px-5 py-4">
        <CardTitle className="text-base">Vessel Certificates</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {dashboard.isLoading ? (
          <div className="space-y-2 p-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : dashboard.isError ? (
          <div className="p-4">
            <CertsInlineError
              title="Could not load vessels"
              message={`Could not load onboarded vessels. ${getErrorMessage(dashboard.error)}`}
              onRetry={() => dashboard.refetch()}
            />
          </div>
        ) : vessels.length === 0 ? (
          <p className="p-5 text-sm text-neutral-600">No onboarded vessels available for your Certs access.</p>
        ) : (
          <div className="divide-y divide-neutral-200">
            {vessels.map((vessel) => {
              const vesselRouteId = vessel.imo || vessel.id;
              return (
                <div key={vessel.id} className="certs-vessel-row flex flex-col gap-4 px-5 py-4 transition-colors hover:bg-neutral-50 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0 space-y-2">
                    <div>
                      <p className="font-semibold text-neutral-900">{vessel.name ?? vessel.code ?? vessel.imo ?? 'Vessel'}</p>
                      <p className="text-sm text-neutral-600">
                        {[vessel.imo ? `IMO ${vessel.imo}` : null, vessel.code].filter(Boolean).join(' - ')}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs">
                      <span className="rounded-md bg-neutral-100 px-2 py-1 text-neutral-700">{vessel.trackedItemCount} certificates</span>
                      <span className="rounded-md bg-amber-50 px-2 py-1 text-amber-700">{vessel.actionItemCount} need attention</span>
                      <span className="rounded-md bg-red-50 px-2 py-1 text-red-700">{vessel.pdfMissingCount} Certificates missing</span>
                    </div>
                  </div>
                  <Button asChild variant="outline" className="w-full sm:w-auto">
                    <Link to={ROUTES.CERTS_VESSEL_DASHBOARD(vesselRouteId)}>Open certificates</Link>
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CertApprovalQueuePage() {
  const auth = useAuth();
  const canOpenQueue = canOpenCertApprovalQueue(auth);
  const canDecide = canDecideCertApproval(auth);
  const pending = useTrackedItems({ approvalState: 'pending_master_approval', page: 1, pageSize: 100 }, canOpenQueue);

  if (!canOpenQueue) {
    return <CertsPermissionDenied />;
  }

  return (
    <RootLayout>
      <PageHeader title="Certificate Approvals" />
      <section className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-6">
        <Card>
          <CardHeader className="border-b border-neutral-200 bg-neutral-50/70">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle>Pending approval</CardTitle>
                <p className="mt-1 text-sm text-neutral-600">
                  Uploaded certificates waiting for Master, PIC, or DPA review.
                </p>
              </div>
              <Badge variant="warning">{pending.data?.count ?? 0} pending</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {pending.isLoading ? (
              <div className="space-y-2 p-4">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : pending.isError ? (
              <div className="p-4">
                <CertsInlineError
                  title="Could not load approvals"
                  message={`Could not load pending certificate approvals. ${getErrorMessage(pending.error)}`}
                  onRetry={() => pending.refetch()}
                />
              </div>
            ) : !pending.data?.results.length ? (
              <div className="p-6 text-center text-sm text-neutral-600">
                No certificate uploads are waiting for approval.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-200 text-sm">
                  <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                    <tr>
                      <th className="px-4 py-3">Certificate</th>
                      <th className="px-4 py-3">Vessel</th>
                      <th className="px-4 py-3">Submitted by</th>
                      <th className="px-4 py-3">Submitted at</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100">
                    {pending.data.results.map((item) => (
                      <CertApprovalQueueRow
                        key={item.id}
                        item={item}
                        canDecide={canDecide}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </RootLayout>
  );
}

function CertApprovalQueueRow({ item, canDecide }: { item: CertTrackedItem; canDecide: boolean }) {
  const auth = useAuth();
  const imo = item.vesselImo || item.vesselId || '';
  const [reason, setReason] = useState('');
  const approveMutation = useApproveTrackedItem(item.id, imo);
  const rejectMutation = useRejectTrackedItem(item.id, imo);
  const canApprove = canDecide && auth.hasProcess?.(PROCESS_IDS.CERTS_APPROVE) === true;
  const canReject = canDecide && auth.hasProcess?.(PROCESS_IDS.CERTS_REJECT) === true;
  const detailHref = ROUTES.CERTS_TRACKED_ITEM_DETAIL(imo, item.id);
  const transitionPayload = () => ({
    reason: reason.trim() || 'Certificate reviewed from approval queue.',
    version: item.version,
  });
  const mutationError = approveMutation.error ?? rejectMutation.error;

  return (
    <tr className="align-top hover:bg-neutral-50">
      <td className="min-w-72 px-4 py-4">
        <Link className="font-medium text-neutral-900 hover:text-primary-600" to={detailHref}>
          {item.displayName ?? item.catalogDisplayName ?? item.catalogCode}
        </Link>
        <p className="mt-1 text-xs text-neutral-500">{item.certificateNumber ?? 'Certificate number not set'}</p>
      </td>
      <td className="px-4 py-4 text-neutral-700">
        <div className="font-medium text-neutral-900">{item.vesselName ?? item.vesselCode ?? item.vesselImo ?? 'Vessel'}</div>
        <div className="text-xs text-neutral-500">{item.vesselImo ? `IMO ${item.vesselImo}` : item.vesselCode}</div>
      </td>
      <td className="px-4 py-4 text-neutral-700">{formatPrincipalLabel(item.submittedByDisplay, item.submittedBy, undefined, 'Not recorded')}</td>
      <td className="px-4 py-4 text-neutral-700">{formatDateTime(item.submittedAt)}</td>
      <td className="px-4 py-4"><Badge variant="warning">Pending approval</Badge></td>
      <td className="min-w-72 px-4 py-4">
        {canApprove || canReject ? (
          <div className="space-y-2">
            <Textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Add a short review note"
              rows={2}
            />
            {mutationError ? <p className="text-xs text-error-700">{getErrorMessage(mutationError)}</p> : null}
            <div className="flex flex-wrap gap-2">
              {canApprove ? (
                <Button size="sm" type="button" onClick={() => approveMutation.mutate(transitionPayload())} disabled={approveMutation.isPending}>
                  Approve
                </Button>
              ) : null}
              {canReject ? (
                <Button size="sm" type="button" variant="destructive" onClick={() => rejectMutation.mutate(transitionPayload())} disabled={rejectMutation.isPending || reason.trim().length < 10}>
                  Reject
                </Button>
              ) : null}
            </div>
          </div>
        ) : (
          <Button asChild size="sm" variant="outline">
            <Link to={detailHref}>Open request</Link>
          </Button>
        )}
      </td>
    </tr>
  );
}

function CertAuditLogPage() {
  const auth = useAuth();
  const canReadAuditLog = auth.hasForm?.(FORM_IDS.CERTS_AUDIT_LOG) === true;

  if (!canReadAuditLog) {
    return <CertsPermissionDenied />;
  }

  return <CertAuditLogContent />;
}

function CertSettingsPage() {
  const auth = useAuth();
  const role = normalizeAuthRole(auth);
  const canReadSettings = isDpaRole(role) && auth.hasForm?.(FORM_IDS.CERTS_NOTIFICATION_CONFIG) === true;
  const canWriteSettings =
    canReadSettings && auth.hasProcess?.(PROCESS_IDS.CERTS_CATALOG_EDIT) === true;

  if (!canReadSettings) {
    return <CertsPermissionDenied />;
  }

  return <CertSettingsContent canWrite={canWriteSettings} />;
}

function CertSettingsContent({ canWrite }: { canWrite: boolean }) {
  const settings = useCertSettings(true);
  const updateSettings = useUpdateCertSettings();
  const [activeTab, setActiveTab] = useState<'alerts' | 'ocr' | 'parser' | 'retention' | 'slack'>('alerts');
  const [draft, setDraft] = useState<CertSettingsResponse | null>(null);
  const [retentionBlobId, setRetentionBlobId] = useState('');
  const [retentionUntil, setRetentionUntil] = useState('');
  const [reason, setReason] = useState('');

  useEffect(() => {
    if (settings.data) {
      setDraft(settings.data);
    }
  }, [settings.data]);

  const updateAlert = (id: string, field: keyof CertAlertConfig, value: string | number | null | Record<string, unknown> | string[]) => {
    setDraft((current) => {
      if (!current) return current;
      return {
        ...current,
        alertConfigs: current.alertConfigs.map((config) => (
          config.id === id ? { ...config, [field]: value } : config
        )),
      };
    });
  };

  const updateSlack = (vesselId: string, field: keyof CertSlackRoute, value: string) => {
    setDraft((current) => {
      if (!current) return current;
      return {
        ...current,
        slackRoutes: current.slackRoutes.map((route) => (
          route.vesselId === vesselId ? { ...route, [field]: value } : route
        )),
      };
    });
  };

  const submitSettings = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!draft || !canWrite) return;
    updateSettings.mutate({
      alertConfigs: draft.alertConfigs.map((config) => ({
        id: config.id,
        dpaOverrideLeadDays: numberOrNull(config.dpaOverrideLeadDays),
        dpaOverrideRecipients: config.dpaOverrideRecipients,
        escalationCadence: config.escalationCadence,
        ocrThresholdOffice: thresholdString(config.ocrThresholdOffice),
        ocrThresholdVessel: thresholdString(config.ocrThresholdVessel),
        ocrThresholdManualFloor: thresholdString(config.ocrThresholdManualFloor),
        classSnapshotCadenceMonths: Number(config.classSnapshotCadenceMonths),
        classSnapshotLeadMonths: Number(config.classSnapshotLeadMonths),
        eventSnapshotGraceDays: Number(config.eventSnapshotGraceDays),
        draftExpireDays: Number(config.draftExpireDays),
      })),
      retentionOverride: retentionBlobId.trim()
        ? {
            blobId: retentionBlobId.trim(),
            dpaRetentionOverrideUntil: retentionUntil ? new Date(retentionUntil).toISOString() : null,
          }
        : undefined,
      slackRoutes: draft.slackRoutes.map((route) => ({
        vesselId: route.vesselId,
        slackChannelVessel: route.slackChannelVessel || '',
        slackChannelOfficeDefault: route.slackChannelOfficeDefault || '',
      })),
      reason,
    });
  };

  if (settings.isLoading || !draft) {
    return (
      <RootLayout>
        <PageHeader title="Certs Settings" />
        <section className="mx-auto grid w-full max-w-6xl gap-4 px-4 py-6">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-64 w-full" />
        </section>
      </RootLayout>
    );
  }

  if (settings.isError) {
    return (
      <RootLayout>
        <PageHeader title="Certs Settings" />
        <section className="mx-auto w-full max-w-6xl px-4 py-6">
          <Card>
            <CardContent className="space-y-4 p-6">
              <h1 className="text-xl font-semibold text-neutral-900">Settings unavailable</h1>
              <p className="text-sm text-neutral-600">{getErrorMessage(settings.error)}</p>
              <Button type="button" variant="outline" onClick={() => settings.refetch()}>
                Retry
              </Button>
            </CardContent>
          </Card>
        </section>
      </RootLayout>
    );
  }

  const tabs = [
    { id: 'alerts', label: 'Alert lead times' },
    { id: 'ocr', label: 'OCR thresholds' },
    { id: 'parser', label: 'Parser version' },
    { id: 'retention', label: 'Retention overrides' },
    { id: 'slack', label: 'Slack routing' },
  ] as const;

  return (
    <RootLayout>
      <PageHeader title="Certs Settings" />
      <form onSubmit={submitSettings} className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 py-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary-50 text-primary-700">
              <SlidersHorizontal className="h-5 w-5" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-neutral-900">Certs Settings</h1>
              <p className="text-sm text-neutral-600">Last updated {formatDateTime(draft.updatedAt) || 'not recorded'}</p>
            </div>
          </div>
          <Badge variant={canWrite ? 'success' : 'secondary'}>{canWrite ? 'DPA edit' : 'Read only'}</Badge>
        </div>

        <div className="flex flex-wrap gap-2 rounded-md border border-neutral-200 bg-white p-2">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              type="button"
              variant={activeTab === tab.id ? 'default' : 'ghost'}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </Button>
          ))}
        </div>

        {activeTab === 'alerts' ? <SettingsAlertLeadTimes configs={draft.alertConfigs} canWrite={canWrite} onChange={updateAlert} /> : null}
        {activeTab === 'ocr' ? <SettingsOcrThresholds configs={draft.alertConfigs} canWrite={canWrite} onChange={updateAlert} /> : null}
        {activeTab === 'parser' ? <SettingsParserCadence configs={draft.alertConfigs} canWrite={canWrite} onChange={updateAlert} /> : null}
        {activeTab === 'retention' ? (
          <SettingsRetentionOverride
            canWrite={canWrite}
            blobId={retentionBlobId}
            until={retentionUntil}
            onBlobIdChange={setRetentionBlobId}
            onUntilChange={setRetentionUntil}
          />
        ) : null}
        {activeTab === 'slack' ? <SettingsSlackRoutes routes={draft.slackRoutes} canWrite={canWrite} onChange={updateSlack} /> : null}

        <Card>
          <CardContent className="grid gap-4 p-4 md:grid-cols-[1fr_auto] md:items-end">
            <div className="space-y-2">
              <Label htmlFor="settings-change-reason">Change reason</Label>
              <Textarea
                id="settings-change-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                disabled={!canWrite}
                minLength={20}
                required
              />
            </div>
            <Button type="submit" disabled={!canWrite || updateSettings.isPending || reason.trim().length < 20}>
              <Save className="mr-2 h-4 w-4" aria-hidden="true" />
              Save settings
            </Button>
            {updateSettings.error ? (
              <p className="text-sm text-red-600 md:col-span-2">{getErrorMessage(updateSettings.error)}</p>
            ) : null}
          </CardContent>
        </Card>
      </form>
    </RootLayout>
  );
}

function SettingsAlertLeadTimes({
  configs,
  canWrite,
  onChange,
}: {
  configs: CertAlertConfig[];
  canWrite: boolean;
  onChange: (id: string, field: keyof CertAlertConfig, value: string | number | null | Record<string, unknown> | string[]) => void;
}) {
  if (!configs.length) {
    return <SettingsEmptyState title="No alert configuration rows" />;
  }
  return (
    <div className="grid gap-3">
      {configs.map((config) => (
        <Card key={config.id}>
          <CardHeader>
            <CardTitle className="text-base">{formatSettingsToken(config.triggerEvent)}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor={`default-lead-${config.id}`}>Default lead days</Label>
              <Input id={`default-lead-${config.id}`} value={config.defaultLeadDays} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor={`override-lead-${config.id}`}>DPA override lead days</Label>
              <Input
                id={`override-lead-${config.id}`}
                type="number"
                min={0}
                max={365}
                value={config.dpaOverrideLeadDays ?? ''}
                disabled={!canWrite}
                onChange={(event) => onChange(config.id, 'dpaOverrideLeadDays', event.target.value ? Number(event.target.value) : null)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={`draft-expire-${config.id}`}>Draft expiry days</Label>
              <Input
                id={`draft-expire-${config.id}`}
                type="number"
                min={1}
                max={30}
                value={config.draftExpireDays}
                disabled={!canWrite}
                onChange={(event) => onChange(config.id, 'draftExpireDays', Number(event.target.value))}
              />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function SettingsOcrThresholds({
  configs,
  canWrite,
  onChange,
}: {
  configs: CertAlertConfig[];
  canWrite: boolean;
  onChange: (id: string, field: keyof CertAlertConfig, value: string) => void;
}) {
  const config = configs[0];
  if (!config) {
    return <SettingsEmptyState title="No OCR threshold row" />;
  }
  return (
    <Card>
      <CardContent className="grid gap-4 p-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="office-ocr-threshold">Office OCR threshold</Label>
          <Input
            id="office-ocr-threshold"
            type="number"
            min="0"
            max="1"
            step="0.001"
            value={config.ocrThresholdOffice}
            disabled={!canWrite}
            onChange={(event) => onChange(config.id, 'ocrThresholdOffice', event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="vessel-ocr-threshold">Vessel OCR threshold</Label>
          <Input
            id="vessel-ocr-threshold"
            type="number"
            min="0"
            max="1"
            step="0.001"
            value={config.ocrThresholdVessel}
            disabled={!canWrite}
            onChange={(event) => onChange(config.id, 'ocrThresholdVessel', event.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="manual-floor-threshold">Manual floor threshold</Label>
          <Input
            id="manual-floor-threshold"
            type="number"
            min="0"
            max="1"
            step="0.001"
            value={config.ocrThresholdManualFloor}
            disabled={!canWrite}
            onChange={(event) => onChange(config.id, 'ocrThresholdManualFloor', event.target.value)}
          />
        </div>
      </CardContent>
    </Card>
  );
}

function SettingsParserCadence({
  configs,
  canWrite,
  onChange,
}: {
  configs: CertAlertConfig[];
  canWrite: boolean;
  onChange: (id: string, field: keyof CertAlertConfig, value: number) => void;
}) {
  const config = configs[0];
  if (!config) {
    return <SettingsEmptyState title="No parser cadence row" />;
  }
  return (
    <Card>
      <CardContent className="grid gap-4 p-4 md:grid-cols-3">
        <div className="space-y-2">
          <Label htmlFor="snapshot-cadence-months">Class snapshot cadence months</Label>
          <Input id="snapshot-cadence-months" type="number" min={1} max={24} value={config.classSnapshotCadenceMonths} disabled={!canWrite} onChange={(event) => onChange(config.id, 'classSnapshotCadenceMonths', Number(event.target.value))} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="snapshot-lead-months">Class snapshot lead months</Label>
          <Input id="snapshot-lead-months" type="number" min={0} max={12} value={config.classSnapshotLeadMonths} disabled={!canWrite} onChange={(event) => onChange(config.id, 'classSnapshotLeadMonths', Number(event.target.value))} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="event-grace-days">Event snapshot grace days</Label>
          <Input id="event-grace-days" type="number" min={0} max={90} value={config.eventSnapshotGraceDays} disabled={!canWrite} onChange={(event) => onChange(config.id, 'eventSnapshotGraceDays', Number(event.target.value))} />
        </div>
      </CardContent>
    </Card>
  );
}

function SettingsRetentionOverride({
  canWrite,
  blobId,
  until,
  onBlobIdChange,
  onUntilChange,
}: {
  canWrite: boolean;
  blobId: string;
  until: string;
  onBlobIdChange: (value: string) => void;
  onUntilChange: (value: string) => void;
}) {
  return (
    <Card>
      <CardContent className="grid gap-4 p-4 md:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="retention-blob-id">PDF blob ID</Label>
          <Input id="retention-blob-id" value={blobId} disabled={!canWrite} onChange={(event) => onBlobIdChange(event.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="retention-override-until">Retention override until</Label>
          <Input id="retention-override-until" type="datetime-local" value={until} disabled={!canWrite} onChange={(event) => onUntilChange(event.target.value)} />
        </div>
      </CardContent>
    </Card>
  );
}

function SettingsSlackRoutes({
  routes,
  canWrite,
  onChange,
}: {
  routes: CertSlackRoute[];
  canWrite: boolean;
  onChange: (vesselId: string, field: keyof CertSlackRoute, value: string) => void;
}) {
  if (!routes.length) {
    return <SettingsEmptyState title="No vessel Slack routes" />;
  }
  return (
    <div className="grid gap-3">
      {routes.map((route, index) => (
        <Card key={route.vesselId}>
          <CardHeader>
            <CardTitle className="text-base">{route.vesselName || formatEntityLabel(route.vesselId, 'Vessel')}</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor={`vessel-slack-${route.vesselId}`}>Vessel Slack channel</Label>
              <Input
                id={`vessel-slack-${route.vesselId}`}
                aria-label={index === 0 ? 'Vessel Slack channel' : `Vessel Slack channel ${route.vesselName || formatEntityLabel(route.vesselId, 'Vessel')}`}
                value={route.slackChannelVessel || ''}
                disabled={!canWrite}
                onChange={(event) => onChange(route.vesselId, 'slackChannelVessel', event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor={`office-slack-${route.vesselId}`}>Office Slack channel</Label>
              <Input
                id={`office-slack-${route.vesselId}`}
                value={route.slackChannelOfficeDefault || ''}
                disabled={!canWrite}
                onChange={(event) => onChange(route.vesselId, 'slackChannelOfficeDefault', event.target.value)}
              />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function SettingsEmptyState({ title }: { title: string }) {
  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="text-base font-semibold text-neutral-900">{title}</h2>
      </CardContent>
    </Card>
  );
}

function thresholdString(value: string | number): string {
  return typeof value === 'number' ? value.toFixed(3) : value;
}

function numberOrNull(value: number | string | null): number | null {
  if (value === null || value === '') return null;
  return Number(value);
}

function formatSettingsToken(value: string): string {
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function CertAuditLogContent() {
  const auth = useAuth();
  const role = normalizeAuthRole(auth);
  const [filters, setFilters] = useState<CertAuditLogFilters>({ page: 1, pageSize: 25 });
  const [coldConfirmed, setColdConfirmed] = useState(false);
  const needsColdPrompt = filters.retentionTier === 'cold' && !coldConfirmed;
  const canExportAuditLog =
    isDpaRole(role) &&
    auth.hasForm?.(FORM_IDS.CERTS_AUDIT_LOG) === true &&
    auth.hasProcess?.(PROCESS_IDS.CERTS_PRINT) === true;

  const auditLog = useAuditLog(filters, !needsColdPrompt);

  const updateFilter = (key: keyof CertAuditLogFilters, value: string) => {
    setFilters((current) => ({
      ...current,
      [key]: value || null,
      page: 1,
      pageSize: 25,
    }));
    if (key === 'retentionTier') {
      setColdConfirmed(value !== 'cold');
    }
  };

  return (
    <RootLayout>
      <PageHeader title="Audit Log" />
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <History className="h-4 w-4" aria-hidden="true" />
              Audit filters
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            <div className="space-y-1.5">
              <Label htmlFor="auditVesselId">Vessel ID</Label>
              <Input
                id="auditVesselId"
                value={filters.vesselId ?? ''}
                onChange={(event) => updateFilter('vesselId', event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="auditActorUserId">Actor</Label>
              <Input
                id="auditActorUserId"
                value={filters.actorUserId ?? ''}
                onChange={(event) => updateFilter('actorUserId', event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="auditEntityType">Entity type</Label>
              <Input
                id="auditEntityType"
                value={filters.entityType ?? ''}
                onChange={(event) => updateFilter('entityType', event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="auditAction">Action</Label>
              <Input
                id="auditAction"
                value={filters.action ?? ''}
                onChange={(event) => updateFilter('action', event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="auditRetentionTier">Retention tier</Label>
              <select
                id="auditRetentionTier"
                className="flex h-10 w-full rounded-md border border-neutral-200 bg-white px-3 py-2 text-sm text-neutral-900 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                value={filters.retentionTier ?? ''}
                onChange={(event) => updateFilter('retentionTier', event.target.value)}
              >
                <option value="">All tiers</option>
                <option value="hot">Hot</option>
                <option value="cold">Cold</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="auditDateFrom">Date from</Label>
              <Input
                id="auditDateFrom"
                type="date"
                value={filters.dateFrom ?? ''}
                onChange={(event) => updateFilter('dateFrom', event.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {canExportAuditLog ? <CertAuditLogExportPanel filters={filters} /> : null}

        {needsColdPrompt ? (
          <Card className="border-amber-200 bg-amber-50">
            <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
              <p className="text-sm font-medium text-amber-900">This range includes archived entries.</p>
              <Button type="button" variant="outline" onClick={() => setColdConfirmed(true)}>
                Continue
              </Button>
            </CardContent>
          </Card>
        ) : null}

        <Card>
          <CardContent className="p-0">
            {auditLog.isLoading ? (
              <div className="space-y-3 p-4">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-2/3" />
              </div>
            ) : auditLog.isError ? (
              <div className="p-4 text-sm text-red-700">{getErrorMessage(auditLog.error)}</div>
            ) : auditLog.data?.results.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-200 text-sm">
                  <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                    <tr>
                      <th className="px-4 py-3">Time</th>
                      <th className="px-4 py-3">Action</th>
                      <th className="px-4 py-3">Actor</th>
                      <th className="px-4 py-3">Vessel</th>
                      <th className="px-4 py-3">Entity</th>
                      <th className="px-4 py-3">Diff</th>
                      <th className="px-4 py-3">Reason</th>
                      <th className="px-4 py-3">Tier</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 bg-white text-neutral-700">
                    {auditLog.data.results.map((entry) => (
                      <tr key={entry.id}>
                        <td className="whitespace-nowrap px-4 py-3">{formatDateTime(entry.timestampUtc)}</td>
                        <td className="px-4 py-3 font-medium text-neutral-900">{formatAuditAction(entry.action)}</td>
                        <td className="whitespace-nowrap px-4 py-3">{formatPrincipalLabel(undefined, entry.actorUserId, entry.actorRole)}</td>
                        <td className="whitespace-nowrap px-4 py-3">{entry.vesselId ? formatEntityLabel(entry.vesselId, 'Vessel') : 'Fleet'}</td>
                        <td className="px-4 py-3">{formatEntityAuditLabel(entry.entityType, entry.entityId)}</td>
                        <td className="px-4 py-3">{summarizeAuditLogDiff(entry)}</td>
                        <td className="px-4 py-3">{entry.reason ?? 'No reason recorded.'}</td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <Badge variant={entry.retentionTier === 'cold' ? 'secondary' : 'default'}>
                            {formatAuditAction(entry.retentionTier)}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-6 text-center text-sm text-neutral-500">No audit events match these filters.</div>
            )}
          </CardContent>
        </Card>
      </section>
    </RootLayout>
  );
}

function CertAuditLogExportPanel({ filters }: { filters: CertAuditLogFilters }) {
  const exportAuditLog = useExportAuditLog();

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-neutral-900">DPA audit export</p>
          {exportAuditLog.data ? (
            <p className="mt-1 text-sm text-success-700">Export ready: {exportAuditLog.data.printId}</p>
          ) : exportAuditLog.isError ? (
            <p className="mt-1 text-sm text-error-700">{getErrorMessage(exportAuditLog.error)}</p>
          ) : (
            <p className="mt-1 text-sm text-neutral-600">Generates a watermarked PDF and CSV from the current filters.</p>
          )}
        </div>
        <Button
          type="button"
          onClick={() => exportAuditLog.mutate({ filters })}
          disabled={exportAuditLog.isPending}
        >
          <FileText className="mr-2 h-4 w-4" aria-hidden="true" />
          {exportAuditLog.isPending ? 'Exporting...' : 'Export filtered PDF and CSV'}
        </Button>
      </CardContent>
    </Card>
  );
}

function CertFleetCadenceHeartbeatCard() {
  const dashboard = useFleetDashboard();

  if (dashboard.isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cadence heartbeat</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (dashboard.isError || !dashboard.data) {
    return (
      <Card className="border-warning-200 bg-warning-50">
        <CardHeader>
          <CardTitle>Cadence heartbeat</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-warning-800">Could not load cadence heartbeat signal.</p>
          <Button type="button" variant="outline" onClick={() => dashboard.refetch()}>
            <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return <CertFleetCadenceHeartbeatCardContent data={dashboard.data} />;
}

function CertFleetCadenceHeartbeatCardContent({ data }: { data: CertFleetDashboardResponse }) {
  const lastHeartbeat = data.cadenceHeartbeat?.lastCadenceHeartbeat ?? null;
  const ageMinutes = getHeartbeatAgeMinutes(lastHeartbeat);
  const stale = ageMinutes === null || ageMinutes > 120;

  return (
    <Card className={stale ? 'border-error-200 bg-error-50' : undefined}>
      <CardHeader>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-center gap-2">
            <Activity className={stale ? 'h-5 w-5 text-error-700' : 'h-5 w-5 text-success-700'} aria-hidden="true" />
            <CardTitle>Cadence heartbeat</CardTitle>
          </div>
          <Badge variant={stale ? 'destructive' : 'success'}>
            {stale ? 'Heartbeat stale' : 'Heartbeat fresh'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className={stale ? 'text-error-800' : 'text-neutral-700'}>
        <p className="text-sm">
          Last heartbeat {lastHeartbeat ? formatDateTime(lastHeartbeat) : 'not recorded'}
        </p>
        <p className="mt-1 text-sm">
          {ageMinutes === null ? 'Office Slack alert active.' : `${formatHeartbeatAge(ageMinutes)} since last cadence run.`}
        </p>
      </CardContent>
    </Card>
  );
}

function CertFleetBouncingEmailCard() {
  const dashboard = useFleetDashboard();

  if (dashboard.isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Bouncing email delivery</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (dashboard.isError || !dashboard.data) {
    return (
      <Card className="border-warning-200 bg-warning-50">
        <CardHeader>
          <CardTitle>Bouncing email delivery</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-warning-800">Could not load email delivery signal.</p>
          <Button type="button" variant="outline" onClick={() => dashboard.refetch()}>
            <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return <CertFleetBouncingEmailCardContent data={dashboard.data} />;
}

function CertFleetBouncingEmailCardContent({ data }: { data: CertFleetDashboardResponse }) {
  const signal = data.bouncingEmailDelivery ?? { bouncingUsersCount: 0, users: [] };
  const users = signal.users.slice(0, 5);
  const noun = signal.bouncingUsersCount === 1 ? 'user' : 'users';

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <CardTitle>Bouncing email delivery</CardTitle>
          <Badge variant={signal.bouncingUsersCount ? 'destructive' : 'success'}>
            {signal.bouncingUsersCount} {noun} with failing email
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {signal.bouncingUsersCount === 0 ? (
          <p className="text-sm text-neutral-600">No vessel-side email recipients are currently bouncing.</p>
        ) : (
          <div className="overflow-hidden rounded-md border border-neutral-200">
            <table className="min-w-full divide-y divide-neutral-200 text-sm">
              <thead className="bg-neutral-50 text-left text-xs uppercase text-neutral-500">
                <tr>
                  <th className="px-3 py-2">User</th>
                  <th className="px-3 py-2">Last bounce</th>
                  <th className="px-3 py-2">Critical fallback</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 bg-white">
                {users.map((user) => (
                  <tr key={user.userId}>
                    <td className="px-3 py-2 font-medium text-neutral-900">{user.userId}</td>
                    <td className="px-3 py-2 text-neutral-700">{formatDateTime(user.lastBouncedAt)}</td>
                    <td className="px-3 py-2 text-neutral-700">{user.criticalFallbackCount} critical fallback{user.criticalFallbackCount === 1 ? '' : 's'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CertFleetHighVolumePrintCard() {
  const dashboard = useFleetDashboard();

  if (dashboard.isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>High-volume print activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (dashboard.isError || !dashboard.data) {
    return (
      <Card className="border-warning-200 bg-warning-50">
        <CardHeader>
          <CardTitle>High-volume print activity</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-warning-800">Could not load print governance signal.</p>
          <Button type="button" variant="outline" onClick={() => dashboard.refetch()}>
            <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return <CertFleetHighVolumePrintCardContent data={dashboard.data} />;
}

function CertFleetHighVolumePrintCardContent({ data }: { data: CertFleetDashboardResponse }) {
  const signal = data.highVolumePrintActivity ?? { thresholdPerHour: 10, windowMinutes: 60, usersAboveThresholdCount: 0, users: [] };
  const users = signal.users.slice(0, 5);
  const noun = signal.usersAboveThresholdCount === 1 ? 'user' : 'users';

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <CardTitle>High-volume print activity</CardTitle>
          <Badge variant={signal.usersAboveThresholdCount ? 'warning' : 'success'}>
            {signal.usersAboveThresholdCount} {noun} above {signal.thresholdPerHour} prints/hour
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {signal.usersAboveThresholdCount === 0 ? (
          <p className="text-sm text-neutral-600">No users exceeded the print soft limit in the last {signal.windowMinutes} minutes.</p>
        ) : (
          <div className="overflow-hidden rounded-md border border-neutral-200">
            <table className="min-w-full divide-y divide-neutral-200 text-sm">
              <thead className="bg-neutral-50 text-left text-xs uppercase text-neutral-500">
                <tr>
                  <th className="px-3 py-2">User</th>
                  <th className="px-3 py-2">Role</th>
                  <th className="px-3 py-2">Volume</th>
                  <th className="px-3 py-2">Last print</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 bg-white">
                {users.map((user) => (
                  <tr key={user.userId}>
                    <td className="px-3 py-2 font-medium text-neutral-900">{user.userId}</td>
                    <td className="px-3 py-2 text-neutral-700">{user.userRole || 'Unknown'}</td>
                    <td className="px-3 py-2 text-neutral-700">{user.printCountLastHour} prints</td>
                    <td className="px-3 py-2 text-neutral-700">{formatDateTime(user.lastPrintAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function CertAuditorAccessPage({ grantId }: { grantId?: string }) {
  const canRead = useCertsPermission(FORM_IDS.CERTS_AUDITOR_ACCESS);
  const canWrite = useCanWriteAuditorAccess();

  if (!canRead) {
    return <CertsPermissionDenied />;
  }

  if (grantId) {
    return <CertAuditorAccessDetailPage grantId={grantId} canWrite={canWrite} />;
  }

  return <CertAuditorAccessListPage canWrite={canWrite} />;
}

function CertAuditorAccessListPage({ canWrite }: { canWrite: boolean }) {
  const grants = useAuditorAccessGrants(true);
  const createGrant = useCreateAuditorAccessGrant();
  const [auditorName, setAuditorName] = useState('');
  const [auditorEmail, setAuditorEmail] = useState('');
  const [vesselIds, setVesselIds] = useState('');
  const [sections, setSections] = useState('');
  const [certIds, setCertIds] = useState('');
  const [expiryAt, setExpiryAt] = useState('');

  const submitGrant = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    createGrant.mutate({
      auditorName,
      auditorEmail,
      scope: {
        vesselIds: splitLinesOrCommas(vesselIds),
        sections: splitLinesOrCommas(sections),
        certIds: splitLinesOrCommas(certIds),
      },
      expiryAt: expiryAt || undefined,
    });
  };

  return (
    <RootLayout>
      <PageHeader title="External auditor access" />
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Active grants</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {grants.isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-2/3" />
              </div>
            ) : grants.isError ? (
              <div className="text-sm text-red-700">{getErrorMessage(grants.error)}</div>
            ) : grants.data?.results.length ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-200 text-sm">
                  <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                    <tr>
                      <th className="px-4 py-3">Auditor</th>
                      <th className="px-4 py-3">Scope</th>
                      <th className="px-4 py-3">Expiry</th>
                      <th className="px-4 py-3">Last access</th>
                      <th className="px-4 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 bg-white">
                    {grants.data.results.map((grant) => (
                      <tr key={grant.id}>
                        <td className="px-4 py-3">
                          <Link className="font-medium text-primary-700 hover:underline" to={ROUTES.CERTS_AUDITOR_ACCESS_DETAIL(grant.id)}>
                            {grant.auditorName}
                          </Link>
                          <div className="text-xs text-neutral-500">{grant.auditorEmail}</div>
                        </td>
                        <td className="px-4 py-3">{formatAuditorGrantScope(grant)}</td>
                        <td className="px-4 py-3">{formatDateTime(grant.expiryAt)}</td>
                        <td className="px-4 py-3">{grant.lastAccessedAt ? formatDateTime(grant.lastAccessedAt) : 'Not used'}</td>
                        <td className="px-4 py-3">
                          <Badge variant={grant.revokedViaExpiryEdit ? 'destructive' : 'secondary'}>
                            {grant.revokedViaExpiryEdit ? 'Expired by edit' : grant.signupTokenUsedAt ? 'Active' : 'Signup pending'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-sm text-neutral-600">No external auditor grants found.</div>
            )}
          </CardContent>
        </Card>

        {canWrite ? (
          <Card>
            <CardHeader>
              <CardTitle>New auditor grant</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="grid gap-4 md:grid-cols-2" onSubmit={submitGrant}>
                <div className="space-y-2">
                  <Label htmlFor="auditorName">Auditor name</Label>
                  <Input id="auditorName" value={auditorName} onChange={(event) => setAuditorName(event.target.value)} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="auditorEmail">Auditor email</Label>
                  <Input id="auditorEmail" type="email" value={auditorEmail} onChange={(event) => setAuditorEmail(event.target.value)} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="auditorVessels">Vessel IDs or IMOs</Label>
                  <Textarea id="auditorVessels" value={vesselIds} onChange={(event) => setVesselIds(event.target.value)} required rows={3} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="auditorSections">Sections</Label>
                  <Textarea id="auditorSections" value={sections} onChange={(event) => setSections(event.target.value)} rows={3} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="auditorCerts">Certificate IDs</Label>
                  <Textarea id="auditorCerts" value={certIds} onChange={(event) => setCertIds(event.target.value)} rows={3} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="auditorExpiry">Expiry</Label>
                  <Input id="auditorExpiry" type="datetime-local" value={expiryAt} onChange={(event) => setExpiryAt(event.target.value)} />
                </div>
                {createGrant.isError ? (
                  <div className="md:col-span-2 text-sm text-red-700">{getErrorMessage(createGrant.error)}</div>
                ) : null}
                {createGrant.data?.signupUrl ? (
                  <div className="md:col-span-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
                    Signup link: {createGrant.data.signupUrl}
                  </div>
                ) : null}
                <div className="md:col-span-2">
                  <Button type="submit" disabled={createGrant.isPending}>
                    <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
                    Create grant
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </RootLayout>
  );
}

function CertAuditorAccessDetailPage({ grantId, canWrite }: { grantId: string; canWrite: boolean }) {
  const grant = useAuditorAccessGrant(grantId);
  const updateExpiry = useUpdateAuditorAccessGrantExpiry(grantId);
  const [expiryAt, setExpiryAt] = useState('');

  const submitExpiry = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (expiryAt) {
      updateExpiry.mutate({ expiryAt });
    }
  };

  return (
    <RootLayout>
      <PageHeader title="Auditor grant detail" />
      <Card>
        <CardContent className="space-y-4 p-6">
          {grant.isLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : grant.isError ? (
            <div className="text-sm text-red-700">{getErrorMessage(grant.error)}</div>
          ) : grant.data ? (
            <>
              <div>
                <h1 className="text-lg font-semibold text-neutral-900">{grant.data.auditorName}</h1>
                <p className="text-sm text-neutral-600">{grant.data.auditorEmail}</p>
              </div>
              <dl className="grid gap-3 text-sm md:grid-cols-2">
                <div><dt className="font-medium text-neutral-500">Scope</dt><dd>{formatAuditorGrantScope(grant.data)}</dd></div>
                <div><dt className="font-medium text-neutral-500">Expiry</dt><dd>{formatDateTime(grant.data.expiryAt)}</dd></div>
                <div><dt className="font-medium text-neutral-500">Granted by</dt><dd>{grant.data.grantedBy}</dd></div>
                <div><dt className="font-medium text-neutral-500">Last access</dt><dd>{grant.data.lastAccessedAt ? formatDateTime(grant.data.lastAccessedAt) : 'Not used'}</dd></div>
              </dl>
              {canWrite ? (
                <form className="flex flex-wrap items-end gap-3" onSubmit={submitExpiry}>
                  <div className="space-y-2">
                    <Label htmlFor="editAuditorExpiry">Edit expiry</Label>
                    <Input id="editAuditorExpiry" type="datetime-local" value={expiryAt} onChange={(event) => setExpiryAt(event.target.value)} required />
                  </div>
                  <Button type="submit" disabled={updateExpiry.isPending}>
                    <Save className="mr-2 h-4 w-4" aria-hidden="true" />
                    Save expiry
                  </Button>
                </form>
              ) : null}
            </>
          ) : null}
        </CardContent>
      </Card>
    </RootLayout>
  );
}

function AuditorPortalPage({ token, view, id }: { token: string; view: 'home' | 'vessel' | 'cert' | 'print'; id?: string }) {
  const signup = useAuditorSignup(view === 'home' ? token : undefined);
  const sessionToken = view === 'home' ? signup.data?.sessionToken : token;

  if (view === 'home' && signup.isError) {
    return <AuditorTerminalPage />;
  }

  if (view === 'home' && signup.isLoading) {
    return (
      <AuditorShell>
        <Skeleton className="h-24 w-full" />
      </AuditorShell>
    );
  }

  if (view === 'vessel') {
    return <AuditorVesselCertsPage sessionToken={sessionToken} imo={id} />;
  }
  if (view === 'cert') {
    return <AuditorCertPage sessionToken={sessionToken} certId={id} />;
  }
  if (view === 'print') {
    return <AuditorPrintPage sessionToken={sessionToken} />;
  }
  return <AuditorVesselListPage sessionToken={sessionToken} />;
}

function AuditorVesselListPage({ sessionToken }: { sessionToken?: string }) {
  const vessels = useAuditorVessels(sessionToken);
  if (vessels.isError) {
    return <AuditorTerminalPage />;
  }
  return (
    <AuditorShell>
      <Card>
        <CardHeader>
          <CardTitle>Auditor vessel scope</CardTitle>
        </CardHeader>
        <CardContent>
          {vessels.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : vessels.data?.results.length ? (
            <div className="grid gap-3 md:grid-cols-2">
              {vessels.data.results.map((vessel) => (
                <Link key={vessel.id} to={ROUTES.CERTS_AUDITOR_VESSEL(sessionToken ?? '', vessel.imo)} className="rounded-md border border-neutral-200 p-4 hover:border-primary-300">
                  <div className="font-semibold text-neutral-900">{vessel.name}</div>
                  <div className="text-sm text-neutral-600">IMO {vessel.imo}</div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-sm text-neutral-600">No vessels available in this audit scope.</div>
          )}
        </CardContent>
      </Card>
    </AuditorShell>
  );
}

function AuditorVesselCertsPage({ sessionToken, imo }: { sessionToken?: string; imo?: string }) {
  const certs = useAuditorVesselCerts(sessionToken, imo);
  if (certs.isError) {
    return <AuditorTerminalPage />;
  }
  return (
    <AuditorShell>
      <Card>
        <CardHeader>
          <CardTitle>Scoped certificates</CardTitle>
        </CardHeader>
        <CardContent>
          {certs.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : certs.data?.results.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-neutral-200 text-sm">
                <tbody className="divide-y divide-neutral-100 bg-white">
                  {certs.data.results.map((cert) => (
                    <tr key={cert.id}>
                      <td className="px-4 py-3">
                        <Link className="font-medium text-primary-700 hover:underline" to={ROUTES.CERTS_AUDITOR_CERT(sessionToken ?? '', cert.id)}>
                          {cert.catalogDisplayName ?? cert.catalogCode}
                        </Link>
                      </td>
                      <td className="px-4 py-3">{cert.certificateNumber ?? '-'}</td>
                      <td className="px-4 py-3">{cert.expiryDate ?? 'Permanent'}</td>
                      <td className="px-4 py-3"><CertStatusBadge status={cert.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-sm text-neutral-600">No certificates available in this vessel scope.</div>
          )}
        </CardContent>
      </Card>
    </AuditorShell>
  );
}

function AuditorCertPage({ sessionToken, certId }: { sessionToken?: string; certId?: string }) {
  const cert = useAuditorCert(sessionToken, certId);
  if (cert.isError) {
    return <AuditorTerminalPage />;
  }
  return (
    <AuditorShell>
      <Card>
        <CardContent className="space-y-4 p-6">
          {cert.isLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : cert.data ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h1 className="text-lg font-semibold text-neutral-900">{cert.data.catalogDisplayName ?? cert.data.catalogCode}</h1>
                  <p className="text-sm text-neutral-600">{cert.data.certificateNumber ?? 'No certificate number'}</p>
                </div>
                <Button asChild variant="outline">
                  <Link to={ROUTES.CERTS_AUDITOR_PRINT(sessionToken ?? '')}>
                    <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
                    Print
                  </Link>
                </Button>
              </div>
              <dl className="grid gap-3 text-sm md:grid-cols-2">
                <div><dt className="font-medium text-neutral-500">Status</dt><dd><CertStatusBadge status={cert.data.status} /></dd></div>
                <div><dt className="font-medium text-neutral-500">Expiry</dt><dd>{cert.data.expiryDate ?? 'Permanent'}</dd></div>
                <div><dt className="font-medium text-neutral-500">Issuing authority</dt><dd>{cert.data.issuingAuthority}</dd></div>
                <div><dt className="font-medium text-neutral-500">Extension note</dt><dd>{cert.data.extensionReason ?? '-'}</dd></div>
                <div><dt className="font-medium text-neutral-500">Rejection note</dt><dd>{cert.data.rejectionReason ?? '-'}</dd></div>
              </dl>
            </>
          ) : null}
        </CardContent>
      </Card>
    </AuditorShell>
  );
}

function AuditorPrintPage({ sessionToken }: { sessionToken?: string }) {
  const print = useGenerateAuditorPrint(sessionToken);

  useEffect(() => {
    if (sessionToken && !print.data && !print.isPending && !print.isError) {
      print.mutate({});
    }
  }, [sessionToken, print]);

  if (print.isError) {
    return <AuditorTerminalPage />;
  }
  return (
    <AuditorShell>
      <Card>
        <CardHeader>
          <CardTitle>Audit copy print</CardTitle>
        </CardHeader>
        <CardContent>
          {print.isPending || !print.data ? (
            <Skeleton className="h-24 w-full" />
          ) : (
            <div className="rounded-md border border-neutral-200 bg-neutral-50 p-4 font-mono text-sm whitespace-pre-line">
              {print.data.watermarkText}
            </div>
          )}
        </CardContent>
      </Card>
    </AuditorShell>
  );
}

function AuditorShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-neutral-50 p-4 md:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-900">VIMS Certificates Audit Portal</h1>
        </div>
        {children}
      </div>
    </main>
  );
}

function AuditorTerminalPage() {
  return (
    <AuditorShell>
      <Card>
        <CardContent className="p-6 text-center">
          <h1 className="text-lg font-semibold text-neutral-900">Access expired — contact the DPA</h1>
        </CardContent>
      </Card>
    </AuditorShell>
  );
}

interface CertPickerOption {
  value: string;
  label: string;
  description?: string | null;
  group?: string | null;
}

const PRINT_ALL_SECTIONS_OPTION = 'all_sections';

function useCertPrintSelectionOptions(filters: CertTrackedItemFilters, enabled: boolean) {
  const trackedItems = useTrackedItems({ ...filters, page: 1, pageSize: 1 }, enabled);

  return {
    certificateItems: trackedItems.data?.results ?? [],
    isCertificatesLoading: trackedItems.isLoading,
  };
}

function buildCertSectionPickerOptions(sections: CertCatalogSection[]): CertPickerOption[] {
  return sections
    .filter((section) => section.sectionId || section.sectionCode)
    .sort((left, right) => left.sortOrder - right.sortOrder || left.displayName.localeCompare(right.displayName))
    .map((section) => ({
      value: String(section.sectionId || section.sectionCode),
      label: section.displayName,
      description: section.activeRowCount
        ? `${section.activeRowCount} catalog row${section.activeRowCount === 1 ? '' : 's'}`
        : null,
    }));
}

function resolveContextVesselId(initialVesselId: string, authVesselId: string | null | undefined): string {
  return String(initialVesselId || authVesselId || '').trim();
}

function formatContextVesselLabel(
  vesselId: string,
  queryImo: string | null,
  authVesselName: string | null | undefined,
  items: CertTrackedItem[]
): string {
  const matchedItem = items.find((item) => item.vesselId === vesselId);
  const name = String(matchedItem?.vesselName ?? authVesselName ?? '').trim();
  const imo = String(matchedItem?.vesselImo ?? queryImo ?? '').trim();
  if (name && imo) return `${name} - IMO ${imo}`;
  return name || (imo ? `IMO ${imo}` : 'Selected vessel');
}

function togglePickerValue(values: string[], optionValue: string, checked: boolean): string[] {
  if (checked) {
    return values.includes(optionValue) ? values : [...values, optionValue];
  }
  return values.filter((value) => value !== optionValue);
}

function includeSelectedFallbackOptions(
  options: CertPickerOption[],
  selectedValues: string[],
  fallback: string
): CertPickerOption[] {
  const knownValues = new Set(options.map((option) => option.value));
  const missingOptions = selectedValues
    .filter((value) => !knownValues.has(value))
    .map((value) => ({ value, label: formatEntityLabel(value, fallback) }));
  return missingOptions.length ? [...missingOptions, ...options] : options;
}

function groupPickerOptions(options: CertPickerOption[]): Array<{ group: string | null; options: CertPickerOption[] }> {
  const grouped = new Map<string, CertPickerOption[]>();
  const ungrouped: CertPickerOption[] = [];

  for (const option of options) {
    const group = String(option.group ?? '').trim();
    if (!group) {
      ungrouped.push(option);
      continue;
    }
    grouped.set(group, [...(grouped.get(group) ?? []), option]);
  }

  return [
    ...Array.from(grouped.entries()).map(([group, groupOptions]) => ({ group, options: groupOptions })),
    ...(ungrouped.length ? [{ group: null, options: ungrouped }] : []),
  ];
}

function formatPickerSummary(
  selectedValues: string[],
  options: CertPickerOption[],
  placeholder: string,
  fallback: string,
  pluralLabel: string
): string {
  if (selectedValues.length === 0) {
    return placeholder;
  }
  if (selectedValues.length === 1) {
    const selected = options.find((option) => option.value === selectedValues[0]);
    return selected?.label ?? formatEntityLabel(selectedValues[0], fallback);
  }
  return `${selectedValues.length} ${pluralLabel} selected`;
}

function CertMultiSelectDropdown({
  id,
  value,
  options,
  onChange,
  placeholder,
  fallbackLabel,
  pluralLabel,
  loading,
  noOptionsText,
}: {
  id: string;
  value: string[];
  options: CertPickerOption[];
  onChange: (value: string[]) => void;
  placeholder: string;
  fallbackLabel: string;
  pluralLabel: string;
  loading: boolean;
  noOptionsText: string;
}) {
  const resolvedOptions = includeSelectedFallbackOptions(options, value, fallbackLabel);
  const summary = loading && resolvedOptions.length === 0
    ? 'Loading'
    : formatPickerSummary(value, resolvedOptions, placeholder, fallbackLabel, pluralLabel);
  const visibleValues = resolvedOptions.map((option) => option.value);
  const selectedVisibleCount = visibleValues.filter((optionValue) => value.includes(optionValue)).length;
  const allVisibleSelected = visibleValues.length > 0 && selectedVisibleCount === visibleValues.length;
  const groupedOptions = groupPickerOptions(resolvedOptions);
  const selectAllVisible = () => onChange(Array.from(new Set([...value, ...visibleValues])));
  const clearVisible = () => onChange(value.filter((selectedValue) => !visibleValues.includes(selectedValue)));

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button id={id} type="button" variant="outline" className="w-full justify-between border-neutral-300 bg-white font-normal text-neutral-900 hover:bg-neutral-50">
          <span className="truncate">{summary}</span>
          <ListFilter className="ml-2 h-4 w-4 shrink-0" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="start"
        className="max-h-80 w-[var(--radix-dropdown-menu-trigger-width)] border border-neutral-200 bg-white p-0 text-neutral-900 shadow-xl ring-1 ring-neutral-900/5"
      >
        {resolvedOptions.length > 0 ? (
          <>
            <div className="sticky top-0 z-10 flex items-center justify-between gap-2 border-b border-neutral-200 bg-white p-2">
              <span className="text-xs font-medium text-neutral-600">{selectedVisibleCount} selected</span>
              <div className="flex items-center gap-2">
                <Button type="button" variant="outline" size="sm" disabled={allVisibleSelected} onClick={selectAllVisible}>
                  Select all
                </Button>
                <Button type="button" variant="ghost" size="sm" disabled={selectedVisibleCount === 0} onClick={clearVisible}>
                  Clear all
                </Button>
              </div>
            </div>
            <div className="py-1">
              {groupedOptions.map((group) => (
                <div key={group.group ?? 'ungrouped'} className="py-1">
                  {group.group ? (
                    <div className="bg-neutral-50 px-3 py-1.5 text-xs font-semibold uppercase text-neutral-500">
                      {group.group}
                    </div>
                  ) : null}
                  {group.options.map((option) => (
                    <DropdownMenuCheckboxItem
                      key={option.value}
                      checked={value.includes(option.value)}
                      onCheckedChange={(checked) => onChange(togglePickerValue(value, option.value, Boolean(checked)))}
                      onSelect={(event) => event.preventDefault()}
                      className="items-start bg-white text-neutral-900 focus:bg-neutral-100 focus:text-neutral-900 data-[state=checked]:bg-primary-50"
                    >
                      <span className="flex min-w-0 flex-col gap-0.5">
                        <span className="truncate font-medium">{option.label}</span>
                        {option.description ? <span className="truncate text-xs text-neutral-500">{option.description}</span> : null}
                      </span>
                    </DropdownMenuCheckboxItem>
                  ))}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="px-2 py-3 text-sm text-neutral-500">{loading ? 'Loading' : noOptionsText}</div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function CertPrintBuilderPage() {
  const canPrint = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT, PROCESS_IDS.CERTS_PRINT);
  const auth = useAuth();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialVesselId = queryParams.get('vesselId') ?? '';
  const queryImo = queryParams.get('imo');
  const contextVesselId = resolveContextVesselId(initialVesselId, auth.vesselId);
  const vesselIds = contextVesselId ? [contextVesselId] : [];
  const [certificateListSelection, setCertificateListSelection] = useState(PRINT_ALL_SECTIONS_OPTION);
  const sections = useCatalogSections();
  const mutation = useGeneratePrintArtifact();
  const printSelectionFilters: CertTrackedItemFilters = contextVesselId
    ? { vesselId: contextVesselId }
    : {};
  const printSelectionEnabled = canPrint && Boolean(contextVesselId);
  const printSelection = useCertPrintSelectionOptions(printSelectionFilters, printSelectionEnabled);
  const sectionOptions = buildCertSectionPickerOptions(sections.data ?? []);
  const vesselContextLabel = contextVesselId
    ? formatContextVesselLabel(contextVesselId, queryImo, auth.user?.vessel_name, printSelection.certificateItems)
    : '';
  const shareBundleHref = contextVesselId
    ? `${ROUTES.CERTS_SHARE_BUNDLE}?vesselId=${encodeURIComponent(contextVesselId)}${queryImo ? `&imo=${encodeURIComponent(queryImo)}` : ''}`
    : ROUTES.CERTS_SHARE_BUNDLE;

  if (!canPrint) {
    return <CertsPermissionDenied />;
  }

  const submitPrint = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (vesselIds.length === 0) {
      return;
    }
    const selectedSection = certificateListSelection === PRINT_ALL_SECTIONS_OPTION ? '' : certificateListSelection;
    mutation.mutate({
      scope: selectedSection ? 'per_vessel_partial' : 'per_vessel_full',
      vesselIds,
      sections: selectedSection ? [selectedSection] : [],
      customCertIds: [],
      filters: {},
      watermarkApplied: 'NONE',
      watermarkRecipient: '',
      recipientEmail: '',
    });
  };

  return (
    <RootLayout>
      <PageHeader title="Print certs status" />
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to={ROUTES.CERTS_PRINT_HISTORY}>
              <History className="mr-2 h-4 w-4" aria-hidden="true" />
              Print history
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={shareBundleHref}>
              <Share2 className="mr-2 h-4 w-4" aria-hidden="true" />
              Share bundle
            </Link>
          </Button>
        </div>
        <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Print certs status</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submitPrint}>
                {vesselContextLabel ? (
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-700">
                    Vessel: <span className="font-medium text-neutral-900">{vesselContextLabel}</span>
                  </div>
                ) : (
                  <div className="rounded-md border border-warning-200 bg-warning-50 px-3 py-2 text-sm text-warning-900">
                    Open a vessel first to print that vessel.
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="printCertificateList">Certificate sections</Label>
                  <Select value={certificateListSelection} onValueChange={setCertificateListSelection} disabled={!contextVesselId || sections.isLoading}>
                    <SelectTrigger id="printCertificateList" className="bg-white">
                      <SelectValue placeholder={sections.isLoading ? 'Loading sections' : 'Choose section'} />
                    </SelectTrigger>
                    <SelectContent className="max-h-80 bg-white">
                      <SelectItem value={PRINT_ALL_SECTIONS_OPTION}>All sections</SelectItem>
                      {sectionOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {mutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(mutation.error)}</p> : null}
                <Button type="submit" disabled={mutation.isPending || vesselIds.length === 0}>
                  <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
                  {mutation.isPending ? 'Generating' : 'Generate PDF and Excel'}
                </Button>
              </form>
            </CardContent>
          </Card>
          <CertPrintArtifactResult artifact={mutation.data} />
        </div>
      </div>
    </RootLayout>
  );
}

function CertPrintArtifactResult({ artifact }: { artifact?: CertPrintArtifact }) {
  if (!artifact) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Artifact</CardTitle>
        </CardHeader>
        <CardContent className="rounded-md border border-dashed border-neutral-300 p-6 text-sm text-neutral-600">
          No print artifact generated in this session.
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader>
        <CardTitle>{artifact.printId}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <CertPrintArtifactSummary artifact={artifact} />
        <CertPrintArtifactDownloads artifact={artifact} />
        <CertPrintEmailStatus artifact={artifact} />
      </CardContent>
    </Card>
  );
}

function CertPrintArtifactDownloads({ artifact, compact = false }: { artifact: CertPrintArtifact; compact?: boolean }) {
  const [downloadingKind, setDownloadingKind] = useState<CertPrintDownloadKind | null>(null);
  const [downloadError, setDownloadError] = useState('');
  const secondaryLabel = artifact.scope === 'audit_log_export' ? 'Download CSV' : 'Download Excel';
  const downloadOptions: Array<{ kind: CertPrintDownloadKind; label: string; available: boolean }> = [
    { kind: 'pdf', label: 'Download PDF', available: Boolean(artifact.pdfBlobId || artifact.downloadUrls?.pdf) },
    { kind: 'excel', label: secondaryLabel, available: Boolean(artifact.excelBlobId || artifact.downloadUrls?.excel) },
    { kind: 'zip', label: 'Download ZIP', available: Boolean(artifact.bundleZipBlobId || artifact.downloadUrls?.zip) },
  ];
  const availableOptions = downloadOptions.filter((option) => option.available);

  const handleDownload = async (kind: CertPrintDownloadKind) => {
    if (downloadingKind) {
      return;
    }
    setDownloadError('');
    setDownloadingKind(kind);
    try {
      saveCertDownload(await certsApi.downloadPrintArtifact(artifact.printId, kind));
    } catch (error) {
      setDownloadError(getErrorMessage(error));
    } finally {
      setDownloadingKind(null);
    }
  };

  if (availableOptions.length === 0) {
    return <p className="text-xs text-neutral-500">No files available.</p>;
  }

  return (
    <div className={compact ? 'space-y-1' : 'space-y-2'}>
      <div className="flex flex-wrap gap-2">
        {availableOptions.map((option) => (
          <Button
            key={option.kind}
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void handleDownload(option.kind)}
            disabled={Boolean(downloadingKind)}
          >
            <Download className="mr-2 h-4 w-4" aria-hidden="true" />
            {downloadingKind === option.kind ? 'Downloading' : option.label}
          </Button>
        ))}
      </div>
      {downloadError ? <p className="text-xs text-error-700">{downloadError}</p> : null}
    </div>
  );
}

function CertPrintEmailStatus({ artifact }: { artifact: CertPrintArtifact }) {
  if (!artifact.recipientEmail) {
    return null;
  }
  if (artifact.emailDeliveryStatus === 'sent') {
    return <p className="rounded-md border border-success-200 bg-success-50 px-3 py-2 text-sm text-success-800">{artifact.emailDeliveryMessage || `Email sent to ${artifact.recipientEmail}.`}</p>;
  }
  if (artifact.emailDeliveryStatus === 'failed') {
    return <p className="rounded-md border border-error-200 bg-error-50 px-3 py-2 text-sm text-error-800">{artifact.emailDeliveryMessage || 'Email could not be sent.'}</p>;
  }
  return null;
}

function saveCertDownload({ blob, fileName }: { blob: Blob; fileName: string }) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
}

function CertPrintHistoryPage() {
  const canRead = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT);
  const artifacts = usePrintArtifacts(canRead ? { pageSize: 100 } : { pageSize: 1 });

  if (!canRead) {
    return <CertsPermissionDenied />;
  }

  if (artifacts.isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Print History" />
        <div className="space-y-3 p-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-80 w-full" />
        </div>
      </RootLayout>
    );
  }

  if (artifacts.isError || !artifacts.data) {
    return (
      <RootLayout>
        <PageHeader title="Print History" />
        <div className="p-4">
          <CertCatalogError message={`Could not load print history. ${getErrorMessage(artifacts.error)}`} onRetry={() => artifacts.refetch()} />
        </div>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <PageHeader title="Print History" />
      <div className="space-y-4 p-4">
            <Button asChild variant="outline">
              <Link to={ROUTES.CERTS_PRINT}>
                <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
                Print certs status
              </Link>
            </Button>
        <Card>
          <CardContent className="p-0">
            {artifacts.data.results.length === 0 ? (
              <div className="p-6 text-center text-sm text-neutral-600">No print artifacts have been generated.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-200 text-sm">
                  <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                    <tr>
                      <th className="px-3 py-3">Print ID</th>
                      <th className="px-3 py-3">Scope</th>
                      <th className="px-3 py-3">Generated</th>
                      <th className="px-3 py-3">Watermark</th>
                      <th className="px-3 py-3">Status</th>
                      <th className="px-3 py-3">Artifacts</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100">
                    {artifacts.data.results.map((artifact) => (
                      <tr key={artifact.printId} className="hover:bg-neutral-50">
                        <td className="px-3 py-3 font-medium text-neutral-900">{artifact.printId}</td>
                        <td className="px-3 py-3 text-neutral-700">{formatStatus(artifact.scope)}</td>
                        <td className="px-3 py-3 text-neutral-700">{formatDateTime(artifact.timestampUtc)}</td>
                        <td className="px-3 py-3 text-neutral-700">{formatStatus(artifact.watermarkApplied)}</td>
                        <td className="min-w-64 px-3 py-3">
                          <div className="space-y-2">
                            <Badge variant={artifact.generationStatus === 'failed' ? 'destructive' : 'success'}>
                              {formatStatus(artifact.generationStatus)}
                            </Badge>
                            {artifact.generationStatus === 'failed' ? (
                              <div className="space-y-2 rounded-md border border-error-200 bg-error-50 p-3 text-sm text-error-800">
                                <p>{artifact.failureMessage}</p>
                                <Button asChild variant="outline">
                                  <Link to={ROUTES.CERTS_PRINT}>
                                    <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
                                    Retry manually
                                  </Link>
                                </Button>
                              </div>
                            ) : null}
                          </div>
                        </td>
                        <td className="px-3 py-3">
                          <CertPrintArtifactDownloads artifact={artifact} compact />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </RootLayout>
  );
}

function CertShareBundlePage() {
  const canShareBundle = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT, PROCESS_IDS.CERTS_EXPORT_BUNDLE);
  const auth = useAuth();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const initialVesselId = queryParams.get('vesselId') ?? '';
  const contextVesselId = resolveContextVesselId(initialVesselId, auth.vesselId);
  const vesselIds = contextVesselId ? [contextVesselId] : [];
  const [selectedSections, setSelectedSections] = useState<string[]>([]);
  const [watermarkRecipient, setWatermarkRecipient] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const sections = useCatalogSections();
  const mutation = useGenerateShareBundle();
  const bundleSelection = useCertPrintSelectionOptions(
    contextVesselId ? { vesselId: contextVesselId } : {},
    canShareBundle && Boolean(contextVesselId)
  );
  const sectionOptions = buildCertSectionPickerOptions(sections.data ?? []);
  const vesselContextLabel = contextVesselId
    ? formatContextVesselLabel(contextVesselId, queryParams.get('imo'), auth.user?.vessel_name, bundleSelection.certificateItems)
    : '';

  if (!canShareBundle) {
    return <CertsPermissionDenied />;
  }

  const submitBundle = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (vesselIds.length === 0) {
      return;
    }
    mutation.mutate({
      vesselIds,
      sections: selectedSections,
      customCertIds: [],
      watermarkRecipient,
      recipientEmail,
    });
  };

  return (
    <RootLayout>
      <PageHeader title="Share Bundle" />
      <div className="space-y-4 p-4">
        <Button asChild variant="outline">
          <Link to={ROUTES.CERTS_PRINT_HISTORY}>
            <History className="mr-2 h-4 w-4" aria-hidden="true" />
            Print history
          </Link>
        </Button>
        <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <Card>
            <CardHeader>
              <CardTitle>Master share bundle</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submitBundle}>
                {vesselContextLabel ? (
                  <div className="rounded-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-neutral-700">
                    Vessel: <span className="font-medium text-neutral-900">{vesselContextLabel}</span>
                  </div>
                ) : (
                  <div className="rounded-md border border-warning-200 bg-warning-50 px-3 py-2 text-sm text-warning-900">
                    Open a vessel first to create a share bundle.
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="bundleSections">Certificate sections</Label>
                  <CertMultiSelectDropdown
                    id="bundleSections"
                    value={selectedSections}
                    options={sectionOptions}
                    onChange={setSelectedSections}
                    placeholder="Choose sections"
                    fallbackLabel="Section"
                    pluralLabel="sections"
                    loading={sections.isLoading}
                    noOptionsText="No sections available."
                  />
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="bundleRecipient">Recipient name</Label>
                    <Input id="bundleRecipient" value={watermarkRecipient} onChange={(event) => setWatermarkRecipient(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bundleEmail">Recipient email</Label>
                    <Input id="bundleEmail" type="email" inputMode="email" autoComplete="email" value={recipientEmail} onChange={(event) => setRecipientEmail(event.target.value)} />
                  </div>
                </div>
                {mutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(mutation.error)}</p> : null}
                <Button type="submit" disabled={mutation.isPending || vesselIds.length === 0 || selectedSections.length === 0}>
                  <Share2 className="mr-2 h-4 w-4" aria-hidden="true" />
                  {mutation.isPending ? 'Generating' : 'Generate ZIP bundle'}
                </Button>
              </form>
            </CardContent>
          </Card>
          <CertPrintArtifactResult artifact={mutation.data} />
        </div>
      </div>
    </RootLayout>
  );
}

function CertPrintArtifactSummary({ artifact }: { artifact: CertPrintArtifact }) {
  return (
    <dl className="grid gap-3 sm:grid-cols-2">
      <div>
        <dt className="text-neutral-500">Generated</dt>
        <dd className="font-medium text-neutral-900">{formatDateTime(artifact.timestampUtc)}</dd>
      </div>
      <div>
        <dt className="text-neutral-500">Pages</dt>
        <dd className="font-medium text-neutral-900">{artifact.pageCount ?? 'n/a'}</dd>
      </div>
    </dl>
  );
}

function CertVesselDashboardLoading({ imo }: { imo: string }) {
  return (
    <RootLayout>
      <PageHeader title={`Vessel Certificates ${imo}`} />
      <div className="space-y-4 p-4">
        <Skeleton className="h-32 w-full" />
        <div className="grid gap-3 md:grid-cols-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
        <Skeleton className="h-80 w-full" />
      </div>
    </RootLayout>
  );
}

function CertVesselDashboardError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <RootLayout>
      <PageHeader title="Vessel Certificates" />
      <div className="p-4">
        <CertCatalogError message={message} onRetry={onRetry} />
      </div>
    </RootLayout>
  );
}

function CertVesselDashboardPage({ imo }: { imo: string }) {
  const canReadTrackedItems = useCertsPermission(FORM_IDS.CERTS_TRACKED_ITEMS);
  const canReadReconciliation = useCertsPermission(FORM_IDS.CERTS_RECONCILIATION);
  const canPrint = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT, PROCESS_IDS.CERTS_PRINT);
  const canShareBundle = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT, PROCESS_IDS.CERTS_EXPORT_BUNDLE);
  const auth = useAuth();
  const role = String(auth.role ?? auth.user?.role_name ?? auth.user?.safety_role_name ?? '').trim().toUpperCase();
  const canShareThisVessel = canShareBundle && ['MASTER', 'VESSEL_MASTER', 'DPA', 'FM', 'FLEET MANAGER'].some((marker) => role.includes(marker));
  const dashboard = useVesselDashboard(canReadTrackedItems ? imo : undefined);
  const showOfficeMessages = auth.isVessel && canReadReconciliation;
  const officeMessages = useMasterReconciliationMessages({ pageSize: 10 }, showOfficeMessages);
  const [statusFilter, setStatusFilter] = useState('all');
  const [sectionFilter, setSectionFilter] = useState('all');
  const [classFilter, setClassFilter] = useState('all');
  const [pdfFilter, setPdfFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  if (!canReadTrackedItems) {
    return <CertsPermissionDenied />;
  }

  if (dashboard.isLoading) {
    return <CertVesselDashboardLoading imo={imo} />;
  }

  if (dashboard.isError || !dashboard.data) {
    return (
      <CertVesselDashboardError
        message={`Could not load vessel certificates. ${getErrorMessage(dashboard.error)}`}
        onRetry={() => dashboard.refetch()}
      />
    );
  }

  const data = dashboard.data;
  const filteredSections = filterDashboardSections(data.sections, {
    status: statusFilter,
    section: sectionFilter,
    classTracked: classFilter,
    pdf: pdfFilter,
    search: searchQuery,
  });
  const hasItems = data.summary.totalTrackedItems > 0;
  const hasFilteredItems = filteredSections.some((section) => section.items.length > 0);
  const filtersActive = [statusFilter, sectionFilter, classFilter, pdfFilter].some((value) => value !== 'all') || searchQuery.trim().length > 0;

  return (
    <RootLayout>
      <PageHeader title="Vessel Certificates" />
      <div className="space-y-4 p-4">
        <CertVesselHeader
          data={data}
          imo={imo}
          canPrint={canPrint}
          canShareBundle={canShareThisVessel}
        />
        <CertVesselSpecialBanners data={data} imo={imo} />
        <CertVesselOfficeMessagesCard enabled={showOfficeMessages} messages={officeMessages.data?.results ?? []} isLoading={officeMessages.isLoading} />
        <CertVesselKpis data={data} />
        <CertVesselFilters
          sections={data.sections}
          statusFilter={statusFilter}
          sectionFilter={sectionFilter}
          classFilter={classFilter}
          pdfFilter={pdfFilter}
          searchQuery={searchQuery}
          setStatusFilter={setStatusFilter}
          setSectionFilter={setSectionFilter}
          setClassFilter={setClassFilter}
          setPdfFilter={setPdfFilter}
          setSearchQuery={setSearchQuery}
        />
        {!hasItems ? (
          <Card>
            <CardContent className="space-y-4 p-6 text-center">
              <FileText className="mx-auto h-8 w-8 text-neutral-500" aria-hidden="true" />
              <div className="space-y-1">
                <h2 className="text-lg font-semibold text-neutral-900">Vessel not yet onboarded</h2>
                <p className="text-sm text-neutral-600">Start the onboarding wizard to create this vessel&apos;s certificate register.</p>
              </div>
              <Button asChild>
                <Link to={`/certs/onboarding/${imo}`}>Start wizard</Link>
              </Button>
            </CardContent>
          </Card>
        ) : !hasFilteredItems ? (
          <Card>
            <CardContent className="p-6 text-center text-sm text-neutral-600">
              No results match these filters.
              <Button
                variant="link"
                className="ml-2 h-auto p-0"
                onClick={() => {
                  setStatusFilter('all');
                  setSectionFilter('all');
                  setClassFilter('all');
                  setPdfFilter('all');
                  setSearchQuery('');
                }}
              >
                Reset filters
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {filteredSections.map((section) => (
              <CertVesselSectionAccordion key={section.sectionId} section={section} imo={imo} defaultOpen={section.actionItemCount > 0 || filtersActive} />
            ))}
          </div>
        )}
      </div>
    </RootLayout>
  );
}

function CertVesselProfilePage({ imo }: { imo: string }) {
  const canReadTrackedItems = useCertsPermission(FORM_IDS.CERTS_TRACKED_ITEMS);
  const canWriteLifecycle = useCertsPermission(FORM_IDS.CERTS_TRACKED_ITEMS, PROCESS_IDS.CERTS_CATALOG_EDIT);
  const auth = useAuth();
  const role = String(auth.role ?? auth.user?.role_name ?? auth.user?.safety_role_name ?? '').trim().toUpperCase();
  const isDpaLifecycleRole = ['DPA', 'SEQ MANAGER', 'ADMIN', 'SUPER ADMIN', 'SYSTEM ADMIN'].some((marker) => role.includes(marker));
  const canRunLifecycleActions = canWriteLifecycle && isDpaLifecycleRole;
  const profile = useVesselProfile(canReadTrackedItems ? imo : undefined);
  const flagMutation = useRecordFlagChange(imo);
  const classMutation = useRecordClassChange(imo);
  const saleMutation = useInitiateSaleHandover(imo);
  const decommissionMutation = useDecommissionVessel(imo);
  const [flagForm, setFlagForm] = useState({ newFlagState: '', effectiveDate: todayInputValue(), reason: '' });
  const [classForm, setClassForm] = useState({ newClassSociety: '', effectiveDate: todayInputValue(), reason: '' });
  const [saleForm, setSaleForm] = useState({ handoverDate: todayInputValue(), watermarkRecipient: '', reason: '' });
  const [decommissionForm, setDecommissionForm] = useState({ decommissionDate: todayInputValue(), reason: '' });

  if (!canReadTrackedItems) {
    return <CertsPermissionDenied />;
  }

  if (profile.isLoading) {
    return <CertVesselDashboardLoading imo={imo} />;
  }

  if (profile.isError || !profile.data) {
    return (
      <CertVesselDashboardError
        message={`Could not load vessel profile. ${getErrorMessage(profile.error)}`}
        onRetry={() => profile.refetch()}
      />
    );
  }

  const data = profile.data;
  const vessel = data.vessel;
  const config = data.config;

  const submitFlag = (event: FormEvent) => {
    event.preventDefault();
    flagMutation.mutate(flagForm);
  };
  const submitClass = (event: FormEvent) => {
    event.preventDefault();
    classMutation.mutate(classForm);
  };
  const submitSale = (event: FormEvent) => {
    event.preventDefault();
    saleMutation.mutate({ ...saleForm, customCertIds: [] });
  };
  const submitDecommission = (event: FormEvent) => {
    event.preventDefault();
    decommissionMutation.mutate(decommissionForm);
  };

  return (
    <RootLayout>
      <PageHeader title="Vessel Profile" />
      <div className="space-y-4 p-4">
        <Card>
          <CardContent className="space-y-4 p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-neutral-900">{vessel.name ?? vessel.code ?? 'Vessel'}</h1>
                <p className="text-sm text-neutral-600">
                  IMO {vessel.imo ?? 'Not set'} - {vessel.flag ?? 'Flag not set'} - {vessel.classSociety ?? 'Class not set'}
                </p>
              </div>
              <Button asChild variant="outline">
                <Link to={ROUTES.CERTS_VESSEL_DASHBOARD(imo)}>Back to certificates</Link>
              </Button>
            </div>
            <div className="grid gap-3 text-sm md:grid-cols-4">
              <LifecycleField label="Lifecycle" value={formatStatus(config?.lifecycleStatus)} />
              <LifecycleField label="Ship type" value={formatShipType(config?.shipType)} />
              <LifecycleField label="Pending disposal" value={formatDate(config?.pendingDisposalStartedAt)} />
              <LifecycleField label="Sale bundle" value={config?.saleHandoverBundleBlobId ?? 'Not generated'} />
            </div>
          </CardContent>
        </Card>

        <CertVesselProfileBanners data={data} />

        {canRunLifecycleActions ? (
          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Flag Change</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={submitFlag}>
                  <LifecycleTextField id="flag-new-state" label="New flag state" value={flagForm.newFlagState} onChange={(value) => setFlagForm((current) => ({ ...current, newFlagState: value }))} />
                  <LifecycleDateField id="flag-effective-date" label="Effective date" value={flagForm.effectiveDate} onChange={(value) => setFlagForm((current) => ({ ...current, effectiveDate: value }))} />
                  <LifecycleReasonField id="flag-reason" value={flagForm.reason} onChange={(value) => setFlagForm((current) => ({ ...current, reason: value }))} />
                  <Button type="submit" disabled={flagMutation.isPending}>Record flag change</Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Class Change</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={submitClass}>
                  <LifecycleTextField id="class-new-society" label="New class society" value={classForm.newClassSociety} onChange={(value) => setClassForm((current) => ({ ...current, newClassSociety: value }))} />
                  <LifecycleDateField id="class-effective-date" label="Effective date" value={classForm.effectiveDate} onChange={(value) => setClassForm((current) => ({ ...current, effectiveDate: value }))} />
                  <LifecycleReasonField id="class-reason" value={classForm.reason} onChange={(value) => setClassForm((current) => ({ ...current, reason: value }))} />
                  <Button type="submit" disabled={classMutation.isPending}>Record class change</Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Sale Handover</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={submitSale}>
                  <LifecycleDateField id="sale-handover-date" label="Handover date" value={saleForm.handoverDate} onChange={(value) => setSaleForm((current) => ({ ...current, handoverDate: value }))} />
                  <LifecycleTextField id="sale-watermark-recipient" label="Watermark recipient" value={saleForm.watermarkRecipient} onChange={(value) => setSaleForm((current) => ({ ...current, watermarkRecipient: value }))} />
                  <LifecycleReasonField id="sale-reason" value={saleForm.reason} onChange={(value) => setSaleForm((current) => ({ ...current, reason: value }))} />
                  <Button type="submit" variant="outline" disabled={saleMutation.isPending}>Initiate sale handover</Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Decommission</CardTitle>
              </CardHeader>
              <CardContent>
                <form className="space-y-3" onSubmit={submitDecommission}>
                  <LifecycleDateField id="decommission-date" label="Decommission date" value={decommissionForm.decommissionDate} onChange={(value) => setDecommissionForm((current) => ({ ...current, decommissionDate: value }))} />
                  <LifecycleReasonField id="decommission-reason" value={decommissionForm.reason} onChange={(value) => setDecommissionForm((current) => ({ ...current, reason: value }))} />
                  <Button type="submit" variant="destructive" disabled={decommissionMutation.isPending}>Start decommission</Button>
                </form>
              </CardContent>
            </Card>
          </div>
        ) : (
          <Card>
            <CardContent className="p-4 text-sm text-neutral-600">Lifecycle actions are restricted to DPA users.</CardContent>
          </Card>
        )}
      </div>
    </RootLayout>
  );
}

function CertVesselProfileBanners({ data }: { data: CertVesselLifecycleResponse }) {
  const config = data.config;
  const banners: Array<{ key: string; variant: 'warning' | 'destructive' | 'info'; text: string }> = [];
  if (config?.lifecycleStatus === 'pending_disposal') {
    banners.push({ key: 'pending-disposal', variant: 'warning', text: `Pending disposal since ${formatDate(config.pendingDisposalStartedAt)}.` });
  }
  if (config?.flagChangePending) {
    const newFlag = config.flagChangeEvent?.newFlagState ? ` New flag: ${String(config.flagChangeEvent.newFlagState)}.` : '';
    banners.push({ key: 'flag-change', variant: 'destructive', text: `Pending statutory re-upload after flag change.${newFlag}` });
  }
  if (config?.classChangePending) {
    banners.push({ key: 'class-change', variant: 'warning', text: 'Class change pending; new class snapshot must be uploaded within 30 days.' });
  }
  if (banners.length === 0) {
    return null;
  }
  return (
    <div className="space-y-2">
      {banners.map((banner) => (
        <div key={banner.key} className={`rounded-md border p-3 text-sm ${bannerClassName(banner.variant)}`}>{banner.text}</div>
      ))}
    </div>
  );
}

function LifecycleField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <p className="text-neutral-500">{label}</p>
      <p className="font-medium text-neutral-900">{value || 'Not set'}</p>
    </div>
  );
}

function LifecycleTextField({ id, label, value, onChange }: { id: string; label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} value={value} onChange={(event) => onChange(event.target.value)} required />
    </div>
  );
}

function LifecycleDateField({ id, label, value, onChange }: { id: string; label: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input id={id} type="date" value={value} onChange={(event) => onChange(event.target.value)} required />
    </div>
  );
}

function LifecycleReasonField({ id, value, onChange }: { id: string; value: string; onChange: (value: string) => void }) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>Reason</Label>
      <Textarea id={id} value={value} onChange={(event) => onChange(event.target.value)} minLength={20} required />
    </div>
  );
}

function CertVesselHeader({
  data,
  imo,
  canPrint,
  canShareBundle,
}: {
  data: CertVesselDashboardResponse;
  imo: string;
  canPrint: boolean;
  canShareBundle: boolean;
}) {
  const vessel = data.vessel;
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 space-y-3">
            <div>
              <h1 className="text-2xl font-semibold text-neutral-900">{vessel.name ?? vessel.code ?? 'Vessel'}</h1>
              <p className="text-sm text-neutral-600">
                IMO {vessel.imo ?? 'Not set'} - {vessel.flag ?? 'Flag not set'} - {vessel.classSociety ?? 'Class not set'} - {formatShipType(vessel.shipType)}
              </p>
            </div>
            <div className="grid gap-x-8 gap-y-3 text-sm sm:grid-cols-3">
              <div className="min-w-0">
                <p className="text-neutral-500">Current Master</p>
                <p className="break-words font-medium text-neutral-900">{vessel.currentMaster ?? 'Not assigned'}</p>
              </div>
              <div className="min-w-0">
                <p className="text-neutral-500">Last class snapshot</p>
                <p className="font-medium text-neutral-900 lg:whitespace-nowrap">{formatSnapshotAge(data.lastClassSnapshot)}</p>
              </div>
              <div className="min-w-0">
                <p className="text-neutral-500">Mandatory coverage</p>
                <p className="font-medium text-neutral-900 lg:whitespace-nowrap">{data.mandatoryCoverage.percent}%</p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 lg:flex-nowrap">
            <Button asChild variant="outline" className="whitespace-nowrap">
              <Link to={ROUTES.CERTS_VESSEL_PROFILE(imo)}>
                <Activity className="mr-2 h-4 w-4" aria-hidden="true" />
                Vessel profile
              </Link>
            </Button>
            {data.lastClassSnapshot?.id ? (
              <ClassSnapshotPdfButton snapshotId={data.lastClassSnapshot.id} className="whitespace-nowrap">
                Open class status PDF
              </ClassSnapshotPdfButton>
            ) : null}
            {canPrint ? (
              <Button asChild variant="outline" className="whitespace-nowrap">
                <Link to={`${ROUTES.CERTS_PRINT}?vesselId=${encodeURIComponent(vessel.id)}&imo=${encodeURIComponent(imo)}`}>
                  <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
                  Print certs status
                </Link>
              </Button>
            ) : null}
            {canShareBundle ? (
              <Button asChild variant="outline" className="whitespace-nowrap">
                <Link to={`${ROUTES.CERTS_SHARE_BUNDLE}?vesselId=${encodeURIComponent(vessel.id)}&imo=${encodeURIComponent(imo)}`}>
                  <Share2 className="mr-2 h-4 w-4" aria-hidden="true" />
                  Share bundle
                </Link>
              </Button>
            ) : null}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

type CertButtonVariant = 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
type CertButtonSize = 'default' | 'sm' | 'lg' | 'icon';

function ClassSnapshotPdfButton({
  snapshotId,
  children,
  className,
  size,
  variant = 'outline',
  showIcon = true,
}: {
  snapshotId: string;
  children: ReactNode;
  className?: string;
  size?: CertButtonSize;
  variant?: CertButtonVariant;
  showIcon?: boolean;
}) {
  const [opening, setOpening] = useState(false);

  const handleOpenPdf = async () => {
    if (opening) {
      return;
    }

    const pdfWindow = window.open('', '_blank');
    if (!pdfWindow) {
      window.alert('Allow pop-ups for this site, then try again.');
      return;
    }
    pdfWindow.opener = null;
    setOpening(true);

    try {
      const blob = await certsApi.getClassSnapshotPdfBlob(snapshotId);
      const objectUrl = URL.createObjectURL(blob);
      pdfWindow.location.href = objectUrl;
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch {
      pdfWindow.close();
      window.alert('Could not open this class status PDF. Try again.');
    } finally {
      setOpening(false);
    }
  };

  return (
    <Button type="button" size={size} variant={variant} className={className} onClick={handleOpenPdf} disabled={opening}>
      {showIcon ? <FileText className="mr-2 h-4 w-4" aria-hidden="true" /> : null}
      {opening ? 'Opening...' : children}
    </Button>
  );
}

function CertVesselSpecialBanners({ data, imo }: { data: CertVesselDashboardResponse; imo: string }) {
  const banners: Array<{ key: string; variant: 'warning' | 'destructive' | 'info'; text: string; cta?: ReactNode }> = [];
  if (data.vessel.lifecycleStatus === 'pending_disposal') {
    banners.push({ key: 'pending-disposal', variant: 'warning', text: `Pending disposal since ${formatDate(data.vessel.pendingDisposalStartedAt)}.` });
  }
  if (data.vessel.lifecycleStatus === 'onboarding_in_progress') {
    banners.push({
      key: 'onboarding',
      variant: 'info',
      text: 'Onboarding is in progress.',
      cta: <Link className="font-semibold underline" to={`/certs/onboarding/${imo}`}>Resume wizard</Link>,
    });
  }
  if (data.mandatoryCoverage.percent < 100 && !data.mandatoryCoverage.overrideActive) {
    const missingCount = data.mandatoryCoverage.missing?.length ?? Math.max(data.mandatoryCoverage.mandatoryCount - data.mandatoryCoverage.coveredCount, 0);
    banners.push({
      key: 'coverage',
      variant: 'destructive',
      text: `Mandatory coverage is ${data.mandatoryCoverage.percent}%; ${missingCount} mandatory cert${missingCount === 1 ? '' : 's'} still missing.`,
    });
  }
  if (data.vessel.flagChangePending) {
    banners.push({ key: 'flag-change', variant: 'destructive', text: 'Pending statutory re-upload after flag change.' });
  }

  if (banners.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {banners.map((banner) => (
        <div key={banner.key} className={`rounded-md border p-3 text-sm ${bannerClassName(banner.variant)}`}>
          <span>{banner.text}</span>
          {banner.cta ? <span className="ml-2">{banner.cta}</span> : null}
        </div>
      ))}
    </div>
  );
}

function CertVesselKpis({ data }: { data: CertVesselDashboardResponse }) {
  const kpis = [
    { label: 'Certificates', value: data.summary.totalTrackedItems },
    { label: 'Need attention', value: data.summary.actionItemCount },
    { label: 'Certificates missing', value: data.summary.pdfMissingCount },
    { label: 'Class certificates', value: data.summary.classTrackedCount },
  ];
  return (
    <div className="certs-kpi-grid grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map((kpi) => (
        <Card key={kpi.label}>
          <CardContent className="p-4">
            <p className="text-sm text-neutral-500">{kpi.label}</p>
            <p className="mt-1 text-2xl font-semibold text-neutral-900">{kpi.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function CertVesselFilters({
  sections,
  statusFilter,
  sectionFilter,
  classFilter,
  pdfFilter,
  searchQuery,
  setStatusFilter,
  setSectionFilter,
  setClassFilter,
  setPdfFilter,
  setSearchQuery,
}: {
  sections: CertVesselDashboardSection[];
  statusFilter: string;
  sectionFilter: string;
  classFilter: string;
  pdfFilter: string;
  searchQuery: string;
  setStatusFilter: (value: string) => void;
  setSectionFilter: (value: string) => void;
  setClassFilter: (value: string) => void;
  setPdfFilter: (value: string) => void;
  setSearchQuery: (value: string) => void;
}) {
  return (
    <Card>
      <CardContent className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-5">
        <div className="space-y-2">
          <Label htmlFor="vesselCertificateSearch">Search</Label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" aria-hidden="true" />
            <Input
              id="vesselCertificateSearch"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search certificate, number, issuer"
              className="pl-9"
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="vesselStatusFilter">Status</Label>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger id="vesselStatusFilter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="current">Current</SelectItem>
              <SelectItem value="window_open">Renewal due</SelectItem>
              <SelectItem value="window_closing">Renewal urgent</SelectItem>
              <SelectItem value="expired">Expired</SelectItem>
              <SelectItem value="pending_first_upload">Pending upload</SelectItem>
              <SelectItem value="pending_master_approval">Pending master approval</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="vesselSectionFilter">Section</Label>
          <Select value={sectionFilter} onValueChange={setSectionFilter}>
            <SelectTrigger id="vesselSectionFilter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All sections</SelectItem>
              {sections.map((section) => (
                <SelectItem key={section.sectionId} value={String(section.sectionId)}>{section.displayName}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="vesselClassFilter">Certificate type</Label>
          <Select value={classFilter} onValueChange={setClassFilter}>
            <SelectTrigger id="vesselClassFilter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All certificates</SelectItem>
              <SelectItem value="class">Class certificates</SelectItem>
              <SelectItem value="non_class">Other certificates</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="vesselPdfFilter">Certificate file</Label>
          <Select value={pdfFilter} onValueChange={setPdfFilter}>
            <SelectTrigger id="vesselPdfFilter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All files</SelectItem>
              <SelectItem value="missing">File missing</SelectItem>
              <SelectItem value="attached">File attached</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}

function CertVesselSectionAccordion({ section, imo, defaultOpen }: { section: CertVesselDashboardSection; imo: string; defaultOpen: boolean }) {
  return (
    <details className="rounded-md border border-neutral-200 bg-white" open={defaultOpen}>
      <summary className="flex cursor-pointer list-none flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-neutral-900">{section.displayName}</h2>
          <p className="text-sm text-neutral-500">{section.activeTrackedItemCount} active certificates</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(section.statusBreakdown).map(([status, count]) => (
            <Badge key={status} variant={statusBadgeVariant(status)}>{formatStatus(status)} {count}</Badge>
          ))}
        </div>
      </summary>
      {section.items.length === 0 ? (
        <div className="border-t border-neutral-100 p-4 text-sm text-neutral-600">No certs in this section yet.</div>
      ) : (
        <div className="border-t border-neutral-100 p-3">
          <div className="hidden overflow-x-auto lg:block">
            <table className="min-w-full divide-y divide-neutral-200 text-sm">
              <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                <tr>
                  <th className="px-3 py-3">Certificate</th>
                  <th className="px-3 py-3">Cert number</th>
                  <th className="px-3 py-3">Issued by</th>
                  <th className="px-3 py-3">Issue date</th>
                  <th className="px-3 py-3">Expiry date</th>
                  <th className="px-3 py-3">Status</th>
                  <th className="px-3 py-3">Valid for</th>
                  <th className="px-3 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {section.items.map((item) => <CertVesselTableRow key={item.id} item={item} imo={imo} />)}
              </tbody>
            </table>
          </div>
          <div className="space-y-3 lg:hidden">
            {section.items.map((item) => <CertVesselItemCard key={item.id} item={item} imo={imo} />)}
          </div>
        </div>
      )}
    </details>
  );
}

function CertVesselTableRow({ item, imo }: { item: CertTrackedItem; imo: string }) {
  return (
    <tr className="hover:bg-neutral-50">
      <td className="min-w-72 px-3 py-3">
        <Link className="font-medium text-neutral-900 hover:text-primary-600" to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(imo, item.id)}>
          {item.displayName ?? item.catalogDisplayName ?? item.catalogCode}
        </Link>
        <div className="mt-1 flex flex-wrap gap-1">
          {item.shortName ? <Badge variant="secondary">{item.shortName}</Badge> : null}
          {item.approvalState && item.approvalState !== 'approved' ? <Badge variant="warning">{formatStatus(item.approvalState)}</Badge> : null}
          {item.pdfMissing ? <Badge variant="destructive">Certificates missing</Badge> : null}
        </div>
      </td>
      <td className="px-3 py-3 text-neutral-700">{item.certificateNumber ?? 'Not set'}</td>
      <td className="px-3 py-3 text-neutral-700">{item.issuingAuthority ?? 'Not set'}</td>
      <td className="px-3 py-3 text-neutral-700">{formatDate(item.issueDate)}</td>
      <td className="px-3 py-3 text-neutral-700">{formatExpiry(item)}</td>
      <td className="px-3 py-3"><CertStatusBadge status={item.status} /></td>
      <td className="px-3 py-3 text-neutral-700">{formatCertificateValidity(item)}</td>
      <td className="px-3 py-3">
        <CertVesselItemActions item={item} imo={imo} />
      </td>
    </tr>
  );
}

function CertVesselItemCard({ item, imo }: { item: CertTrackedItem; imo: string }) {
  return (
    <Card>
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Link className="font-semibold text-neutral-900 hover:text-primary-600" to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(imo, item.id)}>
              {item.displayName ?? item.catalogDisplayName ?? item.catalogCode}
            </Link>
            <p className="text-sm text-neutral-600">{item.certificateNumber ?? 'Cert number not set'}</p>
          </div>
          <CertStatusBadge status={item.status} />
        </div>
        <div className="grid gap-2 text-sm sm:grid-cols-2">
          <div><span className="text-neutral-500">Issued by: </span>{item.issuingAuthority ?? 'Not set'}</div>
          <div><span className="text-neutral-500">Expiry: </span>{formatExpiry(item)}</div>
          <div><span className="text-neutral-500">Valid for: </span>{formatCertificateValidity(item)}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          {item.pdfMissing ? <Badge variant="destructive">Certificates missing</Badge> : null}
          {item.approvalState && item.approvalState !== 'approved' ? <Badge variant="warning">{formatStatus(item.approvalState)}</Badge> : null}
          <CertVesselItemActions item={item} imo={imo} />
        </div>
      </CardContent>
    </Card>
  );
}

function CertVesselItemActions({ item, imo }: { item: CertTrackedItem; imo: string }) {
  const [viewLoading, setViewLoading] = useState(false);
  const hasPdf = Boolean(item.pdfAttachmentId);
  const detailLabel = actionLabel(item);
  const viewLabel = hasPdf ? 'View certificate PDF' : 'No PDF uploaded';

  const handleOpenPdf = async () => {
    const blobId = item.pdfAttachmentId;
    if (!blobId || viewLoading) {
      return;
    }

    const pdfWindow = window.open('', '_blank');
    if (!pdfWindow) {
      window.alert('Allow pop-ups for this site, then try again.');
      return;
    }
    pdfWindow.opener = null;
    setViewLoading(true);

    try {
      const blob = await certsApi.getTrackedItemPdfBlob(item.id, blobId);
      const objectUrl = URL.createObjectURL(blob);
      pdfWindow.location.href = objectUrl;
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch {
      pdfWindow.close();
      window.alert('Could not open this certificate PDF. Try again.');
    } finally {
      setViewLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-1.5">
      <Button
        asChild
        size="icon"
        variant="outline"
        className="h-8 w-8"
        aria-label={detailLabel}
        title={detailLabel}
      >
        <Link to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(imo, item.id)}>
          <UploadCloud className="h-4 w-4" aria-hidden="true" />
        </Link>
      </Button>
      <Button
        type="button"
        size="icon"
        variant="outline"
        className="h-8 w-8"
        onClick={handleOpenPdf}
        disabled={!hasPdf || viewLoading}
        aria-label={viewLabel}
        title={viewLabel}
      >
        <Eye className="h-4 w-4" aria-hidden="true" />
      </Button>
    </div>
  );
}

function CertReconciliationLoading() {
  return (
    <RootLayout>
      <PageHeader title="Class Reconciliation" />
      <div className="space-y-4 p-4">
        <Skeleton className="h-28 w-full" />
        <div className="grid gap-4 lg:grid-cols-[1.3fr_0.7fr]">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    </RootLayout>
  );
}

function CertReconciliationDashboardPage() {
  const canRead = useCertsPermission(FORM_IDS.CERTS_RECONCILIATION);
  const canUpload = useCertsPermission(FORM_IDS.CERTS_RECONCILIATION, PROCESS_IDS.CERTS_CREATE);
  const auth = useAuth();
  const canOpenParserOps = PARSER_OPS_DEV_ENABLED && isParserOpsRole(normalizeAuthRole(auth));
  const [filterVesselId, setFilterVesselId] = useState('all');
  const [vesselId, setVesselId] = useState('');
  const [classSociety, setClassSociety] = useState('NK');
  const [reportDateFromPdf, setReportDateFromPdf] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState('');
  const selectedFilterVesselId = filterVesselId === 'all' ? null : filterVesselId;
  const runs = useReconciliationRuns(canRead ? { vesselId: selectedFilterVesselId } : {});
  const snapshots = useClassSnapshots(canRead ? { vesselId: selectedFilterVesselId } : { vesselId: 'permission-denied' });
  const vesselDashboard = useFleetDashboard(canRead);
  const uploadMutation = useUploadClassSnapshot();

  if (!canRead) {
    return <CertsPermissionDenied />;
  }

  if (runs.isLoading || snapshots.isLoading) {
    return <CertReconciliationLoading />;
  }

  const combinedError = runs.error ?? snapshots.error;
  if (runs.isError || snapshots.isError || !runs.data || !snapshots.data) {
    return (
      <RootLayout>
        <PageHeader title="Class Reconciliation" />
        <div className="p-4">
          <CertCatalogError
            message={`Could not load class reconciliation. ${getErrorMessage(combinedError)}`}
            onRetry={() => {
              runs.refetch();
              snapshots.refetch();
            }}
          />
        </div>
      </RootLayout>
    );
  }

  const hasRuns = runs.data.count > 0;
  const uploadVessels = [...(vesselDashboard.data?.onboardedVessels ?? [])].sort((left, right) =>
    formatClassSnapshotVesselOption(left).localeCompare(formatClassSnapshotVesselOption(right))
  );

  const submitUpload = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setUploadError('');
    if (!uploadFile) {
      setUploadError('Select a class status PDF.');
      return;
    }
    if (!vesselId.trim()) {
      setUploadError('Select a vessel.');
      return;
    }
    uploadMutation.mutate({
      vesselId: vesselId.trim(),
      classSociety,
      printedOnDate: reportDateFromPdf || null,
      file: uploadFile,
    });
  };

  return (
    <RootLayout>
      <PageHeader title="Class Reconciliation" />
      <div className="space-y-4 p-4">
        {canOpenParserOps ? (
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild variant="outline">
              <Link to={ROUTES.CERTS_PARSER_OPS}>
                <History className="mr-2 h-4 w-4" aria-hidden="true" />
                Parser ops
              </Link>
            </Button>
          </div>
        ) : null}

        <Card>
          <CardContent className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium text-neutral-900">Vessel filter</p>
              <p className="text-xs text-neutral-500">Show class reports and recent uploads for one vessel.</p>
            </div>
            <Select
              value={filterVesselId}
              onValueChange={setFilterVesselId}
              disabled={vesselDashboard.isLoading || uploadVessels.length === 0}
            >
              <SelectTrigger className="w-full sm:w-80">
                <SelectValue placeholder={vesselDashboard.isLoading ? 'Loading vessels...' : 'All vessels'} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All vessels</SelectItem>
                {uploadVessels.map((vessel) => (
                  <SelectItem key={vessel.id} value={vessel.id}>
                    {formatClassSnapshotVesselOption(vessel)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
          <Card>
            <CardHeader>
              <CardTitle>Reconciliation runs</CardTitle>
            </CardHeader>
            <CardContent>
              {!hasRuns ? (
                <div className="rounded-md border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-600">
                  No class snapshots have been reconciled yet.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-neutral-200 text-sm">
                    <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                      <tr>
                        <th className="px-3 py-3">Vessel</th>
                        <th className="px-3 py-3">Class</th>
                        <th className="px-3 py-3">Run</th>
                        <th className="px-3 py-3">Findings</th>
                        <th className="px-3 py-3">Printed On</th>
                        <th className="px-3 py-3">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-100">
                      {runs.data.results.map((run) => (
                        <tr key={run.id} className="hover:bg-neutral-50">
                          <td className="px-3 py-3">
                            <p className="font-medium text-neutral-900">{run.vesselName ?? formatEntityLabel(run.vesselId, 'Vessel not set')}</p>
                            <p className="text-xs text-neutral-500">IMO {run.imo ?? 'Not set'}</p>
                          </td>
                          <td className="px-3 py-3 text-neutral-700">{run.classSociety ?? 'Not set'}</td>
                          <td className="px-3 py-3">
                            <Badge variant={statusBadgeVariant(run.parseStatus ?? '')}>{formatStatus(run.parseStatus)}</Badge>
                            <p className="mt-1 text-xs text-neutral-500">{formatDateTime(run.ranAt)}</p>
                          </td>
                          <td className="px-3 py-3 text-neutral-700">{formatReconciliationFindingSummary(run)}</td>
                          <td className="px-3 py-3 text-neutral-700">{formatDate(run.printedOnDate)}</td>
                          <td className="px-3 py-3">
                            <Button asChild size="sm" variant="outline">
                              <Link to={ROUTES.CERTS_RECONCILIATION_RUN(run.id)}>Review</Link>
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="space-y-4">
            {canUpload ? (
              <Card>
                <CardHeader>
                  <CardTitle>Upload class snapshot</CardTitle>
                </CardHeader>
                <CardContent>
                  <form className="space-y-3" onSubmit={submitUpload}>
                    <div className="space-y-2">
                      <Label htmlFor="classSnapshotVesselId">Vessel</Label>
                      <Select
                        value={vesselId}
                        onValueChange={(nextVesselId) => {
                          setVesselId(nextVesselId);
                          const selectedVessel = uploadVessels.find((vessel) => vessel.id === nextVesselId);
                          const supportedClassSociety = normalizeSupportedClassSociety(selectedVessel?.classSociety);
                          if (supportedClassSociety) {
                            setClassSociety(supportedClassSociety);
                          }
                        }}
                        disabled={vesselDashboard.isLoading || uploadVessels.length === 0}
                      >
                        <SelectTrigger id="classSnapshotVesselId">
                          <SelectValue placeholder={vesselDashboard.isLoading ? 'Loading vessels...' : 'Select vessel'} />
                        </SelectTrigger>
                        <SelectContent>
                          {uploadVessels.map((vessel) => (
                            <SelectItem key={vessel.id} value={vessel.id}>
                              {formatClassSnapshotVesselOption(vessel)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <p className="text-xs text-neutral-500">Select the vessel name. The system will use the correct vessel ID automatically.</p>
                      {vesselDashboard.isError ? (
                        <p className="text-xs text-error-700">Could not load vessels. {getErrorMessage(vesselDashboard.error)}</p>
                      ) : null}
                      {!vesselDashboard.isLoading && !vesselDashboard.isError && uploadVessels.length === 0 ? (
                        <p className="text-xs text-neutral-500">No onboarded vessels are available for class snapshot upload.</p>
                      ) : null}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="classSnapshotSociety">Class</Label>
                      <Select value={classSociety} onValueChange={setClassSociety}>
                        <SelectTrigger id="classSnapshotSociety"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="NK">NK</SelectItem>
                          <SelectItem value="KR">KR</SelectItem>
                          <SelectItem value="BV">BV</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="classSnapshotReportDate">Report date from PDF</Label>
                      <Input
                        id="classSnapshotReportDate"
                        type="date"
                        value={reportDateFromPdf}
                        onChange={(event) => setReportDateFromPdf(event.target.value)}
                      />
                      <p className="text-xs text-neutral-500">
                        Leave blank unless the system cannot read the date. If prompted, enter the Printed on or Generated on date shown in the PDF.
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="classSnapshotPdf">Class Status PDF</Label>
                      <Input
                        id="classSnapshotPdf"
                        type="file"
                        accept="application/pdf,.pdf"
                        onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
                      />
                      <p className="text-xs text-neutral-500">
                        Upload the latest official Class Status or Vessel Status PDF downloaded from the class society portal. The report date must come from the PDF, never from the upload date.
                      </p>
                    </div>
                    {uploadError ? <p className="text-sm text-error-700">{uploadError}</p> : null}
                    {uploadMutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(uploadMutation.error)}</p> : null}
                    {uploadMutation.isSuccess ? (
                      <p className={uploadMutation.data.parseStatus === 'failed' ? 'text-sm text-error-700' : 'text-sm text-success-700'}>
                        {formatClassSnapshotUploadResult(uploadMutation.data)}
                      </p>
                    ) : null}
                    <Button type="submit" disabled={uploadMutation.isPending || vesselDashboard.isLoading || uploadVessels.length === 0}>
                      <UploadCloud className="mr-2 h-4 w-4" aria-hidden="true" />
                      Upload snapshot
                    </Button>
                  </form>
                </CardContent>
              </Card>
            ) : null}

            <Card>
              <CardHeader>
                <CardTitle>Recent snapshots</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {snapshots.data.results.length === 0 ? (
                  <div className="rounded-md border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-600">
                    No class status PDFs uploaded.
                  </div>
                ) : (
                  snapshots.data.results.slice(0, 5).map((snapshot) => (
                    <CertClassSnapshotRow key={snapshot.id} snapshot={snapshot} canReparse={canUpload} />
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </RootLayout>
  );
}

function CertClassSnapshotRow({ snapshot, canReparse }: { snapshot: CertClassSnapshot; canReparse: boolean }) {
  const reparseMutation = useReparseClassSnapshot(snapshot.id);
  return (
    <div className="flex flex-col gap-3 rounded-md border border-neutral-200 p-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="font-medium text-neutral-900">{snapshot.filename ?? 'Class snapshot'}</p>
        <p className="text-sm text-neutral-600">
          {snapshot.vesselName ?? formatEntityLabel(snapshot.vesselId, 'Vessel not set')} - {snapshot.classSociety ?? 'Class not set'} - {formatDate(snapshot.uploadedAt)}
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge variant={statusBadgeVariant(snapshot.parseStatus ?? '')}>{formatStatus(snapshot.parseStatus)}</Badge>
          {snapshot.reconciliationRunId ? <Badge variant="info">Run ready</Badge> : null}
        </div>
      </div>
      {canReparse ? (
        <Button type="button" size="sm" variant="outline" onClick={() => reparseMutation.mutate()} disabled={reparseMutation.isPending}>
          <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
          Reparse
        </Button>
      ) : null}
    </div>
  );
}

function CertParserOpsPage() {
  const canRead = useCertsPermission(FORM_IDS.CERTS_RECONCILIATION);
  const auth = useAuth();
  const canOpenParserOps = PARSER_OPS_DEV_ENABLED && canRead && isParserOpsRole(normalizeAuthRole(auth));
  const snapshots = useClassSnapshots(canOpenParserOps ? { pageSize: 100 } : { vesselId: 'permission-denied', pageSize: 1 });
  const runs = useReconciliationRuns(canOpenParserOps ? { pageSize: 100 } : { vesselId: 'permission-denied', pageSize: 1 });

  if (!canOpenParserOps) {
    return <CertsPermissionDenied />;
  }

  if (snapshots.isLoading || runs.isLoading) {
    return <CertReconciliationLoading />;
  }

  const combinedError = snapshots.error ?? runs.error;
  if (snapshots.isError || runs.isError || !snapshots.data || !runs.data) {
    return (
      <RootLayout>
        <PageHeader title="Parser Ops" />
        <div className="p-4">
          <CertCatalogError
            message={`Could not load parser ops. ${getErrorMessage(combinedError)}`}
            onRetry={() => {
              snapshots.refetch();
              runs.refetch();
            }}
          />
        </div>
      </RootLayout>
    );
  }

  const snapshotRows = snapshots.data.results;
  const runRows = runs.data.results;
  const anomalyRuns = runRows.filter((run) => run.anomalyBreaches.length > 0);
  const timeoutCount = snapshotRows.filter((snapshot) => snapshot.parserTimeout).length;
  const retryCount = snapshotRows.reduce((sum, snapshot) => sum + Number(snapshot.retryCount ?? 0), 0);
  const failedCount = snapshotRows.filter((snapshot) => ['failed', 'partial'].includes(snapshot.parseStatus ?? '')).length;
  const durationValues = snapshotRows
    .map(getSnapshotParseDurationSeconds)
    .filter((value): value is number => typeof value === 'number');
  const longestDuration = durationValues.length > 0 ? Math.max(...durationValues) : null;

  return (
    <RootLayout>
      <PageHeader title="Parser Ops" />
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to={ROUTES.CERTS_RECONCILIATION}>
              <CornerDownRight className="mr-2 h-4 w-4" aria-hidden="true" />
              Back to reconciliation
            </Link>
          </Button>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <CertParserOpsMetric label="Snapshots sampled" value={snapshotRows.length} />
          <CertParserOpsMetric label="Failed or partial" value={failedCount} variant={failedCount > 0 ? 'warning' : 'success'} />
          <CertParserOpsMetric label="Timeouts / retries" value={`${timeoutCount} / ${retryCount}`} variant={timeoutCount > 0 ? 'destructive' : 'secondary'} />
          <CertParserOpsMetric label="Longest parse" value={formatDurationSeconds(longestDuration)} variant={longestDuration && longestDuration > 180 ? 'destructive' : 'secondary'} />
        </div>

        {anomalyRuns.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>OBS-CERT-04 anomaly runs</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {anomalyRuns.map((run) => (
                <div key={run.id} className="rounded-md border border-warning-200 bg-warning-50 p-3 text-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold text-neutral-900">{run.vesselName ?? formatEntityLabel(run.vesselId, 'Vessel not set')}</p>
                      <p className="text-neutral-600">
                        {run.classSociety ?? 'Class not set'} - {formatDate(run.printedOnDate)} - parser {run.parserVersion ?? 'not stamped'}
                      </p>
                    </div>
                    <Button asChild size="sm" variant="outline">
                      <Link to={ROUTES.CERTS_RECONCILIATION_RUN(run.id)}>Review run</Link>
                    </Button>
                  </div>
                  <ul className="mt-3 space-y-1 text-warning-900">
                    {run.anomalyBreaches.map((breach, index) => (
                      <li key={`${run.id}-${breach.type ?? 'breach'}-${index}`}>{formatAnomalyBreach(breach)}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-6 text-center text-sm text-neutral-600">
              No parser anomalies in the current sample.
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Recent parser snapshots</CardTitle>
          </CardHeader>
          <CardContent>
            {snapshotRows.length === 0 ? (
              <div className="rounded-md border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-600">
                No class status PDFs uploaded.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-neutral-200 text-sm">
                  <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                    <tr>
                      <th className="px-3 py-3">Snapshot</th>
                      <th className="px-3 py-3">Parser</th>
                      <th className="px-3 py-3">Duration</th>
                      <th className="px-3 py-3">Retry</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100">
                    {snapshotRows.map((snapshot) => (
                      <tr key={snapshot.id} className="hover:bg-neutral-50">
                        <td className="px-3 py-3">
                          <p className="font-medium text-neutral-900">{snapshot.filename ?? 'Class snapshot'}</p>
                          <p className="text-xs text-neutral-500">{snapshot.vesselName ?? formatEntityLabel(snapshot.vesselId, 'Vessel not set')}</p>
                        </td>
                        <td className="px-3 py-3">
                          <Badge variant={statusBadgeVariant(snapshot.parseStatus ?? '')}>{formatStatus(snapshot.parseStatus)}</Badge>
                          <p className="mt-1 text-xs text-neutral-500">{snapshot.parserVersion ?? 'not stamped'}</p>
                        </td>
                        <td className="px-3 py-3 text-neutral-700">{formatDurationSeconds(getSnapshotParseDurationSeconds(snapshot))}</td>
                        <td className="px-3 py-3">
                          <div className="flex flex-wrap gap-2">
                            <Badge variant={snapshot.parserTimeout ? 'destructive' : 'secondary'}>
                              {snapshot.parserTimeout ? 'Timeout' : 'No timeout'}
                            </Badge>
                            <Badge variant={(snapshot.retryCount ?? 0) > 0 ? 'warning' : 'secondary'}>
                              {snapshot.retryCount ?? 0} retries
                            </Badge>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </RootLayout>
  );
}

function CertParserOpsMetric({
  label,
  value,
  variant = 'secondary',
}: {
  label: string;
  value: ReactNode;
  variant?: 'success' | 'warning' | 'destructive' | 'secondary';
}) {
  return (
    <Card>
      <CardContent className="space-y-2 p-4">
        <p className="text-sm text-neutral-500">{label}</p>
        <div className="flex items-center gap-2">
          <p className="text-2xl font-semibold text-neutral-900">{value}</p>
          <Badge variant={variant}>{variant}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}

function CertReconciliationRunPage({ runId }: { runId: string }) {
  const canRead = useCertsPermission(FORM_IDS.CERTS_RECONCILIATION);
  const canReview = useCertsPermission(FORM_IDS.CERTS_RECONCILIATION, PROCESS_IDS.CERTS_SUBMIT);
  const canEditMapping = useCertsPermission(FORM_IDS.CERTS_RECONCILIATION, PROCESS_IDS.CERTS_CATALOG_EDIT);
  const auth = useAuth();
  const role = String(auth.role ?? auth.user?.role_name ?? auth.user?.safety_role_name ?? '').trim().toUpperCase();
  const isDpa = role.includes('DPA') || role.includes('ADMIN');
  const run = useReconciliationRun(canRead ? runId : undefined);
  const [activeBucket, setActiveBucket] = useState('mismatch');
  const [selectedFlagId, setSelectedFlagId] = useState<string | null>(null);

  useEffect(() => {
    if (!run.data) return;
    const visibleBucketTabs = getVisibleReconciliationBucketTabs(run.data);
    const bucketHasRows = run.data.flags.some((flag) => flag.bucket === activeBucket);
    const activeBucketIsVisible = visibleBucketTabs.some((tab) => tab.bucket === activeBucket);
    if (bucketHasRows && activeBucketIsVisible) return;
    const firstBucketWithRows = visibleBucketTabs.find((tab) =>
      run.data?.flags.some((flag) => flag.bucket === tab.bucket)
    );
    if (firstBucketWithRows) {
      setActiveBucket(firstBucketWithRows.bucket);
    } else if (!activeBucketIsVisible && visibleBucketTabs[0]) {
      setActiveBucket(visibleBucketTabs[0].bucket);
    }
  }, [activeBucket, run.data]);

  useEffect(() => {
    if (!run.data) return;
    const bucketFlags = run.data.flags.filter((flag) => flag.bucket === activeBucket);
    if (bucketFlags.some((flag) => flag.id === selectedFlagId)) return;
    setSelectedFlagId(bucketFlags[0]?.id ?? null);
  }, [activeBucket, run.data, selectedFlagId]);

  if (!canRead) {
    return <CertsPermissionDenied />;
  }

  if (run.isLoading) {
    return <CertReconciliationLoading />;
  }

  if (run.isError || !run.data) {
    return (
      <RootLayout>
        <PageHeader title="Class Reconciliation" />
        <div className="p-4">
          <CertCatalogError message={`Could not load reconciliation run. ${getErrorMessage(run.error)}`} onRetry={() => run.refetch()} />
        </div>
      </RootLayout>
    );
  }

  const bucketFlags = run.data.flags.filter((flag) => flag.bucket === activeBucket);
  const selectedFlag = bucketFlags.find((flag) => flag.id === selectedFlagId) ?? bucketFlags[0] ?? null;
  const visibleBucketTabs = getVisibleReconciliationBucketTabs(run.data);
  const selectedIsConditionOfClass = selectedFlag?.bucket === 'conditions_of_class';

  return (
    <RootLayout>
      <PageHeader title="Class Reconciliation" />
      <div className="space-y-4 p-4">
        <CertReconciliationRunHeader run={run.data} />
        <CertReconciliationAnomalyBanner breaches={run.data.anomalyBreaches} />

        <Card>
          <CardContent className="space-y-4 p-4">
            <div
              role="tablist"
              aria-label="Review groups"
              className="grid gap-2 md:grid-cols-2 xl:grid-cols-4"
            >
              {visibleBucketTabs.map((tab) => {
                const count = getReconciliationBucketCount(run.data, tab);
                const selected = activeBucket === tab.bucket;
                return (
                  <button
                    key={tab.bucket}
                    type="button"
                    role="tab"
                    aria-selected={selected}
                    className={`flex min-h-16 items-center justify-between gap-3 rounded-md border px-3 py-2 text-left text-sm font-medium transition ${
                      selected
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-50'
                    }`}
                    onClick={() => setActiveBucket(tab.bucket)}
                  >
                    <span>{tab.label}</span>
                    <Badge variant={count > 0 ? (tab.bucket === 'match' ? 'success' : 'warning') : 'secondary'}>
                      {count}
                    </Badge>
                  </button>
                );
              })}
            </div>

            {run.data.flags.length === 0 ? (
              <div className="rounded-md border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-600">
                No items need review for this check.
              </div>
            ) : bucketFlags.length === 0 ? (
              <div className="rounded-md border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-600">
                No items in this group.
              </div>
            ) : (
              <div className={`grid gap-4 ${selectedIsConditionOfClass ? 'xl:grid-cols-[0.9fr_1.4fr]' : 'xl:grid-cols-[0.9fr_1.05fr_1.05fr]'}`}>
                <CertReconciliationFlagList
                  flags={bucketFlags}
                  selectedFlagId={selectedFlag?.id ?? null}
                  onSelect={setSelectedFlagId}
                />
                {!selectedIsConditionOfClass ? <CertReconciliationCatalogPanel run={run.data} flag={selectedFlag} /> : null}
                <CertReconciliationClassPanel flag={selectedFlag} />
              </div>
            )}
          </CardContent>
        </Card>

        {selectedFlag ? (
          <CertReconciliationActionPanel
            flag={selectedFlag}
            run={run.data}
            canReview={canReview}
            canAddMapping={canEditMapping && isDpa}
          />
        ) : null}
      </div>
    </RootLayout>
  );
}

function CertReconciliationRunHeader({ run }: { run: CertReconciliationRunDetail }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 p-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div>
            <h1 className="text-xl font-semibold text-neutral-900">{run.vesselName ?? formatEntityLabel(run.vesselId, 'Vessel')}</h1>
            <p className="text-sm text-neutral-600">
              IMO {run.imo ?? 'not set'} - {run.classSociety ?? 'Class not set'} - report date {formatDate(run.printedOnDate)}
            </p>
          </div>
          <p className="text-sm text-neutral-600">
            Checked {formatDateTime(run.ranAt)}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="success">{run.matchesCount ?? 0} matched</Badge>
          <Badge variant={getReconciliationExceptionCount(run) > 0 ? 'warning' : 'secondary'}>
            {getReconciliationExceptionCount(run)} findings
          </Badge>
          {run.snapshotId ? (
            <ClassSnapshotPdfButton snapshotId={run.snapshotId}>
              Open class report PDF
            </ClassSnapshotPdfButton>
          ) : (
            <Button type="button" variant="outline" disabled>
              <FileText className="mr-2 h-4 w-4" aria-hidden="true" />
              Open class report PDF
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function CertReconciliationAnomalyBanner({ breaches }: { breaches: CertReconciliationAnomalyBreach[] }) {
  if (!breaches.length) return null;
  return (
    <div role="status" className="rounded-md border border-warning-200 bg-warning-50 p-3 text-sm text-warning-900">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 flex-none" aria-hidden="true" />
        <div className="space-y-2">
          <p className="font-semibold">Many items need attention</p>
          <ul className="space-y-1">
            {breaches.map((breach, index) => (
              <li key={`${breach.type ?? 'breach'}-${index}`} className="flex flex-wrap items-center gap-2">
                <Badge variant={breach.severity === 'critical' ? 'destructive' : 'warning'}>
                  {breach.severity ?? 'warning'}
                </Badge>
                <span>{formatReviewAlert(breach)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function CertReconciliationFlagList({
  flags,
  selectedFlagId,
  onSelect,
}: {
  flags: CertReconciliationFlag[];
  selectedFlagId: string | null;
  onSelect: (flagId: string) => void;
}) {
  return (
    <aside className="space-y-2" aria-label="Items needing review">
      {flags.map((flag) => {
        const selected = flag.id === selectedFlagId;
        const resolved = Boolean(flag.resolvedAt);
        return (
          <button
            key={flag.id}
            type="button"
            className={`w-full rounded-md border p-3 text-left transition ${
              selected ? 'border-primary-500 bg-primary-50' : 'border-neutral-200 bg-white hover:bg-neutral-50'
            }`}
            onClick={() => onSelect(flag.id)}
          >
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={flag.bucket === 'match' ? 'success' : 'warning'}>{formatReconciliationBucketLabel(flag.bucket)}</Badge>
              {resolved ? <Badge variant="success">Done</Badge> : <Badge variant="secondary">Needs review</Badge>}
            </div>
            <p className="mt-2 text-sm font-semibold text-neutral-900">{formatClassReportItemTitle(flag)}</p>
            <p className="text-xs text-neutral-500">
              {flag.trackedItemId ? 'Linked to a VIMS certificate' : 'Not linked to a VIMS certificate'}
            </p>
          </button>
        );
      })}
    </aside>
  );
}

function CertReconciliationCatalogPanel({
  run,
  flag,
}: {
  run: CertReconciliationRunDetail;
  flag: CertReconciliationFlag | null;
}) {
  if (!flag) return null;
  const hasTrackedLink = Boolean(flag.trackedItemId && run.imo);
  return (
    <section className="rounded-md border border-neutral-200 bg-white p-4" aria-label="VIMS certificate record">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-neutral-900">VIMS certificate record</h2>
          <p className="text-sm text-neutral-600">{flag.catalogDisplayName ?? 'No matching VIMS certificate yet'}</p>
        </div>
        {hasTrackedLink ? (
          <Button asChild size="sm" variant="outline">
            <Link to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(String(run.imo), String(flag.trackedItemId))}>
              Open VIMS certificate
            </Link>
          </Button>
        ) : null}
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <CertReconciliationDefinition
          label="Certificate type"
          value={flag.catalogId ? formatEntityLabel(flag.catalogId, flag.catalogDisplayName ? 'Certificate type linked' : 'Certificate type linked') : 'Not linked yet'}
        />
        <CertReconciliationDefinition
          label="Vessel certificate"
          value={flag.trackedItemId ? formatEntityLabel(flag.trackedItemId, 'Linked') : 'Not linked yet'}
        />
        <CertReconciliationDefinition label="Review status" value={flag.resolutionAction ? formatStatus(flag.resolutionAction) : 'Needs review'} />
        <CertReconciliationDefinition
          label="Reviewed"
          value={flag.reviewedAt ? `${formatDateTime(flag.reviewedAt)} by ${formatPrincipalLabel(undefined, flag.reviewedBy, undefined, 'unknown')}` : 'Not reviewed yet'}
        />
      </dl>
      <CertReconciliationSpecialPrefill flag={flag} />
    </section>
  );
}

function CertReconciliationClassPanel({ flag }: { flag: CertReconciliationFlag | null }) {
  if (!flag) return null;
  const fields = getClassReportReviewFields(flag);
  return (
    <section className="rounded-md border border-neutral-200 bg-white p-4" aria-label="Class report item">
      <h2 className="text-base font-semibold text-neutral-900">Class report item</h2>
      {fields.length > 0 ? (
        <dl className="mt-4 grid gap-3 text-sm">
          {fields.map((field) => (
            <CertReconciliationDefinition key={field.label} label={field.label} value={field.value} />
          ))}
        </dl>
      ) : (
        <p className="mt-4 text-sm text-neutral-600">No class report details were stored for this item.</p>
      )}
    </section>
  );
}

function CertReconciliationSpecialPrefill({ flag }: { flag: CertReconciliationFlag }) {
  if (flag.bucket === 'conditional_stc') {
    return (
      <div className="mt-4 rounded-md border border-info-200 bg-info-50 p-3 text-sm text-info-800">
        Short-term certificate found. Review it before asking the vessel to upload supporting evidence.
      </div>
    );
  }
  if (flag.bucket === 'extended_postponed') {
    return (
      <div className="mt-4 rounded-md border border-warning-200 bg-warning-50 p-3 text-sm text-warning-800">
        Extension or postponement found. Review the class report item before asking the vessel to upload supporting evidence.
      </div>
    );
  }
  return null;
}

function CertReconciliationActionPanel({
  flag,
  run,
  canReview,
  canAddMapping,
}: {
  flag: CertReconciliationFlag;
  run: CertReconciliationRunDetail;
  canReview: boolean;
  canAddMapping: boolean;
}) {
  const [reason, setReason] = useState('');
  const markReviewed = useMarkReconciliationFlagReviewed(run.id);
  const notifyMaster = useNotifyMasterForReconciliationFlag(run.id);
  const alreadyResolved = Boolean(flag.resolvedAt);
  const canSubmit = canReview && reason.trim().length >= 10 && !alreadyResolved;
  const mutationError = markReviewed.error ?? notifyMaster.error;
  const diffRows = Object.entries(flag.diff ?? {});
  const showDiffRows = flag.bucket !== 'conditions_of_class';
  const showMappingAction = canAddMapping && ['missing_in_catalog', 'unmapped_low_confidence'].includes(String(flag.bucket));
  const showMasterUploadLink = Boolean(flag.trackedItemId && run.imo);

  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-neutral-900">Review action</h2>
            <p className="text-sm text-neutral-600">{flag.catalogDisplayName ?? formatClassReportItemTitle(flag)} - {formatReconciliationBucketLabel(flag.bucket)}</p>
          </div>
          {alreadyResolved ? <Badge variant="success">Resolved {formatDateTime(flag.resolvedAt)}</Badge> : null}
        </div>

        {showDiffRows && diffRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-200 text-sm">
              <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                <tr>
                  <th className="px-3 py-2">Field</th>
                  <th className="px-3 py-2">VIMS record</th>
                  <th className="px-3 py-2">Class report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {diffRows.map(([field, value]) => {
                  return (
                    <tr key={field}>
                      <td className="px-3 py-2 font-medium text-neutral-900">{humanizeKey(field)}</td>
                      <td className="px-3 py-2 text-neutral-700">{formatReconciliationDiffValue(value, 'vims')}</td>
                      <td className="px-3 py-2 text-neutral-700">{formatReconciliationDiffValue(value, 'class')}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : showDiffRows ? (
          <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3 text-sm text-neutral-600">
            No detailed differences were recorded for this item.
          </div>
        ) : null}

        {canReview && !alreadyResolved ? (
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor={`reconciliationReason-${flag.id}`}>Review note</Label>
              <Textarea id={`reconciliationReason-${flag.id}`} value={reason} onChange={(event) => setReason(event.target.value)} minLength={10} />
            </div>
            {mutationError ? <p className="text-sm text-error-700">{getErrorMessage(mutationError)}</p> : null}
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                disabled={!canSubmit || notifyMaster.isPending}
                onClick={() => notifyMaster.mutate({ flagId: flag.id, reason })}
              >
                <Share2 className="mr-2 h-4 w-4" aria-hidden="true" />
                Notify Master
              </Button>
              {showMasterUploadLink ? (
                <Button asChild type="button" variant="outline">
                  <Link to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(String(run.imo), String(flag.trackedItemId))}>
                    Ask vessel to update
                  </Link>
                </Button>
              ) : null}
              {showMappingAction ? (
                <CertClassMappingDialog flag={flag} run={run} />
              ) : null}
              <Button
                type="button"
                disabled={!canSubmit || markReviewed.isPending}
                onClick={() => markReviewed.mutate({ flagId: flag.id, reason })}
              >
                <CheckCircle2 className="mr-2 h-4 w-4" aria-hidden="true" />
                Mark reviewed
              </Button>
            </div>
          </div>
        ) : null}
        {!canReview && !alreadyResolved && showMappingAction ? (
          <CertClassMappingDialog flag={flag} run={run} />
        ) : null}
      </CardContent>
    </Card>
  );
}

function CertClassMappingDialog({ flag, run }: { flag: CertReconciliationFlag; run: CertReconciliationRunDetail }) {
  const [open, setOpen] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState('');
  const [catalogId, setCatalogId] = useState(flag.catalogId ?? '');
  const [certOrSurveyKind, setCertOrSurveyKind] = useState('renewal');
  const [notes, setNotes] = useState('');
  const [mappingReason, setMappingReason] = useState('');
  const catalogRows = useCatalogRows({ isActive: true, q: catalogSearch || undefined, page: 1, pageSize: 30 });
  const addMapping = useAddClassCodeMappingForFlag(run.id);
  const classExtract = normalizeRecord(flag.classRowExtract);
  const classCode = formatUnknown(
    classExtract?.class_code_or_name ??
      classExtract?.classCodeOrName ??
      classExtract?.class_code ??
      classExtract?.name ??
      'not available'
  );
  const rows = catalogRows.data?.results ?? [];
  const selectedCatalog = rows.find((row) => row.id === catalogId);
  const canSave = Boolean(catalogId.trim()) && mappingReason.trim().length >= 10 && !addMapping.isPending;

  useEffect(() => {
    setCatalogId(flag.catalogId ?? '');
    setCatalogSearch('');
    setCertOrSurveyKind('renewal');
    setNotes('');
    setMappingReason('');
  }, [flag.id, flag.catalogId]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button type="button" variant="outline">
          <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
          Link to VIMS certificate type
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Link class report item</DialogTitle>
          <DialogDescription>
            Connect {classCode} from the class report to the correct VIMS certificate type. Future checks will use this link automatically.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor={`mappingCatalogSearch-${flag.id}`}>Search certificate types</Label>
            <Input
              id={`mappingCatalogSearch-${flag.id}`}
              value={catalogSearch}
              onChange={(event) => setCatalogSearch(event.target.value)}
              placeholder="Search VIMS certificate types"
            />
          </div>
          {rows.length > 0 ? (
            <div className="max-h-40 space-y-2 overflow-y-auto rounded-md border border-neutral-200 p-2">
              {rows.slice(0, 8).map((row) => (
                <button
                  key={row.id}
                  type="button"
                  className={`w-full rounded-md border px-3 py-2 text-left text-sm ${
                    row.id === catalogId ? 'border-primary-500 bg-primary-50' : 'border-neutral-200 bg-white hover:bg-neutral-50'
                  }`}
                  onClick={() => setCatalogId(row.id)}
                >
                  <span className="font-medium text-neutral-900">{row.displayName}</span>
                  <span className="block text-xs text-neutral-500">{row.canonicalCode}</span>
                </button>
              ))}
            </div>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor={`mappingCatalogId-${flag.id}`}>Selected certificate type</Label>
            <Input
              id={`mappingCatalogId-${flag.id}`}
              value={catalogId}
              onChange={(event) => setCatalogId(event.target.value)}
              placeholder="Select from search results"
            />
            {selectedCatalog ? <p className="text-xs text-neutral-600">Selected: {selectedCatalog.displayName}</p> : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor={`mappingKind-${flag.id}`}>Certificate or survey kind</Label>
            <Select value={certOrSurveyKind} onValueChange={setCertOrSurveyKind}>
              <SelectTrigger id={`mappingKind-${flag.id}`}><SelectValue /></SelectTrigger>
              <SelectContent>
                {CLASS_MAPPING_KIND_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor={`mappingNotes-${flag.id}`}>Notes</Label>
            <Textarea id={`mappingNotes-${flag.id}`} value={notes} onChange={(event) => setNotes(event.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor={`mappingReason-${flag.id}`}>Why this is the correct link</Label>
            <Textarea
              id={`mappingReason-${flag.id}`}
              value={mappingReason}
              onChange={(event) => setMappingReason(event.target.value)}
              minLength={10}
            />
          </div>
          {addMapping.error ? <p className="text-sm text-error-700">{getErrorMessage(addMapping.error)}</p> : null}
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button type="button" variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            type="button"
            disabled={!canSave}
            onClick={() =>
              addMapping.mutate(
                {
                  flagId: flag.id,
                  payload: {
                    catalogId,
                    certOrSurveyKind,
                    notes: notes.trim() || null,
                    reason: mappingReason,
                  },
                },
                { onSuccess: () => setOpen(false) }
              )
            }
          >
            <Save className="mr-2 h-4 w-4" aria-hidden="true" />
            Save link
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function CertReconciliationDefinition({ label, value }: { label: string; value: unknown }) {
  const displayValue = formatReconciliationDefinitionValue(label, value);
  return (
    <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
      <dt className="text-xs font-semibold uppercase text-neutral-500">{label}</dt>
      <dd className="mt-1 whitespace-pre-wrap break-words text-neutral-900">{displayValue}</dd>
    </div>
  );
}

function formatReconciliationDefinitionValue(label: string, value: unknown): string {
  const displayValue = formatUnknown(value);
  if (label !== 'Summary') {
    return displayValue;
  }
  return formatClassReportSummaryText(displayValue);
}

function formatClassReportSummaryText(value: string): string {
  return value
    .replace(/\r\n?/g, '\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\s+((?:\d+\.)+\s+)/g, '\n$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function CertTrackedItemDetailLoading({ trackedItemId }: { trackedItemId: string }) {
  return (
    <RootLayout>
      <PageHeader title={`Certificate ${trackedItemId}`} />
      <div className="space-y-4 p-4">
        <Skeleton className="h-28 w-full" />
        <div className="grid gap-4 xl:grid-cols-[1.05fr_1fr_1fr]">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    </RootLayout>
  );
}

function CertTrackedItemDetailPage({ imo, trackedItemId }: { imo: string; trackedItemId: string }) {
  const canReadTrackedItems = useCertsPermission(FORM_IDS.CERTS_TRACKED_ITEMS);
  const canCreateOrEdit = useCertsPermission(FORM_IDS.CERTS_TRACKED_ITEMS, PROCESS_IDS.CERTS_CREATE);
  const canSubmit = useCertsPermission(FORM_IDS.CERTS_TRACKED_ITEMS, PROCESS_IDS.CERTS_SUBMIT);
  const canApprove = useCertsPermission(FORM_IDS.CERTS_TRACKED_ITEMS, PROCESS_IDS.CERTS_APPROVE);
  const canReject = useCertsPermission(FORM_IDS.CERTS_TRACKED_ITEMS, PROCESS_IDS.CERTS_REJECT);
  const auth = useAuth();
  const detail = useTrackedItemDetail(canReadTrackedItems ? trackedItemId : undefined);

  if (!canReadTrackedItems) {
    return <CertsPermissionDenied />;
  }

  if (detail.isLoading) {
    return <CertTrackedItemDetailLoading trackedItemId={trackedItemId} />;
  }

  if (detail.isError || !detail.data) {
    return (
      <RootLayout>
        <PageHeader title="Certificate Detail" />
        <div className="p-4">
          <CertCatalogError
            message={`Could not load certificate detail. ${getErrorMessage(detail.error)}`}
            onRetry={() => detail.refetch()}
          />
        </div>
      </RootLayout>
    );
  }

  const item = detail.data;
  const isVesselCrew = auth.isCrew && !auth.isMaster;
  const canDirectEditItem = canCreateOrEdit && (!isVesselCrew || item.submissionScope !== 'master_only');
  const canSubmitItem = canSubmit && (!isVesselCrew || item.submissionScope === 'all_ranks_with_approval');
  const canDecideApproval = canDecideCertApproval(auth);

  return (
    <RootLayout>
      <PageHeader title="Certificate Detail" />
      <div className="space-y-4 p-4">
        <CertTrackedItemHeader item={item} imo={imo} />
        <CertTrackedItemSpecialBanners item={item} imo={imo} />
        <div className="grid gap-4 xl:grid-cols-[1.05fr_1fr_1fr]">
          <CertTrackedItemMetadataPanel item={item} imo={imo} canEdit={canDirectEditItem} />
          <CertTrackedItemPdfPanel item={item} imo={imo} canUpload={canDirectEditItem} />
          <CertTrackedItemWorkflowPanel
            item={item}
            imo={imo}
            canSubmit={canSubmitItem}
            canApprove={canApprove && canDecideApproval}
            canReject={canReject && canDecideApproval}
          />
        </div>
      </div>
    </RootLayout>
  );
}

function CertTrackedItemHeader({ item, imo }: { item: CertTrackedItemDetail; imo: string }) {
  const vesselLabel = item.vesselName ?? item.vesselCode ?? item.vesselImo ?? formatEntityLabel(imo, 'Vessel');
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-3">
            <div>
              <div className="mb-2 flex flex-wrap gap-2">
                {item.catalogCode ? <Badge variant="secondary">Certificate code {item.catalogCode}</Badge> : null}
                {item.type ? <Badge variant="info">{formatStatus(item.type)}</Badge> : null}
              </div>
              <h1 className="text-2xl font-semibold text-neutral-900">
                {item.displayName ?? item.catalogDisplayName ?? item.catalogCode ?? 'Certificate'}
              </h1>
              <p className="text-sm text-neutral-600">
                {vesselLabel} - {item.certificateNumber ?? 'certificate number not set'}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <CertStatusBadge status={item.status} />
              {item.approvalState ? <Badge variant={statusBadgeVariant(item.approvalState)}>{formatStatus(item.approvalState)}</Badge> : null}
              {item.pdfMissing ? <Badge variant="destructive">Certificates missing</Badge> : null}
              {item.lifecycleStatus ? <Badge variant="secondary">{formatStatus(item.lifecycleStatus)}</Badge> : null}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link to={ROUTES.CERTS_VESSEL_DASHBOARD(imo)}>Back to vessel</Link>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function CertTrackedItemSpecialBanners({ item, imo }: { item: CertTrackedItemDetail; imo: string }) {
  const banners: Array<{ key: string; variant: 'warning' | 'destructive' | 'info'; content: ReactNode }> = [];
  if (item.status === 'expired_at_onboarding') {
    banners.push({
      key: 'quarantine',
      variant: 'warning',
      content: 'This cert was already expired at onboarding. Alerts are suppressed until renewal or DPA acknowledgement.',
    });
  }
  if (item.pdfMissing) {
    banners.push({
      key: 'pdf-missing',
      variant: 'destructive',
      content: 'Certificate not on file. Request copy from issuer.',
    });
  }
  if (item.approvalState === 'rejected') {
    banners.push({
      key: 'rejected',
      variant: 'destructive',
      content: `Rejected: ${item.rejectionReason ?? 'No rejection reason recorded.'}`,
    });
  }
  if (item.supersedesId) {
    banners.push({
      key: 'supersedes',
      variant: 'info',
      content: (
        <>
          This cert supersedes{' '}
          <Link className="font-semibold underline" to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(imo, item.supersedesId)}>
            superseded certificate
          </Link>
          .
        </>
      ),
    });
  }

  if (banners.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      {banners.map((banner) => (
        <div key={banner.key} className={`rounded-md border p-3 text-sm ${bannerClassName(banner.variant)}`}>
          {banner.content}
        </div>
      ))}
    </div>
  );
}

function CertTrackedItemMetadataPanel({ item, imo, canEdit }: { item: CertTrackedItemDetail; imo: string; canEdit: boolean }) {
  const updateMetadata = useUpdateTrackedItemMetadata(item.id, imo);
  const [isEditing, setIsEditing] = useState(false);
  const [certificateNumber, setCertificateNumber] = useState(item.certificateNumber ?? '');
  const [issuingAuthority, setIssuingAuthority] = useState(item.issuingAuthority ?? '');
  const [placeOfIssue, setPlaceOfIssue] = useState(item.placeOfIssue ?? '');
  const [issueDate, setIssueDate] = useState(item.issueDate ?? '');
  const [expiryDate, setExpiryDate] = useState(item.expiryDate ?? '');
  const [reason, setReason] = useState('Certificate details corrected after review.');
  const [formError, setFormError] = useState('');
  const hierarchyRows = [
    ['Parent', item.parentId ? formatEntityLabel(item.parentId, 'Parent certificate') : 'Top-level certificate'],
    ['Relationship', item.relationshipType ? formatStatus(item.relationshipType) : 'None'],
    ['Supersedes', item.supersedesId ? formatEntityLabel(item.supersedesId, 'Superseded certificate') : 'None'],
  ];

  useEffect(() => {
    if (isEditing) {
      return;
    }
    setCertificateNumber(item.certificateNumber ?? '');
    setIssuingAuthority(item.issuingAuthority ?? '');
    setPlaceOfIssue(item.placeOfIssue ?? '');
    setIssueDate(item.issueDate ?? '');
    setExpiryDate(item.expiryDate ?? '');
  }, [isEditing, item.certificateNumber, item.expiryDate, item.issueDate, item.issuingAuthority, item.placeOfIssue]);

  const resetMetadataForm = () => {
    setCertificateNumber(item.certificateNumber ?? '');
    setIssuingAuthority(item.issuingAuthority ?? '');
    setPlaceOfIssue(item.placeOfIssue ?? '');
    setIssueDate(item.issueDate ?? '');
    setExpiryDate(item.expiryDate ?? '');
    setReason('Certificate details corrected after review.');
    setFormError('');
    setIsEditing(false);
  };

  const handleMetadataSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedAuthority = issuingAuthority.trim();
    const trimmedReason = reason.trim();
    if (!trimmedAuthority) {
      setFormError('Issuing authority is required.');
      return;
    }
    if (!trimmedReason) {
      setFormError('Please enter a reason for the change.');
      return;
    }
    setFormError('');
    updateMetadata.mutate(
      {
        certificateNumber: certificateNumber.trim() || null,
        issuingAuthority: trimmedAuthority,
        placeOfIssue: placeOfIssue.trim() || null,
        issueDate: issueDate || null,
        expiryDate: item.validityType === 'permanent' ? null : expiryDate || null,
        reason: trimmedReason,
      },
      {
        onSuccess: () => {
          setIsEditing(false);
        },
      }
    );
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle>Certificate details</CardTitle>
        {canEdit ? (
          <Button type="button" variant="outline" size="sm" onClick={() => setIsEditing((current) => !current)}>
            {isEditing ? 'Close edit' : 'Edit'}
          </Button>
        ) : null}
      </CardHeader>
      <CardContent className="space-y-5">
        {isEditing ? (
          <form className="space-y-4" onSubmit={handleMetadataSubmit}>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor={`certNumber-${item.id}`}>Certificate number</Label>
                <Input id={`certNumber-${item.id}`} value={certificateNumber} onChange={(event) => setCertificateNumber(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`issuingAuthority-${item.id}`}>Issuing authority</Label>
                <Input id={`issuingAuthority-${item.id}`} value={issuingAuthority} onChange={(event) => setIssuingAuthority(event.target.value)} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`placeOfIssue-${item.id}`}>Place of issue</Label>
                <Input id={`placeOfIssue-${item.id}`} value={placeOfIssue} onChange={(event) => setPlaceOfIssue(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`issueDate-${item.id}`}>Issue date</Label>
                <Input id={`issueDate-${item.id}`} type="date" value={issueDate} onChange={(event) => setIssueDate(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`expiryDate-${item.id}`}>Expiry date</Label>
                <Input
                  id={`expiryDate-${item.id}`}
                  type="date"
                  value={expiryDate}
                  onChange={(event) => setExpiryDate(event.target.value)}
                  disabled={item.validityType === 'permanent'}
                />
              </div>
              <div className="space-y-2">
                <Label>Valid for</Label>
                <Input value={formatCertificateValidity(item)} disabled />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor={`metadataReason-${item.id}`}>Reason</Label>
              <Textarea id={`metadataReason-${item.id}`} value={reason} onChange={(event) => setReason(event.target.value)} required />
            </div>
            {formError ? <p className="text-sm text-error-700">{formError}</p> : null}
            {updateMetadata.isError ? <p className="text-sm text-error-700">{getErrorMessage(updateMetadata.error)}</p> : null}
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={updateMetadata.isPending}>
                Save details
              </Button>
              <Button type="button" variant="outline" onClick={resetMetadataForm} disabled={updateMetadata.isPending}>
                Cancel
              </Button>
            </div>
          </form>
        ) : (
          <CertDetailGrid
            rows={[
              ['Certificate number', item.certificateNumber ?? 'Not set'],
              ['Issuing authority', item.issuingAuthority ?? 'Not set'],
              ['Place of issue', item.placeOfIssue ?? 'Not set'],
              ['Valid for', formatCertificateValidity(item)],
            ]}
          />
        )}
        <div>
          <h2 className="mb-3 text-sm font-semibold uppercase text-neutral-500">Important dates</h2>
          <CertDetailGrid
            rows={[
              ['Issue date', formatDate(item.issueDate)],
              ['Expiry date', formatExpiry(item)],
              ['Renewal starts', formatDate(item.windowOpen)],
              ['Renewal deadline', formatDate(item.windowClose)],
              ['Next due', formatDate(item.nextDueDate)],
            ]}
          />
        </div>
        <details className="rounded-md border border-neutral-200 bg-neutral-50/60">
          <summary className="cursor-pointer px-3 py-2 text-sm font-medium text-neutral-700">More details</summary>
          <div className="space-y-4 border-t border-neutral-200 p-3">
            <CertDetailGrid
              rows={[
                ['Anniversary date', formatDate(item.anniversaryDate)],
                ['Last completed', formatDate(item.lastDoneDate)],
                ['Postponed until', formatDate(item.postponedUntil)],
                ['Certificate family', item.formVariant ?? 'n/a'],
                ['Source', item.source ? formatStatus(item.source) : 'Not set'],
              ]}
            />
            <CertDetailGrid rows={hierarchyRows} />
          </div>
        </details>
        {item.extensionAuthority || item.extensionReason || item.extensionLetterPdfId ? (
          <div>
            <h2 className="mb-3 text-sm font-semibold uppercase text-neutral-500">Extension</h2>
            <CertDetailGrid
              rows={[
                ['Authority', item.extensionAuthority ?? 'Not set'],
                ['Reason', item.extensionReason ?? 'Not set'],
                ['Letter PDF', item.extensionLetterPdfId ? formatEntityLabel(item.extensionLetterPdfId, 'Attached PDF') : 'Not attached'],
              ]}
            />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function CertTrackedItemPdfPanel({ item, imo, canUpload }: { item: CertTrackedItemDetail; imo: string; canUpload: boolean }) {
  const activePdf = item.pdfVersions.find((pdf) => pdf.isActive);
  const uploadMutation = useUploadTrackedItemPdf(item.id, imo);
  const reparseMutation = useReparseTrackedItemPdf(item.id, imo);
  const removeMutation = useRemoveTrackedItemPdf(item.id, imo);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadReason, setUploadReason] = useState('');
  const [removeOpen, setRemoveOpen] = useState(false);
  const [removeReason, setRemoveReason] = useState('');
  const [viewError, setViewError] = useState('');
  const [viewLoading, setViewLoading] = useState(false);

  const handleUploadSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!uploadFile || uploadMutation.isPending) {
      return;
    }

    uploadMutation.mutate(
      {
        file: uploadFile,
        reason: uploadReason.trim() || 'Certificate PDF uploaded from detail screen.',
      },
      {
        onSuccess: () => {
          setUploadFile(null);
          setUploadReason('');
          setUploadOpen(false);
        },
      }
    );
  };

  const handleRemoveSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const reason = removeReason.trim();
    if (!activePdf || !reason || removeMutation.isPending) {
      return;
    }

    removeMutation.mutate(
      { reason },
      {
        onSuccess: () => {
          setRemoveReason('');
          setRemoveOpen(false);
        },
      }
    );
  };

  const handleOpenPdf = async () => {
    if (!activePdf?.id || viewLoading) {
      return;
    }

    setViewError('');
    const pdfWindow = window.open('', '_blank');
    if (!pdfWindow) {
      setViewError('Allow pop-ups for this site, then try again.');
      return;
    }
    pdfWindow.opener = null;
    setViewLoading(true);

    try {
      const blob = await certsApi.getTrackedItemPdfBlob(item.id, activePdf.id);
      const objectUrl = URL.createObjectURL(blob);
      pdfWindow.location.href = objectUrl;
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch (error) {
      pdfWindow.close();
      setViewError(getErrorMessage(error));
    } finally {
      setViewLoading(false);
    }
  };

  const handleReparsePdf = () => {
    if (!activePdf || reparseMutation.isPending) {
      return;
    }
    reparseMutation.mutate({ reason: 'Certificate PDF read again from detail screen.' });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Certificate file</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md border border-neutral-200 bg-neutral-50/70 p-3">
          {activePdf ? (
            <div className="space-y-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <button
                    type="button"
                    className="max-w-full truncate text-left font-medium text-primary-700 underline-offset-4 transition-colors hover:text-primary-800 hover:underline disabled:cursor-wait disabled:text-neutral-500"
                    onClick={handleOpenPdf}
                    disabled={viewLoading}
                  >
                    {activePdf.filename || 'View certificate PDF'}
                  </button>
                  <p className="text-sm text-neutral-600">
                    Uploaded {formatDateTime(activePdf.uploadedAt)} by {formatPrincipalLabel(activePdf.uploadedByDisplay, activePdf.uploadedBy)}
                  </p>
                  <p className="text-xs text-neutral-500">{formatBytes(activePdf.sizeBytes)}</p>
                </div>
                <Button type="button" size="sm" variant="outline" onClick={handleOpenPdf} disabled={viewLoading}>
                  <FileText className="mr-2 h-4 w-4" aria-hidden="true" />
                  {viewLoading ? 'Opening...' : 'View PDF'}
                </Button>
              </div>
              {viewError ? <p className="rounded-md border border-error-200 bg-error-50 px-3 py-2 text-sm text-error-700">{viewError}</p> : null}
            </div>
          ) : (
            <div className="flex min-h-56 items-center justify-center text-center">
              <div className="space-y-2">
              <FileText className="mx-auto h-8 w-8 text-neutral-400" aria-hidden="true" />
              <p className="font-medium text-neutral-900">No active certificate file</p>
              <p className="text-sm text-neutral-600">{item.pdfMissing ? 'This certificate is marked as missing.' : 'No certificate file has been uploaded yet.'}</p>
              </div>
            </div>
          )}
        </div>
        {canUpload ? (
          <div className="flex flex-wrap gap-2">
            <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
              <DialogTrigger asChild>
                <Button type="button" variant="outline">
                  <UploadCloud className="mr-2 h-4 w-4" aria-hidden="true" />
                  Upload certificate
                </Button>
              </DialogTrigger>
              <DialogContent>
                <form className="space-y-4" onSubmit={handleUploadSubmit}>
                  <DialogHeader>
                    <DialogTitle>Upload certificate</DialogTitle>
                    <DialogDescription>
                      Attach the scanned certificate file and add a short reason for the change.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-2">
                    <Label htmlFor={`trackedItemPdfUpload-${item.id}`}>Certificate file</Label>
                    <Input
                      id={`trackedItemPdfUpload-${item.id}`}
                      type="file"
                      accept="application/pdf,.pdf"
                      onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`trackedItemPdfReason-${item.id}`}>Reason</Label>
                    <Textarea
                      id={`trackedItemPdfReason-${item.id}`}
                      value={uploadReason}
                      onChange={(event) => setUploadReason(event.target.value)}
                      placeholder="Uploading renewed certificate."
                    />
                  </div>
                  {uploadMutation.error ? (
                    <p className="text-sm text-error-700">{getErrorMessage(uploadMutation.error)}</p>
                  ) : null}
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button type="button" variant="outline" disabled={uploadMutation.isPending}>
                        Cancel
                      </Button>
                    </DialogClose>
                    <Button type="submit" disabled={!uploadFile || uploadMutation.isPending}>
                      {uploadMutation.isPending ? 'Uploading...' : 'Upload certificate'}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
            {activePdf ? (
              <Button type="button" variant="outline" onClick={handleReparsePdf} disabled={reparseMutation.isPending}>
                <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
                {reparseMutation.isPending ? 'Reading...' : 'Read PDF again'}
              </Button>
            ) : null}
            {activePdf ? (
              <Dialog open={removeOpen} onOpenChange={setRemoveOpen}>
                <DialogTrigger asChild>
                  <Button type="button" variant="outline">
                    <Trash2 className="mr-2 h-4 w-4" aria-hidden="true" />
                    Remove file
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <form className="space-y-4" onSubmit={handleRemoveSubmit}>
                    <DialogHeader>
                      <DialogTitle>Remove active certificate file</DialogTitle>
                      <DialogDescription>
                        Remove the currently active certificate file and add a short reason for the change.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3 text-sm">
                      <p className="font-medium text-neutral-900">{activePdf.filename}</p>
                      <p className="text-neutral-600">
                        Uploaded {formatDateTime(activePdf.uploadedAt)} by {formatPrincipalLabel(activePdf.uploadedByDisplay, activePdf.uploadedBy)}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor={`trackedItemPdfRemoveReason-${item.id}`}>Reason</Label>
                      <Textarea
                        id={`trackedItemPdfRemoveReason-${item.id}`}
                        value={removeReason}
                        onChange={(event) => setRemoveReason(event.target.value)}
                        placeholder="Wrong certificate file uploaded."
                      />
                    </div>
                    {removeMutation.error ? (
                      <p className="text-sm text-error-700">{getErrorMessage(removeMutation.error)}</p>
                    ) : null}
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button type="button" variant="outline" disabled={removeMutation.isPending}>
                          Cancel
                        </Button>
                      </DialogClose>
                      <Button type="submit" variant="destructive" disabled={!removeReason.trim() || removeMutation.isPending}>
                        {removeMutation.isPending ? 'Removing...' : 'Remove file'}
                      </Button>
                    </DialogFooter>
                  </form>
                </DialogContent>
              </Dialog>
            ) : null}
          </div>
        ) : null}
        {reparseMutation.error ? (
          <p className="rounded-md border border-error-200 bg-error-50 px-3 py-2 text-sm text-error-700">{getErrorMessage(reparseMutation.error)}</p>
        ) : null}
        <div className="space-y-2">
          <h2 className="text-sm font-semibold uppercase text-neutral-500">Version history</h2>
          {item.pdfVersions.length === 0 ? (
            <p className="text-sm text-neutral-600">No certificate files recorded.</p>
          ) : (
            <div className="space-y-2">
              {item.pdfVersions.map((pdf) => (
                <div key={pdf.id} className={`rounded-md border p-3 text-sm ${pdf.isActive ? 'border-green-200 bg-green-50' : 'border-neutral-200 bg-white'}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-neutral-900">{pdf.filename}</p>
                      <p className="text-neutral-600">
                        {formatBytes(pdf.sizeBytes)} - uploaded {formatDateTime(pdf.uploadedAt)} by {formatPrincipalLabel(pdf.uploadedByDisplay, pdf.uploadedBy)}
                      </p>
                    </div>
                    <Badge variant={pdf.isActive ? 'success' : 'secondary'}>{pdf.isActive ? 'Active' : 'Superseded'}</Badge>
                  </div>
                  {pdf.scheduledDeleteAt ? <p className="mt-2 text-xs text-warning-700">Delete scheduled {formatDateTime(pdf.scheduledDeleteAt)}</p> : null}
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function CertTrackedItemWorkflowPanel({
  item,
  imo,
  canSubmit,
  canApprove,
  canReject,
}: {
  item: CertTrackedItemDetail;
  imo: string;
  canSubmit: boolean;
  canApprove: boolean;
  canReject: boolean;
}) {
  const [reason, setReason] = useState('');
  const submitMutation = useSubmitTrackedItem(item.id, imo);
  const approveMutation = useApproveTrackedItem(item.id, imo);
  const rejectMutation = useRejectTrackedItem(item.id, imo);
  const canSubmitCurrent = canSubmit && ['draft', 'rejected'].includes(item.approvalState ?? '');
  const canApprovalDecision = item.approvalState === 'pending_master_approval';
  const mutationError = submitMutation.error ?? approveMutation.error ?? rejectMutation.error;

  const transitionPayload = () => ({
    reason: reason.trim() || 'Certificate workflow action.',
    version: item.version,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Review and history</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <CertDetailGrid
          rows={[
            ['Approval status', item.approvalState ? formatStatus(item.approvalState) : 'Not set'],
            ['Submitted by', formatPrincipalLabel(item.submittedByDisplay, item.submittedBy, undefined, 'Not submitted')],
            ['Submitted on', formatDateTime(item.submittedAt)],
            ['Approved by', formatPrincipalLabel(item.approvedByDisplay, item.approvedBy, undefined, 'Not approved')],
            ['Approved on', formatDateTime(item.approvedAt)],
            ['Times rejected', String(item.rejectionCount ?? 0)],
            ['Draft expires on', formatDateTime(item.draftExpiresAt)],
          ]}
        />
        {(canSubmitCurrent || (canApprovalDecision && (canApprove || canReject))) ? (
          <div className="space-y-3 rounded-md border border-neutral-200 p-3">
            <Label htmlFor="trackedItemTransitionReason">Review note</Label>
            <Textarea
              id="trackedItemTransitionReason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Add a short note for this review"
            />
            {mutationError ? <p className="text-sm text-error-700">{getErrorMessage(mutationError)}</p> : null}
            <div className="flex flex-wrap gap-2">
              {canSubmitCurrent ? (
                <Button type="button" onClick={() => submitMutation.mutate(transitionPayload())} disabled={submitMutation.isPending}>
                  Submit for approval
                </Button>
              ) : null}
              {canApprovalDecision && canApprove ? (
                <Button type="button" onClick={() => approveMutation.mutate(transitionPayload())} disabled={approveMutation.isPending}>
                  Approve
                </Button>
              ) : null}
              {canApprovalDecision && canReject ? (
                <Button type="button" variant="destructive" onClick={() => rejectMutation.mutate(transitionPayload())} disabled={rejectMutation.isPending}>
                  Reject
                </Button>
              ) : null}
            </div>
          </div>
        ) : null}
        <CertApprovalTimeline events={item.approvalEvents} />
        <CertTrackedAuditEvents events={item.auditEvents} />
      </CardContent>
    </Card>
  );
}

function CertDetailGrid({ rows }: { rows: Array<[string, ReactNode]> }) {
  return (
    <dl className="grid gap-3 text-sm sm:grid-cols-2">
      {rows.map(([label, value]) => (
        <div key={label} className="space-y-1">
          <dt className="text-neutral-500">{label}</dt>
          <dd className="font-medium text-neutral-900">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function CertApprovalTimeline({ events }: { events: CertTrackedItemDetail['approvalEvents'] }) {
  return (
    <div className="space-y-2">
      <h2 className="text-sm font-semibold uppercase text-neutral-500">Approval history</h2>
      {events.length === 0 ? (
        <p className="text-sm text-neutral-600">No approval activity yet.</p>
      ) : (
        <div className="space-y-2">
          {events.map((event) => (
            <div key={event.id} className="rounded-md border border-neutral-200 p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={statusBadgeVariant(event.toState)}>{formatApprovalEventTitle(event)}</Badge>
                <span className="text-neutral-600">{formatPrincipalLabel(event.actorDisplayName, event.actorUserId, event.actorRole)}</span>
              </div>
              <p className="mt-1 text-neutral-600">{formatDateTime(event.timestampUtc)}</p>
              {event.reason ? <p className="mt-2 text-neutral-800">{event.reason}</p> : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CertTrackedAuditEvents({ events }: { events: CertTrackedItemAuditEvent[] }) {
  return (
    <div className="space-y-2">
      <h2 className="text-sm font-semibold uppercase text-neutral-500">Recent activity</h2>
      {events.length === 0 ? (
        <p className="text-sm text-neutral-600">No activity recorded yet.</p>
      ) : (
        <div className="space-y-2">
          {events.map((event) => (
            <div key={event.id} className="rounded-md border border-neutral-200 p-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Badge variant="secondary">{formatAuditAction(event.action)}</Badge>
                <span className="text-neutral-500">{formatDateTime(event.timestampUtc)}</span>
              </div>
              <p className="mt-1 text-neutral-600">
                By {formatPrincipalLabel(event.actorDisplayName, event.actorUserId, event.actorRole)}
              </p>
              <p className="mt-2 text-neutral-700">{summarizeTrackedAuditDiff(event)}</p>
              {event.reason ? <p className="mt-1 text-neutral-600">{event.reason}</p> : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CertOnboardingHubPage() {
  const canRead = useCertsPermission(FORM_IDS.CERTS_ONBOARDING);
  const canStart = useCertsPermission(FORM_IDS.CERTS_ONBOARDING, PROCESS_IDS.CERTS_CREATE);
  const hub = useOnboardingHub();

  if (!canRead) {
    return <CertsPermissionDenied />;
  }

  if (hub.isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Onboarding Hub" />
        <div className="space-y-3 p-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-80 w-full" />
        </div>
      </RootLayout>
    );
  }

  if (hub.isError || !hub.data) {
    return (
      <RootLayout>
        <PageHeader title="Onboarding Hub" />
        <div className="p-4">
          <CertCatalogError message={getErrorMessage(hub.error)} onRetry={() => hub.refetch()} />
        </div>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <PageHeader title="Onboarding Hub" />
      <div className="space-y-4 p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-neutral-900">Onboarding Hub</h1>
            <p className="text-sm text-neutral-600">Vessels currently in certificate onboarding.</p>
          </div>
          {canStart ? (
            <Button asChild>
              <Link to={ROUTES.CERTS_ONBOARDING_NEW}>
                <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
                New vessel onboarding
              </Link>
            </Button>
          ) : null}
        </div>
        {hub.data.results.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-sm text-neutral-600">No onboardings in progress.</CardContent>
          </Card>
        ) : (
          <div className="overflow-x-auto rounded-md border border-neutral-200">
            <table className="min-w-full divide-y divide-neutral-200 text-sm">
              <thead className="bg-neutral-50 text-left text-xs uppercase text-neutral-500">
                <tr>
                  <th className="px-4 py-3">Vessel</th>
                  <th className="px-4 py-3">Step</th>
                  <th className="px-4 py-3">Batches</th>
                  <th className="px-4 py-3">Coverage</th>
                  <th className="px-4 py-3">FM sign-off</th>
                  <th className="px-4 py-3">Last activity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100 bg-white">
                {hub.data.results.map((row) => (
                  <CertOnboardingHubTableRow key={row.vessel.id ?? row.vessel.imo ?? row.vessel.name} row={row} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </RootLayout>
  );
}

function CertOnboardingHubTableRow({ row }: { row: CertOnboardingHubRow }) {
  const vesselKey = row.vessel.imo ?? row.vessel.id ?? '';
  return (
    <tr className="hover:bg-neutral-50">
      <td className="px-4 py-3">
        <Link className="font-medium text-primary-700 hover:text-primary-800" to={ROUTES.CERTS_ONBOARDING_WIZARD(vesselKey)}>
          {row.vessel.name ?? row.vessel.code ?? row.vessel.imo ?? 'Unknown vessel'}
        </Link>
        <div className="text-xs text-neutral-500">{row.vessel.imo ?? row.vessel.code ?? 'No IMO'}</div>
      </td>
      <td className="px-4 py-3">Step {row.currentStep}</td>
      <td className="px-4 py-3">{row.batchCount}</td>
      <td className="px-4 py-3">{row.mandatoryCoveragePercent}%</td>
      <td className="px-4 py-3">{row.pendingFmSignoff ? 'Pending' : 'Not ready'}</td>
      <td className="px-4 py-3">{formatDateTime(row.lastActivity)}</td>
    </tr>
  );
}

function CertOnboardingWizardPage({ vesselId }: { vesselId: string }) {
  const canRead = useCertsPermission(FORM_IDS.CERTS_ONBOARDING);
  const canCreate = useCertsPermission(FORM_IDS.CERTS_ONBOARDING, PROCESS_IDS.CERTS_CREATE);
  const canSignoff = useCertsPermission(FORM_IDS.CERTS_ONBOARDING, PROCESS_IDS.CERTS_SUBMIT);
  const canRollback = useCertsPermission(FORM_IDS.CERTS_ONBOARDING, PROCESS_IDS.CERTS_ROLLBACK);
  const wizard = useOnboardingWizardState(canRead ? vesselId : undefined);
  const profileMutation = useSaveOnboardingProfile(vesselId);
  const batchMutation = useCreateOnboardingBatch(vesselId);
  const coverageMutation = useCoverageOverride(vesselId);
  const signoffMutation = useFmSignoff(vesselId);
  const rollbackMutation = useRollbackOnboarding(vesselId);
  const location = useLocation();
  const requestedStep = Number(new URLSearchParams(location.search).get('step') || 0);
  const [profileForm, setProfileForm] = useState({
    anniversaryDate: '',
    shipType: 'bulk_carrier',
    marineSuptUserId: '',
    technicalManagerUserId: '',
  });
  const [batchBlobIds, setBatchBlobIds] = useState('');
  const [coverageReason, setCoverageReason] = useState('');
  const [actionReason, setActionReason] = useState('');
  const [rollbackReason, setRollbackReason] = useState('');

  if (!canRead) {
    return <CertsPermissionDenied />;
  }

  if (wizard.isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Onboarding" />
        <div className="space-y-3 p-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </RootLayout>
    );
  }

  if (wizard.isError || !wizard.data) {
    return (
      <RootLayout>
        <PageHeader title="Onboarding" />
        <div className="p-4">
          <CertCatalogError message={getErrorMessage(wizard.error)} onRetry={() => wizard.refetch()} />
        </div>
      </RootLayout>
    );
  }

  const state = wizard.data;
  const currentStep = requestedStep >= 1 && requestedStep <= 7 ? requestedStep : state.currentStep;
  const vesselName = state.vessel.name ?? state.vessel.imo ?? formatEntityLabel(vesselId, 'Vessel');

  const saveProfile = (event: FormEvent) => {
    event.preventDefault();
    profileMutation.mutate({
      anniversaryDate: profileForm.anniversaryDate || state.config?.anniversaryDate || '',
      shipType: profileForm.shipType || state.config?.shipType || 'bulk_carrier',
      marineSuptUserId: profileForm.marineSuptUserId || state.config?.marineSuptUserId || null,
      technicalManagerUserId: profileForm.technicalManagerUserId || state.config?.technicalManagerUserId || null,
    });
  };
  const createBatch = (event: FormEvent) => {
    event.preventDefault();
    const pdfBlobIds = batchBlobIds.split(',').map((item) => item.trim()).filter(Boolean);
    if (pdfBlobIds.length > 0) {
      batchMutation.mutate({ pdfBlobIds });
    }
  };

  return (
    <RootLayout>
      <PageHeader title={`Onboarding: ${vesselName}`} />
      <div className="space-y-4 p-4">
        <div className="rounded-md border border-neutral-200 bg-white p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-neutral-900">Onboarding: {vesselName}</h1>
              <p className="text-sm text-neutral-600">
                {state.vessel.imo ?? 'No IMO'} - {state.vessel.flag ?? 'No flag'} - {state.vessel.classSociety ?? 'No class'}
              </p>
              <p className="mt-2 text-xs font-medium text-neutral-500">
                Session re-auth preserves step {state.currentStep}
              </p>
            </div>
            {canRollback && state.config?.lifecycleStatus === 'onboarding_in_progress' ? (
              <Dialog>
                <DialogTrigger asChild>
                  <Button type="button" variant="outline" disabled={rollbackMutation.isPending}>
                    <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
                    Reset onboarding
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Reset onboarding for this vessel?</DialogTitle>
                    <DialogDescription>
                      This cancels onboarding batches and marks onboarding-created cert rows and PDFs inactive before FM sign-off.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-2">
                    <Label htmlFor="rollbackReason">Rollback reason</Label>
                    <Textarea
                      id="rollbackReason"
                      value={rollbackReason}
                      onChange={(event) => setRollbackReason(event.target.value)}
                      minLength={20}
                    />
                    {rollbackMutation.error ? <p className="text-sm text-error-700">{getErrorMessage(rollbackMutation.error)}</p> : null}
                  </div>
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button type="button" variant="outline">Cancel</Button>
                    </DialogClose>
                    <Button
                      type="button"
                      variant="destructive"
                      onClick={() => rollbackMutation.mutate(rollbackReason)}
                      disabled={rollbackMutation.isPending || rollbackReason.trim().length < 20}
                    >
                      Confirm reset
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            ) : null}
          </div>
          <div className="mt-4 grid gap-2 md:grid-cols-7">
            {state.steps.map((step) => (
              <Link
                key={step.number}
                to={`${ROUTES.CERTS_ONBOARDING_WIZARD(vesselId)}?step=${step.number}`}
                className={`rounded-md border p-3 text-sm ${step.number === currentStep ? 'border-primary-500 bg-primary-50 text-primary-800' : 'border-neutral-200 bg-white text-neutral-700'}`}
              >
                <div className="font-semibold">Step {step.number}</div>
                <div className="mt-1 text-xs">{step.label}</div>
              </Link>
            ))}
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <div className="space-y-4">
            {currentStep === 1 ? <CertWizardStepCard title="Vessel selection" body="Vessel context is locked for this onboarding session." /> : null}
            {currentStep === 2 ? (
              <Card>
                <CardHeader>
                  <CardTitle>Vessel profile</CardTitle>
                </CardHeader>
                <CardContent>
                  <form className="grid gap-3 md:grid-cols-2" onSubmit={saveProfile}>
                    <div className="space-y-1">
                      <Label htmlFor="onboardingAnniversary">Anniversary date</Label>
                      <Input
                        id="onboardingAnniversary"
                        type="date"
                        value={profileForm.anniversaryDate || state.config?.anniversaryDate || ''}
                        onChange={(event) => setProfileForm((current) => ({ ...current, anniversaryDate: event.target.value }))}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="onboardingShipType">Ship type</Label>
                      <Input
                        id="onboardingShipType"
                        value={profileForm.shipType || state.config?.shipType || ''}
                        onChange={(event) => setProfileForm((current) => ({ ...current, shipType: event.target.value }))}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="onboardingMarine">Marine Supt user ID</Label>
                      <Input
                        id="onboardingMarine"
                        value={profileForm.marineSuptUserId || state.config?.marineSuptUserId || ''}
                        onChange={(event) => setProfileForm((current) => ({ ...current, marineSuptUserId: event.target.value }))}
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="onboardingTech">Technical Manager user ID</Label>
                      <Input
                        id="onboardingTech"
                        value={profileForm.technicalManagerUserId || state.config?.technicalManagerUserId || ''}
                        onChange={(event) => setProfileForm((current) => ({ ...current, technicalManagerUserId: event.target.value }))}
                      />
                    </div>
                    {canCreate ? (
                      <div className="md:col-span-2">
                        <Button type="submit" disabled={profileMutation.isPending}>Save and continue</Button>
                      </div>
                    ) : null}
                  </form>
                </CardContent>
              </Card>
            ) : null}
            {currentStep === 3 ? (
              <Card>
                <CardHeader>
                  <CardTitle>Cert PDF batch ingest</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <form className="flex flex-col gap-2 sm:flex-row" onSubmit={createBatch}>
                    <Input
                      aria-label="PDF blob IDs"
                      placeholder="Existing PDF blob IDs, comma separated"
                      value={batchBlobIds}
                      onChange={(event) => setBatchBlobIds(event.target.value)}
                    />
                    {canCreate ? <Button type="submit" disabled={batchMutation.isPending}>Create batch</Button> : null}
                  </form>
                  <div className="space-y-2">
                    {state.batches.length === 0 ? (
                      <p className="text-sm text-neutral-600">No PDF batches uploaded yet.</p>
                    ) : (
                      state.batches.map((batch) => <CertOnboardingBatchRow key={batch.id} batch={batch} vesselId={vesselId} />)
                    )}
                  </div>
                </CardContent>
              </Card>
            ) : null}
            {currentStep === 4 ? <CertWizardStepCard title="Class status upload" body="Class parser and reconciliation execution remain Phase 4 surfaces; this wizard keeps the gated step visible." /> : null}
            {currentStep === 5 ? <CertWizardStepCard title="Reconciliation review" body="Reconciliation review opens after class snapshot parser output is available." /> : null}
            {currentStep === 6 ? (
              <Card>
                <CardHeader>
                  <CardTitle>Coverage gate</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-neutral-700">
                    Mandatory coverage is {state.mandatoryCoverage.percent}% ({state.mandatoryCoverage.coveredCount}/{state.mandatoryCoverage.mandatoryCount}).
                  </p>
                  {state.mandatoryCoverage.percent < 100 ? (
                    <div className="space-y-2">
                      {(state.mandatoryCoverage.missing?.length ?? 0) > 0 ? (
                        <div className="rounded-md border border-amber-200 bg-amber-50 p-3">
                          <p className="text-sm font-medium text-amber-900">Missing mandatory certs</p>
                          <ul className="mt-2 space-y-1 text-sm text-amber-900">
                            {state.mandatoryCoverage.missing?.map((item) => (
                              <li key={`${item.catalogId ?? item.catalogCode}-${item.trackedItemId ?? 'new'}`}>
                                {item.displayName ?? item.catalogCode ?? 'Mandatory cert'} - {item.reason === 'missing_tracked_item' ? 'not created for this vessel' : 'pending first upload'}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                      <Textarea
                        value={coverageReason}
                        onChange={(event) => setCoverageReason(event.target.value)}
                        placeholder="Coverage override reason"
                      />
                      {canCreate ? (
                        <Button type="button" onClick={() => coverageMutation.mutate(coverageReason)} disabled={coverageMutation.isPending || coverageReason.trim().length < 20}>
                          Save override reason
                        </Button>
                      ) : null}
                    </div>
                  ) : (
                    <Badge variant="success">Ready to enable alerts</Badge>
                  )}
                </CardContent>
              </Card>
            ) : null}
            {currentStep === 7 ? (
              <Card>
                <CardHeader>
                  <CardTitle>FM sign-off</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <CertDetailGrid
                    rows={[
                      ['Vessel', vesselName],
                      ['Coverage', `${state.mandatoryCoverage.percent}%`],
                      ['Batches', String(state.batches.length)],
                      ['Anniversary', formatDate(state.config?.anniversaryDate)],
                    ]}
                  />
                  <Textarea
                    value={actionReason}
                    onChange={(event) => setActionReason(event.target.value)}
                    placeholder="FM sign-off reason"
                  />
                  {canSignoff ? (
                    <Button type="button" onClick={() => signoffMutation.mutate(actionReason || 'FM signed off vessel onboarding.')} disabled={signoffMutation.isPending}>
                      Sign off - vessel goes live
                    </Button>
                  ) : null}
                </CardContent>
              </Card>
            ) : null}
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <CertDetailGrid
                rows={[
                  ['Current step', `Step ${state.currentStep}`],
                  ['Lifecycle', formatStatus(state.config?.lifecycleStatus ?? 'not_onboarded')],
                  ['Coverage', `${state.mandatoryCoverage.percent}%`],
                  ['Tracked rows', String(state.trackedItems.length)],
                  ['Batches uploaded', String(state.batches.length)],
                ]}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </RootLayout>
  );
}

function CertWizardStepCard({ title, body }: { title: string; body: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-neutral-700">{body}</p>
      </CardContent>
    </Card>
  );
}

function CertOnboardingBatchRow({ batch, vesselId }: { batch: CertOnboardingBatch; vesselId: string }) {
  return (
    <div className="flex flex-col gap-3 rounded-md border border-neutral-200 p-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <div className="font-medium text-neutral-900">{formatBatchStatus(batch.status)}</div>
        <div className="text-sm text-neutral-600">
          {batch.pdfCount} PDFs - {formatDateTime(batch.ocrCompletedAt ?? batch.createdAt)}
        </div>
      </div>
      <Button asChild variant="outline" size="sm">
        <Link to={ROUTES.CERTS_ONBOARDING_GAP_FILL(vesselId, batch.id)}>
          Review batch
        </Link>
      </Button>
    </div>
  );
}

function CertOnboardingGapFillPage({ imo, batchId }: { imo: string; batchId: string }) {
  const canRead = useCertsPermission(FORM_IDS.CERTS_ONBOARDING);
  const canPreview = useCertsPermission(FORM_IDS.CERTS_ONBOARDING, PROCESS_IDS.CERTS_CREATE);
  const canCommit = useCertsPermission(FORM_IDS.CERTS_ONBOARDING, PROCESS_IDS.CERTS_SUBMIT);
  const gapFill = useOnboardingBatchGapFill(canRead ? batchId : undefined);
  const previewValidation = usePreviewOnboardingBatch(canRead ? batchId : undefined);
  const commitBatch = useCommitOnboardingBatch(canRead ? batchId : undefined);
  const [warningsAcknowledged, setWarningsAcknowledged] = useState(false);
  const [supersedeAcknowledged, setSupersedeAcknowledged] = useState(false);

  if (!canRead) {
    return <CertsPermissionDenied />;
  }

  if (gapFill.isLoading) {
    return (
      <RootLayout>
        <PageHeader title="Gap-Fill Review" />
        <div className="space-y-3 p-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </RootLayout>
    );
  }

  if (gapFill.isError || !gapFill.data) {
    return (
      <RootLayout>
        <PageHeader title="Gap-Fill Review" />
        <div className="p-4">
          <CertCatalogError message={getErrorMessage(gapFill.error)} onRetry={() => gapFill.refetch()} />
        </div>
      </RootLayout>
    );
  }

  const validationBlocks = gapFill.data.batch.validationBlocks ?? [];
  const validationWarns = gapFill.data.batch.validationWarns ?? [];
  const supersedeBlocks = validationBlocks.filter((entry) => entry.code === 'supersede_confirmation_required');
  const nonSupersedeBlocks = validationBlocks.filter((entry) => entry.code !== 'supersede_confirmation_required');
  const supersedeDecisions = supersedeBlocks
    .filter((entry) => entry.blobId && entry.value)
    .map((entry) => ({
      blobId: String(entry.blobId),
      existingBlobId: String(entry.value),
      confirm: supersedeAcknowledged,
    }));
  const commitDisabled =
    !canCommit ||
    commitBatch.isPending ||
    nonSupersedeBlocks.length > 0 ||
    (supersedeBlocks.length > 0 && !supersedeAcknowledged) ||
    (validationWarns.length > 0 && !warningsAcknowledged);

  return (
    <RootLayout>
      <PageHeader title="Gap-Fill Review" />
      <div className="space-y-4 p-4">
        <div className="flex flex-col gap-3 rounded-md border border-neutral-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-neutral-900">Gap-Fill Review</h1>
            <p className="text-sm text-neutral-600">
              {gapFill.data.vessel.name ?? imo} - batch {gapFill.data.batch.id}
            </p>
          </div>
          <Badge variant="secondary">{formatBatchStatus(gapFill.data.batch.status)}</Badge>
        </div>
        <div className="rounded-md border border-neutral-200 bg-white p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-3">
              <div>
                <h2 className="text-base font-semibold text-neutral-900">D-CERT-116 validation</h2>
                <p className="text-sm text-neutral-600">
                  {validationBlocks.length} blocks, {validationWarns.length} warnings
                </p>
              </div>
              <CertValidationEntries title="D-CERT-116 / D-CERT-118 blocks" entries={validationBlocks} tone="block" />
              <CertValidationEntries title="D-CERT-116 warnings" entries={validationWarns} tone="warn" />
              {supersedeBlocks.length > 0 ? (
                <label className="flex items-start gap-2 text-sm text-neutral-700">
                  <Checkbox
                    checked={supersedeAcknowledged}
                    onCheckedChange={(checked) => setSupersedeAcknowledged(Boolean(checked))}
                  />
                  <span>Confirm these PDFs supersede the existing certificate versions.</span>
                </label>
              ) : null}
              {validationWarns.length > 0 ? (
                <label className="flex items-start gap-2 text-sm text-neutral-700">
                  <Checkbox
                    checked={warningsAcknowledged}
                    onCheckedChange={(checked) => setWarningsAcknowledged(Boolean(checked))}
                  />
                  <span>I acknowledge D-CERT-116 warnings for this batch.</span>
                </label>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                disabled={!canPreview || previewValidation.isPending}
                onClick={() => previewValidation.mutate(undefined)}
              >
                Preview validation
              </Button>
              <Button
                type="button"
                disabled={commitDisabled}
                onClick={() =>
                  commitBatch.mutate({
                    acknowledgeWarnings: warningsAcknowledged,
                    supersedeDecisions: supersedeDecisions.length > 0 ? supersedeDecisions : undefined,
                  })
                }
              >
                Commit batch
              </Button>
            </div>
          </div>
          {previewValidation.error || commitBatch.error ? (
            <div className="mt-3 rounded-md border border-danger-200 bg-danger-50 p-3 text-sm text-danger-800">
              {getErrorMessage(previewValidation.error ?? commitBatch.error)}
            </div>
          ) : null}
        </div>
        <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
          <div className="space-y-2">
            {gapFill.data.pdfs.map((pdf) => (
              <CertGapFillPdfListItem key={pdf.id} pdf={pdf} />
            ))}
          </div>
          <div className="space-y-4">
            {gapFill.data.pdfs.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-sm text-neutral-600">No PDFs are attached to this batch.</CardContent>
              </Card>
            ) : (
              gapFill.data.pdfs.map((pdf) => <CertGapFillPdfPanel key={pdf.id} pdf={pdf} />)
            )}
          </div>
        </div>
      </div>
    </RootLayout>
  );
}

function CertValidationEntries({
  title,
  entries,
  tone,
}: {
  title: string;
  entries: CertValidationEntry[];
  tone: 'block' | 'warn';
}) {
  if (entries.length === 0) {
    return null;
  }
  const className =
    tone === 'block'
      ? 'border-danger-200 bg-danger-50 text-danger-800'
      : 'border-warning-200 bg-warning-50 text-warning-800';
  return (
    <div className={`rounded-md border p-3 text-sm ${className}`}>
      <div className="font-medium">{title}</div>
      <ul className="mt-2 space-y-1">
        {entries.map((entry, index) => (
          <li key={`${entry.code}-${entry.blobId ?? index}`}>
            {entry.message}
            {entry.filename ? <span className="ml-1 text-neutral-600">({entry.filename})</span> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

function CertGapFillPdfListItem({ pdf }: { pdf: CertGapFillPdf }) {
  const incompleteCount = pdf.fieldStates.filter((field) => field.mode === 'manual_entry').length;
  return (
    <div className="rounded-md border border-neutral-200 bg-white p-3 text-sm">
      <div className="font-medium text-neutral-900">{pdf.filename}</div>
      <div className="mt-1 text-neutral-600">{pdf.fieldStates.length} OCR fields</div>
      <Badge variant={incompleteCount ? 'destructive' : 'success'}>{incompleteCount ? 'Incomplete' : 'Ready'}</Badge>
    </div>
  );
}

function CertGapFillPdfPanel({ pdf }: { pdf: CertGapFillPdf }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{pdf.filename}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
        <div className="flex min-h-64 items-center justify-center rounded-md border border-neutral-200 bg-neutral-50 p-4 text-center text-sm text-neutral-600">
          PDF preview metadata only for this phase
        </div>
        <div className="space-y-3">
          {pdf.ocrPayload?.unprocessable ? (
            <div className="rounded-md border border-warning-200 bg-warning-50 p-3 text-sm text-warning-800">
              OCR could not process this PDF. Please enter all fields manually.
            </div>
          ) : null}
          {pdf.fieldStates.length === 0 ? (
            <p className="text-sm text-neutral-600">No OCR fields recorded for this PDF.</p>
          ) : (
            pdf.fieldStates.map((field) => <CertGapFillFieldRow key={field.field} field={field} />)
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function CertGapFillFieldRow({ field }: { field: CertGapFillFieldState }) {
  return (
    <div className={`rounded-md border p-3 text-sm ${confidenceClassName(field.mode)}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="font-medium text-neutral-900">{humanizeKey(field.field)}</div>
          <div className="text-neutral-600">{field.value ?? field.rawValue ?? 'Manual entry required'}</div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={field.mode === 'manual_entry' ? 'destructive' : field.mode === 'gap_fill' ? 'warning' : 'success'}>
            {humanizeKey(field.mode)}
          </Badge>
          <span className="font-medium text-neutral-700">{Math.round((field.confidence ?? 0) * 100)}%</span>
        </div>
      </div>
    </div>
  );
}

function CertStatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-2 py-1 text-xs font-semibold uppercase ${statusClassName(status)}`}>
      <span className={`h-2.5 w-2.5 rounded-full border ${statusShapeClassName(status)}`} aria-hidden="true" />
      {formatStatus(status)}
    </span>
  );
}

function useCanWriteCatalog() {
  const auth = useAuth();
  const hasEditPermission = useCertsPermission(FORM_IDS.CERTS_CATALOG, PROCESS_IDS.CERTS_CATALOG_EDIT);
  const role = String(auth.role ?? auth.user?.role_name ?? auth.user?.safety_role_name ?? '').trim().toUpperCase();
  return hasEditPermission && CATALOG_WRITER_ROLES.has(role);
}

function useCanWriteAuditorAccess() {
  const auth = useAuth();
  const hasProvisionPermission = useCertsPermission(FORM_IDS.CERTS_AUDITOR_ACCESS, PROCESS_IDS.CERTS_PROVISION_AUDITOR);
  const role = String(auth.role ?? auth.user?.role_name ?? auth.user?.safety_role_name ?? '').trim().toUpperCase();
  return hasProvisionPermission && ['DPA', 'MARINE SUPERINTENDENT', "MARINE SUP'TT", 'MARINE SUPT'].includes(role);
}

function useCanBulkActionCatalog() {
  const auth = useAuth();
  const hasBulkPermission = useCertsPermission(FORM_IDS.CERTS_CATALOG, PROCESS_IDS.CERTS_BULK_ACTION);
  const role = String(auth.role ?? auth.user?.role_name ?? auth.user?.safety_role_name ?? '').trim().toUpperCase();
  return hasBulkPermission && CATALOG_WRITER_ROLES.has(role);
}

function CertCatalogLoading() {
  return (
    <RootLayout>
      <PageHeader title="Catalog Admin" />
      <div className="grid gap-4 p-4 lg:grid-cols-[240px_1fr]">
        <Skeleton className="h-96 w-full" />
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-80 w-full" />
        </div>
      </div>
    </RootLayout>
  );
}

function CertCatalogError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <Card className="border-error-200 bg-error-50">
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3 text-error-700">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
          <p className="text-sm font-medium">{message}</p>
        </div>
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
          Retry
        </Button>
      </CardContent>
    </Card>
  );
}

type CatalogSelectOption = {
  value: string;
  label: string;
};

function CertCatalogTextOrSelectField({
  id,
  value,
  onChange,
  options,
  required = false,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly CatalogSelectOption[];
  required?: boolean;
}) {
  if (options.length === 0) {
    return <Input id={id} value={value} onChange={(event) => onChange(event.target.value)} required={required} />;
  }

  const resolvedOptions = includeCurrentCatalogOption(options, value);
  return (
    <Select value={value || undefined} onValueChange={onChange}>
      <SelectTrigger id={id}>
        <SelectValue placeholder="Select" />
      </SelectTrigger>
      <SelectContent>
        {resolvedOptions.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function CertCatalogVesselDropdown({
  id,
  value,
  onChange,
  vessels,
  isLoading,
}: {
  id: string;
  value: string[];
  onChange: (value: string[]) => void;
  vessels: CertFleetDashboardVessel[];
  isLoading: boolean;
}) {
  const selected = new Set(value);
  const sortedVessels = [...vessels].sort((left, right) => (
    formatCatalogVesselName(left).localeCompare(formatCatalogVesselName(right))
  ));
  const toggleVessel = (vesselId: string, checked: boolean) => {
    const next = new Set(selected);
    if (checked) {
      next.add(vesselId);
    } else {
      next.delete(vesselId);
    }
    onChange(Array.from(next));
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          id={id}
          type="button"
          variant="outline"
          className="w-full justify-between bg-white text-left font-normal"
          disabled={isLoading || sortedVessels.length === 0}
        >
          <span className="truncate">{formatSelectedCatalogVessels(value, sortedVessels)}</span>
          <span className="ml-2 text-xs text-neutral-500">{isLoading ? 'Loading' : `${value.length} selected`}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-72 w-[var(--radix-dropdown-menu-trigger-width)] overflow-y-auto border border-neutral-200 bg-white p-1 text-neutral-900 shadow-xl">
        {sortedVessels.length === 0 ? (
          <div className="px-3 py-2 text-sm text-neutral-500">No vessels available</div>
        ) : (
          sortedVessels.map((vessel) => (
            <DropdownMenuCheckboxItem
              key={vessel.id}
              checked={selected.has(vessel.id)}
              onCheckedChange={(checked) => toggleVessel(vessel.id, Boolean(checked))}
              onSelect={(event) => event.preventDefault()}
            >
              {formatCatalogVesselOption(vessel)}
            </DropdownMenuCheckboxItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function CertCatalogCreateForm({
  onCancel,
  parentOptions,
  printSectionLabelOptions,
  vesselOptions,
  vesselsLoading,
  vesselsError,
  inlinePromotion,
}: {
  onCancel: () => void;
  parentOptions: CertCatalogRow[];
  printSectionLabelOptions: CatalogSelectOption[];
  vesselOptions: CertFleetDashboardVessel[];
  vesselsLoading: boolean;
  vesselsError: string | null;
  inlinePromotion?: CertCatalogInlinePromotionContext;
}) {
  const createMutation = useCreateCatalogRow();
  const [canonicalCode, setCanonicalCode] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [shortName, setShortName] = useState('');
  const [sectionId, setSectionId] = useState(2);
  const [printSectionLabel, setPrintSectionLabel] = useState('Statutory & Flag');
  const [validityType, setValidityType] = useState('full');
  const [cadenceMonths, setCadenceMonths] = useState('60');
  const [issuingAuthorityType, setIssuingAuthorityType] = useState('flag');
  const [submissionScope, setSubmissionScope] = useState('all_ranks_with_approval');
  const [parentId, setParentId] = useState('none');
  const [applicableShipTypes, setApplicableShipTypes] = useState<string[]>(['all']);
  const [applicabilityMode, setApplicabilityMode] = useState('all_matching_type');
  const [specificVesselIds, setSpecificVesselIds] = useState<string[]>([]);
  const [isClassTracked, setIsClassTracked] = useState(false);
  const [mandatoryForAllVessels, setMandatoryForAllVessels] = useState(true);
  const [parentSupportsDynamicChildren, setParentSupportsDynamicChildren] = useState(false);
  const [reason, setReason] = useState('');
  const [specificVesselError, setSpecificVesselError] = useState('');

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (applicabilityMode === 'specific_vessel_ids' && specificVesselIds.length === 0) {
      setSpecificVesselError('Select at least one vessel.');
      return;
    }
    setSpecificVesselError('');
    createMutation.mutate(
      {
        canonicalCode,
        displayName,
        shortName: shortName || null,
        sectionId,
        printSectionLabel,
        validityType,
        cadenceMonths: validityType === 'permanent' ? null : parseOptionalCatalogInteger(cadenceMonths),
        issuingAuthorityType,
        isClassTracked,
        submissionScope,
        parentId: parentId === 'none' ? null : parentId,
        applicableShipTypes,
        mandatoryForAllVessels,
        applicabilityMode,
        specificVesselIds: applicabilityMode === 'specific_vessel_ids' ? specificVesselIds : [],
        reason,
        parentSupportsDynamicChildren,
        inlinePromotion,
      },
      { onSuccess: onCancel }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{inlinePromotion ? 'Create Catalog Row From Onboarding' : 'Add Catalog Row'}</CardTitle>
      </CardHeader>
      <CardContent>
        {inlinePromotion ? (
          <div className="mb-4 rounded-md border border-primary-200 bg-primary-50 p-3 text-sm text-primary-800">
            Inline promotion from onboarding gap-fill
          </div>
        ) : null}
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={submit}>
          <div className="space-y-2">
            <Label htmlFor="canonicalCode">Canonical code</Label>
            <Input id="canonicalCode" value={canonicalCode} onChange={(event) => setCanonicalCode(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="sectionId">Section ID</Label>
            <Input id="sectionId" type="number" min={1} max={9} value={sectionId} onChange={(event) => setSectionId(Number(event.target.value))} required />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="displayName">Display name</Label>
            <Input id="displayName" value={displayName} onChange={(event) => setDisplayName(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="shortName">Short name</Label>
            <Input id="shortName" value={shortName} onChange={(event) => setShortName(event.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="printSectionLabel">Print section label</Label>
            <CertCatalogTextOrSelectField
              id="printSectionLabel"
              value={printSectionLabel}
              onChange={setPrintSectionLabel}
              options={printSectionLabelOptions}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="validityType">Validity type</Label>
            <CertCatalogTextOrSelectField
              id="validityType"
              value={validityType}
              onChange={setValidityType}
              options={CATALOG_VALIDITY_TYPE_OPTIONS}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="cadenceMonths">Cadence months</Label>
            <Input
              id="cadenceMonths"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={cadenceMonths}
              onChange={(event) => setCadenceMonths(cleanCatalogIntegerInput(event.target.value))}
              disabled={validityType === 'permanent'}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="issuingAuthorityType">Issuing authority type</Label>
            <CertCatalogTextOrSelectField
              id="issuingAuthorityType"
              value={issuingAuthorityType}
              onChange={setIssuingAuthorityType}
              options={CATALOG_ISSUING_AUTHORITY_TYPE_OPTIONS}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="submissionScope">Submission scope</Label>
            <CertCatalogTextOrSelectField
              id="submissionScope"
              value={submissionScope}
              onChange={setSubmissionScope}
              options={CATALOG_SUBMISSION_SCOPE_OPTIONS}
              required
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="createParentId">Parent row</Label>
            <Select value={parentId} onValueChange={setParentId}>
              <SelectTrigger id="createParentId">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No parent</SelectItem>
                {parentOptions.map((option) => (
                  <SelectItem key={option.id} value={option.id}>{formatParentOption(option)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Applicable ship types</Label>
            <CertShipTypeCheckboxGroup
              idPrefix="createShipType"
              value={applicableShipTypes}
              onChange={setApplicableShipTypes}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="createApplicabilityMode">Applicability mode</Label>
            <Select value={applicabilityMode} onValueChange={setApplicabilityMode}>
              <SelectTrigger id="createApplicabilityMode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {APPLICABILITY_MODE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {applicabilityMode === 'specific_vessel_ids' ? (
            <div className="space-y-2">
              <Label htmlFor="createSpecificVessels">Specific vessels</Label>
              <CertCatalogVesselDropdown
                id="createSpecificVessels"
                value={specificVesselIds}
                onChange={setSpecificVesselIds}
                vessels={vesselOptions}
                isLoading={vesselsLoading}
              />
              <p className="text-xs text-neutral-500">Choose vessel names. The system will use the correct vessel IDs automatically.</p>
              {vesselsError ? <p className="text-xs text-error-700">{vesselsError}</p> : null}
              {specificVesselError ? <p className="text-sm text-error-700">{specificVesselError}</p> : null}
            </div>
          ) : null}
          <label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
            <Checkbox checked={isClassTracked} onCheckedChange={(checked) => setIsClassTracked(Boolean(checked))} />
            Class tracked
          </label>
          <label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
            <Checkbox checked={mandatoryForAllVessels} onCheckedChange={(checked) => setMandatoryForAllVessels(Boolean(checked))} />
            Mandatory for all vessels
          </label>
          <label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
            <Checkbox
              checked={parentSupportsDynamicChildren}
              onCheckedChange={(checked) => setParentSupportsDynamicChildren(Boolean(checked))}
            />
            Dynamic child TrackedItems
          </label>
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="reason">Reason</Label>
            <Input id="reason" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Workshop seed row" />
          </div>
          {createMutation.isError ? (
            <p className="text-sm text-error-700 sm:col-span-2">{getErrorMessage(createMutation.error)}</p>
          ) : null}
          <div className="flex gap-2 sm:col-span-2">
            <Button type="submit" disabled={createMutation.isPending}>
              <Save className="mr-2 h-4 w-4" aria-hidden="true" />
              Save row
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function CertCatalogDetail({
  rowId,
  catalogRows,
  printSectionLabelOptions,
  vesselOptions,
  vesselsLoading,
  vesselsError,
}: {
  rowId: string;
  catalogRows: CertCatalogRow[];
  printSectionLabelOptions: CatalogSelectOption[];
  vesselOptions: CertFleetDashboardVessel[];
  vesselsLoading: boolean;
  vesselsError: string | null;
}) {
  const canWrite = useCanWriteCatalog();
  const { data: row, isLoading, isError, error, refetch } = useCatalogRow(rowId);
  const auditHistory = useCatalogRowAuditHistory(rowId);
  const updateMutation = useUpdateCatalogRow(rowId);
  const deprecateMutation = useDeprecateCatalogRow(rowId);
  const parentOptions = getParentOptions(catalogRows, rowId);
  const parentRow = row?.parentId ? catalogRows.find((candidate) => candidate.id === row.parentId) : undefined;
  const [displayName, setDisplayName] = useState('');
  const [printSectionLabel, setPrintSectionLabel] = useState('');
  const [validityType, setValidityType] = useState('');
  const [cadenceMonths, setCadenceMonths] = useState('');
  const [issuingAuthorityType, setIssuingAuthorityType] = useState('');
  const [submissionScope, setSubmissionScope] = useState('');
  const [parentId, setParentId] = useState('none');
  const [applicableShipTypes, setApplicableShipTypes] = useState<string[]>(['all']);
  const [applicabilityMode, setApplicabilityMode] = useState('all_matching_type');
  const [specificVesselIds, setSpecificVesselIds] = useState<string[]>([]);
  const [isClassTracked, setIsClassTracked] = useState(false);
  const [mandatoryForAllVessels, setMandatoryForAllVessels] = useState(true);
  const [parentSupportsDynamicChildren, setParentSupportsDynamicChildren] = useState(false);
  const [linkedPmsComponentId, setLinkedPmsComponentId] = useState('');
  const [reason, setReason] = useState('');
  const [reasonError, setReasonError] = useState('');
  const [specificVesselError, setSpecificVesselError] = useState('');

  useEffect(() => {
    if (row) {
      setDisplayName(row.displayName);
      setPrintSectionLabel(row.printSectionLabel);
      setValidityType(row.validityType);
      setCadenceMonths(row.cadenceMonths == null ? '' : String(row.cadenceMonths));
      setIssuingAuthorityType(row.issuingAuthorityType);
      setSubmissionScope(row.submissionScope === 'master_only' ? 'all_ranks_with_approval' : row.submissionScope);
      setParentId(row.parentId ?? 'none');
      setApplicableShipTypes(row.applicableShipTypes.length ? row.applicableShipTypes : ['all']);
      setApplicabilityMode(row.applicabilityMode || 'all_matching_type');
      setSpecificVesselIds(row.specificVesselIds);
      setIsClassTracked(row.isClassTracked);
      setMandatoryForAllVessels(row.mandatoryForAllVessels);
      setParentSupportsDynamicChildren(row.parentSupportsDynamicChildren);
      setLinkedPmsComponentId(row.linkedPmsComponentId ?? '');
    }
  }, [row]);

  if (isLoading) {
    return <Skeleton className="h-72 w-full" />;
  }

  if (isError) {
    return <CertCatalogError message={`Could not load catalog row. ${getErrorMessage(error)}`} onRetry={() => refetch()} />;
  }

  if (!row) {
    return null;
  }

  const save = (event: FormEvent) => {
    event.preventDefault();
    setReasonError('');
    if (applicabilityMode === 'specific_vessel_ids' && specificVesselIds.length === 0) {
      setSpecificVesselError('Select at least one vessel.');
      return;
    }
    setSpecificVesselError('');
    updateMutation.mutate({
      displayName,
      printSectionLabel,
      validityType,
      cadenceMonths: validityType === 'permanent' ? null : parseOptionalCatalogInteger(cadenceMonths),
      issuingAuthorityType,
      isClassTracked,
      submissionScope,
      parentId: parentId === 'none' ? null : parentId,
      applicableShipTypes,
      mandatoryForAllVessels,
      parentSupportsDynamicChildren,
      linkedPmsComponentId: linkedPmsComponentId || null,
      applicabilityMode,
      specificVesselIds: applicabilityMode === 'specific_vessel_ids' ? specificVesselIds : [],
      reason,
    });
  };

  const deprecate = () => {
    const trimmedReason = reason.trim();
    if (!trimmedReason) {
      setReasonError('Deprecation reason is required.');
      return;
    }
    setReasonError('');
    deprecateMutation.mutate({ reason: trimmedReason });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{row.canonicalCode}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <p className="text-neutral-500">Section</p>
            <p className="font-medium text-neutral-900">{row.sectionName}</p>
          </div>
          <div>
            <p className="text-neutral-500">Validity</p>
            <p className="font-medium text-neutral-900">{row.validityType}</p>
          </div>
          <div>
            <p className="text-neutral-500">Updated</p>
            <p className="font-medium text-neutral-900">{formatDate(row.updatedAt)}</p>
          </div>
          <div>
            <p className="text-neutral-500">Parent</p>
            <p className="font-medium text-neutral-900">{parentRow ? parentRow.canonicalCode : 'No parent'}</p>
          </div>
          <div>
            <p className="text-neutral-500">Catalog behavior</p>
            <div className="mt-1 flex flex-wrap gap-2">
              {row.parentSupportsDynamicChildren ? <Badge variant="info">Dynamic instances</Badge> : null}
              {isRollupCatalogRow(row) ? <Badge variant="secondary">Roll-up service row</Badge> : null}
              {!row.parentSupportsDynamicChildren && !isRollupCatalogRow(row) ? (
                <span className="font-medium text-neutral-900">Standard row</span>
              ) : null}
            </div>
          </div>
        </div>
        {canWrite ? (
          <form className="grid gap-3" onSubmit={save}>
            <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="detailDisplayName">Display name</Label>
              <Input id="detailDisplayName" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailPrintSectionLabel">Print section label</Label>
              <CertCatalogTextOrSelectField
                id="detailPrintSectionLabel"
                value={printSectionLabel}
                onChange={setPrintSectionLabel}
                options={printSectionLabelOptions}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailValidityType">Validity type</Label>
              <CertCatalogTextOrSelectField
                id="detailValidityType"
                value={validityType}
                onChange={setValidityType}
                options={CATALOG_VALIDITY_TYPE_OPTIONS}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailCadenceMonths">Cadence months</Label>
              <Input
                id="detailCadenceMonths"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={cadenceMonths}
                onChange={(event) => setCadenceMonths(cleanCatalogIntegerInput(event.target.value))}
                disabled={validityType === 'permanent'}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailIssuingAuthorityType">Issuing authority type</Label>
              <CertCatalogTextOrSelectField
                id="detailIssuingAuthorityType"
                value={issuingAuthorityType}
                onChange={setIssuingAuthorityType}
                options={CATALOG_ISSUING_AUTHORITY_TYPE_OPTIONS}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailSubmissionScope">Submission scope</Label>
              <CertCatalogTextOrSelectField
                id="detailSubmissionScope"
                value={submissionScope}
                onChange={setSubmissionScope}
                options={CATALOG_SUBMISSION_SCOPE_OPTIONS}
              />
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="detailParentId">Parent row</Label>
              <Select value={parentId} onValueChange={setParentId}>
                <SelectTrigger id="detailParentId">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No parent</SelectItem>
                  {parentOptions.map((option) => (
                    <SelectItem key={option.id} value={option.id}>{formatParentOption(option)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Applicable ship types</Label>
              <CertShipTypeCheckboxGroup
                idPrefix="detailShipType"
                value={applicableShipTypes}
                onChange={setApplicableShipTypes}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailApplicabilityMode">Applicability mode</Label>
              <Select value={applicabilityMode} onValueChange={setApplicabilityMode}>
                <SelectTrigger id="detailApplicabilityMode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {APPLICABILITY_MODE_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {applicabilityMode === 'specific_vessel_ids' ? (
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="detailSpecificVessels">Specific vessels</Label>
                <CertCatalogVesselDropdown
                  id="detailSpecificVessels"
                  value={specificVesselIds}
                  onChange={setSpecificVesselIds}
                  vessels={vesselOptions}
                  isLoading={vesselsLoading}
                />
                <p className="text-xs text-neutral-500">Choose vessel names. The system will use the correct vessel IDs automatically.</p>
                {vesselsError ? <p className="text-xs text-error-700">{vesselsError}</p> : null}
                {specificVesselError ? <p className="text-sm text-error-700">{specificVesselError}</p> : null}
              </div>
            ) : null}
            <label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
              <Checkbox checked={isClassTracked} onCheckedChange={(checked) => setIsClassTracked(Boolean(checked))} />
              Class tracked
            </label>
            <label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
              <Checkbox checked={mandatoryForAllVessels} onCheckedChange={(checked) => setMandatoryForAllVessels(Boolean(checked))} />
              Mandatory for all vessels
            </label>
            <label className="flex items-center gap-2 text-sm font-medium text-neutral-700">
              <Checkbox
                checked={parentSupportsDynamicChildren}
                onCheckedChange={(checked) => setParentSupportsDynamicChildren(Boolean(checked))}
              />
              Dynamic child TrackedItems
            </label>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="detailLinkedPmsComponentId">PMS component ID</Label>
              <Input
                id="detailLinkedPmsComponentId"
                value={linkedPmsComponentId}
                onChange={(event) => setLinkedPmsComponentId(event.target.value)}
                title="Cross-module integration deferred - value stored only"
              />
              <p className="text-xs text-neutral-500">
                Cross-module integration deferred - value stored only
              </p>
            </div>
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="detailReason">Reason</Label>
              <Input id="detailReason" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Catalog metadata correction" />
              {reasonError ? <p className="text-sm text-error-700">{reasonError}</p> : null}
            </div>
            </div>
            {updateMutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(updateMutation.error)}</p> : null}
            {deprecateMutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(deprecateMutation.error)}</p> : null}
            <div className="flex flex-wrap gap-2">
              <Button type="submit" className="w-fit" disabled={updateMutation.isPending}>
                <Save className="mr-2 h-4 w-4" aria-hidden="true" />
                Save changes
              </Button>
              {row.isActive ? (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button type="button" variant="destructive" disabled={deprecateMutation.isPending}>
                      <ArchiveX className="mr-2 h-4 w-4" aria-hidden="true" />
                      Deprecate row
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Deprecate catalog row?</DialogTitle>
                      <DialogDescription>
                        This marks the row inactive and blocks future TrackedItem creation for this catalog row. Existing instances remain queryable and printable.
                      </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button type="button" variant="outline">Cancel</Button>
                      </DialogClose>
                      <Button type="button" variant="destructive" onClick={deprecate} disabled={deprecateMutation.isPending}>
                        Deprecate row
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              ) : null}
            </div>
          </form>
        ) : null}
        <section className="space-y-3 rounded-md border border-neutral-200 bg-neutral-50 p-4">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-neutral-500" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-neutral-900">Audit history</h2>
          </div>
          {auditHistory.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : auditHistory.isError ? (
            <CertCatalogError
              message={`Could not load audit history. ${getErrorMessage(auditHistory.error)}`}
              onRetry={() => auditHistory.refetch()}
            />
          ) : auditHistory.data && auditHistory.data.length > 0 ? (
            <ol className="space-y-2">
              {auditHistory.data.map((entry) => (
                <li key={entry.id} className="rounded-md border border-neutral-200 bg-white p-3 text-sm">
                  <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <p className="font-medium text-neutral-900">{formatAuditAction(entry.action)}</p>
                    <p className="text-xs text-neutral-500">{formatDateTime(entry.timestampUtc)}</p>
                  </div>
                  <p className="mt-1 text-neutral-600">
                    {formatPrincipalLabel(undefined, entry.actorUserId, entry.actorRole)}
                  </p>
                  {entry.reason ? <p className="mt-1 text-neutral-700">{entry.reason}</p> : null}
                  <p className="mt-1 text-xs text-neutral-500">{summarizeAuditDiff(entry)}</p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-neutral-600">No catalog audit entries yet.</p>
          )}
        </section>
      </CardContent>
    </Card>
  );
}

function CertCatalogTable({
  rows,
  canSelect = false,
  selectedIds = new Set<string>(),
  onToggleRow,
}: {
  rows: CertCatalogRow[];
  canSelect?: boolean;
  selectedIds?: Set<string>;
  onToggleRow?: (rowId: string, selected: boolean) => void;
}) {
  const navigate = useNavigate();
  const parentLookup = new Map(rows.map((row) => [row.id, row]));
  const orderedRows = orderRowsForHierarchy(rows);
  return (
    <div className="overflow-x-auto rounded-md border border-neutral-200 bg-white">
      <table className="min-w-full divide-y divide-neutral-200 text-sm">
        <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
          <tr>
            {canSelect ? <th className="w-12 px-3 py-3">Select</th> : null}
            <th className="px-3 py-3">Code</th>
            <th className="px-3 py-3">Name</th>
            <th className="px-3 py-3">Validity</th>
            <th className="px-3 py-3">Ship types</th>
            <th className="px-3 py-3">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-100">
          {orderedRows.map((row) => {
            const parent = row.parentId ? parentLookup.get(row.parentId) : undefined;
            return (
            <tr key={row.id} className="cursor-pointer hover:bg-neutral-50" onClick={() => navigate(ROUTES.CERTS_CATALOG_DETAIL(row.id))}>
              {canSelect ? (
                <td className="px-3 py-3" onClick={(event) => event.stopPropagation()}>
                  <Checkbox
                    id={`select-catalog-row-${row.id}`}
                    aria-label={`Select ${row.canonicalCode}`}
                    checked={selectedIds.has(row.id)}
                    onCheckedChange={(checked) => onToggleRow?.(row.id, Boolean(checked))}
                  />
                </td>
              ) : null}
              <td className="whitespace-nowrap px-3 py-3 font-medium text-neutral-900">
                <div className={row.parentId ? 'flex items-center gap-2 pl-5' : ''}>
                  {row.parentId ? <CornerDownRight className="h-4 w-4 text-neutral-400" aria-hidden="true" /> : null}
                  <span>{row.canonicalCode}</span>
                </div>
              </td>
              <td className="min-w-72 px-3 py-3 text-neutral-700">
                <div className={row.parentId ? 'space-y-1 pl-5' : 'space-y-1'}>
                  <p>{row.displayName}</p>
                  {parent ? (
                    <p className="text-xs text-neutral-500">Child of {parent.canonicalCode}</p>
                  ) : null}
                  <div className="flex flex-wrap gap-1">
                    {row.parentSupportsDynamicChildren ? <Badge variant="info">Dynamic instances</Badge> : null}
                    {isRollupCatalogRow(row) ? <Badge variant="secondary">Roll-up service row</Badge> : null}
                  </div>
                </div>
              </td>
              <td className="whitespace-nowrap px-3 py-3 text-neutral-700">{row.validityType}</td>
              <td className="min-w-40 px-3 py-3 text-neutral-700">{formatShipTypes(row.applicableShipTypes)}</td>
              <td className="whitespace-nowrap px-3 py-3">
                <Badge variant={row.isActive ? 'success' : 'secondary'}>{row.isActive ? 'Active' : 'Inactive'}</Badge>
              </td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function CertCatalogAdminPage({ rowId }: { rowId?: string }) {
  const location = useLocation();
  const canReadCatalog = useCertsPermission(FORM_IDS.CERTS_CATALOG);
  const canWriteCatalog = useCanWriteCatalog();
  const canBulkActionCatalog = useCanBulkActionCatalog();
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null);
  const [filter, setFilter] = useState('');
  const [applicableShipTypeFilter, setApplicableShipTypeFilter] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [selectedBulkIds, setSelectedBulkIds] = useState<Set<string>>(new Set());
  const [bulkReason, setBulkReason] = useState('');
  const [bulkReasonError, setBulkReasonError] = useState('');
  const inlinePromotion = getInlinePromotionContext(location.search);
  const sections = useCatalogSections();
  const rows = useCatalogRowsLazy({
    sectionId: selectedSectionId,
    isActive: true,
    q: filter,
    applicableShipType: applicableShipTypeFilter || null,
  }, 50);
  const vesselDashboard = useFleetDashboard(canReadCatalog);
  const bulkSoftDeleteMutation = useBulkSoftDeleteCatalogRows();
  const {
    dataUpdatedAt: catalogRowsDataUpdatedAt,
    fetchNextPage: fetchNextCatalogRowsPage,
    hasNextPage: hasNextCatalogRowsPage,
    isFetchingNextPage: isFetchingNextCatalogRowsPage,
    isLoading: isCatalogRowsLoading,
  } = rows;
  const loadedCatalogRows = rows.data?.pages.flatMap((page) => page.results) ?? [];
  const catalogTotalCount = rows.data?.pages[0]?.count ?? 0;
  const catalogVesselOptions = vesselDashboard.data?.onboardedVessels ?? [];
  const catalogVesselsError = vesselDashboard.isError
    ? `Could not load vessels. ${getErrorMessage(vesselDashboard.error)}`
    : null;
  const printSectionLabelOptions = getCatalogPrintSectionLabelOptions(loadedCatalogRows, sections.data ?? []);

  useEffect(() => {
    if (!hasNextCatalogRowsPage || isFetchingNextCatalogRowsPage || isCatalogRowsLoading) {
      return undefined;
    }
    const timer = window.setTimeout(() => {
      void fetchNextCatalogRowsPage();
    }, 150);
    return () => window.clearTimeout(timer);
  }, [catalogRowsDataUpdatedAt, fetchNextCatalogRowsPage, hasNextCatalogRowsPage, isFetchingNextCatalogRowsPage, isCatalogRowsLoading]);

  const toggleBulkRow = (rowId: string, selected: boolean) => {
    setSelectedBulkIds((current) => {
      const next = new Set(current);
      if (selected) {
        next.add(rowId);
      } else {
        next.delete(rowId);
      }
      return next;
    });
  };

  const submitBulkSoftDelete = () => {
    const reason = bulkReason.trim();
    if (selectedBulkIds.size === 0) {
      setBulkReasonError('Select at least one catalog row.');
      return;
    }
    if (selectedBulkIds.size > 50) {
      setBulkReasonError('Bulk soft-delete is capped at 50 rows per batch.');
      return;
    }
    if (reason.length < 10) {
      setBulkReasonError('Reason must be at least 10 characters.');
      return;
    }
    setBulkReasonError('');
    bulkSoftDeleteMutation.mutate(
      {
        catalogIds: Array.from(selectedBulkIds),
        reason,
      },
      {
        onSuccess: () => {
          setSelectedBulkIds(new Set());
          setBulkReason('');
        },
      }
    );
  };

  if (!canReadCatalog) {
    return <CertsPermissionDenied />;
  }

  if (sections.isLoading || isCatalogRowsLoading) {
    return <CertCatalogLoading />;
  }

  const combinedError = sections.error ?? rows.error;

  return (
    <RootLayout>
      <PageHeader title="Catalog Admin" />
      <div className="space-y-4 p-4">
        {combinedError ? (
          <CertCatalogError
            message={`Could not load catalog. ${getErrorMessage(combinedError)}`}
            onRetry={() => {
              sections.refetch();
              rows.refetch();
            }}
          />
        ) : null}
        <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
          <aside className="rounded-md border border-neutral-200 bg-white p-3">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-neutral-700">
              <ListFilter className="h-4 w-4" aria-hidden="true" />
              Sections
            </div>
            <div className="space-y-1">
              <button
                className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedSectionId === null ? 'bg-primary-50 text-primary-700' : 'text-neutral-700 hover:bg-neutral-50'}`}
                onClick={() => setSelectedSectionId(null)}
              >
                All sections
              </button>
              {(sections.data ?? []).map((section) => (
                <button
                  key={section.sectionId}
                  className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm ${selectedSectionId === section.sectionId ? 'bg-primary-50 text-primary-700' : 'text-neutral-700 hover:bg-neutral-50'}`}
                  onClick={() => setSelectedSectionId(section.sectionId)}
                >
                  <span>{section.displayName}</span>
                  <span className="text-xs text-neutral-500">{section.activeRowCount}</span>
                </button>
              ))}
            </div>
          </aside>
          <main className="space-y-4">
            <Card>
              <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-end md:justify-between">
                <div className="w-full max-w-md space-y-2">
                  <Label htmlFor="catalogFilter">Filter catalog</Label>
                  <Input id="catalogFilter" value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Code or display name" />
                </div>
                <div className="w-full max-w-xs space-y-2">
                  <Label htmlFor="catalogShipTypeFilter">Ship type</Label>
                  <Select value={applicableShipTypeFilter || 'all'} onValueChange={(value) => setApplicableShipTypeFilter(value === 'all' ? '' : value)}>
                    <SelectTrigger id="catalogShipTypeFilter">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All ship types</SelectItem>
                      {SPECIFIC_SHIP_TYPE_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {canWriteCatalog || canBulkActionCatalog ? (
                  <div className="flex flex-wrap gap-2">
                    {canBulkActionCatalog ? (
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button type="button" variant="outline" disabled={selectedBulkIds.size === 0 || bulkSoftDeleteMutation.isPending}>
                            <ArchiveX className="mr-2 h-4 w-4" aria-hidden="true" />
                            Bulk soft-delete
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Bulk soft-delete catalog rows?</DialogTitle>
                            <DialogDescription>
                              This marks selected catalog rows inactive. The batch is capped at 50 rows and requires an audit reason.
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-2">
                            <Label htmlFor="bulkSoftDeleteReason">Bulk soft-delete reason</Label>
                            <Textarea
                              id="bulkSoftDeleteReason"
                              value={bulkReason}
                              onChange={(event) => setBulkReason(event.target.value)}
                              minLength={10}
                            />
                            {bulkReasonError ? <p className="text-sm text-error-700">{bulkReasonError}</p> : null}
                            {bulkSoftDeleteMutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(bulkSoftDeleteMutation.error)}</p> : null}
                          </div>
                          <DialogFooter>
                            <DialogClose asChild>
                              <Button type="button" variant="outline">Cancel</Button>
                            </DialogClose>
                            <Button type="button" variant="destructive" onClick={submitBulkSoftDelete} disabled={bulkSoftDeleteMutation.isPending}>
                              Confirm bulk soft-delete
                            </Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    ) : null}
                    {canWriteCatalog ? (
                      <Button onClick={() => setIsCreating(true)}>
                        <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
                        Add row
                      </Button>
                    ) : null}
                  </div>
                ) : null}
              </CardContent>
            </Card>
            {isCreating ? (
              <CertCatalogCreateForm
                onCancel={() => setIsCreating(false)}
                parentOptions={getParentOptions(loadedCatalogRows)}
                printSectionLabelOptions={printSectionLabelOptions}
                vesselOptions={catalogVesselOptions}
                vesselsLoading={vesselDashboard.isLoading}
                vesselsError={catalogVesselsError}
                inlinePromotion={inlinePromotion}
              />
            ) : null}
            {rowId ? (
              <CertCatalogDetail
                rowId={rowId}
                catalogRows={loadedCatalogRows}
                printSectionLabelOptions={printSectionLabelOptions}
                vesselOptions={catalogVesselOptions}
                vesselsLoading={vesselDashboard.isLoading}
                vesselsError={catalogVesselsError}
              />
            ) : null}
            {loadedCatalogRows.length > 0 ? (
              <div className="space-y-2">
                <CertCatalogTable
                  rows={loadedCatalogRows}
                  canSelect={canBulkActionCatalog}
                  selectedIds={selectedBulkIds}
                  onToggleRow={toggleBulkRow}
                />
                {rows.isFetchingNextPage ? (
                  <p className="text-sm text-neutral-500">
                    Loading more catalog rows... {loadedCatalogRows.length} of {catalogTotalCount}
                  </p>
                ) : null}
              </div>
            ) : (
              <Card>
                <CardContent className="p-6 text-center text-sm text-neutral-600">
                  No catalog rows match your filter.
                  <Button
                    variant="link"
                    className="ml-2 h-auto p-0"
                    onClick={() => {
                      setFilter('');
                      setApplicableShipTypeFilter('');
                    }}
                  >
                    Reset
                  </Button>
                </CardContent>
              </Card>
            )}
          </main>
        </div>
      </div>
    </RootLayout>
  );
}

function getReconciliationExceptionCount(run: CertReconciliationRun): number {
  const flags = (run as Partial<CertReconciliationRunDetail>).flags;
  const conditionCount = Array.isArray(flags)
    ? flags.filter((flag) => flag.bucket === 'conditions_of_class').length
    : 0;
  return (
    (run.mismatchesCount ?? 0)
    + (run.missingInCatalogCount ?? 0)
    + (run.missingInClassCount ?? 0)
    + (run.conditionalStcDetectedCount ?? 0)
    + (run.extendedPostponedDetectedCount ?? 0)
    + (run.unmappedLowConfidenceCount ?? 0)
    + conditionCount
  );
}

function getVisibleReconciliationBucketTabs(run: CertReconciliationRunDetail): typeof RECONCILIATION_BUCKET_TABS {
  return RECONCILIATION_BUCKET_TABS.filter((tab) => {
    if (!RECONCILIATION_HIDE_WHEN_EMPTY_BUCKETS.has(tab.bucket)) {
      return true;
    }
    return getReconciliationBucketCount(run, tab) > 0;
  }) as typeof RECONCILIATION_BUCKET_TABS;
}

function getReconciliationBucketCount(
  run: CertReconciliationRunDetail,
  tab: (typeof RECONCILIATION_BUCKET_TABS)[number]
): number {
  if (tab.countKey) {
    return Number(run[tab.countKey] ?? 0);
  }
  return run.flags.filter((flag) => flag.bucket === tab.bucket).length;
}

function formatReconciliationFindingSummary(run: CertReconciliationRun): string {
  const parts = [
    ['mismatch', run.mismatchesCount ?? 0],
    ['missing catalog', run.missingInCatalogCount ?? 0],
    ['missing class', run.missingInClassCount ?? 0],
    ['conditional', run.conditionalStcDetectedCount ?? 0],
    ['extended', run.extendedPostponedDetectedCount ?? 0],
    ['low confidence', run.unmappedLowConfidenceCount ?? 0],
  ]
    .filter(([, count]) => Number(count) > 0)
    .map(([label, count]) => `${count} ${label}`);
  return parts.length ? parts.join(', ') : 'No findings';
}

function normalizeRecord(value: unknown): Record<string, unknown> | null {
  if (!value || Array.isArray(value) || typeof value !== 'object') return null;
  return value as Record<string, unknown>;
}

function formatReconciliationDiffValue(value: unknown, side: 'vims' | 'class'): string {
  const diff = normalizeRecord(value);
  if (!diff) {
    return formatReadableReviewValue(value);
  }
  const keys = side === 'vims'
    ? ['tracked', 'catalog', 'vims', 'record']
    : ['class', 'snapshot', 'report'];
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(diff, key)) {
      return formatReadableReviewValue(diff[key]);
    }
  }
  return formatReadableReviewValue(diff);
}

function formatReadableReviewValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => formatReadableReviewValue(item)).join(', ') : 'not set';
  }
  const record = normalizeRecord(value);
  if (record) {
    const parts = Object.entries(record)
      .filter(([, entryValue]) => hasDisplayValue(entryValue))
      .map(([key, entryValue]) => `${humanizeKey(key)}: ${formatReadableReviewValue(entryValue)}`);
    return parts.length ? parts.join('; ') : 'not set';
  }
  return formatUnknown(value);
}

function formatReconciliationBucketLabel(bucket: string | null | undefined): string {
  return RECONCILIATION_BUCKET_TABS.find((tab) => tab.bucket === bucket)?.label ?? formatStatus(bucket);
}

function formatClassReportItemTitle(flag: CertReconciliationFlag): string {
  const extract = normalizeRecord(flag.classRowExtract);
  const displayName = cleanDisplayValue(extract?.display_name ?? extract?.displayName ?? extract?.name);
  const code = cleanDisplayValue(extract?.class_code_or_name ?? extract?.classCodeOrName ?? extract?.class_code);
  if (flag.bucket === 'conditions_of_class') return displayName || 'Condition of class';
  if (displayName && code && !displayName.includes(code)) return `${displayName} (${code})`;
  return displayName || code || flag.catalogDisplayName || 'Class report item';
}

function getClassReportReviewFields(flag: CertReconciliationFlag): Array<{ label: string; value: unknown }> {
  const extract = normalizeRecord(flag.classRowExtract);
  if (!extract) return [];
  return [
    { label: 'Summary', value: extract.raw_text ?? extract.rawText },
    { label: 'Due date', value: extract.due_date ?? extract.dueDate },
  ].filter((field) => hasDisplayValue(field.value));
}

function formatMasterMessageTitle(message: CertMasterReconciliationMessage): string {
  const extract = normalizeRecord(message.classRowExtract);
  const displayName = cleanDisplayValue(extract?.display_name ?? extract?.displayName ?? extract?.name);
  const code = cleanDisplayValue(extract?.class_code_or_name ?? extract?.classCodeOrName ?? extract?.class_code);
  if (message.bucket === 'conditions_of_class') return displayName || 'Condition of class';
  if (displayName && code && !displayName.includes(code)) return `${displayName} (${code})`;
  return displayName || code || message.catalogDisplayName || 'Class status item';
}

function getMasterMessageClassFields(message: CertMasterReconciliationMessage): Array<{ label: string; value: unknown }> {
  const extract = normalizeRecord(message.classRowExtract);
  if (!extract) return [];
  return [
    { label: 'Summary', value: extract.raw_text ?? extract.rawText },
    { label: 'Due date', value: extract.due_date ?? extract.dueDate },
  ].filter((field) => hasDisplayValue(field.value));
}

function cleanDisplayValue(value: unknown): string {
  return String(value ?? '').trim();
}

function hasDisplayValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  return true;
}

function formatReviewAlert(breach: CertReconciliationAnomalyBreach): string {
  if (typeof breach.count === 'number' && typeof breach.total === 'number' && breach.total > 0) {
    return `${breach.count} of ${breach.total} class report items need attention (${formatPercent(breach.value)}). Review the items below.`;
  }
  if (breach.type === 'parse_duration') {
    return 'This check took longer than usual. You can continue reviewing the results.';
  }
  if (breach.type === 'parsed_row_count_shortfall') {
    return 'The class report had fewer readable items than expected. Review the results before taking action.';
  }
  return 'This class report needs attention. Review the items below.';
}

function formatAnomalyBreach(breach: CertReconciliationAnomalyBreach): string {
  const message = breach.message ?? formatStatus(breach.type);
  if (breach.type === 'parse_duration') {
    return `${message} ${formatDurationSeconds(breach.valueSeconds)} measured, threshold ${formatDurationSeconds(breach.thresholdSeconds)}.`;
  }
  if (breach.type === 'parsed_row_count_shortfall') {
    return `${message} ${breach.actual ?? 0} parsed rows vs minimum ${breach.expectedMinimum ?? 'n/a'} from ${breach.expectedClassTrackedRows ?? 0} class-tracked rows.`;
  }
  if (typeof breach.value === 'number' && typeof breach.threshold === 'number') {
    return `${message} ${formatPercent(breach.value)} measured, threshold ${formatPercent(breach.threshold)} (${breach.count ?? 0}/${breach.total ?? 0} rows).`;
  }
  return message;
}

function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
  return `${(value * 100).toFixed(1)}%`;
}

function formatDurationSeconds(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
  if (value < 60) return `${value}s`;
  const minutes = Math.floor(value / 60);
  const seconds = value % 60;
  return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`;
}

function getSnapshotParseDurationSeconds(snapshot: CertClassSnapshot): number | null {
  if (!snapshot.parseStartedAt || !snapshot.parseCompletedAt) return null;
  const started = new Date(snapshot.parseStartedAt);
  const completed = new Date(snapshot.parseCompletedAt);
  if (Number.isNaN(started.getTime()) || Number.isNaN(completed.getTime())) return null;
  return Math.max(Math.round((completed.getTime() - started.getTime()) / 1000), 0);
}

function formatDate(value: string | null | undefined): string {
  if (!value) return 'Not set';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

function todayInputValue(): string {
  return new Date().toISOString().slice(0, 10);
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) return 'Not set';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getHeartbeatAgeMinutes(value: string | null | undefined): number | null {
  if (!value) return null;
  const heartbeat = new Date(value);
  if (Number.isNaN(heartbeat.getTime())) return null;
  return Math.max(Math.floor((Date.now() - heartbeat.getTime()) / 60000), 0);
}

function formatHeartbeatAge(ageMinutes: number): string {
  if (ageMinutes < 60) return `${ageMinutes} min`;
  const hours = Math.floor(ageMinutes / 60);
  const minutes = ageMinutes % 60;
  return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
}

function formatBytes(value: number | null | undefined): string {
  if (!value || value < 0) return 'Size not recorded';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatUnknown(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'not set';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  return JSON.stringify(value);
}

function formatExpiry(item: CertTrackedItem): string {
  if (!item.expiryDate && item.validityType === 'permanent') {
    return 'Permanent';
  }
  return formatDate(item.expiryDate);
}

function formatCertificateValidity(item: CertTrackedItem): string {
  if (item.validityShortCode) {
    return formatValidityShortCode(item.validityShortCode);
  }
  if (item.validityType === 'permanent') {
    return 'Permanent';
  }
  if (item.validityType === 'conditional') {
    return 'Survey based';
  }
  if (item.validityType === 'full') {
    return 'Fixed expiry';
  }
  return item.validityType ? formatStatus(item.validityType) : 'n/a';
}

function formatValidityShortCode(value: string): string {
  const normalized = value.trim().toUpperCase().replace(/\s+/g, '');
  const labels: Record<string, string> = {
    A: 'Annual',
    'BI-A': 'Bi-annual',
    '5-Y': '5 years',
    '10-Y': '10 years',
    PERM: 'Permanent',
    'PERM.': 'Permanent',
    ST: 'Short term',
    '6-MTH': '6 months',
    '6MTH': '6 months',
  };
  return labels[normalized] ?? value;
}

function formatShipType(value: string | null | undefined): string {
  if (!value) return 'Ship type not set';
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatSnapshotAge(snapshot: CertVesselDashboardResponse['lastClassSnapshot']): string {
  if (!snapshot) return 'No class snapshot uploaded';
  if (snapshot.daysAgo === 0) return 'Report dated today';
  if (snapshot.daysAgo === 1) return 'Report dated 1 day ago';
  if (typeof snapshot.daysAgo === 'number') return `Report dated ${snapshot.daysAgo} days ago`;
  if (snapshot.printedOnDate) return `Report dated ${formatDate(snapshot.printedOnDate)}`;
  return 'Report date not set';
}

function formatClassSnapshotUploadResult(snapshot: CertClassSnapshot): string {
  if (snapshot.parseStatus === 'success' && snapshot.reconciliationRunId) {
    return 'Snapshot uploaded, parsed, and reconciled.';
  }
  if (snapshot.parseStatus === 'partial' && snapshot.reconciliationRunId) {
    return 'Snapshot uploaded with partial parser output; reconciliation is ready for review.';
  }
  if (snapshot.parseStatus === 'failed') {
    return formatClassSnapshotParseFailure(snapshot);
  }
  return 'Snapshot uploaded. Parser is pending.';
}

function formatClassSnapshotParseFailure(snapshot: CertClassSnapshot): string {
  const failureReason = getClassSnapshotParseFailureReason(snapshot);
  if (failureReason?.includes('OCR fallback read no text')) {
    return 'Snapshot uploaded, but neither text extraction nor OCR could read usable class-status data from this PDF. Upload the official Class Status PDF exported from NK, KR, or BV, then retry.';
  }
  if (failureReason?.includes('printed/generated date')) {
    return 'Snapshot uploaded, but the report date could not be read. Enter the Printed on or Generated on date shown in the PDF, then upload again.';
  }
  return 'Snapshot uploaded, but the parser could not read this PDF. Check the snapshot row and try Reparse after correcting the file.';
}

function getClassSnapshotParseFailureReason(snapshot: CertClassSnapshot): string | null {
  const payload = snapshot.parsedPayload;
  if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
    return null;
  }
  const rows = (payload as { unmapped_rows?: unknown }).unmapped_rows;
  if (!Array.isArray(rows)) {
    return null;
  }
  for (const row of rows) {
    if (row && typeof row === 'object' && 'error' in row) {
      const error = String((row as { error?: unknown }).error ?? '').trim();
      if (error) {
        return error;
      }
    }
  }
  return null;
}

function formatClassSnapshotVesselOption(vessel: CertFleetDashboardVessel): string {
  const name = String(vessel.name ?? '').trim();
  const code = String(vessel.code ?? '').trim();
  const imo = String(vessel.imo ?? '').trim();
  const baseLabel = name || code || (imo ? `IMO ${imo}` : formatEntityLabel(vessel.id, 'Vessel'));
  const details = [
    code && code !== baseLabel ? code : null,
    imo && baseLabel !== `IMO ${imo}` ? `IMO ${imo}` : null,
  ].filter((value): value is string => Boolean(value));

  return details.length ? `${baseLabel} (${details.join(', ')})` : baseLabel;
}

function normalizeSupportedClassSociety(value: string | null | undefined): string | null {
  const normalized = String(value ?? '').trim().toUpperCase();
  return ['NK', 'KR', 'BV'].includes(normalized) ? normalized : null;
}

function formatStatus(value: string | null | undefined): string {
  return String(value ?? 'unknown')
    .replace(/_/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatBatchStatus(value: string | null | undefined): string {
  const label = formatStatus(value);
  return value === 'ready_for_review' ? 'Batch ready for review' : label;
}

function humanizeKey(value: string | null | undefined): string {
  return String(value ?? 'not set').replace(/[_-]+/g, ' ');
}

function confidenceClassName(mode: string): string {
  if (mode === 'manual_entry') return 'border-error-300 bg-error-50';
  if (mode === 'gap_fill') return 'border-warning-300 bg-warning-50';
  return 'border-neutral-200 bg-white';
}

function actionLabel(item: CertTrackedItem): string {
  if (item.pdfMissing || item.status === 'pending_first_upload') return 'Upload';
  if (ACTION_STATUSES.has(item.status)) return 'Renew';
  return 'Open';
}

function bannerClassName(variant: 'warning' | 'destructive' | 'info'): string {
  if (variant === 'destructive') return 'border-error-200 bg-error-50 text-error-800';
  if (variant === 'warning') return 'border-warning-200 bg-warning-50 text-warning-800';
  return 'border-info-200 bg-info-50 text-info-800';
}

function statusBadgeVariant(status: string): 'success' | 'warning' | 'destructive' | 'secondary' | 'info' {
  if (['current', 'ok', 'permanent', 'approved'].includes(status)) return 'success';
  if (['window_open', 'window_closing', 'pending_first_upload', 'pending_master_approval'].includes(status)) return 'warning';
  if (['overdue', 'expired', 'expired_at_onboarding', 'invalid_due_to_reflag', 'rejected'].includes(status)) return 'destructive';
  if (['pending_supersession', 'postponed'].includes(status)) return 'info';
  return 'secondary';
}

function statusClassName(status: string): string {
  if (['current', 'ok', 'permanent'].includes(status)) return 'border-green-600 bg-green-600 text-white';
  if (status === 'window_open') return 'border-yellow-300 bg-yellow-300 text-black';
  if (status === 'window_closing') return 'border-amber-500 bg-amber-500 text-black';
  if (status === 'overdue') return 'border-orange-600 bg-orange-600 text-white';
  if (['expired', 'expired_at_onboarding', 'invalid_due_to_reflag'].includes(status)) return 'border-red-600 bg-red-600 text-white';
  if (status === 'pending_first_upload') return 'border-neutral-300 bg-neutral-100 text-neutral-700';
  if (status === 'pending_supersession') return 'border-yellow-200 bg-yellow-200 text-black';
  return 'border-neutral-300 bg-white text-neutral-700';
}

function statusShapeClassName(status: string): string {
  if (['current', 'ok', 'permanent'].includes(status)) return 'border-white bg-white';
  if (['window_open', 'window_closing', 'overdue', 'pending_supersession'].includes(status)) return 'border-black bg-white';
  if (['expired', 'expired_at_onboarding', 'invalid_due_to_reflag'].includes(status)) return 'border-white bg-transparent';
  return 'border-current bg-current';
}

function filterDashboardSections(
  sections: CertVesselDashboardSection[],
  filters: { status: string; section: string; classTracked: string; pdf: string; search: string }
): CertVesselDashboardSection[] {
  const searchTerm = filters.search.trim().toLowerCase();
  return sections
    .filter((section) => filters.section === 'all' || String(section.sectionId) === filters.section)
    .map((section) => {
      const items = section.items.filter((item) => {
        if (filters.status !== 'all') {
          if (filters.status === 'current') {
            if (!['current', 'ok', 'permanent'].includes(item.status)) return false;
          } else if (filters.status === 'pending_master_approval') {
            if (item.approvalState !== 'pending_master_approval') return false;
          } else if (item.status !== filters.status) {
            return false;
          }
        }
        if (filters.classTracked === 'class' && !item.isClassTracked) return false;
        if (filters.classTracked === 'non_class' && item.isClassTracked) return false;
        if (filters.pdf === 'missing' && !item.pdfMissing) return false;
        if (filters.pdf === 'attached' && item.pdfMissing) return false;
        if (searchTerm && !dashboardItemMatchesSearch(item, section, searchTerm)) return false;
        return true;
      });
      return {
        ...section,
        items,
        activeTrackedItemCount: items.length,
        actionItemCount: items.filter((item) => ACTION_STATUSES.has(item.status) || item.pdfMissing).length,
        statusBreakdown: items.reduce<Record<string, number>>((accumulator, item) => {
          accumulator[item.status] = (accumulator[item.status] ?? 0) + 1;
          return accumulator;
        }, {}),
      };
    });
}

function dashboardItemMatchesSearch(
  item: CertTrackedItem,
  section: CertVesselDashboardSection,
  searchTerm: string
): boolean {
  return [
    section.displayName,
    section.sectionCode,
    item.displayName,
    item.catalogDisplayName,
    item.catalogCode,
    item.shortName,
    item.catalogShortName,
    item.certificateNumber,
    item.issuingAuthority,
    item.placeOfIssue,
    item.issueDate,
    item.expiryDate,
    item.validityShortCode,
    item.validityType,
    item.status,
    item.approvalState,
    item.daysToGo == null ? null : String(item.daysToGo),
  ]
    .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
    .some((value) => value.toLowerCase().includes(searchTerm));
}

const AUDIT_ACTION_LABELS: Record<string, string> = {
  create_tracked_item: 'Certificate record created',
  update_tracked_item: 'Certificate details updated',
  submit_tracked_item: 'Submitted for approval',
  approve_tracked_item: 'Approved',
  reject_tracked_item: 'Rejected',
  upload_tracked_item_pdf: 'Certificate file uploaded',
  remove_tracked_item_pdf: 'Certificate file removed',
  quarantine_resolve: 'Certificate status updated',
};

const TRACKED_AUDIT_FIELD_LABELS: Record<string, string> = {
  approvalState: 'Approval status',
  approvedAt: 'Approved on',
  approvedBy: 'Approved by',
  certificateNumber: 'Certificate number',
  draftExpiresAt: 'Draft expiry',
  expiryDate: 'Expiry date',
  extensionAuthority: 'Extension authority',
  extensionLetterPdfId: 'Extension letter',
  extensionReason: 'Extension reason',
  issuingAuthority: 'Issuing authority',
  issueDate: 'Issue date',
  lastDoneDate: 'Last completed',
  nextDueDate: 'Next due date',
  pdfAttachmentId: 'Certificate file',
  pdfMissing: 'Certificate file status',
  placeOfIssue: 'Place of issue',
  postponedUntil: 'Postponed until',
  rejectionCount: 'Rejection count',
  rejectionReason: 'Rejection reason',
  status: 'Certificate status',
  submittedAt: 'Submitted on',
  submittedBy: 'Submitted by',
  supersedesId: 'Superseded certificate',
  windowClose: 'Renewal deadline',
  windowOpen: 'Renewal starts',
};

const TRACKED_AUDIT_TECHNICAL_FIELDS = new Set([
  'createdAt',
  'createdBy',
  'createdByDisplay',
  'id',
  'rowVersion',
  'updatedAt',
  'updatedBy',
  'updatedByDisplay',
  'version',
]);

function formatAuditAction(action: string): string {
  const normalized = String(action || '').trim();
  if (AUDIT_ACTION_LABELS[normalized]) {
    return AUDIT_ACTION_LABELS[normalized];
  }
  return normalized
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ') || 'Activity recorded';
}

function formatApprovalEventTitle(event: CertTrackedItemDetail['approvalEvents'][number]): string {
  if (event.toState === 'approved') return 'Approved';
  if (event.toState === 'rejected') return 'Rejected';
  if (event.toState === 'pending_master_approval') return 'Submitted for approval';
  if (event.toState === 'draft') return 'Saved as draft';
  return `${formatStatus(event.fromState)} to ${formatStatus(event.toState)}`;
}

function isUuidLike(value: string | null | undefined): boolean {
  const text = String(value ?? '').trim();
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(text) || /^[0-9a-f]{32}$/i.test(text);
}

function formatPrincipalLabel(
  displayName: string | null | undefined,
  rawIdentifier: string | null | undefined,
  role?: string | null,
  emptyLabel = 'User not resolved'
): string {
  const cleanDisplayName = String(displayName ?? '').trim();
  if (cleanDisplayName) return cleanDisplayName;

  const cleanRole = String(role ?? '').trim();
  const cleanIdentifier = String(rawIdentifier ?? '').trim();
  if (cleanRole && cleanIdentifier && !isUuidLike(cleanIdentifier)) {
    return `${cleanRole} - ${cleanIdentifier}`;
  }
  if (cleanRole) return cleanRole;
  if (cleanIdentifier && !isUuidLike(cleanIdentifier)) return cleanIdentifier;
  return emptyLabel;
}

function formatEntityLabel(rawIdentifier: string | null | undefined, fallback: string): string {
  const cleanIdentifier = String(rawIdentifier ?? '').trim();
  if (!cleanIdentifier || isUuidLike(cleanIdentifier)) return fallback;
  return cleanIdentifier;
}

function formatEntityAuditLabel(entityType: string, entityId: string | null | undefined): string {
  const label = formatAuditAction(entityType);
  const cleanEntityId = String(entityId ?? '').trim();
  if (!cleanEntityId || isUuidLike(cleanEntityId)) return label;
  return `${label} ${cleanEntityId}`;
}

function summarizeAuditDiff(entry: CertCatalogAuditEntry): string {
  if (!entry.before && entry.after) {
    return 'Created catalog row.';
  }
  if (entry.before && entry.after) {
    const keys = new Set([...Object.keys(entry.before), ...Object.keys(entry.after)]);
    const changed = Array.from(keys).filter((key) => JSON.stringify(entry.before?.[key]) !== JSON.stringify(entry.after?.[key]));
    return changed.length ? `Changed: ${changed.join(', ')}` : 'No field-level diff.';
  }
  return 'Audit event recorded.';
}

function summarizeTrackedAuditDiff(entry: CertTrackedItemAuditEvent): string {
  if (!entry.before && entry.after) {
    return 'Certificate record was created.';
  }
  if (entry.before && entry.after) {
    const keys = new Set([...Object.keys(entry.before), ...Object.keys(entry.after)]);
    const changed = Array.from(keys)
      .filter((key) => !TRACKED_AUDIT_TECHNICAL_FIELDS.has(key))
      .filter((key) => JSON.stringify(entry.before?.[key]) !== JSON.stringify(entry.after?.[key]))
      .map((key) => TRACKED_AUDIT_FIELD_LABELS[key] ?? formatAuditAction(key))
      .filter((label, index, labels) => labels.indexOf(label) === index);
    if (changed.length === 0) {
      return 'Certificate record was reviewed.';
    }
    return `Updated: ${changed.join(', ')}.`;
  }
  return 'Activity recorded.';
}

function summarizeAuditLogDiff(entry: CertAuditLogEntry): string {
  if (!entry.before && entry.after) {
    return `Created ${entry.entityType.replace(/_/g, ' ')}.`;
  }
  if (entry.before && entry.after) {
    const keys = new Set([...Object.keys(entry.before), ...Object.keys(entry.after)]);
    const changed = Array.from(keys).filter((key) => JSON.stringify(entry.before?.[key]) !== JSON.stringify(entry.after?.[key]));
    return changed.length ? `Changed: ${changed.join(', ')}` : 'No field-level diff.';
  }
  return 'Audit event recorded.';
}

function formatAuditorGrantScope(grant: CertAuditorAccessGrant): string {
  const scope = grant.scope;
  const parts = [
    `${scope.vesselIds.length} vessel${scope.vesselIds.length === 1 ? '' : 's'}`,
    `${scope.sections.length} section${scope.sections.length === 1 ? '' : 's'}`,
  ];
  if (scope.certIds.length > 0) {
    parts.push(`${scope.certIds.length} cert${scope.certIds.length === 1 ? '' : 's'}`);
  }
  return parts.join(' / ');
}

function splitLinesOrCommas(value: string): string[] {
  return value
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function orderRowsForHierarchy(rows: CertCatalogRow[]): CertCatalogRow[] {
  const childrenByParent = new Map<string, CertCatalogRow[]>();
  const topLevelRows: CertCatalogRow[] = [];
  const orphanRows: CertCatalogRow[] = [];
  const rowIds = new Set(rows.map((row) => row.id));

  rows.forEach((row) => {
    if (!row.parentId) {
      topLevelRows.push(row);
      return;
    }
    if (!rowIds.has(row.parentId)) {
      orphanRows.push(row);
      return;
    }
    const siblings = childrenByParent.get(row.parentId) ?? [];
    siblings.push(row);
    childrenByParent.set(row.parentId, siblings);
  });

  return topLevelRows.flatMap((row) => [row, ...(childrenByParent.get(row.id) ?? [])]).concat(orphanRows);
}

function getParentOptions(rows: CertCatalogRow[], currentRowId?: string): CertCatalogRow[] {
  return rows.filter((row) => row.id !== currentRowId && !row.parentId);
}

function formatParentOption(row: CertCatalogRow): string {
  return `${row.canonicalCode} - ${row.displayName}`;
}

function getCatalogPrintSectionLabelOptions(
  rows: CertCatalogRow[],
  sections: CertCatalogSection[]
): CatalogSelectOption[] {
  const labels = new Map<string, string>();
  sections.forEach((section) => {
    const label = String(section.displayName ?? '').trim();
    if (label) {
      labels.set(label.toLowerCase(), label);
    }
  });
  rows.forEach((row) => {
    const label = String(row.printSectionLabel ?? '').trim();
    if (label) {
      labels.set(label.toLowerCase(), label);
    }
  });
  return Array.from(labels.values())
    .sort((left, right) => left.localeCompare(right))
    .map((label) => ({ value: label, label }));
}

function includeCurrentCatalogOption(
  options: readonly CatalogSelectOption[],
  currentValue: string
): CatalogSelectOption[] {
  const value = currentValue.trim();
  if (!value || options.some((option) => option.value === value)) {
    return [...options];
  }
  return [{ value, label: formatStatus(value) }, ...options];
}

function cleanCatalogIntegerInput(value: string): string {
  return value.replace(/\D/g, '');
}

function parseOptionalCatalogInteger(value: string): number | null {
  const cleaned = cleanCatalogIntegerInput(value);
  return cleaned ? Number(cleaned) : null;
}

function formatCatalogVesselName(vessel: CertFleetDashboardVessel): string {
  return String(vessel.name || vessel.code || vessel.imo || vessel.id).trim();
}

function formatCatalogVesselOption(vessel: CertFleetDashboardVessel): string {
  const name = formatCatalogVesselName(vessel);
  const details = [
    vessel.code ? String(vessel.code).trim() : null,
    vessel.imo ? `IMO ${String(vessel.imo).trim()}` : null,
  ].filter(Boolean);
  return details.length ? `${name} - ${details.join(' - ')}` : name;
}

function formatSelectedCatalogVessels(
  selectedIds: string[],
  vessels: CertFleetDashboardVessel[]
): string {
  if (selectedIds.length === 0) {
    return 'Select vessels';
  }
  if (selectedIds.length === 1) {
    const selectedVessel = vessels.find((vessel) => vessel.id === selectedIds[0]);
    return selectedVessel ? formatCatalogVesselName(selectedVessel) : '1 vessel selected';
  }
  return `${selectedIds.length} vessels selected`;
}

function normalizedCatalogText(value: string | null | undefined): string {
  return String(value ?? '').trim().toUpperCase().replace(/[_\s]+/g, '-');
}

function isRollupCatalogRow(row: CertCatalogRow): boolean {
  const haystack = [
    normalizedCatalogText(row.canonicalCode),
    normalizedCatalogText(row.displayName),
    normalizedCatalogText(row.shortName),
  ].join(' ');
  return ROLLUP_ROW_TOKENS.some((token) => haystack.includes(token));
}

function getInlinePromotionContext(search: string): CertCatalogInlinePromotionContext | undefined {
  const params = new URLSearchParams(search);
  if (params.get('source') !== 'onboarding_gap_fill') {
    return undefined;
  }
  const vesselId = params.get('vesselId')?.trim();
  if (!vesselId) {
    return undefined;
  }
  const batchId = params.get('batchId')?.trim();
  return {
    source: 'onboarding_gap_fill',
    vesselId,
    ...(batchId ? { batchId } : {}),
  };
}

function CertShipTypeCheckboxGroup({
  idPrefix,
  value,
  onChange,
}: {
  idPrefix: string;
  value: string[];
  onChange: (value: string[]) => void;
}) {
  const selected = value.length ? value : ['all'];
  const toggle = (shipType: string, checked: boolean) => {
    if (shipType === 'all') {
      onChange(checked ? ['all'] : []);
      return;
    }
    const next = new Set(selected.filter((item) => item !== 'all'));
    if (checked) {
      next.add(shipType);
    } else {
      next.delete(shipType);
    }
    onChange(next.size ? Array.from(next) : ['all']);
  };

  return (
    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {SHIP_TYPE_OPTIONS.map((option) => {
        const id = `${idPrefix}-${option.value}`;
        return (
          <label key={option.value} htmlFor={id} className="flex items-center gap-2 text-sm text-neutral-700">
            <Checkbox
              id={id}
              checked={selected.includes(option.value)}
              onCheckedChange={(checked) => toggle(option.value, Boolean(checked))}
            />
            {option.label}
          </label>
        );
      })}
    </div>
  );
}

function formatShipTypes(values: string[]): string {
  const selected = values.length ? values : ['all'];
  return selected
    .map((value) => SHIP_TYPE_OPTIONS.find((option) => option.value === value)?.label ?? value)
    .join(', ');
}

function CertsRouteContent() {
  const location = useLocation();
  const auth = useAuth();
  const canOpenCerts = useHasAnyCertsForm();
  const path = location.pathname.replace(/\/+$/, '');

  const auditorPrintMatch = path.match(/^\/auditor\/([^/]+)\/print$/);
  if (auditorPrintMatch) {
    return <AuditorPortalPage token={decodeURIComponent(auditorPrintMatch[1])} view="print" />;
  }

  const auditorVesselMatch = path.match(/^\/auditor\/([^/]+)\/vessels\/([^/]+)$/);
  if (auditorVesselMatch) {
    return (
      <AuditorPortalPage
        token={decodeURIComponent(auditorVesselMatch[1])}
        view="vessel"
        id={decodeURIComponent(auditorVesselMatch[2])}
      />
    );
  }

  const auditorCertMatch = path.match(/^\/auditor\/([^/]+)\/cert\/([^/]+)$/);
  if (auditorCertMatch) {
    return (
      <AuditorPortalPage
        token={decodeURIComponent(auditorCertMatch[1])}
        view="cert"
        id={decodeURIComponent(auditorCertMatch[2])}
      />
    );
  }

  const auditorHomeMatch = path.match(/^\/auditor\/([^/]+)$/);
  if (auditorHomeMatch) {
    return <AuditorPortalPage token={decodeURIComponent(auditorHomeMatch[1])} view="home" />;
  }

  if (!canOpenCerts) {
    return <CertsPermissionDenied />;
  }

  const certsHomeRoute = getCertsHomeRoute(auth);
  if (path === ROUTES.CERTS && certsHomeRoute !== ROUTES.CERTS) {
    return <Navigate to={certsHomeRoute} replace />;
  }
  if (path === ROUTES.CERTS_CATALOG && certsHomeRoute !== ROUTES.CERTS) {
    return <Navigate to={certsHomeRoute} replace />;
  }

  if (path === ROUTES.CERTS_APPROVALS) {
    return <CertApprovalQueuePage />;
  }

  if (path === ROUTES.CERTS_CATALOG || path.startsWith(`${ROUTES.CERTS_CATALOG}/`)) {
    const rowId = path.startsWith(`${ROUTES.CERTS_CATALOG}/`)
      ? decodeURIComponent(path.slice(`${ROUTES.CERTS_CATALOG}/`.length).split('/').filter(Boolean)[0] ?? '')
      : undefined;
    return <CertCatalogAdminPage rowId={rowId} />;
  }

  if (path === ROUTES.CERTS_MASTER_MESSAGES) {
    return <CertMasterMessagesPage />;
  }

  if (path === ROUTES.CERTS_RECONCILIATION) {
    return <CertReconciliationDashboardPage />;
  }

  if (path === ROUTES.CERTS_PARSER_OPS) {
    return <CertParserOpsPage />;
  }

  if (path === ROUTES.CERTS_PRINT) {
    return <CertPrintBuilderPage />;
  }

  if (path === ROUTES.CERTS_PRINT_HISTORY) {
    return <CertPrintHistoryPage />;
  }

  if (path === ROUTES.CERTS_SHARE_BUNDLE) {
    return <CertShareBundlePage />;
  }

  if (path === ROUTES.CERTS_AUDIT_LOG) {
    return <CertAuditLogPage />;
  }

  if (path === ROUTES.CERTS_SETTINGS) {
    return <CertSettingsPage />;
  }

  if (path === ROUTES.CERTS_AUDITOR_ACCESS || path.startsWith(`${ROUTES.CERTS_AUDITOR_ACCESS}/`)) {
    const grantId = path.startsWith(`${ROUTES.CERTS_AUDITOR_ACCESS}/`)
      ? path.slice(`${ROUTES.CERTS_AUDITOR_ACCESS}/`.length)
      : undefined;
    return <CertAuditorAccessPage grantId={grantId ? decodeURIComponent(grantId) : undefined} />;
  }

  const reconciliationRunMatch = path.match(/^\/certs\/reconciliation\/([^/]+)$/);
  if (reconciliationRunMatch) {
    return <CertReconciliationRunPage runId={decodeURIComponent(reconciliationRunMatch[1])} />;
  }

  if (path === ROUTES.CERTS_ONBOARDING || path === ROUTES.CERTS_ONBOARDING_NEW) {
    return <CertOnboardingHubPage />;
  }

  const onboardingGapFillMatch = path.match(/^\/certs\/onboarding\/([^/]+)\/batch\/([^/]+)\/gap-fill$/);
  if (onboardingGapFillMatch) {
    return (
      <CertOnboardingGapFillPage
        imo={decodeURIComponent(onboardingGapFillMatch[1])}
        batchId={decodeURIComponent(onboardingGapFillMatch[2])}
      />
    );
  }

  const onboardingWizardMatch = path.match(/^\/certs\/onboarding\/([^/]+)$/);
  if (onboardingWizardMatch) {
    return <CertOnboardingWizardPage vesselId={decodeURIComponent(onboardingWizardMatch[1])} />;
  }

  const trackedItemDetailMatch = path.match(/^\/certs\/vessels\/([^/]+)\/cert\/([^/]+)$/);
  if (trackedItemDetailMatch) {
    return (
      <CertTrackedItemDetailPage
        imo={decodeURIComponent(trackedItemDetailMatch[1])}
        trackedItemId={decodeURIComponent(trackedItemDetailMatch[2])}
      />
    );
  }

  const vesselProfileMatch = path.match(/^\/certs\/vessels\/([^/]+)\/profile$/);
  if (vesselProfileMatch) {
    return <CertVesselProfilePage imo={decodeURIComponent(vesselProfileMatch[1])} />;
  }

  const vesselDashboardMatch = path.match(/^\/certs\/vessels\/([^/]+)$/);
  if (vesselDashboardMatch) {
    return <CertVesselDashboardPage imo={decodeURIComponent(vesselDashboardMatch[1])} />;
  }

  return <CertsLandingStub />;
}

export function CertsDashboardStubPage() {
  return (
    <div className="certs-theme">
      <CertsRouteContent />
    </div>
  );
}

function CertVesselOfficeMessagesCard({
  enabled,
  messages,
  isLoading,
}: {
  enabled: boolean;
  messages: CertMasterReconciliationMessage[];
  isLoading: boolean;
}) {
  if (!enabled) return null;
  const pendingCount = messages.filter((message) => !message.masterReviewedAt).length;
  return (
    <Card>
      <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-warning-50 text-warning-700">
            <AlertTriangle className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-neutral-900">Messages from office</h2>
            <p className="text-sm text-neutral-600">
              {isLoading
                ? 'Checking for office messages.'
                : pendingCount > 0
                  ? `${pendingCount} message${pendingCount === 1 ? '' : 's'} from office need review.`
                  : 'No pending office messages.'}
            </p>
          </div>
        </div>
        <Button asChild variant={pendingCount > 0 ? 'default' : 'outline'}>
          <Link to={ROUTES.CERTS_MASTER_MESSAGES}>Open messages</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

function CertMasterMessagesPage() {
  const canRead = useCertsPermission(FORM_IDS.CERTS_RECONCILIATION);
  const auth = useAuth();
  const [includeReviewed, setIncludeReviewed] = useState(false);
  const messages = useMasterReconciliationMessages({ includeReviewed, pageSize: 100 }, canRead && auth.isVessel);
  const canAcknowledgeMessages = isMasterRole(normalizeAuthRole(auth));

  if (!canRead || !auth.isVessel) {
    return <CertsPermissionDenied />;
  }

  return (
    <RootLayout>
      <PageHeader title="Messages from Office" />
      <div className="space-y-4 p-4">
        <Card>
          <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-neutral-900">Class status items from office</h2>
              <p className="text-sm text-neutral-600">Review the items office sent after checking the class status PDF.</p>
            </div>
            <label className="flex items-center gap-2 text-sm text-neutral-700">
              <Checkbox checked={includeReviewed} onCheckedChange={(checked) => setIncludeReviewed(Boolean(checked))} />
              Show reviewed messages
            </label>
          </CardContent>
        </Card>

        {messages.isLoading ? (
          <div className="space-y-3">
            <Skeleton className="h-36 w-full" />
            <Skeleton className="h-36 w-full" />
          </div>
        ) : messages.isError ? (
          <CertsInlineError
            title="Could not load office messages"
            message={getErrorMessage(messages.error)}
            onRetry={() => messages.refetch()}
          />
        ) : !messages.data?.results.length ? (
          <Card>
            <CardContent className="p-6 text-center text-sm text-neutral-600">
              {includeReviewed ? 'No office messages found.' : 'No pending office messages.'}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {messages.data.results.map((message) => (
              <CertMasterMessageCard key={message.id} message={message} canAcknowledge={canAcknowledgeMessages && !message.masterReviewedAt} />
            ))}
          </div>
        )}
      </div>
    </RootLayout>
  );
}

function CertMasterMessageCard({
  message,
  canAcknowledge,
}: {
  message: CertMasterReconciliationMessage;
  canAcknowledge: boolean;
}) {
  const [note, setNote] = useState('');
  const acknowledge = useAcknowledgeMasterReconciliationMessage();
  const diffRows = Object.entries(message.diff ?? {});
  const classFields = getMasterMessageClassFields(message);

  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={message.masterReviewedAt ? 'success' : 'warning'}>
                {message.masterReviewedAt ? 'Reviewed' : 'Needs review'}
              </Badge>
              <Badge variant="secondary">{formatReconciliationBucketLabel(message.bucket)}</Badge>
            </div>
            <h2 className="text-base font-semibold text-neutral-900">{formatMasterMessageTitle(message)}</h2>
            <p className="text-sm text-neutral-600">
              Sent {formatDateTime(message.officeNotifiedAt)} by {formatPrincipalLabel(undefined, message.officeNotifiedBy, undefined, 'office')}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {message.snapshotId ? (
              <ClassSnapshotPdfButton snapshotId={message.snapshotId} size="sm" showIcon={false}>
                Open class status PDF
              </ClassSnapshotPdfButton>
            ) : null}
            {message.trackedItemId && message.imo ? (
              <Button asChild size="sm" variant="outline">
                <Link to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(message.imo, message.trackedItemId)}>Open certificate</Link>
              </Button>
            ) : null}
          </div>
        </div>

        <section className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
          <h3 className="text-sm font-semibold text-neutral-900">Office note</h3>
          <p className="mt-1 whitespace-pre-wrap text-sm text-neutral-700">{message.officeNote || 'No note added.'}</p>
        </section>

        {diffRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-200 text-sm">
              <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                <tr>
                  <th className="px-3 py-2">Item</th>
                  <th className="px-3 py-2">VIMS record</th>
                  <th className="px-3 py-2">Class report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {diffRows.map(([field, value]) => {
                  return (
                    <tr key={field}>
                      <td className="px-3 py-2 font-medium text-neutral-900">{humanizeKey(field)}</td>
                      <td className="px-3 py-2 text-neutral-700">{formatReconciliationDiffValue(value, 'vims')}</td>
                      <td className="px-3 py-2 text-neutral-700">{formatReconciliationDiffValue(value, 'class')}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : classFields.length > 0 ? (
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            {classFields.map((field) => (
              <CertReconciliationDefinition key={field.label} label={field.label} value={field.value} />
            ))}
          </dl>
        ) : null}

        {message.masterReviewedAt ? (
          <div className="rounded-md border border-success-200 bg-success-50 p-3 text-sm text-success-800">
            Reviewed {formatDateTime(message.masterReviewedAt)}
            {message.masterReviewNote ? ` - ${message.masterReviewNote}` : ''}
          </div>
        ) : canAcknowledge ? (
          <div className="space-y-3 border-t border-neutral-200 pt-4">
            <div className="space-y-2">
              <Label htmlFor={`masterReviewNote-${message.id}`}>Review note</Label>
              <Textarea
                id={`masterReviewNote-${message.id}`}
                value={note}
                onChange={(event) => setNote(event.target.value)}
                placeholder="Add a short note for office"
              />
            </div>
            {acknowledge.error ? <p className="text-sm text-error-700">{getErrorMessage(acknowledge.error)}</p> : null}
            <Button
              type="button"
              disabled={acknowledge.isPending}
              onClick={() => acknowledge.mutate({ messageId: message.id, note })}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" aria-hidden="true" />
              Mark reviewed
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default CertsDashboardStubPage;
