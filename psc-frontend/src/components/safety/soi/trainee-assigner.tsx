import type { SafetySoiCrewSnapshot } from "../../../schemas/safety/soi";

interface SafetyTraineeAssignerProps {
  availableCrew: SafetySoiCrewSnapshot[];
  disabled?: boolean;
  maxTrainees: number;
  onTraineeCrewIdChange?: (slot: number, crewId: string) => void;
  traineeCrewIds: string[];
}

function findCrew(
  availableCrew: SafetySoiCrewSnapshot[],
  crewId: string | undefined,
) {
  if (!crewId) {
    return null;
  }

  return availableCrew.find((candidate) => candidate.crew_id === crewId) ?? null;
}

export default function SafetyTraineeAssigner({
  availableCrew,
  disabled = false,
  maxTrainees,
  onTraineeCrewIdChange,
  traineeCrewIds,
}: SafetyTraineeAssignerProps) {
  const slots = Array.from({ length: maxTrainees }, (_, index) => index + 1);

  return (
    <section className="rounded-[1.75rem] border border-emerald-200 bg-gradient-to-br from-emerald-50 via-white to-slate-50 p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Trainee participation</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Up to three crew may accompany the inspection for training-through-participation.
            They are tracked for rotation coverage but do not enter the SO + Assistant
            paper-signature chain.
          </p>
        </div>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-800">
          Max {maxTrainees}
        </span>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {slots.map((slot) => {
          const selectedCrew = findCrew(availableCrew, traineeCrewIds[slot - 1]);

          return (
            <article
              key={slot}
              className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                Slot {slot}
              </div>
              {onTraineeCrewIdChange ? (
                <label className="mt-3 block">
                  <span className="sr-only">Trainee slot {slot}</span>
                  <select
                    aria-label={`Trainee slot ${slot}`}
                    className="w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm text-slate-900"
                    disabled={disabled}
                    onChange={(event) => onTraineeCrewIdChange(slot, event.target.value)}
                    value={traineeCrewIds[slot - 1] ?? ""}
                  >
                    <option value="">No trainee assigned</option>
                    {availableCrew.map((candidate) => (
                      <option key={`${slot}-${candidate.crew_id}`} value={candidate.crew_id}>
                        {candidate.crew_id} - {candidate.rank}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
              {selectedCrew ? (
                <>
                  <h3 className="mt-3 text-base font-semibold text-slate-900">
                    {selectedCrew.crew_id}
                  </h3>
                  <p className="mt-2 text-sm text-slate-600">
                    {selectedCrew.rank} · {selectedCrew.department}
                  </p>
                </>
              ) : (
                <p className="mt-3 text-sm text-slate-500">
                  Keep open for the next trainee if the vessel wants broader rotation coverage.
                </p>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
