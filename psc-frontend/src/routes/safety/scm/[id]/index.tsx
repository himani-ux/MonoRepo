import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import SafetyClosedSinceLastBlock from "../../../../components/safety/scm/closed-since-last-block";
import SafetyScmAutoFeed from "../../../../components/safety/scm/soi-findings-auto-feed";
import SafetyFloatingFeedback from "../../../../components/safety/shared/safety-floating-feedback";
import { useSafetyAuth } from "../../../../hooks/safety/use-auth";
import {
  safetyKeys,
  useSafetyScmAgenda,
  useSafetyScmAttendance,
  useSafetyScmAutoFeed,
  useSafetyScmClosedSinceLast,
  useSafetyScmMeeting,
} from "../../../../hooks/use-safety";
import { safetyApi, type SafetyScmSection } from "../../../../lib/api/safety";
import { getErrorMessage } from "../../../../lib/api/client";
import { formatScmState } from "../../../../lib/safety/scm-status";

function DetailCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-lg font-semibold text-slate-900">{value}</p>
    </article>
  );
}

function isRole(role: string | null, ...values: string[]) {
  const normalizedRole = (role ?? "").trim().toUpperCase();
  return values.some((value) => normalizedRole === value);
}

const MARINE_SUPERINTENDENT_PROFILE_ID = "407ef017-0f1c-ef11-a9f1-f348983bae6b";

function hasMarineSuperintendentProfile(profileId?: string | null) {
  return String(profileId ?? "").trim().toLowerCase() === MARINE_SUPERINTENDENT_PROFILE_ID;
}

function downloadBlob({ blob, fileName }: { blob: Blob; fileName: string }) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "Not recorded";
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString();
}

function formatRestHours(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const numericValue = Number(value);
  return Number.isNaN(numericValue) ? String(value) : numericValue.toFixed(2);
}

function formatTimezoneOffset(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "Unavailable";
  }

  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) {
    return "Unavailable";
  }

  const sign = numericValue >= 0 ? "+" : "-";
  const absoluteMinutes = Math.abs(numericValue);
  const hours = Math.trunc(absoluteMinutes / 60);
  const minutes = absoluteMinutes % 60;

  if (minutes === 0) {
    return `UTC ${sign} ${hours} hr${hours === 1 ? "" : "s"}`;
  }

  return `UTC ${sign} ${hours} hr${hours === 1 ? "" : "s"} ${minutes} min`;
}

function formatLegacyValue(value: string | number | boolean | null | undefined, fieldType?: string) {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  if (fieldType === "BOOLEAN") {
    if (String(value).trim().toUpperCase() === "N/A") {
      return "N/A";
    }
    return value === true || String(value).toLowerCase() === "true" ? "Yes" : "No";
  }
  return String(value);
}

function formatDiscussionStatus(value: string | number | boolean | null | undefined) {
  const normalized = String(value ?? "").trim().toUpperCase();
  if (normalized === "DISCUSSED") {
    return "Discussed";
  }
  if (normalized === "NOT_DISCUSSED") {
    return "Not discussed";
  }
  return String(value ?? "");
}

function parseDiscussionRows(value: unknown) {
  const rawValue = String(value ?? "").trim();
  if (!rawValue || !rawValue.startsWith("[")) {
    return [];
  }
  try {
    const parsed = JSON.parse(rawValue);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed
      .filter((row) => row && typeof row === "object")
      .map((row) => ({
        reason: String(row.reason ?? ""),
        reference: String(row.reference ?? row.incidentNumber ?? row.incident_number ?? row.srNo ?? row.sr_no ?? ""),
        status: String(row.status ?? ""),
        title: String(row.title ?? ""),
      }))
      .filter((row) => row.reference || row.title || row.status || row.reason);
  } catch {
    return [];
  }
}

const hiddenLegacyFields = new Set([
  "circular_discussion_status",
  "circular_not_discussed_reason",
  "near_miss_discussion_status",
  "near_miss_not_discussed_reason",
]);

type ScmSectionTabKey = number | "office-review";

