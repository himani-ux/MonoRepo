interface SafetyTolerableFailureMarkerProps {
  enabled: boolean;
}

export function SafetyTolerableFailureMarker({
  enabled,
}: SafetyTolerableFailureMarkerProps) {
  return (
    <div
      className={`rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] ${
        enabled
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-slate-200 bg-slate-50 text-slate-500"
      }`}
    >
      {enabled ? "GREEN-only tolerable failure available" : "Tolerable failure locked"}
    </div>
  );
}

export default SafetyTolerableFailureMarker;
