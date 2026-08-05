import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../../hooks/use-auth";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import { getSafetyDeviceFingerprint, resolveSignatureTypedName } from "../../../lib/safety/digital-signature";
import { formatVesselName } from "../../../lib/safety/vessel-display";
import {
  SAFETY_NEAR_MISS_CAUSE_FACTORS,
  SAFETY_NEAR_MISS_OTHER_CATEGORY,
  SAFETY_NEAR_MISS_OTHER_MAX_LENGTH,
  SAFETY_NEAR_MISS_OTHER_PREFIX,
  SAFETY_NEAR_MISS_SCHEMA_VERSION,
  type SafetyNearMissSubmitValues,
  type SafetyNearMissValues,
} from "../../../schemas/safety/near-miss";
import SafetyFloatingFeedback from "../shared/safety-floating-feedback";
import { SafetyNearMissForm } from "./near-miss-form";

type NearMissMode = "detail" | "review" | "rework" | "office-comments" | "fleet-alert" | "closure" | "audit" | "pdf";
const SAFETY_CIRCULAR_PREFILL_KEY = "safetyCircularPrefill";

interface NearMissRecord {
  id: string;
  incident_number: string | null;
  incident_type_id?: number | null;
  loss_type_primary_id?: number | null;
  vessel_id: string;
  state: string;
  current_phase?: number;
  occurred_at?: string | null;
  reported_at?: string | null;
  near_miss_immediate_action?: string | null;
  near_miss_mscat_subcode_id?: string | null;
  near_miss_mscat_category_id?: number | null;
  narrative?: string | null;
  near_miss_priority?: "LOW" | "MEDIUM" | "HIGH" | string | null;
  near_miss_severity?: "HIGH" | "MED" | "LOW" | string | null;
  near_miss_place?: "AT_ANCHOR" | "AT_SEA" | "AT_PORT" | string | null;
  near_miss_shell_tag?: string | null;
  near_miss_category_tags?: string[];
  near_miss_incident_type_ids?: number[];
  near_miss_suggestion?: string | null;
  near_miss_mscat_subcode_ids?: string[];
  near_miss_factor_causes?: SafetyNearMissValues["near_miss_factor_causes"];
  near_miss_root_cause_detail?: string | null;
  near_miss_corrective_action?: string | null;
  near_miss_weather_voyage_details?: string | null;
  near_miss_equipment_details?: string | null;
  near_miss_lessons_learned?: string | null;
  reporter_name?: string | null;
  reporter_rank?: string | null;
  reporter_user_id?: string | null;
  vessel_code?: string | null;
  vessel_display_name?: string | null;
  vessel_name?: string | null;
  visibility_rule?: string;
  closure_reason?: string | null;
  closed_at?: string | null;
  office_comment?: string | null;
  evidence_attachments?: NearMissEvidenceAttachment[];
  rework_summary?: {
    comment?: string | null;
    requested_at?: string | null;
    requested_by?: string | null;
    requested_by_role?: string | null;
  } | null;
  vessel_review_summary?: {
    comment?: string | null;
    decision?: string | null;
    reviewed_at?: string | null;
    reviewed_by?: string | null;
    reviewed_by_role?: string | null;
    typed_name?: string | null;
  } | null;
}

interface NearMissEvidenceAttachment {
  id: string;
  title?: string | null;
  description?: string | null;
  file_name?: string | null;
  content_type?: string | null;
  byte_size?: number | null;
  uploaded_at?: string | null;
  high_severity_required?: boolean;
  preview_url?: string | null;
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
  near_miss?: NearMissRecord;
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
    id: string;
    phase_from: number | null;
    phase_to: number;
    transition_type: string;
    actor_user_id: string;
    actor_role_code: string;
    occurred_at: string;
  }>;
  field_history?: Array<{
    id: string;
    field_name: string;
    old_value?: unknown;
    actor_user_id: string;
    actor_role_code: string;
    change_reason?: string | null;
    changed_at: string;
    new_value: unknown;
  }>;
}

const PRIORITIES = ["LOW", "MEDIUM", "HIGH"] as const;
const READY_FOR_OFFICE_COMMENTS_STATE = "READY_FOR_OFFICE_COMMENTS";
const OFFICE_COMMENTS_COMPLETED_STATE = "OFFICE_COMMENTS_COMPLETED";
const REJECTED_STATE = "REJECTED";
const VESSEL_REVIEW_ROLES = new Set(["MASTER", "CAPTAIN", "CO", "CE", "HOD", "CHIEF OFFICER", "CHIEF ENGINEER", "HEAD OF DEPARTMENT"]);
const HIGH_PRIORITY_CLOSE_ROLES = new Set(["DPA", "FM", "FLEET MANAGER"]);
const OFFICE_COMMENT_PIC_ROLES = new Set(["PIC", "OFFICE_PIC", "OFFICE_SSQE", "OFFICE_SUPT", "VESSEL SUPERINTENDENT"]);
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

function formatNearMissState(value: unknown) {
  const state = normalizeCode(value);
  switch (state) {
    case READY_FOR_OFFICE_COMMENTS_STATE:
      return "Ready for Office Comments";
    case OFFICE_COMMENTS_COMPLETED_STATE:
      return "Office Comments Completed";
    case "PENDING_VESSEL_REVIEW":
      return "Pending Vessel Review";
    case "REWORK_REQUIRED":
      return "Rework Required";
    case REJECTED_STATE:
      return "Rejected";
    default:
      return state ? state.replace(/_/g, " ") : "Not recorded";
  }
}

function buildOfficeReworkSummary({
  categoryChanged,
  categoryReason,
  currentCategory,
  currentPriority,
  immediateCause,
  officeComment,
  priorityChanged,
  priorityReason,
  suggestedCategory,
  suggestedPriority,
}: {
  categoryChanged: boolean;
  categoryReason: string;
  currentCategory?: string | null;
  currentPriority?: string | null;
  immediateCause?: string | null;
  officeComment: string;
  priorityChanged: boolean;
  priorityReason: string;
  suggestedCategory?: string | null;
  suggestedPriority: string;
}) {
  const parts = [
    officeComment.trim() ? `Office comment: ${officeComment.trim()}` : "",
    priorityChanged ? `Suggested priority: ${normalizeCode(currentPriority || "LOW") || "Not selected"} -> ${suggestedPriority}` : "",
    priorityChanged && priorityReason.trim() ? `Reason for priority change: ${priorityReason.trim()}` : "",
    categoryChanged ? `Suggested category: ${currentCategory || "Not selected"} -> ${suggestedCategory || "Not selected"}` : "",
    categoryChanged && categoryReason.trim() ? `Reason for category change: ${categoryReason.trim()}` : "",
    immediateCause ? `Suggested immediate cause: ${immediateCause}` : "",
  ].filter(Boolean);
  return parts.join("\n");
}

