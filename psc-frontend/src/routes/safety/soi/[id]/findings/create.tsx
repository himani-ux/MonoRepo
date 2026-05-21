import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import SafetyIncidentWorthyNudgeModal from "../../../../../components/safety/soi/incident-worthy-nudge-modal";
import SafetyHighSeverityPhotoUpload from "../../../../../components/safety/soi/high-severity-photo-upload";
import SafetyLifeThreatEscalationBanner from "../../../../../components/safety/soi/life-threat-escalation-banner";
import SafetyFloatingFeedback from "../../../../../components/safety/shared/safety-floating-feedback";
import {
  SafetyMscatPicker,
  SafetySoiItemSelect,
} from "../../../../../components/safety/shared/reference-pickers";
import { safetyKeys, useSafetySoiInspection } from "../../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../../lib/api/client";
import { safetyApi } from "../../../../../lib/api/safety";
import { findSafetySoiLifeThreatMatches } from "../../../../../schemas/safety/soi-finding";

export default function SafetySoiFindingCreateRoute() {
  const params = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const inspectionId = params.id ?? "";
  const enabled = Boolean(inspectionId);
  const inspectionQuery = useSafetySoiInspection(inspectionId, enabled);
  const [areaId, setAreaId] = useState<number | null>(null);
  const [itemId, setItemId] = useState<number | null>(null);
  const [checklistUniqueId, setChecklistUniqueId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState<"HIGH" | "MED" | "LOW">("MED");
  const [priority, setPriority] = useState<"HIGH" | "MED" | "LOW">("MED");
  const [mscatCategoryId, setMscatCategoryId] = useState<number | null>(null);
  const [mscatSubcodeId, setMscatSubcodeId] = useState<string | null>(null);
  const [shellTag, setShellTag] = useState("");
  const [assignedCrewId, setAssignedCrewId] = useState("");
  const [photoAttachmentPath, setPhotoAttachmentPath] = useState("");
  const [lifeThreatTarget, setLifeThreatTarget] = useState<"INCIDENT" | "NEAR_MISS" | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [photoUploadError, setPhotoUploadError] = useState<string | null>(null);
  const [nudgeOpen, setNudgeOpen] = useState(false);
  const [pendingSaveMode, setPendingSaveMode] = useState<"CREATE_INCIDENT" | "KEEP_SOI_ONLY" | null>(null);

  useEffect(() => {
    if (!inspectionQuery.data || areaId !== null) {
      return;
    }
    setAreaId(inspectionQuery.data.selected_areas[0]?.area_id ?? null);
  }, [inspectionQuery.data, areaId]);

  useEffect(() => {
    const existingChecklistId = inspectionQuery.data?.checklist_unique_id?.trim();
    if (!existingChecklistId || checklistUniqueId.trim().length > 0) {
      return;
    }
    setChecklistUniqueId(existingChecklistId);
  }, [inspectionQuery.data?.checklist_unique_id, checklistUniqueId]);

  const createMutation = useMutation({
    mutationFn: (payload: Parameters<typeof safetyApi.createSoiFinding>[1]) =>
      safetyApi.createSoiFinding(inspectionId, payload),
    onSuccess: async (payload) => {
      setMessage(`Finding saved for Area ${areaId}.`);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiFindings(inspectionId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiInspection(inspectionId) }),
      ]);
      if (payload.high_severity_nudge?.record_type === "INCIDENT") {
        navigate(`/safety/incidents/create?source=soi&soi_id=${inspectionId}&finding_id=${payload.id}`);
      } else if (payload.high_severity_nudge?.record_type === "NEAR_MISS") {
        navigate(`/safety/near-miss/create?source=soi&soi_id=${inspectionId}&finding_id=${payload.id}`);
      }
    },
  });

  const photoUploadMutation = useMutation({
    mutationFn: (file: File) => safetyApi.uploadSoiFindingPhoto(inspectionId, file),
    onSuccess: (payload) => {
      setPhotoAttachmentPath(payload.photo_attachment_path);
      setPhotoUploadError(null);
      setError(null);
    },
    onError: (mutationError) => {
      setPhotoAttachmentPath("");
      setPhotoUploadError(getErrorMessage(mutationError));
    },
  });

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SOI finding route.
      </section>
    );
  }

  if (inspectionQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SOI inspection...
      </section>
    );
  }

  if (inspectionQuery.isError) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(inspectionQuery.error)}
      </section>
    );
  }

  const inspection = inspectionQuery.data;
  const selectedArea = inspection.selected_areas.find((item) => item.area_id === areaId);
  const assigneeOptions = [
    inspection.safety_officer_crew_id,
    inspection.assistant_crew_id,
    ...inspection.trainees.map((trainee) => trainee.crew_id),
  ].filter((crewId, index, all) => crewId && all.indexOf(crewId) === index);
  const hasPaperChecklist = Boolean(inspection.checklist_unique_id && inspection.checklist_generated_at);
  const lifeThreatMatches = findSafetySoiLifeThreatMatches(title, description);
  const isHighSeverity = severity === "HIGH";

  const submitFinding = (incidentWorthyAction?: "CREATE_INCIDENT" | "KEEP_SOI_ONLY", incidentWorthyReason?: string) => {
    if (areaId === null) {
      setError("Select an SOI area before saving.");
      return;
    }
    const normalizedChecklistId = checklistUniqueId.trim() || inspection.checklist_unique_id?.trim() || "";
    if (normalizedChecklistId.length === 0) {
      setError("Enter the unique checklist ID printed on the paper packet.");
      return;
    }

    createMutation.mutate({
      assigned_crew_id: assignedCrewId || null,
      area_id: areaId,
      checklist_unique_id: normalizedChecklistId,
      description,
      incident_worthy_action: incidentWorthyAction ?? undefined,
      incident_worthy_reason: incidentWorthyReason ?? undefined,
      item_id: itemId,
      life_threat_escalation_target: lifeThreatTarget,
      mscat_category_id: mscatCategoryId,
      mscat_subcode_id: mscatSubcodeId,
      photo_attachment_path: photoAttachmentPath || null,
      priority,
      severity,
      shell_tag: shellTag || null,
      title,
    });
  };

  if (!hasPaperChecklist) {
    return (
      <section className="space-y-6">
        <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-semibold text-slate-900">Create SOI Finding</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            {inspection.inspection_reference} - {inspection.cycle_label}
          </p>
        </section>

        <section className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-amber-950">Download paper checklist first</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-amber-900">
            This SOI does not have a paper checklist unique ID yet. Download the PDF or Excel checklist first; the
            system will allocate the unique ID and print it on the paper packet. Use that printed ID when registering
            findings.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              className="inline-flex items-center justify-center rounded-full bg-amber-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-amber-700"
              to={`/safety/soi/${inspectionId}/download`}
            >
              Download paper checklist
            </Link>
            <Link
              className="inline-flex items-center justify-center rounded-full border border-amber-300 bg-white px-5 py-3 text-sm font-semibold text-amber-950 transition hover:border-amber-400 hover:bg-amber-100"
              to={`/safety/soi/${inspectionId}/findings`}
            >
              Back to findings
            </Link>
          </div>
        </section>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      {error ? <SafetyFloatingFeedback tone="error">{error}</SafetyFloatingFeedback> : null}
      {createMutation.isError ? (
        <SafetyFloatingFeedback tone="error">{getErrorMessage(createMutation.error)}</SafetyFloatingFeedback>
      ) : null}
      {message ? <SafetyFloatingFeedback tone="success">{message}</SafetyFloatingFeedback> : null}
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.16),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(16,185,129,0.12),_transparent_30%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Create SOI Finding</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              {inspection.inspection_reference} - {inspection.cycle_label}
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

      <SafetyLifeThreatEscalationBanner
        matches={lifeThreatMatches}
        onSelectTarget={(target) => {
          setLifeThreatTarget(target);
          setError(null);
        }}
        selectedTarget={lifeThreatTarget}
      />

      <section className="grid gap-6 xl:grid-cols-[1.25fr,0.75fr]">
        <form
          className="space-y-5 rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm"
          onSubmit={(event) => {
            event.preventDefault();
            setMessage(null);

            if (isHighSeverity && photoAttachmentPath.trim().length === 0) {
              setError("HIGH-severity SOI findings require >=1 photo.");
              return;
            }

            if (lifeThreatMatches.length > 0 && lifeThreatTarget === null) {
              setError("Life-threat findings must escalate through Incident or Near Miss before save can continue.");
              return;
            }

            if (isHighSeverity && lifeThreatMatches.length === 0) {
              setError(null);
              setPendingSaveMode("KEEP_SOI_ONLY");
              setNudgeOpen(true);
              return;
            }

            setError(null);
            submitFinding();
          }}
        >
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="text-sm font-semibold text-slate-900">Area</span>
              <select
                aria-label="Area"
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(event) => {
                  setAreaId(Number(event.target.value));
                  setItemId(null);
                }}
                value={areaId ?? ""}
              >
                {inspection.selected_areas.map((area) => (
                  <option key={area.selection_id} value={area.area_id}>
                    {area.area_id} - {area.area_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-slate-900">Checklist item</span>
              <SafetySoiItemSelect
                areaId={areaId}
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={setItemId}
                value={itemId}
              />
            </label>
          </div>

          <label className="block">
            <span className="text-sm font-semibold text-slate-900">Paper checklist unique ID</span>
            <input
              aria-label="Paper checklist unique ID"
              autoComplete="off"
              className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              onChange={(event) => setChecklistUniqueId(event.target.value)}
              placeholder={inspection.checklist_unique_id ?? "Enter printed checklist ID"}
              type="text"
              value={checklistUniqueId}
            />
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="text-sm font-semibold text-slate-900">Severity</span>
              <select
                aria-label="Severity"
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(event) => setSeverity(event.target.value as "HIGH" | "MED" | "LOW")}
                value={severity}
              >
                <option value="HIGH">HIGH</option>
                <option value="MED">MED</option>
                <option value="LOW">LOW</option>
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-slate-900">Priority</span>
              <select
                aria-label="Priority"
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(event) => setPriority(event.target.value as "HIGH" | "MED" | "LOW")}
                value={priority}
              >
                <option value="HIGH">HIGH</option>
                <option value="MED">MED</option>
                <option value="LOW">LOW</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="text-sm font-semibold text-slate-900">M-SCAT code</span>
              <SafetyMscatPicker
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(nextValue) => {
                  setMscatCategoryId(nextValue.categoryId);
                  setMscatSubcodeId(nextValue.subcodeId);
                }}
                value={{ categoryId: mscatCategoryId, subcodeId: mscatSubcodeId }}
              />
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-slate-900">SHELL tag</span>
              <select
                aria-label="SHELL tag"
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(event) => setShellTag(event.target.value)}
                value={shellTag}
              >
                <option value="">Select SHELL tag</option>
                <option value="Software">Software</option>
                <option value="Hardware">Hardware</option>
                <option value="Environment">Environment</option>
                <option value="Liveware">Liveware</option>
                <option value="Liveware-Liveware">Liveware-Liveware</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="block">
              <span className="text-sm font-semibold text-slate-900">Assignee</span>
              <select
                aria-label="Finding assignee"
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(event) => setAssignedCrewId(event.target.value)}
                value={assignedCrewId}
              >
                <option value="">Default to Safety Officer</option>
                {assigneeOptions.map((crewId) => (
                  <option key={crewId} value={crewId}>
                    {crewId}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-slate-900">Title</span>
              <input
                aria-label="Title"
                className="mt-2 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
                onChange={(event) => setTitle(event.target.value)}
                type="text"
                value={title}
              />
            </label>
          </div>

          <label className="block">
            <span className="text-sm font-semibold text-slate-900">Description</span>
            <textarea
              aria-label="Description"
              className="mt-2 min-h-36 w-full rounded-3xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
              onChange={(event) => setDescription(event.target.value)}
              value={description}
            />
          </label>

          <SafetyHighSeverityPhotoUpload
            error={photoUploadError}
            isUploading={photoUploadMutation.isPending}
            isRequired={isHighSeverity}
            onFileSelect={(file) => {
              setMessage(null);
              setPhotoUploadError(null);
              photoUploadMutation.mutate(file);
            }}
            value={photoAttachmentPath}
          />

          <button
            className="rounded-full bg-emerald-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-emerald-700/60"
            disabled={createMutation.isPending || photoUploadMutation.isPending}
            type="submit"
          >
            {createMutation.isPending ? "Saving..." : "Save finding"}
          </button>
        </form>

        <aside className="space-y-4">
          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">SOI context</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div>
                <dt className="font-medium text-slate-500">Reference</dt>
                <dd className="mt-1 font-semibold text-slate-900">{inspection.inspection_reference}</dd>
              </div>
              <div>
                <dt className="font-medium text-slate-500">Vessel</dt>
                <dd className="mt-1 font-semibold text-slate-900">
                  {inspection.vessel_display_name ?? inspection.vessel_name ?? inspection.vessel_id}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-slate-500">Cycle</dt>
                <dd className="mt-1 font-semibold text-slate-900">{inspection.cycle_label}</dd>
              </div>
            </dl>
          </section>

          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Default ownership</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              If you leave the assignee blank, the backend defaults the finding owner to the Safety Officer:
              <span className="font-medium text-slate-900"> {inspection.safety_officer_crew_id}</span>.
            </p>
          </section>

          <section className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Current selection</h2>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Area {selectedArea?.area_id}: {selectedArea?.area_name}
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Checklist ID must match paper packet {inspection.checklist_unique_id ?? "pending first download"}.
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Priority {priority} / Severity {severity}.
            </p>
            {lifeThreatMatches.length > 0 ? (
              <p className="mt-2 text-sm leading-6 text-rose-700">
                Escalation keywords detected: {lifeThreatMatches.join(", ")}.
              </p>
            ) : null}
          </section>
        </aside>
      </section>

      <SafetyIncidentWorthyNudgeModal
        onClose={() => {
          setNudgeOpen(false);
          setPendingSaveMode(null);
        }}
        onCreateIncident={() => {
          setNudgeOpen(false);
          setPendingSaveMode("CREATE_INCIDENT");
          submitFinding("CREATE_INCIDENT");
        }}
        onKeepSoiOnly={(reason) => {
          setNudgeOpen(false);
          if (pendingSaveMode) {
            submitFinding("KEEP_SOI_ONLY", reason);
          }
        }}
        open={nudgeOpen}
      />
    </section>
  );
}
