import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../../hooks/use-auth";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import type { SafetyIncidentClosureSummary } from "../../../schemas/safety/incident-closure";

function emptySummary(): SafetyIncidentClosureSummary {
  return {
    audit_summary: {
      field_history_count: 0,
      latest_field_change: null,
      latest_phase_log: null,
      phase_log_count: 0,
    },
    incident: {
      closed_at: null,
      closure_reason: null,
      current_phase: 9,
      dpa_accepted_at: null,
      dpa_accepted_by: null,
      fm_approved_at: null,
      fm_approved_by: null,
      id: 0,
      imo_classifier: null,
      incident_number: null,
      narrative: null,
      occurred_at: null,
      record_type: "INCIDENT",
      reported_at: null,
      risk_band: null,
      state: "CLOSED",
      vessel_id: "",
    },
  };
}

function normalizeCode(value: unknown) {
  return String(value ?? "").trim().toUpperCase();
}

function authorityForBand(riskBand: SafetyIncidentClosureSummary["incident"]["risk_band"]) {
  if (riskBand === "RED") {
    return {
      roles: ["FM", "FLEET MANAGER"],
      text: "RED reopen is restricted to FM.",
    };
  }
  if (riskBand === "GREEN" || riskBand === "YELLOW") {
    return {
      roles: ["DPA"],
      text: `${riskBand} reopen is restricted to DPA.`,
    };
  }
  return {
    roles: [],
    text: "Risk band must be assigned before reopen.",
  };
}

export function SafetyIncidentReopenWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { hasProcess, role, user } = useAuth();
  const [summary, setSummary] = useState<SafetyIncidentClosureSummary>(emptySummary());
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const reload = useCallback(async () => {
    if (!id) {
      setError("Invalid incident id.");
      setIsLoading(false);
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const response = await safetyApi.getIncidentClosureSummary(id);
      setSummary(response as unknown as SafetyIncidentClosureSummary);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const incident = summary.incident;
  const authority = useMemo(() => authorityForBand(incident.risk_band), [incident.risk_band]);
  const currentRole = normalizeCode(user?.role || role || user?.safety_role_name || user?.role_name);
  const hasAuthority = authority.roles.includes(currentRole);
  const hasReopenProcess = hasProcess("SAF_P_008");
  const isClosedPhaseNine = incident.state === "CLOSED" && incident.current_phase === 9;
  const canSubmit = hasAuthority && hasReopenProcess && isClosedPhaseNine;

  async function submitReopen(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsSubmitting(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.reopenIncident(id, { reason: reason.trim() });
      const currentPhase = Number((response as { current_phase?: number }).current_phase ?? 5);
      setResultMessage("Incident reopened.");
      navigate(`/safety/incidents/${id}/phase-${currentPhase}`);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Incident / Reopen
        </p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Reopen Request</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Reopen a closed Phase 9 incident with band-gated authority and an auditable reason. Reopened incidents return to Phase 5.
            </p>
          </div>
        </div>
      </header>

      {error ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section> : null}
      {resultMessage ? <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">{resultMessage}</section> : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading reopen authority...</section>
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,0.85fr)_minmax(420px,1.15fr)]">
          <aside className="space-y-4">
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">Closed Record</h2>
              <dl className="mt-4 space-y-3 text-sm">
                <div className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <dt className="text-slate-500">Incident</dt>
                  <dd className="font-semibold text-slate-900">{incident.incident_number ?? `#${incident.id}`}</dd>
                </div>
                <div className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <dt className="text-slate-500">State</dt>
                  <dd className="font-semibold text-slate-900">{incident.state}</dd>
                </div>
                <div className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <dt className="text-slate-500">Phase</dt>
                  <dd className="font-semibold text-slate-900">{incident.current_phase}</dd>
                </div>
                <div className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <dt className="text-slate-500">Risk band</dt>
                  <dd className="font-semibold text-slate-900">{incident.risk_band ?? "Not set"}</dd>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                  <dt className="text-slate-500">Closure note</dt>
                  <dd className="mt-2 text-slate-700">{incident.closure_reason || "Not recorded"}</dd>
                </div>
              </dl>
            </section>

            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">Authority</h2>
              <p className="mt-3 text-sm leading-6 text-slate-600">{authority.text}</p>
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p>Allowed role: <span className="font-semibold text-slate-900">{authority.roles.join(", ") || "None"}</span></p>
                <p className="mt-2">Current role: <span className="font-semibold text-slate-900">{currentRole || "Not available"}</span></p>
                <p className="mt-2">Process permission: <span className="font-semibold text-slate-900">{hasReopenProcess ? "Present" : "Missing"}</span></p>
              </div>
            </section>
          </aside>

          <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={submitReopen}>
            <h2 className="text-xl font-semibold text-slate-900">Submit Reopen</h2>
            {!isClosedPhaseNine ? (
              <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                Only closed Phase 9 incidents can be reopened.
              </div>
            ) : null}
            {!canSubmit ? (
              <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                Your current session cannot submit this reopen request. Backend authority remains enforced.
              </div>
            ) : null}
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Reopen reason
              <textarea
                className="mt-2 min-h-44 w-full rounded-2xl border border-slate-300 p-3"
                onChange={(event) => setReason(event.target.value)}
                value={reason}
              />
            </label>
            <button
              className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
              disabled={isSubmitting || !canSubmit || !reason.trim()}
              type="submit"
            >
              {isSubmitting ? "Reopening..." : "Reopen to Phase 5"}
            </button>
          </form>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/phase-9`}>
          Back to Phase 9
        </Link>
      </div>
    </section>
  );
}

export default SafetyIncidentReopenWorkspace;
