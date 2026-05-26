import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../../hooks/use-auth";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import type {
  SafetyPhase8RecommendationRow,
  SafetyPhase8WorkspacePayload,
} from "../../../schemas/safety/incident-phase8";
import SafetyDeadlinePauseBanner from "./deadline-pause-banner";

const RESIDUAL_RISK_OPTIONS = ["ALARP", "LOW", "MEDIUM", "HIGH", "DEFERRED"] as const;
const GREEN_PIC_ROLES = new Set([
  "PIC",
  "VESSEL SUPERINTENDENT",
  "OFFICE_PIC",
  "OFFICE_SSQE",
  "OFFICE_SUPT",
]);

interface VerificationDraft {
  is_effective: boolean;
  mode: "effective" | "defer" | "ineffective";
  notes: string;
  recommendation_id: string | null;
  residual_risk: string;
}

function emptyWorkspace(): SafetyPhase8WorkspacePayload {
  return {
    blockers: [],
    corrective_actions_summary: {
      closed: 0,
      in_progress: 0,
      open: 0,
      pending_verify: 0,
      total: 0,
    },
    current_phase: 8,
    deadline_pause: {
      is_paused: false,
      last_actor_user_id: null,
      last_event_at: null,
      state: "RUNNING",
    },
    incident_id: "",
    physical_verification: {
      done: 0,
      pending: 0,
      separate_track: true,
    },
    pic_retention: {
      replacement_access: "STANDARD",
      retained: false,
      retained_pic_user_id: null,
    },
    ready_for_close: false,
    recommendations: [],
    required_process_id: "SAF_P_004",
    risk_band: null,
    state: "",
  };
}

function normalizeCode(value: unknown) {
  return String(value ?? "").trim().toUpperCase();
}

function formatBlocker(value: string) {
  const [code, id] = value.split(":");
  const label = code.replace(/_/g, " ");
  return id ? `${label} #${id}` : label;
}

function formatTier(value: string) {
  if (value === "LESSONS_LEARNT") {
    return "Lessons Learnt";
  }
  return value.charAt(0) + value.slice(1).toLowerCase();
}

function verificationLabel(row: SafetyPhase8RecommendationRow) {
  if (row.verification_deferred) {
    return "Deferred";
  }
  if (!row.latest_verification) {
    return "Pending";
  }
  return row.latest_verification.is_effective ? "Effective" : "Ineffective";
}

function roleCanAct(riskBand: SafetyPhase8WorkspacePayload["risk_band"], role: string) {
  if (riskBand === "GREEN") {
    return GREEN_PIC_ROLES.has(role);
  }
  if (riskBand === "YELLOW") {
    return role === "DPA";
  }
  if (riskBand === "RED") {
    return role === "DPA" || role === "FM" || role === "FLEET MANAGER";
  }
  return false;
}

