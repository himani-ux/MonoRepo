import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi, type SafetyOfficeWorkflowPayload } from "../../../lib/api/safety";
import {
  safetyIncidentPhase5WorkspaceSchema,
  type SafetyBiasGuard,
  type SafetyIncidentAnalysisTool,
  type SafetyIncidentCauseLayer,
  type SafetyIncidentPhase5Workspace,
} from "../../../schemas/safety/incident-phase5";
import { SafetyMscatPicker } from "../shared/reference-pickers";
import SafetyBiasGuardChecklist from "../shared/bias-guard-checklist";
import SafetyCausalLayerTabs from "../shared/causal-layer-tabs";
import SafetyHumanFactorsPanel from "./human-factors-panel";
import SafetyMultiToolWorkspace from "./multi-tool-workspace";
import SafetyPeopleProcessPlantInterrogatory from "./people-process-plant-interrogatory";
import SafetySafeguardFailureInterrogatory from "./safeguard-failure-interrogatory";

const ANALYSIS_TOOLS = ["STEP", "FACT_TREE", "ECF", "BARRIER", "CHANGE"] as const;
const CAUSAL_LAYERS = ["IMMEDIATE", "INTERMEDIATE", "ROOT"] as const;
const BIAS_STATES = ["PASSED", "WARNED", "BLOCKED", "JUSTIFIED", "OVERRIDE", "SOFTWARN_OVERRIDE"] as const;
const SAFEGUARD_FIELDS = [
  ["design_mscat_subcode_id", "Design"],
  ["installation_mscat_subcode_id", "Installation"],
  ["maintenance_mscat_subcode_id", "Maintenance"],
  ["operation_mscat_subcode_id", "Operation"],
  ["testing_mscat_subcode_id", "Testing"],
  ["override_mscat_subcode_id", "Override"],
] as const;
const SHELL_OPTIONS = [
  ["software", "Software", "Procedures, manuals, charts, and computer programs."],
  ["hardware", "Hardware", "Equipment, controls, displays, and ergonomics."],
  ["environment", "Environment", "Weather, fatigue, noise, climate, and working conditions."],
  ["liveware_central", "Liveware - central", "The person, capability, state, and limits."],
  ["liveware_peripheral", "Liveware - peripheral", "Other people, supervision, teamwork, and ship-shore communication."],
] as const;
const HUMAN_FACTOR_DOMAINS = [
  ["people", "People", "Qualifications, experience, fatigue, health."],
  ["organization_on_board", "Organization on board", "Task division, manning, communication, workload, hours/rest."],
  ["working_living_conditions", "Working & living conditions", "Ergonomics, recreation, food, motion, and noise."],
  ["ship_factors", "Ship factors", "Design, maintenance, equipment, and cargo."],
  ["shore_side_management", "Shore-side management", "Recruitment, scheduling, contracts, and ship-shore communication."],
  ["external_influences_environment", "External influences & environment", "Weather, traffic, regulations, inspections."],
  ["sequence_of_events", "Sequence of events", "Timeline and immediate conditions."],
  ["risk_change", "Risk & Change Management", "Risk controls, monitoring gaps, change management, regulatory compliance."],
] as const;
const TOOL_WORKSPACE_FIELDS = {
  STEP: [
    ["swimlane_notes", "Actor/time swimlane"],
    ["sequence_gaps", "Sequence gaps"],
  ],
  FACT_TREE: [
    ["backward_chain", "Backward chain"],
    ["evidence_leaf_gaps", "Evidence leaf gaps"],
  ],
  ECF: [
    ["event_condition_chart", "Event/condition chart"],
    ["presumptive_links", "Presumptive links"],
  ],
  BARRIER: [
    ["hazard_barriers", "Hazard/barrier table"],
    ["failure_effect", "Failure effect"],
  ],
  CHANGE: [
    ["incident_prior_difference_effect", "Incident/prior/difference/effect"],
    ["change_control_gaps", "Change-control gaps"],
  ],
} as const satisfies Record<SafetyIncidentAnalysisTool, ReadonlyArray<readonly [string, string]>>;

type SafeguardDraft = Record<(typeof SAFEGUARD_FIELDS)[number][0], string> & {
  notes: string;
  safeguard_name: string;
};
type HumanFactorDomainKey = (typeof HUMAN_FACTOR_DOMAINS)[number][0];
type HumanFactorDomainDraft = {
  considered: boolean;
  not_applicable: boolean;
  notes: string;
};
type ToolWorkspaceDraft = Record<SafetyIncidentAnalysisTool, Record<string, string>>;

