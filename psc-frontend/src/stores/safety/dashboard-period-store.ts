import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export type SafetyDashboardPeriod = "90D" | "12M" | "3Y";
export const DEFAULT_SAFETY_DASHBOARD_PERIOD: SafetyDashboardPeriod = "3Y";
export const SAFETY_DASHBOARD_PERIOD_STORAGE_KEY = "vims-safety-dashboard-period";

const DEFAULT_SCOPE_KEY = "anonymous";
const VALID_PERIODS = new Set<SafetyDashboardPeriod>(["90D", "12M", "3Y"]);

interface SafetyDashboardPeriodPersistedState {
  periodByScope: Record<string, SafetyDashboardPeriod>;
}

interface SafetyDashboardPeriodStore {
  bindScope: (scopeKey?: string | null) => void;
  period: SafetyDashboardPeriod;
  periodByScope: Record<string, SafetyDashboardPeriod>;
  reset: () => void;
  setPeriod: (period: SafetyDashboardPeriod) => void;
  scopeKey: string;
}

function isSafetyDashboardPeriod(value: unknown): value is SafetyDashboardPeriod {
  return VALID_PERIODS.has(value as SafetyDashboardPeriod);
}

function normalizeScopeKey(scopeKey?: string | null): string {
  const trimmed = scopeKey?.trim();
  return trimmed ? trimmed : DEFAULT_SCOPE_KEY;
}

function resolveScopedPeriod(
  periodByScope: Record<string, SafetyDashboardPeriod>,
  scopeKey: string,
): SafetyDashboardPeriod {
  const persistedPeriod = periodByScope[scopeKey];
  return isSafetyDashboardPeriod(persistedPeriod)
    ? persistedPeriod
    : DEFAULT_SAFETY_DASHBOARD_PERIOD;
}

function sanitizePeriodByScope(
  persisted: unknown,
): Record<string, SafetyDashboardPeriod> {
  if (!persisted || typeof persisted !== "object") {
    return {};
  }

  return Object.fromEntries(
    Object.entries(persisted).filter(([, period]) => isSafetyDashboardPeriod(period)),
  );
}

export function buildSafetyDashboardPeriodScopeKey(user?: {
  id?: number | string | null;
  role?: string | null;
  vesselIds?: Array<number | string> | null;
}): string {
  const userId = user?.id;
  if (userId !== undefined && userId !== null && `${userId}`.trim() !== "") {
    return `user:${userId}`;
  }

  const role = user?.role?.trim().toUpperCase();
  const vesselIds = (user?.vesselIds ?? [])
    .map((value) => `${value}`.trim())
    .filter(Boolean)
    .sort();

  if (role && vesselIds.length > 0) {
    return `role:${role}|vessels:${vesselIds.join(",")}`;
  }

  if (role) {
    return `role:${role}`;
  }

  return DEFAULT_SCOPE_KEY;
}

export const useSafetyDashboardPeriodStore = create<SafetyDashboardPeriodStore>()(
  persist(
    (set) => ({
      bindScope: (scopeKey) => {
        const normalizedScopeKey = normalizeScopeKey(scopeKey);
        set((state) => ({
          period: resolveScopedPeriod(state.periodByScope, normalizedScopeKey),
          scopeKey: normalizedScopeKey,
        }));
      },
      period: DEFAULT_SAFETY_DASHBOARD_PERIOD,
      periodByScope: {},
      reset: () =>
        set({
          period: DEFAULT_SAFETY_DASHBOARD_PERIOD,
          periodByScope: {},
          scopeKey: DEFAULT_SCOPE_KEY,
        }),
      scopeKey: DEFAULT_SCOPE_KEY,
      setPeriod: (period) =>
        set((state) => {
          const scopeKey = normalizeScopeKey(state.scopeKey);
          return {
            period,
            periodByScope: {
              ...state.periodByScope,
              [scopeKey]: period,
            },
            scopeKey,
          };
        }),
    }),
    {
      merge: (persistedState, currentState) => {
        const periodByScope = sanitizePeriodByScope(
          (persistedState as Partial<SafetyDashboardPeriodPersistedState> | undefined)?.periodByScope,
        );

        return {
          ...currentState,
          period: resolveScopedPeriod(periodByScope, currentState.scopeKey),
          periodByScope,
        };
      },
      name: SAFETY_DASHBOARD_PERIOD_STORAGE_KEY,
      partialize: (state) => ({
        periodByScope: state.periodByScope,
      }),
      storage: createJSONStorage(() => localStorage),
      version: 1,
    },
  ),
);
