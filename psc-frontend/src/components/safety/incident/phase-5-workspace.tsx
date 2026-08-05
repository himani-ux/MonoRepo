import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent, type RefObject } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../../../lib/api/client";
import {
  safetyApi,
  type SafetyNearMissCauseOption,
  type SafetyOfficeWorkflowPayload,
} from "../../../lib/api/safety";
import { SAFETY_NEAR_MISS_CAUSE_FACTORS } from "../../../schemas/safety/near-miss";
import {
  safetyIncidentPhase5WorkspaceSchema,
  type SafetyBiasGuard,
  type SafetyIncidentAnalysisTool,
  type SafetyIncidentCauseTag,
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
type CurrentCauseLayer = Extract<SafetyIncidentCauseLayer, "IMMEDIATE" | "ROOT">;
const CAUSAL_LAYERS = ["IMMEDIATE", "ROOT"] as const satisfies CurrentCauseLayer[];
const BIAS_STATES = ["PASSED", "WARNED", "BLOCKED", "JUSTIFIED", "OVERRIDE", "SOFTWARN_OVERRIDE"] as const;
const MAX_ROOT_CAUSES = 3;
const OTHER_ROOT_CAUSE_SUBCODE = "OTHER";
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
const showTechnicalAnalysisPanels = false;

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
type IncidentCauseFactor = (typeof SAFETY_NEAR_MISS_CAUSE_FACTORS)[number]["value"];

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

function causeLayerLabel(layer: CurrentCauseLayer) {
  if (layer === "IMMEDIATE") {
    return "Immediate Cause";
  }
  return "Root Cause";
}

function causeStageForLayer(layer: CurrentCauseLayer): SafetyNearMissCauseOption["cause_stage"] {
  return layer === "IMMEDIATE" ? "IMMEDIATE" : "ROOT";
}

function currentCauseLayer(cause: SafetyIncidentCauseTag): CurrentCauseLayer {
  return cause.causal_layer === "IMMEDIATE" ? "IMMEDIATE" : "ROOT";
}

function causeOptionsFor(
  options: SafetyNearMissCauseOption[],
  factor: IncidentCauseFactor,
  causeStage: SafetyNearMissCauseOption["cause_stage"],
) {
  return options
    .filter((option) => option.factor === factor && option.cause_stage === causeStage && option.active)
    .sort((left, right) => left.display_order - right.display_order);
}

function isOtherCauseOption(option?: SafetyNearMissCauseOption | null) {
  return String(option?.option_text ?? "").trim().toLowerCase() === "other";
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
  const [saveNotice, setSaveNotice] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [phaseAdvanceError, setPhaseAdvanceError] = useState<string | null>(null);
  const savedCausesRef = useRef<HTMLDivElement>(null);
  const causeFormRef = useRef<HTMLFormElement>(null);

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

  const [causeOptions, setCauseOptions] = useState<SafetyNearMissCauseOption[]>([]);
  const [causeFactor, setCauseFactor] = useState<IncidentCauseFactor>("HUMAN");
  const [causeOptionId, setCauseOptionId] = useState("");
  const [otherCauseText, setOtherCauseText] = useState("");
  const [causeLayer, setCauseLayer] = useState<CurrentCauseLayer>("ROOT");
  const [causeTool, setCauseTool] = useState<SafetyIncidentAnalysisTool>("FACT_TREE");
  const [causeRationale, setCauseRationale] = useState("");
  const [editingCauseId, setEditingCauseId] = useState<string | null>(null);

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
    } catch (caught) {
      const message = getErrorMessage(caught);
      if (message.includes("Submit resource handoff") || message.includes("Submit office communication")) {
        navigate(`/safety/incidents/${id}/office-communication`, {
          replace: true,
          state: {
            workflowMessage: "Confirm office communication first. Root cause can be added after that.",
          },
        });
        return;
      }
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    let cancelled = false;
    safetyApi
      .getNearMissCauseOptions()
      .then((options) => {
        if (!cancelled) {
          setCauseOptions(options);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCauseOptions([]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const rootCauseCount = useMemo(
    () => workspace.causes.filter((cause) => cause.causal_layer === "ROOT").length,
    [workspace.causes],
  );
  const causeLayerCounts = useMemo(
    () =>
      Object.fromEntries(
        CAUSAL_LAYERS.map((layer) => [
          layer,
          workspace.causes.filter((cause) => cause.causal_layer === layer).length,
        ]),
      ) as Record<CurrentCauseLayer, number>,
    [workspace.causes],
  );
  const phase5GateHints = useMemo(() => {
    const hints: string[] = [];
    CAUSAL_LAYERS.forEach((layer) => {
      if ((causeLayerCounts[layer] ?? 0) < 1) {
        hints.push(`Add at least one ${causeLayerLabel(layer)}.`);
      }
    });
    return hints;
  }, [causeLayerCounts]);
  const availableCauseOptions = useMemo(
    () => causeOptionsFor(causeOptions, causeFactor, causeStageForLayer(causeLayer)),
    [causeFactor, causeLayer, causeOptions],
  );
  const selectedCauseOption = useMemo(
    () => availableCauseOptions.find((option) => option.id === causeOptionId) ?? null,
    [availableCauseOptions, causeOptionId],
  );
  const selectedCauseIsOther = isOtherCauseOption(selectedCauseOption);
  const editingCause = useMemo(
    () => workspace.causes.find((cause) => cause.id === editingCauseId) ?? null,
    [editingCauseId, workspace.causes],
  );
  const rootCauseCountExcludingEdit = useMemo(() => {
    if (!editingCause || currentCauseLayer(editingCause) !== "ROOT") {
      return rootCauseCount;
    }
    return Math.max(0, rootCauseCount - 1);
  }, [editingCause, rootCauseCount]);
  const rootCauseLimitReached = causeLayer === "ROOT" && rootCauseCountExcludingEdit >= MAX_ROOT_CAUSES;

  function showSaveNotice(message: string, targetRef?: RefObject<HTMLDivElement>) {
    setSaveNotice(message);
    window.setTimeout(() => {
      targetRef?.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }

  function resetCauseForm() {
    setEditingCauseId(null);
    setCauseOptionId("");
    setOtherCauseText("");
    setCauseRationale("");
  }

  function startEditingCause(cause: SafetyIncidentCauseTag) {
    setError(null);
    setSaveNotice(null);
    setEditingCauseId(cause.id ?? null);
    setCauseLayer(currentCauseLayer(cause));
    setCauseFactor((cause.cause_factor ?? "HUMAN") as IncidentCauseFactor);
    setCauseOptionId(cause.cause_option_id ?? "");
    setOtherCauseText(cause.cause_other_text ?? "");
    setCauseTool(cause.analysis_tool);
    setCauseRationale(cause.rationale);
    window.setTimeout(() => {
      causeFormRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }

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

  async function saveCause(event: FormEvent) {
    event.preventDefault();
    const selectedOption = causeOptions.find((option) => option.id === causeOptionId) ?? null;
    const isOtherCause = isOtherCauseOption(selectedOption);
    const cleanedOtherCause = otherCauseText.trim();
    const cleanedRationale = causeRationale.trim();
    if (!id) {
      return;
    }
    if (rootCauseLimitReached) {
      setError("Maximum three root causes are allowed.");
      return;
    }
    if (!selectedOption) {
      setError(`Select a cause before adding ${causeLayerLabel(causeLayer)}.`);
      return;
    }
    if (isOtherCause && !cleanedOtherCause) {
      setError(`Please specify the other ${causeLayerLabel(causeLayer)}.`);
      return;
    }
    if (!cleanedRationale) {
      setError(`Write why this is the ${causeLayerLabel(causeLayer)}.`);
      return;
    }
    setError(null);
    setSaveNotice(null);
    setIsMutating(true);
    try {
      const savedCauseLayer = causeLayer;
      const payload: SafetyOfficeWorkflowPayload = {
        analysis_tool: causeTool,
        causal_layer: savedCauseLayer,
        cause_factor: causeFactor,
        cause_option_id: selectedOption.id,
        cause_other_text: isOtherCause ? cleanedOtherCause : "",
        mscat_subcode_id: OTHER_ROOT_CAUSE_SUBCODE,
        rationale: cleanedRationale,
      };
      if (editingCauseId) {
        await safetyApi.updateIncidentPhase5Cause(id, editingCauseId, payload);
      } else {
        await safetyApi.createIncidentPhase5Cause(id, payload);
      }
      const savedMode = editingCauseId ? "updated" : "saved";
      resetCauseForm();
      await reload();
      showSaveNotice(`${causeLayerLabel(savedCauseLayer)} ${savedMode}. Review it under Causal Layers.`, savedCausesRef);
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

  async function continueToNextActions() {
    if (!id) {
      return;
    }
    setPhaseAdvanceError(null);
    if (phase5GateHints.length > 0) {
      setPhaseAdvanceError(phase5GateHints.join(" "));
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.transitionIncident(id, { target_phase: 6 });
      navigate(`/safety/incidents/${id}/phase-3`);
    } catch (caught) {
      setPhaseAdvanceError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  return (
    <section className="space-y-6">
      <section className="grid grid-cols-2 gap-3 text-sm">
        {CAUSAL_LAYERS.map((layer) => (
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm" key={layer}>
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{causeLayerLabel(layer)}</div>
            <div className="mt-1 font-semibold text-slate-900">{causeLayerCounts[layer] ?? 0}</div>
          </div>
        ))}
      </section>

      {error ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section> : null}
      {saveNotice ? (
        <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-900" role="status">
          {saveNotice}
        </section>
      ) : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading Phase 2...</section>
      ) : (
        <>
          <div className="scroll-mt-24 outline-none" ref={savedCausesRef} tabIndex={-1}>
            <SafetyCausalLayerTabs causes={workspace.causes} onEditCause={startEditingCause} />
          </div>

          <form className="scroll-mt-24 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={saveCause} ref={causeFormRef}>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">{editingCauseId ? "Edit Cause" : "Add a Cause"}</h2>
                <p className="mt-2 text-sm text-slate-600">
                  Choose the cause type, select the best matching cause from the list, and write why you selected it.
                </p>
              </div>
              {editingCauseId ? (
                <button
                  className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
                  onClick={resetCauseForm}
                  type="button"
                >
                  Cancel edit
                </button>
              ) : null}
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">
                Type of cause
                <select
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2"
                  onChange={(event) => {
                    setCauseLayer(event.target.value as CurrentCauseLayer);
                    setCauseOptionId("");
                    setOtherCauseText("");
                  }}
                  value={causeLayer}
                >
                  {CAUSAL_LAYERS.map((layer) => (
                    <option key={layer} value={layer}>
                      {causeLayerLabel(layer)}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Cause factor
                <select
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2"
                  onChange={(event) => {
                    setCauseFactor(event.target.value as IncidentCauseFactor);
                    setCauseOptionId("");
                    setOtherCauseText("");
                  }}
                  value={causeFactor}
                >
                  {SAFETY_NEAR_MISS_CAUSE_FACTORS.map((factor) => (
                    <option key={factor.value} value={factor.value}>
                      {factor.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Select cause
                <select
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2"
                  onChange={(event) => {
                    setCauseOptionId(event.target.value);
                    setOtherCauseText("");
                  }}
                  value={causeOptionId}
                >
                  <option value="">
                    {availableCauseOptions.length ? "Select cause" : "No cause options added"}
                  </option>
                  {availableCauseOptions.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.option_text}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {selectedCauseIsOther ? (
              <label className="mt-4 block space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                <span className="font-medium">Type other {causeLayerLabel(causeLayer)}</span>
                <textarea
                  aria-label={`Specify other ${causeLayerLabel(causeLayer)}`}
                  className="min-h-[90px] w-full rounded-xl border border-slate-200 bg-white px-3 py-2 leading-6"
                  onChange={(event) => setOtherCauseText(event.target.value)}
                  placeholder={`Type ${causeLayerLabel(causeLayer)}`}
                  value={otherCauseText}
                />
              </label>
            ) : null}
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Why did you select this?
              <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setCauseRationale(event.target.value)} value={causeRationale} />
            </label>
            {rootCauseLimitReached ? (
              <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                Three root causes are already added. Remove or edit one if you need to change it.
              </p>
            ) : null}
            <button
              className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
              disabled={
                isMutating ||
                rootCauseLimitReached ||
                !causeRationale.trim() ||
                !selectedCauseOption ||
                (selectedCauseIsOther && !otherCauseText.trim())
              }
              type="submit"
            >
              {editingCauseId ? "Update" : "Add"} {causeLayerLabel(causeLayer)}
            </button>
          </form>

          {showTechnicalAnalysisPanels ? (
            <>
          <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={saveAssessment}>
            <h2 className="text-xl font-semibold text-slate-900">Extra Review Notes</h2>
            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              {[
                ["People", peopleText, setPeopleText],
                ["Work process", processText, setProcessText],
                ["Equipment", plantText, setPlantText],
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
              People and condition notes
              <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setHfNotes(event.target.value)} value={hfNotes} />
            </label>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">Human factor type</p>
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
                Human factor notes
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
                          Checked
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
                      placeholder="Notes"
                      value={domain.notes}
                    />
                  </section>
                );
              })}
            </div>
            {rootCauseCount === 1 ? (
              <label className="mt-4 block text-sm font-medium text-slate-700">
                Why is there only one root cause?
                <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setMonocausalJustification(event.target.value)} value={monocausalJustification} />
                <span className="mt-1 block text-xs text-slate-500">{monocausalJustification.trim().length}/80 characters</span>
              </label>
            ) : null}
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Why is there no opposite evidence?
              <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setConfirmationOverrideReason(event.target.value)} value={confirmationOverrideReason} />
            </label>
            <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating} type="submit">
              Save notes
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
            <h2 className="text-xl font-semibold text-slate-900">Add Failed Safety Control</h2>
            <label className="mt-4 block text-sm font-medium text-slate-700">
              Safety control name
              <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setSafeguardDraft((current) => ({ ...current, safeguard_name: event.target.value }))} value={safeguardDraft.safeguard_name} />
            </label>
            <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {SAFEGUARD_FIELDS.map(([field, label]) => (
                <div key={field}>
                  <p className="mb-2 text-sm font-medium text-slate-700">{label}</p>
                  <SafetyMscatPicker
                    label={`${label} cause code`}
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
              Add safety control
            </button>
          </form>

          <SafetyBiasGuardChecklist guards={workspace.bias_guards} />
          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Complete Final Checks</h2>
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
                        Confirm
                      </label>
                    </div>
                    <textarea className="mt-3 min-h-16 w-full rounded-2xl border border-slate-300 p-3 text-sm" onChange={(event) => setBiasDraft((current) => ({ ...current, [guard.guard_code]: { ...draft, justification: event.target.value } }))} placeholder="Notes" value={draft.justification ?? ""} />
                  </article>
                );
              })}
            </div>
            <button className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating} onClick={() => void saveBiasGuards()} type="button">
              Save final checks
            </button>
          </section>
            </>
          ) : null}
        </>
      )}

      {phase5GateHints.length > 0 ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-semibold">Still needed:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {phase5GateHints.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {phaseAdvanceError ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{phaseAdvanceError}</section> : null}

      <div className="flex flex-wrap gap-3">
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/office-communication`}>
          Back to Phase 1 Details
        </Link>
        <button className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || phase5GateHints.length > 0} onClick={continueToNextActions} type="button">
          {isMutating ? "Checking..." : "Continue to Corrective Action"}
        </button>
      </div>
    </section>
  );
}

export default SafetyIncidentPhase5;
