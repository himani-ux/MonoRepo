import { useCallback, useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi, type SafetyOfficeWorkflowPayload } from "../../../lib/api/safety";
import {
  safetyChainOfCustodyRowSchema,
  safetyEvidenceDeadlineTaskSchema,
  safetyEvidenceMatrixRowSchema,
  safetyIncidentPhase3TabSchema,
  safetyWitnessInterviewSchema,
  type SafetyChainOfCustodyRow,
  type SafetyEvidenceDeadlineTask,
  type SafetyEvidenceMatrixRow,
  type SafetyIncidentPhase3Tab,
  type SafetyWitnessInterview,
} from "../../../schemas/safety/incident-phase3";
import SafetyChainOfCustodyTable from "./chain-of-custody-table";
import SafetyEvidenceDeadlineTasks from "./evidence-deadline-tasks";
import SafetyEvidenceMatrix from "./evidence-matrix";
import SafetyHealthFatiguePanel from "./health-fatigue-panel";
import SafetyInterviewModule from "./interview-module";
import SafetyMarineDocumentChecklist from "./marine-document-checklist";

export type SafetyIncidentPhase3TabKey =
  | "people"
  | "position"
  | "parts"
  | "paper"
  | "electronic"
  | "chain-of-custody"
  | "matrix"
  | "interviews";

type EvidenceTabKey = Extract<
  SafetyIncidentPhase3TabKey,
  "people" | "position" | "parts" | "paper" | "electronic"
>;

interface SafetyIncidentPhase3Props {
  activeTab?: SafetyIncidentPhase3TabKey;
}

interface SafetyIncidentPhase3State {
  chainOfCustody: SafetyChainOfCustodyRow[];
  deadlineTasks: SafetyEvidenceDeadlineTask[];
  evidenceMatrix: SafetyEvidenceMatrixRow[];
  interviews: SafetyWitnessInterview[];
  tabs: Record<EvidenceTabKey, SafetyIncidentPhase3Tab>;
}

const evidenceTabs: Array<{
  key: EvidenceTabKey;
  label: string;
  route: string;
  prompt: string;
}> = [
  {
    key: "people",
    label: "People",
    prompt: "Witnesses, interview links, health and fatigue evidence.",
    route: "people",
  },
  {
    key: "position",
    label: "Position / Places",
    prompt: "Position, place, 4-angle photos, sketches, deck-plan references.",
    route: "places",
  },
  {
    key: "parts",
    label: "Parts / Equipment",
    prompt: "Damaged equipment, samples, wear notes, manual PMS reference.",
    route: "parts",
  },
  {
    key: "paper",
    label: "Paper / Procedures",
    prompt: "SMS procedures, voyage documents, logs, permits, certificates.",
    route: "paper",
  },
  {
    key: "electronic",
    label: "Photos / Electronic",
    prompt: "VDR, ECDIS, GPS, UMS, VTS, CCTV, fire-system, AIS evidence.",
    route: "photos",
  },
];

const workspaceTabs: Array<{
  key: SafetyIncidentPhase3TabKey;
  label: string;
  route: string;
}> = [
  ...evidenceTabs.map(({ key, label, route }) => ({ key, label, route })),
  { key: "chain-of-custody", label: "Chain of Custody", route: "chain-of-custody" },
  { key: "matrix", label: "Evidence Matrix", route: "evidence-matrix" },
  { key: "interviews", label: "Interviews", route: "interviews" },
];

const tabCodeByKey: Record<EvidenceTabKey, SafetyIncidentPhase3Tab["tab_code"]> = {
  electronic: "ELECTRONIC",
  paper: "PAPER",
  parts: "PARTS",
  people: "PEOPLE",
  position: "POSITION",
};

const defaultState: SafetyIncidentPhase3State = {
  chainOfCustody: [],
  deadlineTasks: [],
  evidenceMatrix: [],
  interviews: [],
  tabs: {
    electronic: createDefaultEvidenceTab("electronic"),
    paper: createDefaultEvidenceTab("paper"),
    parts: createDefaultEvidenceTab("parts"),
    people: createDefaultEvidenceTab("people"),
    position: createDefaultEvidenceTab("position"),
  },
};

