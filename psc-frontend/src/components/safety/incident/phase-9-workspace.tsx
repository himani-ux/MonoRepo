import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../../../hooks/use-auth";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import { incidentPhaseLabel } from "../../../lib/safety/incident-phase-display";
import { formatVesselName } from "../../../lib/safety/vessel-display";
import {
  DEFAULT_INCIDENT_PDF_SECTION_KEYS,
  IncidentPdfSectionSelector,
  type IncidentPdfSectionKey,
} from "./incident-pdf-section-selector";
import type {
  SafetyClosurePhaseLog,
  SafetyIncidentClosureSummary,
} from "../../../schemas/safety/incident-closure";

function emptySummary(): SafetyIncidentClosureSummary {
  return {
    audit_summary: {
      field_history_count: 0,
      latest_field_change: null,
      latest_phase_log: null,
      phase_log_count: 0,
    },
    exports: {},
    field_history: [],
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
      vessel_name: null,
    },
    phase_logs: [],
    signature_chain: {},
  };
}

function formatValue(value: unknown) {
  if (value === null || value === undefined || value === "") {
    return "Not recorded";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function formatTimestamp(value: string | null | undefined) {
  if (!value) {
    return "Not recorded";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function actorLabel(row: SafetyClosurePhaseLog) {
  return `${row.actor_role_code || "Role not recorded"} / ${row.actor_user_id || "User not recorded"}`;
}

function normalizeRole(value: unknown) {
  return String(value || "").trim().toUpperCase();
}

function resolveSafetyRole(user: ReturnType<typeof useAuth>["user"], fallbackRole: string | undefined) {
  const centralRole = normalizeRole(user?.role || fallbackRole);
  if (["DPA", "FM", "FLEET MANAGER", "OFFICE_PIC", "OFFICE_SSQE", "OFFICE_SUPT", "PHYSICAL_VERIFIER"].includes(centralRole)) {
    return centralRole;
  }
  return normalizeRole(user?.safety_role_name || user?.role_name || user?.rank || centralRole);
}

function formatRiskLevel(value: SafetyIncidentClosureSummary["incident"]["risk_band"]) {
  if (value === "GREEN") {
    return "Low";
  }
  if (value === "YELLOW") {
    return "Medium";
  }
  if (value === "RED") {
    return "High";
  }
  return "Not set";
}

function formatImoClassifier(value: string | null) {
  if (!value || value === "NOT_APPLICABLE") {
    return "No IMO class";
  }
  return value.replace(/_/g, " ");
}

function transitionStatusLabel(value: string) {
  const normalized = value.toUpperCase();
  if (normalized === "FORWARD") {
    return "Completed";
  }
  if (normalized === "LOOP_BACK") {
    return "Sent back";
  }
  if (normalized === "REWORK") {
    return "Rework";
  }
  if (normalized === "REOPEN") {
    return "Reopened";
  }
  if (normalized === "CLOSE") {
    return "Closed";
  }
  return value.replace(/_/g, " ");
}

function phaseHistoryDetail(row: SafetyClosurePhaseLog) {
  const to = incidentPhaseLabel(row.phase_to);
  if (row.phase_from === null || row.phase_from === undefined) {
    return `Record started at ${to}.`;
  }
  const from = incidentPhaseLabel(row.phase_from);
  if (from === to) {
    return `${to} was updated.`;
  }
  return `Moved from ${from} to ${to}.`;
}

function signatureLabel(value: string) {
  return value.toUpperCase();
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

export function SafetyIncidentPhase9() {
  const { id } = useParams();
  const { hasProcess, role, user } = useAuth();
  const [summary, setSummary] = useState<SafetyIncidentClosureSummary>(emptySummary());
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDownloading, setIsDownloading] = useState<string | null>(null);
  const [selectedPdfSections, setSelectedPdfSections] = useState<IncidentPdfSectionKey[]>(
    DEFAULT_INCIDENT_PDF_SECTION_KEYS,
  );

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

  async function downloadPdf() {
    if (!id) {
      return;
    }
    setIsDownloading("pdf");
    setError(null);
    try {
      downloadBlob(await safetyApi.downloadIncidentPdf(id, selectedPdfSections));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsDownloading(null);
    }
  }

  async function downloadMscMepc3() {
    if (!id) {
      return;
    }
    setIsDownloading("msc");
    setError(null);
    try {
      downloadBlob(await safetyApi.downloadIncidentMscMepc3(id));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsDownloading(null);
    }
  }

  const incident = summary.incident;
  const phaseLogs = summary.phase_logs ?? [];
  const signatureEntries = Object.entries(summary.signature_chain ?? {});
  const isDpa = resolveSafetyRole(user, role) === "DPA";
  const canDownloadMscMepc3 = isDpa && hasProcess("SAF_P_023");

  return (
    <section className="space-y-6">
      {error ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section> : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading final record...</section>
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-3">
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Incident</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">{incident.incident_number ?? `#${incident.id}`}</p>
              <p className="mt-1 text-sm text-slate-600">{incident.record_type}</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Risk Level</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">{formatRiskLevel(incident.risk_band)}</p>
              <p className="mt-1 text-sm text-slate-600">IMO class: {formatImoClassifier(incident.imo_classifier)}</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Closed On</p>
              <p className="mt-2 text-sm font-semibold text-slate-900">{formatValue(incident.closed_at)}</p>
            </article>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Incident Details</h2>
            <dl className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Vessel</dt>
                <dd className="mt-2 text-sm font-semibold text-slate-900">{formatVesselName(incident)}</dd>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Occurred</dt>
                <dd className="mt-2 text-sm font-semibold text-slate-900">{formatValue(incident.occurred_at)}</dd>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Reported</dt>
                <dd className="mt-2 text-sm font-semibold text-slate-900">{formatValue(incident.reported_at)}</dd>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 xl:col-span-3">
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Closing Note</dt>
                <dd className="mt-2 text-sm leading-6 text-slate-700">{formatValue(incident.closure_reason)}</dd>
              </div>
            </dl>
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.75fr)]">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">Phase History</h2>
                  <p className="mt-1 text-sm text-slate-600">A simple timeline of how the incident moved through the workflow.</p>
                </div>
                <span className="w-fit rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600">
                  {phaseLogs.length} step{phaseLogs.length === 1 ? "" : "s"}
                </span>
              </div>
              <div className="mt-5 space-y-4">
                {phaseLogs.length > 0 ? phaseLogs.map((row, index) => (
                  <article key={row.id} className="relative rounded-2xl border border-slate-200 bg-slate-50 p-4 pl-16">
                    <div className="absolute left-4 top-4 flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                      {index + 1}
                    </div>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">{incidentPhaseLabel(row.phase_to)}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-600">{phaseHistoryDetail(row)}</p>
                      </div>
                      <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700">
                        {transitionStatusLabel(row.transition_type)}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-slate-600">
                      Done by {actorLabel(row)} on {formatTimestamp(row.occurred_at)}
                    </p>
                    {row.loop_back_reason ? (
                      <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
                        Reason: {row.loop_back_reason}
                      </p>
                    ) : null}
                  </article>
                )) : (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">
                    No phase history is available yet.
                  </div>
                )}
              </div>
            </div>

            <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">Approvals</h2>
              <div className="mt-4 space-y-3">
                {signatureEntries.map(([roleName, status]) => (
                  <div key={roleName} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm">
                    <span className="font-semibold text-slate-900">{signatureLabel(roleName)}</span>
                    <span className={status.present ? "text-emerald-700" : status.required ? "text-amber-700" : "text-slate-500"}>
                      {status.present ? "Present" : status.required ? "Required" : "Not required"}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p>DPA: {incident.dpa_accepted_by ?? "Not recorded"}</p>
                <p className="mt-2">FM: {incident.fm_approved_by ?? "Not recorded"}</p>
              </div>
            </aside>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Reports</h2>
            <div className="mt-4">
              <IncidentPdfSectionSelector
                disabled={isDownloading !== null}
                onChange={setSelectedPdfSections}
                value={selectedPdfSections}
              />
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              <button className="min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isDownloading !== null || selectedPdfSections.length === 0} onClick={() => void downloadPdf()} type="button">
                {isDownloading === "pdf" ? "Preparing..." : "Incident PDF"}
              </button>
              {summary.exports?.msc_mepc3?.available ? (
                <div className="flex flex-col gap-2">
                  <button
                    className="min-h-11 rounded-full border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-700 disabled:bg-slate-100 disabled:text-slate-400"
                    disabled={isDownloading !== null || !canDownloadMscMepc3}
                    onClick={() => void downloadMscMepc3()}
                    type="button"
                  >
                    {isDownloading === "msc" ? "Preparing..." : "IMO Report"}
                  </button>
                  {!canDownloadMscMepc3 ? (
                    <p className="max-w-xs text-xs leading-5 text-slate-500">
                      IMO report download is restricted to DPA.
                    </p>
                  ) : null}
                </div>
              ) : null}
            </div>
          </section>
        </>
      )}

      <div className="flex flex-wrap gap-3">
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/phase-6`}>
          Back to Loss Evaluation
        </Link>
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/reopen`}>
          Reopen Incident
        </Link>
      </div>
    </section>
  );
}

export default SafetyIncidentPhase9;
