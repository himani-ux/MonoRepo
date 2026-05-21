import type { SafetyIncidentFact } from "../../../schemas/safety/incident-phase4";

interface SafetyNearMissFactTreeEditorProps {
  facts: SafetyIncidentFact[];
  incidentId: string;
}

function confidenceTone(confidence: SafetyIncidentFact["confidence"]) {
  if (confidence === "HIGH") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  if (confidence === "LOW") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}

export function SafetyNearMissFactTreeEditor({
  facts,
  incidentId,
}: SafetyNearMissFactTreeEditorProps) {
  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            Safety / Near Miss / High Priority
          </p>
          <h1 className="text-3xl font-semibold text-slate-900">Near Miss Fact Tree</h1>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            Step 2.3 stays intentionally lightweight: fact tree only, no causal-layer
            tagging, no safeguard matrix, and no full incident-phase investigation stack.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <div>Ref: {incidentId}</div>
          <div>Mode: Fact Tree only</div>
          <div>Physical verification: not required</div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <section className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-5">
          {facts.length > 0 ? (
            facts.map((fact) => (
              <article
                key={fact.id ?? `${fact.sequence_index}-${fact.fact_text}`}
                className="rounded-2xl border border-slate-200 bg-white p-4"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium uppercase text-slate-700">
                    Fact {fact.sequence_index}
                  </span>
                  <span
                    className={`rounded-full border px-3 py-1 text-xs font-medium uppercase ${confidenceTone(fact.confidence)}`}
                  >
                    {fact.confidence}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-900">{fact.fact_text}</p>
                <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                  <p>Evidence: {fact.evidence_summary}</p>
                  <p>Timestamp: {fact.fact_timestamp ?? "Pending timestamp"}</p>
                </div>
              </article>
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-5 text-sm text-slate-600">
              No fact-tree rows yet. Add the first evidence-linked fact to start the lightweight analysis.
            </div>
          )}
        </section>

        <aside className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5">
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
            Bias guards 1, 2, and 3 still apply in this lightweight workspace. The heavier
            incident-only analysis checks stay out of scope here.
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700">
            Required outputs for this step:
            <div className="mt-2">Lessons Learned and Immediate Action remain in scope.</div>
            <div>System Action stays optional until later near-miss steps.</div>
          </div>
        </aside>
      </div>
    </section>
  );
}

export default SafetyNearMissFactTreeEditor;
