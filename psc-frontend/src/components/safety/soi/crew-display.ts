export interface SafetyCrewDisplayInput {
  crew_id?: string | null;
  rank?: string | null;
}

export function formatSoiCrewDisplay(crew: SafetyCrewDisplayInput | null | undefined) {
  const crewId = String(crew?.crew_id ?? "").trim();
  const rank = String(crew?.rank ?? "").trim();

  if (rank && crewId) {
    return `${rank} (${crewId})`;
  }

  return rank || crewId || "Not resolved";
}

