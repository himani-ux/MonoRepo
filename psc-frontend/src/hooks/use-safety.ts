import { useQuery } from '@tanstack/react-query';

import {
  safetyApi,
  type SafetyDashboardPeriodCode,
  type SafetyIncidentFilters,
  type SafetyNearMissFilters,
  type SafetyScmFilters,
  type SafetySoiFilters,
} from '@/lib/api/safety';
import { STALE_TIME } from '@/lib/utils/constants';

export const safetyKeys = {
  all: ['safety'] as const,
  dashboard: () => [...safetyKeys.all, 'dashboard'] as const,
  dashboardComposite: (period: SafetyDashboardPeriodCode, vesselId?: string | null) =>
    [...safetyKeys.dashboard(), 'composite', { period, vesselId }] as const,
  dashboardHeinrich: (vesselId?: string | null) =>
    [...safetyKeys.dashboard(), 'heinrich', { vesselId }] as const,
  dashboardRepeatRoot: (vesselId?: string | null) =>
    [...safetyKeys.dashboard(), 'repeat-root', { vesselId }] as const,
  dashboardPareto: (vesselId?: string | null) =>
    [...safetyKeys.dashboard(), 'pareto', { vesselId }] as const,
  dashboardSoiCompliance: (vesselId?: string | null) =>
    [...safetyKeys.dashboard(), 'soi-compliance', { vesselId }] as const,
  dashboardCaAging: (vesselId?: string | null) =>
    [...safetyKeys.dashboard(), 'ca-aging', { vesselId }] as const,
  incidents: (filters: SafetyIncidentFilters) =>
    [...safetyKeys.all, 'incidents', filters] as const,
  incidentPhase3Evidence: (id: number | string) =>
    [...safetyKeys.all, 'incidents', id, 'phase-3-evidence'] as const,
  incidentPhase4Facts: (id: number | string) =>
    [...safetyKeys.all, 'incidents', id, 'phase-4-facts'] as const,
  incidentPhase5Workspace: (id: number | string) =>
    [...safetyKeys.all, 'incidents', id, 'phase-5-workspace'] as const,
  incidentPhase6Workspace: (id: number | string) =>
    [...safetyKeys.all, 'incidents', id, 'phase-6-workspace'] as const,
  incidentPhase7Preflight: (id: number | string) =>
    [...safetyKeys.all, 'incidents', id, 'phase-7-preflight'] as const,
  incidentPhase8Workspace: (id: number | string) =>
    [...safetyKeys.all, 'incidents', id, 'phase-8-workspace'] as const,
  incidentClosureSummary: (id: number | string) =>
    [...safetyKeys.all, 'incidents', id, 'closure-summary'] as const,
  incidentAudit: (id: number | string) =>
    [...safetyKeys.all, 'incidents', id, 'audit'] as const,
  correctiveActions: (filters: Record<string, string | number | boolean | null | undefined>) =>
    [...safetyKeys.all, 'corrective-actions', filters] as const,
  nearMisses: (filters: SafetyNearMissFilters) =>
    [...safetyKeys.all, 'near-miss', filters] as const,
  nearMissDetail: (id: number | string) =>
    [...safetyKeys.all, 'near-miss', id, 'detail'] as const,
  nearMissAnalysis: (id: number | string) =>
    [...safetyKeys.all, 'near-miss', id, 'analysis'] as const,
  nearMissFleetAlert: (id: number | string) =>
    [...safetyKeys.all, 'near-miss', id, 'fleet-alert'] as const,
  nearMissClosureSummary: (id: number | string) =>
    [...safetyKeys.all, 'near-miss', id, 'closure-summary'] as const,
  nearMissAudit: (id: number | string) =>
    [...safetyKeys.all, 'near-miss', id, 'audit'] as const,
  scmMeetings: (filters: SafetyScmFilters) =>
    [...safetyKeys.all, 'scm', filters] as const,
  scmMeeting: (id: number | string) => [...safetyKeys.all, 'scm', 'detail', id] as const,
  scmCreateRegular: (vesselId?: string | null) =>
    [...safetyKeys.all, 'scm', 'create-regular', { vesselId }] as const,
  scmCreateAdhoc: (vesselId?: string | null) =>
    [...safetyKeys.all, 'scm', 'create-adhoc', { vesselId }] as const,
  scmAgenda: (id: number | string, includeCarriedForward = false) =>
    [...safetyKeys.all, 'scm', 'agenda', id, { includeCarriedForward }] as const,
  scmClosedSinceLast: (id: number | string) =>
    [...safetyKeys.all, 'scm', 'closed-since-last', id] as const,
  scmAutoFeed: (id: number | string) => [...safetyKeys.all, 'scm', 'auto-feed', id] as const,
  scmOpenFindings: (vesselId?: string | null) =>
    [...safetyKeys.all, 'scm', 'open-findings', { vesselId }] as const,
  scmAttendance: (id: number | string) => [...safetyKeys.all, 'scm', 'attendance', id] as const,
  soiCompliance: (vesselId?: string | null) =>
    [...safetyKeys.all, 'soi-compliance', { vesselId }] as const,
  soiInspections: (filters: SafetySoiFilters) =>
    [...safetyKeys.all, 'soi', filters] as const,
  soiCreateConfig: (plannedDate?: string, safetyOfficerCrewId?: string, vesselId?: string) =>
    [...safetyKeys.all, 'soi', 'create-config', { plannedDate, safetyOfficerCrewId, vesselId }] as const,
  soiInspection: (id: number | string) => [...safetyKeys.all, 'soi', 'detail', id] as const,
  soiPickAreas: (id: number | string) => [...safetyKeys.all, 'soi', 'pick-areas', id] as const,
  soiCloseSnapshot: (id: number | string) => [...safetyKeys.all, 'soi', 'close', id] as const,
  soiFindings: (id: number | string) => [...safetyKeys.all, 'soi', 'findings', id] as const,
  soiFinding: (id: number | string) => [...safetyKeys.all, 'soi', 'finding', id] as const,
  soiApplicabilityRequest: (id: number | string) =>
    [...safetyKeys.all, 'soi', 'applicability-request', id] as const,
  soiApplicabilityApproval: (id: number | string) =>
    [...safetyKeys.all, 'soi', 'applicability-approval', id] as const,
  search: (query: string, recordType: string, includeArchived: boolean) =>
    [...safetyKeys.all, 'search', { query, recordType, includeArchived }] as const,
};