function SectionContent({ section }: { section: SafetyScmSection }) {
  const legacyRows = (section.legacy_field_meta ?? [])
    .filter((field) => !hiddenLegacyFields.has(field.field_key))
    .map((field) => ({
      label: field.field_label,
      value: formatLegacyValue(section.legacy_fields?.[field.field_key], field.field_type),
    }))
    .filter((row) => row.value.trim());
  const circularRows = parseDiscussionRows(section.legacy_fields?.circular_discussion_status);
  const nearMissRows = parseDiscussionRows(section.legacy_fields?.near_miss_discussion_status);

  if (legacyRows.length === 0 && circularRows.length === 0 && nearMissRows.length === 0) {
    return (
      <p className="mt-3 text-sm leading-6 text-slate-600">
        {section.content.trim() || "No discussion notes recorded for this section yet."}
      </p>
    );
  }

  return (
    <div className="mt-4 space-y-4">
      {legacyRows.length > 0 ? (
        <dl className="grid gap-3">
          {legacyRows.map((row) => (
            <div className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3" key={row.label}>
              <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                {row.label}
              </dt>
              <dd className="mt-1 whitespace-pre-wrap text-sm leading-6 text-slate-800">
                {row.value}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
      <DiscussionTable rows={nearMissRows} title="Near miss discussion" />
      <DiscussionTable rows={circularRows} title="Circular / safety alert discussion" />
    </div>
  );
}

function DiscussionTable({
  rows,
  title,
}: {
  rows: Array<{ reason: string; reference: string; status: string; title: string }>;
  title: string;
}) {
  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200">
      <div className="bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-900">{title}</div>
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-white text-left text-slate-600">
          <tr>
            <th className="px-4 py-3 font-medium">Reference</th>
            <th className="px-4 py-3 font-medium">Title</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Reason</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, index) => (
            <tr key={`${row.reference}-${row.title}-${index}`}>
              <td className="px-4 py-3 font-medium text-slate-900">{row.reference || "-"}</td>
              <td className="px-4 py-3 text-slate-700">{row.title || "-"}</td>
              <td className="px-4 py-3 text-slate-700">{formatDiscussionStatus(row.status) || "-"}</td>
              <td className="px-4 py-3 text-slate-700">{row.reason || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function SafetyScmDetailRoute() {
  const params = useParams();
  const auth = useSafetyAuth();
  const queryClient = useQueryClient();
  const meetingId = params.id ?? "";
  const enabled = Boolean(meetingId);
  const canManageScm = isRole(auth.role, "CO", "MASTER");
  const [pdfPending, setPdfPending] = useState(false);
  const [pdfError, setPdfError] = useState<unknown>(null);
  const [officeCommentDraft, setOfficeCommentDraft] = useState("");
  const [officeReviewPending, setOfficeReviewPending] = useState(false);
  const [officeReviewError, setOfficeReviewError] = useState<unknown>(null);
  const [officeReviewSaved, setOfficeReviewSaved] = useState(false);
  const [activeSectionKey, setActiveSectionKey] = useState<ScmSectionTabKey | null>(null);
  const [showAttendanceRows, setShowAttendanceRows] = useState(false);

  const meetingQuery = useSafetyScmMeeting(meetingId, enabled);
  const agendaQuery = useSafetyScmAgenda(meetingId, enabled);
  const attendanceQuery = useSafetyScmAttendance(meetingId, enabled);
  const closedQuery = useSafetyScmClosedSinceLast(meetingId, enabled);
  const autoFeedQuery = useSafetyScmAutoFeed(meetingId, enabled);

  useEffect(() => {
    const meeting = meetingQuery.data;
    if (!meeting) {
      return;
    }
    const existingComment = meeting.office_comment ?? "";
    setOfficeCommentDraft(existingComment);
    setOfficeReviewSaved(false);
    setOfficeReviewError(null);
  }, [
    meetingQuery.data?.id,
    meetingQuery.data?.office_comment,
    meetingQuery.data?.office_comment_at,
  ]);

  async function handleDownloadPdf() {
    setPdfPending(true);
    setPdfError(null);
    try {
      downloadBlob(await safetyApi.downloadScmPdf(meetingId));
    } catch (error) {
      setPdfError(error);
    } finally {
      setPdfPending(false);
    }
  }

  async function handleOfficeReview() {
    setOfficeReviewPending(true);
    setOfficeReviewError(null);
    try {
      const updatedMeeting = await safetyApi.addScmOfficeReview(meetingId, {
        office_comment: officeCommentDraft.trim(),
        is_reviewed: true,
      });
      queryClient.setQueryData(safetyKeys.scmMeeting(meetingId), updatedMeeting);
      await queryClient.invalidateQueries({ queryKey: safetyKeys.scmMeeting(meetingId) });
      setOfficeReviewSaved(true);
    } catch (error) {
      setOfficeReviewError(error);
    } finally {
      setOfficeReviewPending(false);
    }
  }

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SCM meeting id.
      </section>
    );
  }

  if (
    meetingQuery.isLoading
    || agendaQuery.isLoading
    || closedQuery.isLoading
  ) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SCM detail...
      </section>
    );
  }

  if (meetingQuery.isError || agendaQuery.isError || closedQuery.isError) {
    const error = meetingQuery.error ?? agendaQuery.error ?? closedQuery.error;
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(error)}
      </section>
    );
  }

  const meeting = meetingQuery.data;
  const agenda = agendaQuery.data;
  const attendance = attendanceQuery.data;
  const closedSinceLast = closedQuery.data;
  const autoFeed = autoFeedQuery.data;
  const canOfficeReview =
    isRole(auth.role, "DPA", "FM", "HOD SHORE", "SHORE HOD")
    || hasMarineSuperintendentProfile(auth.user?.profileId);
  const officeReviewAvailable = meeting.state !== "CLOSED" && !meeting.office_comment_at;
  const officeReviewEditable = canOfficeReview && officeReviewAvailable;
  const canEditMeeting = canManageScm && !meeting.is_reviewed && !meeting.office_comment_at;
  const detailSections = (agenda?.rows ?? []).filter((section) => section.agenda_item_number !== 9);
  const firstSectionKey: ScmSectionTabKey = detailSections[0]?.agenda_item_number ?? "office-review";
  const selectedSectionKey: ScmSectionTabKey =
    activeSectionKey === "office-review"
    || detailSections.some((section) => section.agenda_item_number === activeSectionKey)
      ? activeSectionKey
      : firstSectionKey;
  const activeDetailSection =
    typeof selectedSectionKey === "number"
      ? detailSections.find((section) => section.agenda_item_number === selectedSectionKey) ?? null
      : null;
  const actionError = pdfError ?? officeReviewError;
  const actionSuccess = officeReviewSaved ? "Section 9 Office Review saved and meeting closed." : null;
  const attendanceRows = attendance?.rows ?? [];
  const presentCount = attendanceRows.filter((row) => row.present).length;
  const absentCount = attendanceRows.length - presentCount;
  const wrhUnavailableCount = attendanceRows.filter((row) => !row.wrh_data_available || row.wrh_flag === "RED").length;
  const wrhNonCompliantCount = attendanceRows.filter((row) => row.wrh_non_compliance_flag || row.wrh_flag === "YELLOW").length;
  const wrhClear = attendanceRows.length > 0 && wrhUnavailableCount === 0 && wrhNonCompliantCount === 0 && (attendance?.warnings.length ?? 0) === 0;
  const officeReviewSection = (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Section 9
          </p>
          <h2 className="mt-2 text-lg font-semibold text-slate-900">Office Comment</h2>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
          meeting.is_reviewed ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
        }`}>
          {meeting.is_reviewed ? "Reviewed" : "Pending office review"}
        </span>
      </div>

      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          Current Office Comments
        </p>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
          {meeting.office_comment?.trim() || "No office review recorded yet."}
        </p>
        {meeting.office_comment_at ? (
          <p className="mt-3 text-xs text-slate-500">
            Reviewed by {meeting.office_comment_by ?? "Not recorded"} Â· {formatDateTime(meeting.office_comment_at)}
          </p>
        ) : null}
      </div>

      {officeReviewEditable ? (
        <div className="mt-5 space-y-4">
          <label className="block">
            <span className="text-sm font-semibold text-slate-800">OFFICE COMMENTS</span>
            <textarea
              className="mt-2 min-h-[140px] w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm leading-6 outline-none focus:border-slate-400"
              onChange={(event) => {
                setOfficeCommentDraft(event.target.value);
                setOfficeReviewSaved(false);
              }}
              placeholder="Enter office review comments after checking meeting content, attendance, SOI items, findings, decisions, and PDF."
              value={officeCommentDraft}
            />
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <button
              className="min-h-[44px] rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={officeReviewPending || !officeCommentDraft.trim()}
              onClick={() => void handleOfficeReview()}
              type="button"
            >
              {officeReviewPending ? "Saving office review..." : "Save Section 9 Office Review"}
            </button>
          </div>
        </div>
      ) : (
        <p className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
          {officeReviewAvailable
            ? "Office review entry is restricted to DPA/FM/Shore HOD/Marine Superintendent users."
            : "Office review has been completed and the meeting is closed."}
        </p>
      )}
    </section>
  );

  return (
    <section className="space-y-6">
      {actionError ? <SafetyFloatingFeedback tone="error">{getErrorMessage(actionError)}</SafetyFloatingFeedback> : null}
      {actionSuccess ? <SafetyFloatingFeedback tone="success">{actionSuccess}</SafetyFloatingFeedback> : null}
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_55%,#fef9c3_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / SCM
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">SCM Detail</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Meeting record for the locked SCM structure with attendance,
          agenda, closed-since-last summary, and SOI findings.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-4">
        <DetailCard label="Meeting No" value={meeting.scm_number ?? `#${meeting.id}`} />
        <DetailCard label="Type" value={meeting.meeting_type} />
        <DetailCard label="Chair" value={meeting.chair_crew_id ?? "Not assigned"} />
        <DetailCard label="State" value={formatScmState(meeting.state)} />
      </section>

      <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">SCM PDF</h2>
            <p className="mt-2 text-sm leading-6 text-emerald-900">
              Download the current SCM PDF at any time after the meeting is created.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              className="inline-flex min-h-[44px] items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={pdfPending}
              onClick={() => void handleDownloadPdf()}
              type="button"
            >
              {pdfPending ? "Preparing PDF..." : "Download / Print PDF"}
            </button>
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Attendance + WRH snapshot</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {attendanceQuery.isLoading
                ? "Loading saved attendance and WRH status..."
                : attendanceQuery.isError
                  ? getErrorMessage(attendanceQuery.error)
                  : attendanceRows.length === 0
                    ? "No attendees recorded yet."
                    : wrhClear
                      ? "All saved attendance rows are WRH compliant."
                      : "WRH warnings are present in the saved attendance record."}
            </p>
          </div>
          {canManageScm ? (
            <Link
              className="inline-flex min-h-[44px] items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white"
              to={`/safety/scm/${meeting.id}/attendance`}
            >
              Open attendance
            </Link>
          ) : null}
        </div>
        {attendanceQuery.isSuccess ? (
          <div className="mt-5 space-y-4">
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
              <DetailCard label="Attendees" value={String(attendanceRows.length)} />
              <DetailCard label="Present" value={String(presentCount)} />
              <DetailCard label="Absent" value={String(absentCount)} />
              <DetailCard label="WRH data unavailable" value={String(wrhUnavailableCount)} />
              <DetailCard label="WRH warnings" value={String(wrhNonCompliantCount)} />
              <DetailCard
                label="Ship time"
                value={formatTimezoneOffset(attendance?.timezone_offset_minutes)}
              />
            </div>
            {attendanceRows.length > 0 ? (
              <div className="flex justify-end">
                <button
                  aria-expanded={showAttendanceRows}
                  className="inline-flex min-h-[40px] items-center gap-2 rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 shadow-sm transition hover:border-slate-400 hover:bg-slate-50"
                  onClick={() => setShowAttendanceRows((current) => !current)}
                  type="button"
                >
                  {showAttendanceRows ? "Hide sheet" : "Open sheet"}
                  <span
                    aria-hidden="true"
                    className="mt-[-2px] h-2 w-2 border-b-2 border-r-2 border-slate-600 transition"
                    style={{ transform: showAttendanceRows ? "rotate(225deg)" : "rotate(45deg)" }}
                  />
                </button>
              </div>
            ) : null}
            {attendanceRows.length > 0 && showAttendanceRows ? (
              <div className="overflow-hidden rounded-2xl border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-slate-600">
                    <tr>
                      <th className="px-4 py-3 font-medium">Crew</th>
                      <th className="px-4 py-3 font-medium">Attendance</th>
                      <th className="px-4 py-3 font-medium">WRH status</th>
                      <th className="px-4 py-3 font-medium">Rest hours</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {attendanceRows.map((row) => (
                      <tr key={row.crew_id}>
                        <td className="px-4 py-3">
                          <div className="font-medium text-slate-900">{row.display_name}</div>
                          <div className="mt-1 text-xs uppercase tracking-[0.14em] text-slate-500">{row.rank_name || "-"}</div>
                        </td>
                        <td className="px-4 py-3 text-slate-700">
                          {row.present ? "Present" : `Absent${row.absence_reason ? ` - ${row.absence_reason}` : ""}`}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            row.wrh_flag === "GREEN"
                              ? "bg-emerald-100 text-emerald-800"
                              : row.wrh_flag === "YELLOW"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-rose-100 text-rose-800"
                          }`}>
                            {row.wrh_flag === "GREEN"
                              ? "Compliant"
                              : row.wrh_flag === "YELLOW"
                                ? "Non-compliant"
                                : "WRH data unavailable"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-700">
                          24h {formatRestHours(row.wrh_rest_hours_24h)} / 7d {formatRestHours(row.wrh_rest_hours_7d)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
            {attendance?.warnings.length ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                {attendance.warnings.map((warning) => (
                  <p key={warning}>{warning}</p>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      <SafetyClosedSinceLastBlock payload={closedSinceLast} />
      {autoFeed ? <SafetyScmAutoFeed payload={autoFeed} /> : null}
      {autoFeedQuery.isError ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900 shadow-sm">
          SOI findings could not be loaded: {getErrorMessage(autoFeedQuery.error)}
        </section>
      ) : null}


      {canEditMeeting ? (
        <div className="flex justify-end">
          <Link
            className="inline-flex min-h-[44px] items-center rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700"
            to={`/safety/scm/${meeting.id}/edit`}
          >
            Edit Meeting
          </Link>
        </div>
      ) : null}

      <section className="space-y-4">
        <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-white p-3 shadow-sm">
          <div
            aria-label="SCM meeting sections"
            className="flex min-w-max gap-2"
            role="tablist"
          >
            {detailSections.map((section) => {
              const isSelected = selectedSectionKey === section.agenda_item_number;

              return (
                <button
                  aria-selected={isSelected}
                  className={`min-h-[56px] max-w-[260px] whitespace-nowrap rounded-2xl border px-4 py-2 text-left transition ${
                    isSelected
                      ? "border-slate-900 bg-slate-900 text-white shadow-sm"
                      : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                  }`}
                  key={section.agenda_item_number}
                  onClick={() => setActiveSectionKey(section.agenda_item_number)}
                  role="tab"
                  type="button"
                >
                  <span className={`block text-[11px] font-semibold uppercase tracking-[0.14em] ${
                    isSelected ? "text-slate-200" : "text-slate-500"
                  }`}>
                    Section {section.agenda_item_number}
                  </span>
                  <span className="block overflow-hidden text-ellipsis text-sm font-semibold">
                    {section.section_label}
                  </span>
                </button>
              );
            })}
            <button
              aria-selected={selectedSectionKey === "office-review"}
              className={`min-h-[56px] whitespace-nowrap rounded-2xl border px-4 py-2 text-left transition ${
                selectedSectionKey === "office-review"
                  ? "border-slate-900 bg-slate-900 text-white shadow-sm"
                  : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
              }`}
              onClick={() => setActiveSectionKey("office-review")}
              role="tab"
              type="button"
            >
              <span className={`block text-[11px] font-semibold uppercase tracking-[0.14em] ${
                selectedSectionKey === "office-review" ? "text-slate-200" : "text-slate-500"
              }`}>
                Section 9
              </span>
              <span className="block text-sm font-semibold">Office Comment</span>
            </button>
          </div>
        </div>

        {activeDetailSection ? (
          <article
            className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            role="tabpanel"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Section {activeDetailSection.agenda_item_number}
            </p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">
              {activeDetailSection.section_label}
            </h2>
            <SectionContent section={activeDetailSection} />
            {activeDetailSection.decision ? (
              <p className="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                Suggestions / Recommendations: {activeDetailSection.decision}
              </p>
            ) : null}
          </article>
        ) : (
          officeReviewSection
        )}
      </section>
    </section>
  );
}
