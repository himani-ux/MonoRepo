import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import { useAuth } from "../../../hooks/use-auth";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../lib/safety/digital-signature";
import { formatVesselName } from "../../../lib/safety/vessel-display";
import SafetyFloatingFeedback from "../shared/safety-floating-feedback";

type NearMissMode = "detail" | "review" | "rework" | "triage" | "analysis" | "fleet-alert" | "closure" | "audit" | "pdf";
const SAFETY_CIRCULAR_PREFILL_KEY = "safetyCircularPrefill";

interface NearMissRecord {
  id: number;
  public_id?: string;
  incident_number: string | null;
  vessel_id: string;
  state: string;
  current_phase?: number;
  occurred_at?: string | null;
  reported_at?: string | null;
  near_miss_immediate_action?: string | null;
  near_miss_mscat_subcode_id?: string | null;
  narrative?: string | null;
  near_miss_priority?: "LOW" | "HIGH" | string | null;
  near_miss_severity?: "HIGH" | "MED" | "LOW" | string | null;
  near_miss_shell_tag?: string | null;
  near_miss_suggestion?: string | null;
  reporter_name?: string | null;
  reporter_rank?: string | null;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_name?: string | null;
  visibility_rule?: string;
  closure_reason?: string | null;
  closed_at?: string | null;
}

interface AnalysisFact {
  evidence_preview?: EvidencePreview | null;
  id: number;
  public_id?: string;
  sequence_index: number;
  fact_text: string;
  fact_timestamp: string | null;
  source_evidence_id: number | string;
  evidence_summary?: string;
  confidence: "LOW" | "MEDIUM" | "HIGH" | string;
}

interface EvidenceSourceOption {
  id: number;
  public_id?: string;
  label: string;
  preview?: EvidencePreview | null;
  source_type: string;
}

interface EvidencePreview {
  content_type: string;
  file_name?: string | null;
  preview_url: string;
  title?: string | null;
}

interface AnalysisPayload {
  analysis_mode: string;
  evidence_sources?: EvidenceSourceOption[];
  near_miss: NearMissRecord;
  facts: AnalysisFact[];
  requirements: Record<string, boolean>;
}

interface FleetAlertPayload {
  draft?: {
    title: string;
    body: string;
    due_by: string;
    anonymised: boolean;
    fleet_learning_text?: string;
  };
  issued?: boolean;
  issued_at?: string | null;
  sla?: {
    due_by?: string | null;
    status?: string | null;
    overdue?: boolean;
    extension?: {
      reason?: string | null;
    } | null;
  };
  circular_publish?: {
    circular_id?: string | null;
    detail_url?: string | null;
    status?: string | null;
  };
  near_miss?: Pick<NearMissRecord, "id" | "incident_number" | "near_miss_priority" | "state">;
  recipient_vessels?: Array<{
    display_name?: string | null;
    vessel_code?: string | null;
    vessel_id: string;
    vessel_name?: string | null;
  }>;
  recipients?: string[];
}

interface AuditPayload {
  phase_log?: Array<{
    id: number;
    phase_from: number | null;
    phase_to: number;
    transition_type: string;
    actor_user_id: string;
    actor_role_code: string;
    occurred_at: string;
  }>;
  field_history?: Array<{
    id: number;
    field_name: string;
    actor_user_id: string;
    actor_role_code: string;
    changed_at: string;
    new_value: unknown;
  }>;
}

const PRIORITIES = ["LOW", "HIGH"] as const;
const CONFIDENCE = ["LOW", "MEDIUM", "HIGH"] as const;
const CONFLICT_APPROVER_ROLES = ["", "DPA", "FM", "MASTER", "HOD"] as const;
const VESSEL_REVIEW_ROLES = new Set(["MASTER", "CAPTAIN", "CO", "CE", "HOD", "CHIEF OFFICER", "CHIEF ENGINEER", "HEAD OF DEPARTMENT"]);
const HIGH_PRIORITY_CLOSE_ROLES = new Set(["DPA", "FM", "FLEET MANAGER"]);
const LOW_PRIORITY_CLOSE_ROLES = new Set([
  "MASTER",
  "CAPTAIN",
  "DPA",
  "FM",
  "FLEET MANAGER",
  "PIC",
  "OFFICE_PIC",
  "OFFICE_SSQE",
  "OFFICE_SUPT",
]);

function normalizeCode(value: unknown) {
  return String(value ?? "").trim().toUpperCase();
}

export function resolveAuthorityRole(user: unknown, fallbackRole: unknown) {
  const record = (user ?? {}) as Record<string, unknown>;
  const centralRole = normalizeCode(record.role ?? fallbackRole);
  if (["DPA", "FM", "FLEET MANAGER", "OFFICE_PIC", "OFFICE_SSQE", "OFFICE_SUPT"].includes(centralRole)) {
    return centralRole;
  }

  const vesselRole = normalizeCode(record.safety_role_name ?? record.role_name ?? record.rank);
  if (vesselRole) {
    return vesselRole;
  }

  if (centralRole === "VESSEL_MASTER") {
    return "MASTER";
  }
  return centralRole;
}

