export interface SafetyClosureSummaryPayload {
  auditSummary: {
    fieldHistoryCount: number;
    phaseLogCount: number;
  };
  closedAt: string;
  closureReason: string;
  incidentNumber: string;
  riskBand: string;
  state: string;
  vesselId: string;
  vesselName?: string;
  visibilityRule: string;
}

export function SafetyClosureSummary({
  auditSummary,
  closedAt,
  closureReason,
  incidentNumber,
  riskBand,
  state,
  vesselId,
  vesselName,
  visibilityRule,
}: SafetyClosureSummaryPayload) {
  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#ecfeff_0%,#ffffff_50%,#fef3c7_100%)] p-6 shadow-sm">
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          Closed Incident Summary
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Read-only closure summary for closed-record review, vessel learning,
          and audit readiness. Rank persists, and the closure record stays tied
          to the current role-holder rather than any Acting-role variant.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
              {incidentNumber}
            </span>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
              {state}
            </span>
            <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
              {riskBand}
            </span>
          </div>

          <dl className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Vessel
              </dt>
              <dd className="mt-2 text-lg font-semibold text-slate-900">{vesselName || vesselId}</dd>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Closed At
              </dt>
              <dd className="mt-2 text-lg font-semibold text-slate-900">{closedAt}</dd>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Phase Log Rows
              </dt>
              <dd className="mt-2 text-lg font-semibold text-slate-900">
                {auditSummary.phaseLogCount}
              </dd>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <dt className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Field Changes
              </dt>
              <dd className="mt-2 text-lg font-semibold text-slate-900">
                {auditSummary.fieldHistoryCount}
              </dd>
            </div>
          </dl>

          <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-4">
            <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-500">
              Closure Reason
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-700">{closureReason}</p>
          </div>
        </article>

        <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Visibility Rule</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">{visibilityRule}</p>
          <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
            Office classification maintenance remains separate from this closure
            view. Closed-record review is read-only here.
          </div>
        </aside>
      </div>
    </section>
  );
}

export default SafetyClosureSummary;
