import { useEffect, useRef, useState } from "react";

import SafetyExternalPartyInjuryForm, {
  type SafetyExternalPartyInjuryValues,
} from "./external-party-injury-form";
import SafetyMscmepc3PositionPicker from "./msc-mepc3-position-picker";
import {
  SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION,
  type SafetyIncidentPhase1SubmitValues,
  type SafetyIncidentPhase1Values,
  safetyIncidentPhase1Schema,
  safetyIncidentPhase1SubmitSchema,
} from "../../../schemas/safety/incident-phase1";
import { useDraftAutosave } from "../../../hooks/safety/use-draft-autosave";
import {
  toUtcIsoTimestamp,
  useMscmepc3Position,
} from "../../../hooks/safety/use-msc-mepc3-position";
import { SafetySelfReportGuardModal } from "./self-report-guard-modal";
import { useAuth } from "../../../hooks/use-auth";
import { useToast } from "../../../hooks/use-toast";
import { getSafetyDeviceFingerprint } from "../../../lib/safety/digital-signature";
import {
  SafetyIncidentTypeSelect,
  SafetyLossTypeSelect,
} from "../shared/reference-pickers";

interface SafetyIncidentPhase1FormProps {
  incidentId?: string;
  initialValues?: Partial<SafetyIncidentPhase1Values>;
  mode: "create" | "edit";
  onSaveDraft?: (values: SafetyIncidentPhase1Values) => void;
  onSubmitPhase?: (values: SafetyIncidentPhase1SubmitValues) => void;
}

const defaultValues: SafetyIncidentPhase1Values = {
  awaiting_daily_report_match: false,
  first_hour_checklist_done: false,
  narrative: "",
  reporter_device_fingerprint: "",
  reporter_name: "",
  reporter_rank: "",
  reporter_user_id: "",
  schema_version: SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION,
  vessel_id: "",
};

const FIRST_HOUR_CHECKLIST_ITEMS = [
  {
    key: "scene_secured",
    label: "Scene secured",
    description: "No repairs, movements, or cleanup before initial evidence is protected.",
  },
  {
    key: "alarms_frozen",
    label: "Alarms frozen",
    description: "Alarm logs are frozen or marked before reset/acknowledgement.",
  },
  {
    key: "photos_sketches_captured",
    label: "Photos/sketches captured",
    description: "Initial photographs and a sketch are captured before detailed examination.",
  },
  {
    key: "witnesses_noted",
    label: "Witnesses noted",
    description: "People present and immediate witnesses are recorded.",
  },
  {
    key: "damage_extent_noted",
    label: "Damage extent noted",
    description: "Initial extent of damage or loss is recorded.",
  },
] as const;

type FirstHourChecklistKey = (typeof FIRST_HOUR_CHECKLIST_ITEMS)[number]["key"];
type FirstHourChecklistState = Record<FirstHourChecklistKey, boolean>;

function buildFirstHourChecklistState(done: boolean): FirstHourChecklistState {
  return Object.fromEntries(
    FIRST_HOUR_CHECKLIST_ITEMS.map((item) => [item.key, done]),
  ) as FirstHourChecklistState;
}

function firstNonBlank(...values: Array<string | null | undefined>) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return "";
}

function buildReporterNameFromAuth(user: ReturnType<typeof useAuth>["user"]) {
  const combinedName = [user?.first_name, user?.surname]
    .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
    .join(" ")
    .trim();

  return firstNonBlank(
    user?.full_name,
    user?.display_name,
    combinedName,
    user?.username,
    user?.UserName,
    user?.crew_id,
  );
}

