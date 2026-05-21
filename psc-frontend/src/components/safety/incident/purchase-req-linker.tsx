import type { SafetyCorrectiveAction } from "../../../schemas/safety/corrective-action";

interface SafetyPurchaseReqLinkerProps {
  action: SafetyCorrectiveAction;
}

export default function SafetyPurchaseReqLinker({
  action,
}: SafetyPurchaseReqLinkerProps) {
  const href = action.purchase_req_id
    ? `/purchase/requisitions/${action.purchase_req_id}`
    : `/purchase/requisitions/create?linked_safety_ca=${action.id}`;

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        Purchase Link
      </p>
      <p className="mt-2 text-sm text-slate-700">
        {action.purchase_req_id
          ? `Linked Purchase Req ${action.purchase_req_id} keeps the hard-FK lifecycle visible from Safety.`
          : "Create the linked Purchase Req from the corrective-action row when parts or services are required."}
      </p>
      <a
        className="mt-3 inline-flex items-center rounded-full border border-slate-300 px-3 py-1 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-white"
        href={href}
      >
        {action.purchase_req_id ? "Open Purchase Req" : "Link Purchase Req"}
      </a>
    </div>
  );
}
