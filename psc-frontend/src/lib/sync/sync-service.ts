/**
 * Sync Service — orchestrates pull/push sync between vessel and server.
 *
 * Source: FRONTEND_GUIDELINES.md §7
 * Implements: PRD.md FEAT-SYNC-002 (pull), FEAT-SYNC-003 (push), FEAT-SYNC-004 (conflicts)
 */

import { useSyncStore } from '@/stores/sync-store';
import { useAuthStore } from '@/stores/auth-store';
import {
  pullChanges,
  pushChanges,
  type SyncPullResponse,
  type SyncPushEvent,
  type SyncPushAttachment,
  type SyncPushResponse,
} from '@/lib/api/sync';
import {
  bulkPutInspections,
  removeInspection,
  bulkPutDeficiencies,
  removeDeficiency,
} from '@/lib/db/inspections';
import { bulkPutCARs, removeCAR } from '@/lib/db/cars';
import { bulkPutMasterData } from '@/lib/db/masters';
import {
  getRetryableSyncQueue,
  updateSyncQueueItem,
  clearCompletedFromQueue,
  countPendingSyncQueue,
} from '@/lib/db/sync-queue';
import { isStorageNearlyFull } from '@/lib/db';
import { SYNC_STATUS } from '@/lib/utils/constants';
import type { SyncStatus } from '@/types';
import { uploadAttachments, registerFileForUpload } from './attachment-uploader';

// ============================================================================
// Constants
// ============================================================================

/** Fields that should never be sent in push events */
const PUSH_READONLY_FIELDS = new Set([
  'id',
  'created_date',
  'created_by',
  'sync_version',
  'car_number',
]);

/** Client-only payload fields that should never be sent to sync push API */
const CLIENT_ONLY_FIELDS = new Set([
  'file',
  'blob',
  '__upload_blob',
]);

/** Sync state persisted in localStorage */
const SYNC_STORAGE_KEY = 'sync-server-version';
const SYNC_TOKEN_KEY = 'sync-token';

// ============================================================================
// Helpers
// ============================================================================

/** Get the last server version from localStorage */
function getLastServerVersion(): number {
  const stored = localStorage.getItem(SYNC_STORAGE_KEY);
  return stored ? parseInt(stored, 10) : 0;
}

/** Save server version to localStorage */
function setLastServerVersion(version: number): void {
  localStorage.setItem(SYNC_STORAGE_KEY, String(version));
}

/** Get the last sync token from localStorage */
function getLastSyncToken(): string | null {
  return localStorage.getItem(SYNC_TOKEN_KEY);
}

/** Save sync token to localStorage */
function setLastSyncToken(token: string): void {
  localStorage.setItem(SYNC_TOKEN_KEY, token);
}

/** Generate a UUID v4 */
function generateUUID(): string {
  return crypto.randomUUID();
}

/**
 * Generate SHA-256 checksum of the push payload.
 * Used for integrity verification by the server.
 */
async function generateChecksum(payload: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(payload);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Strip readonly fields from event data before sending to server.
 * Per BACKEND_STRUCTURE.md: server filters these out on push.
 */
function stripReadonlyFields(
  data: Record<string, unknown>
): Record<string, unknown> {
  const cleaned: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(data)) {
    if (!PUSH_READONLY_FIELDS.has(key) && !CLIENT_ONLY_FIELDS.has(key)) {
      cleaned[key] = value;
    }
  }
  return cleaned;
}

/** Extract attachment file/blob from queue item payload if present. */
function getAttachmentFileFromData(
  data: Record<string, unknown>
): File | Blob | null {
  const candidate = data.file ?? data.blob ?? data.__upload_blob;
  if (typeof Blob !== 'undefined' && candidate instanceof Blob) {
    return candidate;
  }
  return null;
}

// ============================================================================
// Pull — Server to Vessel (FEAT-SYNC-002)
// ============================================================================

/**
 * Pull changes from server and merge into IndexedDB.
 *
 * - Uses delta sync via last_server_version
 * - Handles is_deleted records (removes from IndexedDB)
 * - Saves sync_token and server_version for next pull
 * - Checks storage before pull
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: FEAT-SYNC-002
 */
