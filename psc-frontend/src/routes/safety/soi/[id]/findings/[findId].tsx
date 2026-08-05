import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import SafetyMasterCountersignBlock from "../../../../../components/safety/soi/master-countersign-block";
import SafetyRepeatFindingBadge from "../../../../../components/safety/soi/repeat-finding-badge";
import { useSafetyAuth } from "../../../../../hooks/safety/use-auth";
import { safetyKeys, useSafetySoiFinding, useSafetySoiInspection } from "../../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../../lib/api/client";
import { safetyApi } from "../../../../../lib/api/safety";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../../../lib/safety/digital-signature";

function lifecycleClass(active: boolean, complete: boolean) {
  if (complete) {
    return "border-emerald-300 bg-emerald-50 text-emerald-900";
  }
  if (active) {
    return "border-amber-300 bg-amber-50 text-amber-900";
  }
  return "border-slate-200 bg-slate-50 text-slate-600";
}

const lifecycle = [
  { key: "OPEN", label: "Open" },
  { key: "PENDING_CLOSURE", label: "Pending Closure" },
  { key: "MASTER_APPROVED", label: "Master Approved" },
  { key: "CLOSED", label: "Closed" },
];
const pendingClosureRoles = new Set(["SO", "CO", "CHIEF OFFICER", "2E", "2/E", "SECOND ENGINEER"]);
const alternateSafetyOfficerRoles = new Set(["2E", "2/E", "SECOND ENGINEER"]);

function resolveCurrentUserIds(user: ReturnType<typeof useSafetyAuth>["user"]) {
  const candidates = [
    user?.crewId,
    user?.employeeId,
    user?.login_id,
    user?.id,
    user?.userName,
  ];
  return new Set(
    candidates
      .map((value) => String(value ?? "").trim())
      .filter(Boolean),
  );
}

function formatLifecycleStatus(status: string) {
  return status
    .split("_")
    .map((part) => part.charAt(0) + part.slice(1).toLowerCase())
    .join(" ");
}

