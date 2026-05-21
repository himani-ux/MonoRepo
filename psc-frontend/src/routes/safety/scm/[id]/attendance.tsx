import SafetyAttendanceTable, {
  type SafetyScmAttendanceRow,
} from "../../../../components/safety/scm/attendance-table";
import SafetyWrhUnavailableWarning from "../../../../components/safety/scm/wrh-unavailable-warning";
import SafetyFloatingFeedback from "../../../../components/safety/shared/safety-floating-feedback";
import { safetyKeys, useSafetyScmAttendance } from "../../../../hooks/use-safety";
import { useAuth } from "../../../../hooks/use-auth";
import { safetyApi } from "../../../../lib/api/safety";
import { getErrorMessage } from "../../../../lib/api/client";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../../lib/safety/digital-signature";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

function formatRestHours(value: number | string | null) {
  if (value === null) {
    return "Unavailable";
  }

  const normalized = typeof value === "number" ? value : Number(value);
  return Number.isFinite(normalized) ? `${normalized.toFixed(1)} h` : "Unavailable";
}

function normalizeSafetyRole(user: unknown) {
  const value = user as {
    rank?: string | null;
    role?: string | null;
    role_name?: string | null;
    safety_role_name?: string | null;
  } | null;
  return [
    value?.safety_role_name,
    value?.role_name,
    value?.role,
    value?.rank,
  ]
    .map((item) => String(item ?? "").trim().toUpperCase())
    .filter(Boolean)
    .join(" ");
}

export default function SafetyScmAttendanceRoute() {
  const params = useParams();
  const meetingId = params.id ?? "";
  const enabled = Boolean(meetingId);
  const query = useSafetyScmAttendance(meetingId, enabled);
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [deviceFingerprint] = useState(() => getSafetyDeviceFingerprint());
  const [message, setMessage] = useState<string | null>(null);
  const signatureMutation = useMutation({
    mutationFn: (payload: { crewId: string; role: "CO" | "ATTENDEE"; typedName: string }) =>
      safetyApi.recordScmSignature(meetingId, {
        device_fingerprint: deviceFingerprint,
        signer_crew_id: payload.crewId,
        signer_role: payload.role,
        typed_name: payload.typedName,
      }),
    onSuccess: async (signature) => {
      setMessage(`${signature.display_name || signature.typed_name} signature captured.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmAttendance(meetingId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmSignoffPreflight(meetingId) }),
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
    signature: row.signature
      ? {
          required: row.signature.required,
          signedAt: row.signature.signed_at,
          signerRole: row.signature.signer_role,
          status: row.signature.status,
          typedName: row.signature.typed_name,
        }
      : undefined,
  }));

  const coSignature = query.data.co_signature;
  const coSigned = coSignature?.status === "SIGNED";
  const roleText = normalizeSafetyRole(user);
  const canCaptureCoSignature = roleText === "CO" || roleText.includes("CHIEF OFFICER") || roleText.includes("CHIEF MATE");
  const canCaptureAttendeeSignature = canCaptureCoSignature || roleText.includes("MASTER") || roleText.includes("CAPTAIN");

  return (
    <section className="space-y-6">
      {message ? <SafetyFloatingFeedback tone="success">{message}</SafetyFloatingFeedback> : null}
      {signatureMutation.isError ? (
        <SafetyFloatingFeedback tone="error">{getErrorMessage(signatureMutation.error)}</SafetyFloatingFeedback>
      ) : null}
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
            {query.data.timezone_offset_minutes === null
              ? "Unavailable"
              : `UTC ${query.data.timezone_offset_minutes >= 0 ? "+" : ""}${query.data.timezone_offset_minutes} min`}
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

      {coSignature?.required ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                Chief Officer co-signature
              </p>
              <p className="mt-2 text-sm text-slate-600">
                {coSigned
                  ? `Signed by ${coSignature.typed_name ?? coSignature.signer_crew_id} at ${coSignature.signed_at ?? "recorded time"}`
                  : "Required before Master sign-off."}
              </p>
            </div>
            <button
              className="min-h-[42px] rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              disabled={coSigned || signatureMutation.isPending || !canCaptureCoSignature}
              onClick={() =>
                signatureMutation.mutate({
                  crewId: coSignature.signer_crew_id,
                  role: "CO",
                  typedName: resolveSignatureTypedName(user) || coSignature.signer_crew_id,
                })
              }
              type="button"
            >
              {coSigned ? "CO signature captured" : canCaptureCoSignature ? "Capture CO signature" : "CO login required"}
            </button>
          </div>
        </section>
      ) : null}

      <SafetyAttendanceTable
        isSigning={signatureMutation.isPending}
        onCaptureSignature={
          canCaptureAttendeeSignature
            ? (row) =>
                signatureMutation.mutate({
                  crewId: row.crewId,
                  role: "ATTENDEE",
                  typedName: row.displayName,
                })
            : undefined
        }
        rows={rows}
      />
    </section>
  );
}
