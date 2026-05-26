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
  useSafetyScmAutoFeed,
  useSafetyScmClosedSinceLast,
  useSafetyScmMeeting,
} from "../../../../hooks/use-safety";
import { safetyApi, type SafetyScmSection } from "../../../../lib/api/safety";
import { getErrorMessage } from "../../../../lib/api/client";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../../lib/safety/digital-signature";

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
  const canSignOff = isRole(auth.role, "MASTER");
  const canManageScm = isRole(auth.role, "CO", "MASTER");
  const [finalizeName, setFinalizeName] = useState(() => resolveSignatureTypedName(auth.user));
  const [finalizeDevice] = useState(() => getSafetyDeviceFingerprint());
  const [finalizePending, setFinalizePending] = useState(false);
  const [finalizeError, setFinalizeError] = useState<unknown>(null);
  const [finalized, setFinalized] = useState(false);
  const [pdfPending, setPdfPending] = useState(false);
  const [pdfError, setPdfError] = useState<unknown>(null);
  const [officeCommentDraft, setOfficeCommentDraft] = useState("");
  const [officeReviewPending, setOfficeReviewPending] = useState(false);
  const [officeReviewError, setOfficeReviewError] = useState<unknown>(null);
  const [officeReviewSaved, setOfficeReviewSaved] = useState(false);

  const meetingQuery = useSafetyScmMeeting(meetingId, enabled);
  const agendaQuery = useSafetyScmAgenda(meetingId, enabled);
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

  async function handleFinalize() {
    setFinalizePending(true);
    setFinalizeError(null);
    try {
      await safetyApi.submitScmMeeting(meetingId, {
        typed_name: finalizeName,
        device_fingerprint: finalizeDevice,
      });
      setFinalized(true);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmMeeting(meetingId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmSignoffPreflight(meetingId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmMeetings({}) }),
      ]);
    } catch (error) {
      setFinalizeError(error);
    } finally {
      setFinalizePending(false);
    }
  }

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
    || autoFeedQuery.isLoading
  ) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SCM detail...
      </section>
    );
  }

  if (meetingQuery.isError || agendaQuery.isError || closedQuery.isError || autoFeedQuery.isError) {
    const error = meetingQuery.error ?? agendaQuery.error ?? closedQuery.error ?? autoFeedQuery.error;
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(error)}
      </section>
    );
  }

  const meeting = meetingQuery.data;
  const agenda = agendaQuery.data;
  const closedSinceLast = closedQuery.data;
  const autoFeed = autoFeedQuery.data;
  const canFinalize = meeting.state === "DRAFT" && canManageScm;
  const canOpenSignoff = canSignOff && ["SUBMITTED", "REOPENED", "SIGNED_OFF"].includes(meeting.state);
  const pdfIsSigned = meeting.state === "SIGNED_OFF" || Boolean(meeting.master_signed_off_at);
  const canOfficeReview = isRole(auth.role, "DPA", "FM", "HOD SHORE", "SHORE HOD");
  const officeReviewAvailable = meeting.state === "SIGNED_OFF" && Boolean(meeting.master_signed_off_at);
  const officeReviewEditable = canOfficeReview && officeReviewAvailable;
  const canEditMeeting = canManageScm && !meeting.is_reviewed && !meeting.office_comment_at;
  const detailSections = meeting.sections.filter((section) => section.agenda_item_number !== 9);
  const actionError = pdfError ?? finalizeError ?? officeReviewError;
  const actionSuccess = finalized
    ? "SCM finalized for Master sign-off."
    : officeReviewSaved
      ? "Section 9 Office Review saved."
      : null;
  const officeReviewSection = (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Section 9
          </p>
          <h2 className="mt-2 text-lg font-semibold text-slate-900">Office Review</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            OFFICECOMMENTS and IsReviewed are completed by DPA/FM/Shore HOD after Master sign-off.
          </p>
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
        <p className="mt-3 text-xs text-slate-500">
          Reviewed by {meeting.office_comment_by ?? "Not recorded"} Â· {formatDateTime(meeting.office_comment_at)}
        </p>
      </div>

      {officeReviewEditable ? (
        <div className="mt-5 space-y-4">
          <label className="block">
            <span className="text-sm font-semibold text-slate-800">OFFICECOMMENTS</span>
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
            ? "Office review entry is restricted to DPA/FM/Shore HOD users."
            : "Section 9 becomes editable after Master sign-off."}
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
        <DetailCard label="State" value={meeting.state} />
      </section>

      <section className={`rounded-3xl border p-5 shadow-sm ${
        pdfIsSigned ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"
      }`}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">SCM PDF</h2>
            <p className={`mt-2 text-sm leading-6 ${pdfIsSigned ? "text-emerald-900" : "text-amber-900"}`}>
              {pdfIsSigned
                ? "Master sign-off is complete. Download the signed SCM PDF for filing or printing."
                : meeting.state === "DRAFT"
                  ? "Signed PDF is created after the meeting host finalizes the meeting and Master completes sign-off."
                  : "Meeting is finalized for Master sign-off. Signed PDF will be available after Master signs."}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            {canOpenSignoff ? (
              <Link
                className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800"
                to={`/safety/scm/${meeting.id}/signoff`}
              >
                Master's closure for scm
              </Link>
            ) : null}
            {pdfIsSigned ? (
              <button
                className="inline-flex min-h-[44px] items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={pdfPending}
                onClick={() => void handleDownloadPdf()}
                type="button"
              >
                {pdfPending ? "Preparing PDF..." : "Download / Print Signed PDF"}
              </button>
            ) : null}
          </div>
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Attendance + WRH snapshot</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Attendance rows and WRH warnings come from the saved attendance record for this meeting.
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
      </section>

      {canFinalize ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Finalize for Sign-Off</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]">
            <input
              aria-label="Typed signature"
              className="min-h-[44px] rounded-2xl border border-slate-200 px-3 py-2"
              onChange={(event) => setFinalizeName(event.target.value)}
              placeholder="Typed name"
              value={finalizeName}
            />
            <button
              className="min-h-[44px] rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
              disabled={finalizePending || finalized || !finalizeName.trim()}
              onClick={() => void handleFinalize()}
              type="button"
            >
              {finalizePending ? "Finalizing..." : finalized ? "Finalized" : "Finalize"}
            </button>
          </div>
        </section>
      ) : null}

      <SafetyClosedSinceLastBlock payload={closedSinceLast} />
      <SafetyScmAutoFeed payload={autoFeed} />


      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Meeting actions</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Update meeting details before office review.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            {canEditMeeting ? (
              <Link
                className="inline-flex min-h-[44px] items-center rounded-full bg-emerald-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-700"
                to={`/safety/scm/${meeting.id}/edit`}
              >
                Edit Meeting
              </Link>
            ) : null}
            {canOpenSignoff ? (
              <Link
                className="inline-flex min-h-[44px] items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
                to={`/safety/scm/${meeting.id}/signoff`}
              >
                Master's closure for scm
              </Link>
            ) : null}
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          <DetailCard
            label="Current action items"
            value={String(agenda.summary.current_action_item_count)}
          />
          <DetailCard
            label="Open action items"
            value={String(agenda.summary.open_action_item_count)}
          />
          <DetailCard
            label="Carried forward"
            value={String(agenda.summary.carried_forward_count)}
          />
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {detailSections.map((section) => (
          <article
            className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            key={section.agenda_item_number}
          >
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Section {section.agenda_item_number}
            </p>
            <h2 className="mt-2 text-lg font-semibold text-slate-900">
              {section.section_label}
            </h2>
            <SectionContent section={section} />
            {section.decision ? (
              <p className="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                Decision: {section.decision}
              </p>
            ) : null}
          </article>
        ))}
        {officeReviewSection}
      </section>
    </section>
  );
}
