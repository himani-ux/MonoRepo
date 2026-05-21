interface SafetyWitnessReadbackProps {
  readBackConfirmed: boolean;
  witnessSignature?: string | null;
  copyToWitnessRecorded: boolean;
}

export function SafetyWitnessReadback({
  readBackConfirmed,
  witnessSignature,
  copyToWitnessRecorded,
}: SafetyWitnessReadbackProps) {
  const rows = [
    {
      done: readBackConfirmed,
      label: "Read-back to witness",
    },
    {
      done: Boolean(witnessSignature),
      label: "Witness signature captured",
    },
    {
      done: copyToWitnessRecorded,
      label: "Copy to witness recorded",
    },
  ];

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        FEAT-SAF-INC-014
      </p>
      <h2 className="mt-1 text-xl font-semibold text-slate-900">
        Witness Read-Back + Sign-Off
      </h2>
      <div className="mt-4 grid gap-3">
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-700"
          >
            <input checked={row.done} readOnly type="checkbox" />
            <span>{row.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

export default SafetyWitnessReadback;
