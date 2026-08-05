import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import type {
  SafetyIncidentLossEvaluation,
  SafetyLossEvaluationOption,
  SafetyLossEvaluationReportType,
  SafetyPhase8WorkspacePayload,
} from "../../../schemas/safety/incident-phase8";

type LossEvaluationDraft = Omit<SafetyIncidentLossEvaluation, "id" | "updated_date">;

const lossEvaluationChoiceDefaults = {
  consequence: [
    { label: "Minor", value: "MINOR" },
    { label: "Appreciable", value: "APPRECIABLE" },
    { label: "Major", value: "MAJOR" },
    { label: "Severe", value: "SEVERE" },
    { label: "Catastrophic", value: "CATASTROPHIC" },
  ],
  likelihood: [
    { label: "Remote", value: "REMOTE" },
    { label: "Unlikely", value: "UNLIKELY" },
    { label: "Possible", value: "POSSIBLE" },
    { label: "Likely", value: "LIKELY" },
    { label: "Almost certain", value: "ALMOST_CERTAIN" },
  ],
  repair_type: [
    { label: "Temporary", value: "TEMPORARY" },
    { label: "Permanent", value: "PERMANENT" },
  ],
  report_type: [
    { label: "Incident Report", value: "INCIDENT" as const },
    { label: "Injury Report", value: "INJURY" as const },
  ],
  risk_level: [
    { label: "Very low", value: "VERY_LOW" },
    { label: "Low", value: "LOW" },
    { label: "Medium", value: "MEDIUM" },
    { label: "High", value: "HIGH" },
    { label: "Very high", value: "VERY_HIGH" },
  ],
  safe_working_practice: [
    "Health and hygiene",
    "Good housekeeping",
    "Fitness, health and hygiene",
    "Smoking",
    "Avoiding the effects of fatigue (tiredness)",
    "Working in hot or sunny climates and hot environments",
    "Working in cold climates and environments",
    "Risk from sharps",
    "Head protection",
    "Hearing protection",
    "Face and eye protection",
    "Respiratory protective equipment",
    "Hand and foot protection",
    "Protection from falls",
    "Body protection",
    "Protection against drowning",
    "Gas cylinders",
    "Pipelines",
    "Portable fire extinguishers",
    "Good manual-handling techniques",
    "Drainage",
    "Lighting",
    "Guarding of openings",
    "Watertight doors",
    "Stairways, ladders and portable ladders",
    "Shipboard vehicles",
    "Working on deck while ship is at sea",
    "Adverse weather",
    "General advice to seafarers",
    "Assessing exposure to noise",
    "Mitigation: hand-arm vibration",
    "Mitigation: whole-body vibration",
    "Permit to work systems",
    "Enclosed Space Entry",
    "Portable ladders",
    "Cradles and stages",
    "Bosun's chair",
    "Working from punts",
    "Scaffolding",
    "Hand tools",
    "Electrical equipment",
    "High or very low temperatures",
    "Controls",
    "Markings",
    "Warnings",
    "Portable power-operated tools and equipment",
    "Workshop and bench machines (fixed installations)",
    "Abrasive wheels",
    "Hydraulic/pneumatic/high-pressure jetting equipment",
    "Hydraulic jacks",
    "Use of mobile work equipment",
    "Carrying of seafarers on mobile work equipment",
    "Overturning of fork-lift trucks",
    "Self-propelled work equipment",
    "Remote-controlled self-propelled work equipment",
    "Drive units and power take-off shafts",
    "Ropes and wires",
    "Laundry equipment",
    "Lifting Plant",
    "Thorough examination of lifting equipment",
    "Reports, records and marking of lifting equipment",
    "Lifting operations",
    "Use of winches and cranes",
    "Use of derricks",
    "Use of derricks in union purchase",
    "Use of stoppers",
    "Overhaul of cargo gear",
    "Trucks and other vehicles/appliances",
    "Personnel-lifting equipment, lifts",
    "Maintenance and testing of lifts",
    "Work in machinery spaces",
    "Unmanned machinery spaces",
    "Maintenance of machinery",
    "Hydraulic and pneumatic equipment",
    "Storage batteries: general",
    "Storage batteries: lead acid",
    "Storage batteries: alkaline",
    "Carcinogens and mutagens",
    "Safety nets",
    "Use of Equipment",
    "Access for pilots",
    "Safe rigging of pilot ladder",
    "Safe access to small craft",
    "Slips, falls and tripping hazards",
    "Galley stoves, steam boilers and deep fat fryers",
    "Liquid petroleum gas appliances",
    "Deep fat frying",
    "Microwave ovens",
    "Catering equipment",
    "Knives, meat saws, choppers, etc.",
    "Refrigerated rooms and store rooms",
    "Painting",
  ].map((label) => ({ label, value: label })),
  yes_no: [
    { label: "Yes", value: true },
    { label: "No", value: false },
  ],
};

