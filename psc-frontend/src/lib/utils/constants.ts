/**
 * Application constants
 * Centralized configuration values used throughout the app
 */

// API Configuration
const RAW_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function normalizeApiBaseUrl(value: string): string {
  return value
    .trim()
    .replace(/\/+$/, '')
    .replace(/\/api\/(?:psc|safety)$/i, '')
    .replace(/\/api$/i, '');
}

export const API_BASE_URL = normalizeApiBaseUrl(RAW_API_BASE_URL);
export const API_PREFIX = '/api/psc';

// Authentication
export const ACCESS_TOKEN_KEY = 'access_token';
export const REFRESH_TOKEN_KEY = 'refresh_token';
export const TOKEN_EXPIRY_BUFFER_MS = 60 * 1000; // Refresh 1 minute before expiry

// File Upload Constraints
export const MAX_FILE_SIZE_BYTES = 3 * 1024 * 1024; // 3MB
export const MAX_FILE_SIZE_MB = 3;
export const ALLOWED_FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg'];
export const ALLOWED_FILE_EXTENSIONS = ['.pdf', '.jpg', '.jpeg'];

// Offline Storage
export const OFFLINE_STORAGE_LIMIT_MB = 150;
export const OFFLINE_STORAGE_WARNING_THRESHOLD_MB = 10;
export const SYNC_RETRY_ATTEMPTS = 3;
export const SYNC_RETRY_DELAYS_MS = [1000, 2000, 4000]; // Exponential backoff

// Validation Constraints
export const ROOT_CAUSE_MIN_LENGTH = 50;
export const REWORK_REASON_MIN_LENGTH = 20;

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Stale Times for TanStack Query (milliseconds)
export const STALE_TIME = {
  MASTERS: 24 * 60 * 60 * 1000, // 24 hours - master data rarely changes
  INSPECTIONS: 5 * 60 * 1000, // 5 minutes
  CARS: 5 * 60 * 1000, // 5 minutes
  NOTIFICATIONS: 60 * 1000, // 1 minute
  DASHBOARD: 5 * 60 * 1000, // 5 minutes
} as const;

// Inspection Types
export const INSPECTION_TYPES = {
  PSC: 'PSC',
  RS: 'RS',
  AUDIT: 'AUDIT',
} as const;

// PSC Subtypes
export const PSC_SUBTYPES = {
  INITIAL: 'INITIAL',
  EXPANDED: 'EXPANDED',
  CIC: 'CIC',
  FOLLOW_UP: 'FOLLOW_UP',
} as const;

// Inspection Status (legacy stored workflow)
export const INSPECTION_STATUS = {
  DRAFT: 'DRAFT',
  SUBMITTED: 'SUBMITTED',
  PIC_REVIEWED: 'PIC_REVIEWED',
  DPA_CLOSED: 'DPA_CLOSED',
} as const;

// Operational Status (computed from deficiency action_code_id)
export const OPERATIONAL_STATUS = {
  OPEN: 'OPEN',
  CLOSED: 'CLOSED',
} as const;

// CAR Status (unified workflow)
export const CAR_STATUS = {
  ALLOTTED: 'ALLOTTED',
  IN_PROGRESS: 'IN_PROGRESS',
  PENDING_CE_REVIEW: 'PENDING_CE_REVIEW',
  PENDING_MASTER_REVIEW: 'PENDING_MASTER_REVIEW',
  SUBMITTED_TO_PIC: 'SUBMITTED_TO_PIC',
  PIC_REVIEW: 'PIC_REVIEW',
  SUBMITTED_TO_DPA: 'SUBMITTED_TO_DPA',
  CLOSED: 'CLOSED',
  RETURNED_FOR_REWORK: 'RETURNED_FOR_REWORK',
} as const;

// Workflow Actions (named transitions)
export const WORKFLOW_ACTIONS = {
  START_WORK: 'START_WORK',
  MARK_COMPLETED: 'MARK_COMPLETED',
  SUBMIT_FOR_CE_REVIEW: 'SUBMIT_FOR_CE_REVIEW',
  SUBMIT_FOR_MASTER_REVIEW: 'SUBMIT_FOR_MASTER_REVIEW',
  APPROVE_AND_FORWARD: 'APPROVE_AND_FORWARD',
  RETURN_FOR_REWORK: 'RETURN_FOR_REWORK',
  SUBMIT_TO_PIC: 'SUBMIT_TO_PIC',
  START_PIC_REVIEW: 'START_PIC_REVIEW',
  SUBMIT_TO_DPA: 'SUBMIT_TO_DPA',
  CLOSE_CAR: 'CLOSE_CAR',
  REOPEN_CAR: 'REOPEN_CAR',
  REQUEST_REWORK: 'REQUEST_REWORK',
} as const;

