import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const certsRouteMocks = vi.hoisted(() => ({
  useAuth: vi.fn(),
  useCatalogSections: vi.fn(),
  useCatalogRows: vi.fn(),
  useCatalogRow: vi.fn(),
  useCatalogRowAuditHistory: vi.fn(),
  useBulkSoftDeleteCatalogRows: vi.fn(),
  useCreateCatalogRow: vi.fn(),
  useDeprecateCatalogRow: vi.fn(),
  useHardPurgeCatalogRow: vi.fn(),
  useUpdateCatalogRow: vi.fn(),
  useFleetDashboard: vi.fn(),
  useVesselDashboard: vi.fn(),
  useVesselProfile: vi.fn(),
  useRecordFlagChange: vi.fn(),
  useRecordClassChange: vi.fn(),
  useInitiateSaleHandover: vi.fn(),
  useDecommissionVessel: vi.fn(),
  useTrackedItemDetail: vi.fn(),
  useSubmitTrackedItem: vi.fn(),
  useApproveTrackedItem: vi.fn(),
  useRejectTrackedItem: vi.fn(),
  useUploadTrackedItemPdf: vi.fn(),
  useOnboardingHub: vi.fn(),
  useOnboardingWizardState: vi.fn(),
  useOnboardingBatchGapFill: vi.fn(),
  usePreviewOnboardingBatch: vi.fn(),
  useCommitOnboardingBatch: vi.fn(),
  useSaveOnboardingProfile: vi.fn(),
  useCreateOnboardingBatch: vi.fn(),
  useCoverageOverride: vi.fn(),
  useFmSignoff: vi.fn(),
  useRollbackOnboarding: vi.fn(),
  useClassSnapshots: vi.fn(),
  useReconciliationRuns: vi.fn(),
  useReconciliationRun: vi.fn(),
  useUploadClassSnapshot: vi.fn(),
  useReparseClassSnapshot: vi.fn(),
  useMarkReconciliationFlagReviewed: vi.fn(),
  useNotifyMasterForReconciliationFlag: vi.fn(),
  useAddClassCodeMappingForFlag: vi.fn(),
  useGeneratePrintArtifact: vi.fn(),
  useGenerateShareBundle: vi.fn(),
  usePrintArtifacts: vi.fn(),
  useAuditLog: vi.fn(),
  useExportAuditLog: vi.fn(),
  useAuditorAccessGrants: vi.fn(),
  useAuditorAccessGrant: vi.fn(),
  useCreateAuditorAccessGrant: vi.fn(),
  useUpdateAuditorAccessGrantExpiry: vi.fn(),
  useAuditorSignup: vi.fn(),
  useAuditorVessels: vi.fn(),
  useAuditorVesselCerts: vi.fn(),
  useAuditorCert: vi.fn(),
  useGenerateAuditorPrint: vi.fn(),
  useCertSettings: vi.fn(),
  useUpdateCertSettings: vi.fn(),
}));

vi.mock('@/hooks/use-auth', () => ({
  useAuth: () => certsRouteMocks.useAuth(),
  useRequireAuth: () => ({ isAuthenticated: true, isLoading: false }),
}));

vi.mock('@/components/layout/root-layout', () => ({
  RootLayout: ({ children }: { children: React.ReactNode }) => (
    <main>{children}</main>
  ),
}));

vi.mock('@/components/layout/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <header>{title}</header>,
}));

vi.mock('@/hooks/certs/use-catalog', () => ({
  useCatalogSections: () => certsRouteMocks.useCatalogSections(),
  useCatalogRows: (filters: unknown) => certsRouteMocks.useCatalogRows(filters),
  useCatalogRow: (id: string | undefined) => certsRouteMocks.useCatalogRow(id),
  useCatalogRowAuditHistory: (id: string | undefined) => certsRouteMocks.useCatalogRowAuditHistory(id),
  useBulkSoftDeleteCatalogRows: () => certsRouteMocks.useBulkSoftDeleteCatalogRows(),
  useCreateCatalogRow: () => certsRouteMocks.useCreateCatalogRow(),
  useDeprecateCatalogRow: (id: string) => certsRouteMocks.useDeprecateCatalogRow(id),
  useHardPurgeCatalogRow: (id: string) => certsRouteMocks.useHardPurgeCatalogRow(id),
  useUpdateCatalogRow: (id: string) => certsRouteMocks.useUpdateCatalogRow(id),
}));

vi.mock('@/hooks/certs/use-vessel-dashboard', () => ({
  useFleetDashboard: () => certsRouteMocks.useFleetDashboard(),
  useVesselDashboard: (imo: string | undefined) => certsRouteMocks.useVesselDashboard(imo),
  useVesselProfile: (imo: string | undefined) => certsRouteMocks.useVesselProfile(imo),
  useRecordFlagChange: (imo: string) => certsRouteMocks.useRecordFlagChange(imo),
  useRecordClassChange: (imo: string) => certsRouteMocks.useRecordClassChange(imo),
  useInitiateSaleHandover: (imo: string) => certsRouteMocks.useInitiateSaleHandover(imo),
  useDecommissionVessel: (imo: string) => certsRouteMocks.useDecommissionVessel(imo),
}));

vi.mock('@/hooks/certs/use-tracked-item', () => ({
  useTrackedItemDetail: (id: string | undefined) => certsRouteMocks.useTrackedItemDetail(id),
  useSubmitTrackedItem: (id: string, imo: string) => certsRouteMocks.useSubmitTrackedItem(id, imo),
  useApproveTrackedItem: (id: string, imo: string) => certsRouteMocks.useApproveTrackedItem(id, imo),
  useRejectTrackedItem: (id: string, imo: string) => certsRouteMocks.useRejectTrackedItem(id, imo),
  useUploadTrackedItemPdf: (id: string, imo: string) => certsRouteMocks.useUploadTrackedItemPdf(id, imo),
}));

vi.mock('@/hooks/certs/use-onboarding', () => ({
  useOnboardingHub: () => certsRouteMocks.useOnboardingHub(),
  useOnboardingWizardState: (vesselId: string | undefined) => certsRouteMocks.useOnboardingWizardState(vesselId),
  useOnboardingBatchGapFill: (batchId: string | undefined) => certsRouteMocks.useOnboardingBatchGapFill(batchId),
  usePreviewOnboardingBatch: (batchId: string | undefined) => certsRouteMocks.usePreviewOnboardingBatch(batchId),
  useCommitOnboardingBatch: (batchId: string | undefined) => certsRouteMocks.useCommitOnboardingBatch(batchId),
  useSaveOnboardingProfile: (vesselId: string) => certsRouteMocks.useSaveOnboardingProfile(vesselId),
  useCreateOnboardingBatch: (vesselId: string) => certsRouteMocks.useCreateOnboardingBatch(vesselId),
  useCoverageOverride: (vesselId: string) => certsRouteMocks.useCoverageOverride(vesselId),
  useFmSignoff: (vesselId: string) => certsRouteMocks.useFmSignoff(vesselId),
  useRollbackOnboarding: (vesselId: string) => certsRouteMocks.useRollbackOnboarding(vesselId),
}));

vi.mock('@/hooks/certs/use-reconciliation', () => ({
  useClassSnapshots: (filters: unknown) => certsRouteMocks.useClassSnapshots(filters),
  useReconciliationRuns: (filters: unknown) => certsRouteMocks.useReconciliationRuns(filters),
  useReconciliationRun: (id: string | undefined) => certsRouteMocks.useReconciliationRun(id),
  useUploadClassSnapshot: () => certsRouteMocks.useUploadClassSnapshot(),
  useReparseClassSnapshot: (id: string | undefined) => certsRouteMocks.useReparseClassSnapshot(id),
  useMarkReconciliationFlagReviewed: (runId: string | undefined) => certsRouteMocks.useMarkReconciliationFlagReviewed(runId),
  useNotifyMasterForReconciliationFlag: (runId: string | undefined) => certsRouteMocks.useNotifyMasterForReconciliationFlag(runId),
  useAddClassCodeMappingForFlag: (runId: string | undefined) => certsRouteMocks.useAddClassCodeMappingForFlag(runId),
}));

vi.mock('@/hooks/certs/use-print', () => ({
  useGeneratePrintArtifact: () => certsRouteMocks.useGeneratePrintArtifact(),
  useGenerateShareBundle: () => certsRouteMocks.useGenerateShareBundle(),
  usePrintArtifacts: (filters: unknown) => certsRouteMocks.usePrintArtifacts(filters),
}));

vi.mock('@/hooks/certs/use-audit-log', () => ({
  useAuditLog: (filters: unknown, enabled?: boolean) => certsRouteMocks.useAuditLog(filters, enabled),
  useExportAuditLog: () => certsRouteMocks.useExportAuditLog(),
}));

vi.mock('@/hooks/certs/use-auditor-access', () => ({
  useAuditorAccessGrants: (enabled?: boolean) => certsRouteMocks.useAuditorAccessGrants(enabled),
  useAuditorAccessGrant: (id: string | undefined) => certsRouteMocks.useAuditorAccessGrant(id),
  useCreateAuditorAccessGrant: () => certsRouteMocks.useCreateAuditorAccessGrant(),
  useUpdateAuditorAccessGrantExpiry: (id: string | undefined) => certsRouteMocks.useUpdateAuditorAccessGrantExpiry(id),
  useAuditorSignup: (token: string | undefined) => certsRouteMocks.useAuditorSignup(token),
  useAuditorVessels: (sessionToken: string | undefined) => certsRouteMocks.useAuditorVessels(sessionToken),
  useAuditorVesselCerts: (sessionToken: string | undefined, imo: string | undefined) => certsRouteMocks.useAuditorVesselCerts(sessionToken, imo),
  useAuditorCert: (sessionToken: string | undefined, certId: string | undefined) => certsRouteMocks.useAuditorCert(sessionToken, certId),
  useGenerateAuditorPrint: (sessionToken: string | undefined) => certsRouteMocks.useGenerateAuditorPrint(sessionToken),
}));

vi.mock('@/hooks/certs/use-settings', () => ({
  useCertSettings: (enabled?: boolean) => certsRouteMocks.useCertSettings(enabled),
  useUpdateCertSettings: () => certsRouteMocks.useUpdateCertSettings(),
}));

import { CertsDashboardStubPage } from '../../../src/routes/certs';

function onboardingWizardFixture() {
  return {
    vessel: {
      id: 'vessel-1',
      imo: '9876543',
      code: 'KSMF',
      name: 'KSM Fortitude',
      flag: 'Panama',
      classSociety: 'NK',
    },
    config: {
      vesselId: 'vessel-1',
      anniversaryDate: '2026-01-15',
      shipType: 'bulk_carrier',
      marineSuptUserId: 'marine-1',
      technicalManagerUserId: 'tech-1',
      lifecycleStatus: 'onboarding_in_progress',
      mandatoryCoverageOverrideReason: null,
      mandatoryCoverageOverrideAt: null,
      mandatoryCoverageOverrideBy: null,
      updatedAt: '2026-06-26T09:00:00Z',
      updatedBy: 'dpa-1',
    },
    steps: [
      { number: 1, label: 'Vessel selection', status: 'complete' },
      { number: 2, label: 'Vessel profile', status: 'complete' },
      { number: 3, label: 'Cert PDF batch ingest', status: 'current' },
      { number: 4, label: 'Class status upload', status: 'locked' },
      { number: 5, label: 'Reconciliation review', status: 'locked' },
      { number: 6, label: 'Coverage gate', status: 'locked' },
      { number: 7, label: 'FM sign-off', status: 'locked' },
    ],
    currentStep: 3,
    batches: [
      {
        id: 'batch-1',
        onboardingSessionId: 'session-1',
        pdfBlobIds: ['blob-1'],
        pdfCount: 1,
        status: 'ready_for_review',
        createdAt: '2026-06-26T09:00:00Z',
        createdBy: 'dpa-1',
        ocrCompletedAt: '2026-06-26T09:05:00Z',
        reviewStartedAt: null,
        committedAt: null,
        committedBy: null,
        cancelledAt: null,
        cancelledBy: null,
        validationBlocks: [],
        validationWarns: [],
        reportCsvBlobId: null,
      },
    ],
    mandatoryCoverage: {
      percent: 50,
      mandatoryCount: 2,
      coveredCount: 1,
      missing: [],
      overrideActive: false,
      overrideReason: null,
      overrideAt: null,
      overrideBy: null,
    },
    trackedItems: [],
  };
}

