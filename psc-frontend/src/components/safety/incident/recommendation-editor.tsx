import type {
  SafetyIncidentPhase6Workspace,
  SafetyRecommendation,
} from "../../../schemas/safety/incident-phase6";

interface SafetyRecommendationEditorProps {
  workspace: SafetyIncidentPhase6Workspace;
}

const TIER_META: Record<
  keyof SafetyIncidentPhase6Workspace["recommendations"],
  { eyebrow: string; tone: string }
> = {
  CORRECTIVE: {
    eyebrow: "Corrective / Immediate",
    tone: "border-rose-200 bg-rose-50 text-rose-900",
  },
  PREVENTIVE: {
    eyebrow: "Preventive / System",
    tone: "border-sky-200 bg-sky-50 text-sky-900",
  },
  LESSONS_LEARNT: {
    eyebrow: "Lessons Learnt",
    tone: "border-emerald-200 bg-emerald-50 text-emerald-900",
  },
};

function RecommendationCard({
  recommendation,
}: {
  recommendation: SafetyRecommendation;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-base font-semibold text-slate-900">
          {recommendation.title}
        </h3>
        {recommendation.tolerable_failure_filter ? (
          <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
            Tolerable failure
          </span>
        ) : null}
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        {recommendation.description}
      </p>
      {recommendation.theme_code ? (
        <p className="mt-3 text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
          Theme: {recommendation.theme_code.replaceAll("_", " ")}
        </p>
      ) : null}
      {recommendation.estimated_effort ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
          <p>
            <span className="font-semibold">Estimated effort:</span>{" "}
            {recommendation.estimated_effort}
          </p>
          <p className="mt-2">
            <span className="font-semibold">Likelihood reduction:</span>{" "}
            {recommendation.estimated_likelihood_reduction ?? "Pending"}
          </p>
          <p className="mt-2">
            <span className="font-semibold">Residual risk:</span>{" "}
            {recommendation.residual_risk_statement ?? "Pending"}
          </p>
        </div>
      ) : null}
    </article>
  );
}

export function SafetyRecommendationEditor({
  workspace,
}: SafetyRecommendationEditorProps) {
  return (
    <section className="space-y-4">
      <header className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            FEAT-SAF-INC-027
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            Three-Tier Recommendation Editor
          </h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-600">
          {workspace.corrective_actions.length} linked CA rows
        </div>
      </header>

      <div className="grid gap-4 xl:grid-cols-3">
        {(Object.keys(workspace.recommendations) as Array<
          keyof SafetyIncidentPhase6Workspace["recommendations"]
        >).map((tierKey) => {
          const rows = workspace.recommendations[tierKey];
          const meta = TIER_META[tierKey];

          return (
            <section
              key={tierKey}
              className={`rounded-3xl border p-4 shadow-sm ${meta.tone}`}
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em]">
                    {meta.eyebrow}
                  </p>
                  <h3 className="mt-2 text-lg font-semibold">
                    {workspace.tier_counts[tierKey] ?? 0} row
                    {(workspace.tier_counts[tierKey] ?? 0) === 1 ? "" : "s"}
                  </h3>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                {rows.length > 0 ? (
                  rows.map((recommendation) => (
                    <RecommendationCard
                      key={`${tierKey}-${recommendation.id ?? recommendation.title}`}
                      recommendation={recommendation}
                    />
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-current/25 bg-white/70 p-4 text-sm leading-6">
                    No rows scaffolded in this tier yet.
                  </div>
                )}
              </div>
            </section>
          );
        })}
      </div>
    </section>
  );
}

export default SafetyRecommendationEditor;
