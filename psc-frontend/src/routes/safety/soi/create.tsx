import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import SafetyAssistantPicker from "../../../components/safety/soi/assistant-picker";
import SafetyAreaPicker from "../../../components/safety/soi/area-picker";
import { formatSoiCrewDisplay } from "../../../components/safety/soi/crew-display";
import SafetyTraineeAssigner from "../../../components/safety/soi/trainee-assigner";
import { useToast } from "../../../hooks/use-toast";
import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import { safetyKeys, useSafetySoiCreateConfig } from "../../../hooks/use-safety";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi, type SafetySoiCreatePayload } from "../../../lib/api/safety";
import { SAFETY_SOI_MAX_SELECTED_AREAS } from "../../../schemas/safety/soi";

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function toggleArea(selectedAreaIds: number[], areaId: number) {
  if (selectedAreaIds.includes(areaId)) {
    return selectedAreaIds.filter((value) => value !== areaId);
  }
  if (selectedAreaIds.length >= SAFETY_SOI_MAX_SELECTED_AREAS) {
    return selectedAreaIds;
  }
  return [...selectedAreaIds, areaId];
}

function normalizeTrainees(crewIds: string[]) {
  return crewIds.filter((crewId, index) => crewId && crewIds.indexOf(crewId) === index);
}

