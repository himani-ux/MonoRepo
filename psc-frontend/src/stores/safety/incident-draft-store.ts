import { create } from "zustand";

export interface SafetyIncidentDraft {
  draftReference?: string | null;
  incidentNumber?: string | null;
  phase: number | null;
  recordId: string;
  updatedAt: string;
  values: Record<string, unknown>;
}

interface SafetyIncidentDraftStore {
  clearDraft: (recordId: string) => void;
  drafts: Record<string, SafetyIncidentDraft>;
  reset: () => void;
  setDraft: (draft: SafetyIncidentDraft) => void;
}

export const useSafetyIncidentDraftStore = create<SafetyIncidentDraftStore>(
  (set) => ({
    clearDraft: (recordId) =>
      set((state) => {
        const nextDrafts = { ...state.drafts };
        delete nextDrafts[recordId];

        return { drafts: nextDrafts };
      }),
    drafts: {},
    reset: () => set({ drafts: {} }),
    setDraft: (draft) =>
      set((state) => ({
        drafts: {
          ...state.drafts,
          [draft.recordId]: draft,
        },
      })),
  }),
);