// Evidence Types
export const EVIDENCE_TYPES = {
  BEFORE: 'BEFORE',
  AFTER: 'AFTER',
  EVIDENCE: 'EVIDENCE',
  OTHER: 'OTHER',
} as const;

// Corrective Action Types
export const ACTION_TYPES = {
  IMMEDIATE: 'IMMEDIATE',
  LONG_TERM: 'LONG_TERM',
} as const;

// User Roles
export const USER_ROLES = {
  VESSEL_MASTER: 'VESSEL_MASTER',
  VESSEL_CREW: 'VESSEL_CREW',
  OFFICE_PIC: 'OFFICE_PIC',
  OFFICE_SSQE: 'OFFICE_SSQE',
  OFFICE_SUPT: 'OFFICE_SUPT',
  DPA: 'DPA',
  PHYSICAL_VERIFIER: 'PHYSICAL_VERIFIER',
} as const;

// Sync Status
export const SYNC_STATUS = {
  PENDING: 'PENDING',
  IN_PROGRESS: 'IN_PROGRESS',
  COMPLETED: 'COMPLETED',
  FAILED: 'FAILED',
  CONFLICT: 'CONFLICT',
} as const;

// Breakpoints (matching Tailwind config)
export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

// Date Formats
export const DATE_FORMAT = {
  DISPLAY: 'dd MMM yyyy', // 05 Feb 2026
  DISPLAY_WITH_TIME: 'dd MMM yyyy HH:mm', // 05 Feb 2026 14:30
  ISO: 'yyyy-MM-dd', // 2026-02-05
  API: 'yyyy-MM-dd', // 2026-02-05
} as const;

// Route Paths
export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  HELP: '/help',
  INSPECTIONS: '/inspections',
  INSPECTION_NEW: '/inspections/new',
  INSPECTION_DETAIL: (id: string | number) => `/inspections/${id}`,
  INSPECTION_EDIT: (id: string | number) => `/inspections/${id}/edit`,
  INSPECTION_FOLLOW_UP: (id: string | number) => `/inspections/${id}/follow-up`,
  DEFICIENCIES: '/deficiencies',
  CARS: '/cars',
  CAR_DETAIL: (id: string | number) => `/cars/${id}`,
  CAR_EDIT: (id: string | number) => `/cars/${id}/edit`,
  NOTIFICATIONS: '/notifications',
  SYNC: '/sync',
  CIRCULAR: '/circular',
  ORB: '/orb',
  CERTS: '/certs',
  CERTS_CATALOG: '/certs/catalog',
  CERTS_CATALOG_DETAIL: (id: string) => `/certs/catalog/${id}`,
  CERTS_VESSEL_DASHBOARD: (imo: string) => `/certs/vessels/${imo}`,
  CERTS_VESSEL_PROFILE: (imo: string) => `/certs/vessels/${imo}/profile`,
  CERTS_TRACKED_ITEM_DETAIL: (imo: string, id: string) => `/certs/vessels/${imo}/cert/${id}`,
  CERTS_RECONCILIATION: '/certs/reconciliation',
  CERTS_PARSER_OPS: '/certs/reconciliation/parser-ops',
  CERTS_RECONCILIATION_RUN: (id: string) => `/certs/reconciliation/${id}`,
  CERTS_PRINT: '/certs/print',
  CERTS_PRINT_HISTORY: '/certs/print/history',
  CERTS_SHARE_BUNDLE: '/certs/share-bundle',
  CERTS_AUDIT_LOG: '/certs/audit-log',
  CERTS_SETTINGS: '/certs/settings',
  CERTS_AUDITOR_ACCESS: '/certs/auditor-access',
  CERTS_AUDITOR_ACCESS_DETAIL: (id: string) => `/certs/auditor-access/${id}`,
  CERTS_AUDITOR_PORTAL: (token: string) => `/auditor/${token}`,
  CERTS_AUDITOR_VESSEL: (token: string, imo: string) => `/auditor/${token}/vessels/${imo}`,
  CERTS_AUDITOR_CERT: (token: string, id: string) => `/auditor/${token}/cert/${id}`,
  CERTS_AUDITOR_PRINT: (token: string) => `/auditor/${token}/print`,
  CERTS_ONBOARDING: '/certs/onboarding',
  CERTS_ONBOARDING_NEW: '/certs/onboarding/new',
  CERTS_ONBOARDING_WIZARD: (imo: string) => `/certs/onboarding/${imo}`,
  CERTS_ONBOARDING_GAP_FILL: (imo: string, batchId: string) => `/certs/onboarding/${imo}/batch/${batchId}/gap-fill`,
} as const;
