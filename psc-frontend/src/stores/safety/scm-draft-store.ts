import { create } from "zustand";

type SafetyScmMeetingType = "AD_HOC" | "REGULAR" | null;

interface SafetyScmDraftStore {
  addAgendaItem: (item: string) => void;
  agendaItems: string[];
  meetingType: SafetyScmMeetingType;
  removeAgendaItem: (index: number) => void;
  reset: () => void;
  setMeetingType: (meetingType: SafetyScmMeetingType) => void;
  setTitle: (title: string) => void;
  title: string;
}

export const useSafetyScmDraftStore = create<SafetyScmDraftStore>((set) => ({
  addAgendaItem: (item) =>
    set((state) => ({
      agendaItems: [...state.agendaItems, item],
    })),
  agendaItems: [],
  meetingType: null,
  removeAgendaItem: (index) =>
    set((state) => ({
      agendaItems: state.agendaItems.filter((_, itemIndex) => itemIndex !== index),
    })),
  reset: () =>
    set({
      agendaItems: [],
      meetingType: null,
      title: "",
    }),
  setMeetingType: (meetingType) => set({ meetingType }),
  setTitle: (title) => set({ title }),
  title: "",
}));

