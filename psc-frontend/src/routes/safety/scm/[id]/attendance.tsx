import SafetyAttendanceTable, {
  type SafetyScmAttendanceRow,
} from "../../../../components/safety/scm/attendance-table";
import SafetyWrhUnavailableWarning from "../../../../components/safety/scm/wrh-unavailable-warning";
import { useSafetyScmAttendance } from "../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../lib/api/client";
import { useParams } from "react-router-dom";

function formatRestHours(value: number | string | null) {
  if (value === null) {
    return "Unavailable";
  }

  const normalized = typeof value === "number" ? value : Number(value);
  return Number.isFinite(normalized) ? `${normalized.toFixed(1)} h` : "Unavailable";
}

function formatTimezoneOffset(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "Unavailable";
  }

  const normalized = Number(value);
  if (!Number.isFinite(normalized)) {
    return "Unavailable";
  }

  const sign = normalized >= 0 ? "+" : "-";
  const absoluteMinutes = Math.abs(normalized);
  const hours = Math.trunc(absoluteMinutes / 60);
  const minutes = absoluteMinutes % 60;

  if (minutes === 0) {
    return `UTC ${sign} ${hours} hr${hours === 1 ? "" : "s"}`;
  }

  return `UTC ${sign} ${hours} hr${hours === 1 ? "" : "s"} ${minutes} min`;
}

export default function SafetyScmAttendanceRoute() {
  const params = useParams();
  const meetingId = params.id ?? "";
  const enabled = Boolean(meetingId);
  const query = useSafetyScmAttendance(meetingId, enabled);

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SCM meeting id.
      </section>
    );
  }

  if (query.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SCM attendance...
      </section>
    );
  }

  if (query.isError) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(query.error)}
      </section>
    );
  }

  const rows: SafetyScmAttendanceRow[] = query.data.rows.map((row) => ({
    crewId: row.crew_id,
    displayName: row.display_name,
    present: row.present,
    rankName: row.rank_name,
    wrhFlag: row.wrh_flag,
    wrhRest24h: formatRestHours(row.wrh_rest_hours_24h),
    wrhRest7d: formatRestHours(row.wrh_rest_hours_7d),
  }));

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f0fdf4_0%,#ffffff_55%,#eff6ff_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / SCM
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">SCM Attendance</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          WRH attendance snapshots and warning-only exceptions are now read from the live meeting payload.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Meeting date
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">{query.data.meeting_date}</p>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Ship time
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {formatTimezoneOffset(query.data.timezone_offset_minutes)}
          </p>
        </article>
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Contract
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">Warn, don&apos;t block</p>
        </article>
      </section>

      <section className="space-y-3">
        {query.data.warnings.map((warning) => (
          <SafetyWrhUnavailableWarning key={warning} message={warning} />
        ))}
      </section>

      <SafetyAttendanceTable rows={rows} />
    </section>
  );
}
