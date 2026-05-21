import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import SafetySoiFindingRow from "../../../../../components/safety/shared/soi-finding-row";
import SafetyPartialSubmissionIndicator from "../../../../../components/safety/soi/partial-submission-indicator";
import { useSafetyAuth } from "../../../../../hooks/safety/use-auth";
import { safetyKeys, useSafetySoiFindings, useSafetySoiInspection } from "../../../../../hooks/use-safety";
import { getErrorMessage } from "../../../../../lib/api/client";
import { safetyApi } from "../../../../../lib/api/safety";

function savePdfLink(downloadPath: string) {
  window.open(downloadPath, "_blank", "noopener,noreferrer");
}

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

export default function SafetySoiFindingsRoute() {
  const params = useParams();
  const auth = useSafetyAuth();
  const queryClient = useQueryClient();
  const inspectionId = params.id ?? "";
  const enabled = Boolean(inspectionId);
  const inspectionQuery = useSafetySoiInspection(inspectionId, enabled);
  const findingsQuery = useSafetySoiFindings(inspectionId, enabled);

  const submitMutation = useMutation({
    mutationFn: (areaId: number) => safetyApi.submitSoiAreas(inspectionId, [areaId]),
    onSuccess: async (response) => {
      if (response.pdf_export?.download_path) {
        savePdfLink(response.pdf_export.download_path);
      }
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiInspection(inspectionId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiFindings(inspectionId) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiInspections({}) }),
      ]);
    },
  });

  if (!enabled) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        Invalid SOI findings route.
      </section>
    );
  }

  if (inspectionQuery.isLoading || findingsQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SOI findings register...
      </section>
    );
  }

  if (inspectionQuery.isError || findingsQuery.isError) {
    const error = inspectionQuery.error ?? findingsQuery.error;
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(error)}
      </section>
    );
  }

  const inspection = inspectionQuery.data;
  const findings = findingsQuery.data;
  const areaMap = new Map(
    inspection.selected_areas.map((area) => [area.area_id, area.area_name]),
  );
  const normalizedRole = (auth.role ?? "").trim().toUpperCase();
  const currentUserIds = resolveCurrentUserIds(auth.user);
  const activeSafetyOfficerForRecord = !alternateSafetyOfficerRoles.has(normalizedRole)
    || currentUserIds.has(String(inspection.safety_officer_crew_id ?? "").trim());
  const canDownloadChecklist = auth.hasProcess("SAF_P_001")
    && pendingClosureRoles.has(normalizedRole)
    && activeSafetyOfficerForRecord;
  const canSubmitForMasterClosure = auth.hasProcess("SAF_P_014")
    && pendingClosureRoles.has(normalizedRole)
    && activeSafetyOfficerForRecord;
  const canCloseInspection = auth.hasProcess("SAF_P_004") && normalizedRole === "MASTER";
  const hasPaperChecklist = Boolean(inspection.checklist_unique_id && inspection.checklist_generated_at);
  const completedAreaIds = inspection.selected_areas
    .filter((area) => area.inspected)
    .map((area) => area.area_id);
  const pendingAreas = inspection.selected_areas.filter((area) => !area.inspected);

  return (
    <section className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.16),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(16,185,129,0.14),_transparent_32%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">SOI Findings Register</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              {inspection.inspection_reference} - {inspection.cycle_label}
            </p>
          </div>
          <div className="rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-950">
            Checklist ID: {inspection.checklist_unique_id ?? "Allocated on first checklist download"}
          </div>
        </div>
      </section>

      <SafetyPartialSubmissionIndicator
        completedCount={completedAreaIds.length}
        pendingAreaNames={pendingAreas.map((area) => area.area_name)}
        totalCount={inspection.selected_areas.length}
      />

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              Active findings for {inspection.inspection_reference}
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Findings are live records. Area submission updates inspection state and compliance timing.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            {canDownloadChecklist ? (
              <Link
                className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-800 transition hover:border-slate-400 hover:bg-slate-50"
                to={`/safety/soi/${inspectionId}/download`}
              >
                Download paper
              </Link>
            ) : null}
            {hasPaperChecklist ? (
              <Link
                className="inline-flex items-center justify-center rounded-full bg-emerald-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-800"
                to={`/safety/soi/${inspectionId}/findings/create`}
              >
                Add Finding
              </Link>
            ) : canDownloadChecklist ? (
              <Link
                className="inline-flex items-center justify-center rounded-full bg-amber-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-amber-700"
                to={`/safety/soi/${inspectionId}/download`}
              >
                Download paper first
              </Link>
            ) : null}
            {canCloseInspection && (inspection.state === "REPORTED" || inspection.state === "CLOSED") ? (
              <Link
                className="inline-flex items-center justify-center rounded-full border border-emerald-300 bg-emerald-50 px-5 py-3 text-sm font-semibold text-emerald-900 transition hover:border-emerald-400 hover:bg-emerald-100"
                to={`/safety/soi/${inspectionId}/close`}
              >
                {inspection.state === "CLOSED" ? "View close event" : "Close SOI event"}
              </Link>
            ) : null}
          </div>
        </div>

        <div className="mt-5 space-y-4">
          {findings.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center text-sm text-slate-600">
              No findings registered for this inspection yet.
            </div>
          ) : (
            findings.map((finding) => (
              <SafetySoiFindingRow
                key={finding.id}
                finding={{
                  area_id: finding.area_id,
                  area_name: areaMap.get(finding.area_id) ?? `Area ${finding.area_id}`,
                  actionLabel:
                    finding.status === "OPEN" && canSubmitForMasterClosure
                      ? "Submit for Master closure"
                      : finding.status === "PENDING_CLOSURE" && canCloseInspection
                        ? "Close with Master"
                        : "Open closure",
                  assigned_crew_id: finding.assigned_crew_id,
                  description: finding.description,
                  due_date: finding.due_date,
                  id: finding.id,
                  inspection_id: finding.inspection_id,
                  master_approval_state: finding.master_approval_state,
                  master_counter_signature: finding.master_counter_signature,
                  pending_closure_signature: finding.pending_closure_signature,
                  photo_attachment_path: finding.photo_attachment_path,
                  priority: finding.priority,
                  repeat: {
                    badge_text: finding.repeat_badge_text,
                    is_repeat: finding.is_repeat,
                    occurrence_count: finding.repeat_occurrence_count,
                  },
                  severity: finding.severity,
                  status: finding.status,
                  title: finding.title,
                }}
              />
            ))
          )}
        </div>
      </section>

      {submitMutation.isError ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900 shadow-sm">
          {getErrorMessage(submitMutation.error)}
        </section>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-3">
        {pendingAreas.map((area) => (
          <article
            key={area.area_id}
            className="rounded-3xl border border-amber-200 bg-amber-50 p-4 shadow-sm"
          >
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-800">
              Pending area
            </div>
            <h3 className="mt-2 text-base font-semibold text-slate-900">
              Area {area.area_id}: {area.area_name}
            </h3>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Submit this area after its paper findings have been keyed into the digital register.
            </p>
            <button
              className="mt-4 rounded-full border border-amber-300 bg-white px-4 py-2 text-sm font-semibold text-amber-900 transition hover:border-amber-400 hover:bg-amber-100 disabled:cursor-not-allowed disabled:bg-amber-100"
              disabled={submitMutation.isPending}
              onClick={() => submitMutation.mutate(area.area_id)}
              type="button"
            >
              {submitMutation.isPending ? "Submitting..." : `Submit Area ${area.area_id}`}
            </button>
          </article>
        ))}
      </section>
    </section>
  );
}
