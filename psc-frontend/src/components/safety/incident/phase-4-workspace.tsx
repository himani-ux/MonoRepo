import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../../../lib/api/client";
import {
  safetyApi,
  type SafetyIncidentPhase4Gate,
  type SafetyIncidentPhase4EvidenceSource,
} from "../../../lib/api/safety";
import {
  safetyIncidentFactSchema,
  type SafetyIncidentFact,
} from "../../../schemas/safety/incident-phase4";

type FactDraft = {
  confidence: SafetyIncidentFact["confidence"];
  fact_text: string;
  fact_timestamp: string;
  hindsight_override_reason: string;
  source_evidence_id: string;
};

const emptyDraft: FactDraft = {
  confidence: "MEDIUM",
  fact_text: "",
  fact_timestamp: "",
  hindsight_override_reason: "",
  source_evidence_id: "",
};

const confidenceOptions: SafetyIncidentFact["confidence"][] = ["LOW", "MEDIUM", "HIGH"];

function factRowsFromPayload(payload: unknown): unknown[] {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (
    payload &&
    typeof payload === "object" &&
    Array.isArray((payload as { results?: unknown }).results)
  ) {
    return (payload as { results: unknown[] }).results;
  }
  return [];
}

function parseFacts(payload: unknown): SafetyIncidentFact[] {
  return safetyIncidentFactSchema.array().parse(factRowsFromPayload(payload));
}

function toDateTimeLocalValue(value?: string | null) {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value.slice(0, 16);
  }
  const offsetMs = parsed.getTimezoneOffset() * 60_000;
  return new Date(parsed.getTime() - offsetMs).toISOString().slice(0, 16);
}

function buildDraft(fact: SafetyIncidentFact): FactDraft {
  return {
    confidence: fact.confidence,
    fact_text: fact.fact_text,
    fact_timestamp: toDateTimeLocalValue(fact.fact_timestamp),
    hindsight_override_reason: fact.hindsight_override_reason ?? "",
    source_evidence_id: String(fact.source_evidence_id),
  };
}

function buildPayload(draft: FactDraft) {
  const sourceEvidenceId = draft.source_evidence_id.trim();
  if (!sourceEvidenceId) {
    throw new Error("Select a source evidence record before adding a fact.");
  }

  const payload: Record<string, unknown> = {
    confidence: draft.confidence,
    fact_text: draft.fact_text.trim(),
    source_evidence_id: sourceEvidenceId,
  };

  if (draft.fact_timestamp) {
    payload.fact_timestamp = draft.fact_timestamp;
  }
  if (draft.hindsight_override_reason.trim()) {
    payload.hindsight_override_reason = draft.hindsight_override_reason.trim();
  }
  return payload;
}

function emptyDraftForSources(sources: SafetyIncidentPhase4EvidenceSource[]): FactDraft {
  const firstSource = sources.find((source) => String(source.id).trim().length > 0);
  return {
    ...emptyDraft,
    source_evidence_id: firstSource ? String(firstSource.id) : "",
  };
}

