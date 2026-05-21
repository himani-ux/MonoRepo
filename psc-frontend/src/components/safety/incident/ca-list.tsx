import SafetyPurchaseReqLinker from "./purchase-req-linker";
import type { SafetyCorrectiveAction } from "../../../schemas/safety/corrective-action";

interface SafetyCaListProps {
  actions: SafetyCorrectiveAction[];
}

function resolveOwnerLabel(action: SafetyCorrectiveAction) {
  if (action.assigned_crew_id) {
    return `Crew ${action.assigned_crew_id}`;
  }
  if (action.assigned_office_user_id) {
    return `Office ${action.assigned_office_user_id}`;
  }
  return "Unassigned";
}

export default function SafetyCaList({ actions }: SafetyCaListProps) {
  return (
    <div className="space-y-4">
      {actions.map((action) => (
        <article
          key={action.id}
          className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-white">
                  {action.status.replaceAll("_", " ")}
                </span>
                <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
                  Aging {action.aging_bucket}
                </span>
                {action.physical_verification_done ? (
                  <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
                    Physical verification logged
                  </span>
                ) : null}
              </div>
              <h2 className="text-xl font-semibold text-slate-900">
                {action.title}
              </h2>
              <p className="text-sm leading-6 text-slate-600">
                {action.description}
              </p>
            </div>
            <div className="grid gap-3 text-sm text-slate-600 sm:grid-cols-3 lg:min-w-[360px]">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Owner
                </p>
                <p className="mt-1 text-slate-900">{resolveOwnerLabel(action)}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Due Date
                </p>
                <p className="mt-1 text-slate-900">{action.due_date ?? "Pending"}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
                  Verifier
                </p>
                <p className="mt-1 text-slate-900">
                  {action.verifier_user_id ?? "Pending assignment"}
                </p>
              </div>
            </div>
          </div>
          <div className="mt-4">
            <SafetyPurchaseReqLinker action={action} />
          </div>
        </article>
      ))}
    </div>
  );
}
