import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../../hooks/use-auth";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../lib/safety/digital-signature";
import type { SafetyIncidentPhase7Preflight } from "../../../schemas/safety/incident-phase7";
import SafetyDpaAcceptancePanel from "./dpa-acceptance-panel";

const SEND_BACK_PHASES = [3, 4, 5, 6] as const;
const GREEN_PIC_ROLE_CODES = new Set([
  "PIC",
  "VESSEL SUPERINTENDENT",
  "OFFICE_PIC",
  "OFFICE_SSQE",
  "OFFICE_SUPT",
]);
const HOD_SIGNER_ROLE_CODES = new Set(["HOD", "HEAD OF DEPARTMENT", "CE", "CHIEF ENGINEER", "CO", "CHIEF OFFICER"]);
const CENTRAL_OFFICE_ROLE_CODES = new Set([
  "DPA",
  "FM",
  "FLEET MANAGER",
  "OFFICE_PIC",
  "OFFICE_SSQE",
  "OFFICE_SUPT",
  "PHYSICAL_VERIFIER",
]);

function emptyPreflight(): SafetyIncidentPhase7Preflight {
  return {
    alarp_complete: false,
    bias_guards_resolved: false,
    blockers: [],
    closer_role: "DPA",
    current_phase: 7,
    generated_at: "",
    incident_id: 0,
    pdf_preview: {
      available: false,
      expected_sections: 10,
      incident_id: 0,
      message: "",
      status: "NOT_AVAILABLE",
    },
    ready_for_acceptance: false,
    recommendation_tier_count: {},
    required_process_id: "SAF_P_004",
    risk_band: null,
    root_count: 0,
    signature_chain_status: {
      dpa: { present: false, required: false },
      fm: { present: false, required: false },
      hod: { present: false, required: true },
      master: { present: false, required: true },
      pic: { present: false, required: false },
      reporter: { present: false, required: true },
    },
  };
}

function normalizeCode(value: unknown) {
  return String(value ?? "").trim().toUpperCase();
}

function resolveActorId(user: ReturnType<typeof useAuth>["user"]) {
  if (!user) {
    return "";
  }
  const userWithBackendIds = user as typeof user & { user_id?: string | number | null };
  return String(
    user.username ||
      user.employee_id ||
      user.crew_id ||
      userWithBackendIds.user_id ||
      user.id ||
      "",
  ).trim();
}

function resolveRoleCode(user: ReturnType<typeof useAuth>["user"], fallbackRole: string | undefined) {
  const centralRole = normalizeCode(user?.role || fallbackRole);
  if (CENTRAL_OFFICE_ROLE_CODES.has(centralRole)) {
    return centralRole;
  }
  return normalizeCode(user?.safety_role_name || user?.role_name || user?.rank || centralRole);
}

function phasePath(id: string | undefined, phase: number) {
  return `/safety/incidents/${id}/phase-${phase}`;
}