function createDefaultEvidenceTab(key: EvidenceTabKey): SafetyIncidentPhase3Tab {
  return {
    entry_count: 0,
    na_justification: null,
    status_chip: "",
    structured_data: {},
    summary: "",
    tab_code: tabCodeByKey[key],
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function parseEvidenceTab(key: EvidenceTabKey, value: unknown): SafetyIncidentPhase3Tab {
  const parsed = safetyIncidentPhase3TabSchema.safeParse(value);
  return parsed.success ? parsed.data : createDefaultEvidenceTab(key);
}

function parseRows<T>(rows: unknown, parser: { safeParse: (row: unknown) => { success: true; data: T } | { success: false } }): T[] {
  return asArray(rows).map((row) => parser.safeParse(row)).filter((result) => result.success).map((result) => result.data);
}

function buildWorkspaceState(
  evidencePayload: unknown,
  chainPayload: unknown,
  matrixPayload: unknown,
  interviewPayload: unknown,
): SafetyIncidentPhase3State {
  const payload = asRecord(evidencePayload);

  return {
    chainOfCustody: parseRows(
      asArray(chainPayload).length > 0 ? chainPayload : payload.chain_of_custody,
      safetyChainOfCustodyRowSchema,
    ),
    deadlineTasks: parseRows(payload.deadline_tasks, safetyEvidenceDeadlineTaskSchema),
    evidenceMatrix: parseRows(
      asArray(matrixPayload).length > 0 ? matrixPayload : payload.evidence_matrix,
      safetyEvidenceMatrixRowSchema,
    ),
    interviews: parseRows(
      asArray(interviewPayload).length > 0 ? interviewPayload : payload.interviews ?? payload.witness_interviews,
      safetyWitnessInterviewSchema,
    ),
    tabs: {
      electronic: parseEvidenceTab("electronic", payload.electronic),
      paper: parseEvidenceTab("paper", payload.paper),
      parts: parseEvidenceTab("parts", payload.parts),
      people: parseEvidenceTab("people", payload.people),
      position: parseEvidenceTab("position", payload.position),
    },
  };
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Not recorded";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (Array.isArray(value)) {
    return `${value.length} item${value.length === 1 ? "" : "s"}`;
  }
  if (typeof value === "object") {
    return `${Object.keys(value).length} field${Object.keys(value).length === 1 ? "" : "s"}`;
  }
  return String(value);
}

function readableKey(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getTabHref(id: string | undefined, route: string) {
  return `/safety/incidents/${id ?? ""}/phase-3/${route}`;
}

function SafetyLoadingState() {
  return (
    <section className="space-y-4">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-24 animate-pulse rounded-3xl bg-slate-100" />
      ))}
    </section>
  );
}

function SafetyTabSummaryCard({ tab }: { tab: SafetyIncidentPhase3Tab }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            {tab.tab_code}
          </p>
          <h2 className="mt-1 text-xl font-semibold text-slate-900">Evidence Summary</h2>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium uppercase text-slate-700">
          {tab.status_chip || `${tab.entry_count} entries`}
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-700">
        {tab.summary || "No evidence summary captured yet."}
      </p>
      {tab.na_justification ? (
        <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {tab.na_justification}
        </p>
      ) : null}
    </article>
  );
}

