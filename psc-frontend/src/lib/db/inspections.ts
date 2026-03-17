/**
 * IndexedDB CRUD operations for inspections and deficiencies.
 *
 * Source: FRONTEND_GUIDELINES.md Section 7.1
 * Implements: PRD.md FEAT-SYNC-001
 */

import type { Inspection, Deficiency, InspectionStatus } from '@/types';
import { getDB } from './index';

// ============================================================================
// Inspections
// ============================================================================

/** Get all cached inspections, optionally filtered by vessel. */
export async function getAllInspections(
  vesselId?: number
): Promise<Inspection[]> {
  const db = await getDB();
  if (vesselId) {
    return db.getAllFromIndex('inspections', 'by-vessel', vesselId);
  }
  return db.getAll('inspections');
}

/** Get inspections filtered by status. */
export async function getInspectionsByStatus(
  status: InspectionStatus
): Promise<Inspection[]> {
  const db = await getDB();
  return db.getAllFromIndex('inspections', 'by-status', status);
}

/** Get a single inspection by ID. */
export async function getInspectionById(
  id: number
): Promise<Inspection | undefined> {
  const db = await getDB();
  return db.get('inspections', id);
}

/** Store or update a single inspection. */
export async function putInspection(
  inspection: Inspection
): Promise<void> {
  const db = await getDB();
  await db.put('inspections', {
    ...inspection,
    _synced_at: new Date().toISOString(),
  });
}

/** Bulk store/update inspections (used after sync pull). */
export async function bulkPutInspections(
  inspections: Inspection[]
): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('inspections', 'readwrite');
  const now = new Date().toISOString();
  await Promise.all([
    ...inspections.map((insp) =>
      tx.store.put({ ...insp, _synced_at: now })
    ),
    tx.done,
  ]);
}

/** Remove an inspection from the cache. */
export async function removeInspection(id: number): Promise<void> {
  const db = await getDB();
  await db.delete('inspections', id);
}

/** Count cached inspections. */
export async function countInspections(): Promise<number> {
  const db = await getDB();
  return db.count('inspections');
}

/** Clear all cached inspections. */
export async function clearInspections(): Promise<void> {
  const db = await getDB();
  await db.clear('inspections');
}

// ============================================================================
// Deficiencies
// ============================================================================

/** Get all cached deficiencies, optionally filtered by inspection. */
export async function getAllDeficiencies(
  inspectionId?: number
): Promise<Deficiency[]> {
  const db = await getDB();
  if (inspectionId) {
    return db.getAllFromIndex('deficiencies', 'by-inspection', inspectionId);
  }
  return db.getAll('deficiencies');
}

/** Get a single deficiency by ID. */
export async function getDeficiencyById(
  id: number
): Promise<Deficiency | undefined> {
  const db = await getDB();
  return db.get('deficiencies', id);
}

/** Store or update a single deficiency. */
export async function putDeficiency(deficiency: Deficiency): Promise<void> {
  const db = await getDB();
  await db.put('deficiencies', {
    ...deficiency,
    _synced_at: new Date().toISOString(),
  });
}

/** Bulk store/update deficiencies (used after sync pull). */
export async function bulkPutDeficiencies(
  deficiencies: Deficiency[]
): Promise<void> {
  const db = await getDB();
  const tx = db.transaction('deficiencies', 'readwrite');
  const now = new Date().toISOString();
  await Promise.all([
    ...deficiencies.map((def) =>
      tx.store.put({ ...def, _synced_at: now })
    ),
    tx.done,
  ]);
}

/** Remove a deficiency from the cache. */
export async function removeDeficiency(id: number): Promise<void> {
  const db = await getDB();
  await db.delete('deficiencies', id);
}

/** Count cached deficiencies. */
export async function countDeficiencies(): Promise<number> {
  const db = await getDB();
  return db.count('deficiencies');
}

/** Clear all cached deficiencies. */
export async function clearDeficiencies(): Promise<void> {
  const db = await getDB();
  await db.clear('deficiencies');
}
