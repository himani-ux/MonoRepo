import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import {
  safetyIncidentPhase6WorkspaceSchema,
  type SafetyIncidentPhase6Workspace,
  type SafetyRecommendation,
} from "../../../schemas/safety/incident-phase6";
import SafetyAlarpGateModal from "./alarp-gate-modal";
import SafetyRecommendationEditor from "./recommendation-editor";

const TIERS = ["CORRECTIVE", "PREVENTIVE", "LESSONS_LEARNT"] as const;
const LIKELIHOOD = ["LOW", "MED", "HIGH", "QUANTIFIED"] as const;
const MAX_RECOMMENDATION_TITLE_LENGTH = 256;
const MAX_CORRECTIVE_ACTION_USER_ID_LENGTH = 64;
const MIN_BLAME_OVERRIDE_JUSTIFICATION_LENGTH = 200;

type Tier = (typeof TIERS)[number];

interface RecommendationDraft {
  alarp_attested: boolean;
  assigned_crew_id: string;
  assigned_office_user_id: string;
  description: string;
  due_date: string;
  estimated_effort: string;
  estimated_likelihood_reduction: "" | (typeof LIKELIHOOD)[number];
  rationale: string;
  residual_risk_statement: string;
  theme_code: string;
  tier: Tier;
  title: string;
  tolerable_failure_filter: boolean;
  verifier_user_id: string;
}

const emptyDraft: RecommendationDraft = {
  alarp_attested: false,
  assigned_crew_id: "",
  assigned_office_user_id: "",
  description: "",
  due_date: "",
  estimated_effort: "",
  estimated_likelihood_reduction: "",
  rationale: "",
  residual_risk_statement: "",
  theme_code: "",
  tier: "CORRECTIVE",
  title: "",
  tolerable_failure_filter: false,
  verifier_user_id: "",
};

function emptyWorkspace(): SafetyIncidentPhase6Workspace {
  return {
    alarp_complete: false,
    corrective_actions: [],
    incident_id: 0,
    missing_tiers: [],
    bias_guards_complete: false,
    blame_evaluation: {
      all_root_personal_factors: false,
      blocked: false,
      has_lack_of_control: false,
      override_by: null,
      trigger_terms: [],
    },
    gate_blockers: [],
    recommendations: {
      CORRECTIVE: [],
      LESSONS_LEARNT: [],
      PREVENTIVE: [],
    },
    schema_version: 1,
    themes: [],
    threshold_hint: null,
    tier_counts: {},
    tolerable_failure_allowed: false,
  };
}

function tierLabel(tier: Tier) {
  if (tier === "LESSONS_LEARNT") {
    return "Lessons Learnt";
  }
  return tier.charAt(0) + tier.slice(1).toLowerCase();
}

function recommendationNeedsAlarp(row: SafetyRecommendation) {
  return row.tier === "PREVENTIVE";
}

