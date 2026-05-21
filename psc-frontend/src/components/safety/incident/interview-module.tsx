import type { SafetyWitnessInterview } from "../../../schemas/safety/incident-phase3";
import { SafetyWitnessReadback } from "./witness-readback";

interface SafetyInterviewModuleProps {
  interviews: SafetyWitnessInterview[];
}

export function SafetyInterviewModule({
  interviews,
}: SafetyInterviewModuleProps) {
  return (
    <section className="space-y-5 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            FEAT-SAF-INC-012 / 013
          </p>
          <h2 className="text-xl font-semibold text-slate-900">
            Structured 4-Phase Interview Module
          </h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {interviews.length} interviews
        </div>
      </div>

      {interviews.length > 0 ? (
        interviews.map((interview, index) => (
          <article
            key={interview.id ?? `${interview.witness_name}-${index}`}
            className="rounded-3xl border border-slate-100 bg-slate-50 p-4"
          >
            <div className="flex flex-wrap items-center gap-3">
              <h3 className="text-lg font-semibold text-slate-900">
                {interview.witness_name}
              </h3>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-600">
                {interview.interview_type}
              </span>
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600">
                {interview.phase_count} / 4 phases
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-700">
              {interview.meeting_notes || "Interview notes pending."}
            </p>
            <div className="mt-4">
              <SafetyWitnessReadback
                copyToWitnessRecorded={interview.copy_to_witness_recorded}
                readBackConfirmed={interview.read_back_confirmed}
                witnessSignature={interview.witness_signature}
              />
            </div>
          </article>
        ))
      ) : (
        <p className="text-sm text-slate-500">No witness interviews recorded yet.</p>
      )}
    </section>
  );
}

export default SafetyInterviewModule;