function SafetyStructuredDataPanel({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data).filter(([key]) => !["cargo_overlay_items", "health_fatigue"].includes(key));

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-xl font-semibold text-slate-900">Captured Fields</h2>
      {entries.length > 0 ? (
        <dl className="mt-4 grid gap-3 md:grid-cols-2">
          {entries.map(([key, value]) => (
            <div key={key} className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3">
              <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                {readableKey(key)}
              </dt>
              <dd className="mt-1 text-sm text-slate-800">{formatValue(value)}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="mt-3 text-sm text-slate-500">No structured fields captured yet.</p>
      )}
    </section>
  );
}

function SafetyEvidenceTabForm({
  disabled,
  onSubmit,
  tabKey,
  tab,
}: {
  disabled: boolean;
  onSubmit: (tabKey: EvidenceTabKey, payload: SafetyOfficeWorkflowPayload) => Promise<void>;
  tabKey: EvidenceTabKey;
  tab: SafetyIncidentPhase3Tab;
}) {
  const [summary, setSummary] = useState(tab.summary);
  const [entryCount, setEntryCount] = useState(String(tab.entry_count));
  const [naJustification, setNaJustification] = useState(tab.na_justification ?? "");
  const [statusChip, setStatusChip] = useState(tab.status_chip);
  const [checklistComplete, setChecklistComplete] = useState(Boolean(asRecord(tab.structured_data).checklist_complete));
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setSummary(tab.summary);
    setEntryCount(String(tab.entry_count));
    setNaJustification(tab.na_justification ?? "");
    setStatusChip(tab.status_chip);
    setChecklistComplete(Boolean(asRecord(tab.structured_data).checklist_complete));
  }, [tab]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onSubmit(tabKey, {
        entry_count: Number(entryCount) || 0,
        na_justification: naJustification.trim() || null,
        status_chip: statusChip,
        structured_data:
          tabKey === "paper"
            ? { ...tab.structured_data, checklist_complete: checklistComplete }
            : tab.structured_data,
        summary,
      });
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <h2 className="text-xl font-semibold text-slate-900">Update Evidence Source</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-[1fr_160px]">
        <label className="block text-sm font-medium text-slate-700">
          Summary
          <textarea
            className="mt-2 min-h-28 w-full rounded-2xl border border-slate-300 bg-white p-3 text-sm text-slate-900 outline-none focus:border-slate-500"
            onChange={(event) => setSummary(event.target.value)}
            value={summary}
          />
        </label>
        <div className="grid gap-4">
          <label className="block text-sm font-medium text-slate-700">
            Entries
            <input
              className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
              min={0}
              onChange={(event) => setEntryCount(event.target.value)}
              type="number"
              value={entryCount}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Status
            <input
              className="mt-2 w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-slate-500"
              onChange={(event) => setStatusChip(event.target.value)}
              value={statusChip}
            />
          </label>
        </div>
      </div>
      <label className="mt-4 block text-sm font-medium text-slate-700">
        N/A justification
        <textarea
          className="mt-2 min-h-20 w-full rounded-2xl border border-slate-300 bg-white p-3 text-sm text-slate-900 outline-none focus:border-slate-500"
          onChange={(event) => setNaJustification(event.target.value)}
          placeholder="Use only when this evidence category is not applicable or unavailable."
          value={naJustification}
        />
      </label>
      {tabKey === "paper" ? (
        <label className="mt-4 flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <input
            checked={checklistComplete}
            className="mt-1 h-4 w-4 rounded border-slate-300"
            onChange={(event) => setChecklistComplete(event.target.checked)}
            type="checkbox"
          />
          <span>
            <span className="block font-medium text-slate-900">Marine document checklist complete</span>
            <span className="mt-1 block text-slate-600">
              Required before the incident can move from Phase 3 to Phase 4.
            </span>
          </span>
        </label>
      ) : null}
      {error ? <p className="mt-3 text-sm font-medium text-rose-700">{error}</p> : null}
      <button
        className="mt-4 inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        disabled={disabled || isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Saving..." : "Save evidence source"}
      </button>
    </form>
  );
}

function SafetyEvidenceAttachmentUpload({
  disabled,
  onUpload,
  tabKey,
}: {
  disabled: boolean;
  onUpload: (tabKey: EvidenceTabKey, file: File) => Promise<void>;
  tabKey: EvidenceTabKey;
}) {
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setError(null);
    setIsUploading(true);
    try {
      await onUpload(tabKey, file);
      event.target.value = "";
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <label className="block rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <span className="text-xl font-semibold text-slate-900">Add Photo Evidence</span>
      <span className="mt-2 block text-sm leading-6 text-slate-600">
        JPG, JPEG, or PNG. Maximum 3MB. The saved path is stored in Phase 3 evidence metadata.
      </span>
      <input
        accept="image/jpeg,image/jpg,image/png"
        aria-label="Phase 3 photo evidence"
        className="mt-4 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900 file:mr-4 file:rounded-full file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
        disabled={disabled || isUploading}
        onChange={handleFileChange}
        type="file"
      />
      {isUploading ? <span className="mt-3 block text-sm font-medium text-slate-600">Uploading photo...</span> : null}
      {error ? <span className="mt-3 block text-sm font-medium text-rose-700">{error}</span> : null}
    </label>
  );
}

