import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import SafetyOverdueSoiBlockBanner from "../../../../components/safety/scm/overdue-soi-block-banner";
import SafetyScmSignoffSignatureBlock from "../../../../components/safety/scm/signoff-signature-block";
import { useSafetyAuth } from "../../../../hooks/safety/use-auth";
import { safetyApi } from "../../../../lib/api/safety";
import { getErrorMessage } from "../../../../lib/api/client";
import { safetyKeys, useSafetyScmMeeting, useSafetyScmSignoffPreflight } from "../../../../hooks/use-safety";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../../lib/safety/digital-signature";

function parseMissingDecisionSections(errors: string[] | undefined): number[] {
  const seen = new Set<number>();
  for (const error of errors ?? []) {
    const match = /^Section\s+(\d+)\s+requires a decision\/outcome\.$/i.exec(error.trim());
    if (!match) {
      continue;
    }
    seen.add(Number(match[1]));
  }
  return Array.from(seen).sort((left, right) => left - right);
}

function PreflightPill({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-900">{value}</p>
    </article>
  );
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

export default function SafetyScmSignoffRoute() {
  const params = useParams();
  const auth = useSafetyAuth();
  const queryClient = useQueryClient();
  const meetingId = params.id ?? "";
  const enabled = Boolean(meetingId);
  const meetingQuery = useSafetyScmMeeting(meetingId, enabled);
  const preflightQuery = useSafetyScmSignoffPreflight(meetingId, enabled);
  const [typedName, setTypedName] = useState(() => resolveSignatureTypedName(auth.user));
  const [deviceFingerprint] = useState(() => getSafetyDeviceFingerprint());
  const [message, setMessage] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<unknown>(null);
  const [quickDecisionBySection, setQuickDecisionBySection] = useState<Record<number, string>>({});
  const [preflightFixMessage, setPreflightFixMessage] = useState<string | null>(null);

  const signoffMutation = useMutation({
    mutationFn: () =>
      safetyApi.signoffScm(meetingId, {
        device_fingerprint: deviceFingerprint,
        typed_name: typedName,
      }),
    onSuccess: async (response) => {
      setMessage(`SCM is closed. PDF generated as ${response.pdf.file_name}.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmMeeting(meetingId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmSignoffPreflight(meetingId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmMeetings({}) }),
      ]);
    },
  });

  const acknowledgeMutation = useMutation({
    mutationFn: () => safetyApi.acknowledgeScmAttendance(meetingId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmMeeting(meetingId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmSignoffPreflight(meetingId) }),
      ]);
    },
  });

  const pdfMutation = useMutation({
    mutationFn: () => safetyApi.downloadScmPdf(meetingId),
    onSuccess: (result) => {
      downloadBlob(result);
    },
    onError: (error) => {
      setPdfError(error);
    },
  });

  const agendaFixMutation = useMutation({
    mutationFn: (rows: Array<{ agenda_item_number: number; decision: string }>) =>
      safetyApi.updateScmAgenda(meetingId, { rows }),
    onSuccess: async () => {
      setPreflightFixMessage("Agenda decision saved. Preflight refreshed.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmMeeting(meetingId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmSignoffPreflight(meetingId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmAgenda(meetingId) }),
      ]);
    },
  });

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SCM meeting id.
      </section>
    );
  }

  if (meetingQuery.isLoading || preflightQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SCM sign-off...
      </section>
    );
  }

  if (meetingQuery.isError || preflightQuery.isError) {
    const error = meetingQuery.error ?? preflightQuery.error;
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(error)}
      </section>
    );
  }

  const meeting = meetingQuery.data;
  const preflight = preflightQuery.data;
  const signoffResult = signoffMutation.data;
  const missingDecisionSections = parseMissingDecisionSections(preflight.agenda_errors);
  const signoffStateReady = meeting.state === "SUBMITTED" || meeting.state === "REOPENED";
  const pdfDownloadAvailable = Boolean(
    meeting.state === "SIGNED_OFF" || meeting.master_signed_off_at || signoffResult?.pdf.download_path,
  );
  const signoffBlockers = [
    ...(!typedName.trim() ? ["Typed name is required."] : []),
    ...(!signoffStateReady && !meeting.master_signed_off_at
      ? ["Meeting must be finalized for Master sign-off before the Master can sign."]
      : []),
    ...(!preflight.attendance_acknowledged ? ["Attendance must be recorded and WRH warnings acknowledged."] : []),
    ...(!preflight.agenda_complete ? preflight.agenda_errors ?? [] : []),
    ...(!preflight.signatures_complete ? preflight.signature_errors ?? ["Required digital signatures are incomplete."] : []),
    ...(preflight.overdue_soi_areas.length > 0 ? ["Overdue SOI areas must be cleared."] : []),
    ...(meeting.master_signed_off_at ? ["This meeting is already signed off."] : []),
  ];
  const canSubmit = Boolean(
    typedName.trim()
    && signoffStateReady
    && preflight.attendance_acknowledged
    && preflight.agenda_complete
    && Boolean(preflight.signatures_complete)
    && preflight.overdue_soi_areas.length === 0
    && !meeting.master_signed_off_at,
  );

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#fee2e2_0%,#ffffff_55%,#fef3c7_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / SCM
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">SCM Sign-Off</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Review the preflight checks and capture the Master signature to close the SCM.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <PreflightPill
          label="Overdue SOI areas"
          value={String(preflight.overdue_soi_areas.length)}
        />
        <PreflightPill
          label="Attendance warnings"
          value={preflight.attendance_acknowledged ? "Acknowledged" : "Pending"}
        />
        <PreflightPill
          label="Agenda complete"
          value={preflight.agenda_complete ? "Yes" : "No"}
        />
        <PreflightPill
          label="Digital signatures"
          value={preflight.signatures_complete ? "Complete" : "Pending"}
        />
      </section>

      <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Sign-off preflight</h2>
        <p className="mt-2 text-sm leading-6 text-slate-700">
          Sign-off is allowed only when attendance warnings are acknowledged, all agenda
          sections have content and decisions, required digital signatures are complete,
          and no overdue SOI areas block closure.
        </p>
        {preflight.attendance_warnings_present && !preflight.attendance_acknowledged ? (
          <div className="mt-4 rounded-2xl border border-amber-300 bg-white px-4 py-3">
            <p className="text-sm font-semibold text-slate-900">
              Attendance warnings require Master acknowledgement.
            </p>
            {acknowledgeMutation.isError ? (
              <p className="mt-2 text-sm text-rose-800">
                {getErrorMessage(acknowledgeMutation.error)}
              </p>
            ) : null}
            <button
              className="mt-3 rounded-full bg-amber-700 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={acknowledgeMutation.isPending}
              onClick={() => acknowledgeMutation.mutate()}
              type="button"
            >
              {acknowledgeMutation.isPending ? "Acknowledging..." : "Acknowledge warnings"}
            </button>
          </div>
        ) : null}
        {!preflight.agenda_complete && preflight.agenda_errors?.length ? (
          <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-700">
            {preflight.agenda_errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        ) : null}
        {missingDecisionSections.length > 0 ? (
          <div className="mt-4 rounded-2xl border border-amber-300 bg-white px-4 py-3">
            <p className="text-sm font-semibold text-slate-900">Resolve agenda decision blockers</p>
            <p className="mt-1 text-sm text-slate-600">
              Enter the missing decision/outcome below, save it, then the sign-off preflight will refresh.
            </p>
            <div className="mt-3 space-y-3">
              {missingDecisionSections.map((sectionNumber) => {
                const section = meeting.sections.find((row) => row.agenda_item_number === sectionNumber);
                return (
                  <label className="block" key={sectionNumber}>
                    <span className="text-sm font-medium text-slate-900">
                      Section {sectionNumber}
                      {section?.section_label ? ` - ${section.section_label}` : ""}
                    </span>
                    <textarea
                      className="mt-2 min-h-[96px] w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                      onChange={(event) =>
                        setQuickDecisionBySection((current) => ({
                          ...current,
                          [sectionNumber]: event.target.value,
                        }))
                      }
                      placeholder="Decision / outcome"
                      value={quickDecisionBySection[sectionNumber] ?? section?.decision ?? ""}
                    />
                  </label>
                );
              })}
            </div>
            {agendaFixMutation.isError ? (
              <p className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
                {getErrorMessage(agendaFixMutation.error)}
              </p>
            ) : null}
            {preflightFixMessage ? (
              <p className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
                {preflightFixMessage}
              </p>
            ) : null}
            <button
              className="mt-3 rounded-full bg-amber-700 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={
                agendaFixMutation.isPending
                || missingDecisionSections.some((sectionNumber) => {
                  const section = meeting.sections.find((row) => row.agenda_item_number === sectionNumber);
                  return !(quickDecisionBySection[sectionNumber] ?? section?.decision ?? "").trim();
                })
              }
              onClick={() => {
                setPreflightFixMessage(null);
                agendaFixMutation.mutate(
                  missingDecisionSections.map((sectionNumber) => {
                    const section = meeting.sections.find((row) => row.agenda_item_number === sectionNumber);
                    return {
                      agenda_item_number: sectionNumber,
                      decision: (quickDecisionBySection[sectionNumber] ?? section?.decision ?? "").trim(),
                    };
                  }),
                );
              }}
              type="button"
            >
              {agendaFixMutation.isPending ? "Saving decision..." : "Save missing decision"}
            </button>
          </div>
        ) : null}
        {!preflight.signatures_complete && preflight.signature_errors?.length ? (
          <div className="mt-4 rounded-2xl border border-amber-300 bg-white px-4 py-3">
            <p className="text-sm font-semibold text-slate-900">Signature blockers</p>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {preflight.signature_errors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
            <Link
              className="mt-3 inline-flex min-h-[40px] items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
              to={`/safety/scm/${meeting.id}/attendance`}
            >
              Open attendance signatures
            </Link>
          </div>
        ) : null}
      </section>

      <SafetyScmSignoffSignatureBlock signature={signoffResult?.signature} />

      {meeting.master_signed_off_at && !signoffResult?.signature ? (
        <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-900 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span>This meeting was already signed off at {meeting.master_signed_off_at}.</span>
            <button
              className="inline-flex min-h-[44px] items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={pdfMutation.isPending}
              onClick={() => {
                setPdfError(null);
                pdfMutation.mutate();
              }}
              type="button"
            >
              {pdfMutation.isPending ? "Preparing PDF..." : "Download / Print PDF"}
            </button>
          </div>
        </section>
      ) : null}

      {!meeting.master_signed_off_at ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-4">
            <label className="block">
              <span className="text-sm font-semibold text-slate-900">Typed name</span>
              <input
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(event) => setTypedName(event.target.value)}
                type="text"
                value={typedName}
              />
            </label>
          </div>
          {signoffMutation.isError ? (
            <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
              {getErrorMessage(signoffMutation.error)}
            </div>
          ) : null}
          <button
            className="mt-4 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={!canSubmit || signoffMutation.isPending}
            onClick={() => signoffMutation.mutate()}
            type="button"
          >
            {signoffMutation.isPending ? "Closing meeting..." : "Close Meeting"}
          </button>
          {!canSubmit && signoffBlockers.length > 0 ? (
            <div className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <p className="font-semibold text-slate-900">Sign-off is disabled because:</p>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {signoffBlockers.map((blocker, index) => (
                  <li key={`${blocker}-${index}`}>{blocker}</li>
                ))}
              </ul>
              {!signoffStateReady && !meeting.master_signed_off_at ? (
                <Link
                  className="mt-3 inline-flex min-h-[40px] items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
                  to={`/safety/scm/${meeting.id}`}
                >
                  Open SCM detail to finalize
                </Link>
              ) : null}
            </div>
          ) : null}
        </section>
      ) : null}

      {message ? (
        <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-900 shadow-sm">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span>{message}</span>
            {pdfDownloadAvailable ? (
              <button
                className="inline-flex min-h-[44px] items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={pdfMutation.isPending}
                onClick={() => {
                  setPdfError(null);
                  pdfMutation.mutate();
                }}
                type="button"
              >
                {pdfMutation.isPending ? "Preparing PDF..." : "Download / Print PDF"}
              </button>
            ) : null}
          </div>
          {pdfError ? (
            <p className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
              {getErrorMessage(pdfError)}
            </p>
          ) : null}
        </section>
      ) : null}

      {pdfError && !message ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900 shadow-sm">
          {getErrorMessage(pdfError)}
        </section>
      ) : null}

      <SafetyOverdueSoiBlockBanner overdueAreas={preflight.overdue_soi_areas} />
    </section>
  );
}
