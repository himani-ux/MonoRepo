import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../../../hooks/use-auth";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import type {
  SafetyIncidentLossEvaluation,
  SafetyLossEvaluationOption,
  SafetyLossEvaluationReportType,
  SafetyPhase8WorkspacePayload,
} from "../../../schemas/safety/incident-phase8";

type LossEvaluationDraft = Omit<SafetyIncidentLossEvaluation, "id" | "updated_date">;

const PIC_ROLES = new Set([
  "PIC",
  "VESSEL SUPERINTENDENT",
  "OFFICE_PIC",
  "OFFICE_SSQE",
  "OFFICE_SUPT",
]);
const OFFICE_DECISION_ROLES = new Set(["DPA", ...PIC_ROLES]);

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
      consequence: [],
      likelihood: [],
      repair_type: [],
      report_type: [
        { label: "Incident Report", value: "INCIDENT" },
        { label: "Injury Report", value: "INJURY" },
      ],
      risk_level: [],
      safe_working_practice: [],
      yes_no: [
        { label: "Yes", value: true },
        { label: "No", value: false },
      ],
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

function normalizeCode(value: unknown) {
  return String(value ?? "").trim().toUpperCase();
}

function roleCanAct(role: string) {
  return OFFICE_DECISION_ROLES.has(role);
}

function displayText(value: string | null | undefined) {
  return String(value ?? "").trim();
}

function decimalInputValue(value: string | null | undefined) {
  return value == null ? "" : String(value);
}

function toOptionalString(value: string) {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
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

function cleanPayload(draft: LossEvaluationDraft, reportType: SafetyLossEvaluationReportType) {
  const payload: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(draft)) {
    payload[key] = value === "" ? null : value;
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
          onChange={(event) => onChange(toOptionalString(event.target.value))}
          value={displayText(value)}
        />
      ) : (
        <input
          className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
          onChange={(event) => onChange(toOptionalString(event.target.value))}
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
  const navigate = useNavigate();
  const { role, user } = useAuth();
  const noticeRef = useRef<HTMLDivElement | null>(null);
  const [workspace, setWorkspace] = useState<SafetyPhase8WorkspacePayload>(emptyWorkspace());
  const [draft, setDraft] = useState<LossEvaluationDraft>(commonEmptyDraft);
  const [closureReason, setClosureReason] = useState("");
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
      const normalizedPayload = {
        ...emptyWorkspace(),
        ...payload,
        blocker_details: payload.blocker_details ?? [],
        blockers: payload.blockers ?? [],
        choices: {
          ...emptyWorkspace().choices,
          ...(payload.choices ?? {}),
        },
        loss_evaluation: {
          ...emptyWorkspace().loss_evaluation,
          ...(payload.loss_evaluation ?? {}),
        },
      };
      setWorkspace(normalizedPayload);
      const nextDraft = mergeDraft(normalizedPayload.loss_evaluation);
      if (normalizedPayload.has_loss_evaluation && !nextDraft.report_type) {
        nextDraft.report_type = normalizedPayload.report_type;
      }
      setDraft(nextDraft);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const currentRole = normalizeCode(user?.role || role || user?.safety_role_name || user?.role_name);
  const selectedReportType = draft.report_type;
  const reportTypeSelected = selectedReportType !== null;
  const isInjuryReport = selectedReportType === "INJURY";
  const reportLabel = selectedReportType
    ? isInjuryReport
      ? "Injury Report"
      : "Incident Report"
    : "Choose report type";
  const canClose = roleCanAct(currentRole);
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
      setWorkspace({
        ...emptyWorkspace(),
        ...response,
        choices: {
          ...emptyWorkspace().choices,
          ...(response.choices ?? {}),
        },
        loss_evaluation: {
          ...emptyWorkspace().loss_evaluation,
          ...(response.loss_evaluation ?? {}),
        },
      });
      const nextDraft = mergeDraft(response.loss_evaluation);
      if (!nextDraft.report_type) {
        nextDraft.report_type = response.report_type;
      }
      setDraft(nextDraft);
      setResultMessage("Loss Evaluation saved.");
      window.setTimeout(() => noticeRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } catch (caught) {
      setError(getErrorMessage(caught));
      window.setTimeout(() => noticeRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
    } finally {
      setIsMutating(false);
    }
  }

  async function closeIncident(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    setResultMessage(null);
    try {
      await safetyApi.closeIncidentPhase8(id, { closure_reason: closureReason });
      navigate("/safety/incidents");
    } catch (caught) {
      setError(getErrorMessage(caught));
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

      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">Phase 7</p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-950">Loss Evaluation</h1>
            <p className="mt-3 text-sm text-slate-600">{reportLabel}</p>
          </div>
          <span className="w-fit rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">
            {workspace.has_loss_evaluation ? "Saved" : "Not saved"}
          </span>
        </div>
      </header>

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
          <p className="mt-3 text-sm text-slate-600">
            Select Incident Report or Injury Report first. The form below will change based on this choice.
          </p>
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

      <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={closeIncident}>
        <h2 className="text-xl font-semibold text-slate-950">Close Incident</h2>
        {!canClose ? (
          <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            Office role is required to close the incident.
          </p>
        ) : null}
        {!workspace.ready_for_close ? (
          <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            Save Loss Evaluation before closing.
          </p>
        ) : null}
        <label className="mt-4 block text-sm font-medium text-slate-700">
          Closing note
          <textarea
            className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
            onChange={(event) => setClosureReason(event.target.value)}
            value={closureReason}
          />
        </label>
        <button
          className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
          disabled={isMutating || !canClose || !workspace.ready_for_close || !closureReason.trim()}
          type="submit"
        >
          {isMutating ? "Closing..." : "Close Incident"}
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
