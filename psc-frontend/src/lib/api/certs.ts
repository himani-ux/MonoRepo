import { apiClient } from '@/lib/api/client';
import { API_BASE_URL } from '@/lib/utils/constants';

const CERTS_API_BASE_URL = `${API_BASE_URL}/api/certs`;
const AUDITOR_API_BASE_URL = `${API_BASE_URL}/api/auditor`;

function buildCertsApiUrl(path: string): string {
  return `${CERTS_API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

function buildAuditorApiUrl(path: string): string {
  return `${AUDITOR_API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export interface CertCatalogSection {
  id: number;
  sectionId: number;
  sectionCode: string;
  displayName: string;
  sortOrder: number;
  activeRowCount: number;
}

export interface CertCatalogRow {
  id: string;
  canonicalCode: string;
  sectionId: number;
  sectionCode?: string;
  sectionName?: string;
  displayName: string;
  shortName: string | null;
  printSectionLabel: string;
  validityType: string;
  cadenceMonths: number | null;
  cadenceCustomDays: number | null;
  issuingAuthorityType: string;
  isClassTracked: boolean;
  submissionScope: string;
  parentId: string | null;
  relationshipTypeDefault: string | null;
  applicableShipTypes: string[];
  mandatoryForAllVessels: boolean;
  applicabilityMode: string;
  specificVesselIds: string[];
  parentSupportsDynamicChildren: boolean;
  ageGateMaxYears: number | null;
  retainAllVersions: boolean;
  linkedPmsComponentId: string | null;
  alertLeadOverrides: Record<string, unknown> | null;
  regulatoryAnchor: string | null;
  legacyRemarks: string | null;
  printOrder: number;
  isActive: boolean;
  createdAt: string;
  createdBy: string;
  updatedAt: string;
  updatedBy: string;
}

export interface CertCatalogRowsResponse {
  count: number;
  page: number | null;
  pageSize: number | null;
  results: CertCatalogRow[];
}

export interface CertCatalogBulkSoftDeletePayload {
  catalogIds: string[];
  reason: string;
}

export interface CertCatalogBulkSoftDeleteResponse {
  requestedCount: number;
  updatedCount: number;
  results: CertCatalogRow[];
}

export interface CertCatalogAuditEntry {
  id: string;
  timestampUtc: string;
  vesselId: string | null;
  actorUserId: string;
  actorRole: string;
  action: string;
  entityType: string;
  entityId: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  reason: string | null;
  eventMetadata: Record<string, unknown> | null;
  retentionTier: string;
  archivedAt: string | null;
  schemaVersion: number;
}

export interface CertCatalogAuditHistoryResponse {
  results: CertCatalogAuditEntry[];
}

export interface CertCatalogSectionsResponse {
  results: CertCatalogSection[];
}

export interface CertAlertConfig {
  id: string;
  triggerEvent: string;
  defaultLeadDays: number;
  dpaOverrideLeadDays: number | null;
  recipientsDefault: string[];
  dpaOverrideRecipients: string[] | null;
  escalationCadence: Record<string, unknown>;
  ocrThresholdOffice: number | string;
  ocrThresholdVessel: number | string;
  ocrThresholdManualFloor: number | string;
  classSnapshotCadenceMonths: number;
  classSnapshotLeadMonths: number;
  eventSnapshotGraceDays: number;
  draftExpireDays: number;
  createdAt: string | null;
  updatedAt: string | null;
  updatedBy: string | null;
}

export interface CertSlackRoute {
  vesselId: string;
  vesselName: string | null;
  imo: string | null;
  slackChannelVessel: string | null;
  slackChannelOfficeDefault: string | null;
  updatedAt: string | null;
  updatedBy: string | null;
}

export interface CertSettingsResponse {
  id: string | null;
  singletonKey: string;
  lastHeartbeatAt: string | null;
  updatedAt: string | null;
  updatedBy: string | null;
  alertConfigs: CertAlertConfig[];
  slackRoutes: CertSlackRoute[];
}

export interface CertRetentionOverridePayload {
  blobId: string;
  dpaRetentionOverrideUntil: string | null;
}

export interface CertSettingsUpdatePayload {
  alertConfigs?: Array<Partial<CertAlertConfig> & { id: string }>;
  retentionOverride?: CertRetentionOverridePayload;
  slackRoutes?: Array<Pick<CertSlackRoute, 'vesselId' | 'slackChannelVessel' | 'slackChannelOfficeDefault'>>;
  reason: string;
}

export interface CertTrackedItem {
  id: string;
  vesselId: string | null;
  vesselName?: string | null;
  vesselCode?: string | null;
  vesselImo?: string | null;
  catalogId: string | null;
  catalogCode: string | null;
  catalogDisplayName: string | null;
  catalogShortName: string | null;
  submissionScope: string | null;
  sectionId?: number;
  sectionCode?: string | null;
  sectionName?: string | null;
  displayName?: string | null;
  shortName?: string | null;
  validityShortCode?: string | null;
  type: string | null;
  validityType: string | null;
  formVariant: string | null;
  cadenceMonths: number | null;
  cadenceCustomDays: number | null;
  parentId: string | null;
  relationshipType: string | null;
  supersedesId: string | null;
  issueDate: string | null;
  expiryDate: string | null;
  anniversaryDate: string | null;
  windowOpen: string | null;
  windowClose: string | null;
  lastDoneDate: string | null;
  nextDueDate: string | null;
  postponedUntil: string | null;
  status: string;
  certificateNumber: string | null;
  issuingAuthority: string | null;
  placeOfIssue: string | null;
  extensionAuthority: string | null;
  extensionLetterPdfId: string | null;
  extensionReason: string | null;
  pdfAttachmentId: string | null;
  pdfMissing: boolean;
  source: string | null;
  lastClassSyncId: string | null;
  approvalState: string | null;
  submittedBy?: string | null;
  submittedByDisplay?: string | null;
  submittedAt?: string | null;
  approvedBy?: string | null;
  approvedByDisplay?: string | null;
  approvedAt?: string | null;
  rejectionReason: string | null;
  rejectionCount?: number | null;
  draftExpiresAt?: string | null;
  lifecycleStatus: string | null;
  rowVersion: string | null;
  version: number | null;
  createdAt?: string | null;
  createdBy?: string | null;
  createdByDisplay?: string | null;
  updatedAt?: string | null;
  updatedBy?: string | null;
  updatedByDisplay?: string | null;
  daysToGo?: number | null;
  isClassTracked?: boolean;
  mandatoryForAllVessels?: boolean;
}

export interface CertTrackedItemsResponse {
  count: number;
  results: CertTrackedItem[];
}

export interface CertTrackedItemFilters {
  vesselId?: string;
  catalogId?: string;
  status?: string;
  approvalState?: string;
}

export interface CertPdfVersion {
  id: string;
  trackedItemId: string | null;
  snapshotId: string | null;
  filename: string;
  sizeBytes: number;
  uploadedBy: string;
  uploadedByDisplay?: string | null;
  uploadedAt: string;
  isActive: boolean;
  supersededAt: string | null;
  retentionPolicy: string;
  scheduledDeleteAt: string | null;
  deletePendingSince: string | null;
  dpaRetentionOverrideUntil: string | null;
  ocrPayload?: CertOcrPayload | null;
  ocrConfidencePerField?: Record<string, number> | null;
  ocrProcessedAt?: string | null;
  ocrEngineVersion?: string | null;
}

export type CertOcrContext = 'office' | 'vessel';
export type CertOcrFieldMode = 'auto_accept' | 'gap_fill' | 'manual_entry';

export interface CertOcrFieldResult {
  value: string | null;
  raw_value: string | null;
  confidence: number;
  mode: CertOcrFieldMode;
  threshold: number;
  manual_floor: number;
  required: boolean;
}

export interface CertOcrPayload {
  schema_version: string;
  engine: string;
  context: CertOcrContext;
  thresholds: {
    auto_accept: number;
    manual_floor: number;
  };
  status: string;
  unprocessable: boolean;
  unprocessable_reason?: string;
  raw_text: string;
  fields: Record<string, CertOcrFieldResult>;
}

export interface CertTrackedItemUploadPdfPayload {
  file: File;
  context?: CertOcrContext;
  reason?: string;
}

export interface CertTrackedItemUploadPdfResponse {
  trackedItem: CertTrackedItemDetail;
  pdfBlob: CertPdfVersion;
  ocrPayload: CertOcrPayload;
  ocrConfidencePerField: Record<string, number>;
}

export interface CertTrackedItemMetadataUpdatePayload {
  certificateNumber?: string | null;
  issuingAuthority?: string | null;
  placeOfIssue?: string | null;
  issueDate?: string | null;
  expiryDate?: string | null;
  reason?: string | null;
}

export interface CertTrackedItemRemovePdfPayload {
  reason: string;
}

export interface CertTrackedItemRemovePdfResponse {
  trackedItem: CertTrackedItemDetail;
  removedPdfBlob: CertPdfVersion;
  restoredPdfBlob: CertPdfVersion | null;
}

export interface CertApprovalEvent {
  id: string;
  fromState: string;
  toState: string;
  actorUserId: string;
  actorDisplayName?: string | null;
  actorRole: string;
  reason: string | null;
  timestampUtc: string;
}

export interface CertTrackedItemAuditEvent {
  id: string;
  timestampUtc: string;
  vesselId: string | null;
  actorUserId: string;
  actorDisplayName?: string | null;
  actorRole: string;
  action: string;
  entityType: string;
  entityId: string | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  reason: string | null;
  eventMetadata: Record<string, unknown> | null;
  retentionTier: string;
  archivedAt: string | null;
  schemaVersion: number;
}

export interface CertAuditLogEntry {
  id: string;
  timestampUtc: string;
  vesselId: string | null;
  actorUserId: string;
  actorRole: string;
  action: string;
  entityType: string;
  entityId: string | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  reason: string | null;
  eventMetadata: Record<string, unknown> | null;
  retentionTier: string;
  archivedAt: string | null;
  schemaVersion: number;
}

export interface CertAuditLogFilters {
  vesselId?: string | null;
  actorUserId?: string | null;
  action?: string | null;
  entityType?: string | null;
  retentionTier?: string | null;
  dateFrom?: string | null;
  dateTo?: string | null;
  page?: number | null;
  pageSize?: number | null;
}

export interface CertAuditLogResponse {
  count: number;
  page: number;
  pageSize: number;
  includesColdTier: boolean;
  results: CertAuditLogEntry[];
}

export interface CertAuditLogExportPayload {
  filters: CertAuditLogFilters;
}

export interface CertAuditorGrantScope {
  vesselIds: string[];
  sections: string[];
  certIds: string[];
}

export interface CertAuditorAccessGrant {
  id: string;
  auditorName: string;
  auditorEmail: string;
  scope: CertAuditorGrantScope;
  expiryAt: string;
  grantedBy: string;
  grantedAt: string;
  signupTokenUsedAt: string | null;
  lastAccessedAt: string | null;
  revokedViaExpiryEdit: boolean;
  signupUrl?: string;
}

export interface CertAuditorAccessGrantsResponse {
  results: CertAuditorAccessGrant[];
}

export interface CertAuditorAccessCreatePayload {
  auditorName: string;
  auditorEmail: string;
  scope: CertAuditorGrantScope;
  expiryAt?: string;
}

export interface CertAuditorAccessExpiryPayload {
  expiryAt: string;
}

export interface CertAuditorSignupResponse {
  sessionToken: string;
  grant: CertAuditorAccessGrant;
}

export interface CertAuditorVessel {
  id: string;
  imo: string;
  name: string;
  code?: string | null;
}

export interface CertAuditorVesselsResponse {
  results: CertAuditorVessel[];
}

export interface CertAuditorCertsResponse {
  results: CertTrackedItem[];
}

export interface CertAuditorPrintResponse {
  watermarkApplied: 'AUDIT_COPY';
  watermarkRecipient: string;
  watermarkText: string;
  scope: CertAuditorGrantScope;
}

export interface CertChangeHistoryEntry {
  id: string;
  fieldName: string;
  oldValue: unknown;
  newValue: unknown;
  versionAfter: number;
  sourceModule: string;
  sourceRef: string | null;
  changedBy: string | null;
  changedByDisplay?: string | null;
  changedAt: string;
}

export interface CertTrackedItemDetail extends CertTrackedItem {
  pdfVersions: CertPdfVersion[];
  approvalEvents: CertApprovalEvent[];
  auditEvents: CertTrackedItemAuditEvent[];
  changeHistory: CertChangeHistoryEntry[];
}

export interface CertTrackedItemTransitionPayload {
  reason: string;
  version?: number | null;
}

export interface CertVesselDashboardSection {
  sectionId: number;
  sectionCode: string;
  displayName: string;
  activeTrackedItemCount: number;
  actionItemCount: number;
  statusBreakdown: Record<string, number>;
  items: CertTrackedItem[];
}

export interface CertCoverageMissingItem {
  catalogId: string | null;
  catalogCode: string | null;
  displayName: string | null;
  shortName: string | null;
  sectionId: number | null;
  sectionCode: string | null;
  sectionName: string | null;
  trackedItemId: string | null;
  status: string | null;
  reason: 'missing_tracked_item' | 'pending_first_upload';
}

export interface CertVesselDashboardResponse {
  vessel: {
    id: string;
    imo: string | null;
    code: string | null;
    name: string | null;
    flag: string | null;
    classSociety: string | null;
    shipType: string | null;
    currentMaster: string | null;
    lifecycleStatus: string;
    pendingDisposalStartedAt: string | null;
    saleHandoverBundleBlobId?: string | null;
    flagChangePending: boolean;
    flagChangeEvent?: Record<string, unknown> | null;
    classChangePending?: boolean;
    iwsAgeGateDisabled: boolean;
  };
  mandatoryCoverage: {
    percent: number;
    mandatoryCount: number;
    coveredCount: number;
    missing?: CertCoverageMissingItem[];
    overrideActive: boolean;
    overrideReason: string | null;
    overrideAt: string | null;
    overrideBy: string | null;
  };
  lastClassSnapshot: {
    id: string;
    classSociety: string | null;
    uploadedAt: string | null;
    daysAgo: number | null;
    parseStatus: string | null;
    reconciliationRunId: string | null;
  } | null;
  sections: CertVesselDashboardSection[];
  summary: {
    totalTrackedItems: number;
    actionItemCount: number;
    pdfMissingCount: number;
    classTrackedCount: number;
  };
}

export interface CertVesselLifecycleConfig {
  vesselId: string | null;
  anniversaryDate: string | null;
  shipType: string | null;
  marineSuptUserId: string | null;
  technicalManagerUserId: string | null;
  lifecycleStatus: string | null;
  pendingDisposalStartedAt: string | null;
  saleHandoverBundleBlobId: string | null;
  flagChangePending: boolean;
  flagChangeEvent: Record<string, unknown> | null;
  classChangePending: boolean;
  mandatoryCoverageOverrideReason: string | null;
  mandatoryCoverageOverrideAt: string | null;
  mandatoryCoverageOverrideBy: string | null;
  iwsAgeGateDisabled: boolean;
  updatedAt: string | null;
  updatedBy: string | null;
}

export interface CertVesselLifecycleResponse {
  vessel: CertOnboardingVessel;
  config: CertVesselLifecycleConfig | null;
  affectedTrackedItems: number;
  saleHandoverArtifact?: {
    printId: string;
    bundleZipBlobId: string | null;
    systemStateHash: string | null;
  } | null;
}

export interface CertFlagChangePayload {
  newFlagState: string;
  effectiveDate: string;
  reason: string;
}

export interface CertClassChangePayload {
  newClassSociety: string;
  effectiveDate: string;
  reason: string;
}

export interface CertSaleHandoverPayload {
  handoverDate: string;
  customCertIds?: string[];
  watermarkRecipient?: string;
  reason: string;
}

export interface CertDecommissionPayload {
  decommissionDate: string;
  reason: string;
}

export interface CertHighVolumePrintUser {
  userId: string;
  userRole: string;
  printCountLastHour: number;
  lastPrintAt: string | null;
  lastSignalAt: string | null;
}

export interface CertBouncingEmailUser {
  userId: string;
  lastBouncedAt: string | null;
  criticalFallbackCount: number;
}

export interface CertFleetDashboardVessel {
  id: string;
  name: string | null;
  code: string | null;
  imo: string | null;
  lifecycleStatus: string | null;
  trackedItemCount: number;
  actionItemCount: number;
  pdfMissingCount: number;
}

export interface CertFleetDashboardResponse {
  onboardedVessels?: CertFleetDashboardVessel[];
  highVolumePrintActivity?: {
    thresholdPerHour: number;
    windowMinutes: number;
    usersAboveThresholdCount: number;
    users: CertHighVolumePrintUser[];
  };
  bouncingEmailDelivery?: {
    bouncingUsersCount: number;
    users: CertBouncingEmailUser[];
  };
  cadenceHeartbeat?: {
    lastCadenceHeartbeat: string | null;
  };
}

export interface CertClassSnapshot {
  id: string;
  vesselId: string | null;
  vesselName: string | null;
  imo: string | null;
  classSociety: string | null;
  pdfBlobId: string | null;
  filename: string | null;
  sizeBytes: number | null;
  printedOnDate: string | null;
  uploadedBy: string | null;
  uploadedAt: string | null;
  parserVersion: string | null;
  parseStatus: string | null;
  parseStartedAt: string | null;
  parseCompletedAt: string | null;
  parserTimeout: boolean;
  retryCount: number | null;
  parsedPayload: Record<string, unknown> | unknown[] | null;
  parsedPayloadSchemaVersion: number | null;
  reconciliationRunId: string | null;
  uploadSha256: string | null;
  supersededUserError: boolean;
}

export interface CertClassSnapshotUploadPayload {
  vesselId: string;
  classSociety: string;
  printedOnDate?: string | null;
  file: File;
}

export interface CertClassSnapshotReparseResponse {
  snapshot: CertClassSnapshot;
  reconciliationRun: CertReconciliationRun | null;
}

export interface CertClassSnapshotFilters {
  vesselId?: string | null;
  classSociety?: string | null;
  pageSize?: number | null;
}

export interface CertClassSnapshotsResponse {
  count: number;
  results: CertClassSnapshot[];
}

export interface CertReconciliationAnomalyBreach {
  type?: string;
  severity?: string;
  message?: string;
  value?: number;
  threshold?: number;
  count?: number;
  total?: number;
  actual?: number;
  expectedClassTrackedRows?: number;
  expectedMinimum?: number;
  thresholdFactor?: number;
  valueSeconds?: number;
  thresholdSeconds?: number;
}

export interface CertReconciliationRun {
  id: string;
  snapshotId: string | null;
  vesselId: string | null;
  vesselName: string | null;
  imo: string | null;
  classSociety: string | null;
  printedOnDate: string | null;
  parseStatus: string | null;
  parserVersion: string | null;
  ranAt: string | null;
  matchesCount: number | null;
  mismatchesCount: number | null;
  missingInCatalogCount: number | null;
  missingInClassCount: number | null;
  conditionalStcDetectedCount: number | null;
  extendedPostponedDetectedCount: number | null;
  unmappedLowConfidenceCount: number | null;
  notificationsSent: unknown[];
  mappingVersionUsed: number | null;
  anomalyBreaches: CertReconciliationAnomalyBreach[];
}

export interface CertReconciliationFlag {
  id: string;
  runId: string | null;
  bucket: string | null;
  catalogId: string | null;
  catalogDisplayName: string | null;
  trackedItemId: string | null;
  classRowExtract: Record<string, unknown> | unknown[] | null;
  diff: Record<string, unknown>;
  reviewedBy: string | null;
  reviewedAt: string | null;
  resolutionAction: string | null;
  resolvedAt: string | null;
}

export interface CertReconciliationRunDetail extends CertReconciliationRun {
  flags: CertReconciliationFlag[];
}

export interface CertMasterReconciliationMessage {
  id: string;
  runId: string | null;
  snapshotId: string | null;
  vesselId: string | null;
  vesselName: string | null;
  imo: string | null;
  classSociety: string | null;
  printedOnDate: string | null;
  ranAt: string | null;
  bucket: string | null;
  catalogId: string | null;
  catalogDisplayName: string | null;
  trackedItemId: string | null;
  classRowExtract: Record<string, unknown> | unknown[] | null;
  diff: Record<string, unknown>;
  officeNotifiedAt: string | null;
  officeNotifiedBy: string | null;
  officeNotifiedRole: string | null;
  officeNote: string | null;
  masterReviewedAt: string | null;
  masterReviewedBy: string | null;
  masterReviewedRole: string | null;
  masterReviewNote: string | null;
}

export interface CertMasterReconciliationMessageFilters {
  includeReviewed?: boolean;
  vesselId?: string | null;
  pageSize?: number | null;
}

export interface CertMasterReconciliationMessagesResponse {
  count: number;
  results: CertMasterReconciliationMessage[];
}

export interface CertClassCodeMapping {
  id: string;
  classSociety: string | null;
  classCodeOrName: string | null;
  catalogId: string | null;
  certOrSurveyKind: string | null;
  notes: string | null;
  version: number | null;
  active: boolean;
  createdAt: string | null;
  createdBy: string | null;
  updatedAt: string | null;
  updatedBy: string | null;
}

export interface CertAddClassMappingPayload {
  catalogId: string;
  certOrSurveyKind: string;
  notes?: string | null;
  reason: string;
}

export interface CertAddClassMappingResponse {
  mapping: CertClassCodeMapping;
  flag: CertReconciliationFlag | null;
  reconciliationRun: CertReconciliationRun | null;
}

export interface CertReconciliationRunFilters {
  vesselId?: string | null;
  bucket?: string | null;
  pageSize?: number | null;
}

export interface CertReconciliationRunsResponse {
  count: number;
  results: CertReconciliationRun[];
}

export interface CertOnboardingVessel {
  id: string | null;
  code: string | null;
  name: string | null;
  imo: string | null;
  flag: string | null;
  classSociety: string | null;
}

export interface CertVesselConfig {
  vesselId: string | null;
  anniversaryDate: string | null;
  shipType: string | null;
  marineSuptUserId: string | null;
  technicalManagerUserId: string | null;
  lifecycleStatus: string | null;
  mandatoryCoverageOverrideReason: string | null;
  mandatoryCoverageOverrideAt: string | null;
  mandatoryCoverageOverrideBy: string | null;
  updatedAt: string | null;
  updatedBy: string | null;
}

export interface CertOnboardingBatch {
  id: string;
  onboardingSessionId: string | null;
  pdfBlobIds: string[];
  pdfCount: number;
  status: string;
  createdAt: string | null;
  createdBy: string | null;
  ocrCompletedAt: string | null;
  reviewStartedAt: string | null;
  committedAt: string | null;
  committedBy: string | null;
  cancelledAt: string | null;
  cancelledBy: string | null;
  validationBlocks: CertValidationEntry[];
  validationWarns: CertValidationEntry[];
  reportCsvBlobId: string | null;
}

export interface CertValidationEntry {
  code: string;
  severity: 'block' | 'warn';
  message: string;
  blobId?: string | null;
  filename?: string | null;
  field?: string | null;
  value?: string | null;
  certificateNumber?: string | null;
}

export interface CertOnboardingValidationPreview {
  batchId?: string;
  pdfCount: number;
  attachmentCount: number;
  commitCount: number;
  blockCount: number;
  warnCount: number;
}

export interface CertOnboardingValidationResult {
  batch: CertOnboardingBatch;
  validationBlocks: CertValidationEntry[];
  validationWarns: CertValidationEntry[];
  canCommit: boolean;
  requiresWarningAck: boolean;
  preview: CertOnboardingValidationPreview;
}

export interface CertOnboardingHubRow {
  vessel: CertOnboardingVessel;
  config: CertVesselConfig | null;
  batchCount: number;
  currentStep: number;
  mandatoryCoveragePercent: number;
  pendingFmSignoff: boolean;
  lastActivity: string | null;
  startedAt: string | null;
  startedBy: string | null;
}

export interface CertOnboardingHubResponse {
  results: CertOnboardingHubRow[];
}

export interface CertOnboardingStep {
  number: number;
  label: string;
  status: 'complete' | 'current' | 'locked';
}

export interface CertOnboardingCoverage {
  percent: number;
  mandatoryCount: number;
  coveredCount: number;
  missing?: CertCoverageMissingItem[];
  overrideActive: boolean;
  overrideReason: string | null;
  overrideAt: string | null;
  overrideBy: string | null;
}

export interface CertOnboardingWizardState {
  vessel: CertOnboardingVessel;
  config: CertVesselConfig | null;
  steps: CertOnboardingStep[];
  currentStep: number;
  batches: CertOnboardingBatch[];
  mandatoryCoverage: CertOnboardingCoverage;
  trackedItems: CertTrackedItem[];
}

export interface CertGapFillFieldState {
  field: string;
  value: string | null;
  rawValue: string | null;
  confidence: number | null;
  mode: CertOcrFieldMode;
  required: boolean;
}

export interface CertGapFillPdf extends CertPdfVersion {
  trackedItem: CertTrackedItem | null;
  fieldStates: CertGapFillFieldState[];
}

export interface CertOnboardingGapFillState {
  batch: CertOnboardingBatch;
  vessel: CertOnboardingVessel;
  pdfs: CertGapFillPdf[];
}

export interface CertOnboardingProfilePayload {
  anniversaryDate: string;
  shipType: string;
  marineSuptUserId?: string | null;
  technicalManagerUserId?: string | null;
}

export interface CertOnboardingBatchPayload {
  pdfBlobIds: string[];
  onboardingSessionId?: string | null;
}

export interface CertOnboardingCommitPayload {
  acknowledgeWarnings: boolean;
  supersedeDecisions?: Array<{
    blobId: string;
    existingBlobId: string;
    confirm: boolean;
  }>;
}

export interface CertCatalogInlinePromotionContext {
  source: 'onboarding_gap_fill';
  vesselId: string;
  batchId?: string;
}

export interface CertCatalogRowInput {
  canonicalCode?: string;
  sectionId?: number;
  displayName?: string;
  shortName?: string | null;
  printSectionLabel?: string;
  validityType?: string;
  cadenceMonths?: number | null;
  cadenceCustomDays?: number | null;
  issuingAuthorityType?: string;
  isClassTracked?: boolean;
  submissionScope?: string;
  parentId?: string | null;
  applicableShipTypes?: string[];
  mandatoryForAllVessels?: boolean;
  applicabilityMode?: string;
  specificVesselIds?: string[];
  parentSupportsDynamicChildren?: boolean;
  ageGateMaxYears?: number | null;
  retainAllVersions?: boolean;
  linkedPmsComponentId?: string | null;
  regulatoryAnchor?: string | null;
  legacyRemarks?: string | null;
  printOrder?: number;
  isActive?: boolean;
  reason?: string;
  inlinePromotion?: CertCatalogInlinePromotionContext;
}

export interface CertCatalogRowFilters {
  sectionId?: number | null;
  isActive?: boolean | null;
  q?: string;
  applicableShipType?: string | null;
  page?: number | null;
  pageSize?: number | null;
}

export type CertPrintScope = 'per_vessel_full' | 'per_vessel_partial' | 'per_section_fleetwide' | 'custom_selection' | 'share_bundle' | 'audit_log_export';
export type CertPrintWatermark = 'NONE' | 'INTERNAL' | 'AUDIT_COPY' | 'MASTER_COPY' | 'DRAFT';

export interface CertPrintArtifact {
  printId: string;
  scope: CertPrintScope;
  vessels: string[];
  sections: string[];
  filters: Record<string, unknown>;
  customCertIds: string[];
  userId: string;
  userRole: string;
  timestampUtc: string | null;
  systemStateHash: string;
  watermarkApplied: CertPrintWatermark;
  watermarkRecipient: string;
  pdfBlobId: string | null;
  excelBlobId: string | null;
  bundleZipBlobId: string | null;
  recipientEmail: string;
  pageCount: number | null;
  generationStatus: string;
  failureMessage: string;
}

export interface CertPrintArtifactsResponse {
  results: CertPrintArtifact[];
}

export interface CertPrintPayload {
  scope: Exclude<CertPrintScope, 'share_bundle' | 'audit_log_export'>;
  vesselIds?: string[];
  sections?: string[];
  filters?: Record<string, unknown>;
  customCertIds?: string[];
  watermarkApplied?: CertPrintWatermark;
  watermarkRecipient?: string;
  recipientEmail?: string;
}

export interface CertShareBundlePayload {
  vesselIds: string[];
  customCertIds: string[];
  watermarkRecipient?: string;
  recipientEmail?: string;
}

export interface CertPrintArtifactFilters {
  pageSize?: number | null;
}

function appendIfPresent(params: URLSearchParams, key: string, value: string | number | boolean | null | undefined): void {
  if (value !== undefined && value !== null && value !== '') {
    params.set(key, String(value));
  }
}

function buildParams(filters: CertCatalogRowFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.sectionId) params.set('sectionId', String(filters.sectionId));
  if (filters.isActive !== undefined && filters.isActive !== null) {
    params.set('isActive', String(filters.isActive));
  }
  if (filters.q) params.set('q', filters.q);
  if (filters.applicableShipType) {
    params.set('applicableShipType', filters.applicableShipType);
  }
  appendIfPresent(params, 'page', filters.page);
  appendIfPresent(params, 'pageSize', filters.pageSize);
  return params;
}

function buildClassSnapshotParams(filters: CertClassSnapshotFilters): URLSearchParams {
  const params = new URLSearchParams();
  appendIfPresent(params, 'vesselId', filters.vesselId);
  appendIfPresent(params, 'classSociety', filters.classSociety);
  appendIfPresent(params, 'pageSize', filters.pageSize);
  return params;
}

function buildReconciliationRunParams(filters: CertReconciliationRunFilters): URLSearchParams {
  const params = new URLSearchParams();
  appendIfPresent(params, 'vesselId', filters.vesselId);
  appendIfPresent(params, 'bucket', filters.bucket);
  appendIfPresent(params, 'pageSize', filters.pageSize);
  return params;
}

function buildPrintArtifactParams(filters: CertPrintArtifactFilters): URLSearchParams {
  const params = new URLSearchParams();
  appendIfPresent(params, 'pageSize', filters.pageSize);
  return params;
}

function buildAuditLogParams(filters: CertAuditLogFilters): URLSearchParams {
  const params = new URLSearchParams();
  appendIfPresent(params, 'vesselId', filters.vesselId);
  appendIfPresent(params, 'actorUserId', filters.actorUserId);
  appendIfPresent(params, 'action', filters.action);
  appendIfPresent(params, 'entityType', filters.entityType);
  appendIfPresent(params, 'retentionTier', filters.retentionTier);
  appendIfPresent(params, 'dateFrom', filters.dateFrom);
  appendIfPresent(params, 'dateTo', filters.dateTo);
  appendIfPresent(params, 'page', filters.page);
  appendIfPresent(params, 'pageSize', filters.pageSize);
  return params;
}

export const certsApi = {
  async getCatalogSections(): Promise<CertCatalogSection[]> {
    const response = await apiClient.get<CertCatalogSectionsResponse>(
      buildCertsApiUrl('/catalog/sections/')
    );
    return response.data.results;
  },

  async getCatalogRows(filters: CertCatalogRowFilters = {}): Promise<CertCatalogRowsResponse> {
    const params = buildParams(filters);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get<CertCatalogRowsResponse>(
      buildCertsApiUrl(`/catalog/rows/${suffix}`)
    );
    return response.data;
  },

  async getCatalogRow(id: string): Promise<CertCatalogRow> {
    const response = await apiClient.get<CertCatalogRow>(
      buildCertsApiUrl(`/catalog/rows/${id}/`)
    );
    return response.data;
  },

  async getCatalogRowAuditHistory(id: string): Promise<CertCatalogAuditEntry[]> {
    const response = await apiClient.get<CertCatalogAuditHistoryResponse>(
      buildCertsApiUrl(`/catalog/rows/${id}/audit/`)
    );
    return response.data.results;
  },

  async getAuditLog(filters: CertAuditLogFilters = {}): Promise<CertAuditLogResponse> {
    const params = buildAuditLogParams(filters);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get<CertAuditLogResponse>(
      buildCertsApiUrl(`/audit-log/${suffix}`)
    );
    return response.data;
  },

  async getAuditLogEntry(id: string): Promise<CertAuditLogEntry> {
    const response = await apiClient.get<CertAuditLogEntry>(
      buildCertsApiUrl(`/audit-log/${encodeURIComponent(id)}/`)
    );
    return response.data;
  },

  async getSettings(): Promise<CertSettingsResponse> {
    const response = await apiClient.get<CertSettingsResponse>(
      buildCertsApiUrl('/settings/')
    );
    return response.data;
  },

  async updateSettings(payload: CertSettingsUpdatePayload): Promise<CertSettingsResponse> {
    const response = await apiClient.patch<CertSettingsResponse>(
      buildCertsApiUrl('/settings/'),
      payload
    );
    return response.data;
  },

  async exportAuditLog(payload: CertAuditLogExportPayload): Promise<CertPrintArtifact> {
    const response = await apiClient.post<CertPrintArtifact>(
      buildCertsApiUrl('/audit-log/export/'),
      payload
    );
    return response.data;
  },

  async getAuditorAccessGrants(): Promise<CertAuditorAccessGrantsResponse> {
    const response = await apiClient.get<CertAuditorAccessGrantsResponse>(
      buildCertsApiUrl('/auditor-access/')
    );
    return response.data;
  },

  async getAuditorAccessGrant(id: string): Promise<CertAuditorAccessGrant> {
    const response = await apiClient.get<CertAuditorAccessGrant>(
      buildCertsApiUrl(`/auditor-access/${encodeURIComponent(id)}/`)
    );
    return response.data;
  },

  async createAuditorAccessGrant(payload: CertAuditorAccessCreatePayload): Promise<CertAuditorAccessGrant> {
    const response = await apiClient.post<CertAuditorAccessGrant>(
      buildCertsApiUrl('/auditor-access/'),
      payload
    );
    return response.data;
  },

  async updateAuditorAccessGrantExpiry(id: string, payload: CertAuditorAccessExpiryPayload): Promise<CertAuditorAccessGrant> {
    const response = await apiClient.patch<CertAuditorAccessGrant>(
      buildCertsApiUrl(`/auditor-access/${encodeURIComponent(id)}/`),
      payload
    );
    return response.data;
  },

  async signupAuditor(token: string): Promise<CertAuditorSignupResponse> {
    const response = await apiClient.post<CertAuditorSignupResponse>(
      buildAuditorApiUrl(`/signup/${encodeURIComponent(token)}/`),
      {}
    );
    return response.data;
  },

  async getAuditorVessels(sessionToken: string): Promise<CertAuditorVesselsResponse> {
    const response = await apiClient.get<CertAuditorVesselsResponse>(
      buildAuditorApiUrl(`/${encodeURIComponent(sessionToken)}/vessels/`)
    );
    return response.data;
  },

  async getAuditorVesselCerts(sessionToken: string, imo: string): Promise<CertAuditorCertsResponse> {
    const response = await apiClient.get<CertAuditorCertsResponse>(
      buildAuditorApiUrl(`/${encodeURIComponent(sessionToken)}/vessels/${encodeURIComponent(imo)}/certs/`)
    );
    return response.data;
  },

  async getAuditorCert(sessionToken: string, certId: string): Promise<CertTrackedItem> {
    const response = await apiClient.get<CertTrackedItem>(
      buildAuditorApiUrl(`/${encodeURIComponent(sessionToken)}/cert/${encodeURIComponent(certId)}/`)
    );
    return response.data;
  },

  async generateAuditorPrint(sessionToken: string, payload: { trackedItemIds?: string[] } = {}): Promise<CertAuditorPrintResponse> {
    const response = await apiClient.post<CertAuditorPrintResponse>(
      buildAuditorApiUrl(`/${encodeURIComponent(sessionToken)}/print/`),
      payload
    );
    return response.data;
  },

  async createCatalogRow(payload: CertCatalogRowInput): Promise<CertCatalogRow> {
    const { inlinePromotion, ...body } = payload;
    const params = new URLSearchParams();
    if (inlinePromotion?.source === 'onboarding_gap_fill') {
      params.set('source', 'onboarding_gap_fill');
      params.set('vesselId', inlinePromotion.vesselId);
      if (inlinePromotion.batchId) {
        params.set('batchId', inlinePromotion.batchId);
      }
    }
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.post<CertCatalogRow>(
      buildCertsApiUrl(`/catalog/rows/${suffix}`),
      body
    );
    return response.data;
  },

  async updateCatalogRow(id: string, payload: CertCatalogRowInput): Promise<CertCatalogRow> {
    const response = await apiClient.patch<CertCatalogRow>(
      buildCertsApiUrl(`/catalog/rows/${id}/`),
      payload
    );
    return response.data;
  },

  async deprecateCatalogRow(id: string, payload: { reason: string }): Promise<CertCatalogRow> {
    const response = await apiClient.post<CertCatalogRow>(
      buildCertsApiUrl(`/catalog/rows/${id}/deprecate/`),
      payload
    );
    return response.data;
  },

  async bulkSoftDeleteCatalogRows(payload: CertCatalogBulkSoftDeletePayload): Promise<CertCatalogBulkSoftDeleteResponse> {
    const response = await apiClient.post<CertCatalogBulkSoftDeleteResponse>(
      buildCertsApiUrl('/catalog/rows/bulk-soft-delete/'),
      payload
    );
    return response.data;
  },

  async hardPurgeCatalogRow(id: string, payload: { reason: string }): Promise<void> {
    await apiClient.delete(
      buildCertsApiUrl(`/catalog/rows/${id}/`),
      { data: payload }
    );
  },

  async getVesselDashboard(imo: string): Promise<CertVesselDashboardResponse> {
    const response = await apiClient.get<CertVesselDashboardResponse>(
      buildCertsApiUrl(`/dashboard/vessel/${encodeURIComponent(imo)}/`)
    );
    return response.data;
  },

  async getVesselProfile(imo: string): Promise<CertVesselLifecycleResponse> {
    const response = await apiClient.get<CertVesselLifecycleResponse>(
      buildCertsApiUrl(`/vessel/${encodeURIComponent(imo)}/profile/`)
    );
    return response.data;
  },

  async recordFlagChange(imo: string, payload: CertFlagChangePayload): Promise<CertVesselLifecycleResponse> {
    const response = await apiClient.post<CertVesselLifecycleResponse>(
      buildCertsApiUrl(`/vessel/${encodeURIComponent(imo)}/flag-change/`),
      payload
    );
    return response.data;
  },

  async recordClassChange(imo: string, payload: CertClassChangePayload): Promise<CertVesselLifecycleResponse> {
    const response = await apiClient.post<CertVesselLifecycleResponse>(
      buildCertsApiUrl(`/vessel/${encodeURIComponent(imo)}/class-change/`),
      payload
    );
    return response.data;
  },

  async initiateSaleHandover(imo: string, payload: CertSaleHandoverPayload): Promise<CertVesselLifecycleResponse> {
    const response = await apiClient.post<CertVesselLifecycleResponse>(
      buildCertsApiUrl(`/vessel/${encodeURIComponent(imo)}/sale-handover/`),
      payload
    );
    return response.data;
  },

  async decommissionVessel(imo: string, payload: CertDecommissionPayload): Promise<CertVesselLifecycleResponse> {
    const response = await apiClient.post<CertVesselLifecycleResponse>(
      buildCertsApiUrl(`/vessel/${encodeURIComponent(imo)}/decommission/`),
      payload
    );
    return response.data;
  },

  async getFleetDashboard(): Promise<CertFleetDashboardResponse> {
    const response = await apiClient.get<CertFleetDashboardResponse>(
      buildCertsApiUrl('/dashboard/fleet/')
    );
    return response.data;
  },

  async getClassSnapshots(filters: CertClassSnapshotFilters = {}): Promise<CertClassSnapshotsResponse> {
    const params = buildClassSnapshotParams(filters);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get<CertClassSnapshotsResponse>(
      buildCertsApiUrl(`/class-snapshots/${suffix}`)
    );
    return response.data;
  },

  async getClassSnapshot(id: string): Promise<CertClassSnapshot> {
    const response = await apiClient.get<CertClassSnapshot>(
      buildCertsApiUrl(`/class-snapshots/${encodeURIComponent(id)}/`)
    );
    return response.data;
  },

  async uploadClassSnapshot(payload: CertClassSnapshotUploadPayload): Promise<CertClassSnapshot> {
    const formData = new FormData();
    formData.append('vesselId', payload.vesselId);
    formData.append('classSociety', payload.classSociety);
    if (payload.printedOnDate) {
      formData.append('printedOnDate', payload.printedOnDate);
    }
    formData.append('file', payload.file);
    const response = await apiClient.post<CertClassSnapshot>(
      buildCertsApiUrl('/class-snapshots/'),
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  async reparseClassSnapshot(id: string): Promise<CertClassSnapshotReparseResponse> {
    const response = await apiClient.post<CertClassSnapshotReparseResponse>(
      buildCertsApiUrl(`/class-snapshots/${encodeURIComponent(id)}/reparse/`),
      {}
    );
    return response.data;
  },

  async getReconciliationRuns(filters: CertReconciliationRunFilters = {}): Promise<CertReconciliationRunsResponse> {
    const params = buildReconciliationRunParams(filters);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get<CertReconciliationRunsResponse>(
      buildCertsApiUrl(`/reconciliation/runs/${suffix}`)
    );
    return response.data;
  },

  async getReconciliationRun(id: string): Promise<CertReconciliationRunDetail> {
    const response = await apiClient.get<CertReconciliationRunDetail>(
      buildCertsApiUrl(`/reconciliation/runs/${encodeURIComponent(id)}/`)
    );
    return response.data;
  },

  async markReconciliationFlagReviewed(id: string, reason: string): Promise<CertReconciliationFlag> {
    const response = await apiClient.post<CertReconciliationFlag>(
      buildCertsApiUrl(`/reconciliation/flags/${encodeURIComponent(id)}/mark-reviewed/`),
      { reason }
    );
    return response.data;
  },

  async notifyMasterForReconciliationFlag(id: string, reason: string): Promise<CertReconciliationFlag> {
    const response = await apiClient.post<CertReconciliationFlag>(
      buildCertsApiUrl(`/reconciliation/flags/${encodeURIComponent(id)}/notify-master/`),
      { reason }
    );
    return response.data;
  },

  async getMasterReconciliationMessages(
    filters: CertMasterReconciliationMessageFilters = {}
  ): Promise<CertMasterReconciliationMessagesResponse> {
    const params = new URLSearchParams();
    if (filters.includeReviewed) params.set('includeReviewed', 'true');
    if (filters.vesselId) params.set('vesselId', filters.vesselId);
    if (filters.pageSize) params.set('pageSize', String(filters.pageSize));
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get<CertMasterReconciliationMessagesResponse>(
      buildCertsApiUrl(`/reconciliation/master-messages/${suffix}`)
    );
    return response.data;
  },

  async acknowledgeMasterReconciliationMessage(id: string, note: string): Promise<CertMasterReconciliationMessage> {
    const response = await apiClient.post<CertMasterReconciliationMessage>(
      buildCertsApiUrl(`/reconciliation/master-messages/${encodeURIComponent(id)}/ack/`),
      { note }
    );
    return response.data;
  },

  async addClassCodeMappingForFlag(id: string, payload: CertAddClassMappingPayload): Promise<CertAddClassMappingResponse> {
    const response = await apiClient.post<CertAddClassMappingResponse>(
      buildCertsApiUrl(`/reconciliation/flags/${encodeURIComponent(id)}/add-mapping/`),
      payload
    );
    return response.data;
  },

  async generatePrintArtifact(payload: CertPrintPayload): Promise<CertPrintArtifact> {
    const response = await apiClient.post<CertPrintArtifact>(
      buildCertsApiUrl('/print/'),
      payload
    );
    return response.data;
  },

  async getPrintArtifacts(filters: CertPrintArtifactFilters = {}): Promise<CertPrintArtifactsResponse> {
    const params = buildPrintArtifactParams(filters);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get<CertPrintArtifactsResponse>(
      buildCertsApiUrl(`/print/artifacts/${suffix}`)
    );
    return response.data;
  },

  async getPrintArtifact(printId: string): Promise<CertPrintArtifact> {
    const response = await apiClient.get<CertPrintArtifact>(
      buildCertsApiUrl(`/print/artifacts/${encodeURIComponent(printId)}/`)
    );
    return response.data;
  },

  async generateShareBundle(payload: CertShareBundlePayload): Promise<CertPrintArtifact> {
    const response = await apiClient.post<CertPrintArtifact>(
      buildCertsApiUrl('/print/share-bundle/'),
      payload
    );
    return response.data;
  },

  async getTrackedItemDetail(id: string): Promise<CertTrackedItemDetail> {
    const response = await apiClient.get<CertTrackedItemDetail>(
      buildCertsApiUrl(`/tracked-items/${id}/`)
    );
    return response.data;
  },

  async getTrackedItems(filters: CertTrackedItemFilters = {}): Promise<CertTrackedItemsResponse> {
    const params = new URLSearchParams();
    if (filters.vesselId) params.set('vesselId', filters.vesselId);
    if (filters.catalogId) params.set('catalogId', filters.catalogId);
    if (filters.status) params.set('status', filters.status);
    if (filters.approvalState) params.set('approvalState', filters.approvalState);
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get<CertTrackedItemsResponse>(
      buildCertsApiUrl(`/tracked-items/${suffix}`)
    );
    return response.data;
  },

  async submitTrackedItem(id: string, payload: CertTrackedItemTransitionPayload): Promise<CertTrackedItemDetail> {
    const response = await apiClient.post<CertTrackedItemDetail>(
      buildCertsApiUrl(`/tracked-items/${id}/submit/`),
      payload
    );
    return response.data;
  },

  async approveTrackedItem(id: string, payload: CertTrackedItemTransitionPayload): Promise<CertTrackedItemDetail> {
    const response = await apiClient.post<CertTrackedItemDetail>(
      buildCertsApiUrl(`/tracked-items/${id}/approve/`),
      payload
    );
    return response.data;
  },

  async rejectTrackedItem(id: string, payload: CertTrackedItemTransitionPayload): Promise<CertTrackedItemDetail> {
    const response = await apiClient.post<CertTrackedItemDetail>(
      buildCertsApiUrl(`/tracked-items/${id}/reject/`),
      payload
    );
    return response.data;
  },

  async updateTrackedItemMetadata(id: string, payload: CertTrackedItemMetadataUpdatePayload): Promise<CertTrackedItemDetail> {
    const response = await apiClient.patch<CertTrackedItemDetail>(
      buildCertsApiUrl(`/tracked-items/${id}/`),
      payload
    );
    return response.data;
  },

  async getTrackedItemPdfBlob(trackedItemId: string, blobId: string): Promise<Blob> {
    const response = await apiClient.get<Blob>(
      buildCertsApiUrl(`/tracked-items/${encodeURIComponent(trackedItemId)}/pdfs/${encodeURIComponent(blobId)}/view/`),
      { responseType: 'blob' }
    );
    return response.data;
  },

  async uploadTrackedItemPdf(id: string, payload: CertTrackedItemUploadPdfPayload): Promise<CertTrackedItemUploadPdfResponse> {
    const formData = new FormData();
    formData.append('file', payload.file);
    if (payload.context) {
      formData.append('context', payload.context);
    }
    if (payload.reason) {
      formData.append('reason', payload.reason);
    }
    const response = await apiClient.post<CertTrackedItemUploadPdfResponse>(
      buildCertsApiUrl(`/tracked-items/${id}/upload-pdf/`),
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  async removeTrackedItemPdf(id: string, payload: CertTrackedItemRemovePdfPayload): Promise<CertTrackedItemRemovePdfResponse> {
    const response = await apiClient.post<CertTrackedItemRemovePdfResponse>(
      buildCertsApiUrl(`/tracked-items/${id}/remove-pdf/`),
      payload
    );
    return response.data;
  },

  async getOnboardingHub(): Promise<CertOnboardingHubResponse> {
    const response = await apiClient.get<CertOnboardingHubResponse>(
      buildCertsApiUrl('/onboarding/')
    );
    return response.data;
  },

  async getOnboardingWizardState(vesselId: string): Promise<CertOnboardingWizardState> {
    const response = await apiClient.get<CertOnboardingWizardState>(
      buildCertsApiUrl(`/onboarding/${encodeURIComponent(vesselId)}/`)
    );
    return response.data;
  },

  async saveOnboardingProfile(vesselId: string, payload: CertOnboardingProfilePayload): Promise<unknown> {
    const response = await apiClient.post(
      buildCertsApiUrl(`/onboarding/${encodeURIComponent(vesselId)}/profile/`),
      payload
    );
    return response.data;
  },

  async createOnboardingBatch(vesselId: string, payload: CertOnboardingBatchPayload): Promise<CertOnboardingBatch> {
    const response = await apiClient.post<CertOnboardingBatch>(
      buildCertsApiUrl(`/onboarding/${encodeURIComponent(vesselId)}/batch/`),
      payload
    );
    return response.data;
  },

  async getOnboardingBatchGapFill(batchId: string): Promise<CertOnboardingGapFillState> {
    const response = await apiClient.get<CertOnboardingGapFillState>(
      buildCertsApiUrl(`/onboarding/batch/${encodeURIComponent(batchId)}/`)
    );
    return response.data;
  },

  async previewOnboardingBatch(batchId: string): Promise<CertOnboardingValidationResult> {
    const response = await apiClient.post<CertOnboardingValidationResult>(
      buildCertsApiUrl(`/onboarding/batch/${encodeURIComponent(batchId)}/preview/`),
      {}
    );
    return response.data;
  },

  async commitOnboardingBatch(
    batchId: string,
    payload: CertOnboardingCommitPayload
  ): Promise<CertOnboardingValidationResult> {
    const response = await apiClient.post<CertOnboardingValidationResult>(
      buildCertsApiUrl(`/onboarding/batch/${encodeURIComponent(batchId)}/commit/`),
      payload
    );
    return response.data;
  },

  async saveCoverageOverride(vesselId: string, reason: string): Promise<unknown> {
    const response = await apiClient.post(
      buildCertsApiUrl(`/onboarding/${encodeURIComponent(vesselId)}/coverage-override/`),
      { reason }
    );
    return response.data;
  },

  async fmSignoff(vesselId: string, reason: string): Promise<unknown> {
    const response = await apiClient.post(
      buildCertsApiUrl(`/onboarding/${encodeURIComponent(vesselId)}/fm-signoff/`),
      { reason }
    );
    return response.data;
  },

  async rollbackOnboarding(vesselId: string, reason: string): Promise<unknown> {
    const response = await apiClient.post(
      buildCertsApiUrl(`/onboarding/${encodeURIComponent(vesselId)}/rollback/`),
      { reason }
    );
    return response.data;
  },
};