function confidenceTone(confidence: SafetyIncidentFact["confidence"]) {
  if (confidence === "HIGH") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (confidence === "LOW") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function FactForm({
  draft,
  disabled,
  evidenceSources,
  onChange,
  onSubmit,
  submitLabel,
}: {
  draft: FactDraft;
  disabled: boolean;
  evidenceSources: SafetyIncidentPhase4EvidenceSource[];
  onChange: (draft: FactDraft) => void;
  onSubmit: (event: FormEvent) => void;
  submitLabel: string;
}) {
  return (
    <form className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={onSubmit}>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700 md:col-span-2">
          Fact
          <textarea
            className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 p-3 text-sm text-slate-900 outline-none focus:border-slate-500"
            disabled={disabled}
            onChange={(event) => onChange({ ...draft, fact_text: event.target.value })}
            required
            value={draft.fact_text}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Source evidence
          <select
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
            disabled={disabled || evidenceSources.length === 0}
            onChange={(event) => onChange({ ...draft, source_evidence_id: event.target.value })}
            required
            value={draft.source_evidence_id}
          >
            <option value="">Select evidence source</option>
            {evidenceSources.map((source) => (
              <option key={`${source.source_type}-${source.id}`} value={source.id}>
                {source.source_type}: {source.label}
              </option>
            ))}
          </select>
          {evidenceSources.length === 0 ? (
            <span className="mt-2 block text-xs leading-5 text-amber-700">
              Add Phase 3 evidence, matrix rows, interviews, or chain-of-custody items before
              creating facts.
            </span>
          ) : null}
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Confidence
          <select
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
            disabled={disabled}
            onChange={(event) =>
              onChange({
                ...draft,
                confidence: event.target.value as SafetyIncidentFact["confidence"],
              })
            }
            value={draft.confidence}
          >
            {confidenceOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Fact timestamp
          <input
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
            disabled={disabled}
            onChange={(event) => onChange({ ...draft, fact_timestamp: event.target.value })}
            type="datetime-local"
            value={draft.fact_timestamp}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Hindsight override reason
          <input
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
            disabled={disabled}
            onChange={(event) =>
              onChange({ ...draft, hindsight_override_reason: event.target.value })
            }
            value={draft.hindsight_override_reason}
          />
        </label>
      </div>
      <button
        className="mt-4 inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        disabled={disabled}
        type="submit"
      >
        {submitLabel}
      </button>
    </form>
  );
}

export function SafetyIncidentPhase4() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [facts, setFacts] = useState<SafetyIncidentFact[]>([]);
  const [evidenceSources, setEvidenceSources] = useState<SafetyIncidentPhase4EvidenceSource[]>([]);
  const [gate, setGate] = useState<SafetyIncidentPhase4Gate | null>(null);
  const [draft, setDraft] = useState<FactDraft>(emptyDraft);
  const [editingFactId, setEditingFactId] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<FactDraft>(emptyDraft);
  const [contradictionTargets, setContradictionTargets] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [phaseAdvanceError, setPhaseAdvanceError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);

  const sortedFacts = useMemo(
    () => [...facts].sort((first, second) => first.sequence_index - second.sequence_index),
    [facts],
  );

  const reload = useCallback(async () => {
    if (!id) {
      setError("Invalid incident id.");
      setIsLoading(false);
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const [factPayload, sourcePayload] = await Promise.all([
        safetyApi.getIncidentPhase4Facts(id),
        safetyApi.getIncidentPhase4EvidenceSources(id),
      ]);
      const gatePayload = await safetyApi.getIncidentPhase4Gate(id);
      const parsedSources = sourcePayload.filter((source) => String(source.id).trim().length > 0);
      setFacts(parseFacts(factPayload));
      setEvidenceSources(parsedSources);
      setGate(gatePayload);
      setDraft((current) =>
        current.source_evidence_id &&
        parsedSources.some((source) => String(source.id) === current.source_evidence_id)
          ? current
          : emptyDraftForSources(parsedSources),
      );
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function createFact(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setError(null);
    setIsMutating(true);
    try {
      await safetyApi.createIncidentPhase4Fact(id, buildPayload(draft));
      setDraft(emptyDraftForSources(evidenceSources));
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function saveFact(event: FormEvent) {
    event.preventDefault();
    if (!id || editingFactId === null) {
      return;
    }
    setError(null);
    setIsMutating(true);
    try {
      await safetyApi.updateIncidentPhase4Fact(id, editingFactId, buildPayload(editDraft));
      setEditingFactId(null);
      setEditDraft(emptyDraft);
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function moveFact(factId: number, direction: -1 | 1) {
    if (!id) {
      return;
    }
    const currentIndex = sortedFacts.findIndex((fact) => fact.id === factId);
    const targetIndex = currentIndex + direction;
    if (currentIndex < 0 || targetIndex < 0 || targetIndex >= sortedFacts.length) {
      return;
    }
    const orderedIds = sortedFacts.map((fact) => fact.id).filter((value): value is number => Boolean(value));
    const [moved] = orderedIds.splice(currentIndex, 1);
    orderedIds.splice(targetIndex, 0, moved);
    setError(null);
    setIsMutating(true);
    try {
      setFacts(parseFacts(await safetyApi.reorderIncidentPhase4Facts(id, orderedIds)));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function markContradiction(factId: number) {
    if (!id) {
      return;
    }
    const targetId = Number(contradictionTargets[factId]);
    if (!targetId) {
      return;
    }
    setError(null);
    setIsMutating(true);
    try {
      await safetyApi.setIncidentPhase4FactContradiction(id, {
        contradicts_fact_id: targetId,
        fact_id: factId,
      });
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  async function continueToPhase5() {
    if (!id) {
      return;
    }
    setPhaseAdvanceError(null);
    if (gate && !gate.can_continue) {
      setPhaseAdvanceError(gate.blockers.join(" "));
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.transitionIncident(id, { target_phase: 5 });
      navigate(`/safety/incidents/${id}/phase-5`);
    } catch (caught) {
      setPhaseAdvanceError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Safety / Incident / Phase 4
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">
              Phase 4 Facts and Sequence
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Build the fact sequence from evidence, resolve contradictions, and keep hindsight
              controls visible before causal analysis.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                Incident
              </div>
              <div className="mt-1 font-semibold text-slate-900">#{id}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                Facts
              </div>
              <div className="mt-1 font-semibold text-slate-900">{facts.length}</div>
            </div>
          </div>
        </div>
      </header>

      {error ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          {error}
        </section>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(360px,420px)]">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-slate-900">Fact Sequence</h2>
            <button
              className="inline-flex min-h-10 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:text-slate-400"
              disabled={isMutating}
              onClick={() => void reload()}
              type="button"
            >
              Refresh
            </button>
          </div>

          {isLoading ? (
            <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
              Loading phase 4 facts...
            </section>
          ) : sortedFacts.length === 0 ? (
            <section className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600">
              No facts recorded yet.
            </section>
          ) : (
            <div className="space-y-3">
              {sortedFacts.map((fact, index) => (
                <article
                  className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
                  key={fact.id ?? `${fact.sequence_index}-${fact.fact_text}`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium uppercase text-slate-700">
                          Step {fact.sequence_index}
                        </span>
                        <span
                          className={`rounded-full border px-3 py-1 text-xs font-medium uppercase ${confidenceTone(
                            fact.confidence,
                          )}`}
                        >
                          {fact.confidence}
                        </span>
                        {fact.hindsight_guard_triggered ? (
                          <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium uppercase text-amber-800">
                            Hindsight override
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-3 text-sm leading-6 text-slate-900">{fact.fact_text}</p>
                      <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2">
                        <p>Evidence: {fact.evidence_summary}</p>
                        <p>Timestamp: {fact.fact_timestamp ?? "Not set"}</p>
                        <p>Source ID: {fact.source_evidence_id}</p>
                        <p>Contradicts: {fact.contradicts_fact ?? "None"}</p>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        className="rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 disabled:cursor-not-allowed disabled:text-slate-400"
                        disabled={isMutating || index === 0}
                        onClick={() => fact.id && void moveFact(fact.id, -1)}
                        type="button"
                      >
                        Up
                      </button>
                      <button
                        className="rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 disabled:cursor-not-allowed disabled:text-slate-400"
                        disabled={isMutating || index === sortedFacts.length - 1}
                        onClick={() => fact.id && void moveFact(fact.id, 1)}
                        type="button"
                      >
                        Down
                      </button>
                      <button
                        className="rounded-full bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
                        disabled={isMutating || !fact.id}
                        onClick={() => {
                          setEditingFactId(fact.id ?? null);
                          setEditDraft(buildDraft(fact));
                        }}
                        type="button"
                      >
                        Edit
                      </button>
                    </div>
                  </div>

                  {editingFactId === fact.id ? (
                    <div className="mt-4">
                      <FactForm
                        disabled={isMutating}
                        draft={editDraft}
                        evidenceSources={evidenceSources}
                        onChange={setEditDraft}
                        onSubmit={saveFact}
                        submitLabel={isMutating ? "Saving..." : "Save fact"}
                      />
                      <button
                        className="mt-3 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
                        disabled={isMutating}
                        onClick={() => {
                          setEditingFactId(null);
                          setEditDraft(emptyDraft);
                        }}
                        type="button"
                      >
                        Cancel edit
                      </button>
                    </div>
                  ) : null}

                  {fact.id && sortedFacts.length > 1 ? (
                    <div className="mt-4 flex flex-wrap items-end gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-3">
                      <label className="block min-w-56 flex-1 text-sm font-medium text-slate-700">
                        Contradicts fact
                        <select
                          className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
                          disabled={isMutating}
                          onChange={(event) =>
                            setContradictionTargets((current) => ({
                              ...current,
                              [fact.id as number]: event.target.value,
                            }))
                          }
                          value={contradictionTargets[fact.id] ?? ""}
                        >
                          <option value="">Select fact</option>
                          {sortedFacts
                            .filter((candidate) => candidate.id && candidate.id !== fact.id)
                            .map((candidate) => (
                              <option key={candidate.id} value={candidate.id}>
                                Step {candidate.sequence_index}: {candidate.fact_text.slice(0, 70)}
                              </option>
                            ))}
                        </select>
                      </label>
                      <button
                        className="inline-flex min-h-10 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
                        disabled={isMutating || !contradictionTargets[fact.id]}
                        onClick={() => void markContradiction(fact.id as number)}
                        type="button"
                      >
                        Mark contradiction
                      </button>
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </div>

        <aside className="space-y-4">
          <section>
            <h2 className="mb-3 text-xl font-semibold text-slate-900">Add Fact</h2>
            <FactForm
              disabled={isMutating || evidenceSources.length === 0}
              draft={draft}
              evidenceSources={evidenceSources}
              onChange={setDraft}
              onSubmit={createFact}
              submitLabel={isMutating ? "Adding..." : "Add fact"}
            />
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Phase Gate</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Continue when the fact sequence is complete and every required evidence tab has
              entries or an accepted not-applicable justification.
            </p>
            <button
              className="mt-4 inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
              disabled={isMutating || Boolean(gate && !gate.can_continue)}
              onClick={continueToPhase5}
              type="button"
            >
              {isMutating ? "Checking phase gate..." : "Continue to Phase 5"}
            </button>
            {phaseAdvanceError ? (
              <p className="mt-3 text-sm font-medium text-rose-700">{phaseAdvanceError}</p>
            ) : gate && !gate.can_continue ? (
              <div className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                {gate.blockers.map((blocker) => (
                  <p key={blocker}>{blocker}</p>
                ))}
              </div>
            ) : null}
          </section>

          <Link
            className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
            to="/safety/incidents"
          >
            Back to incidents
          </Link>
        </aside>
      </section>
    </section>
  );
}

export default SafetyIncidentPhase4;
