import { createContext, useContext, type PropsWithChildren } from "react";

export interface SafetyAuthUser {
  crewId?: number | string | null;
  displayName?: string | null;
  employeeId?: number | string | null;
  firstName?: string | null;
  fullName?: string | null;
  id?: number | string;
  login_id?: string | null;
  role?: string | null;
  formIds?: string[];
  processIds?: string[];
  surname?: string | null;
  userName?: string | null;
  vesselIds?: Array<number | string>;
  vesselNames?: string[];
  isGlobal?: boolean;
}

export interface SafetyAuthSnapshot {
  formIds: string[];
  hasAnySafetyAccess: () => boolean;
  hasForm: (formId: string) => boolean;
  hasProcess: (processId: string) => boolean;
  isGlobal: boolean;
  processIds: string[];
  role: string | null;
  scopedVesselLabel: string;
  user: SafetyAuthUser | null;
  vesselIds: Array<number | string>;
  vesselNames: string[];
}

const DEFAULT_AUTH_USER: SafetyAuthUser = {
  formIds: [],
  isGlobal: false,
  processIds: [],
  role: null,
  vesselIds: [],
  vesselNames: [],
};

const SafetyAuthContext = createContext<SafetyAuthUser>(DEFAULT_AUTH_USER);

export function buildSafetyAuthSnapshot(
  user: SafetyAuthUser | null | undefined,
): SafetyAuthSnapshot {
  const safeUser = user ?? DEFAULT_AUTH_USER;
  const formIds = [...new Set(safeUser.formIds ?? [])];
  const processIds = [...new Set(safeUser.processIds ?? [])];
  const vesselIds = [...new Set(safeUser.vesselIds ?? [])];
  const vesselNames = [...new Set((safeUser.vesselNames ?? []).map((name) => name.trim()).filter(Boolean))];
  const role = safeUser.role ?? null;
  const isGlobal = Boolean(safeUser.isGlobal);
  const scopedVesselLabel = isGlobal ? "Global" : vesselNames.join(", ") || vesselIds.join(", ") || "None";

  return {
    formIds,
    hasAnySafetyAccess: () => formIds.some((formId) => formId.startsWith("SAF_F_")),
    hasForm: (formId: string) => formIds.includes(formId),
    hasProcess: (processId: string) => processIds.includes(processId),
    isGlobal,
    processIds,
    role,
    scopedVesselLabel,
    user: user ?? null,
    vesselIds,
    vesselNames,
  };
}

export function SafetyAuthProvider({
  children,
  value,
}: PropsWithChildren<{ value: SafetyAuthUser }>) {
  return (
    <SafetyAuthContext.Provider value={value ?? DEFAULT_AUTH_USER}>
      {children}
    </SafetyAuthContext.Provider>
  );
}

export function useSafetyAuth(): SafetyAuthSnapshot {
  return buildSafetyAuthSnapshot(useContext(SafetyAuthContext));
}
