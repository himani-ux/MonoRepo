interface SafetyHealthFatiguePanelProps {
  mlcReportable?: boolean;
  medicalRecords?: string[];
  summary?: string;
}

export function SafetyHealthFatiguePanel({
  mlcReportable = false,
  medicalRecords = [],
  summary = "No health / fatigue narrative captured yet.",
}: SafetyHealthFatiguePanelProps) {
  return (
    <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
        FEAT-SAF-INC-010
      </p>
      <h2 className="mt-1 text-xl font-semibold text-emerald-950">
        Health / Fatigue Evidence
      </h2>
      <p className="mt-3 text-sm leading-6 text-emerald-900">{summary}</p>
      <div className="mt-4 flex flex-wrap gap-3 text-sm">
        <span className="rounded-full border border-emerald-200 bg-white/80 px-3 py-1 text-emerald-800">
          MLC reportable: {mlcReportable ? "Yes" : "No"}
        </span>
        <span className="rounded-full border border-emerald-200 bg-white/80 px-3 py-1 text-emerald-800">
          Medical records: {medicalRecords.length}
        </span>
      </div>
    </section>
  );
}

export default SafetyHealthFatiguePanel;
