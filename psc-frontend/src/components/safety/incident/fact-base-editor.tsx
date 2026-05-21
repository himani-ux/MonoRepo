import type { SafetyIncidentFact } from "../../../schemas/safety/incident-phase4";

interface SafetyFactBaseEditorProps {
  facts: SafetyIncidentFact[];
}

function renderConfidenceChip(confidence: SafetyIncidentFact["confidence"]) {
  const tone =
    confidence === "HIGH"
      ? "border-emerald-200 bg-emerald-50 text-emerald-700"
      : confidence === "LOW"
        ? "border-rose-200 bg-rose-50 text-rose-700"
        : "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <span className={`rounded-full border px-3 py-1 text-xs font-medium uppercase ${tone}`}>
      {confidence}
    </span>
  );
}

export function SafetyFactBaseEditor({ facts }: SafetyFactBaseEditorProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            FEAT-SAF-INC-015
          </p>
          <h2 className="text-xl font-semibold text-slate-900">Fact Base Editor</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {facts.length} facts
        </div>
      </div>
      <div className="mt-4 space-y-3">
        {facts.length > 0 ? (
          facts.map((fact) => (
            <article
              key={fact.id ?? `${fact.sequence_index}-${fact.fact_text}`}
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium uppercase text-slate-700">
                  Step {fact.sequence_index}
                </span>
                {renderConfidenceChip(fact.confidence)}
                {fact.hindsight_guard_triggered ? (
                  <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium uppercase text-amber-800">
                    Hindsight override
                  </span>
                ) : null}
              </div>
              <p className="mt-3 text-sm text-slate-900">{fact.fact_text}</p>
              <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                <p>Evidence: {fact.evidence_summary}</p>
                <p>Timestamp: {fact.fact_timestamp ?? "Pending investigator timestamp"}</p>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-600">
            No facts systemized yet. Add your first fact - each must cite evidence.
          </div>
        )}
      </div>
    </section>
  );
}

export default SafetyFactBaseEditor;
