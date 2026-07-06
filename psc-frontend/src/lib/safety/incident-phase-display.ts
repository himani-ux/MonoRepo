export function displayIncidentPhase(phase?: number | null): number {
  const normalized = Number(phase || 1);
  if (!Number.isFinite(normalized) || normalized <= 1) {
    return 1;
  }
  if (normalized === 2) {
    return 1;
  }
  if (normalized === 3 || normalized === 5) {
    return 2;
  }
  if (normalized === 6) {
    return 3;
  }
  if (normalized === 4) {
    return 5;
  }
  if (normalized === 7) {
    return 6;
  }
  if (normalized === 8) {
    return 7;
  }
  return normalized;
}

export function incidentPhaseLabel(phase?: number | null): string {
  const normalized = Number(phase || 1);
  if (normalized >= 9) {
    return "Closed";
  }
  const displayPhase = displayIncidentPhase(phase);
  if (displayPhase === 1) {
    return "Phase 1 - Report Incident";
  }
  if (displayPhase === 2) {
    return "Phase 2 - RCA (Root Cause Analysis)";
  }
  if (displayPhase === 3) {
    return "Phase 3 - Corrective Action";
  }
  if (displayPhase === 4) {
    return "Phase 4 - Preventive Action";
  }
  if (displayPhase === 5) {
    return "Phase 5 - Add Evidence";
  }
  if (displayPhase === 6) {
    return "Phase 6 - Office Review";
  }
  if (displayPhase === 7) {
    return "Phase 7 - Loss Evaluation";
  }
  return `Phase ${displayPhase}`;
}

export function incidentPhaseStepLabel(phase?: number | null): string {
  const normalized = Number(phase || 1);
  if (normalized === 2) {
    return "Phase 1 - Report Incident";
  }
  return incidentPhaseLabel(normalized);
}

export function incidentPhaseRoute(id: number | string, phase?: number | null): string {
  const normalized = Number(phase || 1);
  if (normalized >= 9) {
    return `/safety/incidents/${id}/phase-6`;
  }
  if (normalized === 2) {
    return `/safety/incidents/${id}/office-communication`;
  }
  if (normalized === 3 || normalized === 5) {
    return `/safety/incidents/${id}/phase-2`;
  }
  if (normalized === 4) {
    return `/safety/incidents/${id}/phase-4/paper`;
  }
  if (normalized === 6) {
    return `/safety/incidents/${id}/phase-3`;
  }
  if (normalized === 7) {
    return `/safety/incidents/${id}/phase-5`;
  }
  if (normalized === 8) {
    return `/safety/incidents/${id}/phase-6`;
  }
  return `/safety/incidents/${id}/phase-${displayIncidentPhase(normalized)}`;
}