const emptySafeguardDraft: SafeguardDraft = {
  design_mscat_subcode_id: "",
  installation_mscat_subcode_id: "",
  maintenance_mscat_subcode_id: "",
  notes: "",
  operation_mscat_subcode_id: "",
  override_mscat_subcode_id: "",
  safeguard_name: "",
  testing_mscat_subcode_id: "",
};
const emptyHumanFactorDomains = Object.fromEntries(
  HUMAN_FACTOR_DOMAINS.map(([key]) => [
    key,
    { considered: false, not_applicable: false, notes: "" },
  ]),
) as Record<HumanFactorDomainKey, HumanFactorDomainDraft>;
const emptyToolWorkspaces = Object.fromEntries(
  ANALYSIS_TOOLS.map((tool) => [
    tool,
    Object.fromEntries(TOOL_WORKSPACE_FIELDS[tool].map(([field]) => [field, ""])),
  ]),
) as ToolWorkspaceDraft;

function emptyWorkspace(): SafetyIncidentPhase5Workspace {
  return {
    analysis_tools_used: [],
    assessment: null,
    bias_guards: [],
    blame_evaluation: {
      all_root_personal_factors: false,
      blocked: false,
      has_lack_of_control: false,
      override_by: null,
      trigger_terms: [],
    },
    causes: [],
    facts: [],
    incident_id: 0,
    investigation_depth: null,
    matrix_rows: [],
    minimum_tools_required: 2,
    safeguards: [],
  };
}

