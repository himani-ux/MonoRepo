import { type FormEvent, type ReactNode, useEffect, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import {
  ArchiveX,
  Activity,
  AlertTriangle,
  CornerDownRight,
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
  useHardPurgeCatalogRow,
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
  useClassSnapshots,
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
  useSubmitTrackedItem,
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
import type {
  CertCatalogAuditEntry,
  CertAuditLogEntry,
  CertAuditLogFilters,
  CertAuditorAccessGrant,
  CertCatalogInlinePromotionContext,
  CertCatalogRow,
  CertClassSnapshot,
  CertGapFillFieldState,
  CertGapFillPdf,
  CertOnboardingBatch,
  CertOnboardingHubRow,
  CertReconciliationAnomalyBreach,
  CertReconciliationFlag,
  CertReconciliationRun,
  CertReconciliationRunDetail,
  CertTrackedItemAuditEvent,
  CertTrackedItemDetail,
  CertTrackedItem,
  CertOnboardingWizardState,
  CertPrintArtifact,
  CertPrintScope,
  CertPrintWatermark,
  CertValidationEntry,
  CertFleetDashboardResponse,
  CertVesselLifecycleResponse,
  CertVesselDashboardResponse,
  CertVesselDashboardSection,
  CertAlertConfig,
  CertSettingsResponse,
  CertSlackRoute,
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
  { value: 'specific_vessel_ids', label: 'Specific vessel IDs' },
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
  { bucket: 'match', label: 'Matches', countKey: 'matchesCount' },
  { bucket: 'mismatch', label: 'Mismatches', countKey: 'mismatchesCount' },
  { bucket: 'missing_in_catalog', label: 'Missing in Catalog', countKey: 'missingInCatalogCount' },
  { bucket: 'missing_in_class', label: 'Missing in Class', countKey: 'missingInClassCount' },
  { bucket: 'conditional_stc', label: 'Conditional/STC detected', countKey: 'conditionalStcDetectedCount' },
  { bucket: 'extended_postponed', label: 'Extended/Postponed detected', countKey: 'extendedPostponedDetectedCount' },
  { bucket: 'unmapped_low_confidence', label: 'Unmapped low confidence', countKey: 'unmappedLowConfidenceCount' },
] as const;

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
                You don't have access to this page.
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

function CertsLandingStub() {
  const auth = useAuth();
  const role = normalizeAuthRole(auth);
  const canReadCatalog = auth.hasForm?.(FORM_IDS.CERTS_CATALOG) === true;
  const canReadTrackedItems = auth.hasForm?.(FORM_IDS.CERTS_TRACKED_ITEMS) === true;
  const vesselDashboardIdentifier = getCertsVesselIdentifier(auth);
  const showOfficeVesselList = canReadTrackedItems && !vesselDashboardIdentifier;
  const showHighVolumePrintCard = isFleetManagerRole(role) && auth.hasForm?.(FORM_IDS.CERTS_PRINT_EXPORT);
  const showBouncingEmailCard = isDpaRole(role) && auth.hasForm?.(FORM_IDS.CERTS_TRACKED_ITEMS);
  const showHeartbeatCard = isDpaRole(role) && auth.hasForm?.(FORM_IDS.CERTS_TRACKED_ITEMS);

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
            {canReadTrackedItems && vesselDashboardIdentifier ? (
              <Button asChild>
                <Link to={ROUTES.CERTS_VESSEL_DASHBOARD(vesselDashboardIdentifier)}>Open vessel certificates</Link>
              </Button>
            ) : null}
          </div>
        </div>
        {showOfficeVesselList ? <CertOfficeVesselListCard /> : null}
        {showHeartbeatCard ? <CertFleetCadenceHeartbeatCard /> : null}
        {showBouncingEmailCard ? <CertFleetBouncingEmailCard /> : null}
        {showHighVolumePrintCard ? <CertFleetHighVolumePrintCard /> : null}
      </section>
    </RootLayout>
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
            <ErrorState
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

function CertPrintBuilderPage() {
  const canPrint = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT, PROCESS_IDS.CERTS_PRINT);
  const location = useLocation();
  const initialVesselId = new URLSearchParams(location.search).get('vesselId') ?? '';
  const [scope, setScope] = useState<Exclude<CertPrintScope, 'share_bundle'>>('per_vessel_full');
  const [vesselIds, setVesselIds] = useState(initialVesselId);
  const [sections, setSections] = useState('');
  const [customCertIds, setCustomCertIds] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [watermark, setWatermark] = useState<CertPrintWatermark>('NONE');
  const [watermarkRecipient, setWatermarkRecipient] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const mutation = useGeneratePrintArtifact();

  if (!canPrint) {
    return <CertsPermissionDenied />;
  }

  const submitPrint = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    mutation.mutate({
      scope,
      vesselIds: parseCsvValues(vesselIds),
      sections: parseCsvValues(sections),
      customCertIds: parseCsvValues(customCertIds),
      filters: { status: statusFilter },
      watermarkApplied: watermark,
      watermarkRecipient,
      recipientEmail,
    });
  };

  return (
    <RootLayout>
      <PageHeader title="Print Builder" />
      <div className="space-y-4 p-4">
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to={ROUTES.CERTS_PRINT_HISTORY}>
              <History className="mr-2 h-4 w-4" aria-hidden="true" />
              Print history
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link to={ROUTES.CERTS_SHARE_BUNDLE}>
              <Share2 className="mr-2 h-4 w-4" aria-hidden="true" />
              Share bundle
            </Link>
          </Button>
        </div>
        <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <Card>
            <CardHeader>
              <CardTitle>SQE S 633 export</CardTitle>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={submitPrint}>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="printScope">Scope</Label>
                    <Select value={scope} onValueChange={(value) => setScope(value as Exclude<CertPrintScope, 'share_bundle'>)}>
                      <SelectTrigger id="printScope"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="per_vessel_full">Per-vessel full</SelectItem>
                        <SelectItem value="per_vessel_partial">Per-vessel partial</SelectItem>
                        <SelectItem value="per_section_fleetwide">Per-section fleet-wide</SelectItem>
                        <SelectItem value="custom_selection">Custom selection</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="printStatus">Status</Label>
                    <Select value={statusFilter} onValueChange={setStatusFilter}>
                      <SelectTrigger id="printStatus"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All statuses</SelectItem>
                        <SelectItem value="ok">Current</SelectItem>
                        <SelectItem value="window_open">Window open</SelectItem>
                        <SelectItem value="window_closing">Window closing</SelectItem>
                        <SelectItem value="overdue">Overdue</SelectItem>
                        <SelectItem value="expired">Expired</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="printVessels">Vessel IDs</Label>
                  <Textarea id="printVessels" value={vesselIds} onChange={(event) => setVesselIds(event.target.value)} rows={2} />
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="printSections">Sections</Label>
                    <Input id="printSections" value={sections} onChange={(event) => setSections(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="printWatermark">Watermark</Label>
                    <Select value={watermark} onValueChange={(value) => setWatermark(value as CertPrintWatermark)}>
                      <SelectTrigger id="printWatermark"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NONE">None</SelectItem>
                        <SelectItem value="INTERNAL">Internal</SelectItem>
                        <SelectItem value="AUDIT_COPY">Audit copy</SelectItem>
                        <SelectItem value="DRAFT">Draft</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="printCustomCerts">Custom certificate IDs</Label>
                  <Textarea id="printCustomCerts" value={customCertIds} onChange={(event) => setCustomCertIds(event.target.value)} rows={3} />
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="printWatermarkRecipient">Watermark recipient</Label>
                    <Input id="printWatermarkRecipient" value={watermarkRecipient} onChange={(event) => setWatermarkRecipient(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="printRecipientEmail">Recipient email</Label>
                    <Input id="printRecipientEmail" type="email" value={recipientEmail} onChange={(event) => setRecipientEmail(event.target.value)} />
                  </div>
                </div>
                {mutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(mutation.error)}</p> : null}
                <Button type="submit" disabled={mutation.isPending}>
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
        <div className="grid gap-2 md:grid-cols-3">
          <Badge variant={artifact.pdfBlobId ? 'success' : 'secondary'}>PDF {artifact.pdfBlobId ? 'ready' : 'n/a'}</Badge>
          <Badge variant={artifact.excelBlobId ? 'success' : 'secondary'}>Excel {artifact.excelBlobId ? 'ready' : 'n/a'}</Badge>
          <Badge variant={artifact.bundleZipBlobId ? 'success' : 'secondary'}>ZIP {artifact.bundleZipBlobId ? 'ready' : 'n/a'}</Badge>
        </div>
      </CardContent>
    </Card>
  );
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
            Print builder
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
                          <div className="flex flex-wrap gap-1">
                            {artifact.pdfBlobId ? <Badge variant="success">PDF</Badge> : null}
                            {artifact.excelBlobId ? <Badge variant="success">Excel</Badge> : null}
                            {artifact.bundleZipBlobId ? <Badge variant="success">ZIP</Badge> : null}
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

function CertShareBundlePage() {
  const canShareBundle = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT, PROCESS_IDS.CERTS_EXPORT_BUNDLE);
  const location = useLocation();
  const initialVesselId = new URLSearchParams(location.search).get('vesselId') ?? '';
  const [vesselIds, setVesselIds] = useState(initialVesselId);
  const [customCertIds, setCustomCertIds] = useState('');
  const [watermarkRecipient, setWatermarkRecipient] = useState('');
  const [recipientEmail, setRecipientEmail] = useState('');
  const mutation = useGenerateShareBundle();

  if (!canShareBundle) {
    return <CertsPermissionDenied />;
  }

  const submitBundle = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    mutation.mutate({
      vesselIds: parseCsvValues(vesselIds),
      customCertIds: parseCsvValues(customCertIds),
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
                <div className="space-y-2">
                  <Label htmlFor="bundleVessels">Vessel IDs</Label>
                  <Textarea id="bundleVessels" value={vesselIds} onChange={(event) => setVesselIds(event.target.value)} rows={2} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="bundleCerts">Certificate IDs</Label>
                  <Textarea id="bundleCerts" value={customCertIds} onChange={(event) => setCustomCertIds(event.target.value)} rows={4} />
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="bundleRecipient">Recipient name</Label>
                    <Input id="bundleRecipient" value={watermarkRecipient} onChange={(event) => setWatermarkRecipient(event.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bundleEmail">Recipient email</Label>
                    <Input id="bundleEmail" type="email" value={recipientEmail} onChange={(event) => setRecipientEmail(event.target.value)} />
                  </div>
                </div>
                {mutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(mutation.error)}</p> : null}
                <Button type="submit" disabled={mutation.isPending}>
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
        <dt className="text-neutral-500">Scope</dt>
        <dd className="font-medium text-neutral-900">{formatStatus(artifact.scope)}</dd>
      </div>
      <div>
        <dt className="text-neutral-500">Generated</dt>
        <dd className="font-medium text-neutral-900">{formatDateTime(artifact.timestampUtc)}</dd>
      </div>
      <div>
        <dt className="text-neutral-500">Hash</dt>
        <dd className="font-medium text-neutral-900">{artifact.systemStateHash}</dd>
      </div>
      <div>
        <dt className="text-neutral-500">Watermark</dt>
        <dd className="font-medium text-neutral-900">{formatStatus(artifact.watermarkApplied)}</dd>
      </div>
      <div>
        <dt className="text-neutral-500">Pages</dt>
        <dd className="font-medium text-neutral-900">{artifact.pageCount ?? 'n/a'}</dd>
      </div>
      <div>
        <dt className="text-neutral-500">Recipient</dt>
        <dd className="font-medium text-neutral-900">{artifact.watermarkRecipient || artifact.recipientEmail || 'Not set'}</dd>
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
  const canPrint = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT, PROCESS_IDS.CERTS_PRINT);
  const canShareBundle = useCertsPermission(FORM_IDS.CERTS_PRINT_EXPORT, PROCESS_IDS.CERTS_EXPORT_BUNDLE);
  const auth = useAuth();
  const role = String(auth.role ?? auth.user?.role_name ?? auth.user?.safety_role_name ?? '').trim().toUpperCase();
  const canShareThisVessel = canShareBundle && ['MASTER', 'VESSEL_MASTER', 'DPA', 'FM', 'FLEET MANAGER'].some((marker) => role.includes(marker));
  const dashboard = useVesselDashboard(canReadTrackedItems ? imo : undefined);
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
                <p className="text-sm text-neutral-600">Start the onboarding wizard to create this vessel's certificate register.</p>
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
          <div className="space-y-3">
            <div>
              <h1 className="text-2xl font-semibold text-neutral-900">{vessel.name ?? vessel.code ?? 'Vessel'}</h1>
              <p className="text-sm text-neutral-600">
                IMO {vessel.imo ?? 'Not set'} - {vessel.flag ?? 'Flag not set'} - {vessel.classSociety ?? 'Class not set'} - {formatShipType(vessel.shipType)}
              </p>
            </div>
            <div className="grid gap-3 text-sm sm:grid-cols-3">
              <div>
                <p className="text-neutral-500">Current Master</p>
                <p className="font-medium text-neutral-900">{vessel.currentMaster ?? 'Not assigned'}</p>
              </div>
              <div>
                <p className="text-neutral-500">Last class snapshot</p>
                <p className="font-medium text-neutral-900">{formatSnapshotAge(data.lastClassSnapshot)}</p>
              </div>
              <div>
                <p className="text-neutral-500">Mandatory coverage</p>
                <p className="font-medium text-neutral-900">{data.mandatoryCoverage.percent}%</p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link to={ROUTES.CERTS_VESSEL_PROFILE(imo)}>
                <Activity className="mr-2 h-4 w-4" aria-hidden="true" />
                Vessel profile
              </Link>
            </Button>
            {canPrint ? (
              <Button asChild variant="outline">
                <Link to={`${ROUTES.CERTS_PRINT}?vesselId=${encodeURIComponent(vessel.id)}&imo=${encodeURIComponent(imo)}`}>
                  <Printer className="mr-2 h-4 w-4" aria-hidden="true" />
                  Print this vessel
                </Link>
              </Button>
            ) : null}
            {canShareBundle ? (
              <Button asChild variant="outline">
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
                  <th className="px-3 py-3">Days</th>
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
      <td className="px-3 py-3 text-neutral-700">{item.daysToGo ?? 'Permanent'}</td>
      <td className="px-3 py-3"><CertStatusBadge status={item.status} /></td>
      <td className="px-3 py-3 text-neutral-700">{formatCertificateValidity(item)}</td>
      <td className="px-3 py-3">
        <Button asChild size="sm" variant="outline">
          <Link to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(imo, item.id)}>{actionLabel(item)}</Link>
        </Button>
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
          <div><span className="text-neutral-500">Days: </span>{item.daysToGo ?? 'Permanent'}</div>
          <div><span className="text-neutral-500">Valid for: </span>{formatCertificateValidity(item)}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          {item.pdfMissing ? <Badge variant="destructive">Certificates missing</Badge> : null}
          {item.approvalState && item.approvalState !== 'approved' ? <Badge variant="warning">{formatStatus(item.approvalState)}</Badge> : null}
          <Button asChild size="sm" variant="outline">
            <Link to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(imo, item.id)}>{actionLabel(item)}</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
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
  const [bucketFilter, setBucketFilter] = useState('all');
  const [vesselId, setVesselId] = useState('');
  const [classSociety, setClassSociety] = useState('NK');
  const [printedOnDate, setPrintedOnDate] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState('');
  const runs = useReconciliationRuns(canRead ? { bucket: bucketFilter === 'all' ? null : bucketFilter } : {});
  const snapshots = useClassSnapshots(canRead ? {} : { vesselId: 'permission-denied' });
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
  const filtersActive = bucketFilter !== 'all';

  const submitUpload = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setUploadError('');
    if (!uploadFile) {
      setUploadError('Select a class status PDF.');
      return;
    }
    if (!vesselId.trim()) {
      setUploadError('Vessel ID is required.');
      return;
    }
    uploadMutation.mutate({
      vesselId: vesselId.trim(),
      classSociety,
      printedOnDate: printedOnDate || null,
      file: uploadFile,
    });
  };

  return (
    <RootLayout>
      <PageHeader title="Class Reconciliation" />
      <div className="space-y-4 p-4">
        <Card>
          <CardContent className="grid gap-3 p-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="reconciliationBucketFilter">Bucket</Label>
              <Select value={bucketFilter} onValueChange={setBucketFilter}>
                <SelectTrigger id="reconciliationBucketFilter"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All buckets</SelectItem>
                  <SelectItem value="mismatch">Mismatch</SelectItem>
                  <SelectItem value="missing_in_catalog">Missing in catalog</SelectItem>
                  <SelectItem value="missing_in_class">Missing in class</SelectItem>
                  <SelectItem value="conditional_stc">Conditional STC</SelectItem>
                  <SelectItem value="extended_postponed">Extended/postponed</SelectItem>
                  <SelectItem value="unmapped_low_confidence">Low confidence</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-wrap items-end gap-2 md:col-span-3">
              {filtersActive ? (
                <Button type="button" variant="outline" onClick={() => setBucketFilter('all')}>
                  <RotateCw className="mr-2 h-4 w-4" aria-hidden="true" />
                  Reset filters
                </Button>
              ) : null}
              {canOpenParserOps ? (
                <Button asChild variant="outline">
                  <Link to={ROUTES.CERTS_PARSER_OPS}>
                    <History className="mr-2 h-4 w-4" aria-hidden="true" />
                    Parser ops
                  </Link>
                </Button>
              ) : null}
            </div>
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
                  {filtersActive ? 'No reconciliation runs match these filters.' : 'No class snapshots have been reconciled yet.'}
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
                      <Label htmlFor="classSnapshotVesselId">Vessel ID</Label>
                      <Input id="classSnapshotVesselId" value={vesselId} onChange={(event) => setVesselId(event.target.value)} />
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
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
                        <Label htmlFor="classSnapshotPrintedOn">Printed on</Label>
                        <Input id="classSnapshotPrintedOn" type="date" value={printedOnDate} onChange={(event) => setPrintedOnDate(event.target.value)} />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="classSnapshotPdf">PDF</Label>
                      <Input
                        id="classSnapshotPdf"
                        type="file"
                        accept="application/pdf,.pdf"
                        onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)}
                      />
                    </div>
                    {uploadError ? <p className="text-sm text-error-700">{uploadError}</p> : null}
                    {uploadMutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(uploadMutation.error)}</p> : null}
                    {uploadMutation.isSuccess ? <p className="text-sm text-success-700">Snapshot uploaded.</p> : null}
                    <Button type="submit" disabled={uploadMutation.isPending}>
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
    const bucketHasRows = run.data.flags.some((flag) => flag.bucket === activeBucket);
    if (bucketHasRows) return;
    const firstBucketWithRows = RECONCILIATION_BUCKET_TABS.find((tab) =>
      run.data?.flags.some((flag) => flag.bucket === tab.bucket)
    );
    if (firstBucketWithRows) {
      setActiveBucket(firstBucketWithRows.bucket);
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
              aria-label="Reconciliation buckets"
              className="grid gap-2 md:grid-cols-2 xl:grid-cols-7"
            >
              {RECONCILIATION_BUCKET_TABS.map((tab) => {
                const count = getReconciliationBucketCount(run.data, tab.countKey);
                const selected = activeBucket === tab.bucket;
                return (
                  <button
                    key={tab.bucket}
                    type="button"
                    role="tab"
                    aria-selected={selected}
                    className={`flex min-h-14 items-center justify-between rounded-md border px-3 py-2 text-left text-sm font-medium transition ${
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
                No reconciliation flags were produced for this run.
              </div>
            ) : bucketFlags.length === 0 ? (
              <div className="rounded-md border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-600">
                No rows in this reconciliation bucket.
              </div>
            ) : (
              <div className="grid gap-4 xl:grid-cols-[0.85fr_1fr_1fr]">
                <CertReconciliationFlagList
                  flags={bucketFlags}
                  selectedFlagId={selectedFlag?.id ?? null}
                  onSelect={setSelectedFlagId}
                />
                <CertReconciliationCatalogPanel run={run.data} flag={selectedFlag} />
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
              IMO {run.imo ?? 'not set'} - {run.classSociety ?? 'Class not set'} - snapshot {formatDate(run.printedOnDate)}
            </p>
          </div>
          <p className="text-sm text-neutral-600">
            Parser {run.parserVersion ?? 'not stamped'} - reconciled {formatDateTime(run.ranAt)} - mapping v{run.mappingVersionUsed ?? 'n/a'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="success">{run.matchesCount ?? 0} matched</Badge>
          <Badge variant={getReconciliationExceptionCount(run) > 0 ? 'warning' : 'secondary'}>
            {getReconciliationExceptionCount(run)} findings
          </Badge>
          <Button type="button" variant="outline" disabled>
            <FileText className="mr-2 h-4 w-4" aria-hidden="true" />
            Open original Class Status PDF
          </Button>
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
          <p className="font-semibold">Parser anomaly threshold breached</p>
          <ul className="space-y-1">
            {breaches.map((breach, index) => (
              <li key={`${breach.type ?? 'breach'}-${index}`} className="flex flex-wrap items-center gap-2">
                <Badge variant={breach.severity === 'critical' ? 'destructive' : 'warning'}>
                  {breach.severity ?? 'warning'}
                </Badge>
                <span>{formatAnomalyBreach(breach)}</span>
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
    <aside className="space-y-2" aria-label="Reconciliation flag list">
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
              <Badge variant={flag.bucket === 'match' ? 'success' : 'warning'}>{formatStatus(flag.bucket)}</Badge>
              {resolved ? <Badge variant="success">Resolved</Badge> : <Badge variant="secondary">Open</Badge>}
            </div>
            <p className="mt-2 text-sm font-semibold text-neutral-900">{flag.catalogDisplayName ?? 'Unmapped class row'}</p>
            <p className="text-xs text-neutral-500">
              {flag.trackedItemId ? formatEntityLabel(flag.trackedItemId, 'Tracked item linked') : 'Tracked item not linked'}
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
    <section className="rounded-md border border-neutral-200 bg-white p-4" aria-label="Catalog and tracked item state">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-neutral-900">Catalog / tracked item</h2>
          <p className="text-sm text-neutral-600">{flag.catalogDisplayName ?? 'No catalog row linked'}</p>
        </div>
        {hasTrackedLink ? (
          <Button asChild size="sm" variant="outline">
            <Link to={ROUTES.CERTS_TRACKED_ITEM_DETAIL(String(run.imo), String(flag.trackedItemId))}>
              Open tracked item
            </Link>
          </Button>
        ) : null}
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
        <CertReconciliationDefinition
          label="Catalog"
          value={flag.catalogId ? formatEntityLabel(flag.catalogId, flag.catalogDisplayName ? 'Catalog row linked' : 'Catalog linked') : 'Not linked'}
        />
        <CertReconciliationDefinition
          label="Tracked item"
          value={flag.trackedItemId ? formatEntityLabel(flag.trackedItemId, 'Tracked item linked') : 'Not linked'}
        />
        <CertReconciliationDefinition label="Resolution" value={flag.resolutionAction ? formatStatus(flag.resolutionAction) : 'Open'} />
        <CertReconciliationDefinition
          label="Reviewed"
          value={flag.reviewedAt ? `${formatDateTime(flag.reviewedAt)} by ${formatPrincipalLabel(undefined, flag.reviewedBy, undefined, 'unknown')}` : 'Not reviewed'}
        />
      </dl>
      <CertReconciliationSpecialPrefill flag={flag} />
    </section>
  );
}

function CertReconciliationClassPanel({ flag }: { flag: CertReconciliationFlag | null }) {
  if (!flag) return null;
  const extract = normalizeRecord(flag.classRowExtract);
  const fields = extract ? Object.entries(extract).slice(0, 10) : [];
  return (
    <section className="rounded-md border border-neutral-200 bg-white p-4" aria-label="Class snapshot extracted state">
      <h2 className="text-base font-semibold text-neutral-900">Class snapshot extract</h2>
      {fields.length > 0 ? (
        <dl className="mt-4 grid gap-3 text-sm">
          {fields.map(([key, value]) => (
            <CertReconciliationDefinition key={key} label={humanizeKey(key)} value={formatUnknown(value)} />
          ))}
        </dl>
      ) : (
        <p className="mt-4 text-sm text-neutral-600">No class-side row extract was stored for this flag.</p>
      )}
    </section>
  );
}

function CertReconciliationSpecialPrefill({ flag }: { flag: CertReconciliationFlag }) {
  if (flag.bucket === 'conditional_stc') {
    return (
      <div className="mt-4 rounded-md border border-info-200 bg-info-50 p-3 text-sm text-info-800">
        Conditional/STC row detected. Master upload flow will use this row as a short-term child pre-fill when the pending update path is wired.
      </div>
    );
  }
  if (flag.bucket === 'extended_postponed') {
    return (
      <div className="mt-4 rounded-md border border-warning-200 bg-warning-50 p-3 text-sm text-warning-800">
        Extended/postponed row detected. Review the class extract before notifying the Master to upload extension evidence.
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
  const showMappingAction = canAddMapping && ['missing_in_catalog', 'unmapped_low_confidence'].includes(String(flag.bucket));
  const showMasterUploadLink = Boolean(flag.trackedItemId && run.imo);

  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-neutral-900">Diff and actions</h2>
            <p className="text-sm text-neutral-600">{flag.catalogDisplayName ?? 'Unmapped class row'} - {formatStatus(flag.bucket)}</p>
          </div>
          {alreadyResolved ? <Badge variant="success">Resolved {formatDateTime(flag.resolvedAt)}</Badge> : null}
        </div>

        {diffRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-200 text-sm">
              <thead className="bg-neutral-50 text-left text-xs font-semibold uppercase text-neutral-500">
                <tr>
                  <th className="px-3 py-2">Field</th>
                  <th className="px-3 py-2">Tracked / catalog</th>
                  <th className="px-3 py-2">Class snapshot</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {diffRows.map(([field, value]) => {
                  const diff = normalizeRecord(value);
                  return (
                    <tr key={field}>
                      <td className="px-3 py-2 font-medium text-neutral-900">{humanizeKey(field)}</td>
                      <td className="px-3 py-2 text-neutral-700">{formatUnknown(diff?.tracked ?? diff?.catalog ?? 'not set')}</td>
                      <td className="px-3 py-2 text-neutral-700">{formatUnknown(diff?.class ?? diff?.snapshot ?? value)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3 text-sm text-neutral-600">
            No field-level differences were recorded for this flag.
          </div>
        )}

        {canReview && !alreadyResolved ? (
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor={`reconciliationReason-${flag.id}`}>Review reason</Label>
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
                    Resolve via Master upload
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
          Add to ClassCodeMapping
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add to ClassCodeMapping</DialogTitle>
          <DialogDescription>
            Map class row {classCode} to a canonical Certs catalog row and rerun reconciliation with the new mapping version.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor={`mappingCatalogSearch-${flag.id}`}>Catalog search</Label>
            <Input
              id={`mappingCatalogSearch-${flag.id}`}
              value={catalogSearch}
              onChange={(event) => setCatalogSearch(event.target.value)}
              placeholder="Search active catalog rows"
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
            <Label htmlFor={`mappingCatalogId-${flag.id}`}>Catalog row ID</Label>
            <Input
              id={`mappingCatalogId-${flag.id}`}
              value={catalogId}
              onChange={(event) => setCatalogId(event.target.value)}
              placeholder="Paste catalog row UUID"
            />
            {selectedCatalog ? <p className="text-xs text-neutral-600">Selected: {selectedCatalog.displayName}</p> : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor={`mappingKind-${flag.id}`}>Survey kind</Label>
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
            <Label htmlFor={`mappingReason-${flag.id}`}>Mapping reason</Label>
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
            Save mapping
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function CertReconciliationDefinition({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
      <dt className="text-xs font-semibold uppercase text-neutral-500">{label}</dt>
      <dd className="mt-1 break-words text-neutral-900">{formatUnknown(value)}</dd>
    </div>
  );
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
            canApprove={canApprove && auth.isMaster}
            canReject={canReject && auth.isMaster}
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
  const removeMutation = useRemoveTrackedItemPdf(item.id, imo);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadReason, setUploadReason] = useState('');
  const [removeOpen, setRemoveOpen] = useState(false);
  const [removeReason, setRemoveReason] = useState('');

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

  return (
    <Card>
      <CardHeader>
        <CardTitle>Certificate file</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex min-h-56 items-center justify-center rounded-md border border-dashed border-neutral-300 bg-neutral-50 p-4 text-center">
          {activePdf ? (
            <div className="space-y-2">
              <FileText className="mx-auto h-8 w-8 text-neutral-500" aria-hidden="true" />
              <p className="font-medium text-neutral-900">{activePdf.filename}</p>
              <p className="text-sm text-neutral-600">
                Uploaded {formatDateTime(activePdf.uploadedAt)} by {formatPrincipalLabel(activePdf.uploadedByDisplay, activePdf.uploadedBy)}
              </p>
              <p className="text-xs text-neutral-500">{formatBytes(activePdf.sizeBytes)}</p>
            </div>
          ) : (
            <div className="space-y-2">
              <FileText className="mx-auto h-8 w-8 text-neutral-400" aria-hidden="true" />
              <p className="font-medium text-neutral-900">No active certificate file</p>
              <p className="text-sm text-neutral-600">{item.pdfMissing ? 'This certificate is marked as missing.' : 'No certificate file has been uploaded yet.'}</p>
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
  const canMasterDecision = item.approvalState === 'pending_master_approval';
  const mutationError = submitMutation.error ?? approveMutation.error ?? rejectMutation.error;

  const transitionPayload = () => ({
    reason: reason.trim() || 'Certificate workflow action.',
    version: item.version,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Workflow + Audit</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        <CertDetailGrid
          rows={[
            ['Approval state', item.approvalState ? formatStatus(item.approvalState) : 'Not set'],
            ['Submitted by', formatPrincipalLabel(item.submittedByDisplay, item.submittedBy, undefined, 'Not submitted')],
            ['Submitted at', formatDateTime(item.submittedAt)],
            ['Approved by', formatPrincipalLabel(item.approvedByDisplay, item.approvedBy, undefined, 'Not approved')],
            ['Approved at', formatDateTime(item.approvedAt)],
            ['Rejected count', String(item.rejectionCount ?? 0)],
            ['Draft expires', formatDateTime(item.draftExpiresAt)],
            ['Version', String(item.version ?? 'n/a')],
          ]}
        />
        {(canSubmitCurrent || (canMasterDecision && (canApprove || canReject))) ? (
          <div className="space-y-3 rounded-md border border-neutral-200 p-3">
            <Label htmlFor="trackedItemTransitionReason">Action reason</Label>
            <Textarea
              id="trackedItemTransitionReason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Reason for change"
            />
            {mutationError ? <p className="text-sm text-error-700">{getErrorMessage(mutationError)}</p> : null}
            <div className="flex flex-wrap gap-2">
              {canSubmitCurrent ? (
                <Button type="button" onClick={() => submitMutation.mutate(transitionPayload())} disabled={submitMutation.isPending}>
                  Submit for approval
                </Button>
              ) : null}
              {canMasterDecision && canApprove ? (
                <Button type="button" onClick={() => approveMutation.mutate(transitionPayload())} disabled={approveMutation.isPending}>
                  Approve
                </Button>
              ) : null}
              {canMasterDecision && canReject ? (
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
      <h2 className="text-sm font-semibold uppercase text-neutral-500">Approval timeline</h2>
      {events.length === 0 ? (
        <p className="text-sm text-neutral-600">No approval events recorded.</p>
      ) : (
        <div className="space-y-2">
          {events.map((event) => (
            <div key={event.id} className="rounded-md border border-neutral-200 p-3 text-sm">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={statusBadgeVariant(event.toState)}>{formatStatus(event.fromState)} to {formatStatus(event.toState)}</Badge>
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
      <h2 className="text-sm font-semibold uppercase text-neutral-500">Audit events</h2>
      {events.length === 0 ? (
        <p className="text-sm text-neutral-600">No audit events recorded.</p>
      ) : (
        <div className="space-y-2">
          {events.map((event) => (
            <div key={event.id} className="rounded-md border border-neutral-200 p-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Badge variant="secondary">{formatAuditAction(event.action)}</Badge>
                <span className="text-neutral-500">{formatDateTime(event.timestampUtc)}</span>
              </div>
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

function CertCatalogCreateForm({
  onCancel,
  parentOptions,
  inlinePromotion,
}: {
  onCancel: () => void;
  parentOptions: CertCatalogRow[];
  inlinePromotion?: CertCatalogInlinePromotionContext;
}) {
  const createMutation = useCreateCatalogRow();
  const [canonicalCode, setCanonicalCode] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [shortName, setShortName] = useState('');
  const [sectionId, setSectionId] = useState(2);
  const [printSectionLabel, setPrintSectionLabel] = useState('Statutory & Flag');
  const [validityType, setValidityType] = useState('full');
  const [cadenceMonths, setCadenceMonths] = useState(60);
  const [issuingAuthorityType, setIssuingAuthorityType] = useState('flag');
  const [submissionScope, setSubmissionScope] = useState('all_ranks_with_approval');
  const [parentId, setParentId] = useState('none');
  const [applicableShipTypes, setApplicableShipTypes] = useState<string[]>(['all']);
  const [applicabilityMode, setApplicabilityMode] = useState('all_matching_type');
  const [specificVesselIds, setSpecificVesselIds] = useState('');
  const [isClassTracked, setIsClassTracked] = useState(false);
  const [mandatoryForAllVessels, setMandatoryForAllVessels] = useState(true);
  const [parentSupportsDynamicChildren, setParentSupportsDynamicChildren] = useState(false);
  const [reason, setReason] = useState('');

  const submit = (event: FormEvent) => {
    event.preventDefault();
    createMutation.mutate(
      {
        canonicalCode,
        displayName,
        shortName: shortName || null,
        sectionId,
        printSectionLabel,
        validityType,
        cadenceMonths: validityType === 'permanent' ? null : cadenceMonths,
        issuingAuthorityType,
        isClassTracked,
        submissionScope,
        parentId: parentId === 'none' ? null : parentId,
        applicableShipTypes,
        mandatoryForAllVessels,
        applicabilityMode,
        specificVesselIds: applicabilityMode === 'specific_vessel_ids' ? splitCsv(specificVesselIds) : [],
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
            <Input id="printSectionLabel" value={printSectionLabel} onChange={(event) => setPrintSectionLabel(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="validityType">Validity type</Label>
            <Input id="validityType" value={validityType} onChange={(event) => setValidityType(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="cadenceMonths">Cadence months</Label>
            <Input id="cadenceMonths" type="number" min={0} value={cadenceMonths} onChange={(event) => setCadenceMonths(Number(event.target.value))} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="issuingAuthorityType">Issuing authority type</Label>
            <Input id="issuingAuthorityType" value={issuingAuthorityType} onChange={(event) => setIssuingAuthorityType(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="submissionScope">Submission scope</Label>
            <Input id="submissionScope" value={submissionScope} onChange={(event) => setSubmissionScope(event.target.value)} required />
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
              <Label htmlFor="createSpecificVesselIds">Specific vessel IDs</Label>
              <Input
                id="createSpecificVesselIds"
                value={specificVesselIds}
                onChange={(event) => setSpecificVesselIds(event.target.value)}
                required
              />
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
}: {
  rowId: string;
  catalogRows: CertCatalogRow[];
}) {
  const canWrite = useCanWriteCatalog();
  const canBulkAction = useCanBulkActionCatalog();
  const navigate = useNavigate();
  const { data: row, isLoading, isError, error, refetch } = useCatalogRow(rowId);
  const auditHistory = useCatalogRowAuditHistory(rowId);
  const updateMutation = useUpdateCatalogRow(rowId);
  const deprecateMutation = useDeprecateCatalogRow(rowId);
  const hardPurgeMutation = useHardPurgeCatalogRow(rowId);
  const parentOptions = getParentOptions(catalogRows, rowId);
  const parentRow = row?.parentId ? catalogRows.find((candidate) => candidate.id === row.parentId) : undefined;
  const [displayName, setDisplayName] = useState('');
  const [printSectionLabel, setPrintSectionLabel] = useState('');
  const [validityType, setValidityType] = useState('');
  const [cadenceMonths, setCadenceMonths] = useState<number | ''>('');
  const [issuingAuthorityType, setIssuingAuthorityType] = useState('');
  const [submissionScope, setSubmissionScope] = useState('');
  const [parentId, setParentId] = useState('none');
  const [applicableShipTypes, setApplicableShipTypes] = useState<string[]>(['all']);
  const [applicabilityMode, setApplicabilityMode] = useState('all_matching_type');
  const [specificVesselIds, setSpecificVesselIds] = useState('');
  const [isClassTracked, setIsClassTracked] = useState(false);
  const [mandatoryForAllVessels, setMandatoryForAllVessels] = useState(true);
  const [parentSupportsDynamicChildren, setParentSupportsDynamicChildren] = useState(false);
  const [linkedPmsComponentId, setLinkedPmsComponentId] = useState('');
  const [reason, setReason] = useState('');
  const [reasonError, setReasonError] = useState('');

  useEffect(() => {
    if (row) {
      setDisplayName(row.displayName);
      setPrintSectionLabel(row.printSectionLabel);
      setValidityType(row.validityType);
      setCadenceMonths(row.cadenceMonths ?? '');
      setIssuingAuthorityType(row.issuingAuthorityType);
      setSubmissionScope(row.submissionScope);
      setParentId(row.parentId ?? 'none');
      setApplicableShipTypes(row.applicableShipTypes.length ? row.applicableShipTypes : ['all']);
      setApplicabilityMode(row.applicabilityMode || 'all_matching_type');
      setSpecificVesselIds(row.specificVesselIds.join(', '));
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
    updateMutation.mutate({
      displayName,
      printSectionLabel,
      validityType,
      cadenceMonths: cadenceMonths === '' || validityType === 'permanent' ? null : Number(cadenceMonths),
      issuingAuthorityType,
      isClassTracked,
      submissionScope,
      parentId: parentId === 'none' ? null : parentId,
      applicableShipTypes,
      mandatoryForAllVessels,
      parentSupportsDynamicChildren,
      linkedPmsComponentId: linkedPmsComponentId || null,
      applicabilityMode,
      specificVesselIds: applicabilityMode === 'specific_vessel_ids' ? splitCsv(specificVesselIds) : [],
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

  const hardPurge = () => {
    const trimmedReason = reason.trim();
    if (trimmedReason.length < 10) {
      setReasonError('Hard purge reason must be at least 10 characters.');
      return;
    }
    setReasonError('');
    hardPurgeMutation.mutate(
      { reason: trimmedReason },
      { onSuccess: () => navigate(ROUTES.CERTS_CATALOG) }
    );
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
              <Input id="detailPrintSectionLabel" value={printSectionLabel} onChange={(event) => setPrintSectionLabel(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailValidityType">Validity type</Label>
              <Input id="detailValidityType" value={validityType} onChange={(event) => setValidityType(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailCadenceMonths">Cadence months</Label>
              <Input id="detailCadenceMonths" type="number" min={0} value={cadenceMonths} onChange={(event) => setCadenceMonths(event.target.value === '' ? '' : Number(event.target.value))} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailIssuingAuthorityType">Issuing authority type</Label>
              <Input id="detailIssuingAuthorityType" value={issuingAuthorityType} onChange={(event) => setIssuingAuthorityType(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailSubmissionScope">Submission scope</Label>
              <Input id="detailSubmissionScope" value={submissionScope} onChange={(event) => setSubmissionScope(event.target.value)} />
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
                <Label htmlFor="detailSpecificVesselIds">Specific vessel IDs</Label>
                <Input
                  id="detailSpecificVesselIds"
                  value={specificVesselIds}
                  onChange={(event) => setSpecificVesselIds(event.target.value)}
                  required
                />
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
            {hardPurgeMutation.isError ? <p className="text-sm text-error-700">{getErrorMessage(hardPurgeMutation.error)}</p> : null}
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
              {canBulkAction ? (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button type="button" variant="destructive" disabled={hardPurgeMutation.isPending}>
                      <Trash2 className="mr-2 h-4 w-4" aria-hidden="true" />
                      Hard purge
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Hard purge catalog row?</DialogTitle>
                      <DialogDescription>
                        This permanently deletes the catalog row. Retained TrackedItem data blocks the purge through database references.
                      </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                      <DialogClose asChild>
                        <Button type="button" variant="outline">Cancel</Button>
                      </DialogClose>
                      <Button type="button" variant="destructive" onClick={hardPurge} disabled={hardPurgeMutation.isPending}>
                        Confirm hard purge
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
  const bulkSoftDeleteMutation = useBulkSoftDeleteCatalogRows();
  const loadedCatalogRows = rows.data?.pages.flatMap((page) => page.results) ?? [];
  const catalogTotalCount = rows.data?.pages[0]?.count ?? 0;

  useEffect(() => {
    if (!rows.hasNextPage || rows.isFetchingNextPage || rows.isLoading) {
      return undefined;
    }
    const timer = window.setTimeout(() => {
      void rows.fetchNextPage();
    }, 150);
    return () => window.clearTimeout(timer);
  }, [rows.dataUpdatedAt, rows.fetchNextPage, rows.hasNextPage, rows.isFetchingNextPage, rows.isLoading]);

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

  if (sections.isLoading || rows.isLoading) {
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
                inlinePromotion={inlinePromotion}
              />
            ) : null}
            {rowId ? <CertCatalogDetail rowId={rowId} catalogRows={loadedCatalogRows} /> : null}
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
  return (
    (run.mismatchesCount ?? 0)
    + (run.missingInCatalogCount ?? 0)
    + (run.missingInClassCount ?? 0)
    + (run.conditionalStcDetectedCount ?? 0)
    + (run.extendedPostponedDetectedCount ?? 0)
    + (run.unmappedLowConfidenceCount ?? 0)
  );
}

function getReconciliationBucketCount(
  run: CertReconciliationRun,
  countKey: (typeof RECONCILIATION_BUCKET_TABS)[number]['countKey']
): number {
  return Number(run[countKey] ?? 0);
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

function formatJson(value: unknown): string {
  if (value === null || value === undefined) return 'Not recorded';
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function formatJsonCompact(value: unknown): string {
  if (value === null || value === undefined) return 'not recorded';
  if (typeof value === 'string') return value;
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
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
    return item.validityShortCode;
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

function formatShipType(value: string | null | undefined): string {
  if (!value) return 'Ship type not set';
  return value
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatSnapshotAge(snapshot: CertVesselDashboardResponse['lastClassSnapshot']): string {
  if (!snapshot) return 'No class snapshot uploaded';
  if (snapshot.daysAgo === 0) return 'Uploaded today';
  if (snapshot.daysAgo === 1) return 'Uploaded 1 day ago';
  if (typeof snapshot.daysAgo === 'number') return `Uploaded ${snapshot.daysAgo} days ago`;
  return `Uploaded ${formatDate(snapshot.uploadedAt)}`;
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

function formatAuditAction(action: string): string {
  return action
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
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
    return 'Created tracked item.';
  }
  if (entry.before && entry.after) {
    const keys = new Set([...Object.keys(entry.before), ...Object.keys(entry.after)]);
    const changed = Array.from(keys).filter((key) => JSON.stringify(entry.before?.[key]) !== JSON.stringify(entry.after?.[key]));
    return changed.length ? `Changed: ${changed.join(', ')}` : 'No field-level diff.';
  }
  return 'Audit event recorded.';
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

function splitCsv(value: string): string[] {
  const parts = value.split(',').map((part) => part.trim()).filter(Boolean);
  return parts.length > 0 ? parts : ['all'];
}

function parseCsvValues(value: string): string[] {
  return value
    .split(/[\n,]+/)
    .map((part) => part.trim())
    .filter(Boolean);
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

  if (path === ROUTES.CERTS_CATALOG || path.startsWith(`${ROUTES.CERTS_CATALOG}/`)) {
    const rowId = path.startsWith(`${ROUTES.CERTS_CATALOG}/`)
      ? decodeURIComponent(path.slice(`${ROUTES.CERTS_CATALOG}/`.length).split('/').filter(Boolean)[0] ?? '')
      : undefined;
    return <CertCatalogAdminPage rowId={rowId} />;
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

export default CertsDashboardStubPage;
