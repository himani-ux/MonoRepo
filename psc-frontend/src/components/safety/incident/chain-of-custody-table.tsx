import type { SafetyChainOfCustodyRow } from "../../../schemas/safety/incident-phase3";

interface SafetyChainOfCustodyTableProps {
  rows: SafetyChainOfCustodyRow[];
}

export function SafetyChainOfCustodyTable({
  rows,
}: SafetyChainOfCustodyTableProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Evidence control
          </p>
          <h2 className="text-xl font-semibold text-slate-900">Who Has the Evidence</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {rows.length} items
        </div>
      </div>
      <div className="mt-4 space-y-3">
        {rows.length > 0 ? (
          rows.map((row) => (
            <article key={row.id} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
              <h3 className="font-medium text-slate-900">{row.description}</h3>
              <p className="mt-1 text-sm text-slate-600">
                Collected by: {row.collector_name} | Kept at: {row.storage_location}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                Now with: {row.current_holder} | Handovers: {row.handover_log.length}
              </p>
            </article>
          ))
        ) : (
          <p className="text-sm text-slate-500">No evidence control items added yet.</p>
        )}
      </div>
    </section>
  );
}

export default SafetyChainOfCustodyTable;
