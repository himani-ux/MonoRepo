import { Link } from "react-router-dom";

import SafetyRepeatFindingBadge from "../soi/repeat-finding-badge";
import type { SafetySoiDigitalSignatureSnapshot, SafetySoiRepeatFindingSnapshot } from "../../../schemas/safety/soi-finding";

export interface SafetySoiFindingRowItem {
  actionLabel?: string;
  area_id: number;
  area_name: string;
  assigned_crew_id: string | null;
  description: string;
  due_date: string | null;
  id: number;
  inspection_id?: number;
  master_approval_state?: string | null;
  master_counter_signature?: SafetySoiDigitalSignatureSnapshot | null;
  pending_closure_signature?: SafetySoiDigitalSignatureSnapshot | null;
  photo_attachment_path: string | null;
  priority: "HIGH" | "MED" | "LOW";
  repeat?: SafetySoiRepeatFindingSnapshot;
  severity: "HIGH" | "MED" | "LOW";
  status: string;
  title: string;
}

function severityClasses(severity: SafetySoiFindingRowItem["severity"]) {
  switch (severity) {
    case "HIGH":
      return "bg-rose-100 text-rose-800";
    case "MED":
      return "bg-amber-100 text-amber-800";
    default:
      return "bg-emerald-100 text-emerald-800";
  }
}

export default function SafetySoiFindingRow({
  finding,
}: {
  finding: SafetySoiFindingRowItem;
}) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm [touch-action:pan-y]">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">{finding.title}</h3>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${severityClasses(finding.severity)}`}>
              {finding.severity} severity
            </span>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
              {finding.status}
            </span>
            <SafetyRepeatFindingBadge
              badgeText={finding.repeat?.badge_text}
              occurrenceCount={finding.repeat?.occurrence_count}
            />
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">{finding.description}</p>
          {finding.pending_closure_signature ? (
            <p className="mt-2 text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
              Pending closure signed by {finding.pending_closure_signature.signer_display_name}
            </p>
          ) : null}
          {finding.master_approval_state ? (
            <p className="mt-1 text-xs font-medium uppercase tracking-[0.14em] text-emerald-700">
              {finding.master_approval_state}
            </p>
          ) : null}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Area</div>
          <div className="mt-2 font-medium text-slate-900">
            {finding.area_id} - {finding.area_name}
          </div>
          <div className="mt-2 text-slate-600">
            Owner: {finding.assigned_crew_id ?? "Defaults to Safety Officer"}
          </div>
          <div className="text-slate-600">Priority: {finding.priority}</div>
          <div className="text-slate-600">Due: {finding.due_date ?? "Not yet set"}</div>
          <div className="text-slate-600">
            Photo: {finding.photo_attachment_path ? "Attached" : "Not attached"}
          </div>
          {finding.inspection_id ? (
            <Link
              className="mt-3 inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-800 transition hover:border-slate-400 hover:bg-slate-100"
              to={`/safety/soi/${finding.inspection_id}/findings/${finding.id}`}
            >
              {finding.actionLabel ?? "Open closure"}
            </Link>
          ) : null}
        </div>
      </div>
    </article>
  );
}
