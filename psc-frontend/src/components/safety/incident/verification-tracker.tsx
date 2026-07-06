import SafetyDeadlinePauseBanner from "./deadline-pause-banner";
import type { SafetyPhase8WorkspacePayload } from "../../../schemas/safety/incident-phase8";

interface SafetyVerificationTrackerProps {
  workspace: SafetyPhase8WorkspacePayload;
}

export default function SafetyVerificationTracker({
  workspace,
}: SafetyVerificationTrackerProps) {
  const deadlinePause = workspace.deadline_pause ?? {
    is_paused: false,
    last_actor_user_id: null,
    last_event_at: null,
    state: "RUNNING",
  };
  const correctiveSummary = workspace.corrective_actions_summary ?? {
    closed: 0,
    in_progress: 0,
    open: 0,
    pending_verify: 0,
    total: 0,
  };
  const physicalVerification = workspace.physical_verification ?? {
    done: 0,
    pending: 0,
    separate_track: true,
  };
  const picRetention = workspace.pic_retention ?? {
    replacement_access: "STANDARD",
    retained: false,
    retained_pic_user_id: null,
  };
  const recommendations = workspace.recommendations ?? [];

  return (
    <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <SafetyDeadlinePauseBanner status={deadlinePause} />

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Actions
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">
            {correctiveSummary.closed}/{correctiveSummary.total}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Open or unchecked actions still block closing.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Site Check
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">
            {physicalVerification.done}/{physicalVerification.done + physicalVerification.pending}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Site checks are tracked here when needed.
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            PIC
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {picRetention.retained_pic_user_id ?? "Not assigned"}
          </p>
          <p className="mt-1 text-sm text-slate-600">
            {picRetention.retained
              ? "Original PIC is still available."
              : "Standard reassignment rules apply."}
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Action</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Type</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Action</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Check</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {recommendations.map((recommendation) => (
              <tr key={recommendation.id}>
                <td className="px-4 py-3 font-medium text-slate-900">{recommendation.title}</td>
                <td className="px-4 py-3 text-slate-700">{recommendation.tier}</td>
                <td className="px-4 py-3 text-slate-700">
                  {recommendation.action_completed ? "Completed" : "Open"}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {recommendation.latest_verification ? (
                    recommendation.latest_verification.is_effective ? "Working" : "Not working"
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
            ? "Ready to close."
            : "Cannot close until every action is checked or deferred."}
        </p>
        {workspace.blockers.length > 0 ? (
          <p className="mt-1 text-sm text-slate-600">
            Still pending: {workspace.blockers.join(", ")}
          </p>
        ) : null}
      </div>
    </section>
  );
}
