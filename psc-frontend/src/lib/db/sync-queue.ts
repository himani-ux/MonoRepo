/**
 * IndexedDB sync queue management.
 *
 * Queues offline mutations for later push to server.
 * Events are processed FIFO (by autoIncrement key).
 *
 * Source: FRONTEND_GUIDELINES.md Section 7.1
 * Implements: PRD.md FEAT-SYNC-001, FEAT-SYNC-003
 */

import { SYNC_STATUS } from '@/lib/utils/constants';
import type { SyncQueueItem, SyncStatus } from '@/types';
import { getDB } from './index';

// ============================================================================
// Sync Queue Types
// ============================================================================

export type SyncEntityType = SyncQueueItem['entity_type'];
export type SyncOperation = SyncQueueItem['operation'];

export interface AddToQueueParams {
  entity_type: SyncEntityType;
  entity_id: number | string;
  operation: SyncOperation;
  data: Record<string, unknown>;
}

// ============================================================================
// Sync Queue Operations
// ============================================================================

/**
 * Add a mutation event to the sync queue.
 * Called when the user performs a write operation while offline.
 */
export async function addToSyncQueue(
  params: AddToQueueParams
): Promise<number> {
  const db = await getDB();
  const item: Omit<SyncQueueItem, 'id'> = {
    entity_type: params.entity_type,
    entity_id: params.entity_id,
    operation: params.operation,
    data: params.data,
    status: SYNC_STATUS.PENDING as SyncStatus,
    attempts: 0,
    last_attempt_at: null,
    error_message: null,
    created_at: new Date().toISOString(),
  };
  // autoIncrement returns the generated key
  return db.add('syncQueue', item as SyncQueueItem);
}

/** Get all queued sync events, ordered by creation time. */
export async function getAllSyncQueue(): Promise<SyncQueueItem[]> {
  const db = await getDB();
  return db.getAllFromIndex('syncQueue', 'by-created');
}

/** Get only pending sync events (not yet synced or failed). */
export async function getPendingSyncQueue(): Promise<SyncQueueItem[]> {
  const db = await getDB();
  return db.getAllFromIndex(
    'syncQueue',
    'by-status',
    SYNC_STATUS.PENDING
  );
}

/**
 * Get retryable sync events (PENDING + FAILED), ordered by creation time.
 * Used by push sync so failed uploads/events can be retried on next sync.
 */
export async function getRetryableSyncQueue(): Promise<SyncQueueItem[]> {
  const db = await getDB();
  const [pending, failed] = await Promise.all([
    db.getAllFromIndex('syncQueue', 'by-status', SYNC_STATUS.PENDING),
    db.getAllFromIndex('syncQueue', 'by-status', SYNC_STATUS.FAILED),
  ]);

  return [...pending, ...failed].sort((a, b) =>
    a.created_at.localeCompare(b.created_at)
  );
}

/** Get failed sync events (for retry UI). */
export async function getFailedSyncQueue(): Promise<SyncQueueItem[]> {
  const db = await getDB();
  return db.getAllFromIndex(
    'syncQueue',
    'by-status',
    SYNC_STATUS.FAILED
  );
}

/** Get a single sync queue item by ID. */
export async function getSyncQueueItem(
  id: number
): Promise<SyncQueueItem | undefined> {
  const db = await getDB();
  return db.get('syncQueue', id);
}

/**
 * Update sync queue item status (e.g., mark as IN_PROGRESS, FAILED).
 * Increments attempt count and records error if provided.
 */
export async function updateSyncQueueItem(
  id: number,
  updates: {
    status: SyncStatus;
    error_message?: string | null;
  }
): Promise<void> {
  const db = await getDB();
  const item = await db.get('syncQueue', id);
  if (!item) return;

  const updated: SyncQueueItem = {
    ...item,
    status: updates.status,
    attempts: item.attempts + 1,
    last_attempt_at: new Date().toISOString(),
    error_message: updates.error_message ?? item.error_message,
  };
  await db.put('syncQueue', updated);
}

/** Remove a sync queue item after successful sync. */
export async function removeSyncQueueItem(id: number): Promise<void> {
  const db = await getDB();
  await db.delete('syncQueue', id);
}

/** Remove all completed/synced items from the queue. */
export async function clearCompletedFromQueue(): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('syncQueue', 'readwrite');
  const index = tx.store.index('by-status');
  let cursor = await index.openCursor(SYNC_STATUS.COMPLETED);
  while (cursor) {
    await cursor.delete();
    cursor = await cursor.continue();
  }
  await tx.done;
}

/** Clear the entire sync queue. */
export async function clearSyncQueue(): Promise<void> {
  const db = await getDB();
  await db.clear('syncQueue');
}

/** Count total items in the sync queue. */
export async function countSyncQueue(): Promise<number> {
  const db = await getDB();
  return db.count('syncQueue');
}

/** Count only pending items (for badge display). */
export async function countPendingSyncQueue(): Promise<number> {
  const db = await getDB();
  const index = db
    .transaction('syncQueue', 'readonly')
    .store.index('by-status');
  return index.count(SYNC_STATUS.PENDING);
}
