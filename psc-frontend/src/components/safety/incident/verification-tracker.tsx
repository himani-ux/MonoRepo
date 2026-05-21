import SafetyDeadlinePauseBanner from "./deadline-pause-banner";
import type { SafetyPhase8WorkspacePayload } from "../../../schemas/safety/incident-phase8";

interface SafetyVerificationTrackerProps {
  workspace: SafetyPhase8WorkspacePayload;
}

export default function SafetyVerificationTracker({
  workspace,
}: SafetyVerificationTrackerProps) {
  return (
    <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-900">
          Phase 8 Follow-up Verification
        </h1>
        <p className="text-sm text-slate-600">
          Recommendation effectiveness is tracked here while physical verification stays on its
          separate Inspection-module path.
        </p>
      </div>

      <SafetyDeadlinePauseBanner status={workspace.deadline_pause} />

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Corrective Actions
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">
            {workspace.corrective_actions_summary.closed}/{workspace.corrective_actions_summary.total}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Closed actions. Open, in-progress, and pending-verify actions still block closure.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Physical Verification
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">
            {workspace.physical_verification.done}/{workspace.physical_verification.done + workspace.physical_verification.pending}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Separate track. Incident closure is not blocked by outstanding PSC-style physical
            verification here.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            PIC Retention
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {workspace.pic_retention.retained_pic_user_id ?? "Not assigned"}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            {workspace.pic_retention.retained
              ? "Original PIC retained for YELLOW continuity."
              : "Standard reassignment rules apply."}
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Recommendation</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Tier</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Action</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Verification</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {workspace.recommendations.map((recommendation) => (
              <tr key={recommendation.id}>
                <td className="px-4 py-3 font-medium text-slate-900">{recommendation.title}</td>
                <td className="px-4 py-3 text-slate-700">{recommendation.tier}</td>
                <td className="px-4 py-3 text-slate-700">
                  {recommendation.action_completed ? "Completed" : "Open"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {recommendation.latest_verification ? (
                    recommendation.latest_verification.is_effective ? "Effective" : "Ineffective"
                  ) : (
                    "Pending"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm font-medium text-slate-900">
          {workspace.ready_for_close
            ? "Ready for incident closure."
            : "Closure is blocked until every recommendation has a completed verification or explicit deferral."}
        </p>
        {workspace.blockers.length > 0 ? (
          <p className="mt-1 text-sm text-slate-600">
            Active blockers: {workspace.blockers.join(", ")}
          </p>
        ) : null}
      </div>
    </section>
  );
}
