interface SafetyLifeThreatEscalationBannerProps {
  matches: string[];
  onSelectTarget: (target: "INCIDENT" | "NEAR_MISS") => void;
  selectedTarget: "INCIDENT" | "NEAR_MISS" | null;
}

export default function SafetyLifeThreatEscalationBanner({
  matches,
  onSelectTarget,
  selectedTarget,
}: SafetyLifeThreatEscalationBannerProps) {
  if (matches.length === 0) {
    return null;
  }

  return (
    <section className="rounded-[1.75rem] border border-rose-300 bg-[linear-gradient(135deg,_rgba(254,226,226,0.96),_rgba(255,255,255,0.98))] p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-rose-700">Life-threat escalation</p>
      <h2 className="mt-3 text-lg font-semibold text-slate-950">Parallel Incident or Near Miss is mandatory</h2>
      <p className="mt-2 text-sm leading-6 text-slate-700">
        The current finding text matches Step 4.8 life-threat keywords. Save stays blocked until you choose
        the parallel escalation path.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        {matches.map((match) => (
          <span
            className="rounded-full border border-rose-300 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-rose-700"
            key={match}
          >
            {match}
          </span>
        ))}
      </div>
      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <button
          className={`rounded-full px-5 py-3 text-sm font-semibold transition ${
            selectedTarget === "INCIDENT"
              ? "bg-rose-700 text-white"
              : "border border-rose-300 bg-white text-rose-800 hover:bg-rose-50"
          }`}
          onClick={() => onSelectTarget("INCIDENT")}
          type="button"
        >
          Create Incident
        </button>
        <button
          className={`rounded-full px-5 py-3 text-sm font-semibold transition ${
            selectedTarget === "NEAR_MISS"
              ? "bg-slate-900 text-white"
              : "border border-slate-300 bg-white text-slate-800 hover:bg-slate-50"
          }`}
          onClick={() => onSelectTarget("NEAR_MISS")}
          type="button"
        >
          Create Near Miss
        </button>
      </div>
    </section>
  );
}