export function SafetyIncidentPhase7() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, role, hasProcess } = useAuth();
  const [preflight, setPreflight] = useState<SafetyIncidentPhase7Preflight>(emptyPreflight());
  const [typedName, setTypedName] = useState(() => resolveSignatureTypedName(user));
  const [device] = useState(() => getSafetyDeviceFingerprint());
  const [sendBackPhase, setSendBackPhase] = useState<number>(6);
  const [sendBackReason, setSendBackReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);

  const reload = useCallback(async () => {
    if (!id) {
      setError("Invalid incident id.");
      setIsLoading(false);
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const response = await safetyApi.getIncidentPhase7Preflight(id);
      setPreflight(response as unknown as SafetyIncidentPhase7Preflight);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const actionLabel = useMemo(() => {
    if (preflight.risk_band === "RED") {
      return preflight.signature_chain_status.dpa.present ? "FM Final Approval" : "DPA Acceptance";
    }
    if (preflight.risk_band === "GREEN") {
      return "PIC Acceptance";
    }
    return "DPA Acceptance";
  }, [preflight.risk_band, preflight.signature_chain_status.dpa.present]);

  const authority = preflight.authority;
  const requiredProcessId = authority?.required_process_id || preflight.required_process_id;
  const currentActorId = resolveActorId(user);
  const currentRoleCode = resolveRoleCode(user, role);
  const assignedPicUserId = authority?.assigned_pic_user_id?.trim() || "";
  const assignedPicRoleCode = normalizeCode(assignedPicUserId);
  const allowedRoleCodes = new Set((authority?.allowed_role_codes ?? []).map(normalizeCode));
  const hasRequiredProcess = requiredProcessId ? hasProcess(requiredProcessId) : false;
  const hodSignatureMissing = preflight.signature_chain_status.hod.required && !preflight.signature_chain_status.hod.present;
  const canSignHod = hodSignatureMissing && HOD_SIGNER_ROLE_CODES.has(currentRoleCode);
  const hasBandAuthority = useMemo(() => {
    if (preflight.risk_band === "GREEN") {
      if (assignedPicUserId && normalizeCode(currentActorId) === normalizeCode(assignedPicUserId)) {
        return true;
      }
      return GREEN_PIC_ROLE_CODES.has(assignedPicRoleCode) && GREEN_PIC_ROLE_CODES.has(currentRoleCode);
    }
    if (preflight.risk_band === "YELLOW") {
      return currentRoleCode === "DPA";
    }
    if (preflight.risk_band === "RED") {
      return preflight.signature_chain_status.dpa.present
        ? currentRoleCode === "FM" || currentRoleCode === "FLEET MANAGER"
        : currentRoleCode === "DPA";
    }
    return false;
  }, [
    assignedPicRoleCode,
    assignedPicUserId,
    currentActorId,
    currentRoleCode,
    preflight.risk_band,
    preflight.signature_chain_status.dpa.present,
  ]);
  const canSubmitAcceptance = hasRequiredProcess && hasBandAuthority && preflight.ready_for_acceptance;
  const authorityHelp = authority?.message || "Backend authority checks use the incident band, assigned closer, process permission, and signature chain.";
  const blockerLabels = preflight.blockers.map((blocker) => blocker.replace(/_/g, " "));
  const disabledReasons = useMemo(() => {
    const reasons: string[] = [];
    if (!typedName.trim()) {
      reasons.push("Typed full name is required.");
    }
    if (!preflight.ready_for_acceptance) {
      reasons.push(
        blockerLabels.length > 0
          ? `Resolve preflight blocker${blockerLabels.length === 1 ? "" : "s"} first: ${blockerLabels.join(", ")}.`
          : "Resolve the Phase 7 preflight blockers first.",
      );
    }
    if (!hasRequiredProcess) {
      reasons.push(`Your login does not have required process ${requiredProcessId || "for this phase"}.`);
    }
    if (!hasBandAuthority) {
      reasons.push("Your current login does not match the required closer authority for this risk band.");
    }
    return reasons;
  }, [blockerLabels, hasBandAuthority, hasRequiredProcess, preflight.ready_for_acceptance, requiredProcessId, typedName]);

  async function submitAcceptance(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const payload = { device_fingerprint: device, typed_name: typedName };
      const response =
        preflight.risk_band === "RED" && preflight.signature_chain_status.dpa.present
          ? await safetyApi.approveRedIncidentPhase7(id, payload)
          : await safetyApi.acceptIncidentPhase7(id, payload);
      const currentPhase = Number(response.current_phase ?? preflight.current_phase);
      if (currentPhase >= 8) {
        navigate(phasePath(id, 8));
        return;
      }
      setResultMessage("Signature captured. RED-band incidents now require FM final approval.");
      setTypedName("");
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function submitHodSignature() {
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      await safetyApi.signIncidentPhase7Hod(id, {
        device_fingerprint: device,
        typed_name: typedName,
      });
      setResultMessage("HOD signature captured.");
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function submitSendBack(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.sendBackIncidentPhase7(id, {
        reason: sendBackReason,
        target_phase: sendBackPhase,
      });
      const targetPhase = Number(response.current_phase ?? sendBackPhase);
      navigate(phasePath(id, targetPhase));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Incident / Phase 7
        </p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Acceptance and Report Issue</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Review the preflight, capture the required closer signature, issue the report, or send the record back with a reason.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Required closer: <span className="font-semibold text-slate-900">{preflight.closer_role}</span>
          </div>
        </div>
      </header>

      {error ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section> : null}
      {resultMessage ? <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">{resultMessage}</section> : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading Phase 7...</section>
      ) : (
        <>
          <SafetyDpaAcceptancePanel preflight={preflight} />

          {hodSignatureMissing ? (
            <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-amber-950">HOD Signature Required</h2>
                  <p className="mt-1 leading-6">
                    The department HOD must sign before PIC/DPA/FM acceptance can be completed.
                  </p>
                </div>
                <button
                  className="min-h-11 rounded-full bg-amber-950 px-5 text-sm font-semibold text-white disabled:bg-amber-300"
                  disabled={isMutating || !typedName.trim() || !canSignHod}
                  onClick={() => void submitHodSignature()}
                  type="button"
                >
                  {isMutating ? "Signing..." : "Capture HOD Signature"}
                </button>
              </div>
              {!canSignHod ? (
                <p className="mt-3 rounded-2xl border border-amber-300 bg-white/70 px-3 py-2">
                  Login as the department HOD, Chief Engineer, or Chief Officer to capture this signature.
                </p>
              ) : null}
            </section>
          ) : null}

          <div className="grid gap-6 xl:grid-cols-2">
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={submitAcceptance}>
              <h2 className="text-xl font-semibold text-slate-900">{actionLabel}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                {authorityHelp}
              </p>
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p>
                  Required process: <span className="font-semibold text-slate-900">{requiredProcessId}</span>
                </p>
                {preflight.risk_band === "GREEN" ? (
                  <p className="mt-2">
                    Assigned PIC: <span className="font-semibold text-slate-900">{assignedPicUserId || "Not assigned"}</span>
                  </p>
                ) : null}
                <p className="mt-2">
                  Allowed role{allowedRoleCodes.size === 1 ? "" : "s"}:{" "}
                  <span className="font-semibold text-slate-900">
                    {Array.from(allowedRoleCodes).join(", ") || "Not available"}
                  </span>
                </p>
                {disabledReasons.length > 0 ? (
                  <p className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
                    {disabledReasons[0]}
                  </p>
                ) : null}
              </div>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Typed full name
                <input
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                  onChange={(event) => setTypedName(event.target.value)}
                  value={typedName}
                />
              </label>
              <button
                className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
                disabled={isMutating || disabledReasons.length > 0 || !canSubmitAcceptance}
                type="submit"
              >
                {isMutating ? "Submitting..." : actionLabel}
              </button>
            </form>

            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={submitSendBack}>
              <h2 className="text-xl font-semibold text-slate-900">Send Back</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Send the incident back to an earlier phase with a required phase-log reason.
              </p>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Target phase
                <select
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                  onChange={(event) => setSendBackPhase(Number(event.target.value))}
                  value={sendBackPhase}
                >
                  {SEND_BACK_PHASES.map((phase) => (
                    <option key={phase} value={phase}>Phase {phase}</option>
                  ))}
                </select>
              </label>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Reason
                <textarea
                  className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3"
                  onChange={(event) => setSendBackReason(event.target.value)}
                  value={sendBackReason}
                />
              </label>
              <button
                className="mt-4 min-h-11 rounded-full border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-700 disabled:bg-slate-100 disabled:text-slate-400"
                disabled={isMutating || !sendBackReason.trim()}
                type="submit"
              >
                Send back
              </button>
            </form>
          </div>
        </>
      )}

      <div className="flex flex-wrap gap-3">
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/phase-6`}>
          Back to Phase 6
        </Link>
        {preflight.pdf_preview.download_path ? (
          <a className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white" href={preflight.pdf_preview.download_path}>
            PDF Preview
          </a>
        ) : null}
      </div>
    </section>
  );
}

export default SafetyIncidentPhase7;