export async function pullFromServer(): Promise<{
  recordCount: number;
  serverVersion: number;
}> {
  const syncStore = useSyncStore.getState();
  const user = useAuthStore.getState().user;

  if (!user?.vessel_id) {
    throw new Error('Cannot pull: no vessel_id on current user');
  }

  // Check storage before pulling
  if (await isStorageNearlyFull()) {
    throw new Error(
      'Storage nearly full (<10MB remaining). Free space before syncing.'
    );
  }

  const lastServerVersion = getLastServerVersion();
  const lastSyncToken = getLastSyncToken();

  // Call pull API
  const response: SyncPullResponse = await pullChanges({
    vessel_id: user.vessel_id,
    last_sync_token: lastSyncToken,
    last_server_version: lastServerVersion,
  });

  const { data, sync_token, server_version } = response;

  // Merge into IndexedDB — separate active records from deleted
  let recordCount = 0;

  // --- Inspections ---
  if (data.inspections.length > 0) {
    const active = data.inspections.filter((r) => !r.is_deleted);
    const deleted = data.inspections.filter((r) => r.is_deleted);

    if (active.length > 0) {
      // Cast to match IndexedDB store type (sync data has superset of fields)
      await bulkPutInspections(active as never[]);
    }
    for (const record of deleted) {
      await removeInspection(record.id);
    }
    recordCount += data.inspections.length;
  }

  // --- Deficiencies ---
  if (data.deficiencies.length > 0) {
    const active = data.deficiencies.filter((r) => !r.is_deleted);
    const deleted = data.deficiencies.filter((r) => r.is_deleted);

    if (active.length > 0) {
      await bulkPutDeficiencies(active as never[]);
    }
    for (const record of deleted) {
      await removeDeficiency(record.id);
    }
    recordCount += data.deficiencies.length;
  }

  // --- CARs ---
  if (data.cars.length > 0) {
    const active = data.cars.filter((r) => !r.is_deleted);
    const deleted = data.cars.filter((r) => r.is_deleted);

    if (active.length > 0) {
      await bulkPutCARs(active as never[]);
    }
    for (const record of deleted) {
      await removeCAR(record.id);
    }
    recordCount += data.cars.length;
  }

  // --- Master data (bulk upsert, no delete handling needed) ---
  if (data.masters && Object.keys(data.masters).length > 0) {
    await bulkPutMasterData(data.masters);
    recordCount += Object.values(data.masters).reduce((count, value) => {
      return count + (Array.isArray(value) ? value.length : 0);
    }, 0);
  }

  // The corrective_actions, evidence_metadata, activity_history are stored
  // alongside their parent entities in the app — not in separate IDB stores
  recordCount += data.corrective_actions.length;
  recordCount += data.evidence_metadata.length;
  recordCount += data.activity_history.length;
  recordCount += data.inspection_reports.length;

  // Save sync state
  setLastServerVersion(server_version);
  setLastSyncToken(sync_token);
  syncStore.setLastSyncTime(new Date().toISOString());

  return { recordCount, serverVersion: server_version };
}

// ============================================================================
// Push — Vessel to Server (FEAT-SYNC-003)
// ============================================================================

/**
 * Push queued changes from vessel to server.
 *
 * - Reads pending sync queue items in FIFO order
 * - Builds push request with events + attachment metadata
 * - Processes id_mappings, conflicts, and attachment upload URLs
 * - Clears completed items from queue
 *
 * Source: BACKEND_STRUCTURE.md §10.9
 * Implements: FEAT-SYNC-003, FEAT-SYNC-004
 */
