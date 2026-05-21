import { create } from "zustand";

interface SafetySoiPickerStore {
  removeArea: (areaId: string) => void;
  reset: () => void;
  selectedAreaIds: string[];
  setSelectedAreaIds: (areaIds: string[]) => void;
  toggleArea: (areaId: string) => void;
}

export const useSafetySoiPickerStore = create<SafetySoiPickerStore>((set) => ({
  removeArea: (areaId) =>
    set((state) => ({
      selectedAreaIds: state.selectedAreaIds.filter((id) => id !== areaId),
    })),
  reset: () => set({ selectedAreaIds: [] }),
  selectedAreaIds: [],
  setSelectedAreaIds: (areaIds) =>
    set({
      selectedAreaIds: [...new Set(areaIds)],
    }),
  toggleArea: (areaId) =>
    set((state) => ({
      selectedAreaIds: state.selectedAreaIds.includes(areaId)
        ? state.selectedAreaIds.filter((id) => id !== areaId)
        : [...state.selectedAreaIds, areaId],
    })),
}));