function asNumberList(values: unknown, fallback?: number | null) {
  const list = Array.isArray(values) ? values : [];
  const cleaned = list
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value) && value > 0);
  if (cleaned.length) {
    return Array.from(new Set(cleaned)).slice(0, 3);
  }
  return fallback ? [fallback] : [];
}

function asStringList(values: unknown, fallback?: string | null) {
  const list = Array.isArray(values) ? values : [];
  const cleaned = list
    .map((value) => String(value ?? "").trim())
    .filter(Boolean);
  if (cleaned.length) {
    return Array.from(new Set(cleaned)).slice(0, 3);
  }
  return fallback?.trim() ? [fallback.trim()] : [];
}

function formatOtherCategory(value: string) {
  const cleaned = value.trim().replace(/\s+/g, " ");
  return cleaned ? `${SAFETY_NEAR_MISS_OTHER_PREFIX} ${cleaned}` : "";
}

function buildReworkInitialValues(nearMiss: NearMissRecord): Partial<SafetyNearMissValues> {
  const incidentTypeIds = asNumberList(nearMiss.near_miss_incident_type_ids, nearMiss.incident_type_id ?? null);
  const categoryTags = asStringList(nearMiss.near_miss_category_tags, nearMiss.near_miss_shell_tag);
  const immediateCauseIds = asStringList(nearMiss.near_miss_mscat_subcode_ids, nearMiss.near_miss_mscat_subcode_id);

  return {
    incident_type_id: incidentTypeIds[0] ?? null,
    loss_type_primary_id: nearMiss.loss_type_primary_id ?? null,
    narrative: nearMiss.narrative ?? "",
    near_miss_immediate_action: nearMiss.near_miss_immediate_action ?? "",
    near_miss_place: (nearMiss.near_miss_place || null) as SafetyNearMissValues["near_miss_place"],
    near_miss_category_tags: categoryTags as SafetyNearMissValues["near_miss_category_tags"],
    near_miss_incident_type_ids: incidentTypeIds,
    near_miss_mscat_category_id: nearMiss.near_miss_mscat_category_id ?? null,
    near_miss_mscat_subcode_id: nearMiss.near_miss_mscat_subcode_id ?? null,
    near_miss_mscat_subcode_ids: immediateCauseIds,
    near_miss_factor_causes: nearMiss.near_miss_factor_causes ?? [],
    near_miss_severity: (nearMiss.near_miss_severity || null) as SafetyNearMissValues["near_miss_severity"],
    near_miss_shell_tag: (categoryTags[0] ?? null) as SafetyNearMissValues["near_miss_shell_tag"],
    near_miss_suggestion: nearMiss.near_miss_suggestion ?? "",
    near_miss_root_cause_detail: nearMiss.near_miss_root_cause_detail ?? "",
    near_miss_corrective_action: nearMiss.near_miss_corrective_action ?? "",
    near_miss_weather_voyage_details: nearMiss.near_miss_weather_voyage_details ?? "",
    near_miss_equipment_details: nearMiss.near_miss_equipment_details ?? "",
    near_miss_lessons_learned: nearMiss.near_miss_lessons_learned ?? "",
    occurred_at: nearMiss.occurred_at ?? "",
    reporter_device_fingerprint: nearMiss.reporter_device_fingerprint || getSafetyDeviceFingerprint(),
    reporter_name: nearMiss.reporter_name ?? "",
    reporter_rank: nearMiss.reporter_rank ?? "",
    reporter_user_id: nearMiss.reporter_user_id ?? "",
    schema_version: SAFETY_NEAR_MISS_SCHEMA_VERSION,
    vessel_code: nearMiss.vessel_code ?? undefined,
    vessel_id: nearMiss.vessel_id,
  };
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
}: {
  canClose: boolean;
  currentRole: string;
  hasCloseApproval: boolean;
  hasPicClose: boolean;
  nearMiss: NearMissRecord | null;
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
  } else if (state !== OFFICE_COMMENTS_COMPLETED_STATE) {
    blockers.push("Office comments must be completed before closure.");
  }

  if (priority === "HIGH") {
    if (!HIGH_PRIORITY_CLOSE_ROLES.has(currentRole)) {
      blockers.push("HIGH-priority near miss closure is DPA/FM only.");
    }
    if (!hasCloseApproval) {
      blockers.push("HIGH-priority near miss closure is not available for your login.");
    }
  } else if (priority === "LOW" || priority === "MEDIUM") {
    if (!LOW_PRIORITY_CLOSE_ROLES.has(currentRole)) {
      blockers.push("LOW/MEDIUM-priority near miss closure is restricted to Master, PIC, DPA, or FM authority.");
    }
    if (!canClose || (!hasCloseApproval && !hasPicClose)) {
      blockers.push("LOW/MEDIUM-priority near miss closure is not available for your login.");
    }
  } else {
    blockers.push("Near miss priority must be LOW, MEDIUM, or HIGH before closure.");
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
    ["Vessel Review", `/safety/near-miss/${id}/review`],
    ["Rework", `/safety/near-miss/${id}/rework`],
    ["Office Comments", `/safety/near-miss/${id}/office-comments`],
    ["Closure", `/safety/near-miss/${id}/closure`],
    ["Fleet alert", `/safety/near-miss/${id}/fleet-alert`],
    ["History", `/safety/near-miss/${id}/audit`],
    ["PDF", `/safety/near-miss/${id}/pdf`],
  ] as const;
}

