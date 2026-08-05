export interface SafetyNearMissClosureSummaryPayload {
  auditSummary: {
    fieldHistoryCount: number;
    phaseLogCount: number;
  };
  closedAt: string;
  closureReason: string;
  incidentNumber: string;
  priority: "LOW" | "HIGH";
  reporterVisible: boolean;
  state: string;
  vesselId: string;
  vesselName?: string;
  visibilityRule: string;
}

export function SafetyNearMissClosureSummary({
  auditSummary,
  closedAt,
  closureReason,
  incidentNumber,
  priority,
  state,
  vesselId,
  vesselName,
  visibilityRule,
}: SafetyNearMissClosureSummaryPayload) {
  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_48%,#d1fae5_100%)] p-6 shadow-sm">
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          Closed Near Miss Summary
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Read-only closure surface for the lightweight near-miss path. Reporter
          details are available to authorized users.
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
            <span
              className={
                priority === "HIGH"
                  ? "rounded-full bg-rose-50 px-3 py-1 text-xs font-medium text-rose-700"
                  : "rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700"
              }
            >
              {priority}
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

        <aside className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-slate-900">Reporter Details</h2>
          </div>
          <p className="text-sm leading-6 text-slate-600">{visibilityRule}</p>
          <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4 text-sm leading-6 text-sky-900">
            This summary is read-only. Use the review screen to close the record and capture signatures.
          </div>
        </aside>
      </div>
    </section>
  );
}

export default SafetyNearMissClosureSummary;
