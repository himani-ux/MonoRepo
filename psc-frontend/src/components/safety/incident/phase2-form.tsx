import { useEffect, useState } from "react";

import { useDraftAutosave } from "../../../hooks/safety/use-draft-autosave";
import { useToast } from "../../../hooks/use-toast";
import {
  SAFETY_INCIDENT_PHASE_2_SCHEMA_VERSION,
  type SafetyIncidentPhase2SubmitValues,
  type SafetyIncidentPhase2Values,
  safetyIncidentPhase2Schema,
  safetyIncidentPhase2SubmitSchema,
} from "../../../schemas/safety/incident-phase2";
import { SafetyBandHelper } from "./band-helper";
import { SafetyLossTypeMultiSelect } from "../shared/reference-pickers";

interface SafetyIncidentPhase2FormProps {
  incidentId: string;
  initialValues?: Partial<SafetyIncidentPhase2Values>;
  onSaveDraft?: (values: SafetyIncidentPhase2Values) => void;
  onSubmitPhase?: (values: SafetyIncidentPhase2SubmitValues) => void;
}

const defaultValues: SafetyIncidentPhase2Values = {
  dpa_notified_at: null,
  fm_notified_at: null,
  office_notified: null,
  office_notified_at: null,
  pic_user_id: "",
  schema_version: SAFETY_INCIDENT_PHASE_2_SCHEMA_VERSION,
};

function derivedInvestigationDepthLabel(riskBand?: SafetyIncidentPhase2Values["risk_band"]) {
  if (riskBand === "RED") {
    return "High detail check";
  }
  if (riskBand === "YELLOW") {
    return "Medium detail check";
  }
  if (riskBand === "GREEN") {
    return "Basic check";
  }
  return "Select risk level";
}

export function SafetyIncidentPhase2Form({
  incidentId,
  initialValues,
  onSaveDraft,
  onSubmitPhase,
}: SafetyIncidentPhase2FormProps) {
  const { toast } = useToast();
  const [values, setValues] = useState<SafetyIncidentPhase2Values>({
    ...defaultValues,
    ...initialValues,
  });
  useEffect(() => {
    if (!initialValues) {
      return;
    }

    setValues((current) => ({ ...current, ...initialValues }));
  }, [initialValues]);
  const { lastSavedAt, saveDraftNow, status } = useDraftAutosave({
    onRestore: (restoredValues) =>
      setValues((current) => ({ ...current, ...restoredValues })),
    phase: 2,
    recordId: incidentId,
    values,
  });

  const submitReady = safetyIncidentPhase2SubmitSchema.safeParse(values).success;
  const advisoryBand = values.risk_band ?? "GREEN";

  function updateField<K extends keyof SafetyIncidentPhase2Values>(
    field: K,
    nextValue: SafetyIncidentPhase2Values[K],
  ) {
    setValues((current) => ({ ...current, [field]: nextValue }));
  }

  function updateLossTypes(nextValue: {
    lossTypeIds: number[];
    otherSelected: boolean;
    otherText: string;
  }) {
    setValues((current) => ({
      ...current,
      loss_type_other: nextValue.otherSelected ? nextValue.otherText : null,
      loss_type_primary_id: nextValue.lossTypeIds[0] ?? null,
      loss_type_secondary_id: nextValue.lossTypeIds[1] ?? null,
      loss_type_tertiary_id: nextValue.lossTypeIds[2] ?? null,
    }));
  }

  async function handleSaveDraft() {
    const result = safetyIncidentPhase2Schema.safeParse(values);
    if (result.success) {
      onSaveDraft?.(result.data);
      const draft = await saveDraftNow();
      toast({
        title: "Draft saved",
        description: `Draft saved at ${draft.updatedAt}.`,
        variant: "success",
      });
    }
  }

  function handleSubmit() {
    const result = safetyIncidentPhase2SubmitSchema.safeParse(values);
    if (result.success) {
      onSubmitPhase?.(result.data);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
              Incident / Tell Office
            </p>
            <h1 className="text-3xl font-semibold text-slate-900">
              Tell Office
            </h1>
            <p className="max-w-3xl text-sm leading-6 text-slate-600">
              Confirm if office was informed about this incident.
            </p>
          </div>
          <div className="space-y-2">
            <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-600">
              Incident {incidentId}
            </div>
            <div className="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-medium uppercase tracking-[0.18em] text-emerald-800">
              {status === "restored"
                ? `Draft restored${lastSavedAt ? ` ${lastSavedAt}` : ""}`
                : lastSavedAt
                  ? `Auto-saved ${lastSavedAt}`
                  : "Auto-save ready"}
            </div>
          </div>
        </div>
      </header>

      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <div className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <SafetyLossTypeMultiSelect
                onChange={updateLossTypes}
                otherText={values.loss_type_other ?? ""}
                values={{
                  lossTypeIds: [
                    values.loss_type_primary_id,
                    values.loss_type_secondary_id,
                    values.loss_type_tertiary_id,
                  ].filter((value): value is number => typeof value === "number"),
                  otherSelected: values.loss_type_other !== null && values.loss_type_other !== undefined,
                }}
              />
            </div>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Risk level</span>
              <select
                aria-label="Risk level"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) =>
                  updateField(
                    "risk_band",
                    event.target.value as SafetyIncidentPhase2Values["risk_band"],
                  )
                }
                value={values.risk_band ?? ""}
              >
                <option value="">Select risk level</option>
                <option value="GREEN">Low</option>
                <option value="YELLOW">Medium</option>
                <option value="RED">High</option>
              </select>
            </label>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Was office informed?</span>
              <select
                aria-label="Was office informed?"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                onChange={(event) => {
                  const nextValue =
                    event.target.value === ""
                      ? null
                      : event.target.value === "YES";
                  setValues((current) => ({
                    ...current,
                    office_notification_mode: nextValue ? current.office_notification_mode : null,
                    office_notified: nextValue,
                  }));
                }}
                value={
                  values.office_notified === null || values.office_notified === undefined
                    ? ""
                    : values.office_notified
                      ? "YES"
                      : "NO"
                }
              >
                <option value="">Select</option>
                <option value="YES">Yes</option>
                <option value="NO">No</option>
              </select>
            </label>

            {values.office_notified ? (
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">How was office informed?</span>
                <select
                  aria-label="How was office informed?"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                  onChange={(event) =>
                    updateField(
                      "office_notification_mode",
                      (event.target.value || null) as SafetyIncidentPhase2Values["office_notification_mode"],
                    )
                  }
                  value={values.office_notification_mode ?? ""}
                >
                  <option value="">Select how</option>
                  <option value="ON_CALL">On call</option>
                  <option value="EMAIL">On email</option>
                </select>
              </label>
            ) : null}
          </div>
        </div>

        <aside className="space-y-6">
          <SafetyBandHelper advisoryBand={advisoryBand} />

          {values.risk_band === "RED" ? (
            <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-rose-900">
                Get outside expert help
              </h2>
              <p className="mt-2 text-sm leading-6 text-rose-800">
                For high-risk incidents, office should consider outside expert help and inform senior managers.
              </p>
            </section>
          ) : null}

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Save or Submit</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Submit after confirming office was informed.
            </p>
            <p className="mt-3 text-sm font-medium text-slate-700">
              Check needed: {derivedInvestigationDepthLabel(values.risk_band)}
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
                className="min-h-[44px] rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                disabled={!submitReady}
                onClick={handleSubmit}
                type="button"
              >
                Submit
              </button>
            </div>
          </section>
        </aside>
      </section>
    </section>
  );
}

export default SafetyIncidentPhase2Form;
