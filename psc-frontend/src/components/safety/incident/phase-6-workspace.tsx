import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type RefObject,
} from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useAuth } from '../../../hooks/use-auth';
import { getErrorMessage } from '../../../lib/api/client';
import { safetyApi } from '../../../lib/api/safety';
import {
  safetyIncidentPhase6WorkspaceSchema,
  type SafetyIncidentPhase6Workspace,
  type SafetyRecommendation,
} from '../../../schemas/safety/incident-phase6';
import SafetyRecommendationEditor from './recommendation-editor';

const TIERS = ['CORRECTIVE', 'PREVENTIVE'] as const;
const MAX_RECOMMENDATION_TITLE_LENGTH = 256;

type Tier = (typeof TIERS)[number];

interface RecommendationDraft {
  alarp_attested: boolean;
  description: string;
  due_date: string;
  estimated_effort: string;
  residual_risk_statement: string;
  theme_code: string;
  tier: Tier;
  tolerable_failure_filter: boolean;
}

interface SafetyIncidentPhase6Props {
  fixedTier?: Tier;
  formTitle?: string;
  nextLabel?: string;
  nextPath?: string;
  previousLabel?: string;
  previousPath?: string;
  savedHeading?: string;
  transitionTargetPhase?: number | null;
}

function emptyDraftForTier(tier: Tier): RecommendationDraft {
  return {
    alarp_attested: false,
    description: '',
    due_date: '',
    estimated_effort: '',
    residual_risk_statement: '',
    theme_code: '',
    tier,
    tolerable_failure_filter: false,
  };
}