const commonEmptyDraft: LossEvaluationDraft = {
  report_type: null,
  consequence: null,
  likelihood: null,
  risk_level: null,
  name_of_master: null,
  name_of_chief_engineer: null,
  repair_type: null,
  repair_details: null,
  last_overhaul_maintenance_survey_details: null,
  safe_working_practice: null,
  man_hours_worked: null,
  hours_worked_previous_day: null,
  hours_rest_last_96_hours: null,
  delay_to_vessel: null,
  delay_reason: null,
  repair_man_hours_lost: null,
  materials_used_repairs_onboard: null,
  materials_specify_details: null,
  materials_reason: null,
  deviation: null,
  off_hire: null,
  injury_man_hours_lost: null,
  injury_reasons: null,
  repatriation: null,
  hospitalization: null,
  evacuation: null,
  estimated_cost_off_hire: null,
  estimated_cost_delay: null,
  estimated_cost_man_hours: null,
  estimated_cost_deviation: null,
  estimated_cost_materials: null,
  estimated_cost_miscellaneous: null,
  total_estimated_cost: null,
  miscellaneous_expenses_reason: null,
  cost_medicines_onboard: null,
  cost_doctor_visits: null,
  cost_repatriation: null,
  cost_evacuation: null,
  cost_injury_delay: null,
  cost_injury_man_hours: null,
  cost_injury_deviation: null,
  cost_injury_miscellaneous: null,
  injury_total_estimated_cost: null,
  injury_miscellaneous_expenses_reason: null,
};

const incidentCostFields: Array<keyof LossEvaluationDraft> = [
  "estimated_cost_off_hire",
  "estimated_cost_delay",
  "estimated_cost_man_hours",
  "estimated_cost_deviation",
  "estimated_cost_materials",
  "estimated_cost_miscellaneous",
];

const injuryCostFields: Array<keyof LossEvaluationDraft> = [
  "cost_medicines_onboard",
  "cost_doctor_visits",
  "cost_repatriation",
  "cost_evacuation",
  "cost_injury_delay",
  "cost_injury_man_hours",
  "cost_injury_deviation",
  "cost_injury_miscellaneous",
];

function emptyWorkspace(): SafetyPhase8WorkspacePayload {
  return {
    blocker_details: [
      {
        code: "loss_evaluation_not_saved",
        message: "Save Loss Evaluation before closing the incident.",
      },
    ],
    blockers: ["loss_evaluation_not_saved"],
    choices: {
      consequence: lossEvaluationChoiceDefaults.consequence,
      likelihood: lossEvaluationChoiceDefaults.likelihood,
      repair_type: lossEvaluationChoiceDefaults.repair_type,
      report_type: lossEvaluationChoiceDefaults.report_type,
      risk_level: lossEvaluationChoiceDefaults.risk_level,
      safe_working_practice: lossEvaluationChoiceDefaults.safe_working_practice,
      yes_no: lossEvaluationChoiceDefaults.yes_no,
    },
    current_phase: 8,
    has_loss_evaluation: false,
    incident_id: "",
    loss_evaluation: {
      ...commonEmptyDraft,
      id: null,
      updated_date: null,
    },
    phase_title: "Loss Evaluation",
    ready_for_close: false,
    report_type: "INCIDENT",
    required_process_id: "SAF_P_004",
    risk_band: null,
    state: "",
  };
}

