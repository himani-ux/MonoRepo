type SafetySoiComplianceStatus = "GREEN" | "AMBER" | "RED" | "NA";

interface SafetySoiCompliancePillProps {
  applicableAreaCount: number;
  displayValue: string;
  inspectedAreaCount: number;
  label: string;
  note?: string;
  status: SafetySoiComplianceStatus;
}

const statusClasses: Record<SafetySoiComplianceStatus, string> = {
  AMBER: "border-amber-200 bg-amber-50 text-amber-950",
  GREEN: "border-emerald-200 bg-emerald-50 text-emerald-950",
  NA: "border-slate-200 bg-slate-50 text-slate-900",
  RED: "border-rose-200 bg-rose-50 text-rose-950",
};

export function SafetySoiCompliancePill({
  applicableAreaCount,
  displayValue,
  inspectedAreaCount,
  label,
  note,
  status,
}: SafetySoiCompliancePillProps) {
  return (
    <article className={`rounded-[1.75rem] border px-5 py-4 shadow-sm ${statusClasses[status]}`}>
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</div>
      <div className="mt-3 flex items-end justify-between gap-4">
        <div>
          <div className="text-3xl font-semibold">{displayValue}</div>
          <div className="mt-2 text-sm text-slate-600">
            {inspectedAreaCount} of {applicableAreaCount} applicable areas are inside the current 90-day window.
          </div>
        </div>
        <span className="rounded-full border border-current px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]">
          {status}
        </span>
      </div>
      {note ? <p className="mt-3 text-sm text-slate-600">{note}</p> : null}
    </article>
  );
}

export default SafetySoiCompliancePill;