export function useSafetyDashboardComposite(period: SafetyDashboardPeriodCode, vesselId?: string | null) {
  return useQuery({
    queryKey: safetyKeys.dashboardComposite(period, vesselId),
    queryFn: () => safetyApi.getDashboardComposite(period, vesselId),
    staleTime: STALE_TIME.DASHBOARD,
  });
}

export function useSafetyDashboardHeinrich(vesselId?: string | null) {
  return useQuery({
    queryKey: safetyKeys.dashboardHeinrich(vesselId),
    queryFn: () => safetyApi.getDashboardHeinrich(vesselId),
    staleTime: STALE_TIME.DASHBOARD,
  });
}

export function useSafetyDashboardRepeatRoot(vesselId?: string | null) {
  return useQuery({
    queryKey: safetyKeys.dashboardRepeatRoot(vesselId),
    queryFn: () => safetyApi.getDashboardRepeatRoot(vesselId),
    staleTime: STALE_TIME.DASHBOARD,
  });
}

export function useSafetyDashboardPareto(vesselId?: string | null) {
  return useQuery({
    queryKey: safetyKeys.dashboardPareto(vesselId),
    queryFn: () => safetyApi.getDashboardPareto(vesselId),
    staleTime: STALE_TIME.DASHBOARD,
  });
}

export function useSafetyDashboardSoiCompliance(vesselId?: string | null) {
  return useQuery({
    queryKey: safetyKeys.dashboardSoiCompliance(vesselId),
    queryFn: () => safetyApi.getDashboardSoiCompliance(vesselId),
    staleTime: STALE_TIME.DASHBOARD,
  });
}

export function useSafetyDashboardCaAging(vesselId?: string | null) {
  return useQuery({
    queryKey: safetyKeys.dashboardCaAging(vesselId),
    queryFn: () => safetyApi.getDashboardCaAging(vesselId),
    staleTime: STALE_TIME.DASHBOARD,
  });
}

export function useSafetyIncidents(filters: SafetyIncidentFilters = {}) {
  return useQuery({
    queryKey: safetyKeys.incidents(filters),
    queryFn: () => safetyApi.getIncidents(filters),
    staleTime: STALE_TIME.INSPECTIONS,
    placeholderData: (previousData) => previousData,
  });
}