function displayText(value: string | null | undefined) {
  return String(value ?? "");
}

function normalizeLossEvaluationError(caught: unknown) {
  const message = getErrorMessage(caught);
  if (/phase\s*6\s+action\s+check\s+is\s+available\s+after\s+phase\s*5\s+office\s+approval/i.test(message)) {
    return null;
  }
  return message;
}

function decimalInputValue(value: string | null | undefined) {
  return value == null ? "" : String(value);
}

function toOptionalString(value: string) {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function toTextInputValue(value: string) {
  return value === "" ? null : value;
}

function sumDecimalFields(draft: LossEvaluationDraft, fields: Array<keyof LossEvaluationDraft>) {
  const total = fields.reduce((sum, field) => {
    const rawValue = draft[field];
    const parsed = Number(rawValue ?? 0);
    return Number.isFinite(parsed) ? sum + parsed : sum;
  }, 0);
  return total > 0 ? total.toFixed(2) : null;
}

function mergeDraft(payload: SafetyIncidentLossEvaluation): LossEvaluationDraft {
  const merged = { ...commonEmptyDraft };
  for (const key of Object.keys(merged) as Array<keyof LossEvaluationDraft>) {
    merged[key] = payload[key] ?? null;
  }
  return merged;
}

function withFallbackOptions<T extends string | boolean>(
  options: Array<SafetyLossEvaluationOption<T>> | undefined,
  fallback: Array<SafetyLossEvaluationOption<T>>
) {
  return Array.isArray(options) && options.length > 0 ? options : fallback;
}

function normalizeWorkspacePayload(payload: SafetyPhase8WorkspacePayload): SafetyPhase8WorkspacePayload {
  const fallback = emptyWorkspace();
  const choices = payload.choices ?? fallback.choices;
  return {
    ...fallback,
    ...payload,
    blocker_details: payload.blocker_details ?? [],
    blockers: payload.blockers ?? [],
    choices: {
      consequence: withFallbackOptions(choices.consequence, fallback.choices.consequence),
      likelihood: withFallbackOptions(choices.likelihood, fallback.choices.likelihood),
      repair_type: withFallbackOptions(choices.repair_type, fallback.choices.repair_type),
      report_type: withFallbackOptions(choices.report_type, fallback.choices.report_type),
      risk_level: withFallbackOptions(choices.risk_level, fallback.choices.risk_level),
      safe_working_practice: withFallbackOptions(
        choices.safe_working_practice,
        fallback.choices.safe_working_practice
      ),
      yes_no: withFallbackOptions(choices.yes_no, fallback.choices.yes_no),
    },
    loss_evaluation: {
      ...fallback.loss_evaluation,
      ...(payload.loss_evaluation ?? {}),
    },
  };
}

function cleanDraftValue(value: unknown) {
  if (typeof value !== "string") {
    return value;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function cleanPayload(draft: LossEvaluationDraft, reportType: SafetyLossEvaluationReportType) {
  const payload: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(draft)) {
    payload[key] = cleanDraftValue(value);
  }
  if (reportType === "INJURY") {
    payload.injury_total_estimated_cost = sumDecimalFields(draft, injuryCostFields);
  } else {
    payload.total_estimated_cost = sumDecimalFields(draft, incidentCostFields);
  }
  return payload;
}

function FieldGrid({ children }: { children: ReactNode }) {
  return <div className="grid gap-4 md:grid-cols-2">{children}</div>;
}

function TextField({
  label,
  multiline = false,
  onChange,
  value,
}: {
  label: string;
  multiline?: boolean;
  onChange: (value: string | null) => void;
  value: string | null;
}) {
  return (
    <label className={multiline ? "block md:col-span-2" : "block"}>
      <span className="text-sm font-medium text-slate-700">{label}</span>
      {multiline ? (
        <textarea
          className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 bg-white p-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
          onChange={(event) => onChange(toTextInputValue(event.target.value))}
          value={displayText(value)}
        />
      ) : (
        <input
          className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
          onChange={(event) => onChange(toTextInputValue(event.target.value))}
          value={displayText(value)}
        />
      )}
    </label>
  );
}

function NumberField({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (value: string | null) => void;
  value: string | null;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <input
        className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
        min="0"
        onChange={(event) => onChange(toOptionalString(event.target.value))}
        step="0.01"
        type="number"
        value={decimalInputValue(value)}
      />
    </label>
  );
}

function SelectField<T extends string | boolean>({
  disabled = false,
  label,
  onChange,
  options,
  placeholder = "Select",
  value,
}: {
  disabled?: boolean;
  label: string;
  onChange: (value: T | null) => void;
  options: Array<SafetyLossEvaluationOption<T>>;
  placeholder?: string;
  value: T | null;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <select
        className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200 disabled:bg-slate-100 disabled:text-slate-500"
        disabled={disabled}
        onChange={(event) => {
          const nextValue = event.target.value;
          if (nextValue === "") {
            onChange(null);
            return;
          }
          if (nextValue === "true" || nextValue === "false") {
            onChange((nextValue === "true") as T);
            return;
          }
          onChange(nextValue as T);
        }}
        value={value == null ? "" : String(value)}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={String(option.value)} value={String(option.value)}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Card({
  children,
  eyebrow,
  title,
}: {
  children: ReactNode;
  eyebrow?: string;
  title: string;
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      {eyebrow ? (
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">{eyebrow}</p>
      ) : null}
      <h2 className="mt-1 text-xl font-semibold text-slate-950">{title}</h2>
      <div className="mt-5">{children}</div>
    </section>
  );
}

export function SafetyIncidentPhase8() {
  const { id } = useParams();
  const noticeRef = useRef<HTMLDivElement | null>(null);
  const [workspace, setWorkspace] = useState<SafetyPhase8WorkspacePayload>(emptyWorkspace());
  const [draft, setDraft] = useState<LossEvaluationDraft>(commonEmptyDraft);
  const [error, setError] = useState<string | null>(null);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);

  const reload = useCallback(async () => {
    if (!id) {
      setError("Invalid incident id.");
      setIsLoading(false);
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const payload = (await safetyApi.getIncidentPhase8Workspace(id)) as unknown as SafetyPhase8WorkspacePayload;
      const normalizedPayload = normalizeWorkspacePayload(payload);
      setWorkspace(normalizedPayload);
      const nextDraft = mergeDraft(normalizedPayload.loss_evaluation);
      if (normalizedPayload.has_loss_evaluation && !nextDraft.report_type) {
        nextDraft.report_type = normalizedPayload.report_type;
      }
      setDraft(nextDraft);
    } catch (caught) {
      setError(normalizeLossEvaluationError(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const selectedReportType = draft.report_type;
  const reportTypeSelected = selectedReportType !== null;
  const isInjuryReport = selectedReportType === "INJURY";
  const reportLabel = selectedReportType
    ? isInjuryReport
      ? "Injury Report"
      : "Incident Report"
    : "Choose report type";
  const incidentTotal = useMemo(() => sumDecimalFields(draft, incidentCostFields), [draft]);
  const injuryTotal = useMemo(() => sumDecimalFields(draft, injuryCostFields), [draft]);
  const safeWorkingPracticeOptions = useMemo(() => {
    const options = workspace.choices.safe_working_practice ?? [];
    const currentValue = draft.safe_working_practice;
    if (!currentValue || options.some((option) => option.value === currentValue)) {
      return options;
    }
    return [{ label: currentValue, value: currentValue }, ...options];
  }, [draft.safe_working_practice, workspace.choices.safe_working_practice]);

  function updateField<Key extends keyof LossEvaluationDraft>(key: Key, value: LossEvaluationDraft[Key]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  async function saveLossEvaluation(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      if (!selectedReportType) {
        setError("Choose Incident Report or Injury Report before saving.");
        window.setTimeout(() => noticeRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
        return;
      }
      const payload = cleanPayload(draft, selectedReportType);
      const response = (await safetyApi.saveIncidentPhase8LossEvaluation(
        id,
        payload,
      )) as unknown as SafetyPhase8WorkspacePayload;
      const normalizedResponse = normalizeWorkspacePayload(response);
      setWorkspace(normalizedResponse);
      const nextDraft = mergeDraft(normalizedResponse.loss_evaluation);
      if (!nextDraft.report_type) {
        nextDraft.report_type = normalizedResponse.report_type;
      }
      setDraft(nextDraft);
      setResultMessage("Loss Evaluation saved.");
      window.setTimeout(() => noticeRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } catch (caught) {
      setError(normalizeLossEvaluationError(caught));
      window.setTimeout(() => noticeRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } finally {
      setIsMutating(false);
    }
  }

  if (isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading Loss Evaluation...
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div ref={noticeRef} />
      {error ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section>
      ) : null}
      {resultMessage ? (
        <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
          {resultMessage}
        </section>
      ) : null}

      <form className="space-y-6" onSubmit={saveLossEvaluation}>
        <Card eyebrow="Report Type" title="What are you recording?">
          <FieldGrid>
            <SelectField
              label="Loss Evaluation type"
              onChange={(value) => updateField("report_type", value)}
              options={workspace.choices.report_type}
              placeholder="Select report type"
              value={draft.report_type}
            />
          </FieldGrid>
        </Card>

        {reportTypeSelected ? (
          <>
            <Card eyebrow="Risk Assessment" title="Risk Assessment">
              <FieldGrid>
                <SelectField
                  label="Consequence"
                  onChange={(value) => updateField("consequence", value)}
                  options={workspace.choices.consequence}
                  value={draft.consequence}
                />
            <SelectField
              label="Likelihood"
              onChange={(value) => updateField("likelihood", value)}
              options={workspace.choices.likelihood}
              value={draft.likelihood}
            />
            <SelectField
              label="Risk level"
              onChange={(value) => updateField("risk_level", value)}
              options={workspace.choices.risk_level}
              value={draft.risk_level}
            />
          </FieldGrid>
            </Card>

            <Card eyebrow="Other Details" title="Other Details">
          <FieldGrid>
            <TextField
              label="Name of master"
              onChange={(value) => updateField("name_of_master", value)}
              value={draft.name_of_master}
            />
            <TextField
              label="Name of Chief Engineer"
              onChange={(value) => updateField("name_of_chief_engineer", value)}
              value={draft.name_of_chief_engineer}
            />
            {isInjuryReport ? (
              <>
                <SelectField
                  disabled={safeWorkingPracticeOptions.length === 0}
                  label="Code of Safe Working Practices to which the Incident relates"
                  onChange={(value) => updateField("safe_working_practice", value)}
                  options={safeWorkingPracticeOptions}
                  placeholder={
                    safeWorkingPracticeOptions.length === 0
                      ? "Options will be added later"
                      : "Select code"
                  }
                  value={draft.safe_working_practice}
                />
                <NumberField
                  label="Man hours worked"
                  onChange={(value) => updateField("man_hours_worked", value)}
                  value={draft.man_hours_worked}
                />
                <NumberField
                  label="Hours worked on the previous day"
                  onChange={(value) => updateField("hours_worked_previous_day", value)}
                  value={draft.hours_worked_previous_day}
                />
                <NumberField
                  label="Hours of rest in the last 96 hours"
                  onChange={(value) => updateField("hours_rest_last_96_hours", value)}
                  value={draft.hours_rest_last_96_hours}
                />
              </>
            ) : (
              <>
                <SelectField
                  label="Type of Repairs"
                  onChange={(value) => updateField("repair_type", value)}
                  options={workspace.choices.repair_type}
                  value={draft.repair_type}
                />
                <TextField
                  label="Details of temporary / permanent repairs done / required"
                  multiline
                  onChange={(value) => updateField("repair_details", value)}
                  value={draft.repair_details}
                />
                <TextField
                  label="Details of last overhaul / maintenance / survey of equipment"
                  multiline
                  onChange={(value) => updateField("last_overhaul_maintenance_survey_details", value)}
                  value={draft.last_overhaul_maintenance_survey_details}
                />
              </>
            )}
          </FieldGrid>
            </Card>

            <Card eyebrow="Cost Evaluation" title="Cost Evaluation">
          <FieldGrid>
            <TextField
              label="Delays to Vessel (if any)"
              onChange={(value) => updateField("delay_to_vessel", value)}
              value={draft.delay_to_vessel}
            />
            {isInjuryReport ? (
              <>
                <NumberField
                  label="Man hours lost"
                  onChange={(value) => updateField("injury_man_hours_lost", value)}
                  value={draft.injury_man_hours_lost}
                />
                <TextField
                  label="Reasons"
                  multiline
                  onChange={(value) => updateField("injury_reasons", value)}
                  value={draft.injury_reasons}
                />
                <SelectField
                  label="Off Hire"
                  onChange={(value) => updateField("off_hire", value)}
                  options={workspace.choices.yes_no}
                  value={draft.off_hire}
                />
                <SelectField
                  label="Repatriation"
                  onChange={(value) => updateField("repatriation", value)}
                  options={workspace.choices.yes_no}
                  value={draft.repatriation}
                />
                <SelectField
                  label="Hospitalization"
                  onChange={(value) => updateField("hospitalization", value)}
                  options={workspace.choices.yes_no}
                  value={draft.hospitalization}
                />
                <SelectField
                  label="Deviation"
                  onChange={(value) => updateField("deviation", value)}
                  options={workspace.choices.yes_no}
                  value={draft.deviation}
                />
                <SelectField
                  label="Evacuation"
                  onChange={(value) => updateField("evacuation", value)}
                  options={workspace.choices.yes_no}
                  value={draft.evacuation}
                />
              </>
            ) : (
              <>
                <TextField
                  label="Reasons for delay"
                  multiline
                  onChange={(value) => updateField("delay_reason", value)}
                  value={draft.delay_reason}
                />
                <NumberField
                  label="Man hours lost in repairs"
                  onChange={(value) => updateField("repair_man_hours_lost", value)}
                  value={draft.repair_man_hours_lost}
                />
                <TextField
                  label="Materials used for repairs onboard"
                  multiline
                  onChange={(value) => updateField("materials_used_repairs_onboard", value)}
                  value={draft.materials_used_repairs_onboard}
                />
                <TextField
                  label="Specify Details"
                  multiline
                  onChange={(value) => updateField("materials_specify_details", value)}
                  value={draft.materials_specify_details}
                />
                <TextField
                  label="Reasons"
                  multiline
                  onChange={(value) => updateField("materials_reason", value)}
                  value={draft.materials_reason}
                />
                <SelectField
                  label="Deviation"
                  onChange={(value) => updateField("deviation", value)}
                  options={workspace.choices.yes_no}
                  value={draft.deviation}
                />
                <SelectField
                  label="Off Hire"
                  onChange={(value) => updateField("off_hire", value)}
                  options={workspace.choices.yes_no}
                  value={draft.off_hire}
                />
              </>
            )}
          </FieldGrid>
            </Card>

            <Card eyebrow="Estimated Costs" title="Estimated Costs">
          <FieldGrid>
            {isInjuryReport ? (
              <>
                <NumberField
                  label="Cost for Medicines Given Onboard"
                  onChange={(value) => updateField("cost_medicines_onboard", value)}
                  value={draft.cost_medicines_onboard}
                />
                <NumberField
                  label="Cost for Visits to Doctors"
                  onChange={(value) => updateField("cost_doctor_visits", value)}
                  value={draft.cost_doctor_visits}
                />
                <NumberField
                  label="Cost for Repatriation"
                  onChange={(value) => updateField("cost_repatriation", value)}
                  value={draft.cost_repatriation}
                />
                <NumberField
                  label="Cost for Evacuation"
                  onChange={(value) => updateField("cost_evacuation", value)}
                  value={draft.cost_evacuation}
                />
                <NumberField
                  label="Cost for Delays to Vessel if any"
                  onChange={(value) => updateField("cost_injury_delay", value)}
                  value={draft.cost_injury_delay}
                />
                <NumberField
                  label="Cost for Man Hours Lost"
                  onChange={(value) => updateField("cost_injury_man_hours", value)}
                  value={draft.cost_injury_man_hours}
                />
                <NumberField
                  label="Cost for Deviation"
                  onChange={(value) => updateField("cost_injury_deviation", value)}
                  value={draft.cost_injury_deviation}
                />
                <NumberField
                  label="Cost for Miscellaneous Expenses"
                  onChange={(value) => updateField("cost_injury_miscellaneous", value)}
                  value={draft.cost_injury_miscellaneous}
                />
                <TextField
                  label="Reasons for Miscellaneous Expenses"
                  multiline
                  onChange={(value) => updateField("injury_miscellaneous_expenses_reason", value)}
                  value={draft.injury_miscellaneous_expenses_reason}
                />
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Total Estimated cost</span>
                  <input
                    className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-slate-100 px-3 text-sm font-semibold text-slate-900"
                    readOnly
                    value={injuryTotal ?? ""}
                  />
                </label>
              </>
            ) : (
              <>
                <NumberField
                  label="Estimated Cost for Off Hire"
                  onChange={(value) => updateField("estimated_cost_off_hire", value)}
                  value={draft.estimated_cost_off_hire}
                />
                <NumberField
                  label="Estimated Cost for Delays to Vessel if any"
                  onChange={(value) => updateField("estimated_cost_delay", value)}
                  value={draft.estimated_cost_delay}
                />
                <NumberField
                  label="Estimated Cost for Man Hour Lost"
                  onChange={(value) => updateField("estimated_cost_man_hours", value)}
                  value={draft.estimated_cost_man_hours}
                />
                <NumberField
                  label="Estimated Cost for Deviation"
                  onChange={(value) => updateField("estimated_cost_deviation", value)}
                  value={draft.estimated_cost_deviation}
                />
                <NumberField
                  label="Estimated Cost for Materials used in Repairs"
                  onChange={(value) => updateField("estimated_cost_materials", value)}
                  value={draft.estimated_cost_materials}
                />
                <NumberField
                  label="Estimated Cost for Miscellaneous Expenses"
                  onChange={(value) => updateField("estimated_cost_miscellaneous", value)}
                  value={draft.estimated_cost_miscellaneous}
                />
                <TextField
                  label="Reasons for Miscellaneous Expenses"
                  multiline
                  onChange={(value) => updateField("miscellaneous_expenses_reason", value)}
                  value={draft.miscellaneous_expenses_reason}
                />
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">Total Estimated cost</span>
                  <input
                    className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-slate-100 px-3 text-sm font-semibold text-slate-900"
                    readOnly
                    value={incidentTotal ?? ""}
                  />
                </label>
              </>
            )}
          </FieldGrid>
            </Card>
          </>
        ) : (
          <section className="rounded-3xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">
            Choose a Loss Evaluation type to continue.
          </section>
        )}

        <button
          className="min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
          disabled={isMutating || !reportTypeSelected}
          type="submit"
        >
          {isMutating ? "Saving..." : "Save Loss Evaluation"}
        </button>
      </form>

      <Link
        className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
        to={`/safety/incidents/${id}/phase-5`}
      >
        Back to Office Review
      </Link>
    </section>
  );
}

export default SafetyIncidentPhase8;
