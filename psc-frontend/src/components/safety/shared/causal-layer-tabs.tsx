import type { SafetyIncidentCauseTag } from "../../../schemas/safety/incident-phase5";

interface SafetyCausalLayerTabsProps {
  causes: SafetyIncidentCauseTag[];
  onEditCause?: (cause: SafetyIncidentCauseTag) => void;
}

const LAYER_ORDER = [
  "IMMEDIATE",
  "ROOT",
] as const;

const layerTone: Record<
  (typeof LAYER_ORDER)[number],
  string
> = {
  IMMEDIATE: "border-amber-200 bg-white text-amber-700",
  ROOT: "border-rose-300 bg-rose-50 text-rose-800",
};

function causeBelongsToCurrentLayer(cause: SafetyIncidentCauseTag, layer: (typeof LAYER_ORDER)[number]) {
  if (layer === "IMMEDIATE") {
    return cause.causal_layer === "IMMEDIATE";
  }
  return cause.causal_layer !== "IMMEDIATE";
}

export function SafetyCausalLayerTabs({
  causes,
  onEditCause,
}: SafetyCausalLayerTabsProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Cause levels
          </p>
          <h2 className="text-xl font-semibold text-slate-900">Saved causes</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {causes.length} tagged causes
        </div>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {LAYER_ORDER.map((layer) => {
          const layerRows = causes.filter((cause) => causeBelongsToCurrentLayer(cause, layer));
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
                  layerRows.map((cause) => {
                    const causeName = cause.cause_option_text || cause.mscat_description || cause.mscat_subcode_id;
                    return (
                    <article
                      key={cause.id ?? `${cause.cause_option_id ?? cause.mscat_subcode_id}-${cause.rationale}`}
                      className="rounded-2xl border border-current/20 bg-white/80 p-3"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-xs font-medium uppercase">
                            {cause.cause_factor_label || cause.cause_factor || "Cause Factor"}
                          </p>
                          <p className="mt-1 text-sm font-semibold">{causeName}</p>
                        </div>
                        {cause.id && onEditCause ? (
                          <button
                            aria-label={`Edit ${causeName}`}
                            className="rounded-full border border-current/30 bg-white px-3 py-1 text-xs font-semibold"
                            onClick={() => onEditCause(cause)}
                            type="button"
                          >
                            Edit
                          </button>
                        ) : null}
                      </div>
                      {cause.cause_other_text ? (
                        <p className="mt-1 text-sm">Other: {cause.cause_other_text}</p>
                      ) : null}
                      <p className="mt-2 text-sm">{cause.rationale}</p>
                    </article>
                    );
                  })
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
