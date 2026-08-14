import { create } from 'zustand';

interface NcWizardStore {
  findingId: string | null;
  stepIndex: number;
  resetForFinding: (findingId: string, suggestedStep: number) => void;
  setStepIndex: (stepIndex: number) => void;
}

export const useNcWizardStore = create<NcWizardStore>((set) => ({
  findingId: null,
  stepIndex: 0,
  resetForFinding: (findingId, suggestedStep) =>
    set((current) => ({
      findingId,
      stepIndex: current.findingId === findingId ? current.stepIndex : suggestedStep,
    })),
  setStepIndex: (stepIndex) => set({ stepIndex }),
}));
