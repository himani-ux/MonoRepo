export interface SafetyVesselDisplaySource {
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_id?: string | number | null;
  vessel_name?: string | null;
}

function clean(value: unknown): string {
  return String(value ?? "").trim();
}

export function formatVesselName(source: SafetyVesselDisplaySource | null | undefined): string {
  if (!source) {
    return "Not recorded";
  }
  return (
    clean(source.vessel_name) ||
    clean(source.vessel_display_name) ||
    clean(source.vessel_code) ||
    clean(source.vessel_id) ||
    "Not recorded"
  );
}