function buildClosureBlockers({
  canClose,
  currentRole,
  hasCloseApproval,
  hasPicClose,
  nearMiss,
  preventiveMeasures,
  preventiveMeasureDueDate,
  preventiveMeasureOwner,
  preventiveMeasureStatus,
}: {
  canClose: boolean;
  currentRole: string;
  hasCloseApproval: boolean;
  hasPicClose: boolean;
  nearMiss: NearMissRecord | null;
  preventiveMeasures?: string;
  preventiveMeasureDueDate?: string;
  preventiveMeasureOwner?: string;
  preventiveMeasureStatus?: string;
}) {
  if (!nearMiss) {
    return ["Near-miss details are still loading."];
  }

  const blockers: string[] = [];
  const state = normalizeCode(nearMiss.state);
  const priority = normalizeCode(nearMiss.near_miss_priority || "LOW");

  if (state === "CLOSED") {
    blockers.push("Near miss is already closed.");
  } else if (state === "SUPERSEDED") {
    blockers.push("Superseded near misses continue in the incident workflow.");
  } else if (state !== "TRIAGED") {
    blockers.push("DPA triage must be completed before closure.");
  }

  if (priority === "HIGH") {
    if (!HIGH_PRIORITY_CLOSE_ROLES.has(currentRole)) {
      blockers.push("HIGH-priority near miss closure is DPA/FM only.");
    }
    if (!hasCloseApproval) {
      blockers.push("HIGH-priority near miss closure requires SAF_P_004.");
    }
    if (!String(preventiveMeasures ?? nearMiss.near_miss_suggestion ?? "").trim()) {
      blockers.push("HIGH-priority near miss closure requires preventive measures.");
    }
    if (!String(preventiveMeasureOwner ?? "").trim()) {
      blockers.push("HIGH-priority near miss closure requires a preventive-measure owner.");
    }
    if (!String(preventiveMeasureDueDate ?? "").trim()) {
      blockers.push("HIGH-priority near miss closure requires a preventive-measure due date.");
    }
    if (!String(preventiveMeasureStatus ?? "").trim()) {
      blockers.push("HIGH-priority near miss closure requires a preventive-measure status.");
    }
  } else if (priority === "LOW") {
    if (!LOW_PRIORITY_CLOSE_ROLES.has(currentRole)) {
      blockers.push("LOW-priority near miss closure is restricted to Master, PIC, DPA, or FM authority.");
    }
    if (!canClose || (!hasCloseApproval && !hasPicClose)) {
      blockers.push("LOW-priority near miss closure requires SAF_P_004 or SAF_P_006.");
    }
  } else {
    blockers.push("Near miss priority must be LOW or HIGH before closure.");
  }

  return blockers;
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

function lifecycleLinks(id: string | undefined) {
  if (!id) {
    return [];
  }
  return [
    ["Detail", `/safety/near-miss/${id}`],
    ["Review", `/safety/near-miss/${id}/review`],
    ["Rework", `/safety/near-miss/${id}/rework`],
    ["Triage", `/safety/near-miss/${id}/triage`],
    ["Analysis", `/safety/near-miss/${id}/analysis`],
    ["Fleet alert", `/safety/near-miss/${id}/fleet-alert`],
    ["Closure", `/safety/near-miss/${id}/closure`],
    ["Audit", `/safety/near-miss/${id}/audit`],
    ["PDF", `/safety/near-miss/${id}/pdf`],
  ] as const;
}

function modeTitle(mode: NearMissMode) {
  switch (mode) {
    case "review":
      return "Near Miss Vessel Review";
    case "rework":
      return "Near Miss Rework";
    case "triage":
      return "Near Miss Triage";
    case "analysis":
      return "Near Miss Fact Analysis";
    case "fleet-alert":
      return "Near Miss Fleet Alert";
    case "closure":
      return "Near Miss Closure";
    case "audit":
      return "Near Miss Audit Trail";
    case "pdf":
      return "Near Miss PDF Export";
    default:
      return "Near Miss Detail";
  }
}

export function SafetyNearMissWorkspace({ mode }: { mode: NearMissMode }) {
  const { id } = useParams();
  const location = useLocation();
  const initialResultMessage =
    typeof location.state === "object" &&
    location.state !== null &&
    "resultMessage" in location.state &&
    typeof location.state.resultMessage === "string"
      ? location.state.resultMessage
      : null;
  const { hasProcess, role, user } = useAuth();
  const signatureTypedName = resolveSignatureTypedName(user);
  const [payload, setPayload] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [resultMessage, setResultMessage] = useState<string | null>(initialResultMessage);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [triage, setTriage] = useState({
    near_miss_priority: "LOW",
    override_reason: "",
    supersede_to_incident: false,
  });
  const [reviewDraft, setReviewDraft] = useState({
    comment: "",
    device_fingerprint: getSafetyDeviceFingerprint(),
    decision: "SUBMIT_TO_OFFICE",
    typed_name: signatureTypedName,
  });
  const [reworkDraft, setReworkDraft] = useState({
    comment: "",
  });
  const [factDraft, setFactDraft] = useState({
    confidence: "MEDIUM",
    fact_text: "",
    fact_timestamp: "",
    hindsight_override_reason: "",
    sequence_index: 1,
    source_evidence_id: "",
  });
  const [evidenceDraft, setEvidenceDraft] = useState({
    description: "",
    evidence_type: "PHOTO",
    photo_file: null as File | null,
    source_label: "",
    title: "",
  });
  const [alertDraft, setAlertDraft] = useState(() => ({
    alert_text: "",
    device_fingerprint: getSafetyDeviceFingerprint(),
    fleet_learning_text: "",
    recipient_vessel_ids: [] as string[],
    sla_extension_reason: "",
    typed_name: signatureTypedName,
  }));
  const [closureDraft, setClosureDraft] = useState(() => ({
    closure_reason: "",
    conflict_acknowledged: false,
    conflict_approver_role: "",
    device_fingerprint: getSafetyDeviceFingerprint(),
    near_miss_suggestion: "",
    preventive_measure_due_date: "",
    preventive_measure_owner: "",
    preventive_measure_status: "OPEN",
    typed_name: signatureTypedName,
  }));

  const currentRole = resolveAuthorityRole(user, role);
  const canTriage = currentRole === "DPA" && hasProcess("SAF_P_002");
  const canReview = VESSEL_REVIEW_ROLES.has(currentRole) && (hasProcess("SAF_P_002") || hasProcess("SAF_P_006"));
  const canSubmitRework = hasProcess("SAF_P_001");
  const canIssueFleetAlert = currentRole === "DPA" && hasProcess("SAF_P_024");
  const hasCloseApproval = hasProcess("SAF_P_004");
  const hasPicClose = hasProcess("SAF_P_006");
  const canClose = hasCloseApproval || hasPicClose;
  const canAnalyze = hasProcess("SAF_P_002");

  const load = useCallback(async () => {
    if (!id) {
      setError("Invalid near-miss id.");
      setIsLoading(false);
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      let response: unknown;
      if (mode === "analysis") {
        response = await safetyApi.getNearMissAnalysis(id);
      } else if (mode === "fleet-alert") {
        response = await safetyApi.getNearMissFleetAlert(id);
      } else if (mode === "audit") {
        response = await safetyApi.getNearMissAudit(id);
      } else {
        response = await safetyApi.getNearMiss(id);
      }
      setPayload(response);
      const nearMiss = extractNearMiss(response);
      if (nearMiss?.near_miss_priority) {
        setTriage((current) => ({ ...current, near_miss_priority: String(nearMiss.near_miss_priority).toUpperCase() }));
      }
      if (nearMiss?.near_miss_suggestion) {
        setClosureDraft((current) => ({
          ...current,
          near_miss_suggestion: current.near_miss_suggestion || nearMiss.near_miss_suggestion || "",
        }));
      }
      if (mode === "fleet-alert") {
        const fleet = (response ?? {}) as FleetAlertPayload;
        if (fleet.draft?.body) {
          setAlertDraft((current) => ({ ...current, alert_text: fleet.draft?.body ?? current.alert_text }));
        }
        if (fleet.draft?.fleet_learning_text) {
          setAlertDraft((current) => ({
            ...current,
            fleet_learning_text: current.fleet_learning_text || fleet.draft?.fleet_learning_text || "",
          }));
        }
        if (fleet.recipients?.length) {
          setAlertDraft((current) => ({
            ...current,
            recipient_vessel_ids: current.recipient_vessel_ids.length ? current.recipient_vessel_ids : fleet.recipients ?? [],
          }));
        }
      }
      if (mode === "analysis") {
        const analysisPayload = (response ?? {}) as AnalysisPayload;
        const nextSequence =
          (analysisPayload.facts ?? []).reduce((maxSequence, fact) => Math.max(maxSequence, Number(fact.sequence_index) || 0), 0) + 1;
        setFactDraft((current) => ({
          ...current,
          sequence_index: current.sequence_index > nextSequence ? current.sequence_index : nextSequence,
        }));
        const firstSourceId = analysisPayload.evidence_sources?.[0]?.public_id ?? analysisPayload.evidence_sources?.[0]?.id;
        if (firstSourceId) {
          setFactDraft((current) => ({
            ...current,
            source_evidence_id: current.source_evidence_id || String(firstSourceId),
          }));
        }
      }
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id, mode]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!signatureTypedName) {
      return;
    }
    setAlertDraft((current) => ({
      ...current,
      typed_name: current.typed_name || signatureTypedName,
    }));
    setClosureDraft((current) => ({
      ...current,
      typed_name: current.typed_name || signatureTypedName,
    }));
  }, [signatureTypedName]);

  const nearMiss = extractNearMiss(payload);
  const analysis = mode === "analysis" ? (payload as AnalysisPayload | null) : null;
  const evidenceSources = analysis?.evidence_sources ?? [];
  const fleetAlert = mode === "fleet-alert" ? (payload as FleetAlertPayload | null) : null;
  const recipientLabels = (fleetAlert?.recipient_vessels ?? []).map((recipient) => {
    const code = recipient.vessel_code ? `${recipient.vessel_code} - ` : "";
    return `${code}${recipient.display_name || recipient.vessel_name || recipient.vessel_id}`;
  });
  const audit = mode === "audit" ? (payload as AuditPayload | null) : null;
  const isHigh = normalizeCode(nearMiss?.near_miss_priority) === "HIGH" || normalizeCode(fleetAlert?.near_miss?.near_miss_priority) === "HIGH";
  const showHighLinks = isHigh || mode === "analysis" || mode === "fleet-alert";
  const closureBlockers = buildClosureBlockers({
    canClose,
    currentRole,
    hasCloseApproval,
    hasPicClose,
    nearMiss,
    preventiveMeasureDueDate: closureDraft.preventive_measure_due_date,
    preventiveMeasureOwner: closureDraft.preventive_measure_owner,
    preventiveMeasureStatus: closureDraft.preventive_measure_status,
    preventiveMeasures: closureDraft.near_miss_suggestion,
  });
  const closureDisabled = isMutating || closureBlockers.length > 0 || !closureDraft.closure_reason.trim() || !closureDraft.typed_name.trim();
  const triageBlockedByReview = nearMiss ? normalizeCode(nearMiss.state) !== "READY_FOR_DPA_TRIAGE" : true;

  const visibleLinks = useMemo(
    () =>
      lifecycleLinks(id).filter(([label]) => {
        if ((label === "Analysis" || label === "Fleet alert") && !showHighLinks) {
          return false;
        }
        if (label === "Rework" && normalizeCode(nearMiss?.state) !== "REWORK_REQUIRED") {
          return false;
        }
        return true;
      }),
    [id, nearMiss?.state, showHighLinks],
  );

  async function submitReview(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.reviewNearMiss(id, {
        comment: reviewDraft.comment,
        device_fingerprint: reviewDraft.device_fingerprint,
        decision: reviewDraft.decision,
        typed_name: reviewDraft.typed_name,
      });
      setPayload(response);
      await load();
      setResultMessage(
        reviewDraft.decision === "SEND_BACK"
          ? "Near miss sent back for rework."
          : "Near miss submitted to DPA triage.",
      );
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function submitRework(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.resubmitNearMissRework(id, {
        comment: reworkDraft.comment,
      });
      setPayload(response);
      await load();
      setResultMessage("Near miss rework submitted for vessel review.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function submitTriage(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.triageNearMiss(id, {
        near_miss_priority: triage.near_miss_priority,
        override_reason: triage.override_reason || undefined,
        supersede_to_incident: triage.supersede_to_incident,
      });
      setPayload(response);
      await load();
      setResultMessage("Near miss triage saved.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function createFact(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      await safetyApi.createNearMissAnalysisFact(id, {
        confidence: factDraft.confidence,
        fact_text: factDraft.fact_text,
        fact_timestamp: factDraft.fact_timestamp || null,
        hindsight_override_reason: factDraft.hindsight_override_reason || undefined,
        sequence_index: factDraft.sequence_index,
        source_evidence_id: factDraft.source_evidence_id,
      });
      setFactDraft((current) => ({ ...current, fact_text: "", sequence_index: current.sequence_index + 1, source_evidence_id: "" }));
      await load();
      setResultMessage("Analysis fact saved.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function createEvidenceSource(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.createNearMissAnalysisEvidence(id, {
        description: evidenceDraft.description,
        evidence_type: evidenceDraft.evidence_type,
        photo_file: evidenceDraft.photo_file || undefined,
        source_label: evidenceDraft.source_label || undefined,
        title: evidenceDraft.title,
      });
      setPayload(response);
      setEvidenceDraft({ description: "", evidence_type: "PHOTO", photo_file: null, source_label: "", title: "" });
      await load();
      setResultMessage("Evidence source saved.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function issueFleetAlert(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.issueNearMissFleetAlert(id, alertDraft);
      setPayload(response);
      await load();
      setResultMessage("Fleet alert issued.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  function openCircularWithFleetAlertDraft() {
    const sourceNearMiss = fleetAlert?.near_miss ?? nearMiss;
    const incidentNumber = sourceNearMiss?.incident_number || `NM-${id}`;
    const title = (fleetAlert?.draft?.title || `Near Miss Fleet Alert - ${incidentNumber}`).trim();
    const alertText = (alertDraft.alert_text || fleetAlert?.draft?.body || "").trim();
    const learningText = alertDraft.fleet_learning_text.trim();
    const body = [
      alertText,
      learningText ? `Fleet learning / lessons:\n${learningText}` : "",
    ]
      .filter(Boolean)
      .join("\n\n");

    window.localStorage.setItem(
      SAFETY_CIRCULAR_PREFILL_KEY,
      JSON.stringify({
        body,
        created_at: new Date().toISOString(),
        incident_number: incidentNumber,
        near_miss_id: id,
        source: "near_miss_fleet_alert",
        title,
      }),
    );
    window.location.href = "/circular/office?safety_prefill=near_miss_fleet_alert";
  }

  async function closeNearMiss(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.closeNearMiss(id, {
        closure_reason: closureDraft.closure_reason,
        conflict_acknowledged: closureDraft.conflict_acknowledged,
        conflict_approver_role: closureDraft.conflict_approver_role || undefined,
        device_fingerprint: closureDraft.device_fingerprint,
        near_miss_suggestion: closureDraft.near_miss_suggestion || undefined,
        preventive_measure_due_date: closureDraft.preventive_measure_due_date || undefined,
        preventive_measure_owner: closureDraft.preventive_measure_owner || undefined,
        preventive_measure_status: closureDraft.preventive_measure_status || undefined,
        typed_name: closureDraft.typed_name,
      });
      setPayload(response);
      await load();
      setResultMessage("Near miss closed.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function downloadPdf() {
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    try {
      downloadBlob(await safetyApi.downloadNearMissPdf(id));
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
          Safety / Near Miss
        </p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">{modeTitle(mode)}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Lightweight near-miss workflow with backend-controlled reporter masking, DPA triage, optional HIGH-priority fact analysis, fleet alert, and closure.
            </p>
          </div>
          <button className="min-h-11 rounded-full bg-slate-900 px-4 text-sm font-semibold text-white" onClick={() => void load()} type="button">
            Refresh
          </button>
        </div>
      </header>

      <nav className="flex flex-wrap gap-3" aria-label="Near-miss lifecycle">
        <Link className="inline-flex min-h-10 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to="/safety/near-miss">
          List
        </Link>
        {visibleLinks.map(([label, href]) => (
          <Link className="inline-flex min-h-10 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" key={href} to={href}>
            {label}
          </Link>
        ))}
      </nav>

      {error ? <SafetyFloatingFeedback tone="error">{error}</SafetyFloatingFeedback> : null}
      {resultMessage ? <SafetyFloatingFeedback tone="success">{resultMessage}</SafetyFloatingFeedback> : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading near-miss workspace...</section>
      ) : (
        <>
          {nearMiss ? <NearMissSummary nearMiss={nearMiss} /> : null}

          {mode === "review" ? (
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={submitReview}>
              <h2 className="text-xl font-semibold text-slate-900">Vessel-side Review</h2>
              {!canReview ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Vessel review is restricted to Master, HOD, CO, or CE with review authority.</p> : null}
              {nearMiss && normalizeCode(nearMiss.state) !== "PENDING_VESSEL_REVIEW" ? (
                <p className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                  Current state is {nearMiss.state}; vessel review is available only while the near miss is pending vessel review.
                </p>
              ) : null}
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Decision
                <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setReviewDraft((current) => ({ ...current, decision: event.target.value }))} value={reviewDraft.decision}>
                  <option value="SUBMIT_TO_OFFICE">Submit to DPA triage</option>
                  <option value="SEND_BACK">Send back for rework</option>
                </select>
              </label>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Review comment
                <textarea className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setReviewDraft((current) => ({ ...current, comment: event.target.value }))} value={reviewDraft.comment} />
              </label>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <label className="block text-sm font-medium text-slate-700">
                  Reviewer typed name
                  <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setReviewDraft((current) => ({ ...current, typed_name: event.target.value }))} value={reviewDraft.typed_name} />
                </label>
                <label className="block text-sm font-medium text-slate-700">
                  Device fingerprint
                  <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" readOnly value={reviewDraft.device_fingerprint} />
                </label>
              </div>
              <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !canReview || normalizeCode(nearMiss?.state) !== "PENDING_VESSEL_REVIEW" || (reviewDraft.decision === "SEND_BACK" && !reviewDraft.comment.trim()) || !reviewDraft.typed_name.trim() || !reviewDraft.device_fingerprint.trim()} type="submit">
                {isMutating ? "Saving..." : "Save vessel review"}
              </button>
            </form>
          ) : null}

          {mode === "rework" ? (
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={submitRework}>
              <h2 className="text-xl font-semibold text-slate-900">Submit Rework</h2>
              {!canSubmitRework ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Rework submission requires near-miss create permission.</p> : null}
              {nearMiss && normalizeCode(nearMiss.state) !== "REWORK_REQUIRED" ? (
                <p className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                  Current state is {nearMiss.state}; rework is available only after vessel review sends the near miss back.
                </p>
              ) : null}
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Rework note
                <textarea className="mt-2 min-h-32 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setReworkDraft((current) => ({ ...current, comment: event.target.value }))} value={reworkDraft.comment} />
              </label>
              <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !canSubmitRework || normalizeCode(nearMiss?.state) !== "REWORK_REQUIRED" || !reworkDraft.comment.trim()} type="submit">
                {isMutating ? "Submitting..." : "Submit rework"}
              </button>
            </form>
          ) : null}

          {mode === "triage" ? (
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={submitTriage}>
              <h2 className="text-xl font-semibold text-slate-900">DPA Triage</h2>
              {!canTriage ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Triage requires DPA role and SAF_P_002.</p> : null}
              {triageBlockedByReview ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Vessel-side review must submit this near miss to office before DPA triage.</p> : null}
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <label className="block text-sm font-medium text-slate-700">
                  Priority
                  <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setTriage((current) => ({ ...current, near_miss_priority: event.target.value }))} value={triage.near_miss_priority}>
                    {PRIORITIES.map((priority) => <option key={priority} value={priority}>{priority}</option>)}
                  </select>
                </label>
                <label className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700">
                  <input checked={triage.supersede_to_incident} disabled={triage.near_miss_priority !== "HIGH"} onChange={(event) => setTriage((current) => ({ ...current, supersede_to_incident: event.target.checked }))} type="checkbox" />
                  Supersede to incident
                </label>
              </div>
              {triage.supersede_to_incident ? (
                <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                  Superseding will create an Incident record and stop this Near Miss from continuing in the lightweight workflow. Enter the DPA reason below.
                </p>
              ) : null}
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Override / triage reason
                <textarea className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setTriage((current) => ({ ...current, override_reason: event.target.value }))} value={triage.override_reason} />
              </label>
              <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !canTriage || triageBlockedByReview} type="submit">
                {isMutating ? "Saving..." : "Submit triage"}
              </button>
            </form>
          ) : null}

          {mode === "analysis" ? (
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(380px,0.8fr)]">
              <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="text-xl font-semibold text-slate-900">Fact Tree</h2>
                <div className="mt-4 space-y-3">
                  {(analysis?.facts ?? []).map((fact) => (
                    <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4" key={fact.id}>
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <h3 className="font-semibold text-slate-900">Fact {fact.sequence_index}</h3>
                        <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">{fact.confidence}</span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-700">{fact.fact_text}</p>
                      <p className="mt-2 text-xs text-slate-500">{fact.evidence_summary ?? `Evidence #${fact.source_evidence_id}`}</p>
                      {fact.evidence_preview?.preview_url ? (
                        <EvidencePreviewImage preview={fact.evidence_preview} />
                      ) : null}
                    </article>
                  ))}
                  {(analysis?.facts ?? []).length === 0 ? <p className="text-sm text-slate-500">No analysis facts have been created.</p> : null}
                </div>
                <form className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4" onSubmit={createEvidenceSource}>
                  <h3 className="font-semibold text-slate-900">Add Evidence Source</h3>
                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Evidence type
                      <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setEvidenceDraft((current) => ({ ...current, evidence_type: event.target.value }))} value={evidenceDraft.evidence_type}>
                        <option value="PHOTO">Photo</option>
                        <option value="WITNESS_NOTE">Witness note</option>
                        <option value="CHECKLIST_ENTRY">Checklist entry</option>
                        <option value="DOCUMENT">Document</option>
                        <option value="OTHER">Other</option>
                      </select>
                    </label>
                    {evidenceDraft.evidence_type === "PHOTO" ? (
                      <label className="block text-sm font-medium text-slate-700">
                        Attach image
                        <input
                          accept="image/png,image/jpeg"
                          className="mt-2 block min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm"
                          onChange={(event) => setEvidenceDraft((current) => ({ ...current, photo_file: event.target.files?.[0] ?? null }))}
                          type="file"
                        />
                      </label>
                    ) : null}
                    <label className="block text-sm font-medium text-slate-700">
                      Title
                      <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setEvidenceDraft((current) => ({ ...current, title: event.target.value }))} value={evidenceDraft.title} />
                    </label>
                  </div>
                  <label className="mt-4 block text-sm font-medium text-slate-700">
                    Source label
                    <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setEvidenceDraft((current) => ({ ...current, source_label: event.target.value }))} value={evidenceDraft.source_label} />
                  </label>
                  <label className="mt-4 block text-sm font-medium text-slate-700">
                    Description
                    <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setEvidenceDraft((current) => ({ ...current, description: event.target.value }))} value={evidenceDraft.description} />
                  </label>
                  <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !canAnalyze || !evidenceDraft.title.trim() || !evidenceDraft.description.trim() || (evidenceDraft.evidence_type === "PHOTO" && !evidenceDraft.photo_file)} type="submit">
                    {isMutating ? "Saving..." : "Save evidence source"}
                  </button>
                </form>
              </section>
              <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={createFact}>
                <h2 className="text-xl font-semibold text-slate-900">Add Fact</h2>
                {!canAnalyze ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Fact edits require SAF_P_002 and an investigation role.</p> : null}
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Sequence
                    <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" min={1} onChange={(event) => setFactDraft((current) => ({ ...current, sequence_index: Number(event.target.value) }))} type="number" value={factDraft.sequence_index} />
                  </label>
                  <label className="block text-sm font-medium text-slate-700">
                    Confidence
                    <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setFactDraft((current) => ({ ...current, confidence: event.target.value }))} value={factDraft.confidence}>
                      {CONFIDENCE.map((confidence) => <option key={confidence} value={confidence}>{confidence}</option>)}
                    </select>
                  </label>
                </div>
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Source evidence
                  <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setFactDraft((current) => ({ ...current, source_evidence_id: event.target.value }))} value={factDraft.source_evidence_id}>
                    <option value="">Select evidence source</option>
                    {evidenceSources.map((source) => (
                      <option key={`${source.source_type}-${source.public_id ?? source.id}`} value={source.public_id ?? source.id}>
                        {source.label}
                      </option>
                    ))}
                  </select>
                </label>
                {evidenceSources.length === 0 ? (
                  <p className="mt-2 rounded-2xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                    No evidence source is available yet. Refresh the analysis page so the near-miss report narrative can be registered as the default evidence source.
                  </p>
                ) : null}
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Fact
                  <textarea className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setFactDraft((current) => ({ ...current, fact_text: event.target.value }))} value={factDraft.fact_text} />
                </label>
                <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !canAnalyze || !factDraft.fact_text.trim() || !factDraft.source_evidence_id} type="submit">
                  {isMutating ? "Saving..." : "Create fact"}
                </button>
              </form>
            </div>
          ) : null}

          {mode === "fleet-alert" ? (
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={issueFleetAlert}>
              <h2 className="text-xl font-semibold text-slate-900">Fleet Alert</h2>
              {!canIssueFleetAlert ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Fleet alert issue requires DPA role and SAF_P_024.</p> : null}
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Issued</p>
                  <p className="mt-2 font-semibold text-slate-900">{fleetAlert?.issued ? "Yes" : "No"}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">7-day SLA</p>
                  <p className={`mt-2 font-semibold ${fleetAlert?.sla?.overdue ? "text-rose-700" : "text-slate-900"}`}>{fleetAlert?.sla?.status ?? "Pending"}</p>
                  <p className="mt-1 text-xs text-slate-500">{fleetAlert?.sla?.due_by ?? fleetAlert?.draft?.due_by ?? "No due date"}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 md:col-span-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Recipients</p>
                  <p className="mt-2 text-sm text-slate-700">{recipientLabels.join(", ") || (fleetAlert?.recipients ?? []).join(", ") || "Not resolved"}</p>
                </div>
              </div>
              {(fleetAlert?.recipient_vessels ?? []).length > 0 ? (
                <section className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-900">Select recipient vessels</p>
                  <div className="mt-3 grid gap-2 md:grid-cols-2">
                    {(fleetAlert?.recipient_vessels ?? []).map((recipient) => (
                      <label className="inline-flex items-center gap-2 text-sm text-slate-700" key={recipient.vessel_id}>
                        <input
                          checked={alertDraft.recipient_vessel_ids.includes(recipient.vessel_id)}
                          onChange={(event) =>
                            setAlertDraft((current) => ({
                              ...current,
                              recipient_vessel_ids: event.target.checked
                                ? Array.from(new Set([...current.recipient_vessel_ids, recipient.vessel_id]))
                                : current.recipient_vessel_ids.filter((vesselId) => vesselId !== recipient.vessel_id),
                            }))
                          }
                          type="checkbox"
                        />
                        {recipient.vessel_code ? `${recipient.vessel_code} - ` : ""}
                        {recipient.display_name || recipient.vessel_name || recipient.vessel_id}
                      </label>
                    ))}
                  </div>
                </section>
              ) : null}
              {fleetAlert?.sla?.overdue && !fleetAlert.issued ? (
                <label className="mt-4 block text-sm font-medium text-slate-700">
                  Late fleet alert extension reason
                  <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-rose-300 p-3" onChange={(event) => setAlertDraft((current) => ({ ...current, sla_extension_reason: event.target.value }))} value={alertDraft.sla_extension_reason} />
                </label>
              ) : null}
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Alert text
                <textarea className="mt-2 min-h-40 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setAlertDraft((current) => ({ ...current, alert_text: event.target.value }))} value={alertDraft.alert_text} />
              </label>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Fleet learning / lessons
                <textarea className="mt-2 min-h-32 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setAlertDraft((current) => ({ ...current, fleet_learning_text: event.target.value }))} value={alertDraft.fleet_learning_text} />
              </label>
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Issue Circular/Alert</p>
                <p className="mt-1 text-sm text-slate-600">
                  Prepare a Circular/Alert from the current alert text. Only title and body are filled; DPA completes the remaining Circular fields and publishes from the Circular page.
                </p>
                <button className="mt-3 min-h-11 rounded-full border border-slate-300 bg-white px-5 text-sm font-semibold text-slate-900 disabled:bg-slate-100 disabled:text-slate-400" disabled={!alertDraft.alert_text.trim()} onClick={openCircularWithFleetAlertDraft} type="button">
                  Issue Circular/Alert
                </button>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <label className="block text-sm font-medium text-slate-700">
                  Typed name
                  <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setAlertDraft((current) => ({ ...current, typed_name: event.target.value }))} value={alertDraft.typed_name} />
                </label>
              </div>
              <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !canIssueFleetAlert || !alertDraft.alert_text.trim() || !alertDraft.fleet_learning_text.trim() || !alertDraft.typed_name.trim() || alertDraft.recipient_vessel_ids.length === 0 || Boolean(fleetAlert?.sla?.overdue && !fleetAlert.issued && !alertDraft.sla_extension_reason.trim())} type="submit">
                {isMutating ? "Issuing..." : "Issue fleet alert"}
              </button>
            </form>
          ) : null}

          {mode === "closure" ? (
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={closeNearMiss}>
              <h2 className="text-xl font-semibold text-slate-900">Close Near Miss</h2>
              {closureBlockers.length > 0 ? (
                <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                  <p className="font-semibold">Resolve before closing:</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5">
                    {closureBlockers.map((blocker) => (
                      <li key={blocker}>{blocker}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {isHigh ? <p className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">HIGH-priority closure requires preventive measures, completed fact analysis, and an issued fleet alert. The system enforces all three checks.</p> : null}
              {isHigh ? (
                <section className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <label className="block text-sm font-medium text-slate-700">
                    Preventive measures
                    <textarea className="mt-2 min-h-32 w-full rounded-2xl border border-slate-300 bg-white p-3" onChange={(event) => setClosureDraft((current) => ({ ...current, near_miss_suggestion: event.target.value }))} value={closureDraft.near_miss_suggestion} />
                  </label>
                  <div className="mt-4 grid gap-4 md:grid-cols-3">
                    <label className="block text-sm font-medium text-slate-700">
                      Owner
                      <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3" onChange={(event) => setClosureDraft((current) => ({ ...current, preventive_measure_owner: event.target.value }))} value={closureDraft.preventive_measure_owner} />
                    </label>
                    <label className="block text-sm font-medium text-slate-700">
                      Due date
                      <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3" onChange={(event) => setClosureDraft((current) => ({ ...current, preventive_measure_due_date: event.target.value }))} type="date" value={closureDraft.preventive_measure_due_date} />
                    </label>
                    <label className="block text-sm font-medium text-slate-700">
                      Status
                      <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3" onChange={(event) => setClosureDraft((current) => ({ ...current, preventive_measure_status: event.target.value }))} value={closureDraft.preventive_measure_status}>
                        <option value="OPEN">Open</option>
                        <option value="IN_PROGRESS">In progress</option>
                        <option value="CLOSED">Closed</option>
                      </select>
                    </label>
                  </div>
                </section>
              ) : null}
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Closure reason
                <textarea className="mt-2 min-h-36 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setClosureDraft((current) => ({ ...current, closure_reason: event.target.value }))} value={closureDraft.closure_reason} />
              </label>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <label className="block text-sm font-medium text-slate-700">
                  Typed name
                  <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setClosureDraft((current) => ({ ...current, typed_name: event.target.value }))} value={closureDraft.typed_name} />
                </label>
              </div>
              <section className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <label className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                  <input checked={closureDraft.conflict_acknowledged} onChange={(event) => setClosureDraft((current) => ({ ...current, conflict_acknowledged: event.target.checked }))} type="checkbox" />
                  Self-report conflict acknowledged
                </label>
                <label className="mt-3 block text-sm font-medium text-slate-700">
                  Conflict approver role
                  <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setClosureDraft((current) => ({ ...current, conflict_approver_role: event.target.value }))} value={closureDraft.conflict_approver_role}>
                    {CONFLICT_APPROVER_ROLES.map((approverRole) => (
                      <option key={approverRole || "blank"} value={approverRole}>
                        {approverRole || "Not applicable"}
                      </option>
                    ))}
                  </select>
                </label>
              </section>
              <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={closureDisabled} type="submit">
                {isMutating ? "Closing..." : "Close near miss"}
              </button>
            </form>
          ) : null}

          {mode === "audit" ? <NearMissAudit audit={audit} /> : null}

          {mode === "pdf" ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">PDF Export</h2>
              <p className="mt-2 text-sm text-slate-600">The PDF is generated by the backend with reporter masking applied by serializer policy.</p>
              <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating} onClick={() => void downloadPdf()} type="button">
                {isMutating ? "Preparing..." : "Download near-miss PDF"}
              </button>
            </section>
          ) : null}
        </>
      )}
    </section>
  );
}

