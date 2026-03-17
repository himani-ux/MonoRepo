/**
 * IndexedDB CRUD for cached master data (codes, CLC items, etc.).
 *
 * Master data is stored as key-value pairs:
 *   - 'mou_codes' → MOUCode[]
 *   - 'psc_action_codes' → PSCActionCode[]
 *   - 'psc_def_codes' → PSCDefCode[]
 *   - 'clc_items' → CLCItem[]
 *   - 'pic_codes' → PICCode[]
 *
 * Source: FRONTEND_GUIDELINES.md Section 7.1
 * Implements: PRD.md FEAT-SYNC-001
 */

import { getDB } from './index';

// ============================================================================
// Master Data Keys
// ============================================================================

export const MASTER_KEYS = {
  MOU_CODES: 'mou_codes',
  PSC_ACTION_CODES: 'psc_action_codes',
  PSC_DEF_CODES: 'psc_def_codes',
  CLC_ITEMS: 'clc_items',
  PIC_CODES: 'pic_codes',
} as const;

export type MasterKey = (typeof MASTER_KEYS)[keyof typeof MASTER_KEYS];

// ============================================================================
// Master Data Operations
// ============================================================================

/** Get master data by key. Returns the data array or null if not cached. */
export async function getMasterData<T = unknown>(
  key: MasterKey
): Promise<T | null> {
  const db = await getDB();
  const record = await db.get('masters', key);
  return record ? (record.data as T) : null;
}

/** Store master data by key. */
export async function putMasterData(
  key: MasterKey,
  data: unknown
): Promise<void> {
  const db = await getDB();
  await db.put('masters', {
    key,
    data,
    updated_at: new Date().toISOString(),
  });
}

/** Get all cached master data entries. */
export async function getAllMasterData(): Promise<
  Array<{ key: string; data: unknown; updated_at: string }>
> {
  const db = await getDB();
  return db.getAll('masters');
}

/** Check when master data was last updated. Returns ISO string or null. */
export async function getMasterDataTimestamp(
  key: MasterKey
): Promise<string | null> {
  const db = await getDB();
  const record = await db.get('masters', key);
  return record ? record.updated_at : null;
}

/** Clear all cached master data. */
export async function clearMasterData(): Promise<void> {
  const db = await getDB();
  await db.clear('masters');
}

/**
 * Bulk update master data from sync pull response.
 * Accepts a map of { key: data } pairs.
 */
export async function bulkPutMasterData(
  entries: Record<string, unknown>
): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('masters', 'readwrite');
  const now = new Date().toISOString();
  await Promise.all([
    ...Object.entries(entries).map(([key, data]) =>
      tx.store.put({ key, data, updated_at: now })
    ),
    tx.done,
  ]);
}