export default function SafetySoiFindingDetailRoute() {
  const params = useParams();
  const auth = useSafetyAuth();
  const queryClient = useQueryClient();
  const inspectionId = params.id ?? "";
  const findingId = params.findId ?? "";
  const enabled = Boolean(inspectionId && findingId);
  const [soTypedName, setSoTypedName] = useState(() => resolveSignatureTypedName(auth.user));
  const [soDeviceFingerprint] = useState(() => getSafetyDeviceFingerprint());
  const [soClosureNote, setSoClosureNote] = useState("");
  const [dpaReopenReason, setDpaReopenReason] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const inspectionQuery = useSafetySoiInspection(inspectionId, enabled);
  const findingQuery = useSafetySoiFinding(findingId, enabled);

  const pendingMutation = useMutation({
    mutationFn: () =>
      safetyApi.markSoiFindingPendingClosure(findingId, {
        closure_note: soClosureNote,
        device_fingerprint: soDeviceFingerprint,
        typed_name: soTypedName,
      }),
    onSuccess: async () => {
      setMessage("Pending-closure signature captured and routed to Master review.");
      await queryClient.invalidateQueries({ queryKey: safetyKeys.soiFinding(findingId) });
    },
  });

  const approvalMutation = useMutation({
    mutationFn: (payload: Parameters<typeof safetyApi.approveSoiFindingClosure>[1]) =>
      safetyApi.approveSoiFindingClosure(findingId, payload),
    onSuccess: async (response) => {
      setMessage(
        response.status === "CLOSED"
          ? "Finding closed after Master counter-signature."
          : "Finding returned to Open.",
      );
      await queryClient.invalidateQueries({ queryKey: safetyKeys.soiFinding(findingId) });
    },
  });

  const reopenMutation = useMutation({
    mutationFn: () =>
      safetyApi.reopenSoiFinding(findingId, {
        reason: dpaReopenReason,
      }),
    onSuccess: async () => {
      setDpaReopenReason("");
      setMessage("Finding reopened by DPA and returned to Open.");
      await queryClient.invalidateQueries({ queryKey: safetyKeys.soiFinding(findingId) });
      await queryClient.invalidateQueries({ queryKey: safetyKeys.soiFindings(inspectionId) });
    },
  });

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SOI finding route.
      </section>
    );
  }

  if (inspectionQuery.isLoading || findingQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SOI finding...
      </section>
    );
  }

  if (inspectionQuery.isError || findingQuery.isError) {
    const error = inspectionQuery.error ?? findingQuery.error;
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(error)}
      </section>
    );
  }

  const inspection = inspectionQuery.data;
  const selectedFinding = approvalMutation.data ?? pendingMutation.data ?? findingQuery.data;
  const areaName = inspection.selected_areas.find((area) => area.area_id === selectedFinding.area_id)?.area_name
    ?? `Area ${selectedFinding.area_id}`;
  const normalizedRole = (auth.role ?? "").trim().toUpperCase();
  const currentUserIds = resolveCurrentUserIds(auth.user);
  const activeSafetyOfficerForRecord = !alternateSafetyOfficerRoles.has(normalizedRole)
    || currentUserIds.has(String(inspection.safety_officer_crew_id ?? "").trim());
  const canMarkPendingClosure = auth.hasProcess("SAF_P_014")
    && pendingClosureRoles.has(normalizedRole)
    && activeSafetyOfficerForRecord;
  const canApproveClosure = auth.hasProcess("SAF_P_015") && normalizedRole === "MASTER";
  const canReopenFinding = auth.hasProcess("SAF_P_008")
    && normalizedRole === "DPA"
    && (selectedFinding.status === "CLOSED" || selectedFinding.status === "MASTER_APPROVED");
  const isCarriedForward = selectedFinding.status === "CARRIED_FORWARD";
  const canMoveToPendingClosure = selectedFinding.status === "OPEN" || isCarriedForward;
  const lifecycleStatus = isCarriedForward ? "OPEN" : selectedFinding.status;
  const currentLifecycleIndex = lifecycle.findIndex((item) => item.key === lifecycleStatus);
  const activeMasterSignature =
    selectedFinding.status === "CLOSED" || selectedFinding.status === "MASTER_APPROVED"
      ? selectedFinding.master_counter_signature
      : null;

  return (
    <section className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.16),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(14,165,233,0.12),_transparent_28%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-semibold text-slate-900">SOI Finding Closure</h1>
              <SafetyRepeatFindingBadge
                badgeText={selectedFinding.repeat_badge_text}
                occurrenceCount={selectedFinding.repeat_occurrence_count}
              />
            </div>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Open - Pending Closure - Master Approved - Closed. Carried-forward findings remain open until Safety Officer handoff.
            </p>
          </div>
          <Link
            className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
            to={`/safety/soi/${inspectionId}/findings`}
          >
            Back to findings
          </Link>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <section className="space-y-6">
          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{selectedFinding.title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">{selectedFinding.description}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Area</div>
                <div className="mt-2 font-medium text-slate-900">
                  {selectedFinding.area_id} - {areaName}
                </div>
                <div className="mt-2 text-slate-600">Priority: {selectedFinding.priority}</div>
                <div className="text-slate-600">Severity: {selectedFinding.severity}</div>
                <div className="text-slate-600">Due: {selectedFinding.due_date ?? "Not yet set"}</div>
              </div>
            </div>
          </section>

          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Lifecycle</h2>
            <div className="mt-4 grid gap-3 md:grid-cols-4">
              {lifecycle.map((step, index) => {
                const active = step.key === lifecycleStatus;
                const complete = currentLifecycleIndex >= 0 && currentLifecycleIndex > index;
                return (
                  <div
                    key={step.key}
                    className={`rounded-3xl border px-4 py-3 text-sm font-semibold ${lifecycleClass(active, complete)}`}
                  >
                    {step.label}
                  </div>
                );
              })}
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              {isCarriedForward ? (
                <span className="rounded-full border border-amber-300 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-900">
                  Carried Forward
                </span>
              ) : null}
              {selectedFinding.master_approval_state ? (
                <span className="rounded-full border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-900">
                  {formatLifecycleStatus(selectedFinding.master_approval_state)}
                </span>
              ) : null}
            </div>
            {selectedFinding.status !== lifecycleStatus ? (
              <p className="mt-3 text-sm leading-6 text-slate-600">
                Current status: {formatLifecycleStatus(selectedFinding.status)}
              </p>
            ) : null}
          </section>

          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Paper-signature rule</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              SO and Assistant remain paper-signature roles. The digital trail here only records pending closure and Master counter-signature.
            </p>
          </section>

          {canMarkPendingClosure && canMoveToPendingClosure ? (
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Mark pending closure</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                The Safety Officer signs the closure handoff here before Master review.
              </p>
              <div className="mt-5 grid gap-4">
                <label className="block">
                  <span className="text-sm font-semibold text-slate-900">Typed name</span>
                  <input
                    aria-label="Safety Officer typed name"
                    className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                    onChange={(event) => setSoTypedName(event.target.value)}
                    type="text"
                    value={soTypedName}
                  />
                </label>
              </div>
              <label className="mt-4 block">
                <span className="text-sm font-semibold text-slate-900">Closure note</span>
                <textarea
                  aria-label="Safety Officer closure note"
                  className="mt-2 min-h-28 w-full rounded-3xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  onChange={(event) => setSoClosureNote(event.target.value)}
                  value={soClosureNote}
                />
              </label>
              {pendingMutation.isError ? (
                <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
                  {getErrorMessage(pendingMutation.error)}
                </div>
              ) : null}
              <button
                className="mt-4 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={pendingMutation.isPending}
                onClick={() => {
                  setMessage(null);
                  pendingMutation.mutate();
                }}
                type="button"
              >
                {pendingMutation.isPending ? "Saving..." : "Mark pending closure"}
              </button>
            </section>
          ) : null}

          {selectedFinding.pending_closure_signature ? (
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Safety Officer handoff</h2>
              <dl className="mt-4 grid gap-4 md:grid-cols-3">
                <div>
                  <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Signed By</dt>
                  <dd className="mt-1 text-sm text-slate-900">{selectedFinding.pending_closure_signature.signer_display_name}</dd>
                </div>
                <div>
                  <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Signed At</dt>
                  <dd className="mt-1 text-sm text-slate-900">{selectedFinding.pending_closure_signature.signed_at}</dd>
                </div>
                <div>
                  <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Signature record</dt>
                  <dd className="mt-1 text-sm text-slate-900">{selectedFinding.pending_closure_signature.device_fingerprint_last8}</dd>
                </div>
              </dl>
            </section>
          ) : null}
        </section>

        <aside className="space-y-6">
          <SafetyMasterCountersignBlock
            canAct={canApproveClosure}
            error={approvalMutation.isError ? getErrorMessage(approvalMutation.error) : null}
            existingSignature={activeMasterSignature ?? undefined}
            onApprove={({ closureNote, deviceFingerprint, typedName }) => {
              setMessage(null);
              approvalMutation.mutate({
                closure_note: closureNote,
                decision: "APPROVE",
                device_fingerprint: deviceFingerprint,
                typed_name: typedName,
              });
            }}
            onReject={(reason) => {
              setMessage(null);
              approvalMutation.mutate({
                decision: "REJECT",
                reason,
              });
            }}
            status={selectedFinding.status}
          />

          <section className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Repeat-finding visibility</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Repeat findings are checked for this record.
            </p>
          </section>

          {canReopenFinding ? (
            <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">DPA reopen</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Reopen a closed finding only when follow-up evidence or audit review shows the closure is not acceptable.
              </p>
              <label className="mt-4 block">
                <span className="text-sm font-semibold text-slate-900">Reopen reason</span>
                <textarea
                  aria-label="DPA reopen reason"
                  className="mt-2 min-h-28 w-full rounded-3xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                  onChange={(event) => setDpaReopenReason(event.target.value)}
                  value={dpaReopenReason}
                />
              </label>
              {reopenMutation.isError ? (
                <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
                  {getErrorMessage(reopenMutation.error)}
                </div>
              ) : null}
              <button
                className="mt-4 rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={reopenMutation.isPending || !dpaReopenReason.trim()}
                onClick={() => {
                  setMessage(null);
                  reopenMutation.mutate();
                }}
                type="button"
              >
                {reopenMutation.isPending ? "Reopening..." : "Reopen finding"}
              </button>
            </section>
          ) : null}
        </aside>
      </section>

      {message ? (
        <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800">
          {message}
        </div>
      ) : null}
    </section>
  );
}
