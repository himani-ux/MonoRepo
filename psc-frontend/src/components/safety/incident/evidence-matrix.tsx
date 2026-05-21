import type { SafetyEvidenceMatrixRow } from "../../../schemas/safety/incident-phase3";

interface SafetyEvidenceMatrixProps {
  rows: SafetyEvidenceMatrixRow[];
}

export function SafetyEvidenceMatrix({ rows }: SafetyEvidenceMatrixProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            FEAT-SAF-INC-006
          </p>
          <h2 className="text-xl font-semibold text-slate-900">Evidence Matrix</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {rows.length} rows
        </div>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-slate-500">
            <tr>
              <th className="pb-2 pr-4">Finding</th>
              <th className="pb-2 pr-4">Pro evidence</th>
              <th className="pb-2 pr-4">Con evidence</th>
              <th className="pb-2 pr-4">Source</th>
            </tr>
          </thead>
          <tbody className="align-top text-slate-700">
            {rows.length > 0 ? (
              rows.map((row, index) => (
                <tr key={row.id ?? `${row.finding}-${index}`} className="border-t border-slate-100">
                  <td className="py-3 pr-4 font-medium">{row.finding || "Major finding"}</td>
                  <td className="py-3 pr-4">{row.pro_evidence || "Pending"}</td>
                  <td className="py-3 pr-4">{row.con_evidence || "Pending contradiction review"}</td>
                  <td className="py-3 pr-4">{row.source_label || "Investigator entry"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="py-4 text-slate-500" colSpan={4}>
                  No matrix rows drafted yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default SafetyEvidenceMatrix;