function modeTitle(mode: NearMissMode) {
  switch (mode) {
    case "review":
      return "Near Miss Vessel Review";
    case "rework":
      return "Near Miss Rework";
    case "office-comments":
      return "Near Miss Office Comments";
    case "fleet-alert":
      return "Near Miss Fleet Alert";
    case "closure":
      return "Near Miss Closure";
    case "audit":
      return "Near Miss History";
    case "pdf":
      return "Near Miss PDF Export";
    default:
      return "Near Miss Detail";
  }
}

export function SafetyNearMissWorkspace({ mode }: { mode: NearMissMode }) {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
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
  const [nearMissCategoryOptions, setNearMissCategoryOptions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [resultMessage, setResultMessage] = useState<string | null>(initialResultMessage);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [triage, setTriage] = useState({
    near_miss_priority: "LOW",
    category_tag_change_reason: "",
    override_reason: "",
    priority_change_reason: "",
    supersede_to_incident: false,
  });
  const [showOfficeOtherCategoryInput, setShowOfficeOtherCategoryInput] = useState(false);
  const [officeOtherCategoryText, setOfficeOtherCategoryText] = useState("");
  const [reclassificationDraft, setReclassificationDraft] = useState({
    near_miss_shell_tag: "",
    reason: "",
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
    typed_name: signatureTypedName,
  }));

  const currentRole = resolveAuthorityRole(user, role);
  const canAcceptOfficeComment = (currentRole === "DPA" && hasProcess("SAF_P_002"))
    || (OFFICE_COMMENT_PIC_ROLES.has(currentRole) && hasProcess("SAF_P_006"));
  const canSendBackOfficeComment = (currentRole === "DPA" && hasProcess("SAF_P_002"))
    || (OFFICE_COMMENT_PIC_ROLES.has(currentRole) && hasProcess("SAF_P_006"));
  const canRejectOfficeComment = canSendBackOfficeComment;
  const canReview = VESSEL_REVIEW_ROLES.has(currentRole) && (hasProcess("SAF_P_002") || hasProcess("SAF_P_006"));
  const canSubmitRework = hasProcess("SAF_P_001");
  const canIssueFleetAlert = currentRole === "DPA" && hasProcess("SAF_P_024");
  const hasCloseApproval = hasProcess("SAF_P_004");
  const hasPicClose = hasProcess("SAF_P_006");
  const canClose = hasCloseApproval || hasPicClose;
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
      if (mode === "fleet-alert") {
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
      if (nearMiss) {
        setReclassificationDraft((current) => ({
          ...current,
          near_miss_shell_tag: nearMiss.near_miss_shell_tag ?? "",
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
    let cancelled = false;
    safetyApi
      .getNearMissCategories()
      .then((categories) => {
        if (!cancelled) {
          setNearMissCategoryOptions(
            categories
              .filter((category) => category.active)
              .sort((left, right) => left.display_order - right.display_order)
              .map((category) => category.category_name),
          );
        }
      })
      .catch(() => {
        if (!cancelled) {
          setNearMissCategoryOptions([]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

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
  const fleetAlert = mode === "fleet-alert" ? (payload as FleetAlertPayload | null) : null;
  const recipientLabels = (fleetAlert?.recipient_vessels ?? []).map((recipient) => {
    const code = recipient.vessel_code ? `${recipient.vessel_code} - ` : "";
    return `${code}${recipient.display_name || recipient.vessel_name || recipient.vessel_id}`;
  });
  const audit = mode === "audit" ? (payload as AuditPayload | null) : null;
  const isHigh = normalizeCode(nearMiss?.near_miss_priority) === "HIGH" || normalizeCode(fleetAlert?.near_miss?.near_miss_priority) === "HIGH";
  const showHighLinks = isHigh || mode === "fleet-alert";
  const closureBlockers = buildClosureBlockers({
    canClose,
    currentRole,
    hasCloseApproval,
    hasPicClose,
    nearMiss,
  });
  const closureDisabled = isMutating || closureBlockers.length > 0 || !closureDraft.closure_reason.trim() || !closureDraft.typed_name.trim();
  const nearMissState = normalizeCode(nearMiss?.state);
  const officeCommentsCompleted = nearMissState === OFFICE_COMMENTS_COMPLETED_STATE;
  const triageBlockedByReview = nearMiss ? ![READY_FOR_OFFICE_COMMENTS_STATE, OFFICE_COMMENTS_COMPLETED_STATE].includes(nearMissState) : true;
  const officePriorityChanged = nearMiss
    ? triage.near_miss_priority !== normalizeCode(nearMiss.near_miss_priority || "LOW")
    : false;
  const officeCategoryChanged = nearMiss
    ? (reclassificationDraft.near_miss_shell_tag || "") !== (nearMiss.near_miss_shell_tag || "")
    : false;
  const categoryChangeReasonMissing = officeCategoryChanged && !triage.category_tag_change_reason.trim();
  const supersedeReasonMissing = triage.supersede_to_incident && !triage.override_reason.trim();
  const officeReasonMissing = categoryChangeReasonMissing || supersedeReasonMissing;
  const officeReworkReasonMissing = !triage.override_reason.trim() || categoryChangeReasonMissing;
  const reworkAvailableForState = nearMissState === "REWORK_REQUIRED" || nearMissState === REJECTED_STATE;

  const visibleLinks = useMemo(
    () =>
      lifecycleLinks(id).filter(([label]) => {
        if (label === "Fleet alert" && !showHighLinks) {
          return false;
        }
        if (label === "Vessel Review" && nearMissState !== "PENDING_VESSEL_REVIEW") {
          return false;
        }
        if (label === "Rework" && !reworkAvailableForState) {
          return false;
        }
        return true;
      }),
    [id, nearMissState, reworkAvailableForState, showHighLinks],
  );

  async function submitReview(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    if (nearMissState === READY_FOR_OFFICE_COMMENTS_STATE || nearMissState === OFFICE_COMMENTS_COMPLETED_STATE) {
      navigate(`/safety/near-miss/${id}/office-comments`, {
        state: { resultMessage: "This near miss has completed vessel review. Continue in Office Comments." },
      });
      return;
    }
    if (nearMissState !== "PENDING_VESSEL_REVIEW") {
      setError("Vessel review is not available for the current near-miss state.");
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
          : "Near miss submitted to office comments.",
      );
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function submitRework(values: SafetyNearMissSubmitValues) {
    if (!id) {
      return;
    }
    if (!canSubmitRework || !reworkAvailableForState) {
      setError("Rework submission is not available for the current near-miss state or login.");
      return;
    }
    if (!reworkDraft.comment.trim()) {
      setError("Enter the rework summary before submitting.");
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.resubmitNearMissRework(id, {
        ...values,
        comment: reworkDraft.comment,
      });
      setPayload(response);
      await load();
      setResultMessage(
        normalizeCode((response as NearMissRecord).state) === READY_FOR_OFFICE_COMMENTS_STATE
          ? "Near miss rework submitted to office comments."
          : "Near miss rework submitted for vessel review.",
      );
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
        near_miss_shell_tag: reclassificationDraft.near_miss_shell_tag || undefined,
        category_tag_change_reason: triage.category_tag_change_reason || undefined,
        office_comment: triage.override_reason || undefined,
        override_reason: triage.override_reason || undefined,
        priority_change_reason: triage.priority_change_reason || undefined,
        reason: triage.override_reason || undefined,
        supersede_to_incident: triage.supersede_to_incident,
      });
      setPayload(response);
      await load();
      setResultMessage("Office comments saved.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function sendOfficeRework() {
    if (!id) {
      return;
    }
    const officeComment = buildOfficeReworkSummary({
      categoryChanged: officeCategoryChanged,
      categoryReason: triage.category_tag_change_reason,
      currentCategory: nearMiss?.near_miss_shell_tag,
      currentPriority: nearMiss?.near_miss_priority,
      officeComment: triage.override_reason,
      priorityChanged: officePriorityChanged,
      priorityReason: triage.priority_change_reason,
      suggestedCategory: reclassificationDraft.near_miss_shell_tag,
      suggestedPriority: triage.near_miss_priority,
    });
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.triageNearMiss(id, {
        action: "SEND_BACK",
        office_comment: officeComment,
      });
      setPayload(response);
      await load();
      setResultMessage("Near miss sent back for rework.");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function rejectOfficeReview() {
    if (!id) {
      return;
    }
    if (!triage.override_reason.trim()) {
      setError("Enter the rejection reason before rejecting this near miss.");
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      const response = await safetyApi.triageNearMiss(id, {
        action: "REJECT",
        office_comment: triage.override_reason,
      });
      setPayload(response);
      await load();
      setResultMessage("Near miss rejected. Master can still submit rework.");
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
      const notificationsEmitted = Number(response.notifications_emitted ?? 0);
      const emailsSent = Number(response.emails_sent ?? 0);
      const emailFailed = Number(response.email_failed ?? 0);
      const vesselsWithoutEmail = Number(response.vessels_without_email ?? 0);
      const deliveryParts = [
        `In-app notifications: ${notificationsEmitted}`,
        `Email batch addressed to ${emailsSent} vessel(s)`,
      ];
      if (emailFailed > 0) {
        deliveryParts.push(`failed: ${emailFailed}`);
      }
      if (vesselsWithoutEmail > 0) {
        deliveryParts.push(`without email: ${vesselsWithoutEmail}`);
      }
      setResultMessage(`Fleet alert issued. ${deliveryParts.join(", ")}.`);
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

  function selectOfficeCategory(rawValue: string) {
    if (rawValue === SAFETY_NEAR_MISS_OTHER_CATEGORY) {
      setShowOfficeOtherCategoryInput(true);
      setReclassificationDraft((current) => ({ ...current, near_miss_shell_tag: "" }));
      return;
    }
    setShowOfficeOtherCategoryInput(false);
    setOfficeOtherCategoryText("");
    setReclassificationDraft((current) => ({ ...current, near_miss_shell_tag: rawValue }));
  }

  function addOfficeOtherCategory() {
    const formatted = formatOtherCategory(officeOtherCategoryText);
    if (!formatted) {
      return;
    }
    setReclassificationDraft((current) => ({ ...current, near_miss_shell_tag: formatted }));
    setOfficeOtherCategoryText("");
    setShowOfficeOtherCategoryInput(false);
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">{modeTitle(mode)}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Lightweight near-miss workflow with reporter details, vessel review, office comments, fleet alert, and closure.
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
                  Current state is {formatNearMissState(nearMiss.state)}; vessel review is available only while the near miss is pending vessel review.
                  {nearMissState === READY_FOR_OFFICE_COMMENTS_STATE || nearMissState === OFFICE_COMMENTS_COMPLETED_STATE ? (
                    <Link className="ml-2 font-semibold text-slate-900 underline" to={`/safety/near-miss/${id}/office-comments`}>
                      Open Office Comments
                    </Link>
                  ) : null}
                </p>
              ) : null}
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Decision
                <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setReviewDraft((current) => ({ ...current, decision: event.target.value }))} value={reviewDraft.decision}>
                  <option value="SUBMIT_TO_OFFICE">Submit to office comments</option>
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
                  Review record
                  <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" readOnly value={reviewDraft.device_fingerprint} />
                </label>
              </div>
              <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !canReview || nearMissState !== "PENDING_VESSEL_REVIEW" || (reviewDraft.decision === "SEND_BACK" && !reviewDraft.comment.trim()) || !reviewDraft.typed_name.trim() || !reviewDraft.device_fingerprint.trim()} type="submit">
                {isMutating ? "Saving..." : "Save vessel review"}
              </button>
            </form>
          ) : null}

          {mode === "rework" ? (
            <section className="space-y-5">
              <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="text-xl font-semibold text-slate-900">Submit Rework</h2>
              {!canSubmitRework ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Rework submission requires near-miss create permission. The Master can submit rework even when another authorized user originally reported it.</p> : null}
              {nearMiss && !reworkAvailableForState ? (
                <p className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                  Current state is {formatNearMissState(nearMiss.state)}; rework is available only when the near miss is sent to rework or rejected.
                </p>
              ) : null}
              {nearMiss?.rework_summary?.comment ? (
                <section className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4">
                  <h3 className="text-sm font-semibold text-amber-950">What office wants you to correct</h3>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-amber-950">{nearMiss.rework_summary.comment}</p>
                  <p className="mt-3 text-xs font-medium text-amber-900">
                    Requested by {nearMiss.rework_summary.requested_by_role || "office"}
                    {nearMiss.rework_summary.requested_at ? ` on ${formatDisplayDateTime(nearMiss.rework_summary.requested_at)}` : ""}
                  </p>
                </section>
              ) : (
                <p className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                  No office rework summary is recorded yet. Check the History tab if you need older comments.
                </p>
              )}
              </div>
              {nearMiss ? (
                <SafetyNearMissForm
                  afterFields={(
                    <label className="block space-y-2 text-sm text-slate-700">
                      <span className="font-medium">What you changed</span>
                      <textarea
                        className="min-h-32 w-full rounded-2xl border border-slate-300 p-3"
                        onChange={(event) => setReworkDraft((current) => ({ ...current, comment: event.target.value }))}
                        value={reworkDraft.comment}
                      />
                    </label>
                  )}
                  description="Update the returned near-miss details before sending the report back for vessel review."
                  initialValues={buildReworkInitialValues(nearMiss)}
                  onSubmit={submitRework}
                  showRateLimit={false}
                  submitDisabled={isMutating || !canSubmitRework || !reworkAvailableForState || !reworkDraft.comment.trim()}
                  submitLabel={isMutating ? "Submitting..." : "Submit corrected near miss"}
                  title="Correct Near Miss"
                />
              ) : null}
            </section>
          ) : null}

          {mode === "office-comments" ? (
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={submitTriage}>
              <h2 className="text-xl font-semibold text-slate-900">Office Comments</h2>
              {officeCommentsCompleted ? <p className="mt-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">Office comments are completed. Saved comments are shown in the summary above.</p> : null}
              {!canSendBackOfficeComment ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Office comments are available only for the assigned PIC or DPA authority.</p> : null}
              {!canAcceptOfficeComment && canSendBackOfficeComment ? <p className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">This near miss must be accepted by an authorized office reviewer. You can still send this report back for rework or reject it if required.</p> : null}
              {triageBlockedByReview ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Vessel-side review must submit this near miss to office before office comments can be saved.</p> : null}
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
                  Superseding will create an Incident record and stop this Near Miss from continuing in the lightweight workflow. Enter the reason below.
                </p>
              ) : null}
              <div className="mt-4">
                <label className="block text-sm font-medium text-slate-700">
                  Category
                  <select
                    className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3"
                    onChange={(event) => selectOfficeCategory(event.target.value)}
                    value={
                      reclassificationDraft.near_miss_shell_tag.startsWith(SAFETY_NEAR_MISS_OTHER_PREFIX)
                        ? SAFETY_NEAR_MISS_OTHER_CATEGORY
                        : reclassificationDraft.near_miss_shell_tag
                    }
                  >
                    <option value="">Select category</option>
                    {nearMissCategoryOptions.map((tag) => (
                      <option key={tag} value={tag}>{tag}</option>
                    ))}
                  </select>
                  {showOfficeOtherCategoryInput ? (
                    <div className="mt-3 flex flex-col gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:flex-row">
                      <input
                        className="min-h-10 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2"
                        maxLength={SAFETY_NEAR_MISS_OTHER_MAX_LENGTH}
                        onChange={(event) => setOfficeOtherCategoryText(event.target.value)}
                        placeholder="Specify category"
                        value={officeOtherCategoryText}
                      />
                      <button
                        className="min-h-10 rounded-xl bg-slate-900 px-4 text-sm font-semibold text-white disabled:bg-slate-300"
                        disabled={!officeOtherCategoryText.trim()}
                        onClick={addOfficeOtherCategory}
                        type="button"
                      >
                        Add
                      </button>
                    </div>
                  ) : null}
                  {reclassificationDraft.near_miss_shell_tag.startsWith(SAFETY_NEAR_MISS_OTHER_PREFIX) ? (
                    <p className="mt-2 text-xs font-medium text-slate-600">{reclassificationDraft.near_miss_shell_tag}</p>
                  ) : null}
                </label>
              </div>
              {officeCategoryChanged ? (
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {officeCategoryChanged ? (
                    <label className="block text-sm font-medium text-slate-700">
                      Reason for changing category <span className="text-rose-600">*</span>
                      <textarea
                        className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3"
                        onChange={(event) => setTriage((current) => ({ ...current, category_tag_change_reason: event.target.value }))}
                        placeholder="Enter why the category was changed."
                        value={triage.category_tag_change_reason}
                      />
                    </label>
                  ) : null}
                </div>
              ) : null}
              <label className="mt-4 block text-sm font-medium text-slate-700">
                {triage.supersede_to_incident ? "Supersede reason" : "Office comment / Send to Rework / Reject reason"}
                {triage.supersede_to_incident ? <span className="text-rose-600"> *</span> : null}
                <textarea
                  className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3"
                  onChange={(event) => setTriage((current) => ({ ...current, override_reason: event.target.value }))}
                  placeholder={triage.supersede_to_incident ? "Enter the reason for superseding this near miss." : "Add office comments, or enter a reason before using Send to Rework or Reject."}
                  value={triage.override_reason}
                />
              </label>
              <div className="mt-4 flex flex-wrap gap-3">
                <button className="min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || officeCommentsCompleted || !canAcceptOfficeComment || triageBlockedByReview || officeReasonMissing} type="submit">
                  {isMutating ? "Saving..." : "Accept"}
                </button>
                <button className="min-h-11 rounded-full border border-amber-300 bg-amber-50 px-5 text-sm font-semibold text-amber-900 disabled:bg-slate-100 disabled:text-slate-400" disabled={isMutating || officeCommentsCompleted || !canSendBackOfficeComment || triageBlockedByReview || officeReworkReasonMissing} onClick={() => void sendOfficeRework()} type="button">
                  {isMutating ? "Sending..." : "Send to Rework"}
                </button>
                <button className="min-h-11 rounded-full border border-rose-300 bg-rose-50 px-5 text-sm font-semibold text-rose-900 disabled:bg-slate-100 disabled:text-slate-400" disabled={isMutating || officeCommentsCompleted || !canRejectOfficeComment || triageBlockedByReview || !triage.override_reason.trim()} onClick={() => void rejectOfficeReview()} type="button">
                  {isMutating ? "Rejecting..." : "Reject"}
                </button>
              </div>
            </form>
          ) : null}

          {mode === "fleet-alert" ? (
            <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={issueFleetAlert}>
              <h2 className="text-xl font-semibold text-slate-900">Fleet Alert</h2>
              {!canIssueFleetAlert ? <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Issue circular/alert is available only for authorized DPA users.</p> : null}
              <div className="mt-4 grid gap-4 md:grid-cols-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Issued</p>
                  <p className="mt-2 font-semibold text-slate-900">{fleetAlert?.issued ? "Yes" : "No"}</p>
                  <p className="mt-1 text-xs text-slate-500">{fleetAlert?.issued_at ? formatDisplayDateTime(fleetAlert.issued_at) : "Not issued yet"}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">7-day SLA</p>
                  <p className={`mt-2 font-semibold ${fleetAlert?.sla?.overdue ? "text-rose-700" : "text-slate-900"}`}>{fleetAlert?.sla?.status ?? "Pending"}</p>
                  <p className="mt-1 text-xs text-slate-500">{formatDisplayDateTime(fleetAlert?.sla?.due_by ?? fleetAlert?.draft?.due_by)}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 md:col-span-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Recipients</p>
                  <p className="mt-2 text-sm text-slate-700">{recipientLabels.join(", ") || (fleetAlert?.recipients ?? []).join(", ") || "Not resolved"}</p>
                </div>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Draft title</p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">{fleetAlert?.draft?.title || "No draft title"}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Circular status</p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">{fleetAlert?.circular_publish?.status || "Not published"}</p>
                </div>
              </div>
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Fleet alert message
                <textarea
                  className="mt-2 min-h-40 w-full rounded-2xl border border-slate-300 p-3 text-sm leading-6"
                  onChange={(event) => setAlertDraft((current) => ({ ...current, alert_text: event.target.value }))}
                  value={alertDraft.alert_text}
                />
              </label>
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
                Fleet learning / lessons
                <textarea className="mt-2 min-h-32 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setAlertDraft((current) => ({ ...current, fleet_learning_text: event.target.value }))} value={alertDraft.fleet_learning_text} />
              </label>
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold text-slate-900">Issue Circular/Alert</p>
                <p className="mt-1 text-sm text-slate-600">
                  Prepare a Circular/Alert from this near miss. DPA completes the remaining Circular fields and publishes from the Circular page.
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
              <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={closureDisabled} type="submit">
                {isMutating ? "Closing..." : "Close near miss"}
              </button>
            </form>
          ) : null}

          {mode === "audit" ? <NearMissAudit audit={audit} /> : null}

          {mode === "pdf" ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-slate-900">PDF Export</h2>
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
  const vesselReview = nearMiss.vessel_review_summary;
  const officeComment = nearMiss.office_comment?.trim();
  const closureComment = nearMiss.closure_reason?.trim();

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">{nearMiss.incident_number ?? `#${nearMiss.id}`}</span>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">{formatNearMissState(nearMiss.state)}</span>
        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">{nearMiss.near_miss_priority ?? "Pending office comments"}</span>
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
          <dd className="mt-2 text-sm font-semibold text-slate-900">{nearMiss.reporter_name ?? "Reporter not recorded"}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Severity</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{nearMiss.near_miss_severity ?? "Not selected"}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Place</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{formatNearMissPlace(nearMiss.near_miss_place)}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Category</dt>
          <dd className="mt-2 text-sm font-semibold text-slate-900">{formatList(nearMiss.near_miss_category_tags, nearMiss.near_miss_shell_tag, "Not tagged")}</dd>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 md:col-span-3">
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cause factors</dt>
          <dd className="mt-3">
            <CauseFactorsTable rows={nearMiss.near_miss_factor_causes} />
          </dd>
        </div>
      </dl>
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">What happened</p>
        <p className="mt-2 text-sm leading-6 text-slate-700">{nearMiss.narrative ?? "No details available."}</p>
      </div>
      <NearMissEvidenceAttachments attachments={nearMiss.evidence_attachments} />
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Immediate action</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{nearMiss.near_miss_immediate_action ?? "Not recorded."}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Preventive action / suggestion</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{nearMiss.near_miss_suggestion ?? "Not recorded."}</p>
        </div>
      </div>
      {nearMiss.near_miss_root_cause_detail
        || nearMiss.near_miss_corrective_action
        || nearMiss.near_miss_weather_voyage_details
        || nearMiss.near_miss_equipment_details
        || nearMiss.near_miss_lessons_learned ? (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <HighRiskDetail label="Immediate cause detail" value={nearMiss.near_miss_root_cause_detail} />
          <HighRiskDetail label="Corrective action" value={nearMiss.near_miss_corrective_action} />
          <HighRiskDetail label="Weather / voyage details" value={nearMiss.near_miss_weather_voyage_details} />
          <HighRiskDetail label="Equipment details" value={nearMiss.near_miss_equipment_details} />
          <HighRiskDetail label="Lessons learned" value={nearMiss.near_miss_lessons_learned} />
        </div>
      ) : null}
      {vesselReview?.comment ? (
        <div className="mt-4 rounded-2xl border border-sky-200 bg-sky-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-sky-700">Vessel review comment</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-800">{vesselReview.comment}</p>
          <p className="mt-3 text-xs font-medium text-sky-800">
            Reviewed by {vesselReview.reviewed_by_role || "vessel reviewer"}
            {vesselReview.typed_name ? ` (${vesselReview.typed_name})` : ""}
            {vesselReview.reviewed_at ? ` on ${formatDisplayDateTime(vesselReview.reviewed_at)}` : ""}
          </p>
        </div>
      ) : null}
      {officeComment ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">Office comments</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-800">{officeComment}</p>
        </div>
      ) : null}
      {closureComment ? (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Closure comment</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-800">{closureComment}</p>
          {nearMiss.closed_at ? (
            <p className="mt-3 text-xs font-medium text-slate-600">Closed on {formatDisplayDateTime(nearMiss.closed_at)}</p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function NearMissEvidenceAttachments({ attachments }: { attachments?: NearMissEvidenceAttachment[] }) {
  const visibleAttachments = useMemo(
    () => (Array.isArray(attachments) ? attachments.filter((attachment) => attachment.preview_url) : []),
    [attachments],
  );
  const [objectUrls, setObjectUrls] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;
    const createdUrls: string[] = [];

    async function loadPreviews() {
      const entries = await Promise.all(
        visibleAttachments.map(async (attachment) => {
          if (!attachment.preview_url) {
            return null;
          }
          try {
            const blob = await safetyApi.downloadNearMissEvidencePhoto(attachment.preview_url);
            const objectUrl = URL.createObjectURL(blob);
            createdUrls.push(objectUrl);
            return [attachment.id, objectUrl] as const;
          } catch {
            return null;
          }
        }),
      );
      if (!cancelled) {
        setObjectUrls(Object.fromEntries(entries.filter(Boolean) as Array<readonly [string, string]>));
      }
    }

    if (visibleAttachments.length) {
      void loadPreviews();
    } else {
      setObjectUrls({});
    }

    return () => {
      cancelled = true;
      createdUrls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [visibleAttachments]);

  async function openAttachment(attachment: NearMissEvidenceAttachment) {
    const existingUrl = objectUrls[attachment.id];
    if (existingUrl) {
      window.open(existingUrl, "_blank", "noopener,noreferrer");
      return;
    }
    if (!attachment.preview_url) {
      return;
    }
    const blob = await safetyApi.downloadNearMissEvidencePhoto(attachment.preview_url);
    const objectUrl = URL.createObjectURL(blob);
    window.open(objectUrl, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 30_000);
  }

  if (!visibleAttachments.length) {
    return null;
  }

  return (
    <section className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Attachments</p>
          <p className="mt-1 text-sm text-slate-600">Uploaded images linked to this near miss.</p>
        </div>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {visibleAttachments.map((attachment) => {
          const objectUrl = objectUrls[attachment.id];
          return (
            <article key={attachment.id} className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
              <div className="flex min-h-48 items-center justify-center bg-slate-100">
                {objectUrl ? (
                  <button
                    className="block w-full"
                    onClick={() => void openAttachment(attachment)}
                    type="button"
                  >
                    <img
                      alt={attachment.title || attachment.file_name || "Near miss attachment"}
                      className="max-h-72 w-full object-contain"
                      src={objectUrl}
                    />
                  </button>
                ) : (
                  <p className="px-4 py-8 text-sm text-slate-500">Loading image preview...</p>
                )}
              </div>
              <div className="space-y-2 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      {attachment.title || attachment.file_name || "Near miss image"}
                    </p>
                    {attachment.file_name ? (
                      <p className="mt-1 break-all text-xs text-slate-500">{attachment.file_name}</p>
                    ) : null}
                  </div>
                  {attachment.high_severity_required ? (
                    <span className="rounded-full bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700">
                      High severity
                    </span>
                  ) : null}
                </div>
                {attachment.description ? (
                  <p className="text-sm leading-6 text-slate-600">{attachment.description}</p>
                ) : null}
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-xs text-slate-500">
                    Uploaded: {formatDisplayDateTime(attachment.uploaded_at)}
                  </p>
                  <button
                    className="min-h-9 rounded-full border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                    onClick={() => void openAttachment(attachment)}
                    type="button"
                  >
                    View image
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function HighRiskDetail({ label, value }: { label: string; value?: string | null }) {
  if (!value?.trim()) {
    return null;
  }
  return (
    <div className="rounded-2xl border border-rose-100 bg-rose-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm leading-6 text-slate-700">{value}</p>
    </div>
  );
}

function formatList(values: string[] | undefined, fallback?: string | null, emptyLabel = "Not selected") {
  const cleaned = (Array.isArray(values) ? values : [])
    .map((value) => String(value).trim())
    .filter(Boolean);
  if (cleaned.length) {
    return cleaned.join(", ");
  }
  return fallback?.trim() || emptyLabel;
}

function CauseFactorsTable({ rows }: { rows?: SafetyNearMissValues["near_miss_factor_causes"] }) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return <p className="text-sm font-semibold text-slate-900">Not selected</p>;
  }

  const rowByFactor = new Map(rows.map((row) => [row.factor, row]));

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <div className="grid grid-cols-[minmax(120px,0.8fr)_minmax(0,1fr)_minmax(0,1fr)] border-b border-slate-200 bg-slate-100 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        <div className="px-3 py-2">Factor</div>
        <div className="px-3 py-2">Immediate Cause</div>
        <div className="px-3 py-2">Root Cause</div>
      </div>
      {SAFETY_NEAR_MISS_CAUSE_FACTORS.map((factor) => {
        const row = rowByFactor.get(factor.value);
        return (
          <div
            key={factor.value}
            className="grid grid-cols-[minmax(120px,0.8fr)_minmax(0,1fr)_minmax(0,1fr)] border-b border-slate-100 last:border-b-0"
          >
            <div className="px-3 py-3 text-sm font-semibold text-slate-900">{factor.label}</div>
            <div className="px-3 py-3 text-sm leading-6 text-slate-700">
              {formatCauseChoice(row?.immediate_option_text, row?.immediate_other_text)}
            </div>
            <div className="px-3 py-3 text-sm leading-6 text-slate-700">
              {formatCauseChoice(row?.root_option_text, row?.root_other_text)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function formatCauseChoice(optionText?: string | null, otherText?: string | null) {
  const option = String(optionText ?? "").trim();
  const other = String(otherText ?? "").trim();
  if (["other", "others", "other-specify"].includes(option.toLowerCase()) && other) {
    return other;
  }
  return option || other || "Not selected";
}

function formatNearMissPlace(value?: string | null) {
  switch (value) {
    case "AT_ANCHOR":
      return "At Anchor";
    case "AT_SEA":
      return "At Sea";
    case "AT_PORT":
      return "At Port";
    default:
      return "Not selected";
  }
}

function formatDisplayDateTime(value?: string | null) {
  if (!value) {
    return "not recorded";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("en-GB", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function NearMissAudit({ audit }: { audit: AuditPayload | null }) {
  const phaseRows = [...(audit?.phase_log ?? [])].sort((a, b) => auditTime(b.occurred_at) - auditTime(a.occurred_at));
  const historyRows = [...(audit?.field_history ?? [])].sort((a, b) => auditTime(b.changed_at) - auditTime(a.changed_at));
  const timelineRows = [
    ...phaseRows.map((row) => ({
      actor: formatAuditActor(row.actor_role_code, row.actor_user_id),
      id: `workflow-${row.id}`,
      kind: "workflow" as const,
      summary: formatWorkflowStep(row.phase_from, row.phase_to),
      timestamp: row.occurred_at,
      title: formatAuditLabel(row.transition_type),
    })),
    ...historyRows.map((row) => ({
      actor: formatAuditActor(row.actor_role_code, row.actor_user_id),
      after: formatAuditValue(row.new_value),
      before: formatAuditValue(row.old_value),
      id: `change-${row.id}`,
      kind: "change" as const,
      reason: row.change_reason,
      timestamp: row.changed_at,
      title: `${fieldHistoryLabel(row.field_name)} updated`,
    })),
  ].sort((a, b) => auditTime(b.timestamp) - auditTime(a.timestamp));
  const latestActivity = timelineRows[0]?.timestamp;

  return (
    <section className="space-y-4">
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900">History</h2>
            <p className="mt-1 text-sm text-slate-600">
              Latest workflow steps and record changes, shown newest first.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-md bg-slate-50 px-3 py-2">
              <p className="text-lg font-semibold text-slate-900">{timelineRows.length}</p>
              <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Total</p>
            </div>
            <div className="rounded-md bg-slate-50 px-3 py-2">
              <p className="text-lg font-semibold text-slate-900">{phaseRows.length}</p>
              <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Steps</p>
            </div>
            <div className="rounded-md bg-slate-50 px-3 py-2">
              <p className="text-lg font-semibold text-slate-900">{historyRows.length}</p>
              <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">Changes</p>
            </div>
          </div>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Latest activity: {latestActivity ? formatDisplayDateTime(latestActivity) : "No history recorded"}
        </p>
      </div>

      {timelineRows.length ? (
        <ol className="space-y-3">
          {timelineRows.map((row) => (
            <li className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm" key={row.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
                      {row.kind === "workflow" ? "Step" : "Change"}
                    </span>
                    <h3 className="text-sm font-semibold text-slate-900">{row.title}</h3>
                  </div>
                  <p className="mt-2 text-sm text-slate-600">{row.actor}</p>
                </div>
                <time className="shrink-0 text-xs font-medium text-slate-500">{formatDisplayDateTime(row.timestamp)}</time>
              </div>

              {row.kind === "workflow" ? (
                <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">{row.summary}</p>
              ) : (
                <div className="mt-3 space-y-3">
                  {row.reason ? (
                    <p className="rounded-md bg-amber-50 px-3 py-2 text-sm leading-6 text-amber-900">
                      Reason: {row.reason}
                    </p>
                  ) : null}
                  <dl className="grid gap-3 md:grid-cols-2">
                    <div className="min-w-0 rounded-md bg-slate-50 px-3 py-2">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Changed from</dt>
                      <dd className="mt-1 max-h-32 overflow-auto break-words text-sm leading-6 text-slate-700">{row.before}</dd>
                    </div>
                    <div className="min-w-0 rounded-md bg-emerald-50 px-3 py-2">
                      <dt className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Changed to</dt>
                      <dd className="mt-1 max-h-32 overflow-auto break-words text-sm font-medium leading-6 text-slate-900">{row.after}</dd>
                    </div>
                  </dl>
                </div>
              )}
            </li>
          ))}
        </ol>
      ) : (
        <EmptyHistoryBlock message="No history is available yet." />
      )}
    </section>
  );
}

function auditTime(value?: string | null) {
  if (!value) {
    return 0;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function formatWorkflowStep(phaseFrom: number | null, phaseTo: number | null | undefined) {
  const from = phaseFrom === null || phaseFrom === undefined ? "Started" : `Step ${phaseFrom}`;
  const to = phaseTo === null || phaseTo === undefined ? "next step" : `Step ${phaseTo}`;
  return `${from} to ${to}`;
}

function EmptyHistoryBlock({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-600">
      {message}
    </div>
  );
}

const nearMissHistoryFieldLabels: Record<string, string> = {
  category_tag_change_reason: "Category change reason",
  closure_reason: "Closure reason",
  near_miss_priority: "Priority",
  near_miss_shell_tag: "Category",
  near_miss_mscat_subcode_id: "Immediate cause",
  state: "Status",
  updated_by: "Updated by",
  updated_date: "Updated date",
};

function formatAuditLabel(value: string) {
  return value
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}

function fieldHistoryLabel(value: string) {
  return nearMissHistoryFieldLabels[value] ?? formatAuditLabel(value);
}

function formatAuditActor(role?: string | null, userId?: string | null) {
  const cleanRole = role?.trim() || "Unknown role";
  const cleanUser = userId?.trim();
  return cleanUser ? `${cleanRole} (${cleanUser})` : cleanRole;
}

function parseAuditValue(value: string) {
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

function unwrapAuditValue(value: unknown): unknown {
  if (typeof value === "string") {
    const parsed = parseAuditValue(value);
    return parsed === value ? value : unwrapAuditValue(parsed);
  }
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const record = value as Record<string, unknown>;
    if ("__history_scalar__" in record) {
      return unwrapAuditValue(record.__history_scalar__);
    }
  }
  return value;
}

function formatAuditValue(value: unknown) {
  const unwrapped = unwrapAuditValue(value);
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
    return formatAuditStringValue(unwrapped);
  }
  if (Array.isArray(unwrapped)) {
    return unwrapped.map(formatAuditValue).join(", ");
  }
  try {
    return Object.entries(unwrapped as Record<string, unknown>)
      .filter(([, entryValue]) => entryValue !== null && entryValue !== undefined && entryValue !== "")
      .map(([key, entryValue]) => `${formatAuditLabel(key)}: ${formatAuditValue(entryValue)}`)
      .join(" / ") || "Recorded";
  } catch {
    return "Recorded value";
  }
}

function formatAuditStringValue(value: string) {
  const state = normalizeCode(value);
  switch (state) {
    case READY_FOR_OFFICE_COMMENTS_STATE:
    case OFFICE_COMMENTS_COMPLETED_STATE:
    case "PENDING_VESSEL_REVIEW":
    case "REWORK_REQUIRED":
    case "CLOSED":
    case "SUPERSEDED":
    case "DRAFT":
    case "SUBMITTED":
      return formatNearMissState(state);
    default:
      return value;
  }
}

export default SafetyNearMissWorkspace;