function EvidencePreviewImage({ preview }: { preview: EvidencePreview }) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let objectUrl: string | null = null;

    async function loadImage() {
      setFailed(false);
      setImageUrl(null);
      try {
        const blob = await safetyApi.downloadNearMissEvidencePhoto(preview.preview_url);
        objectUrl = URL.createObjectURL(blob);
        if (isMounted) {
          setImageUrl(objectUrl);
        } else {
          URL.revokeObjectURL(objectUrl);
        }
      } catch {
        if (isMounted) {
          setFailed(true);
        }
      }
    }

    void loadImage();
    return () => {
      isMounted = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [preview.preview_url]);

  const label = preview.title || preview.file_name || "Photo evidence";
  return (
    <figure className="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white">
      {imageUrl ? (
        <img alt={label} className="max-h-64 w-full object-contain" src={imageUrl} />
      ) : (
        <div className="flex min-h-28 items-center justify-center px-3 py-6 text-sm text-slate-500">
          {failed ? "Photo preview unavailable." : "Loading photo preview..."}
        </div>
      )}
      <figcaption className="border-t border-slate-200 px-3 py-2 text-xs text-slate-500">{label}</figcaption>
    </figure>
  );
}

function extractNearMiss(payload: unknown): NearMissRecord | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const record = payload as Record<string, unknown>;
  if (record.near_miss && typeof record.near_miss === "object") {
    return record.near_miss as NearMissRecord;
  }
  if (record.id || record.incident_number || record.record_type === "NEAR_MISS") {
    return record as unknown as NearMissRecord;
  }
  return null;
}

