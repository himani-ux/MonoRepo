import { useEffect, useRef, useState } from "react";

import {
  useSafetyIncidentDraftStore,
  type SafetyIncidentDraft,
} from "../../stores/safety/incident-draft-store";

export interface SafetyDraftStorageAdapter<TValues extends Record<string, unknown>> {
  clear: (key: string) => Promise<void>;
  load: (key: string) => Promise<SafetyIncidentDraft | null>;
  save: (draft: SafetyIncidentDraft & { values: TValues }) => Promise<void>;
}

interface SafetyDraftAutosaveOptions<TValues extends Record<string, unknown>> {
  enabled?: boolean;
  intervalMs?: number;
  onRestore?: (values: Partial<TValues>) => void;
  phase: number;
  recordId: string;
  storage?: SafetyDraftStorageAdapter<TValues>;
  values: TValues;
}

type SafetyDraftAutosaveStatus = "idle" | "restored" | "saved";

const DEFAULT_INTERVAL_MS = 30_000;
const DB_NAME = "vims-safety-handover";
const STORE_NAME = "incident-drafts";
const memoryDrafts = new Map<string, SafetyIncidentDraft>();

function buildDraftKey(recordId: string, phase: number) {
  return `${recordId}:phase:${phase}`;
}

function getIndexedDb(): IDBFactory | null {
  if (typeof globalThis === "undefined" || !("indexedDB" in globalThis)) {
    return null;
  }

  return globalThis.indexedDB ?? null;
}

function openDraftDatabase(): Promise<IDBDatabase | null> {
  const indexedDb = getIndexedDb();
  if (!indexedDb) {
    return Promise.resolve(null);
  }

  return new Promise((resolve, reject) => {
    const request = indexedDb.open(DB_NAME, 1);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: "recordId" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function defaultStorageAdapter<TValues extends Record<string, unknown>>(): SafetyDraftStorageAdapter<TValues> {
  return {
    async clear(key) {
      memoryDrafts.delete(key);
      const database = await openDraftDatabase();
      if (!database) {
        return;
      }

      await new Promise<void>((resolve, reject) => {
        const transaction = database.transaction(STORE_NAME, "readwrite");
        transaction.objectStore(STORE_NAME).delete(key);
        transaction.oncomplete = () => {
          database.close();
          resolve();
        };
        transaction.onerror = () => reject(transaction.error);
      });
    },
    async load(key) {
      const memoryDraft = memoryDrafts.get(key);
      if (memoryDraft) {
        return memoryDraft;
      }

      const database = await openDraftDatabase();
      if (!database) {
        return null;
      }

      return new Promise<SafetyIncidentDraft | null>((resolve, reject) => {
        const transaction = database.transaction(STORE_NAME, "readonly");
        const request = transaction.objectStore(STORE_NAME).get(key);
        request.onsuccess = () => {
          database.close();
          resolve((request.result as SafetyIncidentDraft | undefined) ?? null);
        };
        request.onerror = () => reject(request.error);
      });
    },
    async save(draft) {
      memoryDrafts.set(draft.recordId, draft);
      const database = await openDraftDatabase();
      if (!database) {
        return;
      }

      await new Promise<void>((resolve, reject) => {
        const transaction = database.transaction(STORE_NAME, "readwrite");
        transaction.objectStore(STORE_NAME).put(draft);
        transaction.oncomplete = () => {
          database.close();
          resolve();
        };
        transaction.onerror = () => reject(transaction.error);
      });
    },
  };
}

export function useDraftAutosave<TValues extends Record<string, unknown>>({
  enabled = true,
  intervalMs = DEFAULT_INTERVAL_MS,
  onRestore,
  phase,
  recordId,
  storage,
  values,
}: SafetyDraftAutosaveOptions<TValues>) {
  const adapterRef = useRef(storage ?? defaultStorageAdapter<TValues>());
  const onRestoreRef = useRef(onRestore);
  const valuesRef = useRef(values);
  const setDraft = useSafetyIncidentDraftStore((state) => state.setDraft);
  const clearDraft = useSafetyIncidentDraftStore((state) => state.clearDraft);
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
  const [status, setStatus] = useState<SafetyDraftAutosaveStatus>("idle");

  onRestoreRef.current = onRestore;
  valuesRef.current = values;
  const draftKey = buildDraftKey(recordId, phase);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;
    void adapterRef.current.load(draftKey).then((draft) => {
      if (!draft || cancelled) {
        return;
      }

      setDraft(draft);
      setLastSavedAt(draft.updatedAt);
      setStatus("restored");
      onRestoreRef.current?.(draft.values as Partial<TValues>);
    });

    return () => {
      cancelled = true;
    };
  }, [draftKey, enabled, setDraft]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    const timer = window.setInterval(() => {
      const draft: SafetyIncidentDraft & { values: TValues } = {
        phase,
        recordId: draftKey,
        updatedAt: new Date().toISOString(),
        values: valuesRef.current,
      };

      void adapterRef.current.save(draft).then(() => {
        setDraft(draft);
        setLastSavedAt(draft.updatedAt);
        setStatus("saved");
      });
    }, intervalMs);

    return () => {
      window.clearInterval(timer);
    };
  }, [draftKey, enabled, intervalMs, phase, setDraft]);

  async function saveDraftNow() {
    const draft: SafetyIncidentDraft & { values: TValues } = {
      phase,
      recordId: draftKey,
      updatedAt: new Date().toISOString(),
      values: valuesRef.current,
    };

    await adapterRef.current.save(draft);
    setDraft(draft);
    setLastSavedAt(draft.updatedAt);
    setStatus("saved");
    return draft;
  }

  async function restoreDraft() {
    const draft = await adapterRef.current.load(draftKey);
    if (!draft) {
      return null;
    }

    setDraft(draft);
    setLastSavedAt(draft.updatedAt);
    setStatus("restored");
    onRestoreRef.current?.(draft.values as Partial<TValues>);
    return draft;
  }

  async function clearStoredDraft() {
    await adapterRef.current.clear(draftKey);
    clearDraft(draftKey);
    setLastSavedAt(null);
    setStatus("idle");
  }

  return {
    clearStoredDraft,
    draftKey,
    lastSavedAt,
    restoreDraft,
    saveDraftNow,
    status,
  };
}
