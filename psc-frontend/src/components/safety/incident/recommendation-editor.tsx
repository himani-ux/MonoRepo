import type {
  SafetyIncidentPhase6Workspace,
  SafetyRecommendation,
} from '../../../schemas/safety/incident-phase6';

interface SafetyRecommendationEditorProps {
  heading?: string;
  onEditRecommendation?: (recommendation: SafetyRecommendation) => void;
  tiers?: ReadonlyArray<keyof SafetyIncidentPhase6Workspace['recommendations']>;
  workspace: SafetyIncidentPhase6Workspace;
}

const TIER_META: Record<
  keyof SafetyIncidentPhase6Workspace['recommendations'],
  { eyebrow: string; tone: string }
> = {
  CORRECTIVE: {
    eyebrow: 'Fix now',
    tone: 'border-rose-200 bg-rose-50 text-rose-900',
  },
  PREVENTIVE: {
    eyebrow: 'Prevent next time',
    tone: 'border-sky-200 bg-sky-50 text-sky-900',
  },
  LESSONS_LEARNT: {
    eyebrow: 'Lesson learned',
    tone: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  },
};

function RecommendationCard({
  onEdit,
  recommendation,
}: {
  onEdit?: (recommendation: SafetyRecommendation) => void;
  recommendation: SafetyRecommendation;
}) {
  const linkedAction = recommendation.corrective_actions[0];

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          {recommendation.tolerable_failure_filter ? (
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700">
              Tolerable failure
            </span>
          ) : null}
        </div>
        {recommendation.id && onEdit ? (
          <button
            aria-label={`Edit ${recommendation.description}`}
            className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-semibold text-slate-700"
            onClick={() => onEdit(recommendation)}
            type="button"
          >
            Edit
          </button>
        ) : null}
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        {recommendation.description}
      </p>
      {linkedAction?.due_date ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
          <p>
            <span className="font-semibold">Due date:</span>{' '}
            {linkedAction.due_date}
          </p>
        </div>
      ) : null}
    </article>
  );
}

export function SafetyRecommendationEditor({
  heading = 'Summary',
  onEditRecommendation,
  tiers,
  workspace,
}: SafetyRecommendationEditorProps) {
  const visibleTiers =
    tiers ??
    (Object.keys(workspace.recommendations) as Array<
      keyof SafetyIncidentPhase6Workspace['recommendations']
    >);

  return (
    <section className="space-y-4">
      <header className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Saved actions
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">
            {heading}
          </h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-600">
          {workspace.corrective_actions.length} linked actions
        </div>
      </header>

      <div
        className={
          visibleTiers.length === 1 ? 'grid gap-4' : 'grid gap-4 xl:grid-cols-3'
        }
      >
        {visibleTiers.map((tierKey) => {
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
                </div>
              </div>

              <div className="mt-4 space-y-3">
                {rows.length > 0 ? (
                  rows.map((recommendation) => (
                    <RecommendationCard
                      key={`${tierKey}-${recommendation.id ?? recommendation.title}`}
                      onEdit={onEditRecommendation}
                      recommendation={recommendation}
                    />
                  ))
                ) : (
                  <div className="border-current/25 rounded-2xl border border-dashed bg-white/70 p-4 text-sm leading-6">
                    Nothing added here yet.
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
