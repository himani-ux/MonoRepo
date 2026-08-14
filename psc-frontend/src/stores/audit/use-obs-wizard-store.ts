import { create } from 'zustand';

interface ObsWizardStore {
  findingId: string | null;
  stepIndex: number;
  resetForFinding: (findingId: string, suggestedStep: number) => void;
  setStepIndex: (stepIndex: number) => void;
}

export const useObsWizardStore = create<ObsWizardStore>((set) => ({
  findingId: null,
  stepIndex: 0,
  resetForFinding: (findingId, suggestedStep) =>
    set((current) => ({
      findingId,
      stepIndex: current.findingId === findingId ? current.stepIndex : suggestedStep,
    })),
  setStepIndex: (stepIndex) => set({ stepIndex }),
}));
