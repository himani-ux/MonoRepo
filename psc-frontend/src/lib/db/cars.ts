/**
 * IndexedDB CRUD operations for CARs.
 *
 * Source: FRONTEND_GUIDELINES.md Section 7.1
 * Implements: PRD.md FEAT-SYNC-001
 */

import type { CARListItem, CARStatus } from '@/types';
import { getDB } from './index';

// ============================================================================
// CARs
// ============================================================================

/** Get all cached CARs, optionally filtered by vessel. */
export async function getAllCARs(vesselId?: number): Promise<CARListItem[]> {
  const db = await getDB();
  if (vesselId) {
    return db.getAllFromIndex('cars', 'by-vessel', vesselId);
  }
  return db.getAll('cars');
}

/** Get CARs filtered by status. */
export async function getCARsByStatus(
  status: CARStatus
): Promise<CARListItem[]> {
  const db = await getDB();
  return db.getAllFromIndex('cars', 'by-status', status);
}

/** Get a single CAR by ID. */
export async function getCARById(
  id: number
): Promise<CARListItem | undefined> {
  const db = await getDB();
  return db.get('cars', id);
}

/** Store or update a single CAR. */
export async function putCAR(car: CARListItem): Promise<void> {
  const db = await getDB();
  await db.put('cars', {
    ...car,
    _synced_at: new Date().toISOString(),
  });
}

/** Bulk store/update CARs (used after sync pull). */
export async function bulkPutCARs(cars: CARListItem[]): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('cars', 'readwrite');
  const now = new Date().toISOString();
  await Promise.all([
    ...cars.map((car) => tx.store.put({ ...car, _synced_at: now })),
    tx.done,
  ]);
}

/** Remove a CAR from the cache. */
export async function removeCAR(id: number): Promise<void> {
  const db = await getDB();
  await db.delete('cars', id);
}

/** Count cached CARs. */
export async function countCARs(): Promise<number> {
  const db = await getDB();
  return db.count('cars');
}

/** Clear all cached CARs. */
export async function clearCARs(): Promise<void> {
  const db = await getDB();
  await db.clear('cars');
}