function NearMissSummary({ nearMiss }: { nearMiss: NearMissRecord }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">{nearMiss.incident_number ?? `#${nearMiss.id}`}</span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{nearMiss.state}</span>
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">{nearMiss.near_miss_priority ?? "Pending triage"}</span>
      </div>
      <dl className="mt-4 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Vessel</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{formatVesselName(nearMiss)}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Occurred</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{nearMiss.occurred_at ?? "Not recorded"}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Reporter</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{nearMiss.reporter_name ?? "Masked"}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Severity</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{nearMiss.near_miss_severity ?? "Not selected"}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">SHELL</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{nearMiss.near_miss_shell_tag ?? "Not tagged"}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">M-SCAT</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{nearMiss.near_miss_mscat_subcode_id ?? "Not selected"}</dd>
        </div>
      </dl>
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Narrative</p>
        <p className="mt-2 text-sm leading-6 text-slate-700">{nearMiss.narrative ?? "No narrative available."}</p>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Immediate action</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{nearMiss.near_miss_immediate_action ?? "Not recorded."}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Suggestion</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{nearMiss.near_miss_suggestion ?? "Not recorded."}</p>
        </div>
      </div>
    </section>
  );
}

function NearMissAudit({ audit }: { audit: AuditPayload | null }) {
  return (
    <section className="grid gap-6 xl:grid-cols-2">
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900">Phase Log</h2>
        <div className="mt-4 space-y-3">
          {(audit?.phase_log ?? []).map((row) => (
            <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4" key={row.id}>
              <p className="font-semibold text-slate-900">{row.transition_type}</p>
              <p className="mt-2 text-sm text-slate-600">{row.actor_role_code} / {row.actor_user_id} / {row.occurred_at}</p>
            </article>
          ))}
          {(audit?.phase_log ?? []).length === 0 ? <p className="text-sm text-slate-500">No phase-log rows available.</p> : null}
        </div>
      </div>
      <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900">Field History</h2>
        <div className="mt-4 space-y-3">
          {(audit?.field_history ?? []).map((row) => (
            <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4" key={row.id}>
              <p className="font-semibold text-slate-900">{row.field_name}</p>
              <p className="mt-2 text-sm text-slate-600">{row.actor_role_code} / {row.actor_user_id} / {row.changed_at}</p>
            </article>
          ))}
          {(audit?.field_history ?? []).length === 0 ? <p className="text-sm text-slate-500">No field-history rows available.</p> : null}
        </div>
      </div>
    </section>
  );
}

export default SafetyNearMissWorkspace;
