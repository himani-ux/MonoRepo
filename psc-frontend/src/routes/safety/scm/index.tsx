import { useState } from "react";
import { Link } from "react-router-dom";

import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import { useSafetyScmMeetings } from "../../../hooks/use-safety";
import { getErrorMessage } from "../../../lib/api/client";
import { formatScmState } from "../../../lib/safety/scm-status";

function formatDate(value: string | null) {
  if (!value) {
    return "Not recorded";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function isRole(role: string | null, ...values: string[]) {
  const normalizedRole = (role ?? "").trim().toUpperCase();
  return values.some((value) => normalizedRole === value);
}

export default function SafetyScmIndexRoute() {
  const auth = useSafetyAuth();
  const canHostScm = auth.hasProcess("SAF_P_001") && isRole(auth.role, "CO", "MASTER");
  const [hostMeetingType, setHostMeetingType] = useState<"REGULAR" | "AD_HOC">("REGULAR");
  const [meetingType, setMeetingType] = useState("");
  const [state, setState] = useState("");
  const meetingsQuery = useSafetyScmMeetings({
    meeting_type: meetingType || undefined,
    state: state || undefined,
    vessel_id: auth.isGlobal ? undefined : auth.vesselIds[0],
  });

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#ecfccb_0%,#ffffff_55%,#dbeafe_100%)] p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Safety / SCM
            </p>
            <h1 className="text-3xl font-semibold text-slate-900">
              Safety Committee Meetings
            </h1>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            <div>Scoped vessels: {auth.scopedVesselLabel}</div>
            <div>Role: {auth.role ?? "Unknown"}</div>
          </div>
        </div>
        {canHostScm ? (
          <div className="flex flex-wrap items-end gap-3">
            <label className="space-y-1 text-sm text-slate-700">
              <span className="font-medium">Meeting to host</span>
              <select
                aria-label="Meeting type to host"
                className="min-h-[40px] rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
                onChange={(event) => setHostMeetingType(event.target.value as "REGULAR" | "AD_HOC")}
                value={hostMeetingType}
              >
                <option value="REGULAR">Regular SCM</option>
                <option value="AD_HOC">Ad-Hoc SCM</option>
              </select>
            </label>
            <Link
              className="inline-flex min-h-[40px] items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
              to={hostMeetingType === "AD_HOC" ? "/safety/scm/create-adhoc" : "/safety/scm/create-regular"}
            >
              Host meeting
            </Link>
          </div>
        ) : null}
      </header>

      <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Meeting register</h2>
            </div>
            <div className="flex flex-wrap gap-3">
              <select
                aria-label="SCM meeting type filter"
                className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900"
                onChange={(event) => setMeetingType(event.target.value)}
                value={meetingType}
              >
                <option value="">All meeting types</option>
                <option value="REGULAR">Regular</option>
                <option value="AD_HOC">Ad-Hoc</option>
              </select>
              <select
                aria-label="SCM state filter"
                className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900"
                onChange={(event) => setState(event.target.value)}
                value={state}
              >
                <option value="">All states</option>
                <option value="DRAFT">Draft</option>
                <option value="SUBMITTED">Submitted to Office</option>
                <option value="SIGNED_OFF">Signed Off</option>
                <option value="REOPENED">Reopened</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>

          {meetingsQuery.isLoading ? (
            <div className="mt-5 space-y-3" role="status">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-16 animate-pulse rounded-2xl bg-slate-100" />
              ))}
            </div>
          ) : meetingsQuery.error ? (
            <div className="mt-5 rounded-3xl border border-rose-200 bg-rose-50 px-4 py-5 text-sm text-rose-700">
              {getErrorMessage(meetingsQuery.error)}
            </div>
          ) : meetingsQuery.data && meetingsQuery.data.length > 0 ? (
            <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">SCM No</th>
                    <th className="px-4 py-3 font-medium">Type</th>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Chair</th>
                    <th className="px-4 py-3 font-medium">State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {meetingsQuery.data.map((meeting) => (
                    <tr key={meeting.id}>
                      <td className="px-4 py-4 text-slate-900">
                        <Link
                          className="font-medium hover:text-slate-600 hover:underline"
                          to={`/safety/scm/${meeting.id}`}
                        >
                          {meeting.scm_number || `SCM #${meeting.id}`}
                        </Link>
                        <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                          {(meeting.sections ?? []).length} section(s)
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                          {meeting.meeting_type}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-slate-600">{formatDate(meeting.meeting_date)}</td>
                      <td className="px-4 py-4 text-slate-600">{meeting.chair_crew_id || "-"}</td>
                      <td className="px-4 py-4 text-slate-600">{formatScmState(meeting.state)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600">
              No SCM meetings matched the current filter.
            </div>
          )}
        </article>

        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Monthly Meeting Status</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            {(meetingsQuery.data ?? []).slice(0, 3).map((meeting) => (
              <li key={meeting.id} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                <div className="font-medium text-slate-900">
                  Meeting on {formatDate(meeting.meeting_date)}
                </div>
                <div className="mt-1">{meeting.cadence_warning?.message || "No monthly meeting warning."}</div>
              </li>
            ))}
            {!meetingsQuery.isLoading && !meetingsQuery.error && (meetingsQuery.data?.length ?? 0) === 0 ? (
              <li className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3">
                No meetings available in the current scope.
              </li>
            ) : null}
          </ul>
        </article>
      </section>
    </section>
  );
}
