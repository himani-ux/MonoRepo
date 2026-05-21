import { Link } from "react-router-dom";

export interface SafetyScmAutoFeedFinding {
  area_id: number;
  carried_forward_count: number;
  checklist_unique_id: string | null;
  finding_id: number;
  inspection_id: number;
  inspection_reference: string;
  priority: string;
  severity: string;
  source_route: string;
  status: string;
  title: string;
}

export interface SafetyScmAutoFeedPayload {
  carried_forward_findings: SafetyScmAutoFeedFinding[];
  new_findings: SafetyScmAutoFeedFinding[];
  section8: {
    answer: "YES" | "NO";
    applicable_area_count: number;
    coverage_percent: number;
    inspected_area_count: number;
    inspection_count: number;
    summary_text: string;
  };
  summary: {
    carried_forward_count: number;
    new_count: number;
    total_count: number;
  };
}

export const safetyScmAutoFeedDemo: SafetyScmAutoFeedPayload = {
  carried_forward_findings: [
    {
      area_id: 3,
      carried_forward_count: 2,
      checklist_unique_id: "SOI-0000007-20260503-0013",
      finding_id: 301,
      inspection_id: 42,
      inspection_reference: "SOI/ABC/26/13",
      priority: "HIGH",
      severity: "HIGH",
      source_route: "/safety/soi/42/findings",
      status: "CARRIED_FORWARD",
      title: "Repeated enclosed-space permit toolbox-talk gap",
    },
  ],
  new_findings: [
    {
      area_id: 1,
      carried_forward_count: 0,
      checklist_unique_id: "SOI-0000007-20260504-0014",
      finding_id: 302,
      inspection_id: 43,
      inspection_reference: "SOI/ABC/26/14",
      priority: "MED",
      severity: "MED",
      source_route: "/safety/soi/43/findings",
      status: "OPEN",
      title: "Fresh mooring winch guard non-conformity",
    },
    {
      area_id: 5,
      carried_forward_count: 0,
      checklist_unique_id: "SOI-0000007-20260505-0015",
      finding_id: 303,
      inspection_id: 44,
      inspection_reference: "SOI/ABC/26/15",
      priority: "LOW",
      severity: "LOW",
      source_route: "/safety/soi/44/findings",
      status: "OPEN",
      title: "New galley chemical labelling observation",
    },
  ],
  section8: {
    answer: "YES",
    applicable_area_count: 12,
    coverage_percent: 41.7,
    inspected_area_count: 5,
    inspection_count: 2,
    summary_text:
      "Yes - 2 SOI inspection(s) recorded since the prior SCM covering 41.7% of applicable areas.",
  },
  summary: {
    carried_forward_count: 1,
    new_count: 2,
    total_count: 3,
  },
};

interface SafetyScmAutoFeedProps {
  payload: SafetyScmAutoFeedPayload;
}

function normalizeSoiRecordRoute(row: SafetyScmAutoFeedFinding) {
  const route = (row.source_route || "").trim();
  if (/^\/safety\/soi\/\d+\/?$/.test(route)) {
    return `${route.replace(/\/$/, "")}/findings`;
  }
  if (route) {
    return route;
  }
  return `/safety/soi/${row.public_inspection_id ?? row.inspection_id}/findings`;
}

export default function SafetyScmAutoFeed({ payload }: SafetyScmAutoFeedProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">SOI findings for this SCM</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Open SOI findings for this vessel are grouped for committee review. New
            findings are shown separately from items already carried forward.
          </p>
        </div>
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
            Section 8 auto-answer
          </div>
          <div className="mt-2 text-2xl font-semibold">{payload.section8.answer}</div>
          <div className="mt-1 text-xs text-emerald-800">{payload.section8.summary_text}</div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="New findings" value={payload.summary.new_count} />
        <SummaryCard label="Carried forward" value={payload.summary.carried_forward_count} />
        <SummaryCard label="SOI events" value={payload.section8.inspection_count} />
        <SummaryCard
          label="Coverage %"
          value={`${payload.section8.coverage_percent}%`}
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <FeedTable
          emptyMessage="No new open SOI findings since the previous SCM."
          rows={payload.new_findings}
          title="New SOI findings since last SCM"
          tone="bg-sky-50 text-sky-700"
        />
        <FeedTable
          emptyMessage="No carried-forward SOI findings waiting for this SCM."
          rows={payload.carried_forward_findings}
          title="Carried-forward SOI findings"
          tone="bg-amber-50 text-amber-700"
        />
      </div>
    </section>
  );
}

function FeedTable({
  emptyMessage,
  rows,
  title,
  tone,
}: {
  emptyMessage: string;
  rows: SafetyScmAutoFeedFinding[];
  title: string;
  tone: string;
}) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${tone}`}>
          {rows.length} item{rows.length === 1 ? "" : "s"}
        </span>
      </div>

      {rows.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
          {emptyMessage}
        </div>
      ) : (
        <div className="overflow-hidden rounded-3xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">SOI ref</th>
                <th className="px-4 py-3 font-medium">Finding</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {rows.map((row) => (
                <tr key={row.finding_id}>
                  <td className="px-4 py-4 text-slate-700">
                    <div className="font-medium text-slate-900">{row.inspection_reference}</div>
                    {row.checklist_unique_id ? (
                      <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                        UID {row.checklist_unique_id}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-4 py-4 text-slate-700">
                    <div className="font-medium text-slate-900">{row.title}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                      {row.severity} severity / {row.priority} priority
                    </div>
                    <Link
                      className="mt-2 inline-flex text-xs font-medium text-slate-700 underline decoration-slate-300 underline-offset-4"
                      to={normalizeSoiRecordRoute(row)}
                    >
                      Open SOI record
                    </Link>
                  </td>
                  <td className="px-4 py-4 text-slate-700">
                    <div className="font-medium text-slate-900">{row.status}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      Carry count {row.carried_forward_count}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: number | string }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </article>
  );
}
