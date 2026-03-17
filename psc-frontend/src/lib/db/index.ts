/**
 * IndexedDB setup using idb library.
 *
 * Database: 'inspection-module' (version 1)
 * Stores:
 *   - inspections: Cached inspection records
 *   - deficiencies: Cached deficiency records
 *   - cars: Cached CAR records
 *   - syncQueue: Offline mutation queue
 *   - masters: Cached master data (codes, CLC items, etc.)
 *
 * Source: FRONTEND_GUIDELINES.md Section 7.1
 * Implements: PRD.md FEAT-SYNC-001
 */

import { openDB, type DBSchema, type IDBPDatabase } from 'idb';
import type {
  Inspection,
  Deficiency,
  CARListItem,
  SyncQueueItem,
} from '@/types';

// ============================================================================
// Database Schema
// ============================================================================

export interface InspectionDBSchema extends DBSchema {
  inspections: {
    key: number;
    value: Inspection & { _synced_at?: string };
    indexes: {
      'by-vessel': number;
      'by-status': string;
    };
  };
  deficiencies: {
    key: number;
    value: Deficiency & { _synced_at?: string };
    indexes: {
      'by-inspection': number;
    };
  };
  cars: {
    key: number;
    value: CARListItem & { _synced_at?: string };
    indexes: {
      'by-status': string;
      'by-vessel': number;
    };
  };
  syncQueue: {
    key: number;
    value: SyncQueueItem;
    indexes: {
      'by-status': string;
      'by-created': string;
    };
  };
  masters: {
    key: string;
    value: { key: string; data: unknown; updated_at: string };
  };
}

// ============================================================================
// Database Instance
// ============================================================================

const DB_NAME = 'inspection-module';
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase<InspectionDBSchema>> | null = null;

/**
 * Get or create the IndexedDB database instance.
 * Singleton pattern — only one connection per app lifetime.
 */
export async function getDB(): Promise<IDBPDatabase<InspectionDBSchema>> {
  if (!dbPromise) {
    dbPromise = openDB<InspectionDBSchema>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        // Inspections store
        if (!db.objectStoreNames.contains('inspections')) {
          const inspectionStore = db.createObjectStore('inspections', {
            keyPath: 'id',
          });
          inspectionStore.createIndex('by-vessel', 'vessel_id');
          inspectionStore.createIndex('by-status', 'status');
        }

        // Deficiencies store
        if (!db.objectStoreNames.contains('deficiencies')) {
          const deficiencyStore = db.createObjectStore('deficiencies', {
            keyPath: 'id',
          });
          deficiencyStore.createIndex('by-inspection', 'inspection_id');
        }

        // CARs store
        if (!db.objectStoreNames.contains('cars')) {
          const carStore = db.createObjectStore('cars', {
            keyPath: 'id',
          });
          carStore.createIndex('by-status', 'status');
          carStore.createIndex('by-vessel', 'vessel_id');
        }

        // Sync queue (autoIncrement for ordered processing)
        if (!db.objectStoreNames.contains('syncQueue')) {
          const syncStore = db.createObjectStore('syncQueue', {
            keyPath: 'id',
            autoIncrement: true,
          });
          syncStore.createIndex('by-status', 'status');
          syncStore.createIndex('by-created', 'created_at');
        }

        // Masters (key-value store for code tables)
        if (!db.objectStoreNames.contains('masters')) {
          db.createObjectStore('masters', { keyPath: 'key' });
        }
      },
    });
  }
  return dbPromise;
}

// ============================================================================
// Storage Utilities
// ============================================================================

/** Storage limit in bytes (150MB per PRD.md FEAT-SYNC-001). */
export const STORAGE_LIMIT_BYTES = 150 * 1024 * 1024;

/** Warning threshold in bytes (10MB remaining). */
export const STORAGE_WARNING_BYTES = 10 * 1024 * 1024;

/**
 * Estimate current IndexedDB storage usage.
 * Returns { usage, quota } in bytes, or null if StorageManager unavailable.
 */
export async function getStorageEstimate(): Promise<{
  usage: number;
  quota: number;
} | null> {
  if (navigator.storage && navigator.storage.estimate) {
    const estimate = await navigator.storage.estimate();
    return {
      usage: estimate.usage ?? 0,
      quota: estimate.quota ?? STORAGE_LIMIT_BYTES,
    };
  }
  return null;
}

/**
 * Check if storage is nearly full (< 10MB remaining of our 150MB limit).
 */
export async function isStorageNearlyFull(): Promise<boolean> {
  const estimate = await getStorageEstimate();
  if (!estimate) return false;
  const remaining = STORAGE_LIMIT_BYTES - estimate.usage;
  return remaining < STORAGE_WARNING_BYTES;
}

/**
 * Clear all data from all stores. Used for logout or storage cleanup.
 */
export async function clearAllStores(): Promise<void> {
  const db = await getDB();
  const tx = db.transaction(
    ['inspections', 'deficiencies', 'cars', 'syncQueue', 'masters'],
    'readwrite'
  );
  await Promise.all([
    tx.objectStore('inspections').clear(),
    tx.objectStore('deficiencies').clear(),
    tx.objectStore('cars').clear(),
    tx.objectStore('syncQueue').clear(),
    tx.objectStore('masters').clear(),
    tx.done,
  ]);
}

/**
 * Delete the entire database. Nuclear option for hard reset.
 */
export async function deleteDatabase(): Promise<void> {
  dbPromise = null;
  const { deleteDB } = await import('idb');
  await deleteDB(DB_NAME);
}
