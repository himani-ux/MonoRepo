import type { SafetyWitnessInterview } from '../../../schemas/safety/incident-phase3';

interface SafetyInterviewModuleProps {
  interviews: SafetyWitnessInterview[];
  onEditInterview?: (interview: SafetyWitnessInterview) => void;
}

export function SafetyInterviewModule({
  interviews,
  onEditInterview,
}: SafetyInterviewModuleProps) {
  return (
    <section className="space-y-5 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Witness statement
          </p>
          <h2 className="text-xl font-semibold text-slate-900">
            Saved Witness Statements
          </h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {interviews.length} note{interviews.length === 1 ? '' : 's'}
        </div>
      </div>

      {interviews.length > 0 ? (
        interviews.map((interview, index) => (
          <article
            key={interview.id ?? `${interview.witness_name}-${index}`}
            className="rounded-3xl border border-slate-100 bg-slate-50 p-4"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-lg font-semibold text-slate-900">
                {interview.witness_name}
              </h3>
              {interview.id && onEditInterview ? (
                <button
                  aria-label={`Edit ${interview.witness_name}`}
                  className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-semibold text-slate-700"
                  onClick={() => onEditInterview(interview)}
                  type="button"
                >
                  Edit
                </button>
              ) : null}
            </div>
            <dl className="mt-4 grid gap-3">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Remark
                </dt>
                <dd className="mt-1 text-sm leading-6 text-slate-700">
                  {interview.conclusion_notes || 'No remark added.'}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Witness statement
                </dt>
                <dd className="mt-1 text-sm leading-6 text-slate-700">
                  {interview.witness_signature ? (
                    String(interview.witness_signature).startsWith(
                      'data:image/'
                    ) ? (
                      <img
                        alt={`${interview.witness_name} witness statement`}
                        className="max-h-24 rounded-2xl border border-slate-200 bg-white object-contain p-2"
                        src={interview.witness_signature}
                      />
                    ) : (
                      'Witness statement uploaded.'
                    )
                  ) : (
                    'No witness statement uploaded.'
                  )}
                </dd>
              </div>
            </dl>
          </article>
        ))
      ) : (
        <p className="text-sm text-slate-500">
          No witness statements added yet.
        </p>
      )}
    </section>
  );
}

export default SafetyInterviewModule;
