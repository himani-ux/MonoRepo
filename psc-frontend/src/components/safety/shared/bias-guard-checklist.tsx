import type { SafetyBiasGuard } from "../../../schemas/safety/incident-phase5";

interface SafetyBiasGuardChecklistProps {
  guards: SafetyBiasGuard[];
}

const stateTone: Record<SafetyBiasGuard["evaluation_state"], string> = {
  UNCHECKED: "border-slate-200 bg-slate-50 text-slate-700",
  PASSED: "border-emerald-200 bg-emerald-50 text-emerald-700",
  WARNED: "border-amber-200 bg-amber-50 text-amber-800",
  BLOCKED: "border-rose-300 bg-rose-50 text-rose-800",
  OVERRIDE: "border-sky-200 bg-sky-50 text-sky-800",
  JUSTIFIED: "border-slate-300 bg-slate-100 text-slate-700",
  SOFTWARN_OVERRIDE: "border-amber-300 bg-amber-100 text-amber-900",
};

export function SafetyBiasGuardChecklist({
  guards,
}: SafetyBiasGuardChecklistProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Review checks
          </p>
          <h2 className="text-xl font-semibold text-slate-900">Review Checks</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {guards.filter((guard) => guard.acknowledged).length}/{guards.length} acknowledged
        </div>
      </div>
      <div className="mt-4 space-y-3">
        {guards.map((guard) => (
          <article
            key={guard.guard_code}
            className={`rounded-2xl border p-4 ${stateTone[guard.evaluation_state]}`}
          >
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em]">
                  Check {guard.bit_position + 1}
                </p>
                <h3 className="mt-1 text-sm font-semibold">{guard.guard_name}</h3>
              </div>
              <span className="rounded-full border border-current/20 bg-white/70 px-3 py-1 text-[11px] font-semibold uppercase">
                {guard.evaluation_state.replaceAll("_", " ")}
              </span>
            </div>
            <p className="mt-2 text-xs uppercase tracking-[0.16em] text-current/80">
              {guard.family}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default SafetyBiasGuardChecklist;