function toolLabel(tool: string) {
  return tool === "FACT_TREE" ? "Fact Tree" : tool;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function toHumanFactorDomains(value: unknown): Record<HumanFactorDomainKey, HumanFactorDomainDraft> {
  const saved = asRecord(value);
  return Object.fromEntries(
    HUMAN_FACTOR_DOMAINS.map(([key]) => {
      const domain = asRecord(saved[key]);
      return [
        key,
        {
          considered: Boolean(domain.considered),
          not_applicable: Boolean(domain.not_applicable ?? domain.na),
          notes: String(domain.notes ?? ""),
        },
      ];
    }),
  ) as Record<HumanFactorDomainKey, HumanFactorDomainDraft>;
}

function toToolWorkspaces(value: unknown): ToolWorkspaceDraft {
  const saved = asRecord(value);
  return Object.fromEntries(
    ANALYSIS_TOOLS.map((tool) => {
      const toolPayload = asRecord(saved[tool]);
      return [
        tool,
        Object.fromEntries(
          TOOL_WORKSPACE_FIELDS[tool].map(([field]) => [field, String(toolPayload[field] ?? "")]),
        ),
      ];
    }),
  ) as ToolWorkspaceDraft;
}

export function SafetyIncidentPhase5() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<SafetyIncidentPhase5Workspace>(emptyWorkspace());
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [phaseAdvanceError, setPhaseAdvanceError] = useState<string | null>(null);

  const [peopleText, setPeopleText] = useState("");
  const [processText, setProcessText] = useState("");
  const [plantText, setPlantText] = useState("");
  const [selectedTools, setSelectedTools] = useState<SafetyIncidentAnalysisTool[]>([]);
  const [hfNotes, setHfNotes] = useState("");
  const [shellSelection, setShellSelection] = useState("");
  const [shellNotes, setShellNotes] = useState("");
  const [humanFactorDomains, setHumanFactorDomains] = useState(emptyHumanFactorDomains);
  const [toolWorkspaces, setToolWorkspaces] = useState(emptyToolWorkspaces);
  const [monocausalJustification, setMonocausalJustification] = useState("");
  const [confirmationOverrideReason, setConfirmationOverrideReason] = useState("");

  const [sourceFactId, setSourceFactId] = useState("");
  const [causeSubcode, setCauseSubcode] = useState<string | null>(null);
  const [causeLayer, setCauseLayer] = useState<SafetyIncidentCauseLayer>("ROOT");
  const [causeTool, setCauseTool] = useState<SafetyIncidentAnalysisTool>("FACT_TREE");
  const [causeRationale, setCauseRationale] = useState("");

  const [safeguardDraft, setSafeguardDraft] = useState<SafeguardDraft>(emptySafeguardDraft);
  const [biasDraft, setBiasDraft] = useState<Record<string, SafetyBiasGuard>>({});

  const reload = useCallback(async () => {
    if (!id) {
      setError("Invalid incident id.");
      setIsLoading(false);
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const response = await safetyApi.getIncidentPhase5Workspace(id);
      const parsed = safetyIncidentPhase5WorkspaceSchema.parse(response);
      setWorkspace(parsed);
      setPeopleText(parsed.assessment?.people_contribution_text ?? "");
      setProcessText(parsed.assessment?.process_gap_text ?? "");
      setPlantText(parsed.assessment?.plant_failure_text ?? "");
      setSelectedTools(parsed.assessment?.analysis_tools_used ?? []);
      const humanFactors = parsed.assessment?.human_factors_payload ?? {};
      const shell = asRecord(humanFactors.shell);
      setHfNotes(String(humanFactors.summary ?? ""));
      setShellSelection(String(shell.selected ?? humanFactors.shell_tag ?? ""));
      setShellNotes(String(shell.notes ?? ""));
      setHumanFactorDomains(toHumanFactorDomains(humanFactors.domains));
      setToolWorkspaces(toToolWorkspaces(humanFactors.tool_workspaces));
      setMonocausalJustification(parsed.assessment?.monocausal_justification ?? "");
      setConfirmationOverrideReason(parsed.assessment?.confirmation_override_reason ?? "");
      setBiasDraft(Object.fromEntries(parsed.bias_guards.map((guard) => [guard.guard_code, guard])));
      setSourceFactId(parsed.facts[0]?.id ? String(parsed.facts[0].id) : "");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const rootCauseCount = useMemo(
    () => workspace.causes.filter((cause) => cause.causal_layer === "ROOT").length,
    [workspace.causes],
  );
  const phase5GateHints = useMemo(() => {
    const hints: string[] = [];
    if (rootCauseCount < 1) {
      hints.push("Add at least one Root cause.");
    }
    if (rootCauseCount === 1 && monocausalJustification.trim().length < 80) {
      hints.push("Add an 80+ character monocausal justification, or add another Root cause.");
    }
    [
      ["People", peopleText],
      ["Process", processText],
      ["Plant", plantText],
    ].forEach(([label, value]) => {
      if (value.trim().length < 50) {
        hints.push(`${label} analysis must be at least 50 characters.`);
      }
    });
    if (selectedTools.length < workspace.minimum_tools_required) {
      hints.push(`Select at least ${workspace.minimum_tools_required} analysis tool(s).`);
    }
    const riskChange = humanFactorDomains.risk_change;
    if (!riskChange.considered && !riskChange.not_applicable && !riskChange.notes.trim()) {
      hints.push("Complete Human Factors / risk change.");
    }
    if (workspace.safeguards.length < 1) {
      hints.push("Add at least one safeguard failure with all six dimensions.");
    }
    const acknowledged = workspace.bias_guards.filter((guard) => guard.acknowledged).length;
    if (acknowledged < workspace.bias_guards.length) {
      hints.push("Acknowledge all active bias guards.");
    }
    return hints;
  }, [
    monocausalJustification,
    peopleText,
    plantText,
    processText,
    humanFactorDomains,
    rootCauseCount,
    selectedTools.length,
    workspace.bias_guards,
    workspace.minimum_tools_required,
    workspace.safeguards.length,
  ]);

  async function saveAssessment(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      const response = await safetyApi.updateIncidentPhase5Workspace(id, {
        analysis_tools_used: selectedTools,
        confirmation_override_reason: confirmationOverrideReason.trim() || null,
        human_factors_payload: {
          domains: {
            ...humanFactorDomains,
          },
          shell: {
            notes: shellNotes,
            selected: shellSelection,
          },
          // The backend currently exposes one JSON assessment payload for Phase 5 extras.
          // Keep structured tool notes here until dedicated tool tables exist.
          tool_workspaces: toolWorkspaces,
          summary: hfNotes,
        },
        monocausal_justification: monocausalJustification.trim() || null,
        people_contribution_text: peopleText,
        plant_failure_text: plantText,
        process_gap_text: processText,
      });
      setWorkspace(safetyIncidentPhase5WorkspaceSchema.parse(response));
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  function updateHumanFactorDomain(
    key: HumanFactorDomainKey,
    patch: Partial<HumanFactorDomainDraft>,
  ) {
    setHumanFactorDomains((current) => ({
      ...current,
      [key]: { ...current[key], ...patch },
    }));
  }

  function updateToolWorkspace(
    tool: SafetyIncidentAnalysisTool,
    field: string,
    value: string,
  ) {
    setToolWorkspaces((current) => ({
      ...current,
      [tool]: { ...current[tool], [field]: value },
    }));
  }

  async function createCause(event: FormEvent) {
    event.preventDefault();
    if (!id || !causeSubcode) {
      setError("Select a source fact and M-SCAT code before adding a cause.");
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.createIncidentPhase5Cause(id, {
        analysis_tool: causeTool,
        causal_layer: causeLayer,
        mscat_subcode_id: causeSubcode,
        rationale: causeRationale,
        source_fact_id: sourceFactId,
      });
      setCauseRationale("");
      setCauseSubcode(null);
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function createSafeguard(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.createIncidentPhase5Safeguard(id, safeguardDraft as SafetyOfficeWorkflowPayload);
      setSafeguardDraft(emptySafeguardDraft);
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function saveBiasGuards() {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.submitIncidentBiasGuards(id, {
        responses: Object.values(biasDraft).map((guard) => ({
          acknowledged: guard.acknowledged,
          evaluation_state: guard.evaluation_state,
          guard_code: guard.guard_code,
          justification: guard.justification ?? "",
        })),
      });
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function continueToPhase6() {
    if (!id) {
      return;
    }
    setPhaseAdvanceError(null);
    setIsMutating(true);
    try {
      await safetyApi.transitionIncident(id, { target_phase: 6 });
      navigate(`/safety/incidents/${id}/phase-6`);
    } catch (caught) {
      setPhaseAdvanceError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Incident / Phase 5
        </p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Causal Analysis</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Build cause tags from facts, complete People / Process / Plant analysis, map safeguards, and close the bias guards.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Root</div>
              <div className="mt-1 font-semibold text-slate-900">{rootCauseCount}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Tools</div>
              <div className="mt-1 font-semibold text-slate-900">{selectedTools.length}/{workspace.minimum_tools_required}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Guards</div>
              <div className="mt-1 font-semibold text-slate-900">
                {workspace.bias_guards.filter((guard) => guard.acknowledged).length}/{workspace.bias_guards.length}
              </div>
            </div>
          </div>
        </div>
      </header>

      {error ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section> : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading Phase 5...</section>
      ) : (
        <>
          <SafetyCausalLayerTabs causes={workspace.causes} />

          <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={createCause}>
            <h2 className="text-xl font-semibold text-slate-900">Add M-SCAT Cause</h2>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">
                Source fact
                <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setSourceFactId(event.target.value)} value={sourceFactId}>
                  <option value="">Select fact</option>
                  {workspace.facts.map((fact) => (
                    <option key={fact.id} value={fact.id}>
                      #{fact.sequence_index} {fact.fact_text}
                    </option>
                  ))}
                </select>
              </label>
              <SafetyMscatPicker onChange={(value) => setCauseSubcode(value.subcodeId)} value={{ subcodeId: causeSubcode }} />
              <label className="block text-sm font-medium text-slate-700">
                Causal layer
                <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setCauseLayer(event.target.value as SafetyIncidentCauseLayer)} value={causeLayer}>
                  {CAUSAL_LAYERS.map((layer) => <option key={layer} value={layer}>{layer}</option>)}
                </select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Analysis tool
                <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setCauseTool(event.target.value as SafetyIncidentAnalysisTool)} value={causeTool}>
                  {ANALYSIS_TOOLS.map((tool) => <option key={tool} value={tool}>{toolLabel(tool)}</option>)}
                </select>
              </label>
            </div>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Rationale
              <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setCauseRationale(event.target.value)} value={causeRationale} />
            </label>
            <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !sourceFactId || !causeSubcode || !causeRationale.trim()} type="submit">
              Add cause
            </button>
          </form>

          <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={saveAssessment}>
            <h2 className="text-xl font-semibold text-slate-900">Analysis Assessment</h2>
            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              {[
                ["People", peopleText, setPeopleText],
                ["Process", processText, setProcessText],
                ["Plant", plantText, setPlantText],
              ].map(([label, value, setter]) => (
                <label className="block text-sm font-medium text-slate-700" key={label as string}>
                  {label as string}
                  <textarea className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => (setter as (value: string) => void)(event.target.value)} value={value as string} />
                  <span className="mt-1 block text-xs text-slate-500">{(value as string).trim().length}/50 characters</span>
                </label>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              {ANALYSIS_TOOLS.map((tool) => (
                <label key={tool} className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700">
                  <input
                    checked={selectedTools.includes(tool)}
                    onChange={(event) =>
                      setSelectedTools((current) =>
                        event.target.checked ? [...current, tool] : current.filter((item) => item !== tool),
                      )
                    }
                    type="checkbox"
                  />
                  {toolLabel(tool)}
                </label>
              ))}
            </div>
            <div className="mt-4 grid gap-4 xl:grid-cols-2">
              {ANALYSIS_TOOLS.map((tool) => (
                <section key={tool} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="font-semibold text-slate-900">{toolLabel(tool)}</h3>
                    <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium uppercase tracking-[0.14em] text-slate-600">
                      {selectedTools.includes(tool) ? "Selected" : "Not selected"}
                    </span>
                  </div>
                  <div className="mt-3 grid gap-3">
                    {TOOL_WORKSPACE_FIELDS[tool].map(([field, label]) => (
                      <label className="block text-sm font-medium text-slate-700" key={field}>
                        {label}
                        <textarea
                          className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 bg-white p-3"
                          onChange={(event) => updateToolWorkspace(tool, field, event.target.value)}
                          value={toolWorkspaces[tool][field] ?? ""}
                        />
                      </label>
                    ))}
                  </div>
                </section>
              ))}
            </div>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Human factors notes
              <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setHfNotes(event.target.value)} value={hfNotes} />
            </label>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">SHELL tag</p>
              <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
                {SHELL_OPTIONS.map(([value, label, description]) => (
                  <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-3 text-sm text-slate-700" key={value}>
                    <input
                      checked={shellSelection === value}
                      className="mt-1 h-4 w-4"
                      onChange={() => setShellSelection(value)}
                      type="radio"
                    />
                    <span>
                      <span className="block font-medium text-slate-900">{label}</span>
                      <span className="mt-1 block leading-5 text-slate-600">{description}</span>
                    </span>
                  </label>
                ))}
              </div>
              <label className="mt-3 block text-sm font-medium text-slate-700">
                SHELL notes
                <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 bg-white p-3" onChange={(event) => setShellNotes(event.target.value)} value={shellNotes} />
              </label>
            </div>
            <div className="mt-4 grid gap-4 xl:grid-cols-2">
              {HUMAN_FACTOR_DOMAINS.map(([key, label, prompt]) => {
                const domain = humanFactorDomains[key];
                return (
                  <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4" key={key}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-slate-900">{label}</h3>
                        <p className="mt-1 text-sm leading-5 text-slate-600">{prompt}</p>
                      </div>
                      <div className="flex flex-wrap gap-3 text-sm text-slate-700">
                        <label className="inline-flex items-center gap-2">
                          <input
                            checked={domain.considered}
                            onChange={(event) => updateHumanFactorDomain(key, { considered: event.target.checked })}
                            type="checkbox"
                          />
                          Considered
                        </label>
                        <label className="inline-flex items-center gap-2">
                          <input
                            checked={domain.not_applicable}
                            onChange={(event) => updateHumanFactorDomain(key, { not_applicable: event.target.checked })}
                            type="checkbox"
                          />
                          N/A
                        </label>
                      </div>
                    </div>
                    <textarea
                      className="mt-3 min-h-20 w-full rounded-2xl border border-slate-300 bg-white p-3 text-sm"
                      onChange={(event) => updateHumanFactorDomain(key, { notes: event.target.value })}
                      placeholder="Notes / rationale"
                      value={domain.notes}
                    />
                  </section>
                );
              })}
            </div>
            {rootCauseCount === 1 ? (
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Monocausal justification
                <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setMonocausalJustification(event.target.value)} value={monocausalJustification} />
                <span className="mt-1 block text-xs text-slate-500">{monocausalJustification.trim().length}/80 characters</span>
              </label>
            ) : null}
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Confirmation-bias override reason
              <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setConfirmationOverrideReason(event.target.value)} value={confirmationOverrideReason} />
            </label>
            <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating} type="submit">
              Save assessment
            </button>
          </form>

          <div className="grid gap-6 xl:grid-cols-2">
            <SafetyPeopleProcessPlantInterrogatory assessment={workspace.assessment} />
            <SafetyMultiToolWorkspace
              assessment={workspace.assessment}
              minimumToolsRequired={workspace.minimum_tools_required}
              toolWorkspaces={toolWorkspaces}
            />
            <SafetyHumanFactorsPanel assessment={workspace.assessment} />
            <SafetySafeguardFailureInterrogatory safeguards={workspace.safeguards} />
          </div>

          <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={createSafeguard}>
            <h2 className="text-xl font-semibold text-slate-900">Add Safeguard Failure</h2>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Safeguard name
              <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setSafeguardDraft((current) => ({ ...current, safeguard_name: event.target.value }))} value={safeguardDraft.safeguard_name} />
            </label>
            <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {SAFEGUARD_FIELDS.map(([field, label]) => (
                <div key={field}>
                  <p className="mb-2 text-sm font-medium text-slate-700">{label}</p>
                  <SafetyMscatPicker
                    label={`${label} M-SCAT code`}
                    onChange={(value) => setSafeguardDraft((current) => ({ ...current, [field]: value.subcodeId ?? "" }))}
                    value={{ subcodeId: safeguardDraft[field] }}
                  />
                </div>
              ))}
            </div>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Notes
              <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setSafeguardDraft((current) => ({ ...current, notes: event.target.value }))} value={safeguardDraft.notes} />
            </label>
            <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || !safeguardDraft.safeguard_name.trim()} type="submit">
              Add safeguard
            </button>
          </form>

          <SafetyBiasGuardChecklist guards={workspace.bias_guards} />
          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Complete Bias Guards</h2>
            <div className="mt-4 grid gap-3">
              {workspace.bias_guards.map((guard) => {
                const draft = biasDraft[guard.guard_code] ?? guard;
                return (
                  <article key={guard.guard_code} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="grid gap-3 lg:grid-cols-[1fr_180px_140px]">
                      <div>
                        <h3 className="font-semibold text-slate-900">{guard.guard_name}</h3>
                        <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{guard.family}</p>
                      </div>
                      <select className="min-h-11 rounded-2xl border border-slate-300 px-3" onChange={(event) => setBiasDraft((current) => ({ ...current, [guard.guard_code]: { ...draft, evaluation_state: event.target.value as SafetyBiasGuard["evaluation_state"] } }))} value={draft.evaluation_state}>
                        {BIAS_STATES.map((state) => <option key={state} value={state}>{state.replaceAll("_", " ")}</option>)}
                      </select>
                      <label className="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                        <input checked={draft.acknowledged} onChange={(event) => setBiasDraft((current) => ({ ...current, [guard.guard_code]: { ...draft, acknowledged: event.target.checked } }))} type="checkbox" />
                        Acknowledge
                      </label>
                    </div>
                    <textarea className="mt-3 min-h-16 w-full rounded-2xl border border-slate-300 p-3 text-sm" onChange={(event) => setBiasDraft((current) => ({ ...current, [guard.guard_code]: { ...draft, justification: event.target.value } }))} placeholder="Justification / override note" value={draft.justification ?? ""} />
                  </article>
                );
              })}
            </div>
            <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating} onClick={() => void saveBiasGuards()} type="button">
              Save bias guards
            </button>
          </section>
        </>
      )}

      {workspace.blame_evaluation.blocked ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          Blame-fixation guard is blocking Phase 6. Trigger terms: {workspace.blame_evaluation.trigger_terms.join(", ") || "review required"}.
        </section>
      ) : null}
      {phase5GateHints.length > 0 ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-semibold">Phase 6 gate still needs:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {phase5GateHints.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {phaseAdvanceError ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{phaseAdvanceError}</section> : null}

      <div className="flex flex-wrap gap-3">
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/phase-4`}>
          Back to Phase 4
        </Link>
        <button className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating} onClick={continueToPhase6} type="button">
          {isMutating ? "Checking gate..." : "Continue to Phase 6"}
        </button>
      </div>
    </section>
  );
}

export default SafetyIncidentPhase5;