describe('Certs route stub', () => {
  beforeEach(() => {
    certsRouteMocks.useAuth.mockReset();
    certsRouteMocks.useCatalogSections.mockReset();
    certsRouteMocks.useCatalogRows.mockReset();
    certsRouteMocks.useCatalogRow.mockReset();
    certsRouteMocks.useCatalogRowAuditHistory.mockReset();
    certsRouteMocks.useBulkSoftDeleteCatalogRows.mockReset();
    certsRouteMocks.useCreateCatalogRow.mockReset();
    certsRouteMocks.useDeprecateCatalogRow.mockReset();
    certsRouteMocks.useHardPurgeCatalogRow.mockReset();
    certsRouteMocks.useUpdateCatalogRow.mockReset();
    certsRouteMocks.useFleetDashboard.mockReset();
    certsRouteMocks.useVesselDashboard.mockReset();
    certsRouteMocks.useVesselProfile.mockReset();
    certsRouteMocks.useRecordFlagChange.mockReset();
    certsRouteMocks.useRecordClassChange.mockReset();
    certsRouteMocks.useInitiateSaleHandover.mockReset();
    certsRouteMocks.useDecommissionVessel.mockReset();
    certsRouteMocks.useTrackedItemDetail.mockReset();
    certsRouteMocks.useSubmitTrackedItem.mockReset();
    certsRouteMocks.useApproveTrackedItem.mockReset();
    certsRouteMocks.useRejectTrackedItem.mockReset();
    certsRouteMocks.useUploadTrackedItemPdf.mockReset();
    certsRouteMocks.useOnboardingHub.mockReset();
    certsRouteMocks.useOnboardingWizardState.mockReset();
    certsRouteMocks.useOnboardingBatchGapFill.mockReset();
    certsRouteMocks.usePreviewOnboardingBatch.mockReset();
    certsRouteMocks.useCommitOnboardingBatch.mockReset();
    certsRouteMocks.useSaveOnboardingProfile.mockReset();
    certsRouteMocks.useCreateOnboardingBatch.mockReset();
    certsRouteMocks.useCoverageOverride.mockReset();
    certsRouteMocks.useFmSignoff.mockReset();
    certsRouteMocks.useRollbackOnboarding.mockReset();
    certsRouteMocks.useClassSnapshots.mockReset();
    certsRouteMocks.useReconciliationRuns.mockReset();
    certsRouteMocks.useReconciliationRun.mockReset();
    certsRouteMocks.useUploadClassSnapshot.mockReset();
    certsRouteMocks.useReparseClassSnapshot.mockReset();
    certsRouteMocks.useMarkReconciliationFlagReviewed.mockReset();
    certsRouteMocks.useNotifyMasterForReconciliationFlag.mockReset();
    certsRouteMocks.useAddClassCodeMappingForFlag.mockReset();
    certsRouteMocks.useGeneratePrintArtifact.mockReset();
    certsRouteMocks.useGenerateShareBundle.mockReset();
    certsRouteMocks.usePrintArtifacts.mockReset();
    certsRouteMocks.useAuditLog.mockReset();
    certsRouteMocks.useExportAuditLog.mockReset();
    certsRouteMocks.useAuditorAccessGrants.mockReset();
    certsRouteMocks.useAuditorAccessGrant.mockReset();
    certsRouteMocks.useCreateAuditorAccessGrant.mockReset();
    certsRouteMocks.useUpdateAuditorAccessGrantExpiry.mockReset();
    certsRouteMocks.useAuditorSignup.mockReset();
    certsRouteMocks.useAuditorVessels.mockReset();
    certsRouteMocks.useAuditorVesselCerts.mockReset();
    certsRouteMocks.useAuditorCert.mockReset();
    certsRouteMocks.useGenerateAuditorPrint.mockReset();
    certsRouteMocks.useCertSettings.mockReset();
    certsRouteMocks.useUpdateCertSettings.mockReset();
    certsRouteMocks.useRecordFlagChange.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useRecordClassChange.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useInitiateSaleHandover.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useDecommissionVessel.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useCatalogSections.mockReturnValue({
      data: [],
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRows.mockReturnValue({
      data: { count: 0, results: [] },
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRow.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRowAuditHistory.mockReturnValue({
      data: [],
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useBulkSoftDeleteCatalogRows.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: vi.fn(),
    });
    certsRouteMocks.useCreateCatalogRow.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: vi.fn(),
    });
    certsRouteMocks.useDeprecateCatalogRow.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: vi.fn(),
    });
    certsRouteMocks.useHardPurgeCatalogRow.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: vi.fn(),
    });
    certsRouteMocks.useUpdateCatalogRow.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: vi.fn(),
    });
    certsRouteMocks.useFleetDashboard.mockReturnValue({
      data: {
        highVolumePrintActivity: { thresholdPerHour: 10, windowMinutes: 60, usersAboveThresholdCount: 0, users: [] },
        bouncingEmailDelivery: { bouncingUsersCount: 0, users: [] },
        cadenceHeartbeat: { lastCadenceHeartbeat: '2026-06-29T09:15:00Z' },
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useVesselDashboard.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useTrackedItemDetail.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useSubmitTrackedItem.mockReturnValue({
      mutate: vi.fn(),
      error: null,
      isPending: false,
    });
    certsRouteMocks.useApproveTrackedItem.mockReturnValue({
      mutate: vi.fn(),
      error: null,
      isPending: false,
    });
    certsRouteMocks.useRejectTrackedItem.mockReturnValue({
      mutate: vi.fn(),
      error: null,
      isPending: false,
    });
    certsRouteMocks.useUploadTrackedItemPdf.mockReturnValue({
      mutate: vi.fn(),
      error: null,
      isPending: false,
    });
    certsRouteMocks.useOnboardingHub.mockReturnValue({
      data: { results: [] },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useOnboardingWizardState.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useOnboardingBatchGapFill.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.usePreviewOnboardingBatch.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useCommitOnboardingBatch.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useSaveOnboardingProfile.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useCreateOnboardingBatch.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useCoverageOverride.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useFmSignoff.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useRollbackOnboarding.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useClassSnapshots.mockReturnValue({
      data: { count: 0, results: [] },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useReconciliationRuns.mockReturnValue({
      data: { count: 0, results: [] },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useReconciliationRun.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useUploadClassSnapshot.mockReturnValue({ mutate: vi.fn(), error: null, isError: false, isPending: false, isSuccess: false });
    certsRouteMocks.useReparseClassSnapshot.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useMarkReconciliationFlagReviewed.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useNotifyMasterForReconciliationFlag.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useAddClassCodeMappingForFlag.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useGeneratePrintArtifact.mockReturnValue({ mutate: vi.fn(), data: undefined, error: null, isError: false, isPending: false });
    certsRouteMocks.useGenerateShareBundle.mockReturnValue({ mutate: vi.fn(), data: undefined, error: null, isError: false, isPending: false });
    certsRouteMocks.usePrintArtifacts.mockReturnValue({
      data: { results: [] },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useAuditLog.mockReturnValue({
      data: { count: 0, page: 1, pageSize: 25, includesColdTier: false, results: [] },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useExportAuditLog.mockReturnValue({
      mutate: vi.fn(),
      data: undefined,
      error: null,
      isError: false,
      isPending: false,
    });
    certsRouteMocks.useAuditorAccessGrants.mockReturnValue({
      data: { results: [] },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useAuditorAccessGrant.mockReturnValue({
      data: undefined,
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCreateAuditorAccessGrant.mockReturnValue({ mutate: vi.fn(), data: undefined, error: null, isError: false, isPending: false });
    certsRouteMocks.useUpdateAuditorAccessGrantExpiry.mockReturnValue({ mutate: vi.fn(), data: undefined, error: null, isError: false, isPending: false });
    certsRouteMocks.useAuditorSignup.mockReturnValue({ data: { sessionToken: 'session-token', grant: {} }, error: null, isError: false, isLoading: false });
    certsRouteMocks.useAuditorVessels.mockReturnValue({ data: { results: [] }, error: null, isError: false, isLoading: false });
    certsRouteMocks.useAuditorVesselCerts.mockReturnValue({ data: { results: [] }, error: null, isError: false, isLoading: false });
    certsRouteMocks.useAuditorCert.mockReturnValue({ data: undefined, error: null, isError: false, isLoading: false });
    certsRouteMocks.useGenerateAuditorPrint.mockReturnValue({ mutate: vi.fn(), data: undefined, error: null, isError: false, isPending: false });
    certsRouteMocks.useCertSettings.mockReturnValue({
      data: {
        id: 'settings-1',
        singletonKey: 'certs',
        lastHeartbeatAt: '2026-06-30T01:00:00Z',
        updatedAt: '2026-06-30T01:00:00Z',
        updatedBy: 'dpa-1',
        alertConfigs: [
          {
            id: 'alert-1',
            triggerEvent: 'certificate_expiry',
            defaultLeadDays: 90,
            dpaOverrideLeadDays: 75,
            recipientsDefault: ['DPA', 'Fleet Manager'],
            dpaOverrideRecipients: ['DPA'],
            escalationCadence: { levels: [30, 14, 7] },
            ocrThresholdOffice: 0.8,
            ocrThresholdVessel: 0.85,
            ocrThresholdManualFloor: 0.6,
            classSnapshotCadenceMonths: 3,
            classSnapshotLeadMonths: 1,
            eventSnapshotGraceDays: 14,
            draftExpireDays: 7,
            createdAt: '2026-06-30T00:00:00Z',
            updatedAt: '2026-06-30T00:00:00Z',
            updatedBy: 'dpa-1',
          },
        ],
        slackRoutes: [
          {
            vesselId: 'vessel-1',
            vesselName: 'KSM Fortitude',
            imo: '9876543',
            slackChannelVessel: '#certs-ksmf',
            slackChannelOfficeDefault: '#certs-office',
            updatedAt: '2026-06-30T00:00:00Z',
            updatedBy: 'dpa-1',
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useUpdateCertSettings.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
  });

  it('renders the Step 0.6 stub when the user has a Certs form id', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      vesselId: 'vessel-1',
      user: { vessel_id: 'vessel-1' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_002'),
      hasProcess: vi.fn(() => false),
    });

    render(
      <MemoryRouter>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(
      screen.getByRole('heading', { name: 'Certs module coming soon' })
    ).toBeInTheDocument();
    expect(
      screen.queryByText("You don't have access to this page.")
    ).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /open catalog/i })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /open vessel certificates/i })).toHaveAttribute('href', '/certs/vessels/vessel-1');
  });

  it('shows the catalog landing action only to Catalog Admin readers', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn(() => false),
    });

    render(
      <MemoryRouter>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: /open catalog/i })).toHaveAttribute('href', '/certs/catalog');
    expect(screen.queryByRole('link', { name: /open vessel certificates/i })).not.toBeInTheDocument();
  });

  it('renders the FM-only high-volume print activity card on the fleet dashboard', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_004'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useFleetDashboard.mockReturnValue({
      data: {
        highVolumePrintActivity: {
          thresholdPerHour: 10,
          windowMinutes: 60,
          usersAboveThresholdCount: 1,
          users: [
            {
              userId: 'fm-1',
              userRole: 'Fleet Manager',
              printCountLastHour: 11,
              lastPrintAt: '2026-06-29T10:15:00Z',
              lastSignalAt: '2026-06-29T10:15:01Z',
            },
          ],
        },
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'High-volume print activity' })).toBeInTheDocument();
    expect(screen.getByText('1 user above 10 prints/hour')).toBeInTheDocument();
    expect(screen.getByText('fm-1')).toBeInTheDocument();
    expect(screen.getByText('11 prints')).toBeInTheDocument();
  });

  it('renders the DPA-only bouncing email delivery card on the fleet dashboard', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_002'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useFleetDashboard.mockReturnValue({
      data: {
        bouncingEmailDelivery: {
          bouncingUsersCount: 2,
          users: [
            {
              userId: 'master-1',
              lastBouncedAt: '2026-06-29T11:30:00Z',
              criticalFallbackCount: 1,
            },
            {
              userId: 'ce-1',
              lastBouncedAt: '2026-06-29T11:35:00Z',
              criticalFallbackCount: 0,
            },
          ],
        },
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Bouncing email delivery' })).toBeInTheDocument();
    expect(screen.getByText('2 users with failing email')).toBeInTheDocument();
    expect(screen.getByText('master-1')).toBeInTheDocument();
    expect(screen.getByText('1 critical fallback')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'High-volume print activity' })).not.toBeInTheDocument();
  });

  it('renders the DPA-only stale cadence heartbeat tile on the fleet dashboard', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-06-29T12:30:00Z'));
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_002'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useFleetDashboard.mockReturnValue({
      data: {
        cadenceHeartbeat: {
          lastCadenceHeartbeat: '2026-06-29T09:15:00Z',
        },
        bouncingEmailDelivery: { bouncingUsersCount: 0, users: [] },
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Cadence heartbeat' })).toBeInTheDocument();
    expect(screen.getByText('Heartbeat stale')).toBeInTheDocument();
    expect(screen.getByText('Last heartbeat 29 Jun 2026, 14:45')).toBeInTheDocument();
    vi.useRealTimers();
  });

  it('renders the documented 403 state when the user lacks Certs form access', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      hasForm: vi.fn(() => false),
      hasProcess: vi.fn(() => false),
    });

    render(
      <MemoryRouter>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(
      screen.getByRole('heading', { name: "You don't have access to this page." })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Back to Fleet Dashboard' })
    ).toHaveAttribute('href', '/dashboard');
  });

  it('renders DPA settings and saves alert config plus Slack routing', () => {
    const mutate = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_006'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });
    certsRouteMocks.useUpdateCertSettings.mockReturnValue({ mutate, error: null, isPending: false });

    render(
      <MemoryRouter initialEntries={['/certs/settings']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Certs Settings' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'OCR thresholds' }));
    fireEvent.change(screen.getByLabelText('Office OCR threshold'), { target: { value: '0.820' } });
    fireEvent.click(screen.getByRole('button', { name: 'Slack routing' }));
    fireEvent.change(screen.getByLabelText('Vessel Slack channel'), { target: { value: '#certs-fortitude' } });
    fireEvent.change(screen.getByLabelText('Change reason'), {
      target: { value: 'DPA adjusted alert thresholds and Slack routing.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save settings' }));

    expect(mutate).toHaveBeenCalledWith(expect.objectContaining({
      reason: 'DPA adjusted alert thresholds and Slack routing.',
      alertConfigs: [expect.objectContaining({ id: 'alert-1', ocrThresholdOffice: '0.820' })],
      slackRoutes: [expect.objectContaining({ vesselId: 'vessel-1', slackChannelVessel: '#certs-fortitude' })],
    }));
  });

  it('blocks non-DPA users from the settings route', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_006'),
      hasProcess: vi.fn(() => true),
    });

    render(
      <MemoryRouter initialEntries={['/certs/settings']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: "You don't have access to this page." })).toBeInTheDocument();
    expect(certsRouteMocks.useCertSettings).not.toHaveBeenCalled();
  });

  it('renders class reconciliation runs and snapshots at /certs/reconciliation', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_003'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_001'),
    });
    certsRouteMocks.useReconciliationRuns.mockReturnValue({
      data: {
        count: 1,
        results: [
          {
            id: 'run-1',
            snapshotId: 'snapshot-1',
            vesselId: 'vessel-1',
            vesselName: 'KSM Fortitude',
            imo: '9876543',
            classSociety: 'NK',
            printedOnDate: '2026-06-01',
            parseStatus: 'success',
            parserVersion: 'nk-parser-v1',
            ranAt: '2026-06-26T09:00:00Z',
            matchesCount: 2,
            mismatchesCount: 1,
            missingInCatalogCount: 0,
            missingInClassCount: 0,
            conditionalStcDetectedCount: 0,
            extendedPostponedDetectedCount: 0,
            unmappedLowConfidenceCount: 0,
            notificationsSent: [],
            mappingVersionUsed: 3,
            anomalyBreaches: [],
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useClassSnapshots.mockReturnValue({
      data: {
        count: 1,
        results: [
          {
            id: 'snapshot-1',
            vesselId: 'vessel-1',
            vesselName: 'KSM Fortitude',
            imo: '9876543',
            classSociety: 'NK',
            pdfBlobId: 'blob-1',
            filename: 'class-status.pdf',
            sizeBytes: 2048,
            printedOnDate: '2026-06-01',
            uploadedBy: 'dpa-1',
            uploadedAt: '2026-06-26T08:55:00Z',
            parserVersion: 'pending-parser-v1',
            parseStatus: 'success',
            parseStartedAt: null,
            parseCompletedAt: null,
            parserTimeout: false,
            retryCount: 0,
            parsedPayload: null,
            parsedPayloadSchemaVersion: 1,
            reconciliationRunId: 'run-1',
            uploadSha256: 'abc',
            supersededUserError: false,
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/reconciliation']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Reconciliation runs')).toBeInTheDocument();
    expect(screen.getByText('KSM Fortitude')).toBeInTheDocument();
    expect(screen.getByText('class-status.pdf')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Review' })).toHaveAttribute('href', '/certs/reconciliation/run-1');
    expect(certsRouteMocks.useReconciliationRuns).toHaveBeenCalledWith({ bucket: null });
  });

  it('renders Print Builder and submits a per-vessel print payload', () => {
    const mutate = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_004'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_005'),
    });
    certsRouteMocks.useGeneratePrintArtifact.mockReturnValue({
      mutate,
      data: {
        printId: 'SQE-S633-9876543-20260629-001',
        scope: 'per_vessel_full',
        vessels: ['11111111-1111-1111-1111-111111111111'],
        sections: [],
        filters: {},
        customCertIds: [],
        userId: 'dpa-1',
        userRole: 'DPA',
        timestampUtc: '2026-06-29T10:00:00Z',
        systemStateHash: 'abc12345',
        watermarkApplied: 'INTERNAL',
        watermarkRecipient: '',
        pdfBlobId: 'pdf-blob',
        excelBlobId: 'excel-blob',
        bundleZipBlobId: null,
        recipientEmail: '',
        pageCount: 2,
        generationStatus: 'success',
        failureMessage: '',
      },
      error: null,
      isError: false,
      isPending: false,
    });

    render(
      <MemoryRouter initialEntries={['/certs/print?vesselId=11111111-1111-1111-1111-111111111111']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('SQE S 633 export')).toBeInTheDocument();
    expect(screen.getByLabelText('Vessel IDs')).toHaveValue('11111111-1111-1111-1111-111111111111');
    fireEvent.click(screen.getByRole('button', { name: /Generate PDF and Excel/i }));
    expect(mutate).toHaveBeenCalledWith(expect.objectContaining({
      scope: 'per_vessel_full',
      vesselIds: ['11111111-1111-1111-1111-111111111111'],
    }));
    expect(screen.getByText('SQE-S633-9876543-20260629-001')).toBeInTheDocument();
  });

  it('renders Print History artifact rows', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_004'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.usePrintArtifacts.mockReturnValue({
      data: {
        results: [
          {
            printId: 'SQE-S633-9876543-20260629-001',
            scope: 'per_vessel_full',
            vessels: ['vessel-1'],
            sections: [],
            filters: {},
            customCertIds: [],
            userId: 'dpa-1',
            userRole: 'DPA',
            timestampUtc: '2026-06-29T10:00:00Z',
            systemStateHash: 'abc12345',
            watermarkApplied: 'INTERNAL',
            watermarkRecipient: '',
            pdfBlobId: 'pdf-blob',
            excelBlobId: 'excel-blob',
            bundleZipBlobId: null,
            recipientEmail: '',
            pageCount: 2,
            generationStatus: 'success',
            failureMessage: '',
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/print/history']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Print History')).toBeInTheDocument();
    expect(screen.getByText('SQE-S633-9876543-20260629-001')).toBeInTheDocument();
    expect(screen.getByText('Per Vessel Full')).toBeInTheDocument();
  });

  it('renders failed Print History rows with support ticket and manual retry', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_004'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.usePrintArtifacts.mockReturnValue({
      data: {
        results: [
          {
            printId: 'SQE-S633-9876543-20260629-013',
            scope: 'per_vessel_full',
            vessels: ['vessel-1'],
            sections: [],
            filters: {},
            customCertIds: [],
            userId: 'dpa-1',
            userRole: 'DPA',
            timestampUtc: '2026-06-29T10:00:00Z',
            systemStateHash: 'abc12345',
            watermarkApplied: 'INTERNAL',
            watermarkRecipient: '',
            pdfBlobId: null,
            excelBlobId: null,
            bundleZipBlobId: null,
            recipientEmail: '',
            pageCount: 0,
            generationStatus: 'failed',
            failureMessage: 'Generation failed. Support ticket SQE-S633-9876543-20260629-013-ERR was logged. Retry manually.',
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/print/history']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText(/Support ticket SQE-S633-9876543-20260629-013-ERR/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Retry manually/i })).toHaveAttribute('href', '/certs/print');
  });

  it('renders Share Bundle and submits selected certificate IDs', () => {
    const mutate = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'VESSEL_MASTER',
      user: { role_name: 'VESSEL_MASTER' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_004'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_006'),
    });
    certsRouteMocks.useGenerateShareBundle.mockReturnValue({
      mutate,
      data: undefined,
      error: null,
      isError: false,
      isPending: false,
    });

    render(
      <MemoryRouter initialEntries={['/certs/share-bundle?vesselId=11111111-1111-1111-1111-111111111111']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('Certificate IDs'), {
      target: { value: '22222222-2222-2222-2222-222222222222' },
    });
    fireEvent.change(screen.getByLabelText('Recipient name'), {
      target: { value: 'Port State Inspector' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Generate ZIP bundle/i }));

    expect(mutate).toHaveBeenCalledWith({
      vesselIds: ['11111111-1111-1111-1111-111111111111'],
      customCertIds: ['22222222-2222-2222-2222-222222222222'],
      watermarkRecipient: 'Port State Inspector',
      recipientEmail: '',
    });
  });

  it('renders reconciliation 3-panel review controls at /certs/reconciliation/<runId>', () => {
    const notifyMaster = vi.fn();
    const markReviewed = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Marine Superintendent',
      user: { role_name: 'Marine Superintendent' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_003'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_002'),
    });
    certsRouteMocks.useNotifyMasterForReconciliationFlag.mockReturnValue({
      mutate: notifyMaster,
      error: null,
      isPending: false,
    });
    certsRouteMocks.useMarkReconciliationFlagReviewed.mockReturnValue({
      mutate: markReviewed,
      error: null,
      isPending: false,
    });
    certsRouteMocks.useReconciliationRun.mockReturnValue({
      data: {
        id: 'run-1',
        snapshotId: 'snapshot-1',
        vesselId: 'vessel-1',
        vesselName: 'KSM Fortitude',
        imo: '9876543',
        classSociety: 'NK',
        printedOnDate: '2026-06-01',
        parseStatus: 'success',
        parserVersion: 'nk-parser-v1',
        ranAt: '2026-06-26T09:00:00Z',
        matchesCount: 1,
        mismatchesCount: 1,
        missingInCatalogCount: 0,
        missingInClassCount: 0,
        conditionalStcDetectedCount: 0,
        extendedPostponedDetectedCount: 1,
        unmappedLowConfidenceCount: 0,
        notificationsSent: [],
        mappingVersionUsed: 3,
        anomalyBreaches: [
          {
            type: 'mismatch_rate',
            severity: 'critical',
            value: 0.22,
            threshold: 0.15,
            count: 2,
            total: 9,
            message: 'Mismatch rate exceeded the D-CERT-073 15% threshold.',
          },
        ],
        flags: [
          {
            id: 'flag-match',
            runId: 'run-1',
            bucket: 'match',
            catalogId: 'catalog-match',
            catalogDisplayName: 'Load Line Certificate',
            trackedItemId: 'tracked-match',
            classRowExtract: { class_code_or_name: 'LOADLINE', expiry_date: '2031-03-01' },
            diff: {},
            reviewedBy: null,
            reviewedAt: null,
            resolutionAction: null,
            resolvedAt: null,
          },
          {
            id: 'flag-1',
            runId: 'run-1',
            bucket: 'mismatch',
            catalogId: 'catalog-1',
            catalogDisplayName: 'IOPP Certificate',
            trackedItemId: 'tracked-1',
            classRowExtract: { class_code_or_name: 'IOPP', expiry_date: '2031-01-01' },
            diff: { expiry_date: { class: '2031-01-01', tracked: '2030-01-01' } },
            reviewedBy: null,
            reviewedAt: null,
            resolutionAction: null,
            resolvedAt: null,
          },
          {
            id: 'flag-extended',
            runId: 'run-1',
            bucket: 'extended_postponed',
            catalogId: 'catalog-2',
            catalogDisplayName: 'Class Annual Survey',
            trackedItemId: 'tracked-2',
            classRowExtract: { class_code_or_name: 'ANNUAL', postponed_until: '2026-12-31' },
            diff: { postponed_until: { class: '2026-12-31', tracked: null } },
            reviewedBy: null,
            reviewedAt: null,
            resolutionAction: null,
            resolvedAt: null,
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/reconciliation/run-1']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('tab', { name: /Mismatches 1/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getAllByText('IOPP Certificate').length).toBeGreaterThan(1);
    expect(screen.getByText('Parser anomaly threshold breached')).toBeInTheDocument();
    expect(screen.getByText(/Mismatch rate exceeded the D-CERT-073 15% threshold. 22.0% measured, threshold 15.0%/)).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Catalog and tracked item state' })).toHaveTextContent('tracked-1');
    expect(screen.getByRole('region', { name: 'Class snapshot extracted state' })).toHaveTextContent('2031-01-01');
    expect(screen.getAllByText('expiry date').length).toBeGreaterThan(1);
    expect(screen.getByText('2030-01-01')).toBeInTheDocument();
    expect(screen.getAllByText('2031-01-01').length).toBeGreaterThan(1);
    expect(screen.getByRole('link', { name: 'Resolve via Master upload' })).toHaveAttribute('href', '/certs/vessels/9876543/cert/tracked-1');
    expect(screen.getByLabelText('Review reason')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Notify Master' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Mark reviewed' })).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Review reason'), {
      target: { value: 'Master must upload the updated IOPP certificate.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Notify Master' }));
    expect(notifyMaster).toHaveBeenCalledWith({
      flagId: 'flag-1',
      reason: 'Master must upload the updated IOPP certificate.',
    });

    fireEvent.click(screen.getByRole('tab', { name: /Extended\/Postponed detected 1/i }));
    expect(screen.getByText('Extended/postponed row detected. Review the class extract before notifying the Master to upload extension evidence.')).toBeInTheDocument();
    expect(certsRouteMocks.useReconciliationRun).toHaveBeenCalledWith('run-1');
  });

  it('lets DPA add an unmapped class row to ClassCodeMapping', () => {
    const addMapping = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_003'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });
    certsRouteMocks.useAddClassCodeMappingForFlag.mockReturnValue({
      mutate: addMapping,
      error: null,
      isPending: false,
    });
    certsRouteMocks.useCatalogRows.mockReturnValue({
      data: {
        count: 1,
        results: [
          {
            id: 'catalog-iopp',
            canonicalCode: 'CLASS-IOPP',
            displayName: 'IOPP Certificate',
            sectionId: 1,
            printSectionLabel: 'Class Certificates',
            validityType: 'full',
            cadenceMonths: 60,
            cadenceCustomDays: null,
            issuingAuthorityType: 'class',
            isClassTracked: true,
            submissionScope: 'master_only',
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: true,
            printOrder: 1,
            isActive: true,
          },
        ],
      },
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useReconciliationRun.mockReturnValue({
      data: {
        id: 'run-1',
        snapshotId: 'snapshot-1',
        vesselId: 'vessel-1',
        vesselName: 'KSM Fortitude',
        imo: '9876543',
        classSociety: 'NK',
        printedOnDate: '2026-06-01',
        parseStatus: 'success',
        parserVersion: 'nk-parser-v1',
        ranAt: '2026-06-26T09:00:00Z',
        matchesCount: 0,
        mismatchesCount: 0,
        missingInCatalogCount: 1,
        missingInClassCount: 0,
        conditionalStcDetectedCount: 0,
        extendedPostponedDetectedCount: 0,
        unmappedLowConfidenceCount: 0,
        notificationsSent: [],
        mappingVersionUsed: 3,
        anomalyBreaches: [],
        flags: [
          {
            id: 'flag-unmapped',
            runId: 'run-1',
            bucket: 'missing_in_catalog',
            catalogId: null,
            catalogDisplayName: null,
            trackedItemId: null,
            classRowExtract: { class_code_or_name: 'IOPP', certificate_number: 'NK-001' },
            diff: {},
            reviewedBy: null,
            reviewedAt: null,
            resolutionAction: null,
            resolvedAt: null,
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/reconciliation/run-1']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Add to ClassCodeMapping' }));
    fireEvent.click(screen.getByRole('button', { name: /IOPP Certificate/i }));
    fireEvent.change(screen.getByLabelText('Mapping reason'), {
      target: { value: 'DPA mapped the NK IOPP row after class-status review.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save mapping' }));

    expect(addMapping).toHaveBeenCalledWith(
      {
        flagId: 'flag-unmapped',
        payload: {
          catalogId: 'catalog-iopp',
          certOrSurveyKind: 'renewal',
          notes: null,
          reason: 'DPA mapped the NK IOPP row after class-status review.',
        },
      },
      expect.any(Object)
    );
    expect(certsRouteMocks.useAddClassCodeMappingForFlag).toHaveBeenCalledWith('run-1');
  });

  it('renders the dev parser ops page for Technical Superintendent', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Technical Superintendent',
      user: { role_name: 'Technical Superintendent' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_003'),
      hasProcess: vi.fn(),
    });
    certsRouteMocks.useClassSnapshots.mockReturnValue({
      data: {
        count: 1,
        results: [
          {
            id: 'snapshot-ops-1',
            vesselId: 'vessel-1',
            vesselName: 'KSM Fortitude',
            imo: '9876543',
            classSociety: 'NK',
            pdfBlobId: 'blob-1',
            filename: 'class-status.pdf',
            sizeBytes: 2048,
            printedOnDate: '2026-06-01',
            uploadedBy: 'dpa-1',
            uploadedAt: '2026-06-26T08:55:00Z',
            parserVersion: 'nk-parser-v1',
            parseStatus: 'success',
            parseStartedAt: '2026-06-26T08:55:00Z',
            parseCompletedAt: '2026-06-26T08:58:10Z',
            parserTimeout: false,
            retryCount: 1,
            parsedPayload: null,
            parsedPayloadSchemaVersion: 1,
            reconciliationRunId: 'run-ops-1',
            uploadSha256: 'abc',
            supersededUserError: false,
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useReconciliationRuns.mockReturnValue({
      data: {
        count: 1,
        results: [
          {
            id: 'run-ops-1',
            snapshotId: 'snapshot-ops-1',
            vesselId: 'vessel-1',
            vesselName: 'KSM Fortitude',
            imo: '9876543',
            classSociety: 'NK',
            printedOnDate: '2026-06-01',
            parseStatus: 'success',
            parserVersion: 'nk-parser-v1',
            ranAt: '2026-06-26T09:00:00Z',
            matchesCount: 2,
            mismatchesCount: 2,
            missingInCatalogCount: 0,
            missingInClassCount: 0,
            conditionalStcDetectedCount: 0,
            extendedPostponedDetectedCount: 0,
            unmappedLowConfidenceCount: 0,
            notificationsSent: [],
            mappingVersionUsed: 3,
            anomalyBreaches: [
              {
                type: 'parse_duration',
                severity: 'critical',
                valueSeconds: 190,
                thresholdSeconds: 180,
                message: 'Class snapshot parse duration exceeded 3 minutes.',
              },
            ],
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/reconciliation/parser-ops']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Parser Ops')).toBeInTheDocument();
    expect(screen.getByText('OBS-CERT-04 anomaly runs')).toBeInTheDocument();
    expect(screen.getByText(/Class snapshot parse duration exceeded 3 minutes. 3m 10s measured, threshold 3m./)).toBeInTheDocument();
    expect(screen.getByText('class-status.pdf')).toBeInTheDocument();
    expect(certsRouteMocks.useClassSnapshots).toHaveBeenCalledWith({ pageSize: 100 });
    expect(certsRouteMocks.useReconciliationRuns).toHaveBeenCalledWith({ pageSize: 100 });
  });

  it('renders the Vessel Cert Dashboard grouped by section at /certs/vessels/<imo>', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => ['CERT_F_002', 'CERT_F_003', 'CERT_F_004'].includes(formId)),
      hasProcess: vi.fn((processId: string) => ['CERT_P_001', 'CERT_P_005', 'CERT_P_006'].includes(processId)),
    });
    certsRouteMocks.useVesselDashboard.mockReturnValue({
      data: {
        vessel: {
          id: 'vessel-1',
          imo: '9876543',
          code: 'KSMF',
          name: 'KSM Fortitude',
          flag: 'Panama',
          classSociety: 'NK',
          shipType: 'bulk_carrier',
          currentMaster: 'Captain Anil',
          lifecycleStatus: 'active',
          pendingDisposalStartedAt: null,
          flagChangePending: false,
          iwsAgeGateDisabled: false,
        },
        mandatoryCoverage: {
          percent: 50,
          mandatoryCount: 2,
          coveredCount: 1,
          overrideActive: false,
          overrideReason: null,
          overrideAt: null,
          overrideBy: null,
        },
        lastClassSnapshot: {
          id: 'snapshot-1',
          classSociety: 'NK',
          uploadedAt: '2026-06-24T00:00:00Z',
          daysAgo: 1,
          parseStatus: 'success',
          reconciliationRunId: null,
        },
        summary: {
          totalTrackedItems: 2,
          actionItemCount: 1,
          pdfMissingCount: 1,
          classTrackedCount: 1,
        },
        sections: [
          {
            sectionId: 1,
            sectionCode: 'CLASS',
            displayName: 'Class Certificates',
            activeTrackedItemCount: 1,
            actionItemCount: 0,
            statusBreakdown: { ok: 1 },
            items: [
              {
                id: 'tracked-1',
                vesselId: 'vessel-1',
                catalogId: 'catalog-1',
                catalogCode: 'CLASS-COC',
                catalogDisplayName: 'Certificate of Class',
                catalogShortName: 'COC',
                displayName: 'Certificate of Class',
                shortName: 'COC',
                submissionScope: 'master_only',
                type: 'certificate',
                validityType: 'full',
                validityShortCode: '5-Y',
                formVariant: null,
                cadenceMonths: 60,
                cadenceCustomDays: null,
                parentId: null,
                relationshipType: null,
                supersedesId: null,
                issueDate: '2026-01-01',
                expiryDate: '2031-01-01',
                anniversaryDate: '2026-01-01',
                windowOpen: null,
                windowClose: null,
                lastDoneDate: null,
                nextDueDate: '2031-01-01',
                postponedUntil: null,
                status: 'ok',
                certificateNumber: 'COC-001',
                issuingAuthority: 'NK',
                placeOfIssue: 'Tokyo',
                extensionAuthority: null,
                extensionLetterPdfId: null,
                extensionReason: null,
                pdfAttachmentId: 'pdf-1',
                pdfMissing: false,
                source: 'manual',
                lastClassSyncId: null,
                approvalState: 'approved',
                rejectionReason: null,
                lifecycleStatus: 'active',
                rowVersion: '0001',
                version: 1,
                daysToGo: 1648,
                isClassTracked: true,
                mandatoryForAllVessels: true,
              },
            ],
          },
          {
            sectionId: 2,
            sectionCode: 'STATUTORY',
            displayName: 'Statutory & Flag',
            activeTrackedItemCount: 1,
            actionItemCount: 1,
            statusBreakdown: { pending_first_upload: 1 },
            items: [
              {
                id: 'tracked-2',
                vesselId: 'vessel-1',
                catalogId: 'catalog-2',
                catalogCode: 'STAT-IOPP',
                catalogDisplayName: 'International Oil Pollution Prevention Certificate',
                catalogShortName: 'IOPP',
                displayName: 'International Oil Pollution Prevention Certificate',
                shortName: 'IOPP',
                submissionScope: 'master_only',
                type: 'certificate',
                validityType: 'full',
                validityShortCode: '5-Y',
                formVariant: null,
                cadenceMonths: 60,
                cadenceCustomDays: null,
                parentId: null,
                relationshipType: null,
                supersedesId: null,
                issueDate: null,
                expiryDate: null,
                anniversaryDate: null,
                windowOpen: null,
                windowClose: null,
                lastDoneDate: null,
                nextDueDate: null,
                postponedUntil: null,
                status: 'pending_first_upload',
                certificateNumber: null,
                issuingAuthority: 'Flag',
                placeOfIssue: null,
                extensionAuthority: null,
                extensionLetterPdfId: null,
                extensionReason: null,
                pdfAttachmentId: null,
                pdfMissing: true,
                source: 'manual',
                lastClassSyncId: null,
                approvalState: 'approved',
                rejectionReason: null,
                lifecycleStatus: 'active',
                rowVersion: '0002',
                version: 1,
                daysToGo: null,
                isClassTracked: false,
                mandatoryForAllVessels: true,
              },
            ],
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/vessels/9876543']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('KSM Fortitude')).toBeInTheDocument();
    expect(screen.getByText(/Mandatory coverage is 50%/)).toBeInTheDocument();
    expect(screen.getByText('Class Certificates')).toBeInTheDocument();
    expect(screen.getByText('Statutory & Flag')).toBeInTheDocument();
    expect(screen.getByLabelText('Search')).toBeInTheDocument();
    expect(screen.getAllByText('Certificate of Class').length).toBeGreaterThan(0);
    expect(screen.getAllByText('International Oil Pollution Prevention Certificate').length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: /Vessel profile/ })).toHaveAttribute('href', '/certs/vessels/9876543/profile');
    expect(screen.getByRole('link', { name: /Print this vessel/ })).toHaveAttribute('href', '/certs/print?vesselId=vessel-1&imo=9876543');
    expect(screen.getByRole('link', { name: /Share bundle/ })).toHaveAttribute('href', '/certs/share-bundle?vesselId=vessel-1&imo=9876543');
    expect(screen.getByRole('button', { name: /Upload class snapshot/ })).toBeInTheDocument();
  });

  it('filters the Vessel Cert Dashboard by certificate search text', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_002'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useVesselDashboard.mockReturnValue({
      data: {
        vessel: {
          id: 'vessel-1',
          imo: '9876543',
          code: 'KSMF',
          name: 'KSM Fortitude',
          flag: 'Panama',
          classSociety: 'NK',
          shipType: 'bulk_carrier',
          currentMaster: 'Captain Anil',
          lifecycleStatus: 'active',
          pendingDisposalStartedAt: null,
          flagChangePending: false,
          iwsAgeGateDisabled: false,
        },
        mandatoryCoverage: {
          percent: 100,
          mandatoryCount: 2,
          coveredCount: 2,
          overrideActive: false,
          overrideReason: null,
          overrideAt: null,
          overrideBy: null,
        },
        lastClassSnapshot: null,
        summary: {
          totalTrackedItems: 2,
          actionItemCount: 1,
          pdfMissingCount: 1,
          classTrackedCount: 1,
        },
        sections: [
          {
            sectionId: 1,
            sectionCode: 'CLASS',
            displayName: 'Class Certificates',
            activeTrackedItemCount: 1,
            actionItemCount: 0,
            statusBreakdown: { ok: 1 },
            items: [
              {
                id: 'tracked-1',
                vesselId: 'vessel-1',
                catalogId: 'catalog-1',
                catalogCode: 'CLASS-COC',
                catalogDisplayName: 'Certificate of Class',
                catalogShortName: 'COC',
                displayName: 'Certificate of Class',
                shortName: 'COC',
                submissionScope: 'master_only',
                type: 'certificate',
                validityType: 'full',
                validityShortCode: '5-Y',
                formVariant: null,
                cadenceMonths: 60,
                cadenceCustomDays: null,
                parentId: null,
                relationshipType: null,
                supersedesId: null,
                issueDate: '2026-01-01',
                expiryDate: '2031-01-01',
                anniversaryDate: '2026-01-01',
                windowOpen: null,
                windowClose: null,
                lastDoneDate: null,
                nextDueDate: '2031-01-01',
                postponedUntil: null,
                status: 'ok',
                certificateNumber: 'COC-001',
                issuingAuthority: 'NK',
                placeOfIssue: 'Tokyo',
                extensionAuthority: null,
                extensionLetterPdfId: null,
                extensionReason: null,
                pdfAttachmentId: 'pdf-1',
                pdfMissing: false,
                source: 'manual',
                lastClassSyncId: null,
                approvalState: 'approved',
                rejectionReason: null,
                lifecycleStatus: 'active',
                rowVersion: '0001',
                version: 1,
                daysToGo: 1648,
                isClassTracked: true,
                mandatoryForAllVessels: true,
              },
            ],
          },
          {
            sectionId: 2,
            sectionCode: 'STATUTORY',
            displayName: 'Statutory & Flag',
            activeTrackedItemCount: 1,
            actionItemCount: 1,
            statusBreakdown: { pending_first_upload: 1 },
            items: [
              {
                id: 'tracked-2',
                vesselId: 'vessel-1',
                catalogId: 'catalog-2',
                catalogCode: 'STAT-IOPP',
                catalogDisplayName: 'International Oil Pollution Prevention Certificate',
                catalogShortName: 'IOPP',
                displayName: 'International Oil Pollution Prevention Certificate',
                shortName: 'IOPP',
                submissionScope: 'master_only',
                type: 'certificate',
                validityType: 'full',
                validityShortCode: '5-Y',
                formVariant: null,
                cadenceMonths: 60,
                cadenceCustomDays: null,
                parentId: null,
                relationshipType: null,
                supersedesId: null,
                issueDate: null,
                expiryDate: null,
                anniversaryDate: null,
                windowOpen: null,
                windowClose: null,
                lastDoneDate: null,
                nextDueDate: null,
                postponedUntil: null,
                status: 'pending_first_upload',
                certificateNumber: null,
                issuingAuthority: 'Flag',
                placeOfIssue: null,
                extensionAuthority: null,
                extensionLetterPdfId: null,
                extensionReason: null,
                pdfAttachmentId: null,
                pdfMissing: true,
                source: 'manual',
                lastClassSyncId: null,
                approvalState: 'approved',
                rejectionReason: null,
                lifecycleStatus: 'active',
                rowVersion: '0002',
                version: 1,
                daysToGo: null,
                isClassTracked: false,
                mandatoryForAllVessels: true,
              },
            ],
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/vessels/9876543']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'COC-001' },
    });

    expect(screen.getAllByText('Certificate of Class').length).toBeGreaterThan(0);
    expect(screen.queryByText('International Oil Pollution Prevention Certificate')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Search'), {
      target: { value: 'missing target' },
    });

    expect(screen.getByText('No results match these filters.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Reset filters' }));
    expect(screen.getByLabelText('Search')).toHaveValue('');
    expect(screen.getAllByText('International Oil Pollution Prevention Certificate').length).toBeGreaterThan(0);
  });

  it('renders the Vessel Profile lifecycle actions for DPA users', () => {
    const mutateFlag = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_002'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });
    certsRouteMocks.useVesselProfile.mockReturnValue({
      data: {
        vessel: {
          id: 'vessel-1',
          imo: '9876543',
          code: 'KSMF',
          name: 'KSM Fortitude',
          flag: 'Panama',
          classSociety: 'NK',
        },
        config: {
          vesselId: 'vessel-1',
          anniversaryDate: '2026-01-15',
          shipType: 'bulk_carrier',
          marineSuptUserId: null,
          technicalManagerUserId: null,
          lifecycleStatus: 'active',
          pendingDisposalStartedAt: null,
          saleHandoverBundleBlobId: null,
          flagChangePending: true,
          flagChangeEvent: { newFlagState: 'Liberia' },
          classChangePending: true,
          mandatoryCoverageOverrideReason: null,
          mandatoryCoverageOverrideAt: null,
          mandatoryCoverageOverrideBy: null,
          iwsAgeGateDisabled: false,
          updatedAt: '2026-06-30T09:00:00Z',
          updatedBy: 'dpa-1',
        },
        affectedTrackedItems: 0,
        saleHandoverArtifact: null,
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useRecordFlagChange.mockReturnValue({ mutate: mutateFlag, error: null, isPending: false });

    render(
      <MemoryRouter initialEntries={['/certs/vessels/9876543/profile']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Vessel Profile')).toBeInTheDocument();
    expect(screen.getByText(/Pending statutory re-upload after flag change/)).toBeInTheDocument();
    expect(screen.getByText(/Class change pending/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Record flag change/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Record class change/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Initiate sale handover/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Start decommission/ })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('New flag state'), { target: { value: 'Liberia' } });
    fireEvent.change(screen.getAllByLabelText('Reason')[0], {
      target: { value: 'Registered flag state is changing after sale contract review.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Record flag change/ }));

    expect(certsRouteMocks.useVesselProfile).toHaveBeenCalledWith('9876543');
    expect(mutateFlag).toHaveBeenCalledWith(expect.objectContaining({
      newFlagState: 'Liberia',
      reason: 'Registered flag state is changing after sale contract review.',
    }));
  });

  it('renders the Onboarding Hub with in-progress vessel rows', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_005'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_001', 'CERT_P_010'].includes(processId)),
    });
    const fixture = onboardingWizardFixture();
    certsRouteMocks.useOnboardingHub.mockReturnValue({
      data: {
        results: [
          {
            vessel: fixture.vessel,
            config: fixture.config,
            batchCount: 2,
            currentStep: 3,
            mandatoryCoveragePercent: 40,
            pendingFmSignoff: false,
            lastActivity: '2026-06-26T09:00:00Z',
            startedAt: '2026-06-25T09:00:00Z',
            startedBy: 'dpa-1',
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/onboarding']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Onboarding Hub' })).toBeInTheDocument();
    expect(screen.getByText('KSM Fortitude')).toBeInTheDocument();
    expect(screen.getByText('Step 3')).toBeInTheDocument();
    expect(screen.getByText('40%')).toBeInTheDocument();
  });

  it('renders the seven-step onboarding wizard and preserves session-expired state target', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_005'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_001', 'CERT_P_002', 'CERT_P_010'].includes(processId)),
    });
    certsRouteMocks.useOnboardingWizardState.mockReturnValue({
      data: onboardingWizardFixture(),
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/onboarding/9876543?step=3']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Onboarding: KSM Fortitude' })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /Step \d/ })).toHaveLength(7);
    expect(screen.getAllByText('Cert PDF batch ingest').length).toBeGreaterThan(0);
    expect(screen.getByText('Session re-auth preserves step 3')).toBeInTheDocument();
    expect(screen.getByText('Batch ready for review')).toBeInTheDocument();
  });

  it('requires a rollback reason before resetting onboarding', () => {
    const rollback = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_005'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_001', 'CERT_P_010'].includes(processId)),
    });
    certsRouteMocks.useRollbackOnboarding.mockReturnValue({ mutate: rollback, error: null, isPending: false });
    certsRouteMocks.useOnboardingWizardState.mockReturnValue({
      data: onboardingWizardFixture(),
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/onboarding/9876543?step=3']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /Reset onboarding/i }));
    const confirm = screen.getByRole('button', { name: /Confirm reset/i });
    expect(confirm).toBeDisabled();

    fireEvent.change(screen.getByLabelText('Rollback reason'), {
      target: { value: 'Reset failed onboarding import before FM sign-off.' },
    });
    fireEvent.click(confirm);

    expect(rollback).toHaveBeenCalledWith('Reset failed onboarding import before FM sign-off.');
  });

  it('renders gap-fill OCR confidence modes from Phase 3.1 payload', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_005'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_001', 'CERT_P_002'].includes(processId)),
    });
    const fixture = onboardingWizardFixture();
    certsRouteMocks.useOnboardingBatchGapFill.mockReturnValue({
      data: {
        batch: fixture.batches[0],
        vessel: fixture.vessel,
        pdfs: [
          {
            id: 'blob-1',
            trackedItemId: 'tracked-1',
            snapshotId: null,
            filename: 'iopp.pdf',
            sizeBytes: 1234,
            uploadedBy: 'dpa-1',
            uploadedAt: '2026-06-26T09:00:00Z',
            isActive: true,
            supersededAt: null,
            retentionPolicy: 'retain_18_months_then_purge',
            scheduledDeleteAt: null,
            deletePendingSince: null,
            dpaRetentionOverrideUntil: null,
            ocrProcessedAt: '2026-06-26T09:05:00Z',
            ocrEngineVersion: 'static-test',
            ocrConfidencePerField: { certificate_number: 0.58 },
            ocrPayload: {
              schema_version: 'certs-ocr-v1',
              engine: 'static-test',
              context: 'office',
              thresholds: { auto_accept: 0.8, manual_floor: 0.6 },
              status: 'processed',
              unprocessable: false,
              raw_text: 'Certificate No IOPP-001',
              fields: {
                certificate_number: {
                  value: null,
                  raw_value: 'IOPP-001',
                  confidence: 0.58,
                  mode: 'manual_entry',
                  threshold: 0.8,
                  manual_floor: 0.6,
                  required: true,
                },
              },
            },
            fieldStates: [
              {
                field: 'certificate_number',
                value: null,
                rawValue: 'IOPP-001',
                confidence: 0.58,
                mode: 'manual_entry',
                required: true,
              },
            ],
            trackedItem: null,
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/onboarding/9876543/batch/batch-1/gap-fill']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'Gap-Fill Review' })).toBeInTheDocument();
    expect(screen.getAllByText('iopp.pdf').length).toBeGreaterThan(0);
    expect(screen.getByText('certificate number')).toBeInTheDocument();
    expect(screen.getByText('manual entry')).toBeInTheDocument();
    expect(screen.getByText('58%')).toBeInTheDocument();
    expect(screen.getByText('IOPP-001')).toBeInTheDocument();
  });

  it('requires DPA acknowledgment before committing a batch with D-CERT-116 warnings', () => {
    const preview = vi.fn();
    const commit = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_005'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_001', 'CERT_P_002'].includes(processId)),
    });
    const fixture = onboardingWizardFixture();
    certsRouteMocks.usePreviewOnboardingBatch.mockReturnValue({ mutate: preview, error: null, isPending: false });
    certsRouteMocks.useCommitOnboardingBatch.mockReturnValue({ mutate: commit, error: null, isPending: false });
    certsRouteMocks.useOnboardingBatchGapFill.mockReturnValue({
      data: {
        batch: {
          ...fixture.batches[0],
          validationBlocks: [],
          validationWarns: [
            {
              code: 'expiry_date_in_past',
              severity: 'warn',
              message: 'Expiry date is in the past.',
              blobId: 'blob-1',
              filename: 'iopp.pdf',
            },
          ],
        },
        vessel: fixture.vessel,
        pdfs: [],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/onboarding/9876543/batch/batch-1/gap-fill']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('D-CERT-116 warnings')).toBeInTheDocument();
    expect(screen.getByText('Expiry date is in the past.')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Preview validation/i }));
    expect(preview).toHaveBeenCalledWith(undefined);
    expect(screen.getByRole('button', { name: /Commit batch/i })).toBeDisabled();
    fireEvent.click(screen.getByLabelText('I acknowledge D-CERT-116 warnings for this batch.'));
    fireEvent.click(screen.getByRole('button', { name: /Commit batch/i }));
    expect(commit).toHaveBeenCalledWith({ acknowledgeWarnings: true });
  });

  it('requires explicit supersede confirmation before committing same-number replacement PDFs', () => {
    const commit = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_005'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_001', 'CERT_P_002'].includes(processId)),
    });
    const fixture = onboardingWizardFixture();
    certsRouteMocks.usePreviewOnboardingBatch.mockReturnValue({ mutate: vi.fn(), error: null, isPending: false });
    certsRouteMocks.useCommitOnboardingBatch.mockReturnValue({ mutate: commit, error: null, isPending: false });
    certsRouteMocks.useOnboardingBatchGapFill.mockReturnValue({
      data: {
        batch: {
          ...fixture.batches[0],
          validationBlocks: [
            {
              code: 'supersede_confirmation_required',
              severity: 'block',
              message: 'A certificate with this number already exists. Confirm whether this PDF supersedes it.',
              blobId: 'new-blob',
              filename: 'iopp-renewal.pdf',
              field: 'certificate_number',
              value: 'existing-blob',
              certificateNumber: 'IOPP-001',
            },
          ],
          validationWarns: [],
        },
        vessel: fixture.vessel,
        pdfs: [],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/onboarding/9876543/batch/batch-1/gap-fill']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('D-CERT-116 / D-CERT-118 blocks')).toBeInTheDocument();
    expect(screen.getByText('A certificate with this number already exists. Confirm whether this PDF supersedes it.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Commit batch/i })).toBeDisabled();

    fireEvent.click(screen.getByLabelText('Confirm these PDFs supersede the existing certificate versions.'));
    fireEvent.click(screen.getByRole('button', { name: /Commit batch/i }));

    expect(commit).toHaveBeenCalledWith({
      acknowledgeWarnings: false,
      supersedeDecisions: [{ blobId: 'new-blob', existingBlobId: 'existing-blob', confirm: true }],
    });
  });

  it('renders dashboard filtered-empty state with reset filters CTA', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_002'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useVesselDashboard.mockReturnValue({
      data: {
        vessel: {
          id: 'vessel-1',
          imo: '9876543',
          code: 'KSMF',
          name: 'KSM Fortitude',
          flag: 'Panama',
          classSociety: 'NK',
          shipType: 'bulk_carrier',
          currentMaster: null,
          lifecycleStatus: 'active',
          pendingDisposalStartedAt: null,
          flagChangePending: false,
          iwsAgeGateDisabled: false,
        },
        mandatoryCoverage: {
          percent: 100,
          mandatoryCount: 1,
          coveredCount: 1,
          overrideActive: false,
          overrideReason: null,
          overrideAt: null,
          overrideBy: null,
        },
        lastClassSnapshot: null,
        summary: {
          totalTrackedItems: 1,
          actionItemCount: 0,
          pdfMissingCount: 0,
          classTrackedCount: 1,
        },
        sections: [
          {
            sectionId: 1,
            sectionCode: 'CLASS',
            displayName: 'Class Certificates',
            activeTrackedItemCount: 0,
            actionItemCount: 0,
            statusBreakdown: {},
            items: [],
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/vessels/9876543']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('No results match these filters.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Reset filters' })).toBeInTheDocument();
  });

  it('hides Vessel Cert Dashboard when the user lacks CERT_F_002', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn(() => false),
    });

    render(
      <MemoryRouter initialEntries={['/certs/vessels/9876543']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(
      screen.getByRole('heading', { name: "You don't have access to this page." })
    ).toBeInTheDocument();
    expect(certsRouteMocks.useVesselDashboard).toHaveBeenCalledWith(undefined);
  });

  it('renders TrackedItem Detail panels, banners, and Master workflow actions', () => {
    const approveMutate = vi.fn();
    const uploadMutate = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Master',
      user: { role_name: 'Master' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_002'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_001', 'CERT_P_002', 'CERT_P_003', 'CERT_P_004'].includes(processId)),
    });
    certsRouteMocks.useApproveTrackedItem.mockReturnValue({
      mutate: approveMutate,
      error: null,
      isPending: false,
    });
    certsRouteMocks.useUploadTrackedItemPdf.mockReturnValue({
      mutate: uploadMutate,
      error: null,
      isPending: false,
    });
    certsRouteMocks.useTrackedItemDetail.mockReturnValue({
      data: {
        id: 'tracked-1',
        vesselId: 'A282A51B-0183-EE11-B02E-782B4610C006',
        vesselName: 'SFYC ARAYA',
        vesselCode: 'SFA',
        vesselImo: '9487043',
        catalogId: 'catalog-1',
        catalogCode: 'STAT-IOPP',
        catalogDisplayName: 'International Oil Pollution Prevention Certificate',
        catalogShortName: 'IOPP',
        displayName: 'International Oil Pollution Prevention Certificate',
        shortName: 'IOPP',
        submissionScope: 'master_only',
        type: 'certificate',
        validityType: 'full',
        validityShortCode: '5-Y',
        formVariant: 'A',
        cadenceMonths: 60,
        cadenceCustomDays: null,
        parentId: null,
        relationshipType: null,
        supersedesId: 'tracked-old',
        issueDate: '2026-01-01',
        expiryDate: '2031-01-01',
        anniversaryDate: '2026-01-01',
        windowOpen: '2030-10-01',
        windowClose: '2031-01-01',
        lastDoneDate: '2026-01-01',
        nextDueDate: '2031-01-01',
        postponedUntil: null,
        status: 'expired_at_onboarding',
        certificateNumber: 'IOPP-001',
        issuingAuthority: 'Flag',
        placeOfIssue: 'Bangkok',
        extensionAuthority: null,
        extensionLetterPdfId: null,
        extensionReason: null,
        pdfAttachmentId: 'pdf-1',
        pdfMissing: true,
        source: 'manual',
        lastClassSyncId: null,
        approvalState: 'pending_master_approval',
        submittedBy: '7e051002-a5ac-ef11-a9fa-9506b4da1af9',
        submittedByDisplay: 'CHIEF OFFICER - Chaiwut Kwangkaeo',
        submittedAt: '2026-06-25T00:00:00Z',
        approvedBy: '7e051002-a5ac-ef11-a9fa-9506b4da1af9',
        approvedByDisplay: 'CHIEF OFFICER - Chaiwut Kwangkaeo',
        approvedAt: null,
        rejectionReason: null,
        rejectionCount: 0,
        draftExpiresAt: null,
        lifecycleStatus: 'active',
        rowVersion: '0001',
        version: 7,
        createdAt: '2026-06-25T00:00:00Z',
        createdBy: 'dpa-1',
        updatedAt: '2026-06-25T00:00:00Z',
        updatedBy: 'dpa-1',
        daysToGo: 0,
        isClassTracked: true,
        mandatoryForAllVessels: true,
        pdfVersions: [
          {
            id: 'pdf-1',
            trackedItemId: 'tracked-1',
            snapshotId: null,
            filename: 'IOPP.pdf',
            sizeBytes: 2048,
            uploadedBy: '7e051002-a5ac-ef11-a9fa-9506b4da1af9',
            uploadedByDisplay: 'CHIEF OFFICER - Chaiwut Kwangkaeo',
            uploadedAt: '2026-06-25T00:00:00Z',
            isActive: true,
            supersededAt: null,
            retentionPolicy: 'retain_18_months_then_purge',
            scheduledDeleteAt: null,
            deletePendingSince: null,
            dpaRetentionOverrideUntil: null,
          },
        ],
        approvalEvents: [
          {
            id: 'event-1',
            fromState: 'draft',
            toState: 'pending_master_approval',
            actorUserId: '7e051002-a5ac-ef11-a9fa-9506b4da1af9',
            actorDisplayName: 'CHIEF OFFICER - Chaiwut Kwangkaeo',
            actorRole: 'Chief Officer',
            reason: 'Submitted renewal evidence.',
            timestampUtc: '2026-06-25T00:00:00Z',
          },
        ],
        auditEvents: [
          {
            id: 'audit-1',
            timestampUtc: '2026-06-25T00:00:00Z',
            vesselId: 'vessel-1',
            actorUserId: 'dpa-1',
            actorRole: 'DPA',
            action: 'update_tracked_item',
            entityType: 'tracked_item',
            entityId: 'tracked-1',
            before: { certificateNumber: 'OLD' },
            after: { certificateNumber: 'IOPP-001' },
            reason: 'Corrected certificate number.',
            eventMetadata: null,
            retentionTier: 'hot',
            archivedAt: null,
            schemaVersion: 1,
          },
        ],
        changeHistory: [
          {
            id: 'change-1',
            fieldName: 'certificate_number',
            oldValue: 'OLD',
            newValue: 'IOPP-001',
            versionAfter: 7,
            sourceModule: 'CERTS',
            sourceRef: 'api.certs.tracked_items',
            changedBy: 'dpa-1',
            changedByDisplay: 'DPA - DPA User',
            changedAt: '2026-06-25T00:00:00Z',
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/vessels/9876543/cert/tracked-1']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: 'International Oil Pollution Prevention Certificate' })).toBeInTheDocument();
    expect(screen.getByText(/SFYC ARAYA - IOPP-001/)).toBeInTheDocument();
    expect(screen.getAllByText('CHIEF OFFICER - Chaiwut Kwangkaeo').length).toBeGreaterThan(0);
    expect(screen.getByText(/CERTS - DPA - DPA User/)).toBeInTheDocument();
    expect(screen.queryByText(/7e051002-a5ac-ef11-a9fa-9506b4da1af9/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/A282A51B-0183-EE11-B02E-782B4610C006/i)).not.toBeInTheDocument();
    expect(screen.getByText(/already expired at onboarding/)).toBeInTheDocument();
    expect(screen.getByText('PDF not on file. Request copy from issuer.')).toBeInTheDocument();
    expect(screen.getAllByText('IOPP.pdf').length).toBeGreaterThan(0);
    expect(screen.getByText('Submitted renewal evidence.')).toBeInTheDocument();
    expect(screen.getByText('Corrected certificate number.')).toBeInTheDocument();
    expect(screen.getByText('certificate_number')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Approve' }));
    expect(approveMutate).toHaveBeenCalledWith({
      reason: 'Phase 2.6 tracked-item detail workflow action.',
      version: 7,
    });
    fireEvent.click(screen.getByRole('button', { name: 'Upload new PDF' }));
    expect(screen.getByRole('heading', { name: 'Upload certificate PDF' })).toBeInTheDocument();
    const renewedPdf = new File(['%PDF-1.4 renewed certificate'], 'renewed-iopp.pdf', { type: 'application/pdf' });
    fireEvent.change(screen.getByLabelText('Certificate PDF'), {
      target: { files: [renewedPdf] },
    });
    fireEvent.change(screen.getByLabelText('Reason'), {
      target: { value: 'Uploading renewed certificate PDF.' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Upload PDF' }));
    expect(uploadMutate).toHaveBeenCalledWith(
      {
        file: renewedPdf,
        reason: 'Uploading renewed certificate PDF.',
      },
      expect.objectContaining({ onSuccess: expect.any(Function) })
    );
    expect(certsRouteMocks.useTrackedItemDetail).toHaveBeenCalledWith('tracked-1');
    expect(certsRouteMocks.useUploadTrackedItemPdf).toHaveBeenCalledWith('tracked-1', '9876543');
  });

  it('hides TrackedItem Detail when the user lacks CERT_F_002', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn(() => false),
    });

    render(
      <MemoryRouter initialEntries={['/certs/vessels/9876543/cert/tracked-1']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: "You don't have access to this page." })).toBeInTheDocument();
    expect(certsRouteMocks.useTrackedItemDetail).toHaveBeenCalledWith(undefined);
  });

  it('renders Catalog Admin rows at /certs/catalog for catalog readers', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useCatalogSections.mockReturnValue({
      data: [
        {
          id: 2,
          sectionId: 2,
          sectionCode: 'STATUTORY',
          displayName: 'Statutory & Flag',
          sortOrder: 2,
          activeRowCount: 1,
        },
      ],
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRows.mockReturnValue({
      data: {
        count: 2,
        results: [
          {
            id: 'parent-row',
            canonicalCode: 'STAT-IOPP',
            sectionId: 2,
            sectionName: 'Statutory & Flag',
            displayName: 'International Oil Pollution Prevention Certificate',
            shortName: 'IOPP',
            printSectionLabel: 'Statutory & Flag',
            validityType: 'full',
            cadenceMonths: 60,
            cadenceCustomDays: null,
            issuingAuthorityType: 'flag',
            isClassTracked: false,
            submissionScope: 'master_only',
            parentId: null,
            relationshipTypeDefault: null,
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: null,
            legacyRemarks: null,
            printOrder: 10,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'dpa-1',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'dpa-1',
          },
          {
            id: 'child-row',
            canonicalCode: 'STAT-IOPP-ANNUAL-SURVEY',
            sectionId: 2,
            sectionName: 'Statutory & Flag',
            displayName: 'Last Annual Survey',
            shortName: null,
            printSectionLabel: 'Statutory & Flag',
            validityType: 'conditional',
            cadenceMonths: 12,
            cadenceCustomDays: null,
            issuingAuthorityType: 'class',
            isClassTracked: true,
            submissionScope: 'master_only',
            parentId: 'parent-row',
            relationshipTypeDefault: 'survey_of',
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: null,
            legacyRemarks: null,
            printOrder: 11,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'dpa-1',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'dpa-1',
          },
          {
            id: 'dynamic-row',
            canonicalCode: 'EQ-SCBA-ELSA-EEBD',
            sectionId: 4,
            sectionName: 'Equipment LSA/FFA/Nav/GMDSS',
            displayName: 'SCBA / ELSA / EEBD',
            shortName: null,
            printSectionLabel: 'Equipment LSA/FFA/Nav/GMDSS',
            validityType: 'conditional',
            cadenceMonths: 12,
            cadenceCustomDays: null,
            issuingAuthorityType: 'company',
            isClassTracked: false,
            submissionScope: 'master_only',
            parentId: null,
            relationshipTypeDefault: null,
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: true,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: 'D-CERT-035',
            legacyRemarks: null,
            printOrder: 20,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'dpa-1',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'dpa-1',
          },
          {
            id: 'rollup-row',
            canonicalCode: 'EQ-PORTABLE-FIRE-EXTINGUISHERS',
            sectionId: 4,
            sectionName: 'Equipment LSA/FFA/Nav/GMDSS',
            displayName: 'Portable Fire Extinguishers Annual Service',
            shortName: null,
            printSectionLabel: 'Equipment LSA/FFA/Nav/GMDSS',
            validityType: 'conditional',
            cadenceMonths: 12,
            cadenceCustomDays: null,
            issuingAuthorityType: 'company',
            isClassTracked: false,
            submissionScope: 'master_only',
            parentId: null,
            relationshipTypeDefault: null,
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: 'D-CERT-036',
            legacyRemarks: null,
            printOrder: 21,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'dpa-1',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'dpa-1',
          },
        ],
      },
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Catalog Admin')).toBeInTheDocument();
    expect(screen.getByText('STAT-IOPP')).toBeInTheDocument();
    expect(screen.getByText('STAT-IOPP-ANNUAL-SURVEY')).toBeInTheDocument();
    expect(screen.queryByText('STAT-IOPP-A')).not.toBeInTheDocument();
    expect(screen.queryByText('STAT-IOPP-B')).not.toBeInTheDocument();
    expect(screen.getByText('Child of STAT-IOPP')).toBeInTheDocument();
    expect(screen.getByText('EQ-SCBA-ELSA-EEBD')).toBeInTheDocument();
    expect(screen.getByText('Dynamic instances')).toBeInTheDocument();
    expect(screen.getByText('EQ-PORTABLE-FIRE-EXTINGUISHERS')).toBeInTheDocument();
    expect(screen.getByText('Roll-up service row')).toBeInTheDocument();
    expect(screen.getAllByText('All ships').length).toBeGreaterThan(0);
    expect(certsRouteMocks.useCatalogRows).toHaveBeenCalledWith({
      sectionId: null,
      isActive: true,
      q: '',
      applicableShipType: null,
    });
    expect(screen.queryByRole('button', { name: /Add row/i })).not.toBeInTheDocument();
  });

  it('normalizes a trailing slash on Catalog Row Detail before loading the row', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn(() => false),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog/row-with-trailing/']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(certsRouteMocks.useCatalogRow).toHaveBeenCalledWith('row-with-trailing');
    expect(certsRouteMocks.useCatalogRowAuditHistory).toHaveBeenCalledWith('row-with-trailing');
  });

  it('shows DPA-only catalog write affordance when role and process permission match', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: /Add row/i })).toBeInTheDocument();
    expect(screen.getByText('No catalog rows match your filter.')).toBeInTheDocument();
  });

  it('submits DPA bulk soft-delete with selected rows and required reason', () => {
    const bulkSoftDelete = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_008', 'CERT_P_009'].includes(processId)),
    });
    certsRouteMocks.useBulkSoftDeleteCatalogRows.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: bulkSoftDelete,
    });
    certsRouteMocks.useCatalogRows.mockReturnValue({
      data: {
        count: 2,
        results: [
          {
            id: 'bulk-row-1',
            canonicalCode: 'STAT-OLD-ONE',
            sectionId: 2,
            sectionName: 'Statutory & Flag',
            displayName: 'Old Certificate One',
            shortName: null,
            printSectionLabel: 'Statutory & Flag',
            validityType: 'full',
            cadenceMonths: 60,
            cadenceCustomDays: null,
            issuingAuthorityType: 'flag',
            isClassTracked: false,
            submissionScope: 'master_only',
            parentId: null,
            relationshipTypeDefault: null,
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: null,
            legacyRemarks: null,
            printOrder: 10,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'dpa-1',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'dpa-1',
          },
          {
            id: 'bulk-row-2',
            canonicalCode: 'STAT-OLD-TWO',
            sectionId: 2,
            sectionName: 'Statutory & Flag',
            displayName: 'Old Certificate Two',
            shortName: null,
            printSectionLabel: 'Statutory & Flag',
            validityType: 'full',
            cadenceMonths: 60,
            cadenceCustomDays: null,
            issuingAuthorityType: 'flag',
            isClassTracked: false,
            submissionScope: 'master_only',
            parentId: null,
            relationshipTypeDefault: null,
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: null,
            legacyRemarks: null,
            printOrder: 20,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'dpa-1',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'dpa-1',
          },
        ],
      },
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByLabelText('Select STAT-OLD-ONE'));
    fireEvent.click(screen.getByLabelText('Select STAT-OLD-TWO'));
    fireEvent.click(screen.getByRole('button', { name: /Bulk soft-delete/i }));
    fireEvent.change(screen.getByLabelText('Bulk soft-delete reason'), {
      target: { value: 'Superseded duplicate workshop rows.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Confirm bulk soft-delete/i }));

    expect(bulkSoftDelete).toHaveBeenCalledWith({
      catalogIds: ['bulk-row-1', 'bulk-row-2'],
      reason: 'Superseded duplicate workshop rows.',
    }, expect.any(Object));
  });

  it('submits catalog row deprecation with the DPA reason from detail', () => {
    const deprecate = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });
    certsRouteMocks.useDeprecateCatalogRow.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: deprecate,
    });
    certsRouteMocks.useCatalogRow.mockReturnValue({
      data: {
        id: 'row-to-deprecate',
        canonicalCode: 'STAT-OLD-CERT',
        sectionId: 2,
        sectionName: 'Statutory & Flag',
        displayName: 'Old Flag Certificate',
        shortName: null,
        printSectionLabel: 'Statutory & Flag',
        validityType: 'full',
        cadenceMonths: 60,
        cadenceCustomDays: null,
        issuingAuthorityType: 'flag',
        isClassTracked: false,
        submissionScope: 'master_only',
        parentId: null,
        relationshipTypeDefault: null,
        applicableShipTypes: ['all'],
        mandatoryForAllVessels: true,
        applicabilityMode: 'all_matching_type',
        specificVesselIds: [],
        parentSupportsDynamicChildren: false,
        ageGateMaxYears: null,
        retainAllVersions: false,
        linkedPmsComponentId: null,
        alertLeadOverrides: null,
        regulatoryAnchor: null,
        legacyRemarks: null,
        printOrder: 10,
        isActive: true,
        createdAt: '2026-06-24T00:00:00Z',
        createdBy: 'dpa-1',
        updatedAt: '2026-06-24T00:00:00Z',
        updatedBy: 'dpa-1',
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog/row-to-deprecate']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('Reason'), {
      target: { value: 'Superseded by revised flag-state certificate type.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Deprecate row/i }));
    expect(screen.getByText('Deprecate catalog row?')).toBeInTheDocument();
    const deprecateButtons = screen.getAllByRole('button', { name: /Deprecate row/i });
    fireEvent.click(deprecateButtons[deprecateButtons.length - 1]);

    expect(deprecate).toHaveBeenCalledWith({
      reason: 'Superseded by revised flag-state certificate type.',
    });
  });

  it('submits hard purge from Catalog Row Detail with named confirmation', () => {
    const hardPurge = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn((processId: string) => ['CERT_P_008', 'CERT_P_009'].includes(processId)),
    });
    certsRouteMocks.useHardPurgeCatalogRow.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: hardPurge,
    });
    certsRouteMocks.useCatalogRow.mockReturnValue({
      data: {
        id: 'row-to-purge',
        canonicalCode: 'STAT-OLD-CERT',
        sectionId: 2,
        sectionName: 'Statutory & Flag',
        displayName: 'Old Flag Certificate',
        shortName: null,
        printSectionLabel: 'Statutory & Flag',
        validityType: 'full',
        cadenceMonths: 60,
        cadenceCustomDays: null,
        issuingAuthorityType: 'flag',
        isClassTracked: false,
        submissionScope: 'master_only',
        parentId: null,
        relationshipTypeDefault: null,
        applicableShipTypes: ['all'],
        mandatoryForAllVessels: true,
        applicabilityMode: 'all_matching_type',
        specificVesselIds: [],
        parentSupportsDynamicChildren: false,
        ageGateMaxYears: null,
        retainAllVersions: false,
        linkedPmsComponentId: null,
        alertLeadOverrides: null,
        regulatoryAnchor: null,
        legacyRemarks: null,
        printOrder: 10,
        isActive: false,
        createdAt: '2026-06-24T00:00:00Z',
        createdBy: 'dpa-1',
        updatedAt: '2026-06-24T00:00:00Z',
        updatedBy: 'dpa-1',
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog/row-to-purge']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('Reason'), {
      target: { value: 'Retention window expired for duplicate catalog row.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Hard purge/i }));
    expect(screen.getByText('Hard purge catalog row?')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Confirm hard purge/i }));

    expect(hardPurge).toHaveBeenCalledWith({
      reason: 'Retention window expired for duplicate catalog row.',
    }, expect.any(Object));
  });

  it('renders Catalog Row Detail audit history for catalog readers', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useCatalogRow.mockReturnValue({
      data: {
        id: 'row-with-audit',
        canonicalCode: 'STAT-IOPP',
        sectionId: 2,
        sectionName: 'Statutory & Flag',
        displayName: 'International Oil Pollution Prevention Certificate',
        shortName: 'IOPP',
        printSectionLabel: 'Statutory & Flag',
        validityType: 'full',
        cadenceMonths: 60,
        cadenceCustomDays: null,
        issuingAuthorityType: 'flag',
        isClassTracked: false,
        submissionScope: 'master_only',
        parentId: null,
        relationshipTypeDefault: null,
        applicableShipTypes: ['all'],
        mandatoryForAllVessels: true,
        applicabilityMode: 'all_matching_type',
        specificVesselIds: [],
        parentSupportsDynamicChildren: false,
        ageGateMaxYears: null,
        retainAllVersions: false,
        linkedPmsComponentId: null,
        alertLeadOverrides: null,
        regulatoryAnchor: null,
        legacyRemarks: null,
        printOrder: 10,
        isActive: true,
        createdAt: '2026-06-24T00:00:00Z',
        createdBy: 'dpa-1',
        updatedAt: '2026-06-25T06:45:00Z',
        updatedBy: 'dpa-1',
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRowAuditHistory.mockReturnValue({
      data: [
        {
          id: 'audit-1',
          timestampUtc: '2026-06-25T06:45:00Z',
          vesselId: null,
          actorUserId: 'dpa-1',
          actorRole: 'DPA',
          action: 'update_catalog_row',
          entityType: 'catalog_row',
          entityId: 'row-with-audit',
          before: { displayName: 'Old IOPP' },
          after: { displayName: 'International Oil Pollution Prevention Certificate' },
          reason: 'Corrected workshop spelling.',
          eventMetadata: { source: 'api.certs.catalog.rows' },
          retentionTier: 'hot',
          archivedAt: null,
          schemaVersion: 1,
        },
      ],
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog/row-with-audit']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Audit history')).toBeInTheDocument();
    expect(screen.getByText('Update Catalog Row')).toBeInTheDocument();
    expect(screen.getByText('DPA - dpa-1')).toBeInTheDocument();
    expect(screen.getByText('Corrected workshop spelling.')).toBeInTheDocument();
    expect(screen.getByText('Changed: displayName')).toBeInTheDocument();
    expect(certsRouteMocks.useCatalogRowAuditHistory).toHaveBeenCalledWith('row-with-audit');
    expect(screen.queryByRole('button', { name: /Save changes/i })).not.toBeInTheDocument();
  });

  it('passes onboarding gap-fill context when DPA creates an inline-promotion catalog row', () => {
    const create = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });
    certsRouteMocks.useCreateCatalogRow.mockReturnValue({
      isError: false,
      isPending: false,
      mutate: create,
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog?source=onboarding_gap_fill&vesselId=vessel-123&batchId=batch-456']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /Add row/i }));
    expect(screen.getByText('Inline promotion from onboarding gap-fill')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Canonical code'), {
      target: { value: 'FLAG-SPECIAL-PORT-STATE-LETTER' },
    });
    fireEvent.change(screen.getByLabelText('Display name'), {
      target: { value: 'Special Port State Letter' },
    });
    fireEvent.change(screen.getByLabelText('Reason'), {
      target: { value: 'DPA added uncatalogued certificate during onboarding.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Save row/i }));

    expect(create).toHaveBeenCalledWith(
      expect.objectContaining({
        canonicalCode: 'FLAG-SPECIAL-PORT-STATE-LETTER',
        displayName: 'Special Port State Letter',
        inlinePromotion: {
          source: 'onboarding_gap_fill',
          vesselId: 'vessel-123',
          batchId: 'batch-456',
        },
      }),
      expect.any(Object)
    );
  });

  it('renders Class Certificates baseline rows as COC parent and class-survey children', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useCatalogSections.mockReturnValue({
      data: [
        {
          id: 1,
          sectionId: 1,
          sectionCode: 'CLASS',
          displayName: 'Class Certificates',
          sortOrder: 1,
          activeRowCount: 11,
        },
      ],
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRows.mockReturnValue({
      data: {
        count: 3,
        results: [
          {
            id: 'coc-row',
            canonicalCode: 'CLASS-COC',
            sectionId: 1,
            sectionName: 'Class Certificates',
            displayName: 'Certificate of Class',
            shortName: 'COC',
            printSectionLabel: 'Class Certificates',
            validityType: 'full',
            cadenceMonths: 60,
            cadenceCustomDays: null,
            issuingAuthorityType: 'class',
            isClassTracked: true,
            submissionScope: 'master_only',
            parentId: null,
            relationshipTypeDefault: null,
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: 'D-CERT-014',
            legacyRemarks: null,
            printOrder: 10,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'seed_class_certificates',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'seed_class_certificates',
          },
          {
            id: 'annual-survey-row',
            canonicalCode: 'CLASS-ANNUAL-SURVEY',
            sectionId: 1,
            sectionName: 'Class Certificates',
            displayName: 'Class Annual Survey',
            shortName: null,
            printSectionLabel: 'Class Certificates',
            validityType: 'conditional',
            cadenceMonths: 12,
            cadenceCustomDays: null,
            issuingAuthorityType: 'class',
            isClassTracked: true,
            submissionScope: 'master_only',
            parentId: 'coc-row',
            relationshipTypeDefault: 'survey_of',
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: 'D-CERT-014',
            legacyRemarks: null,
            printOrder: 15,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'seed_class_certificates',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'seed_class_certificates',
          },
          {
            id: 'iws-survey-row',
            canonicalCode: 'CLASS-IWS-SURVEY',
            sectionId: 1,
            sectionName: 'Class Certificates',
            displayName: 'Class In-Water Survey',
            shortName: 'IWS',
            printSectionLabel: 'Class Certificates',
            validityType: 'conditional',
            cadenceMonths: 60,
            cadenceCustomDays: null,
            issuingAuthorityType: 'class',
            isClassTracked: true,
            submissionScope: 'master_only',
            parentId: 'coc-row',
            relationshipTypeDefault: 'survey_of',
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: 15,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: 'D-CERT-034',
            legacyRemarks: 'Vessels up to 15 years only.',
            printOrder: 20,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'seed_class_certificates',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'seed_class_certificates',
          },
        ],
      },
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Class Certificates')).toBeInTheDocument();
    expect(screen.getByText('CLASS-COC')).toBeInTheDocument();
    expect(screen.getByText('CLASS-ANNUAL-SURVEY')).toBeInTheDocument();
    expect(screen.getByText('CLASS-IWS-SURVEY')).toBeInTheDocument();
    expect(screen.getAllByText('Child of CLASS-COC')).toHaveLength(2);
  });

  it('renders specific-vessel applicability controls on catalog row detail', () => {
    const vesselId = '11111111-1111-1111-1111-111111111111';
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });
    certsRouteMocks.useCatalogRows.mockReturnValue({
      data: { count: 0, results: [] },
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRow.mockReturnValue({
      data: {
        id: 'row-1',
        canonicalCode: 'STAT-SPECIAL',
        sectionId: 2,
        sectionName: 'Statutory & Flag',
        displayName: 'Special Flag Dispensation',
        shortName: null,
        printSectionLabel: 'Statutory & Flag',
        validityType: 'conditional',
        cadenceMonths: null,
        cadenceCustomDays: null,
        issuingAuthorityType: 'flag',
        isClassTracked: false,
        submissionScope: 'master_only',
        parentId: null,
        relationshipTypeDefault: null,
        applicableShipTypes: ['tanker'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'specific_vessel_ids',
            specificVesselIds: [vesselId],
            parentSupportsDynamicChildren: true,
            ageGateMaxYears: null,
        retainAllVersions: false,
        linkedPmsComponentId: null,
        alertLeadOverrides: null,
        regulatoryAnchor: null,
        legacyRemarks: null,
        printOrder: 10,
        isActive: true,
        createdAt: '2026-06-24T00:00:00Z',
        createdBy: 'dpa-1',
        updatedAt: '2026-06-24T00:00:00Z',
        updatedBy: 'dpa-1',
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog/row-1']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('STAT-SPECIAL')).toBeInTheDocument();
    expect(screen.getByLabelText('Specific vessel IDs')).toHaveValue(vesselId);
    expect(screen.getByLabelText('Tanker')).toBeChecked();
    expect(screen.getByLabelText('Dynamic child TrackedItems')).toBeChecked();
  });

  it('renders and submits inert PMS component metadata on Type Approval detail', () => {
    const mutate = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });
    certsRouteMocks.useUpdateCatalogRow.mockReturnValue({
      isError: false,
      isPending: false,
      mutate,
    });
    certsRouteMocks.useCatalogRows.mockReturnValue({
      data: { count: 0, results: [] },
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRow.mockReturnValue({
      data: {
        id: 'type-row',
        canonicalCode: 'TYPE-OWS-APPROVAL',
        sectionId: 7,
        sectionName: 'Type Approvals',
        displayName: 'OWS Type Approval',
        shortName: null,
        printSectionLabel: 'Type Approvals',
        validityType: 'permanent',
        cadenceMonths: null,
        cadenceCustomDays: null,
        issuingAuthorityType: 'manufacturer',
        isClassTracked: false,
        submissionScope: 'all_ranks_with_approval',
        parentId: null,
        relationshipTypeDefault: null,
        applicableShipTypes: ['all'],
        mandatoryForAllVessels: true,
        applicabilityMode: 'all_matching_type',
        specificVesselIds: [],
        parentSupportsDynamicChildren: false,
        ageGateMaxYears: null,
        retainAllVersions: false,
        linkedPmsComponentId: 'PMS-COMP-OWS-001',
        alertLeadOverrides: null,
        regulatoryAnchor: 'D-CERT-042',
        legacyRemarks: null,
        printOrder: 70,
        isActive: true,
        createdAt: '2026-06-24T00:00:00Z',
        createdBy: 'dpa-1',
        updatedAt: '2026-06-24T00:00:00Z',
        updatedBy: 'dpa-1',
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog/type-row']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByLabelText('PMS component ID')).toHaveValue('PMS-COMP-OWS-001');
    expect(screen.getByText('Cross-module integration deferred - value stored only')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('PMS component ID'), {
      target: { value: 'PMS-COMP-OWS-002' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Save changes/i }));

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        linkedPmsComponentId: 'PMS-COMP-OWS-002',
      })
    );
  });

  it('renders parent-row picker on catalog row detail with only top-level parent options', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_001'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_008'),
    });
    certsRouteMocks.useCatalogRows.mockReturnValue({
      data: {
        count: 2,
        results: [
          {
            id: 'parent-row',
            canonicalCode: 'STAT-IOPP',
            sectionId: 2,
            sectionName: 'Statutory & Flag',
            displayName: 'International Oil Pollution Prevention Certificate',
            shortName: 'IOPP',
            printSectionLabel: 'Statutory & Flag',
            validityType: 'full',
            cadenceMonths: 60,
            cadenceCustomDays: null,
            issuingAuthorityType: 'flag',
            isClassTracked: false,
            submissionScope: 'master_only',
            parentId: null,
            relationshipTypeDefault: null,
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: null,
            legacyRemarks: null,
            printOrder: 10,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'dpa-1',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'dpa-1',
          },
          {
            id: 'child-row',
            canonicalCode: 'STAT-IOPP-ANNUAL-SURVEY',
            sectionId: 2,
            sectionName: 'Statutory & Flag',
            displayName: 'Last Annual Survey',
            shortName: null,
            printSectionLabel: 'Statutory & Flag',
            validityType: 'conditional',
            cadenceMonths: 12,
            cadenceCustomDays: null,
            issuingAuthorityType: 'class',
            isClassTracked: true,
            submissionScope: 'master_only',
            parentId: 'parent-row',
            relationshipTypeDefault: 'survey_of',
            applicableShipTypes: ['all'],
            mandatoryForAllVessels: true,
            applicabilityMode: 'all_matching_type',
            specificVesselIds: [],
            parentSupportsDynamicChildren: false,
            ageGateMaxYears: null,
            retainAllVersions: false,
            linkedPmsComponentId: null,
            alertLeadOverrides: null,
            regulatoryAnchor: null,
            legacyRemarks: null,
            printOrder: 11,
            isActive: true,
            createdAt: '2026-06-24T00:00:00Z',
            createdBy: 'dpa-1',
            updatedAt: '2026-06-24T00:00:00Z',
            updatedBy: 'dpa-1',
          },
        ],
      },
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });
    certsRouteMocks.useCatalogRow.mockReturnValue({
      data: {
        id: 'child-row',
        canonicalCode: 'STAT-IOPP-ANNUAL-SURVEY',
        sectionId: 2,
        sectionName: 'Statutory & Flag',
        displayName: 'Last Annual Survey',
        shortName: null,
        printSectionLabel: 'Statutory & Flag',
        validityType: 'conditional',
        cadenceMonths: 12,
        cadenceCustomDays: null,
        issuingAuthorityType: 'class',
        isClassTracked: true,
        submissionScope: 'master_only',
        parentId: 'parent-row',
        relationshipTypeDefault: 'survey_of',
        applicableShipTypes: ['all'],
        mandatoryForAllVessels: true,
        applicabilityMode: 'all_matching_type',
        specificVesselIds: [],
        parentSupportsDynamicChildren: false,
        ageGateMaxYears: null,
        retainAllVersions: false,
        linkedPmsComponentId: null,
        alertLeadOverrides: null,
        regulatoryAnchor: null,
        legacyRemarks: null,
        printOrder: 11,
        isActive: true,
        createdAt: '2026-06-24T00:00:00Z',
        createdBy: 'dpa-1',
        updatedAt: '2026-06-24T00:00:00Z',
        updatedBy: 'dpa-1',
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/catalog/child-row']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Parent row')).toBeInTheDocument();
    expect(screen.getAllByText('STAT-IOPP - International Oil Pollution Prevention Certificate').length).toBeGreaterThan(0);
  });

  it('renders the Certs audit log read screen for CERT_F_008 users', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_008'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useAuditLog.mockReturnValue({
      data: {
        count: 1,
        page: 1,
        pageSize: 25,
        includesColdTier: false,
        results: [
          {
            id: 'audit-1',
            timestampUtc: '2026-06-29T08:30:00Z',
            vesselId: 'vessel-1',
            actorUserId: 'dpa-1',
            actorRole: 'DPA',
            action: 'update_tracked_item',
            entityType: 'tracked_item',
            entityId: 'tracked-1',
            before: { status: 'current' },
            after: { status: 'window_open' },
            reason: 'Annual survey window opened.',
            eventMetadata: { source: 'api.certs.tracked_items' },
            retentionTier: 'hot',
            archivedAt: null,
            schemaVersion: 1,
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/audit-log']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Audit Log')).toBeInTheDocument();
    expect(screen.getByText('Update Tracked Item')).toBeInTheDocument();
    expect(screen.getByText('DPA - dpa-1')).toBeInTheDocument();
    expect(screen.getByText('Annual survey window opened.')).toBeInTheDocument();
    expect(screen.getByText('Changed: status')).toBeInTheDocument();
    expect(certsRouteMocks.useAuditLog).toHaveBeenCalledWith(
      expect.objectContaining({ pageSize: 25 }),
      true
    );
  });

  it('shows the cold-tier prompt before fetching archived audit rows', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_008'),
      hasProcess: vi.fn(() => false),
    });

    render(
      <MemoryRouter initialEntries={['/certs/audit-log']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('Retention tier'), { target: { value: 'cold' } });
    expect(screen.getByText('This range includes archived entries.')).toBeInTheDocument();
    expect(certsRouteMocks.useAuditLog).toHaveBeenLastCalledWith(
      expect.objectContaining({ retentionTier: 'cold' }),
      false
    );
    fireEvent.click(screen.getByRole('button', { name: /Continue/i }));
    expect(certsRouteMocks.useAuditLog).toHaveBeenLastCalledWith(
      expect.objectContaining({ retentionTier: 'cold' }),
      true
    );
  });

  it('renders DPA-only audit export controls and submits current filters', () => {
    const mutate = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_008'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_005'),
    });
    certsRouteMocks.useExportAuditLog.mockReturnValue({
      mutate,
      data: {
        printId: 'SQE-S633-FLEET-20260630-001',
        pdfBlobId: 'pdf-blob',
        excelBlobId: 'csv-blob',
      },
      error: null,
      isError: false,
      isPending: false,
    });

    render(
      <MemoryRouter initialEntries={['/certs/audit-log']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('Action'), { target: { value: 'update_tracked_item' } });
    fireEvent.click(screen.getByRole('button', { name: /Export filtered PDF and CSV/i }));

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        filters: expect.objectContaining({ action: 'update_tracked_item', pageSize: 25 }),
      })
    );
    expect(screen.getByText('Export ready: SQE-S633-FLEET-20260630-001')).toBeInTheDocument();
  });

  it('hides audit export controls from Fleet Manager audit readers', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_008'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_005'),
    });

    render(
      <MemoryRouter initialEntries={['/certs/audit-log']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.queryByRole('button', { name: /Export filtered PDF and CSV/i })).not.toBeInTheDocument();
    expect(certsRouteMocks.useExportAuditLog).not.toHaveBeenCalled();
  });

  it('denies the Certs audit log screen without CERT_F_008', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Master',
      user: { role_name: 'Master' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_002'),
      hasProcess: vi.fn(() => false),
    });

    render(
      <MemoryRouter initialEntries={['/certs/audit-log']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText("You don't have access to this page.")).toBeInTheDocument();
    expect(certsRouteMocks.useAuditLog).not.toHaveBeenCalled();
  });

  it('renders FM read-only external auditor grant visibility after B-EXT-01', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'Fleet Manager',
      user: { role_name: 'Fleet Manager' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_007'),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useAuditorAccessGrants.mockReturnValue({
      data: {
        results: [
          {
            id: 'grant-1',
            auditorName: 'ABS Auditor',
            auditorEmail: 'auditor@example.com',
            scope: { vesselIds: ['vessel-1'], sections: ['SAFETY'], certIds: [] },
            expiryAt: '2026-07-06T00:00:00Z',
            grantedBy: 'marine-1',
            grantedAt: '2026-06-29T00:00:00Z',
            signupTokenUsedAt: null,
            lastAccessedAt: null,
            revokedViaExpiryEdit: false,
          },
        ],
      },
      error: null,
      isError: false,
      isLoading: false,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/certs/auditor-access']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('External auditor access')).toBeInTheDocument();
    expect(screen.getByText('ABS Auditor')).toBeInTheDocument();
    expect(screen.queryByText('New auditor grant')).not.toBeInTheDocument();
  });

  it('lets DPA submit a new external auditor grant', () => {
    const mutate = vi.fn();
    certsRouteMocks.useAuth.mockReturnValue({
      role: 'DPA',
      user: { role_name: 'DPA' },
      hasForm: vi.fn((formId: string) => formId === 'CERT_F_007'),
      hasProcess: vi.fn((processId: string) => processId === 'CERT_P_007'),
    });
    certsRouteMocks.useCreateAuditorAccessGrant.mockReturnValue({ mutate, data: undefined, error: null, isError: false, isPending: false });

    render(
      <MemoryRouter initialEntries={['/certs/auditor-access']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('Auditor name'), { target: { value: 'ABS Auditor' } });
    fireEvent.change(screen.getByLabelText('Auditor email'), { target: { value: 'auditor@example.com' } });
    fireEvent.change(screen.getByLabelText('Vessel IDs or IMOs'), { target: { value: '9876543' } });
    fireEvent.change(screen.getByLabelText('Sections'), { target: { value: 'SAFETY' } });
    fireEvent.click(screen.getByRole('button', { name: /Create grant/i }));

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        auditorName: 'ABS Auditor',
        auditorEmail: 'auditor@example.com',
        scope: expect.objectContaining({ vesselIds: ['9876543'], sections: ['SAFETY'] }),
      })
    );
  });

  it('renders token-bound auditor vessel scope without Certs form permission', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      hasForm: vi.fn(() => false),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useAuditorSignup.mockReturnValue({
      data: { sessionToken: 'session-token', grant: { auditorName: 'ABS Auditor' } },
      error: null,
      isError: false,
      isLoading: false,
    });
    certsRouteMocks.useAuditorVessels.mockReturnValue({
      data: { results: [{ id: 'vessel-1', imo: '9876543', name: 'YC FORTITUDE', code: 'YCF' }] },
      error: null,
      isError: false,
      isLoading: false,
    });

    render(
      <MemoryRouter initialEntries={['/auditor/signup-token']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('VIMS Certificates Audit Portal')).toBeInTheDocument();
    expect(screen.getByText('YC FORTITUDE')).toBeInTheDocument();
    expect(certsRouteMocks.useAuditorSignup).toHaveBeenCalledWith('signup-token');
  });

  it('renders auditor cert detail with redacted internal notes', () => {
    certsRouteMocks.useAuth.mockReturnValue({
      hasForm: vi.fn(() => false),
      hasProcess: vi.fn(() => false),
    });
    certsRouteMocks.useAuditorCert.mockReturnValue({
      data: {
        id: 'cert-1',
        catalogCode: 'CERT-SAFETY-001',
        catalogDisplayName: 'Cargo Ship Safety Equipment Certificate',
        certificateNumber: 'SE-001',
        status: 'ok',
        expiryDate: '2031-01-01',
        issuingAuthority: 'Class',
        extensionReason: '[REDACTED - internal note]',
        rejectionReason: '[REDACTED - internal note]',
      },
      error: null,
      isError: false,
      isLoading: false,
    });

    render(
      <MemoryRouter initialEntries={['/auditor/session-token/cert/cert-1']}>
        <CertsDashboardStubPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Cargo Ship Safety Equipment Certificate')).toBeInTheDocument();
    expect(screen.getAllByText('[REDACTED - internal note]').length).toBeGreaterThan(0);
  });
});