function SafetyChainOfCustodyCreateForm({
  disabled,
  onCreate,
}: {
  disabled: boolean;
  onCreate: (payload: SafetyOfficeWorkflowPayload) => Promise<void>;
}) {
  const [description, setDescription] = useState("");
  const [collectorName, setCollectorName] = useState("");
  const [storageLocation, setStorageLocation] = useState("");
  const [witnessSignature, setWitnessSignature] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onCreate({
        collection_timestamp: new Date().toISOString(),
        collector_name: collectorName,
        collector_signature: collectorName,
        current_holder: collectorName,
        description,
        storage_location: storageLocation,
        witness_signature: witnessSignature,
      });
      setDescription("");
      setCollectorName("");
      setStorageLocation("");
      setWitnessSignature("");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <h2 className="text-xl font-semibold text-slate-900">Add Custody Item</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700">
          Description
          <input className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setDescription(event.target.value)} value={description} />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Collector
          <input className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setCollectorName(event.target.value)} value={collectorName} />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Storage location
          <input className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setStorageLocation(event.target.value)} value={storageLocation} />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Witness signature
          <input className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setWitnessSignature(event.target.value)} value={witnessSignature} />
        </label>
      </div>
      {error ? <p className="mt-3 text-sm font-medium text-rose-700">{error}</p> : null}
      <button className="mt-4 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:bg-slate-400" disabled={disabled || isSubmitting} type="submit">
        {isSubmitting ? "Adding..." : "Add custody item"}
      </button>
    </form>
  );
}

function SafetyEvidenceMatrixCreateForm({
  disabled,
  onCreate,
}: {
  disabled: boolean;
  onCreate: (payload: SafetyOfficeWorkflowPayload) => Promise<void>;
}) {
  const [finding, setFinding] = useState("");
  const [proEvidence, setProEvidence] = useState("");
  const [conEvidence, setConEvidence] = useState("");
  const [sourceLabel, setSourceLabel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onCreate({
        con_evidence: conEvidence,
        finding,
        pro_evidence: proEvidence,
        source_label: sourceLabel,
      });
      setFinding("");
      setProEvidence("");
      setConEvidence("");
      setSourceLabel("");
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <h2 className="text-xl font-semibold text-slate-900">Add Matrix Row</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700">
          Finding
          <input className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setFinding(event.target.value)} value={finding} />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Source
          <input className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setSourceLabel(event.target.value)} value={sourceLabel} />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Pro evidence
          <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setProEvidence(event.target.value)} value={proEvidence} />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Con evidence
          <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setConEvidence(event.target.value)} value={conEvidence} />
        </label>
      </div>
      {error ? <p className="mt-3 text-sm font-medium text-rose-700">{error}</p> : null}
      <button className="mt-4 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:bg-slate-400" disabled={disabled || isSubmitting} type="submit">
        {isSubmitting ? "Adding..." : "Add matrix row"}
      </button>
    </form>
  );
}

