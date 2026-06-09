import type { SafetyIncidentCauseTag } from "../../../schemas/safety/incident-phase5";

interface SafetyCausalLayerTabsProps {
  causes: SafetyIncidentCauseTag[];
}

const LAYER_ORDER = [
  "IMMEDIATE",
  "INTERMEDIATE",
  "ROOT",
] as const satisfies SafetyIncidentCauseTag["causal_layer"][];

const layerTone: Record<
  SafetyIncidentCauseTag["causal_layer"],
  string
> = {
  IMMEDIATE: "border-amber-200 bg-white text-amber-700",
  INTERMEDIATE: "border-amber-300 bg-amber-50 text-amber-800",
  ROOT: "border-rose-300 bg-rose-50 text-rose-800",
};

export function SafetyCausalLayerTabs({
  causes,
}: SafetyCausalLayerTabsProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Cause levels
          </p>
          <h2 className="text-xl font-semibold text-slate-900">Causal Layers</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {causes.length} tagged causes
        </div>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        {LAYER_ORDER.map((layer) => {
          const layerRows = causes.filter((cause) => cause.causal_layer === layer);
          return (
            <div
              key={layer}
              className={`rounded-2xl border p-4 ${layerTone[layer]}`}
            >
              <p className="text-xs font-semibold uppercase tracking-[0.2em]">
                {layer}
              </p>
              <div className="mt-3 space-y-3">
                {layerRows.length > 0 ? (
                  layerRows.map((cause) => (
                    <article
                      key={cause.id ?? `${cause.mscat_subcode_id}-${cause.rationale}`}
                      className="rounded-2xl border border-current/20 bg-white/80 p-3"
                    >
                      <p className="text-xs font-medium uppercase">
                        {cause.mscat_subcode_id}
                      </p>
                      <p className="mt-2 text-sm">{cause.rationale}</p>
                    </article>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-current/30 bg-white/70 p-4 text-sm">
                    {layer === "ROOT"
                      ? "At least one Root-level cause is required before closing Phase 5."
                      : "No causes tagged in this layer yet."}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default SafetyCausalLayerTabs;
