import { create } from 'zustand';
import type { AuditChecklistWalkStatus } from '@/schemas/audit/checklist';

interface ChecklistWalkItemState {
  status: AuditChecklistWalkStatus;
  remarks: string;
}

interface ChecklistWalkStore {
  auditId: string | null;
  items: Record<string, ChecklistWalkItemState>;
  resetForItems: (auditId: string, itemIds: string[]) => void;
  setItemStatus: (itemId: string, status: AuditChecklistWalkStatus) => void;
  setItemRemarks: (itemId: string, remarks: string) => void;
}

const defaultItemState: ChecklistWalkItemState = {
  status: 'NOT_REVIEWED',
  remarks: '',
};

export const useChecklistWalkStore = create<ChecklistWalkStore>((set) => ({
  auditId: null,
  items: {},
  resetForItems: (auditId, itemIds) =>
    set((current) => {
      const shouldReset = current.auditId !== auditId;
      const nextItems: Record<string, ChecklistWalkItemState> = {};
      for (const itemId of itemIds) {
        nextItems[itemId] = shouldReset
          ? { ...defaultItemState }
          : current.items[itemId] ?? { ...defaultItemState };
      }
      return { auditId, items: nextItems };
    }),
  setItemStatus: (itemId, status) =>
    set((current) => ({
      items: {
        ...current.items,
        [itemId]: {
          ...defaultItemState,
          ...current.items[itemId],
          status,
        },
      },
    })),
  setItemRemarks: (itemId, remarks) =>
    set((current) => ({
      items: {
        ...current.items,
        [itemId]: {
          ...defaultItemState,
          ...current.items[itemId],
          remarks,
        },
      },
    })),
}));
