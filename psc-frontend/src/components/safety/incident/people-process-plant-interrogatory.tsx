import type { SafetyIncidentPhase5Assessment } from "../../../schemas/safety/incident-phase5";

interface SafetyPeopleProcessPlantInterrogatoryProps {
  assessment: SafetyIncidentPhase5Assessment | null | undefined;
}

const PROMPTS = [
  {
    key: "people_contribution_text",
    label: "People",
  },
  {
    key: "process_gap_text",
    label: "Process",
  },
  {
    key: "plant_failure_text",
    label: "Plant",
  },
] as const;

export function SafetyPeopleProcessPlantInterrogatory({
  assessment,
}: SafetyPeopleProcessPlantInterrogatoryProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        Cause review
      </p>
      <h2 className="mt-1 text-xl font-semibold text-slate-900">
        People / Process / Plant
      </h2>
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        {PROMPTS.map((prompt) => (
          <article
            key={prompt.key}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <h3 className="text-sm font-semibold text-slate-900">{prompt.label}</h3>
            <p className="mt-2 text-sm text-slate-600">
              {(assessment?.[prompt.key] as string | undefined) ?? "Pending investigator answer."}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default SafetyPeopleProcessPlantInterrogatory;