function toDateTimeLocalValue(value?: string | null) {
  if (!value) {
    return "";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const timezoneOffsetMs = parsed.getTimezoneOffset() * 60_000;
  return new Date(parsed.getTime() - timezoneOffsetMs).toISOString().slice(0, 16);
}

function describeValidationIssue(
  issue: { message: string; path: Array<string | number> } | undefined,
) {
  if (!issue) {
    return "Complete the required phase 1 fields before continuing.";
  }

  const fieldLabels: Record<string, string> = {
    first_hour_checklist_done: "Checklist complete",
    incident_type_id: "Incident type",
    loss_type_primary_id: "Type of loss",
    narrative: "Narrative",
    occurred_at: "Occurred at",
    pic_candidate_id: "PIC candidate",
    reported_at: "Reported at",
    reporter_device_fingerprint: "Reporter signature device data",
    reporter_name: "Reporter name",
    reporter_rank: "Reporter rank",
    reporter_user_id: "Reporter user ID",
    vessel_code: "Vessel code",
    vessel_id: "Vessel",
  };

  const fieldKey = String(issue.path[0] ?? "");
  const fieldLabel = fieldLabels[fieldKey];
  if (fieldLabel) {
    return `${fieldLabel}: ${issue.message}`;
  }

  return issue.message;
}

export function SafetyIncidentPhase1Form({
  incidentId,
  initialValues,
  mode,
  onSaveDraft,
  onSubmitPhase,
}: SafetyIncidentPhase1FormProps) {
  const { isVessel, user } = useAuth();
  const { toast } = useToast();
  const [values, setValues] = useState<SafetyIncidentPhase1Values>({
    ...defaultValues,
    ...initialValues,
  });
  const [firstHourChecklist, setFirstHourChecklist] = useState<FirstHourChecklistState>(
    buildFirstHourChecklistState(Boolean(initialValues?.first_hour_checklist_done)),
  );
  const [showConflictGuard, setShowConflictGuard] = useState(false);
  const lastAutoFillRef = useRef<string | null>(null);
  const { lastSavedAt, saveDraftNow, status } = useDraftAutosave({
    onRestore: (restoredValues) =>
      setValues((current) => {
        const nextValues = { ...current, ...restoredValues };

        if (isVessel && mode === "create") {
          nextValues.vessel_id = firstNonBlank(nextValues.vessel_id, vesselIdFromAuth);
          nextValues.vessel_code = firstNonBlank(nextValues.vessel_code, vesselCodeFromAuth);
          nextValues.reporter_user_id = firstNonBlank(
            nextValues.reporter_user_id,
            reporterUserIdFromAuth,
          );
          nextValues.reporter_name = firstNonBlank(
            nextValues.reporter_name,
            reporterNameFromAuth,
          );
          nextValues.reporter_rank = firstNonBlank(
            nextValues.reporter_rank,
            reporterRankFromAuth,
          );
        }

        return nextValues;
      }),
    phase: 1,
    recordId: incidentId ?? "draft-phase-1",
    values,
  });
  const positionPrefill = useMscmepc3Position({
    occurredAt: toUtcIsoTimestamp(values.occurred_at ?? null),
    vesselId: values.vessel_code || values.vessel_id,
  });

  const narrativeLength = values.narrative.trim().length;
  const firstHourChecklistComplete = FIRST_HOUR_CHECKLIST_ITEMS.every(
    (item) => firstHourChecklist[item.key],
  );
  const submitReady = safetyIncidentPhase1SubmitSchema.safeParse(values).success;
  const vesselIdFromAuth = firstNonBlank(user?.vessel_id);
  const vesselCodeFromAuth = firstNonBlank(user?.vessel_code);
  const vesselDisplayName = firstNonBlank(user?.vessel_name, user?.vessel_code, values.vessel_code, user?.vessel_id, values.vessel_id);
  const vesselOptions = (user?.vessel_ids ?? [])
    .map((vesselId, index) => ({
      id: String(vesselId).trim(),
      label: firstNonBlank(user?.vessel_names?.[index], String(vesselId)),
    }))
    .filter((option) => option.id);
  const reporterUserIdFromAuth = firstNonBlank(
    user?.crew_id,
    user?.username,
    user?.UserName,
    user?.id,
  );
  const reporterNameFromAuth = buildReporterNameFromAuth(user);
  const reporterRankFromAuth = firstNonBlank(
    user?.rank,
    user?.safety_role_name,
    user?.role_name,
    user?.role,
  );

  useEffect(() => {
    setValues((current) => {
      if (current.reporter_device_fingerprint) {
        return current;
      }
      return {
        ...current,
        reporter_device_fingerprint: getSafetyDeviceFingerprint(),
      };
    });
  }, []);

  useEffect(() => {
    if (!values.first_hour_checklist_done || firstHourChecklistComplete) {
      return;
    }
    setFirstHourChecklist(buildFirstHourChecklistState(true));
  }, [firstHourChecklistComplete, values.first_hour_checklist_done]);

  useEffect(() => {
    if (!isVessel || mode !== "create") {
      return;
    }

    setValues((current) => {
      const nextVesselId = vesselIdFromAuth || current.vessel_id;
      const nextVesselCode = vesselCodeFromAuth || current.vessel_code;

      if (
        current.vessel_id === nextVesselId &&
        (current.vessel_code ?? "") === (nextVesselCode ?? "")
      ) {
        return current;
      }

      return {
        ...current,
        vessel_code: nextVesselCode,
        vessel_id: nextVesselId,
      };
    });
  }, [isVessel, mode, vesselCodeFromAuth, vesselIdFromAuth]);

  useEffect(() => {
    if (!isVessel || mode !== "create") {
      return;
    }

    setValues((current) => {
      const nextReporterUserId = current.reporter_user_id || reporterUserIdFromAuth;
      const nextReporterName = current.reporter_name || reporterNameFromAuth;
      const nextReporterRank = current.reporter_rank || reporterRankFromAuth;

      if (
        current.reporter_user_id === nextReporterUserId &&
        current.reporter_name === nextReporterName &&
        current.reporter_rank === nextReporterRank
      ) {
        return current;
      }

      return {
        ...current,
        reporter_name: nextReporterName,
        reporter_rank: nextReporterRank,
        reporter_user_id: nextReporterUserId,
      };
    });
  }, [
    isVessel,
    mode,
    reporterNameFromAuth,
    reporterRankFromAuth,
    reporterUserIdFromAuth,
  ]);

  useEffect(() => {
    if (positionPrefill.status === "matched" && positionPrefill.data) {
      const sourceReference = positionPrefill.data.source_reference;
      const noPositionYet = values.latitude == null && values.longitude == null;
      if (!noPositionYet || !sourceReference || lastAutoFillRef.current === sourceReference) {
        return;
      }

      lastAutoFillRef.current = sourceReference;
      setValues((current) => ({
        ...current,
        awaiting_daily_report_match: false,
        latitude: positionPrefill.data?.latitude ?? current.latitude,
        longitude: positionPrefill.data?.longitude ?? current.longitude,
        position_daily_report_id:
          positionPrefill.data?.position_daily_report_id ?? current.position_daily_report_id,
        position_source: positionPrefill.data?.position_source ?? current.position_source,
      }));
      return;
    }

    if (positionPrefill.status === "awaiting") {
      setValues((current) => ({
        ...current,
        awaiting_daily_report_match: true,
        position_source: current.position_source ?? "AWAITING_DAILY_REPORT",
      }));
    }
  }, [
    positionPrefill.data,
    positionPrefill.status,
    values.latitude,
    values.longitude,
  ]);

  function updateField<K extends keyof SafetyIncidentPhase1Values>(
    field: K,
    nextValue: SafetyIncidentPhase1Values[K],
  ) {
    setValues((current) => ({ ...current, [field]: nextValue }));
  }

  function updateFirstHourChecklistItem(key: FirstHourChecklistKey, checked: boolean) {
    setFirstHourChecklist((current) => {
      const next = { ...current, [key]: checked };
      const complete = FIRST_HOUR_CHECKLIST_ITEMS.every((item) => next[item.key]);
      setValues((currentValues) => ({
        ...currentValues,
        first_hour_checklist_done: complete,
      }));
      return next;
    });
  }

  function updateExternalParty(nextValue: SafetyExternalPartyInjuryValues | null) {
    setValues((current) => ({ ...current, external_party_injury: nextValue }));
  }

  function applySuggestedPosition() {
    if (!positionPrefill.data || !positionPrefill.data.matched) {
      return;
    }

    lastAutoFillRef.current = positionPrefill.data.source_reference;
    setValues((current) => ({
      ...current,
      awaiting_daily_report_match: false,
      latitude: positionPrefill.data?.latitude ?? current.latitude,
      longitude: positionPrefill.data?.longitude ?? current.longitude,
      position_daily_report_id:
        positionPrefill.data?.position_daily_report_id ?? current.position_daily_report_id,
      position_source: positionPrefill.data?.position_source ?? current.position_source,
    }));
  }

  function handleLatitudeChange(nextValue: string) {
    setValues((current) => ({
      ...current,
      awaiting_daily_report_match: current.awaiting_daily_report_match ?? false,
      latitude: nextValue === "" ? null : Number(nextValue),
      position_source: "MANUAL",
    }));
  }

  function handleLongitudeChange(nextValue: string) {
    setValues((current) => ({
      ...current,
      awaiting_daily_report_match: current.awaiting_daily_report_match ?? false,
      longitude: nextValue === "" ? null : Number(nextValue),
      position_source: "MANUAL",
    }));
  }

  async function handleSaveDraft() {
    const result = safetyIncidentPhase1Schema.safeParse(values);
    if (result.success) {
      onSaveDraft?.(result.data);
    }

    const draft = await saveDraftNow();
    toast({
      title: "Draft saved",
      description: `Incident phase 1 draft saved at ${draft.updatedAt}.`,
      variant: "success",
    });
  }

  function handleSubmit() {
    const result = safetyIncidentPhase1SubmitSchema.safeParse(values);
    if (!result.success) {
      const issue = result.error.issues[0];
      toast({
        title: "Phase 1 is incomplete",
        description: describeValidationIssue(issue),
        variant: "warning",
      });
      return;
    }

    if (values.pic_candidate_id && values.pic_candidate_id === values.reporter_user_id) {
      setShowConflictGuard(true);
      return;
    }

    onSubmitPhase?.(result.data);
  }

  return (
    <>
      <section className="space-y-6">
        <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                Incident / Phase 1
              </p>
              <h1 className="text-3xl font-semibold text-slate-900">
                Intake + Scene Control
              </h1>
              <p className="max-w-3xl text-sm leading-6 text-slate-600">
                Capture the first-hour picture, preserve the scene, and establish
                an attributable draft before the investigation moves to Phase 2.
              </p>
            </div>
            <div className="space-y-2">
              <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-600">
                {mode === "create" ? "Draft create" : `Incident ${incidentId ?? "phase-1"}`}
              </div>
              <div className="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-emerald-800">
                {status === "restored"
                  ? `Draft restored${lastSavedAt ? ` ${lastSavedAt}` : ""}`
                  : lastSavedAt
                    ? `Auto-saved ${lastSavedAt}`
                    : "Auto-save armed"}
              </div>
            </div>
          </div>
        </header>

        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                First-Hour Scene Protection
              </h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                Freeze alarms, note damage extent, secure the scene, photograph
                and sketch, and record witness presence before advancing.
              </p>
            </div>
            <div className="rounded-full border border-amber-300 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-amber-900">
              {firstHourChecklistComplete ? "All 5 complete" : "All 5 required"}
            </div>
          </div>
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            {FIRST_HOUR_CHECKLIST_ITEMS.map((item) => (
              <label
                className="flex min-h-[120px] items-start gap-3 rounded-2xl border border-amber-200 bg-white p-4 text-sm text-slate-700"
                key={item.key}
              >
                <input
                  aria-label={item.label}
                  checked={firstHourChecklist[item.key]}
                  className="mt-1 h-5 w-5 rounded border-slate-300"
                  onChange={(event) => updateFirstHourChecklistItem(item.key, event.target.checked)}
                  type="checkbox"
                />
                <span>
                  <span className="block font-semibold text-slate-900">{item.label}</span>
                  <span className="mt-1 block leading-5 text-slate-600">{item.description}</span>
                </span>
              </label>
            ))}
          </div>
          <input
            aria-hidden="true"
            readOnly
            type="hidden"
            value={values.first_hour_checklist_done ? "true" : "false"}
          />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
          <div className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Incident type</span>
                <SafetyIncidentTypeSelect
                  onChange={(nextValue) => updateField("incident_type_id", nextValue)}
                  value={values.incident_type_id ?? null}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Type of loss</span>
                <SafetyLossTypeSelect
                  onChange={(nextValue) => updateField("loss_type_primary_id", nextValue)}
                  value={values.loss_type_primary_id ?? null}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Vessel</span>
                {!isVessel && vesselOptions.length > 0 ? (
                  <select
                    aria-label="Vessel"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                    onChange={(event) => updateField("vessel_id", event.target.value)}
                    value={values.vessel_id}
                  >
                    <option value="">Select vessel</option>
                    {vesselOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    aria-label="Vessel"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                    onChange={(event) => updateField("vessel_id", event.target.value)}
                    readOnly={isVessel}
                    value={isVessel ? vesselDisplayName : values.vessel_id}
                  />
                )}
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Vessel code</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) => updateField("vessel_code", event.target.value)}
                  readOnly={isVessel}
                  value={values.vessel_code ?? ""}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Occurred at</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField("occurred_at", toUtcIsoTimestamp(event.target.value) ?? null)
                  }
                  type="datetime-local"
                  value={toDateTimeLocalValue(values.occurred_at)}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Reported at</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField("reported_at", toUtcIsoTimestamp(event.target.value) ?? null)
                  }
                  type="datetime-local"
                  value={toDateTimeLocalValue(values.reported_at)}
                />
              </label>
            </div>

            <label className="block space-y-2 text-sm text-slate-700">
              <span className="font-medium">Narrative</span>
              <textarea
                aria-label="Narrative"
                className="min-h-[220px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
                onChange={(event) => updateField("narrative", event.target.value)}
                value={values.narrative}
              />
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">
                  Minimum 200 characters before Phase 2.
                </span>
                <span
                  className={
                    narrativeLength >= 200 ? "text-emerald-700" : "text-amber-700"
                  }
                >
                  {narrativeLength}/200
                </span>
              </div>
            </label>

            <SafetyMscmepc3PositionPicker
              autoFillMessage={positionPrefill.data?.message}
              awaitingDailyReportMatch={values.awaiting_daily_report_match}
              latitude={values.latitude}
              longitude={values.longitude}
              onApplySuggested={applySuggestedPosition}
              onLatitudeChange={handleLatitudeChange}
              onLongitudeChange={handleLongitudeChange}
              sourceReference={positionPrefill.data?.source_reference}
              status={positionPrefill.status}
            />

            <SafetyExternalPartyInjuryForm
              enabled={Boolean(values.external_party_injury)}
              onChange={updateExternalParty}
              value={values.external_party_injury ?? null}
            />
          </div>

          <aside className="space-y-6">
            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Reporter block</h2>
              <div className="mt-4 space-y-4">
                <label className="block space-y-2 text-sm text-slate-700">
                  <span className="font-medium">Reporter user ID</span>
                  <input
                  aria-label="Reporter user ID"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) => updateField("reporter_user_id", event.target.value)}
                  readOnly={isVessel}
                  value={values.reporter_user_id}
                />
              </label>
                <label className="block space-y-2 text-sm text-slate-700">
                  <span className="font-medium">Reporter name</span>
                  <input
                  aria-label="Reporter name"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) => updateField("reporter_name", event.target.value)}
                  readOnly={isVessel}
                  value={values.reporter_name}
                />
              </label>
                <label className="block space-y-2 text-sm text-slate-700">
                  <span className="font-medium">Reporter rank</span>
                  <input
                  aria-label="Reporter rank"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) => updateField("reporter_rank", event.target.value)}
                  readOnly={isVessel}
                  value={values.reporter_rank}
                />
              </label>
                <label className="block space-y-2 text-sm text-slate-700">
                  <span className="font-medium">PIC candidate</span>
                  <input
                    aria-label="PIC candidate"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                    onChange={(event) => updateField("pic_candidate_id", event.target.value)}
                    value={values.pic_candidate_id ?? ""}
                  />
                </label>
              </div>
            </section>

            <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Phase action</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Draft saves remain local-first in this handover scaffold with a
                30-second browser auto-save seam. Server mutation wiring belongs
                to the real monorepo integration pass.
              </p>
              <div className="mt-5 flex flex-col gap-3">
                <button
                  className="min-h-[44px] rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
                  onClick={handleSaveDraft}
                  type="button"
                >
                  Save draft
                </button>
                <button
                  aria-disabled={!submitReady}
                  className="min-h-[44px] rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
                  onClick={handleSubmit}
                  type="button"
                >
                  Continue to Phase 2
                </button>
              </div>
            </section>
          </aside>
        </section>
      </section>

      <SafetySelfReportGuardModal
        message="The reporter also matches the current PIC candidate for this Phase 1 handoff."
        onAcknowledge={() => {
          setShowConflictGuard(false);
          const result = safetyIncidentPhase1SubmitSchema.safeParse(values);
          if (result.success) {
            onSubmitPhase?.(result.data);
          }
        }}
        onCancel={() => setShowConflictGuard(false)}
        open={showConflictGuard}
        requiredApproverRole="MASTER"
      />
    </>
  );
}