export function SafetyIncidentPhase6() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<SafetyIncidentPhase6Workspace>(emptyWorkspace());
  const [draft, setDraft] = useState<RecommendationDraft>(emptyDraft);
  const [error, setError] = useState<string | null>(null);
  const [phaseAdvanceError, setPhaseAdvanceError] = useState<string | null>(null);
  const [blameOverrideJustification, setBlameOverrideJustification] = useState("");
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
      const response = await safetyApi.getIncidentPhase6Workspace(id);
      setWorkspace(safetyIncidentPhase6WorkspaceSchema.parse(response));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const flatRecommendations = useMemo(
    () => TIERS.flatMap((tier) => workspace.recommendations[tier]),
    [workspace.recommendations],
  );

  const availableTiers = useMemo(
    () => TIERS.filter((tier) => (workspace.recommendations[tier]?.length ?? 0) === 0),
    [workspace.recommendations],
  );
  const selectedTierAlreadyExists = (workspace.recommendations[draft.tier]?.length ?? 0) > 0;

  useEffect(() => {
    if (!isLoading && selectedTierAlreadyExists && availableTiers.length > 0) {
      setDraft((current) => ({ ...current, tier: availableTiers[0] }));
    }
  }, [availableTiers, isLoading, selectedTierAlreadyExists]);

  const alarpBlockingRows = flatRecommendations.filter(
    (row) =>
      recommendationNeedsAlarp(row) &&
      (!row.estimated_effort ||
        !row.estimated_likelihood_reduction ||
        !row.residual_risk_statement ||
        !row.alarp_attested),
  ).length;

  const gateHints = useMemo(() => {
    const hints: string[] = [];
    if (workspace.missing_tiers.length > 0) {
      hints.push(`Add missing tier(s): ${workspace.missing_tiers.map(tierLabel).join(", ")}.`);
    }
    if (alarpBlockingRows > 0) {
      hints.push("Complete ALARP effort, likelihood reduction, residual risk, and attestation for preventive system actions.");
    }
    if (workspace.gate_blockers.includes("bias_guards")) {
      hints.push("Complete all Phase 5 bias guards before Phase 7.");
    }
    if (workspace.gate_blockers.includes("blame_override")) {
      hints.push("DPA blame-fixation override is required before Phase 7.");
    }
    return hints;
  }, [alarpBlockingRows, workspace.gate_blockers, workspace.missing_tiers]);

  async function submitBlameOverride() {
    if (!id) {
      return;
    }
    setIsMutating(true);
    setError(null);
    try {
      await safetyApi.overrideIncidentBlameGuard(id, {
        justification: blameOverrideJustification.trim(),
      });
      setBlameOverrideJustification("");
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function createRecommendation(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    if (selectedTierAlreadyExists) {
      setError(`${tierLabel(draft.tier)} recommendation already exists for this incident.`);
      return;
    }
    const title = draft.title.trim();
    const description = draft.description.trim();
    const rationale = draft.rationale.trim();
    const payload: Record<string, unknown> = {
      description,
      rationale,
      tier: draft.tier,
      title,
    };
    if (draft.tier === "PREVENTIVE") {
      payload.theme_code = draft.theme_code || null;
      payload.estimated_effort = draft.estimated_effort || null;
      payload.estimated_likelihood_reduction = draft.estimated_likelihood_reduction || null;
      payload.residual_risk_statement = draft.residual_risk_statement || null;
      payload.alarp_attested = draft.alarp_attested;
    }
    if (draft.tier === "CORRECTIVE") {
      payload.corrective_action = {
        assigned_crew_id: draft.assigned_crew_id.trim() || undefined,
        assigned_office_user_id: draft.assigned_office_user_id.trim() || undefined,
        due_date: draft.due_date,
        verifier_user_id: draft.verifier_user_id.trim(),
      };
    }
    if (workspace.tolerable_failure_allowed) {
      payload.tolerable_failure_filter = draft.tolerable_failure_filter;
    }

    setIsMutating(true);
    setError(null);
    try {
      await safetyApi.createIncidentRecommendation(id, payload);
      setDraft(emptyDraft);
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function continueToPhase7() {
    if (!id) {
      return;
    }
    setPhaseAdvanceError(null);
    setIsMutating(true);
    try {
      await safetyApi.transitionIncident(id, { target_phase: 7 });
      navigate(`/safety/incidents/${id}/phase-7`);
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
          Safety / Incident / Phase 6
        </p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Recommendations and ALARP</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Create corrective, preventive, and lessons-learnt actions, link corrective action ownership, and complete ALARP where required.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            {TIERS.map((tier) => (
              <div key={tier} className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{tierLabel(tier)}</div>
                <div className="mt-1 font-semibold text-slate-900">{workspace.tier_counts[tier] ?? 0}</div>
              </div>
            ))}
          </div>
        </div>
      </header>

      {error ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{error}</section> : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">Loading Phase 6...</section>
      ) : (
        <>
          {alarpBlockingRows > 0 ? (
            <SafetyAlarpGateModal blockingRows={alarpBlockingRows} thresholdHint={workspace.threshold_hint} />
          ) : null}

          <SafetyRecommendationEditor workspace={workspace} />

          {workspace.blame_evaluation.blocked ? (
            <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-950 shadow-sm">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">Blame-fixation gate</p>
                  <h2 className="mt-2 text-lg font-semibold text-slate-950">
                    {workspace.blame_evaluation.override_by ? "Override recorded" : "DPA override required"}
                  </h2>
                  <p className="mt-2 leading-6">
                    {workspace.blame_evaluation.all_root_personal_factors && !workspace.blame_evaluation.has_lack_of_control
                      ? "Root causes are currently concentrated in personal-factor categories without a lack-of-control/system cause."
                      : "The investigation text contains blame-focused language."}
                  </p>
                  {workspace.blame_evaluation.trigger_terms.length > 0 ? (
                    <p className="mt-2 text-amber-800">Terms: {workspace.blame_evaluation.trigger_terms.join(", ")}</p>
                  ) : null}
                  {workspace.blame_evaluation.override_by ? (
                    <p className="mt-2 font-semibold">Approved by {workspace.blame_evaluation.override_by}</p>
                  ) : null}
                </div>
              </div>
              {!workspace.blame_evaluation.override_by ? (
                <div className="mt-4">
                  <label className="block text-sm font-medium text-slate-800">
                    DPA override justification
                    <textarea
                      className="mt-2 min-h-28 w-full rounded-2xl border border-amber-300 bg-white p-3 text-slate-900"
                      onChange={(event) => setBlameOverrideJustification(event.target.value)}
                      value={blameOverrideJustification}
                    />
                  </label>
                  <button
                    className="mt-3 min-h-11 rounded-full bg-amber-900 px-5 text-sm font-semibold text-white disabled:bg-amber-300"
                    disabled={isMutating || blameOverrideJustification.trim().length < MIN_BLAME_OVERRIDE_JUSTIFICATION_LENGTH}
                    onClick={submitBlameOverride}
                    type="button"
                  >
                    {isMutating ? "Saving override..." : "Record DPA override"}
                  </button>
                </div>
              ) : null}
            </section>
          ) : null}

          <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={createRecommendation}>
            <h2 className="text-xl font-semibold text-slate-900">Add Recommendation</h2>
            <div className="mt-4 grid gap-4 lg:grid-cols-3">
              <label className="block text-sm font-medium text-slate-700">
                Tier
                <select
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                  onChange={(event) => setDraft((current) => ({ ...current, tier: event.target.value as Tier }))}
                  value={draft.tier}
                >
                  {TIERS.map((tier) => (
                    <option disabled={(workspace.recommendations[tier]?.length ?? 0) > 0} key={tier} value={tier}>
                      {tierLabel(tier)}{(workspace.recommendations[tier]?.length ?? 0) > 0 ? " (already added)" : ""}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm font-medium text-slate-700 lg:col-span-2">
                Title
                <input
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                  maxLength={MAX_RECOMMENDATION_TITLE_LENGTH}
                  onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
                  value={draft.title}
                />
              </label>
            </div>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <label className="block text-sm font-medium text-slate-700">
                Description
                <textarea
                  className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3"
                  onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
                  value={draft.description}
                />
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Rationale
                <textarea
                  className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3"
                  onChange={(event) => setDraft((current) => ({ ...current, rationale: event.target.value }))}
                  value={draft.rationale}
                />
              </label>
            </div>

            {draft.tier === "CORRECTIVE" ? (
              <section className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <h3 className="text-sm font-semibold text-slate-900">Corrective Action Owner / Verifier</h3>
                <div className="mt-3 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <label className="block text-sm font-medium text-slate-700">
                    Crew assignee ID
                    <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" maxLength={MAX_CORRECTIVE_ACTION_USER_ID_LENGTH} onChange={(event) => setDraft((current) => ({ ...current, assigned_crew_id: event.target.value }))} value={draft.assigned_crew_id} />
                  </label>
                  <label className="block text-sm font-medium text-slate-700">
                    Office assignee ID
                    <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" maxLength={MAX_CORRECTIVE_ACTION_USER_ID_LENGTH} onChange={(event) => setDraft((current) => ({ ...current, assigned_office_user_id: event.target.value }))} value={draft.assigned_office_user_id} />
                  </label>
                  <label className="block text-sm font-medium text-slate-700">
                    Verifier user ID
                    <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" maxLength={MAX_CORRECTIVE_ACTION_USER_ID_LENGTH} onChange={(event) => setDraft((current) => ({ ...current, verifier_user_id: event.target.value }))} value={draft.verifier_user_id} />
                  </label>
                  <label className="block text-sm font-medium text-slate-700">
                    Due date
                    <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setDraft((current) => ({ ...current, due_date: event.target.value }))} type="date" value={draft.due_date} />
                  </label>
                </div>
              </section>
            ) : null}

            {draft.tier === "PREVENTIVE" ? (
              <section className="mt-4 rounded-2xl border border-sky-200 bg-sky-50 p-4">
                <h3 className="text-sm font-semibold text-slate-900">System Action / ALARP</h3>
                <div className="mt-3 grid gap-4 lg:grid-cols-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Theme
                    <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setDraft((current) => ({ ...current, theme_code: event.target.value }))} value={draft.theme_code}>
                      <option value="">Select theme</option>
                      {workspace.themes.map((theme) => (
                        <option key={theme.code} value={theme.code}>{theme.label}</option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-sm font-medium text-slate-700">
                    Likelihood reduction
                    <select className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3" onChange={(event) => setDraft((current) => ({ ...current, estimated_likelihood_reduction: event.target.value as RecommendationDraft["estimated_likelihood_reduction"] }))} value={draft.estimated_likelihood_reduction}>
                      <option value="">Select reduction</option>
                      {LIKELIHOOD.map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-sm font-medium text-slate-700">
                    Estimated effort
                    <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setDraft((current) => ({ ...current, estimated_effort: event.target.value }))} value={draft.estimated_effort} />
                  </label>
                  <label className="block text-sm font-medium text-slate-700">
                    Residual-risk statement
                    <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setDraft((current) => ({ ...current, residual_risk_statement: event.target.value }))} value={draft.residual_risk_statement} />
                  </label>
                </div>
                <label className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-slate-700">
                  <input checked={draft.alarp_attested} onChange={(event) => setDraft((current) => ({ ...current, alarp_attested: event.target.checked }))} type="checkbox" />
                  ALARP attested
                </label>
              </section>
            ) : null}

            {workspace.tolerable_failure_allowed ? (
              <label className="mt-4 inline-flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-900">
                <input checked={draft.tolerable_failure_filter} onChange={(event) => setDraft((current) => ({ ...current, tolerable_failure_filter: event.target.checked }))} type="checkbox" />
                Mark as tolerable failure
              </label>
            ) : null}

            <button
              className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
              disabled={isMutating || availableTiers.length === 0 || selectedTierAlreadyExists || !draft.title.trim() || !draft.description.trim() || (draft.tier === "CORRECTIVE" && (!draft.verifier_user_id.trim() || !draft.due_date))}
              type="submit"
            >
              {isMutating ? "Saving..." : "Create recommendation"}
            </button>
          </form>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">Corrective Actions</h2>
            <div className="mt-4 grid gap-3">
              {workspace.corrective_actions.length > 0 ? (
                workspace.corrective_actions.map((action) => (
                  <article key={action.id ?? action.title} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h3 className="font-semibold text-slate-900">{action.title}</h3>
                      <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-white">{action.status}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-600">{action.description}</p>
                    <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-4">
                      <p>Owner: {action.assigned_crew_id || action.assigned_office_user_id || "Unassigned"}</p>
                      <p>Verifier: {action.verifier_user_id || "Pending"}</p>
                      <p>Due: {action.due_date || "Pending"}</p>
                      <p>Purchase: {action.purchase_req_id ? `PR ${action.purchase_req_id}` : "Not linked"}</p>
                    </div>
                  </article>
                ))
              ) : (
                <p className="text-sm text-slate-500">No corrective actions created yet.</p>
              )}
            </div>
          </section>
        </>
      )}

      {gateHints.length > 0 ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-semibold">Phase 7 gate still needs:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {gateHints.map((hint) => <li key={hint}>{hint}</li>)}
          </ul>
        </section>
      ) : null}
      {phaseAdvanceError ? <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">{phaseAdvanceError}</section> : null}

      <div className="flex flex-wrap gap-3">
        <Link className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700" to={`/safety/incidents/${id}/phase-5`}>
          Back to Phase 5
        </Link>
        <button className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400" disabled={isMutating || workspace.gate_blockers.length > 0} onClick={continueToPhase7} type="button">
          {isMutating ? "Checking gate..." : "Continue to Phase 7"}
        </button>
      </div>
    </section>
  );
}

export default SafetyIncidentPhase6;
