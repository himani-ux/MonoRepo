import type { SafetyIncidentPhase5Assessment } from "../../../schemas/safety/incident-phase5";

interface SafetyMultiToolWorkspaceProps {
  assessment: SafetyIncidentPhase5Assessment | null | undefined;
  minimumToolsRequired: number;
  toolWorkspaces?: Record<string, Record<string, string>>;
}

const TOOL_LABELS: Record<string, string> = {
  STEP: "STEP",
  FACT_TREE: "Fact Tree",
  ECF: "ECF",
  BARRIER: "Barrier",
  CHANGE: "Change",
};

export function SafetyMultiToolWorkspace({
  assessment,
  minimumToolsRequired,
  toolWorkspaces = {},
}: SafetyMultiToolWorkspaceProps) {
  const tools: Array<keyof typeof TOOL_LABELS> =
    assessment?.analysis_tools_used ?? [];

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Analysis methods
          </p>
          <h2 className="text-xl font-semibold text-slate-900">Analysis Notes</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {tools.length}/{minimumToolsRequired} tools
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        {(Object.entries(TOOL_LABELS) as Array<
          [keyof typeof TOOL_LABELS, string]
        >).map(([tool, label]) => {
          const active = tools.includes(tool);
          return (
            <div
              key={tool}
              className={`rounded-full border px-4 py-2 text-sm font-medium ${
                active
                  ? "border-sky-200 bg-sky-50 text-sky-800"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              {label}
            </div>
          );
        })}
      </div>
      <div className="mt-4 grid gap-3">
        {(Object.entries(TOOL_LABELS) as Array<
          [keyof typeof TOOL_LABELS, string]
        >).map(([tool, label]) => {
          const fields = Object.entries(toolWorkspaces[tool] ?? {}).filter(
            ([, value]) => value.trim(),
          );
          return (
            <article key={`${tool}-details`} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <h3 className="font-semibold text-slate-900">{label}</h3>
              {fields.length > 0 ? (
                <dl className="mt-3 grid gap-3 md:grid-cols-2">
                  {fields.map(([field, value]) => (
                    <div key={field}>
                      <dt className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                        {field.replaceAll("_", " ")}
                      </dt>
                      <dd className="mt-1 break-words text-sm leading-6 text-slate-800">{value}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <p className="mt-2 text-sm text-slate-500">No structured notes saved yet.</p>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default SafetyMultiToolWorkspace;