export function SafetyIncidentPhase8() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { hasProcess, role, user } = useAuth();
  const [workspace, setWorkspace] = useState<SafetyPhase8WorkspacePayload>(emptyWorkspace());
  const [draft, setDraft] = useState<VerificationDraft>({
    is_effective: true,
    mode: "effective",
    notes: "",
    recommendation_id: null,
    residual_risk: "ALARP",
  });
  const [closureReason, setClosureReason] = useState("");
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
      const response = await safetyApi.getIncidentPhase8Workspace(id);
      const payload = response as unknown as SafetyPhase8WorkspacePayload;
      setWorkspace(payload);
      setDraft((current) => ({
        ...current,
        recommendation_id: current.recommendation_id ?? payload.recommendations[0]?.id ?? null,
      }));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const currentRole = normalizeCode(user?.role || role || user?.safety_role_name || user?.role_name);
  const canUseProcess = hasProcess(workspace.required_process_id);
  const canAct = canUseProcess && roleCanAct(workspace.risk_band, currentRole);
  const selectedRecommendation = useMemo(
    () => workspace.recommendations.find((row) => row.id === draft.recommendation_id) ?? null,
    [draft.recommendation_id, workspace.recommendations],
  );
  const blockerLabels = workspace.blockers.map(formatBlocker);

  function updateVerificationMode(mode: VerificationDraft["mode"]) {
    setDraft((current) => ({
      ...current,
      is_effective: mode !== "ineffective",
      mode,
      residual_risk: mode === "defer" ? "DEFERRED" : current.residual_risk === "DEFERRED" ? "ALARP" : current.residual_risk,
    }));
  }

  async function submitVerification(event: FormEvent) {
    event.preventDefault();
    if (!id || draft.recommendation_id == null) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const notes =
        draft.mode === "defer" && !draft.notes.trim().toUpperCase().startsWith("DEFERRED:")
          ? `DEFERRED: ${draft.notes.trim()}`
          : draft.notes.trim();
      const response = await safetyApi.verifyIncidentPhase8(id, {
        is_effective: draft.is_effective,
        notes,
        recommendation_id: draft.recommendation_id,
        residual_risk: draft.residual_risk,
      });
      if ((response as { looped_back?: boolean }).looped_back) {
        navigate(`/safety/incidents/${id}/phase-6`);
        return;
      }
      setResultMessage("Effectiveness verification saved.");
      setDraft((current) => ({ ...current, notes: "" }));
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function closeIncident(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      await safetyApi.closeIncidentPhase8(id, { closure_reason: closureReason });
      navigate(`/safety/incidents/${id}/phase-9`);
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
          Safety / Incident / Phase 8
        </p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Follow-up and Effectiveness Verification</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Track corrective actions, verify recommendation effectiveness, record deferrals with justification, and close the incident when blockers are clear.
            </p>
          </div>
        </div>
      </header>

      {error ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section> : null}
      {resultMessage ? <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">{resultMessage}</section> : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading Phase 8...</section>
      ) : (
        <>
          <SafetyDeadlinePauseBanner status={workspace.deadline_pause} />

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Corrective Actions</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {workspace.corrective_actions_summary.closed}/{workspace.corrective_actions_summary.total}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                Open {workspace.corrective_actions_summary.open}, in progress {workspace.corrective_actions_summary.in_progress}, pending verify {workspace.corrective_actions_summary.pending_verify}
              </p>
              <Link
                className="mt-3 inline-flex min-h-9 items-center rounded-full border border-slate-300 bg-white px-3 text-sm font-semibold text-slate-700"
                to={`/safety/incidents/${id}/corrective-actions`}
              >
                Open actions
              </Link>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Physical Verification</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {workspace.physical_verification.done}/{workspace.physical_verification.done + workspace.physical_verification.pending}
              </p>
              <p className="mt-1 text-sm text-slate-600">Separate track retained from the SSOT.</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">PIC Retention</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">
                {workspace.pic_retention.retained_pic_user_id ?? "Not retained"}
              </p>
              <p className="mt-1 text-sm text-slate-600">{workspace.pic_retention.replacement_access}</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Closure Gate</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">
                {workspace.ready_for_close ? "Ready" : "Blocked"}
              </p>
              <p className="mt-1 text-sm text-slate-600">{workspace.risk_band ?? "No band"}</p>
            </article>
          </section>

          {!canAct ? (
            <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              Your current session does not match the Phase 8 authority or process permission for this incident.
            </section>
          ) : null}

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Recommendation Tracker</h2>
                <p className="mt-2 text-sm text-slate-600">Each recommendation needs an effectiveness result or a justified deferral before closure.</p>
              </div>
              <button className="min-h-11 rounded-full border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700" onClick={() => void reload()} type="button">
                Refresh
              </button>
            </div>
            <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-slate-700">Recommendation</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-700">Tier</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-700">CA</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-700">Verification</th>
                    <th className="px-4 py-3 text-left font-semibold text-slate-700">Residual Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 bg-white">
                  {workspace.recommendations.length > 0 ? (
                    workspace.recommendations.map((recommendation) => (
                      <tr key={recommendation.id}>
                        <td className="px-4 py-3 font-medium text-slate-900">{recommendation.title}</td>
                        <td className="px-4 py-3 text-slate-700">{formatTier(recommendation.tier)}</td>
                        <td className="px-4 py-3 text-slate-700">
                          {recommendation.action_completed ? "Completed" : "Open"} ({recommendation.corrective_action_count})
                        </td>
                        <td className="px-4 py-3 text-slate-700">{verificationLabel(recommendation)}</td>
                        <td className="px-4 py-3 text-slate-700">{recommendation.latest_verification?.residual_risk ?? "Pending"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="px-4 py-6 text-sm text-slate-500" colSpan={5}>No recommendations are available for verification.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-2">
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={submitVerification}>
              <h2 className="text-xl font-semibold text-slate-900">Record Effectiveness</h2>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Recommendation
                <select
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                  onChange={(event) => setDraft((current) => ({ ...current, recommendation_id: event.target.value || null }))}
                  value={draft.recommendation_id ?? ""}
                >
                  <option value="" disabled>Select recommendation</option>
                  {workspace.recommendations.map((recommendation) => (
                    <option key={recommendation.id} value={recommendation.id}>{recommendation.title}</option>
                  ))}
                </select>
              </label>
              {selectedRecommendation ? (
                <p className="mt-2 text-sm text-slate-600">
                  Current status: {verificationLabel(selectedRecommendation)} / CA {selectedRecommendation.action_completed ? "completed" : "open"}
                </p>
              ) : null}
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {(["effective", "defer", "ineffective"] as const).map((mode) => (
                  <label key={mode} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700">
                    <input checked={draft.mode === mode} className="mr-2" onChange={() => updateVerificationMode(mode)} type="radio" />
                    {mode === "effective" ? "Effective" : mode === "defer" ? "Defer" : "Ineffective"}
                  </label>
                ))}
              </div>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Residual risk
                <select
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                  onChange={(event) => setDraft((current) => ({ ...current, residual_risk: event.target.value }))}
                  value={draft.residual_risk}
                >
                  {RESIDUAL_RISK_OPTIONS.map((option) => (
                    <option key={option} value={option}>{option}</option>
                  ))}
                </select>
              </label>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Verification notes
                <textarea
                  className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3"
                  onChange={(event) => setDraft((current) => ({ ...current, notes: event.target.value }))}
                  value={draft.notes}
                />
              </label>
              {draft.mode === "ineffective" ? (
                <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                  Ineffective verification sends the incident back to Phase 6 for rework.
                </p>
              ) : null}
              <button
                className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
                disabled={isMutating || !canAct || draft.recommendation_id == null || !draft.notes.trim()}
                type="submit"
              >
                {isMutating ? "Saving..." : "Save verification"}
              </button>
            </form>

            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={closeIncident}>
              <h2 className="text-xl font-semibold text-slate-900">Close Incident</h2>
              {workspace.ready_for_close ? (
                <p className="mt-2 text-sm text-emerald-700">All Phase 8 blockers are clear.</p>
              ) : (
                <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                  <p className="font-semibold">Closure blockers</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {blockerLabels.map((blocker) => <li key={blocker}>{blocker}</li>)}
                  </ul>
                </div>
              )}
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Closure note
                <textarea
                  className="mt-2 min-h-36 w-full rounded-2xl border border-slate-300 p-3"
                  onChange={(event) => setClosureReason(event.target.value)}
                  value={closureReason}
                />
              </label>
              <button
                className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
                disabled={isMutating || !canAct || !workspace.ready_for_close || !closureReason.trim()}
                type="submit"
              >
                {isMutating ? "Closing..." : "Advance to Phase 9"}
              </button>
            </form>
          </div>
        </>
      )}

      <div className="flex flex-wrap gap-3">
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/phase-7`}>
          Back to Phase 7
        </Link>
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/phase-9`}>
          View Phase 9
        </Link>
      </div>
    </section>
  );
}

export default SafetyIncidentPhase8;
