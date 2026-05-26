import { Link } from "react-router-dom";

export interface SafetyScmClosedSinceLastCutoff {
  closed_at: string;
  meeting_id: number;
  meeting_type: string;
  scm_number: string;
}

export interface SafetyScmClosedSinceLastItem {
  closed_at: string;
  item_type: "INCIDENT" | "NEAR_MISS" | "SOI_FINDING" | "CORRECTIVE_ACTION";
  reference: string;
  source_id: number;
  source_route: string | null;
  status: string;
  title: string;
  unique_id: string | null;
}

export interface SafetyScmClosedSinceLastPayload {
  cutoff: SafetyScmClosedSinceLastCutoff | null;
  empty_message: string | null;
  items: SafetyScmClosedSinceLastItem[];
  summary: {
    corrective_action_count: number;
    incident_count: number;
    near_miss_count: number;
    soi_finding_count: number;
    total_count: number;
  };
}

export const safetyScmClosedSinceLastDemo: SafetyScmClosedSinceLastPayload = {
  cutoff: {
    closed_at: "2026-04-01T10:00:00+05:30",
    meeting_id: 11,
    meeting_type: "REGULAR",
    scm_number: "ABC-01-Apr-2026",
  },
  empty_message: null,
  items: [
    {
      closed_at: "2026-04-20T08:30:00+05:30",
      item_type: "SOI_FINDING",
      reference: "SOI/ABC/26/01",
      source_id: 91,
      source_route: "/safety/soi/27/findings",
      status: "CLOSED",
      title: "Closed lifeboat drill follow-up",
      unique_id: "SOI-0000007-20260420-0001",
    },
    {
      closed_at: "2026-04-12T15:00:00+05:30",
      item_type: "CORRECTIVE_ACTION",
      reference: "CA-41",
      source_id: 41,
      source_route: "/safety/incidents/18/corrective-actions",
      status: "CLOSED",
      title: "Closed corrective action from April incident review",
      unique_id: null,
    },
    {
      closed_at: "2026-04-11T12:00:00+05:30",
      item_type: "NEAR_MISS",
      reference: "NM-001",
      source_id: 72,
      source_route: "/safety/near-miss/72",
      status: "CLOSED",
      title: "Near miss correspondence closed by DPA",
      unique_id: null,
    },
    {
      closed_at: "2026-04-10T09:00:00+05:30",
      item_type: "INCIDENT",
      reference: "INC-001",
      source_id: 18,
      source_route: "/safety/incidents/18",
      status: "CLOSED",
      title: "Engine-room incident closed after verification",
      unique_id: null,
    },
  ],
  summary: {
    corrective_action_count: 1,
    incident_count: 1,
    near_miss_count: 1,
    soi_finding_count: 1,
    total_count: 4,
  },
};

interface SafetyClosedSinceLastBlockProps {
  payload: SafetyScmClosedSinceLastPayload;
  title?: string;
}

const typeLabel: Record<SafetyScmClosedSinceLastItem["item_type"], string> = {
  CORRECTIVE_ACTION: "Corrective Action",
  INCIDENT: "Incident",
  NEAR_MISS: "Near Miss",
  SOI_FINDING: "SOI Finding",
};

const typeTone: Record<SafetyScmClosedSinceLastItem["item_type"], string> = {
  CORRECTIVE_ACTION: "bg-amber-50 text-amber-700",
  INCIDENT: "bg-rose-50 text-rose-700",
  NEAR_MISS: "bg-sky-50 text-sky-700",
  SOI_FINDING: "bg-emerald-50 text-emerald-700",
};

function normalizeSourceRoute(item: SafetyScmClosedSinceLastItem) {
  const route = (item.source_route || "").trim();
  if (item.item_type === "SOI_FINDING" && /^\/safety\/soi\/\d+\/?$/.test(route)) {
    return `${route.replace(/\/$/, "")}/findings`;
  }
  return route;
}

export default function SafetyClosedSinceLastBlock({
  payload,
  title = "Closed-Since-Last SCM Summary",
}: SafetyClosedSinceLastBlockProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            For-record visibility only. The snapshot anchors on the prior SCM Master
            sign-off, including Ad-Hoc meetings in the same cadence chain.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <div className="font-medium text-slate-900">Cutoff anchor</div>
          {payload.cutoff ? (
            <>
              <div className="mt-1">{payload.cutoff.scm_number}</div>
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                {payload.cutoff.meeting_type} sign-off
              </div>
              <div className="mt-2 text-xs text-slate-500">{payload.cutoff.closed_at}</div>
            </>
          ) : (
            <div className="mt-1 text-sm text-slate-500">No prior SCM.</div>
          )}
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <SummaryCard label="Total closed" value={payload.summary.total_count} />
        <SummaryCard label="Incidents" value={payload.summary.incident_count} />
        <SummaryCard label="Near miss" value={payload.summary.near_miss_count} />
        <SummaryCard label="SOI findings" value={payload.summary.soi_finding_count} />
        <SummaryCard label="Corrective actions" value={payload.summary.corrective_action_count} />
      </div>

      {payload.items.length === 0 ? (
        <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center text-sm text-slate-600">
          {payload.empty_message ?? "Nothing closed since last SCM."}
        </div>
      ) : (
        <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Reference</th>
                <th className="px-4 py-3 font-medium">Closed item</th>
                <th className="px-4 py-3 font-medium">Closed at</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {payload.items.map((item) => (
                <tr key={`${item.item_type}-${item.source_id}`}>
                  <td className="px-4 py-4">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium ${typeTone[item.item_type]}`}
                    >
                      {typeLabel[item.item_type]}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-slate-700">
                    <div className="font-medium text-slate-900">{item.reference}</div>
                    {item.unique_id ? (
                      <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                        UID {item.unique_id}
                      </div>
                    ) : null}
                  </td>
                  <td className="px-4 py-4 text-slate-700">
                    <div className="font-medium text-slate-900">{item.title}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                      {item.status}
                    </div>
                    {normalizeSourceRoute(item) ? (
                      <Link
                        className="mt-2 inline-flex text-xs font-medium text-slate-700 underline decoration-slate-300 underline-offset-4"
                        to={normalizeSourceRoute(item)}
                      >
                        Open source record
                      </Link>
                    ) : null}
                  </td>
                  <td className="px-4 py-4 text-slate-600">{item.closed_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </article>
  );
}
