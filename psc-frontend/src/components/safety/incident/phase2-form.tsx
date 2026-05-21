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
import { SafetyLossTypeSelect } from "../shared/reference-pickers";

interface SafetyIncidentPhase2FormProps {
  incidentId: string;
  initialValues?: Partial<SafetyIncidentPhase2Values>;
  onSaveDraft?: (values: SafetyIncidentPhase2Values) => void;
  onSubmitPhase?: (values: SafetyIncidentPhase2SubmitValues) => void;
}

const defaultValues: SafetyIncidentPhase2Values = {
  dpa_notified_at: null,
  fm_notified_at: null,
  office_notified_at: null,
  pic_user_id: "",
  schema_version: SAFETY_INCIDENT_PHASE_2_SCHEMA_VERSION,
};

function formatStamp(value?: string | null) {
  return value ? value : "Pending on submit";
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

  async function handleSaveDraft() {
    const result = safetyIncidentPhase2Schema.safeParse(values);
    if (result.success) {
      onSaveDraft?.(result.data);
      const draft = await saveDraftNow();
      toast({
        title: "Draft saved",
        description: `Incident phase 2 draft saved at ${draft.updatedAt}.`,
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
              Incident / Phase 2
            </p>
            <h1 className="text-3xl font-semibold text-slate-900">
              Notifications + Resource Allocation
            </h1>
            <p className="max-w-3xl text-sm leading-6 text-slate-600">
              Confirm the classifier inputs for Phase 2 so submit can assign the
              formal incident number, compute the band, and notify PIC, DPA,
              and the safety channel before the evidence workspace opens.
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
                  : "Auto-save armed"}
            </div>
          </div>
        </div>
      </header>

      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
        <div className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Type of loss</span>
              <SafetyLossTypeSelect
                onChange={(nextValue) => updateField("loss_type_primary_id", nextValue)}
                value={values.loss_type_primary_id ?? null}
              />
            </label>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Internal risk band</span>
              <select
                aria-label="Internal risk band"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) =>
                  updateField(
                    "risk_band",
                    event.target.value as SafetyIncidentPhase2Values["risk_band"],
                  )
                }
                value={values.risk_band ?? ""}
              >
                <option value="">Select band</option>
                <option value="GREEN">GREEN</option>
                <option value="YELLOW">YELLOW</option>
                <option value="RED">RED</option>
              </select>
            </label>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">IMO classifier</span>
              <select
                aria-label="IMO classifier"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) =>
                  updateField(
                    "imo_classifier",
                    event.target.value as SafetyIncidentPhase2Values["imo_classifier"],
                  )
                }
                value={values.imo_classifier ?? ""}
              >
                <option value="">Select classifier</option>
                <option value="SMC">SMC</option>
                <option value="MC">MC</option>
                <option value="MI">MI</option>
                <option value="NOT_APPLICABLE">NOT_APPLICABLE</option>
              </select>
            </label>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Investigation depth</span>
              <select
                aria-label="Investigation depth"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) =>
                  updateField(
                    "investigation_depth",
                    (event.target.value || null) as SafetyIncidentPhase2Values["investigation_depth"],
                  )
                }
                value={values.investigation_depth ?? ""}
              >
                <option value="">Select depth</option>
                <option value="SHALLOW">SHALLOW</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="DEEP">DEEP</option>
              </select>
            </label>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Office notified at</span>
              <input
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-500"
                disabled
                value={formatStamp(values.office_notified_at)}
              />
            </label>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Latitude</span>
              <input
                aria-label="Latitude"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) => updateField("latitude", event.target.value)}
                value={values.latitude ?? ""}
              />
            </label>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Longitude</span>
              <input
                aria-label="Longitude"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) => updateField("longitude", event.target.value)}
                value={values.longitude ?? ""}
              />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">DPA notified at</span>
              <input
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-500"
                disabled
                value={formatStamp(values.dpa_notified_at)}
              />
            </label>
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">FM notified at</span>
              <input
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-500"
                disabled
                value={formatStamp(values.fm_notified_at)}
              />
            </label>
          </div>
        </div>

        <aside className="space-y-6">
          <SafetyBandHelper advisoryBand={advisoryBand} />

          {values.risk_band === "RED" ? (
            <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-rose-900">
                External expert engagement prompt
              </h2>
              <p className="mt-2 text-sm leading-6 text-rose-800">
                RED-band incidents must nudge the office toward external-expert
                engagement alongside FM and Managing Director notification.
              </p>
            </section>
          ) : null}

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Phase action</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Submit stamps the formal incident number, allocates the role-based
              PIC recipient, and emits the office notification fan-out.
            </p>
            <div className="mt-5 flex flex-col gap-3">
              <button
                className="min-h-[44px] rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
                onClick={handleSaveDraft}
                type="button"
              >
                Save Phase 2 draft
              </button>
              <button
                className="min-h-[44px] rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
                disabled={!submitReady}
                onClick={handleSubmit}
                type="button"
              >
                Submit to office
              </button>
            </div>
          </section>
        </aside>
      </section>
    </section>
  );
}

export default SafetyIncidentPhase2Form;
