interface SafetyPartialSubmissionIndicatorProps {
  completedCount: number;
  pendingAreaNames: string[];
  totalCount: number;
}

export default function SafetyPartialSubmissionIndicator({
  completedCount,
  pendingAreaNames,
  totalCount,
}: SafetyPartialSubmissionIndicatorProps) {
  const pendingCount = Math.max(totalCount - completedCount, 0);

  return (
    <section className="rounded-[1.75rem] border border-sky-200 bg-gradient-to-r from-sky-50 via-white to-emerald-50 p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Partial submission progress</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {completedCount} of {totalCount} areas complete. Remaining areas keep the same checklist ID and
            stay resumable until their findings are submitted.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Pending</div>
          <div className="mt-2 font-medium text-slate-900">
            {pendingCount === 0 ? "All selected areas submitted" : `${pendingCount} area(s) pending`}
          </div>
          <div className="mt-2 text-slate-600">
            {pendingAreaNames.length > 0 ? pendingAreaNames.join(", ") : "No remaining areas."}
          </div>
        </div>
      </div>
    </section>
  );
}
