import type { SafetySoiCrewSnapshot } from "../../../schemas/safety/soi";

interface SafetyAssistantPickerProps {
  assistantCandidates: SafetySoiCrewSnapshot[];
  disabled?: boolean;
  onSelectAssistantId?: (crewId: string) => void;
  safetyOfficer: SafetySoiCrewSnapshot;
  selectedAssistantId: string;
}

export default function SafetyAssistantPicker({
  assistantCandidates,
  disabled = false,
  onSelectAssistantId,
  safetyOfficer,
  selectedAssistantId,
}: SafetyAssistantPickerProps) {
  return (
    <section className="rounded-[1.75rem] border border-sky-200 bg-gradient-to-br from-sky-50 via-white to-amber-50 p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Cross-functional assistant</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Step 4.2 locks the SSQE cross-functional rule at the create seam. The
            Safety Officer remains on the deck side here, so the assistant options
            are constrained to current engine-side CMS crew only.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Safety Officer
          </div>
          <div className="mt-2 font-medium text-slate-900">{safetyOfficer.crew_id}</div>
          <div className="text-sm text-slate-600">
            {safetyOfficer.rank} · {safetyOfficer.department}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        {assistantCandidates.map((candidate) => {
          const selected = candidate.crew_id === selectedAssistantId;

          return (
            <article
              key={candidate.crew_id}
              className={`rounded-2xl border p-4 transition ${
                selected
                  ? "border-sky-400 bg-sky-900 text-white shadow-lg shadow-sky-100"
                  : "border-slate-200 bg-white text-slate-700 shadow-sm"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold tracking-[0.18em] uppercase opacity-80">
                    Assistant
                  </div>
                  <h3 className="mt-2 text-lg font-semibold">{candidate.crew_id}</h3>
                  <p className={`mt-2 text-sm ${selected ? "text-sky-100" : "text-slate-600"}`}>
                    {candidate.rank} from {candidate.department}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-medium ${
                    selected
                      ? "bg-white/15 text-white"
                      : "bg-emerald-50 text-emerald-700"
                  }`}
                >
                  {selected ? "Selected" : "Eligible"}
                </span>
              </div>
              {onSelectAssistantId ? (
                <button
                  className={`mt-4 rounded-full px-4 py-2 text-sm font-semibold transition ${
                    selected
                      ? "bg-white/15 text-white"
                      : "border border-slate-300 bg-white text-slate-800 hover:border-slate-400 hover:bg-slate-50"
                  }`}
                  disabled={disabled}
                  onClick={() => onSelectAssistantId(candidate.crew_id)}
                  type="button"
                >
                  {selected ? "Selected assistant" : "Select assistant"}
                </button>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