function SafetyInterviewCreateForm({
  disabled,
  onCreate,
}: {
  disabled: boolean;
  onCreate: (payload: SafetyOfficeWorkflowPayload) => Promise<void>;
}) {
  const [witnessName, setWitnessName] = useState("");
  const [interviewType, setInterviewType] = useState<"FORMAL" | "INFORMAL">("FORMAL");
  const [makeAcquaintanceNotes, setMakeAcquaintanceNotes] = useState("");
  const [introductionNotes, setIntroductionNotes] = useState("");
  const [meetingNotes, setMeetingNotes] = useState("");
  const [conclusionNotes, setConclusionNotes] = useState("");
  const [reason, setReason] = useState("");
  const [readBackConfirmed, setReadBackConfirmed] = useState(false);
  const [witnessSignature, setWitnessSignature] = useState("");
  const [copyToWitnessRecorded, setCopyToWitnessRecorded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const formalComplete = Boolean(
    makeAcquaintanceNotes.trim()
      && introductionNotes.trim()
      && meetingNotes.trim()
      && conclusionNotes.trim()
      && readBackConfirmed
      && witnessSignature.trim()
      && copyToWitnessRecorded,
  );
  const informalComplete = Boolean(reason.trim() && meetingNotes.trim());
  const canSubmit = Boolean(
    witnessName.trim() && (interviewType === "FORMAL" ? formalComplete : informalComplete),
  );

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onCreate({
        conclusion_notes: interviewType === "FORMAL" ? conclusionNotes : "",
        copy_to_witness_recorded: interviewType === "FORMAL" ? copyToWitnessRecorded : false,
        interview_type: interviewType,
        introduction_notes: interviewType === "FORMAL" ? introductionNotes : "",
        make_acquaintance_notes: interviewType === "FORMAL" ? makeAcquaintanceNotes : "",
        meeting_notes: meetingNotes,
        question_rows: [],
        read_back_confirmed: interviewType === "FORMAL" ? readBackConfirmed : false,
        reason_formal_impossible: interviewType === "INFORMAL" ? reason : null,
        witness_signature: interviewType === "FORMAL" ? witnessSignature : null,
        witness_name: witnessName,
      });
      setWitnessName("");
      setInterviewType("FORMAL");
      setMakeAcquaintanceNotes("");
      setIntroductionNotes("");
      setMeetingNotes("");
      setConclusionNotes("");
      setReason("");
      setReadBackConfirmed(false);
      setWitnessSignature("");
      setCopyToWitnessRecorded(false);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <h2 className="text-xl font-semibold text-slate-900">Add Interview</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700">
          Witness
          <input className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setWitnessName(event.target.value)} value={witnessName} />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Interview type
          <select
            className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2"
            onChange={(event) => setInterviewType(event.target.value as "FORMAL" | "INFORMAL")}
            value={interviewType}
          >
            <option value="FORMAL">Formal</option>
            <option value="INFORMAL">Informal</option>
          </select>
        </label>
      </div>
      {interviewType === "FORMAL" ? (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            Make acquaintance
            <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setMakeAcquaintanceNotes(event.target.value)} value={makeAcquaintanceNotes} />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Introduction
            <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setIntroductionNotes(event.target.value)} value={introductionNotes} />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Meeting
            <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setMeetingNotes(event.target.value)} value={meetingNotes} />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Conclusion
            <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setConclusionNotes(event.target.value)} value={conclusionNotes} />
          </label>
          <label className="block text-sm font-medium text-slate-700 md:col-span-2">
            Witness signature
            <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setWitnessSignature(event.target.value)} value={witnessSignature} />
          </label>
          <div className="grid gap-3 md:col-span-2 md:grid-cols-2">
            <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <input checked={readBackConfirmed} className="mt-1 h-4 w-4 rounded border-slate-300" onChange={(event) => setReadBackConfirmed(event.target.checked)} type="checkbox" />
              <span>
                <span className="block font-medium text-slate-900">Read-back confirmed</span>
                <span className="mt-1 block text-slate-600">Statement was read back to the witness.</span>
              </span>
            </label>
            <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <input checked={copyToWitnessRecorded} className="mt-1 h-4 w-4 rounded border-slate-300" onChange={(event) => setCopyToWitnessRecorded(event.target.checked)} type="checkbox" />
              <span>
                <span className="block font-medium text-slate-900">Copy-to-witness recorded</span>
                <span className="mt-1 block text-slate-600">Witness copy was issued or recorded.</span>
              </span>
            </label>
          </div>
        </div>
      ) : (
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-medium text-slate-700">
            Informal reason
            <input className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3 py-2" onChange={(event) => setReason(event.target.value)} value={reason} />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Meeting notes
            <textarea className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3" onChange={(event) => setMeetingNotes(event.target.value)} value={meetingNotes} />
          </label>
        </div>
      )}
      {error ? <p className="mt-3 text-sm font-medium text-rose-700">{error}</p> : null}
      <button className="mt-4 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:bg-slate-400" disabled={disabled || isSubmitting || !canSubmit} type="submit">
        {isSubmitting ? "Adding..." : "Add interview"}
      </button>
    </form>
  );
}

