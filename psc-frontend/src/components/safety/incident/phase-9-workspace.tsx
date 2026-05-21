import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../../../hooks/use-auth";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import { formatVesselName } from "../../../lib/safety/vessel-display";
import type {
  SafetyClosureFieldHistory,
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
  const unwrapped = unwrapHistoryValue(value);
  if (unwrapped !== value) {
    return formatValue(unwrapped);
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

const fieldLabels: Record<string, string> = {
  closed_at: "Incident closed",
  closure_reason: "Closure reason recorded",
  current_phase: "Phase advanced",
  dpa_accepted_at: "DPA acceptance time recorded",
  dpa_accepted_by: "DPA acceptance recorded",
  fm_approved_at: "Fleet manager approval time recorded",
  fm_approved_by: "Fleet manager approval recorded",
  imo_classifier: "IMO classifier set",
  incident_number: "Incident number assigned",
  incident_pdf_export: "Incident PDF generated",
  investigation_depth: "Investigation depth set",
  marine_docs_checklist_done: "Marine documents checklist completed",
  office_notified_at: "Office notified",
  phase7_signature_hod: "HOD signature captured",
  phase7_signature_pic: "PIC acceptance signature captured",
  pic_user_id: "PIC assigned",
  resources_allocated: "Resources allocated",
  risk_band: "Risk band set",
  state: "Incident state changed",
};

function parseJsonValue(value: string) {
  const trimmed = value.trim();
  if (!trimmed || (!trimmed.startsWith("{") && !trimmed.startsWith("["))) {
    return value;
  }
  try {
    return JSON.parse(trimmed) as unknown;
  } catch {
    return value;
  }
}

function unwrapHistoryValue(value: unknown): unknown {
  if (typeof value === "string") {
    const parsed = parseJsonValue(value);
    return parsed === value ? value : unwrapHistoryValue(parsed);
  }
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const record = value as Record<string, unknown>;
    if ("__history_scalar__" in record) {
      return unwrapHistoryValue(record.__history_scalar__);
    }
  }
  return value;
}

function humanizeKey(value: string) {
  return value
    .replace(/^phase\d+_/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
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

function formatDisplayValue(value: unknown): string {
  const unwrapped = unwrapHistoryValue(value);
  if (unwrapped === null || unwrapped === undefined || unwrapped === "") {
    return "Not recorded";
  }
  if (typeof unwrapped === "boolean") {
    return unwrapped ? "Yes" : "No";
  }
  if (typeof unwrapped === "number") {
    return String(unwrapped);
  }
  if (typeof unwrapped === "string") {
    return unwrapped;
  }
  if (Array.isArray(unwrapped)) {
    return unwrapped.map(formatDisplayValue).join(", ");
  }
  const record = unwrapped as Record<string, unknown>;
  return Object.entries(record)
    .filter(([, entryValue]) => entryValue !== null && entryValue !== undefined && entryValue !== "")
    .map(([key, entryValue]) => `${humanizeKey(key)}: ${formatDisplayValue(entryValue)}`)
    .join(" / ");
}

function fieldTitle(fieldName: string) {
  const verificationMatch = fieldName.match(/^phase8_verification_(\d+)$/);
  if (verificationMatch) {
    return `Recommendation #${verificationMatch[1]} verification recorded`;
  }
  return fieldLabels[fieldName] ?? humanizeKey(fieldName);
}

function historyDetail(row: SafetyClosureFieldHistory) {
  const value = unwrapHistoryValue(row.new_value);

  if (row.field_name === "phase7_signature_hod" || row.field_name === "phase7_signature_pic") {
    const record = value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
    const typedName = formatDisplayValue(record.typed_name ?? record.signed_by ?? row.actor_user_id);
    const role = formatDisplayValue(record.signed_role ?? row.actor_role_code);
    const signedAt = formatTimestamp(String(record.signed_at ?? row.changed_at));
    return `${typedName} signed as ${role} at ${signedAt}.`;
  }

  if (row.field_name === "incident_pdf_export") {
    return "Closure PDF export was generated and stored for the audit pack.";
  }

  if (row.field_name === "resources_allocated") {
    return formatDisplayValue(value);
  }

  const verificationMatch = row.field_name.match(/^phase8_verification_(\d+)$/);
  if (verificationMatch) {
    return `Recommendation #${verificationMatch[1]}: ${formatDisplayValue(value)}.`;
  }

  return formatDisplayValue(value);
}

function historyKind(fieldName: string) {
  if (fieldName.includes("signature")) {
    return "Signature";
  }
  if (fieldName.includes("verification")) {
    return "Verification";
  }
  if (fieldName.includes("export")) {
    return "Export";
  }
  if (fieldName.includes("closed") || fieldName.includes("closure")) {
    return "Closure";
  }
  if (fieldName.includes("phase")) {
    return "Phase";
  }
  return "Field";
}

function historyBadgeClass(kind: string) {
  switch (kind) {
    case "Signature":
      return "bg-indigo-50 text-indigo-700 ring-indigo-200";
    case "Verification":
      return "bg-emerald-50 text-emerald-700 ring-emerald-200";
    case "Export":
      return "bg-sky-50 text-sky-700 ring-sky-200";
    case "Closure":
      return "bg-slate-900 text-white ring-slate-900";
    case "Phase":
      return "bg-amber-50 text-amber-700 ring-amber-200";
    default:
      return "bg-slate-50 text-slate-700 ring-slate-200";
  }
}

function actorLabel(row: SafetyClosureFieldHistory | SafetyClosurePhaseLog) {
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

function formatTransition(row: SafetyClosurePhaseLog) {
  const from = row.phase_from == null ? "Start" : `Phase ${row.phase_from}`;
  return `${from} to Phase ${row.phase_to}`;
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
  const [showFieldHistory, setShowFieldHistory] = useState(false);

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
      downloadBlob(await safetyApi.downloadIncidentPdf(id));
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
  const fieldHistory = summary.field_history ?? [];
  const signatureEntries = Object.entries(summary.signature_chain ?? {});
  const isDpa = resolveSafetyRole(user, role) === "DPA";
  const canDownloadMscMepc3 = isDpa && hasProcess("SAF_P_023");

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Incident / Phase 9
        </p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Closure / Read-only Record</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Locked closure view with the incident record, phase log, field history, signature chain, and issued report exports.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Status: <span className="font-semibold text-slate-900">{incident.state}</span>
          </div>
        </div>
      </header>

      {error ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section> : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading Phase 9...</section>
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Incident</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">{incident.incident_number ?? `#${incident.id}`}</p>
              <p className="mt-1 text-sm text-slate-600">{incident.record_type}</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Risk Band</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">{incident.risk_band ?? "Not set"}</p>
              <p className="mt-1 text-sm text-slate-600">{incident.imo_classifier ?? "No IMO classifier"}</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Closed At</p>
              <p className="mt-2 text-sm font-semibold text-slate-900">{formatValue(incident.closed_at)}</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">Audit Rows</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">
                {summary.audit_summary.phase_log_count} / {summary.audit_summary.field_history_count}
              </p>
              <p className="mt-1 text-sm text-slate-600">Phase logs / field changes</p>
            </article>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Read-only Incident Record</h2>
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
                <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Closure Note</dt>
                <dd className="mt-2 text-sm leading-6 text-slate-700">{formatValue(incident.closure_reason)}</dd>
              </div>
            </dl>
          </section>

          <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(360px,0.75fr)]">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">Phase Log</h2>
              <div className="mt-4 space-y-3">
                {phaseLogs.map((row) => (
                  <article key={row.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="font-semibold text-slate-900">{formatTransition(row)}</p>
                      <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">{row.transition_type}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">
                      {actorLabel(row)} / {formatTimestamp(row.occurred_at)}
                    </p>
                    {row.loop_back_reason ? <p className="mt-2 text-sm text-slate-600">{row.loop_back_reason}</p> : null}
                  </article>
                ))}
              </div>
            </div>

            <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">Signature Chain</h2>
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
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Field History</h2>
                <p className="mt-2 text-sm text-slate-600">Latest auditable field changes captured against the incident record.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  aria-expanded={showFieldHistory}
                  className={
                    showFieldHistory
                      ? "min-h-11 rounded-full bg-slate-900 px-4 text-sm font-semibold text-white"
                      : "min-h-11 rounded-full border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700"
                  }
                  onClick={() => setShowFieldHistory((current) => !current)}
                  type="button"
                >
                  {showFieldHistory ? "Hide History" : "Show History"}
                </button>
                <button className="min-h-11 rounded-full border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700" onClick={() => void reload()} type="button">
                  Refresh
                </button>
              </div>
            </div>
            {showFieldHistory ? (
            <div className="mt-4 space-y-3">
              {fieldHistory.length > 0 ? (
                fieldHistory.map((row: SafetyClosureFieldHistory) => {
                  const kind = historyKind(row.field_name);
                  return (
                    <article key={row.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${historyBadgeClass(kind)}`}>{kind}</span>
                            <h3 className="text-sm font-semibold text-slate-900">{fieldTitle(row.field_name)}</h3>
                          </div>
                          <p className="mt-3 text-sm leading-6 text-slate-700">{historyDetail(row)}</p>
                          {row.change_reason ? <p className="mt-2 text-sm text-slate-500">Reason: {row.change_reason}</p> : null}
                        </div>
                        <div className="shrink-0 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 lg:min-w-[260px]">
                          <p className="font-semibold text-slate-900">{actorLabel(row)}</p>
                          <p className="mt-1">{formatTimestamp(row.changed_at)}</p>
                        </div>
                      </div>
                    </article>
                  );
                })
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">No field-history rows are available.</div>
              )}
            </div>
            ) : (
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                Field history is hidden. {fieldHistory.length} audit row{fieldHistory.length === 1 ? "" : "s"} available.
              </div>
            )}
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Reports</h2>
            <div className="mt-4 flex flex-wrap gap-3">
              <button className="min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isDownloading !== null} onClick={() => void downloadPdf()} type="button">
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
                    {isDownloading === "msc" ? "Preparing..." : "MSC-MEPC.3 Export"}
                  </button>
                  {!canDownloadMscMepc3 ? (
                    <p className="max-w-xs text-xs leading-5 text-slate-500">
                      MSC-MEPC.3 export is restricted to DPA.
                    </p>
                  ) : null}
                </div>
              ) : null}
            </div>
          </section>
        </>
      )}

      <div className="flex flex-wrap gap-3">
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/phase-8`}>
          Back to Phase 8
        </Link>
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/reopen`}>
          Reopen Request
        </Link>
      </div>
    </section>
  );
}

export default SafetyIncidentPhase9;
