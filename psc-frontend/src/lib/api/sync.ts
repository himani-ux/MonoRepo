/**
 * Sync API functions
 *
 * Handles all sync-related API calls per BACKEND_STRUCTURE.md Section 10.9.
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: PRD.md FEAT-SYNC-002, FEAT-SYNC-003, FEAT-SYNC-005
 */

import { apiClient } from './client';
import type { SyncConflict } from '@/types';

// ============================================================================
// Types — Pull (FEAT-SYNC-002)
// ============================================================================

/** Request for POST /api/psc/sync/pull/ */
export interface SyncPullRequest {
  vessel_id: string;
  last_sync_token?: string | null;
  last_server_version: number;
}

/** Individual inspection record from pull response */
export interface SyncInspection {
  id: number;
  vessel_id: number;
  inspection_type: string;
  psc_subtype: string | null;
  inspection_date: string;
  port_place: string;
  country: string;
  mou_id: string | null;
  authority: string | null;
  inspector_name: string | null;
  report_reference: string | null;
  is_detention: boolean;
  parent_inspection_id: number | null;
  revision_no: number;
  status: string;
  pic_comment: string | null;
  pic_reviewed_by: string | null;
  pic_reviewed_at: string | null;
  dpa_comment: string | null;
  dpa_closed_by: string | null;
  dpa_closed_at: string | null;
  is_deleted: boolean;
  created_by: string;
  created_date: string;
  updated_by: string | null;
  updated_date: string | null;
  client_id: string | null;
  sync_version: number;
}

/** Inspection report from pull response */
export interface SyncInspectionReport {
  id: number;
  inspection_id: number;
  file_name: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  description: string | null;
  is_deleted: boolean;
  uploaded_by: string;
  uploaded_at: string;
}

/** Deficiency record from pull response */
export interface SyncDeficiency {
  id: number;
  inspection_id: number;
  def_code_id: string;
  def_code: string;
  description: string;
  action_code_id: string | null;
  action_code: string | null;
  target_date: string | null;
  is_cleared: boolean;
  cleared_date: string | null;
  cleared_by_follow_up_id: number | null;
  sequence_no: number;
  car_id: number | null;
  is_deleted: boolean;
  created_by: string;
  created_date: string;
  updated_by: string | null;
  updated_date: string | null;
  client_id: string | null;
  sync_version: number;
}

/** CAR record from pull response */
export interface SyncCAR {
  id: number;
  car_number: string;
  status: string;
  root_cause_summary: string | null;
  target_date: string | null;
  rework_count: number;
  pic_comment: string | null;
  pic_accepted_by: string | null;
  pic_accepted_at: string | null;
  rework_reason: string | null;
  rework_requested_by: string | null;
  rework_requested_at: string | null;
  dpa_comment: string | null;
  dpa_closed_by: string | null;
  dpa_closed_at: string | null;
  is_deleted: boolean;
  created_by: string;
  created_date: string;
  updated_by: string | null;
  updated_date: string | null;
  client_id: string | null;
  sync_version: number;
}

/** Corrective action from pull response */
export interface SyncCorrectiveAction {
  id: number;
  car_id: number;
  action_type: string;
  description: string;
  owner_crew_id: string | null;
  owner_user_id: string | null;
  due_date: string | null;
  is_completed: boolean;
  completed_at: string | null;
  completion_remarks: string | null;
  sequence_no: number;
  is_deleted: boolean;
  created_by: string;
  created_date: string;
  updated_by: string | null;
  updated_date: string | null;
  client_id: string | null;
  sync_version: number;
}

/** Evidence metadata from pull response */
export interface SyncEvidence {
  id: number;
  car_id: number;
  evidence_type: string;
  file_name: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  description: string | null;
  is_deleted: boolean;
  uploaded_by: string;
  uploaded_at: string;
  client_id: string | null;
}

/** Activity history from pull response */
export interface SyncActivityHistory {
  id: number;
  entity_type: string;
  entity_id: number;
  vessel_id: number;
  event_type: string;
  event_description: string;
  performed_by: string;
  performed_by_name: string;
  performed_at: string;
  metadata: Record<string, unknown> | null;
}