export async function pushToServer(): Promise<{
  processed: number;
  failed: number;
  conflicts: number;
}> {
  const user = useAuthStore.getState().user;
  const syncStore = useSyncStore.getState();

  if (!user?.vessel_id) {
    throw new Error('Cannot push: no vessel_id on current user');
  }

  // Get retryable items from sync queue (FIFO via autoIncrement key)
  const pendingItems = await getRetryableSyncQueue();

  if (pendingItems.length === 0) {
    return { processed: 0, failed: 0, conflicts: 0 };
  }

  // Mark all as IN_PROGRESS
  for (const item of pendingItems) {
    if (item.id != null) {
      await updateSyncQueueItem(Number(item.id), {
        status: SYNC_STATUS.IN_PROGRESS as SyncStatus,
      });
    }
  }

  // Build sync events from queue items
  const events: SyncPushEvent[] = pendingItems.map((item) => ({
    event_id: generateUUID(),
    entity_type: mapEntityType(item.entity_type),
    entity_id: String(item.entity_id),
    client_id: item.entity_type === 'EVIDENCE' ? String(item.entity_id) : null,
    operation: item.operation,
    client_version: (item.data?.sync_version as number) ?? 0,
    data: stripReadonlyFields(item.data),
    timestamp: item.created_at,
  }));

  // Extract attachment metadata from EVIDENCE CREATE events
  const attachmentItemIdByClientId = new Map<string, number>();
  const attachments: SyncPushAttachment[] = pendingItems
    .filter(
      (item) => item.entity_type === 'EVIDENCE' && item.operation === 'CREATE'
    )
    .map((item) => {
      const clientId = String(item.entity_id);
      if (item.id != null) {
        attachmentItemIdByClientId.set(clientId, Number(item.id));
      }

      const file = getAttachmentFileFromData(item.data);
      if (file) {
        registerFileForUpload(clientId, file);
      }

      return {
        client_id: clientId,
        car_id: String(item.data?.car_id ?? ''),
        evidence_type: (item.data?.evidence_type as 'BEFORE' | 'AFTER') ?? 'BEFORE',
        file_name: (item.data?.file_name as string) ?? '',
        file_size: (item.data?.file_size as number) ?? 0,
      };
    });

  // Generate idempotency key and checksum
  const syncId = generateUUID();
  const eventsPayload = JSON.stringify(events);
  const checksum = await generateChecksum(eventsPayload);

  // Call push API
  const response: SyncPushResponse = await pushChanges({
    sync_id: syncId,
    vessel_id: user.vessel_id,
    checksum,
    events,
    attachments,
  });

  const result = response.data;

  const attachmentClientIds = new Set(
    result.attachment_upload_urls.map((item) => item.client_id)
  );

  // Process push results for each queue item
  for (const item of pendingItems) {
    if (item.id == null) continue;
    const itemId = Number(item.id);

    // Check if this item's entity had a conflict
    const isConflict = result.conflicts.some(
      (conflictId) => conflictId === String(item.entity_id)
    );

    if (isConflict) {
      await updateSyncQueueItem(itemId, {
        status: SYNC_STATUS.CONFLICT as SyncStatus,
        error_message: 'Conflict detected — awaiting resolution',
      });
      continue;
    }

    // Evidence CREATE items with upload URLs are finalized after upload attempts.
    const isAttachmentAwaitingUpload =
      item.entity_type === 'EVIDENCE' &&
      item.operation === 'CREATE' &&
      attachmentClientIds.has(String(item.entity_id));

    if (!isAttachmentAwaitingUpload) {
      // Successfully processed — mark completed
      await updateSyncQueueItem(itemId, {
        status: SYNC_STATUS.COMPLETED as SyncStatus,
      });
    }
  }

  // Process ID mappings (client_id → server_id)
  if (Object.keys(result.id_mappings).length > 0) {
    await processIdMappings(result.id_mappings);
  }

  let attachmentFailures = 0;

  // Upload attachments if any upload URLs were returned
  if (result.attachment_upload_urls.length > 0) {
    try {
      const uploadResult = await uploadAttachments(result.attachment_upload_urls);

      for (const item of uploadResult.results) {
        const queueItemId = attachmentItemIdByClientId.get(item.client_id);
        if (queueItemId == null) continue;

        if (item.success) {
          await updateSyncQueueItem(queueItemId, {
            status: SYNC_STATUS.COMPLETED as SyncStatus,
            error_message: null,
          });
        } else {
          attachmentFailures += 1;
          await updateSyncQueueItem(queueItemId, {
            status: SYNC_STATUS.FAILED as SyncStatus,
            error_message: item.error ?? 'Attachment upload failed',
          });
        }
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Attachment upload failed';
      console.error('Attachment upload failed:', error);

      for (const clientId of attachmentClientIds) {
        const queueItemId = attachmentItemIdByClientId.get(clientId);
        if (queueItemId == null) continue;
        attachmentFailures += 1;
        await updateSyncQueueItem(queueItemId, {
          status: SYNC_STATUS.FAILED as SyncStatus,
          error_message: errorMessage,
        });
      }
    }
  }

  // Cleanup completed items
  await clearCompletedFromQueue();

  // Update sync store
  const remainingPending = await countPendingSyncQueue();
  syncStore.setPendingChanges(remainingPending);
  syncStore.setConflicts(result.conflicts.length);

  return {
    processed: result.processed,
    failed: result.failed + attachmentFailures,
    conflicts: result.conflicts.length,
  };
}

// ============================================================================
// Full Sync — Pull then Push
// ============================================================================

/**
 * Perform a full sync cycle: pull from server, then push local changes.
 *
 * Source: FRONTEND_GUIDELINES.md §7
 * Implements: FEAT-SYNC-002, FEAT-SYNC-003
 */
export async function fullSync(): Promise<{
  pullRecords: number;
  pushProcessed: number;
  pushFailed: number;
  conflicts: number;
}> {
  const syncStore = useSyncStore.getState();

  if (syncStore.syncInProgress) {
    throw new Error('Sync already in progress');
  }

  syncStore.setSyncInProgress(true);
  syncStore.setLastSyncError(null);

  try {
    // Step 1: Pull from server (get latest data)
    const pullResult = await pullFromServer();

    // Step 2: Push local changes
    const pushResult = await pushToServer();

    // Update sync time
    syncStore.setLastSyncTime(new Date().toISOString());

    return {
      pullRecords: pullResult.recordCount,
      pushProcessed: pushResult.processed,
      pushFailed: pushResult.failed,
      conflicts: pushResult.conflicts,
    };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Sync failed unexpectedly';
    syncStore.setLastSyncError(message);
    throw error;
  } finally {
    syncStore.setSyncInProgress(false);
  }
}

// ============================================================================
// ID Mapping (client_id → server_id)
// ============================================================================

/**
 * Process id_mappings from push response.
 * Updates IndexedDB records to replace client-generated IDs with server IDs.
 *
 * Note: This is a best-effort operation. If individual updates fail,
 * the next pull will bring the correct data from server anyway.
 */
async function processIdMappings(
  idMappings: Record<string, string>
): Promise<void> {
  // ID mappings are returned as { client_id: server_id }
  // The server has created records with proper IDs — next pull will sync them
  // For now, we log the mappings for debugging. The pull cycle handles
  // replacing client-side records with authoritative server records.
  if (Object.keys(idMappings).length > 0) {
    console.info(
      `Sync: ${Object.keys(idMappings).length} ID mappings received. ` +
        'Records will be updated on next pull.'
    );
  }
}

// ============================================================================
// Entity Type Mapping
// ============================================================================

/**
 * Map frontend entity types to backend push event entity types.
 * Backend expects 'CORRECTIVE_ACTION' but frontend queue stores just the type.
 */
function mapEntityType(
  frontendType: string
): 'INSPECTION' | 'DEFICIENCY' | 'CAR' | 'CORRECTIVE_ACTION' | 'EVIDENCE' {
  const mapping: Record<string, SyncPushEvent['entity_type']> = {
    INSPECTION: 'INSPECTION',
    DEFICIENCY: 'DEFICIENCY',
    CAR: 'CAR',
    CORRECTIVE_ACTION: 'CORRECTIVE_ACTION',
    EVIDENCE: 'EVIDENCE',
  };
  return mapping[frontendType] ?? 'INSPECTION';
}