export default function SafetySoiCreateRoute() {
  const auth = useSafetyAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const vesselId = String(auth.vesselIds[0] ?? "");
  const vesselLabel = auth.vesselNames[0] || auth.scopedVesselLabel || vesselId;
  const [plannedDate, setPlannedDate] = useState(todayIsoDate);
  const [selectedAssistantId, setSelectedAssistantId] = useState("");
  const [selectedAreaIds, setSelectedAreaIds] = useState<number[]>([]);
  const [traineeCrewIds, setTraineeCrewIds] = useState<string[]>([]);
  const createConfigQuery = useSafetySoiCreateConfig({ plannedDate, vesselId }, Boolean(vesselId));

  useEffect(() => {
    const config = createConfigQuery.data;
    if (!config?.safety_officer) {
      return;
    }

    const allowedAreaIds = new Set(
      config.areas
        .filter((area) => area.applicable)
        .filter((area) => !area.section_12_flag || config.section_12_status.prompt_required)
        .map((area) => area.area_id),
    );
    const defaultAreaIds = config.areas
      .filter((area) => area.applicable)
      .filter((area) => !area.section_12_flag || config.section_12_status.prompt_required)
      .map((area) => area.area_id)
      .slice(0, SAFETY_SOI_MAX_SELECTED_AREAS);
    const defaultAssistantId = config.assistant_candidates[0]?.crew_id ?? "";

    setSelectedAssistantId((current) =>
      current && config.assistant_candidates.some((candidate) => candidate.crew_id === current)
        ? current
        : defaultAssistantId,
    );
    setSelectedAreaIds((current) => {
      const sanitized = current
        .filter((areaId) => allowedAreaIds.has(areaId))
        .slice(0, SAFETY_SOI_MAX_SELECTED_AREAS);
      return sanitized.length > 0 ? sanitized : defaultAreaIds;
    });
    setTraineeCrewIds((current) =>
      current.filter((crewId) => config.trainee_candidates.some((candidate) => candidate.crew_id === crewId)),
    );
  }, [createConfigQuery.data]);

  const createMutation = useMutation({
    mutationFn: (payload: SafetySoiCreatePayload) => safetyApi.createSoiInspection(payload),
    onSuccess: async (inspection) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiInspections({}) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.soiCompliance(vesselId || undefined) }),
      ]);
      toast({
        title: "SOI created",
        description: "Paper checklist planning is ready. Download the checklist before fieldwork starts.",
        variant: "success",
      });
      navigate(`/safety/soi/${inspection.id}/download`);
    },
    onError: (error) => {
      toast({
        title: "Unable to create SOI",
        description: getErrorMessage(error),
        variant: "destructive",
      });
    },
  });

  const config = createConfigQuery.data;
  const safetyOfficer = config?.safety_officer ?? null;
  const selectedAreaCount = selectedAreaIds.length;
  const section12AreaIds = useMemo(
    () => new Set((config?.areas ?? []).filter((area) => area.section_12_flag).map((area) => area.area_id)),
    [config?.areas],
  );
  const disabledAreaIds = useMemo(
    () =>
      config?.section_12_status.covered_this_cycle
        ? Array.from(section12AreaIds)
        : [],
    [config?.section_12_status.covered_this_cycle, section12AreaIds],
  );
  const traineeOptions = useMemo(() => {
    const blockedCrewIds = new Set(
      [safetyOfficer?.crew_id, selectedAssistantId].filter(Boolean),
    );
    return (config?.trainee_candidates ?? []).filter((candidate) => !blockedCrewIds.has(candidate.crew_id));
  }, [config?.trainee_candidates, safetyOfficer?.crew_id, selectedAssistantId]);

  function handleTraineeChange(slot: number, crewId: string) {
    setTraineeCrewIds((current) => {
      const next = [...current];
      next[slot - 1] = crewId;
      return next;
    });
  }

  async function handleSubmit() {
    if (!config?.safety_officer) {
      return;
    }

    const payload: SafetySoiCreatePayload = {
      area_ids: selectedAreaIds,
      assistant_crew_id: selectedAssistantId,
      cycle_label: config.section_12_status.cycle_label,
      planned_date: plannedDate,
      section_12_included: selectedAreaIds.some((areaId) => section12AreaIds.has(areaId)),
      trainee_crew_ids: normalizeTrainees(traineeCrewIds),
      vessel_id: vesselId,
    };
    createMutation.mutate(payload);
  }

  if (createConfigQuery.isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading SOI create config...
      </section>
    );
  }

  if (createConfigQuery.isError || !config?.safety_officer) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900">
        {getErrorMessage(createConfigQuery.error ?? new Error("Safety Officer snapshot is not available."))}
      </section>
    );
  }

  const canSubmit = Boolean(
    vesselId &&
      plannedDate &&
      safetyOfficer?.crew_id &&
      selectedAssistantId &&
      selectedAreaIds.length > 0 &&
      selectedAreaIds.length <= SAFETY_SOI_MAX_SELECTED_AREAS &&
      !createMutation.isPending,
  );

  return (
    <section className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.16),_transparent_35%),radial-gradient(circle_at_bottom_right,_rgba(251,191,36,0.18),_transparent_30%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Create SOI</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Create the inspection record first, then download the paper checklist. Fieldwork stays on paper;
              findings come back into VIMS only by the checklist unique ID.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Checklist template
            </div>
            <div className="mt-2 font-medium text-slate-900">
              {config.checklist_version?.version_label ?? "No active checklist version"}
            </div>
            <div className="text-sm text-slate-600">
              {config.checklist_version
                ? `Effective ${config.checklist_version.effective_from}`
                : "Activation required before planning"}
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Inspection plan</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              The vessel and Safety Officer stay fixed to the active ship scope. Planned date drives cycle and Section 12 status.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Cycle</div>
            <div className="mt-2 font-medium text-slate-900">{config.section_12_status.cycle_label}</div>
          </div>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Vessel</span>
            <input
              aria-label="Vessel"
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-600"
              disabled
              value={vesselLabel}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Planned date</span>
            <input
              aria-label="Planned date"
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
              onChange={(event) => setPlannedDate(event.target.value)}
              type="date"
              value={plannedDate}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Safety Officer</span>
            <input
              aria-label="Safety Officer"
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-600"
              disabled
              value={formatSoiCrewDisplay(safetyOfficer)}
            />
          </label>
        </div>
      </section>

      <SafetyAssistantPicker
        assistantCandidates={config.assistant_candidates}
        disabled={createMutation.isPending}
        onSelectAssistantId={setSelectedAssistantId}
        safetyOfficer={safetyOfficer}
        selectedAssistantId={selectedAssistantId}
      />

      <SafetyAreaPicker
        areas={config.areas}
        disabledAreaIds={disabledAreaIds}
        maxSelectableAreas={SAFETY_SOI_MAX_SELECTED_AREAS}
        onToggleAreaId={(areaId) => setSelectedAreaIds((current) => toggleArea(current, areaId))}
        section12Status={config.section_12_status}
        selectedAreaIds={selectedAreaIds}
      />

      <SafetyTraineeAssigner
        availableCrew={traineeOptions}
        disabled={createMutation.isPending}
        maxTrainees={config.max_trainees}
        onTraineeCrewIdChange={handleTraineeChange}
        traineeCrewIds={traineeCrewIds}
      />

      {createMutation.isError ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-900 shadow-sm">
          {getErrorMessage(createMutation.error)}
        </section>
      ) : null}

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Paper-first handoff</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Selected areas: {selectedAreaCount}. Creating this record does not upload any scan or digital checklist answer set.
            </p>
          </div>
          <button
            className="inline-flex min-h-[44px] items-center justify-center rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={!canSubmit}
            onClick={handleSubmit}
            type="button"
          >
            {createMutation.isPending ? "Creating SOI..." : "Create and continue to Download Paper"}
          </button>
        </div>
      </section>
    </section>
  );
}