export function useSafetyIncidentPhase3Evidence(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.incidentPhase3Evidence(id),
    queryFn: () => safetyApi.getIncidentPhase3Evidence(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyIncidentPhase4Facts(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.incidentPhase4Facts(id),
    queryFn: () => safetyApi.getIncidentPhase4Facts(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyIncidentPhase5Workspace(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.incidentPhase5Workspace(id),
    queryFn: () => safetyApi.getIncidentPhase5Workspace(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyIncidentPhase6Workspace(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.incidentPhase6Workspace(id),
    queryFn: () => safetyApi.getIncidentPhase6Workspace(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyIncidentPhase7Preflight(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.incidentPhase7Preflight(id),
    queryFn: () => safetyApi.getIncidentPhase7Preflight(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyIncidentPhase8Workspace(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.incidentPhase8Workspace(id),
    queryFn: () => safetyApi.getIncidentPhase8Workspace(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyIncidentClosureSummary(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.incidentClosureSummary(id),
    queryFn: () => safetyApi.getIncidentClosureSummary(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyIncidentAudit(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.incidentAudit(id),
    queryFn: () => safetyApi.getIncidentAudit(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyCorrectiveActions(
  filters: Record<string, string | number | boolean | null | undefined> = {},
) {
  return useQuery({
    queryKey: safetyKeys.correctiveActions(filters),
    queryFn: () => safetyApi.getCorrectiveActions(filters),
    staleTime: STALE_TIME.INSPECTIONS,
    placeholderData: (previousData) => previousData,
  });
}

export function useSafetyNearMisses(filters: SafetyNearMissFilters = {}) {
  return useQuery({
    queryKey: safetyKeys.nearMisses(filters),
    queryFn: () => safetyApi.getNearMisses(filters),
    staleTime: STALE_TIME.INSPECTIONS,
    placeholderData: (previousData) => previousData,
  });
}

export function useSafetyNearMiss(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.nearMissDetail(id),
    queryFn: () => safetyApi.getNearMiss(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyNearMissAnalysis(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.nearMissAnalysis(id),
    queryFn: () => safetyApi.getNearMissAnalysis(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyNearMissFleetAlert(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.nearMissFleetAlert(id),
    queryFn: () => safetyApi.getNearMissFleetAlert(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyNearMissClosureSummary(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.nearMissClosureSummary(id),
    queryFn: () => safetyApi.getNearMissClosureSummary(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyNearMissAudit(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.nearMissAudit(id),
    queryFn: () => safetyApi.getNearMissAudit(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyScmMeetings(filters: SafetyScmFilters = {}) {
  return useQuery({
    queryKey: safetyKeys.scmMeetings(filters),
    queryFn: () => safetyApi.getScmMeetings(filters),
    staleTime: STALE_TIME.INSPECTIONS,
    placeholderData: (previousData) => previousData,
  });
}

export function useSafetyScmMeeting(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.scmMeeting(id),
    queryFn: () => safetyApi.getScmMeeting(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyScmCreateRegularConfig(vesselId?: string | null, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.scmCreateRegular(vesselId),
    queryFn: () => safetyApi.getScmCreateRegularConfig(vesselId),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyScmCreateAdhocConfig(vesselId?: string | null, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.scmCreateAdhoc(vesselId),
    queryFn: () => safetyApi.getScmCreateAdhocConfig(vesselId),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyScmAgenda(
  id: number | string,
  enabled = true,
  includeCarriedForward = false,
) {
  return useQuery({
    queryKey: safetyKeys.scmAgenda(id, includeCarriedForward),
    queryFn: () => safetyApi.getScmAgenda(id, { includeCarriedForward }),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyScmClosedSinceLast(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.scmClosedSinceLast(id),
    queryFn: () => safetyApi.getScmClosedSinceLast(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyScmAutoFeed(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.scmAutoFeed(id),
    queryFn: () => safetyApi.getScmAutoFeed(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyScmOpenFindings(vesselId?: string | null, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.scmOpenFindings(vesselId),
    queryFn: () => safetyApi.getScmOpenFindings(vesselId),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetyScmAttendance(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.scmAttendance(id),
    queryFn: () => safetyApi.getScmAttendance(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySoiCompliance(vesselId?: string | null) {
  return useQuery({
    queryKey: safetyKeys.soiCompliance(vesselId),
    queryFn: () => safetyApi.getSoiCompliance(vesselId),
    staleTime: STALE_TIME.DASHBOARD,
  });
}

export function useSafetySoiInspections(filters: SafetySoiFilters = {}) {
  return useQuery({
    queryKey: safetyKeys.soiInspections(filters),
    queryFn: () => safetyApi.getSoiInspections(filters),
    staleTime: STALE_TIME.INSPECTIONS,
    placeholderData: (previousData) => previousData,
  });
}

export function useSafetySoiCreateConfig(
  options: { plannedDate?: string; safetyOfficerCrewId?: string; vesselId?: string } = {},
  enabled = true,
) {
  return useQuery({
    queryKey: safetyKeys.soiCreateConfig(
      options.plannedDate,
      options.safetyOfficerCrewId,
      options.vesselId,
    ),
    queryFn: () => safetyApi.getSoiCreateConfig(options),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySoiInspection(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.soiInspection(id),
    queryFn: () => safetyApi.getSoiInspection(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySoiPickAreas(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.soiPickAreas(id),
    queryFn: () => safetyApi.getSoiPickAreas(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySoiCloseSnapshot(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.soiCloseSnapshot(id),
    queryFn: () => safetyApi.getSoiCloseSnapshot(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySoiFindings(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.soiFindings(id),
    queryFn: () => safetyApi.getSoiFindings(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySoiFinding(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.soiFinding(id),
    queryFn: () => safetyApi.getSoiFinding(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySoiApplicabilityRequestScreen(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.soiApplicabilityRequest(id),
    queryFn: () => safetyApi.getSoiApplicabilityRequestScreen(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySoiApplicabilityApprovalScreen(id: number | string, enabled = true) {
  return useQuery({
    queryKey: safetyKeys.soiApplicabilityApproval(id),
    queryFn: () => safetyApi.getSoiApplicabilityApprovalScreen(id),
    enabled,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}

export function useSafetySearch(
  query: string,
  recordType: string,
  includeArchived: boolean,
  enabled = true,
) {
  return useQuery({
    queryKey: safetyKeys.search(query, recordType, includeArchived),
    queryFn: () => safetyApi.searchRecords(query, { includeArchived, recordType }),
    enabled: enabled && query.trim().length >= 3,
    staleTime: STALE_TIME.INSPECTIONS,
  });
}