function emptyWorkspace(): SafetyIncidentPhase6Workspace {
  return {
    alarp_complete: false,
    corrective_actions: [],
    incident_id: '',
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
  return tier.charAt(0) + tier.slice(1).toLowerCase();
}

function deriveTitleFromDescription(description: string) {
  const normalized = description.trim().replace(/\s+/g, ' ');
  return normalized.slice(0, MAX_RECOMMENDATION_TITLE_LENGTH);
}

function firstLinkedDueDate(recommendation: SafetyRecommendation | null) {
  return recommendation?.corrective_actions?.find((action) => action.due_date)
    ?.due_date ?? '';
}

function defaultFormTitle(tier?: Tier) {
  if (tier === 'CORRECTIVE') {
    return 'Add Corrective Action';
  }
  if (tier === 'PREVENTIVE') {
    return 'Add Preventive Action';
  }
  return 'Add Action';
}

function defaultSavedHeading(tier?: Tier) {
  if (tier === 'CORRECTIVE') {
    return 'Saved Corrective Action';
  }
  if (tier === 'PREVENTIVE') {
    return 'Saved Preventive Action';
  }
  return 'Summary';
}

export function SafetyIncidentPhase6({
  fixedTier,
  formTitle = defaultFormTitle(fixedTier),
  nextLabel = 'Continue to Office Review',
  nextPath,
  previousLabel = 'Back to Phase 2',
  previousPath,
  savedHeading = defaultSavedHeading(fixedTier),
  transitionTargetPhase,
}: SafetyIncidentPhase6Props = {}) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const resolvedTransitionTargetPhase =
    transitionTargetPhase === undefined
      ? nextPath
        ? null
        : 7
      : transitionTargetPhase;
  const [workspace, setWorkspace] =
    useState<SafetyIncidentPhase6Workspace>(emptyWorkspace());
  const [draft, setDraft] = useState<RecommendationDraft>(() =>
    emptyDraftForTier(fixedTier ?? 'CORRECTIVE')
  );
  const [error, setError] = useState<string | null>(null);
  const [saveNotice, setSaveNotice] = useState<string | null>(null);
  const [phaseAdvanceError, setPhaseAdvanceError] = useState<string | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [editingRecommendationId, setEditingRecommendationId] = useState<
    string | null
  >(null);
  const recommendationFormRef = useRef<HTMLFormElement>(null);
  const savedRecommendationsRef = useRef<HTMLDivElement>(null);

  const reload = useCallback(async () => {
    if (!id) {
      setError('Invalid incident id.');
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

  useEffect(() => {
    if (fixedTier) {
      setDraft((current) => ({ ...current, tier: fixedTier }));
    }
  }, [fixedTier]);

  const visibleTiers = useMemo(
    () => (fixedTier ? [fixedTier] : TIERS),
    [fixedTier]
  );
  const isEditingRecommendation = Boolean(editingRecommendationId);
  const editingRecommendation = useMemo(
    () =>
      TIERS.flatMap((tier) => workspace.recommendations[tier] ?? []).find(
        (recommendation) => recommendation.id === editingRecommendationId
      ) ?? null,
    [editingRecommendationId, workspace.recommendations]
  );
  const actorId = String(user?.username || user?.id || 'system');
  const gateHints = useMemo(() => {
    const hints: string[] = [];
    if (workspace.gate_blockers.includes('recommendations')) {
      hints.push('Add at least one action before office review.');
    }
    return hints;
  }, [workspace.gate_blockers]);

  function showSaveNotice(
    message: string,
    targetRef?: RefObject<HTMLDivElement>
  ) {
    setSaveNotice(message);
    window.setTimeout(() => {
      targetRef?.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 100);
  }

  function resetRecommendationForm() {
    setEditingRecommendationId(null);
    setDraft(emptyDraftForTier(fixedTier ?? 'CORRECTIVE'));
  }

  function startEditingRecommendation(recommendation: SafetyRecommendation) {
    if (!recommendation.id) {
      return;
    }
    setError(null);
    setSaveNotice(null);
    setEditingRecommendationId(recommendation.id);
    setDraft({
      alarp_attested: recommendation.alarp_attested,
      description: recommendation.description,
      due_date: firstLinkedDueDate(recommendation),
      estimated_effort: recommendation.estimated_effort ?? '',
      residual_risk_statement: recommendation.residual_risk_statement ?? '',
      theme_code: recommendation.theme_code ?? '',
      tier: recommendation.tier,
      tolerable_failure_filter: recommendation.tolerable_failure_filter,
    });
    window.setTimeout(() => {
      recommendationFormRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 100);
  }

  async function saveRecommendation(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    const description = draft.description.trim();
    const title = deriveTitleFromDescription(description);
    const payload: Record<string, unknown> = {
      description,
      tier: draft.tier,
      title,
    };
    const shouldPersistDueDate =
      Boolean(draft.due_date) ||
      Boolean(editingRecommendation?.corrective_actions?.length);
    if (shouldPersistDueDate) {
      payload.corrective_action = {
        due_date: draft.due_date || null,
        verifier_user_id: actorId,
      };
    }
    if (draft.tier === 'PREVENTIVE') {
      payload.theme_code = null;
      payload.estimated_effort = null;
      payload.estimated_likelihood_reduction = null;
      payload.residual_risk_statement = description;
      payload.alarp_attested = true;
    }
    if (workspace.tolerable_failure_allowed) {
      payload.tolerable_failure_filter = draft.tolerable_failure_filter;
    }

    const savedTier = draft.tier;
    setIsMutating(true);
    setError(null);
    setSaveNotice(null);
    try {
      if (editingRecommendationId) {
        await safetyApi.updateIncidentRecommendation(
          id,
          editingRecommendationId,
          payload
        );
      } else {
        await safetyApi.createIncidentRecommendation(id, payload);
      }
      const savedMode = editingRecommendationId ? 'updated' : 'saved';
      resetRecommendationForm();
      await reload();
      showSaveNotice(
        `${tierLabel(savedTier)} ${savedMode}. Review it under saved actions.`,
        savedRecommendationsRef
      );
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function continueToNextStep() {
    if (!id) {
      return;
    }
    if (nextPath && resolvedTransitionTargetPhase == null) {
      navigate(nextPath);
      return;
    }
    setPhaseAdvanceError(null);
    setIsMutating(true);
    try {
      if (resolvedTransitionTargetPhase == null) {
        navigate(nextPath ?? `/safety/incidents/${id}/phase-5`);
        return;
      }
      await safetyApi.transitionIncident(id, {
        target_phase: resolvedTransitionTargetPhase,
      });
      navigate(nextPath ?? `/safety/incidents/${id}/phase-5`);
    } catch (caught) {
      setPhaseAdvanceError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  const saveDisabled =
    isMutating ||
    !draft.description.trim();

  return (
    <section className="space-y-6">
      {!fixedTier ? (
        <section className="grid grid-cols-3 gap-3 text-sm">
          {TIERS.map((tier) => (
            <div
              key={tier}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
            >
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                {tierLabel(tier)}
              </div>
              <div className="mt-1 font-semibold text-slate-900">
                {workspace.tier_counts[tier] ?? 0}
              </div>
            </div>
          ))}
        </section>
      ) : null}

      {error ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          {error}
        </section>
      ) : null}
      {saveNotice ? (
        <section
          className="rounded-3xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-900"
          role="status"
        >
          {saveNotice}
        </section>
      ) : null}

      {isLoading ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
          Loading...
        </section>
      ) : (
        <>
          <div
            className="scroll-mt-24 outline-none"
            ref={savedRecommendationsRef}
            tabIndex={-1}
          >
            <SafetyRecommendationEditor
              heading={savedHeading}
              onEditRecommendation={startEditingRecommendation}
              tiers={visibleTiers}
              workspace={workspace}
            />
          </div>

          <form
            className="scroll-mt-24 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
            onSubmit={saveRecommendation}
            ref={recommendationFormRef}
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <h2 className="text-xl font-semibold text-slate-900">
                {isEditingRecommendation
                  ? `Edit ${tierLabel(draft.tier)}`
                  : formTitle}
              </h2>
              {isEditingRecommendation ? (
                <button
                  className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
                  onClick={resetRecommendationForm}
                  type="button"
                >
                  Cancel edit
                </button>
              ) : null}
            </div>
            {!fixedTier ? (
              <div className="mt-4 grid gap-4 lg:grid-cols-3">
                <label className="block text-sm font-medium text-slate-700">
                  Type
                  <select
                    className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                    onChange={(event) => {
                      const nextTier = event.target.value as Tier;
                      setDraft((current) => ({
                        ...current,
                        tier: nextTier,
                      }));
                    }}
                    value={draft.tier}
                  >
                    {TIERS.map((tier) => (
                      <option key={tier} value={tier}>
                        {tierLabel(tier)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            ) : null}
            <div className="mt-4 grid gap-4">
              <label className="block text-sm font-medium text-slate-700">
                Description
                <textarea
                  className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3"
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      description: event.target.value,
                    }))
                  }
                  value={draft.description}
                />
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Due date
                <input
                  className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      due_date: event.target.value,
                    }))
                  }
                  type="date"
                  value={draft.due_date}
                />
              </label>
            </div>

            {workspace.tolerable_failure_allowed ? (
              <label className="mt-4 inline-flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-900">
                <input
                  checked={draft.tolerable_failure_filter}
                  onChange={(event) =>
                    setDraft((current) => ({
                      ...current,
                      tolerable_failure_filter: event.target.checked,
                    }))
                  }
                  type="checkbox"
                />
                Mark as acceptable exception
              </label>
            ) : null}

            <button
              className="mt-4 min-h-11 rounded-full bg-slate-900 px-5 text-sm font-semibold text-white disabled:bg-slate-400"
              disabled={saveDisabled}
              type="submit"
            >
              {isMutating
                ? 'Saving...'
                : `${isEditingRecommendation ? 'Update' : 'Save'} ${fixedTier ? tierLabel(draft.tier).toLowerCase() : 'action'}`}
            </button>
          </form>

        </>
      )}

      {gateHints.length > 0 ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-semibold">Still needed:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {gateHints.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        </section>
      ) : null}
      {phaseAdvanceError ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          {phaseAdvanceError}
        </section>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <Link
          className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
          to={previousPath ?? `/safety/incidents/${id}/phase-2`}
        >
          {previousLabel}
        </Link>
        <button
          className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-400"
          disabled={
            isMutating ||
            (resolvedTransitionTargetPhase != null &&
              workspace.gate_blockers.length > 0)
          }
          onClick={continueToNextStep}
          type="button"
        >
          {isMutating ? 'Checking...' : nextLabel}
        </button>
      </div>
    </section>
  );
}

export default SafetyIncidentPhase6;