function SafetyEvidenceSourcePanel({
  disabled,
  interviews,
  onAttachmentUpload,
  onEvidenceSubmit,
  tabKey,
  tab,
}: {
  disabled: boolean;
  interviews?: SafetyWitnessInterview[];
  onAttachmentUpload: (tabKey: EvidenceTabKey, file: File) => Promise<void>;
  onEvidenceSubmit: (tabKey: EvidenceTabKey, payload: SafetyOfficeWorkflowPayload) => Promise<void>;
  tabKey: EvidenceTabKey;
  tab: SafetyIncidentPhase3Tab;
}) {
  const structuredData = asRecord(tab.structured_data);
  const tabConfig = evidenceTabs.find((item) => item.key === tabKey);
  const healthFatigue = asRecord(structuredData.health_fatigue);
  const cargoOverlayItems = asArray(structuredData.cargo_overlay_items)
    .map((item) => asRecord(item))
    .map((item) => ({
      code: String(item.code ?? item.label ?? "Cargo prompt"),
      status: String(item.status ?? "Pending"),
    }));

  return (
    <div className="space-y-5">
      <section className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          FEAT-SAF-INC-005
        </p>
        <h2 className="mt-1 text-2xl font-semibold text-slate-900">{tabConfig?.label}</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">{tabConfig?.prompt}</p>
      </section>
      <SafetyTabSummaryCard tab={tab} />
      <SafetyStructuredDataPanel data={structuredData} />
      {tabKey === "people" ? (
        <>
          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-semibold text-slate-900">Witness Interviews</h2>
              <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                {interviews?.length ?? 0} interviews
              </span>
            </div>
            {interviews && interviews.length > 0 ? (
              <div className="mt-4 grid gap-3">
                {interviews.map((interview, index) => (
                  <article
                    key={interview.id ?? `${interview.witness_name}-${index}`}
                    className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
                  >
                    <div className="font-medium text-slate-900">{interview.witness_name}</div>
                    <div className="mt-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                      {interview.interview_type} - {interview.phase_count} / 4 phases
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-sm text-slate-500">No witness interviews recorded yet.</p>
            )}
          </section>
          <SafetyHealthFatiguePanel
            medicalRecords={asArray(healthFatigue.medical_records).map(String)}
            mlcReportable={Boolean(healthFatigue.mlc_reportable)}
            summary={String(healthFatigue.summary ?? "No health / fatigue narrative captured yet.")}
          />
        </>
      ) : null}
      {tabKey === "paper" ? (
        <SafetyMarineDocumentChecklist
          cargoOverlayItems={cargoOverlayItems}
          checklistComplete={Boolean(structuredData.checklist_complete)}
        />
      ) : null}
      {tabKey === "parts" ? (
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">Manual PMS Reference</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Record equipment history references manually; PMS remains decoupled for this release.
          </p>
        </section>
      ) : null}
      <SafetyEvidenceAttachmentUpload disabled={disabled} onUpload={onAttachmentUpload} tabKey={tabKey} />
      <SafetyEvidenceTabForm disabled={disabled} onSubmit={onEvidenceSubmit} tab={tab} tabKey={tabKey} />
    </div>
  );
}

export function SafetyIncidentPhase3({
  activeTab = "people",
}: SafetyIncidentPhase3Props) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<SafetyIncidentPhase3State>(defaultState);
  const [error, setError] = useState<string | null>(null);
  const [phaseAdvanceError, setPhaseAdvanceError] = useState<string | null>(null);
  const [loadWarnings, setLoadWarnings] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);

  const currentTab = workspaceTabs.some((tab) => tab.key === activeTab) ? activeTab : "people";

  const totalEvidenceEntries = useMemo(
    () => evidenceTabs.reduce((sum, tab) => sum + workspace.tabs[tab.key].entry_count, 0),
    [workspace.tabs],
  );
  const phase4Blockers = useMemo(() => {
    const blockers: string[] = [];
    if (workspace.chainOfCustody.length === 0) {
      blockers.push("add at least one chain-of-custody item");
    }
    if (!Boolean(asRecord(workspace.tabs.paper.structured_data).checklist_complete)) {
      blockers.push("complete the Paper / Procedures marine document checklist");
    }
    return blockers;
  }, [workspace.chainOfCustody.length, workspace.tabs.paper.structured_data]);

  const reload = useCallback(async () => {
    if (!id) {
      setError("Invalid incident id.");
      setIsLoading(false);
      return;
    }

    setError(null);
    setIsLoading(true);
    const [evidence, chain, matrix, interviews] = await Promise.allSettled([
      safetyApi.getIncidentPhase3Evidence(id),
      safetyApi.getIncidentPhase3ChainOfCustody(id),
      safetyApi.getIncidentPhase3EvidenceMatrix(id),
      safetyApi.getIncidentPhase3Interviews(id),
    ]);

    if (evidence.status === "rejected") {
      setError(getErrorMessage(evidence.reason));
      setIsLoading(false);
      return;
    }

    const warnings = [
      chain.status === "rejected" ? "Chain of custody could not be refreshed." : null,
      matrix.status === "rejected" ? "Evidence matrix could not be refreshed." : null,
      interviews.status === "rejected" ? "Interviews could not be refreshed." : null,
    ].filter(Boolean) as string[];

    setWorkspace(
      buildWorkspaceState(
        evidence.value,
        chain.status === "fulfilled" ? chain.value : undefined,
        matrix.status === "fulfilled" ? matrix.value : undefined,
        interviews.status === "fulfilled" ? interviews.value : undefined,
      ),
    );
    setLoadWarnings(warnings);
    setIsLoading(false);
  }, [id]);

  useEffect(() => {
    void reload();
  }, [reload]);

  async function submitEvidenceTab(tabKey: EvidenceTabKey, payload: SafetyOfficeWorkflowPayload) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      const response = await safetyApi.updateIncidentPhase3Evidence(id, { [tabKey]: payload });
      setWorkspace((current) =>
        buildWorkspaceState(response, current.chainOfCustody, current.evidenceMatrix, current.interviews),
      );
    } finally {
      setIsMutating(false);
    }
  }

  async function uploadEvidenceAttachment(tabKey: EvidenceTabKey, file: File) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      const response = await safetyApi.uploadIncidentPhase3Attachment(id, tabKey, file);
      setWorkspace(
        buildWorkspaceState(response.workspace, workspace.chainOfCustody, workspace.evidenceMatrix, workspace.interviews),
      );
    } finally {
      setIsMutating(false);
    }
  }

  async function createCustody(payload: SafetyOfficeWorkflowPayload) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.createIncidentPhase3ChainOfCustody(id, payload);
      await reload();
    } finally {
      setIsMutating(false);
    }
  }

  async function createMatrixRow(payload: SafetyOfficeWorkflowPayload) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.createIncidentPhase3EvidenceMatrixRow(id, payload);
      await reload();
    } finally {
      setIsMutating(false);
    }
  }

  async function createInterview(payload: SafetyOfficeWorkflowPayload) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.createIncidentPhase3Interview(id, payload);
      await reload();
    } finally {
      setIsMutating(false);
    }
  }

  async function completeDeadlineTask(task: SafetyEvidenceDeadlineTask, justification: string) {
    if (!id || !task.id) {
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.updateIncidentPhase3DeadlineTask(id, task.id, {
        justification: justification.trim() || null,
        status: "COMPLETED",
      });
      await reload();
    } finally {
      setIsMutating(false);
    }
  }

  async function continueToPhase4() {
    if (!id) {
      return;
    }
    if (phase4Blockers.length > 0) {
      setPhaseAdvanceError(`Before Phase 4, ${phase4Blockers.join(" and ")}.`);
      return;
    }
    setPhaseAdvanceError(null);
    setIsMutating(true);
    try {
      await safetyApi.transitionIncident(id, { target_phase: 4 });
      navigate(`/safety/incidents/${id}/phase-4`);
    } catch (caught) {
      setPhaseAdvanceError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  function renderActiveTab() {
    if (currentTab === "chain-of-custody") {
      return (
        <div className="space-y-5">
          <SafetyChainOfCustodyTable rows={workspace.chainOfCustody} />
          <SafetyChainOfCustodyCreateForm disabled={isMutating} onCreate={createCustody} />
        </div>
      );
    }
    if (currentTab === "matrix") {
      return (
        <div className="space-y-5">
          <SafetyEvidenceMatrix rows={workspace.evidenceMatrix} />
          <SafetyEvidenceMatrixCreateForm disabled={isMutating} onCreate={createMatrixRow} />
        </div>
      );
    }
    if (currentTab === "interviews") {
      return (
        <div className="space-y-5">
          <SafetyInterviewModule interviews={workspace.interviews} />
          <SafetyInterviewCreateForm disabled={isMutating} onCreate={createInterview} />
        </div>
      );
    }

    return (
      <SafetyEvidenceSourcePanel
        disabled={isMutating}
        interviews={workspace.interviews}
        onAttachmentUpload={uploadEvidenceAttachment}
        onEvidenceSubmit={submitEvidenceTab}
        tab={workspace.tabs[currentTab]}
        tabKey={currentTab}
      />
    );
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Safety / Incident / Phase 3
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">
              Phase 3 Evidence Workspace
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Capture the DNV five-source evidence picture, preserve custody, and keep interviews tied to the incident record.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Incident</div>
              <div className="mt-1 font-semibold text-slate-900">#{id}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Evidence</div>
              <div className="mt-1 font-semibold text-slate-900">{totalEvidenceEntries}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Custody</div>
              <div className="mt-1 font-semibold text-slate-900">{workspace.chainOfCustody.length}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Interviews</div>
              <div className="mt-1 font-semibold text-slate-900">{workspace.interviews.length}</div>
            </div>
          </div>
        </div>
      </header>

      <nav
        aria-label="Phase 3 evidence tabs"
        className="overflow-x-auto rounded-3xl border border-slate-200 bg-white p-2 shadow-sm"
      >
        <div className="flex min-w-max gap-2">
          {workspaceTabs.map((tab) => (
            <Link
              key={tab.key}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                currentTab === tab.key
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
              to={getTabHref(id, tab.route)}
            >
              {tab.label}
            </Link>
          ))}
        </div>
      </nav>

      {loadWarnings.length > 0 ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {loadWarnings.join(" ")}
        </section>
      ) : null}

      {error ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-900 shadow-sm">
          {error}
        </section>
      ) : isLoading ? (
        <SafetyLoadingState />
      ) : (
        <>
          <SafetyEvidenceDeadlineTasks
            disabled={isMutating}
            onComplete={completeDeadlineTask}
            tasks={workspace.deadlineTasks}
          />
          {renderActiveTab()}
        </>
      )}

      <div className="flex flex-wrap gap-3">
        <Link
          className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
          to="/safety/incidents"
        >
          Back to incidents
        </Link>
        <button
          className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isMutating || phase4Blockers.length > 0}
          onClick={continueToPhase4}
          type="button"
        >
          {isMutating ? "Advancing..." : "Continue to Phase 4"}
        </button>
      </div>
      {phaseAdvanceError ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          {phaseAdvanceError}
        </section>
      ) : phase4Blockers.length > 0 ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Before Phase 4, {phase4Blockers.join(" and ")}.
        </section>
      ) : null}
    </section>
  );
}

export default SafetyIncidentPhase3;