/** Data payload in pull response */
export interface SyncPullData {
  inspections: SyncInspection[];
  inspection_reports: SyncInspectionReport[];
  deficiencies: SyncDeficiency[];
  cars: SyncCAR[];
  corrective_actions: SyncCorrectiveAction[];
  evidence_metadata: SyncEvidence[];
  activity_history: SyncActivityHistory[];
  masters?: Record<string, unknown[]>;
}

/** Response from POST /api/psc/sync/pull/ */
export interface SyncPullResponse {
  data: SyncPullData;
  sync_token: string;
  server_version: number;
}

// ============================================================================
// Types — Push (FEAT-SYNC-003)
// ============================================================================

/** Individual sync event within a push request */
export interface SyncPushEvent {
  event_id: string;
  entity_type: 'INSPECTION' | 'DEFICIENCY' | 'CAR' | 'CORRECTIVE_ACTION' | 'EVIDENCE';
  entity_id: string;
  client_id?: string | null;
  operation: 'CREATE' | 'UPDATE' | 'DELETE';
  client_version: number;
  data: Record<string, unknown>;
  timestamp: string;
}

/** Attachment metadata within a push request */
export interface SyncPushAttachment {
  client_id: string;
  car_id: string;
  evidence_type: 'BEFORE' | 'AFTER';
  file_name: string;
  file_size: number;
}

/** Request for POST /api/psc/sync/push/ */
export interface SyncPushRequest {
  sync_id: string;
  vessel_id: string;
  checksum: string;
  events: SyncPushEvent[];
  attachments: SyncPushAttachment[];
}

/** Upload URL for a single attachment */
export interface AttachmentUploadURL {
  client_id: string;
  upload_url: string;
  expires_at: string;
}

/** Inner data of push response */
export interface SyncPushResponseData {
  sync_id: string;
  processed: number;
  failed: number;
  conflicts: string[];
  id_mappings: Record<string, string>;
  attachment_upload_urls: AttachmentUploadURL[];
}

/** Response from POST /api/psc/sync/push/ */
export interface SyncPushResponse {
  data: SyncPushResponseData;
}

// ============================================================================
// Types — Conflict Resolution (FEAT-SYNC-005)
// ============================================================================

/** Request for POST /api/psc/sync/resolve-conflict/ */
export interface ConflictResolveRequest {
  conflict_id: string;
  resolution: 'KEEP_SERVER' | 'KEEP_VESSEL' | 'REOPEN_FOR_MERGE';
  notes?: string;
}

/** Response from POST /api/psc/sync/resolve-conflict/ */
export interface ConflictResolveResponse {
  data: SyncConflict;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Pull changes from server to vessel (delta sync).
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: FEAT-SYNC-002
 */
export async function pullChanges(
  request: SyncPullRequest
): Promise<SyncPullResponse> {
  const { data } = await apiClient.post<SyncPullResponse>(
    '/sync/pull/',
    request
  );
  return data;
}

/**
 * Push changes from vessel to server.
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: FEAT-SYNC-003
 */
export async function pushChanges(
  request: SyncPushRequest
): Promise<SyncPushResponse> {
  const { data } = await apiClient.post<SyncPushResponse>(
    '/sync/push/',
    request
  );
  return data;
}

/**
 * Resolve a sync conflict (Office/DPA only).
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: FEAT-SYNC-005
 */
export async function resolveConflict(
  request: ConflictResolveRequest
): Promise<ConflictResolveResponse> {
  const { data } = await apiClient.post<ConflictResolveResponse>(
    '/sync/resolve-conflict/',
    request
  );
  return data;
}

/** Response from GET /api/psc/sync/conflicts/ */
export interface ConflictListResponse {
  data: SyncConflict[];
}

/**
 * Get unresolved sync conflicts.
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: FEAT-SYNC-004
 */
export async function getConflicts(): Promise<SyncConflict[]> {
  const { data } = await apiClient.get<ConflictListResponse>(
    '/sync/conflicts/'
  );
  return data.data;
}
