import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../../../../lib/api/client";
import { safetyApi, type SafetyOfficeWorkflowPayload } from "../../../../lib/api/safety";
import { useAuth } from "../../../../hooks/use-auth";
import SafetyIncidentPhase3, {
  type SafetyIncidentPhase3TabKey,
} from "../../../../components/safety/incident/phase-3-workspace";
import SafetyIncidentPhase4 from "../../../../components/safety/incident/phase-4-workspace";
import SafetyIncidentPhase5 from "../../../../components/safety/incident/phase-5-workspace";
import SafetyIncidentPhase6 from "../../../../components/safety/incident/phase-6-workspace";
import SafetyIncidentPhase7 from "../../../../components/safety/incident/phase-7-workspace";
import SafetyIncidentPhase8 from "../../../../components/safety/incident/phase-8-workspace";
import SafetyIncidentPhase9 from "../../../../components/safety/incident/phase-9-workspace";
import SafetyIncidentReopenWorkspace from "../../../../components/safety/incident/reopen-workspace";
import type { SafetyCorrectiveAction } from "../../../../schemas/safety/corrective-action";

type Loader = (id: string) => Promise<unknown>;
type Mutator = (id: string, payload: SafetyOfficeWorkflowPayload) => Promise<unknown>;
type Downloader = (id: string) => Promise<{ blob: Blob; fileName: string }>;
type IncidentCorrectiveAction = SafetyCorrectiveAction & {
  recommendation_id?: number | null;
  source_id?: number | null;
  source_table?: string | null;
};

function stringifyPayload(payload: unknown): string {
  return JSON.stringify(payload ?? null, null, 2);
}

function parseJsonPayload(value: string): SafetyOfficeWorkflowPayload {
  const trimmed = value.trim();
  if (!trimmed) {
    return {};
  }
  const parsed = JSON.parse(trimmed) as SafetyOfficeWorkflowPayload;
  if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Payload must be a JSON object.");
  }
  return parsed;
}

function downloadBlob({ blob, fileName }: { blob: Blob; fileName: string }) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function resolveCurrentActorId(user: ReturnType<typeof useAuth>["user"]) {
  if (!user) {
    return "";
  }
  const userWithBackendIds = user as typeof user & { user_id?: string | number | null };
  return String(
    user.username ||
      user.employee_id ||
      user.crew_id ||
      userWithBackendIds.user_id ||
      user.id ||
      "",
  ).trim();
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-900">{value}</p>
    </article>
  );
}

function PayloadViewer({ payload }: { payload: unknown }) {
  return (
    <pre className="max-h-[520px] overflow-auto rounded-3xl border border-slate-200 bg-slate-950 p-5 text-xs leading-6 text-slate-100 shadow-sm">
      {stringifyPayload(payload)}
    </pre>
  );
}

function JsonMutationForm({
  buttonLabel,
  defaultPayload,
  disabled,
  helperText,
  mutator,
  onMutated,
}: {
  buttonLabel: string;
  defaultPayload: SafetyOfficeWorkflowPayload;
  disabled?: boolean;
  helperText: string;
  mutator: Mutator;
  onMutated: (payload: unknown) => void;
}) {
  const { id } = useParams();
  const [payload, setPayload] = useState(() => stringifyPayload(defaultPayload));
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      const response = await mutator(id, parseJsonPayload(payload));
      onMutated(response);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <h2 className="text-lg font-semibold text-slate-900">{buttonLabel}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{helperText}</p>
      <textarea
        className="mt-4 min-h-44 w-full rounded-2xl border border-slate-300 bg-slate-50 p-3 font-mono text-xs text-slate-800 outline-none focus:border-slate-500"
        onChange={(event) => setPayload(event.target.value)}
        value={payload}
      />
      {error ? <p className="mt-3 text-sm font-medium text-rose-700">{error}</p> : null}
      <button
        className="mt-4 inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        disabled={disabled || isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Submitting..." : buttonLabel}
      </button>
    </form>
  );
}

function DownloadCard({
  buttonLabel,
  downloader,
  helperText,
}: {
  buttonLabel: string;
  downloader: Downloader;
  helperText: string;
}) {
  const { id } = useParams();
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  async function handleDownload() {
    if (!id) {
      return;
    }
    setError(null);
    setIsDownloading(true);
    try {
      downloadBlob(await downloader(id));
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{buttonLabel}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{helperText}</p>
      {error ? <p className="mt-3 text-sm font-medium text-rose-700">{error}</p> : null}
      <button
        className="mt-4 inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        disabled={isDownloading}
        onClick={handleDownload}
        type="button"
      >
        {isDownloading ? "Preparing export..." : buttonLabel}
      </button>
    </section>
  );
}

const nextCorrectiveActionStatus: Partial<Record<SafetyCorrectiveAction["status"], SafetyCorrectiveAction["status"]>> = {
  OPEN: "IN_PROGRESS",
  IN_PROGRESS: "PENDING_VERIFY",
  PENDING_VERIFY: "CLOSED",
  REOPENED: "IN_PROGRESS",
};

function statusActionLabel(status: SafetyCorrectiveAction["status"]) {
  switch (status) {
    case "OPEN":
      return "Start work";
    case "IN_PROGRESS":
      return "Send to verification";
    case "PENDING_VERIFY":
      return "Close action";
    case "REOPENED":
      return "Restart work";
    default:
      return "No transition";
  }
}

function CorrectiveActionManager({
  actions,
  reload,
}: {
  actions: IncidentCorrectiveAction[];
  reload: () => Promise<void>;
}) {
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [mutatingId, setMutatingId] = useState<number | null>(null);

  function noteFor(action: SafetyCorrectiveAction) {
    return notes[action.id] ?? `Progress update for corrective action #${action.id}.`;
  }

  async function transitionAction(action: SafetyCorrectiveAction) {
    const nextStatus = nextCorrectiveActionStatus[action.status];
    if (!nextStatus) {
      return;
    }
    setError(null);
    setMutatingId(action.id);
    try {
      await safetyApi.transitionCorrectiveAction(action.id, {
        note: noteFor(action),
        status: nextStatus,
      });
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setMutatingId(null);
    }
  }

  async function verifyAction(action: SafetyCorrectiveAction) {
    setError(null);
    setMutatingId(action.id);
    try {
      await safetyApi.verifyCorrectiveAction(action.id, {
        note: noteFor(action),
      });
      await reload();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setMutatingId(null);
    }
  }

  return (
    <section className="space-y-4">
      {error ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          {error}
        </div>
      ) : null}
      {actions.length === 0 ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-5 text-sm text-slate-600 shadow-sm">
          No corrective actions are linked to this incident.
        </div>
      ) : null}
      {actions.map((action) => {
        const nextStatus = nextCorrectiveActionStatus[action.status];
        return (
          <article key={action.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div className="flex flex-wrap gap-2">
                  <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-white">
                    CA #{action.id}
                  </span>
                  <span className="rounded-full border border-slate-300 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
                    {action.status.replaceAll("_", " ")}
                  </span>
                  {action.physical_verification_done ? (
                    <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800">
                      Physical verification done
                    </span>
                  ) : null}
                </div>
                <h2 className="mt-3 text-xl font-semibold text-slate-900">{action.title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">{action.description}</p>
                <div className="mt-3 grid gap-3 text-sm text-slate-600 md:grid-cols-3">
                  <p>Recommendation: <span className="font-semibold text-slate-900">#{action.recommendation_id ?? "n/a"}</span></p>
                  <p>Due: <span className="font-semibold text-slate-900">{action.due_date ?? "Not set"}</span></p>
                  <p>Verifier: <span className="font-semibold text-slate-900">{action.verifier_user_id ?? "Not set"}</span></p>
                </div>
              </div>
              <div className="w-full space-y-3 lg:max-w-sm">
                <label className="block text-sm font-medium text-slate-700">
                  Action note
                  <textarea
                    className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3 text-sm"
                    onChange={(event) =>
                      setNotes((current) => ({ ...current, [action.id]: event.target.value }))
                    }
                    value={noteFor(action)}
                  />
                </label>
                <div className="flex flex-wrap gap-2">
                  {nextStatus ? (
                    <button
                      className="min-h-10 rounded-full bg-slate-900 px-4 text-sm font-semibold text-white disabled:bg-slate-400"
                      disabled={mutatingId === action.id || !noteFor(action).trim()}
                      onClick={() => void transitionAction(action)}
                      type="button"
                    >
                      {mutatingId === action.id ? "Saving..." : statusActionLabel(action.status)}
                    </button>
                  ) : null}
                  {!action.physical_verification_done ? (
                    <button
                      className="min-h-10 rounded-full border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 disabled:bg-slate-100 disabled:text-slate-400"
                      disabled={mutatingId === action.id || !noteFor(action).trim()}
                      onClick={() => void verifyAction(action)}
                      type="button"
                    >
                      Record physical verification
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          </article>
        );
      })}
    </section>
  );
}

function CreateCorrectiveActionForm({ onCreated }: { onCreated: () => Promise<void> }) {
  const { id } = useParams();
  const { user } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const verifierUserId = resolveCurrentActorId(user);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!id) {
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      await safetyApi.createCorrectiveAction({
        description,
        due_date: dueDate || null,
        source_id: id,
        source_table: "vims_safety_incident",
        title,
        verifier_user_id: verifierUserId || null,
      });
      setTitle("");
      setDescription("");
      setDueDate("");
      await onCreated();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <h2 className="text-lg font-semibold text-slate-900">Create corrective action</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700">
          Title
          <input
            className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
            onChange={(event) => setTitle(event.target.value)}
            value={title}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Due date
          <input
            className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-3"
            onChange={(event) => setDueDate(event.target.value)}
            type="date"
            value={dueDate}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700 md:col-span-2">
          Description
          <textarea
            className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3"
            onChange={(event) => setDescription(event.target.value)}
            value={description}
          />
        </label>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          Verifier from login:{" "}
          <span className="font-semibold text-slate-900">
            {user?.full_name || verifierUserId || "Current user"}
          </span>
        </div>
      </div>
      {error ? <p className="mt-3 text-sm font-medium text-rose-700">{error}</p> : null}
      <button
        className="mt-4 inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        disabled={isSubmitting || !title.trim() || !description.trim()}
        type="submit"
      >
        {isSubmitting ? "Creating..." : "Create action"}
      </button>
    </form>
  );
}

export function IncidentOfficeReadRoute({
  area,
  loader,
  title,
  children,
}: {
  area: string;
  loader: Loader;
  title: string;
  children?: (args: { payload: unknown; reload: () => Promise<void>; setPayload: (payload: unknown) => void }) => ReactNode;
}) {
  const { id } = useParams();
  const [payload, setPayload] = useState<unknown>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const reload = useMemo(
    () => async () => {
      if (!id) {
        setError("Invalid incident id.");
        setIsLoading(false);
        return;
      }
      setError(null);
      setIsLoading(true);
      try {
        setPayload(await loader(id));
      } catch (caught) {
        setError(getErrorMessage(caught));
      } finally {
        setIsLoading(false);
      }
    },
    [id, loader],
  );

  useEffect(() => {
    void reload();
  }, [reload]);

  if (isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading {title.toLowerCase()}...
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-sm text-rose-900 shadow-sm">
        {error}
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_58%,#e0f2fe_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">{area}</p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          This route is now backed by the live Safety API for incident #{id}. Backend vessel scope,
          role checks, phase gates, audit logs, and field-history rules remain server-enforced.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
            to="/safety/incidents"
          >
            Back to incidents
          </Link>
          <button
            className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            onClick={() => void reload()}
            type="button"
          >
            Refresh backend state
          </button>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <StatusCard label="Record" value={`Incident #${id}`} />
        <StatusCard label="Source" value="Live Safety API" />
        <StatusCard label="Security" value="Backend vessel scope enforced" />
      </section>

      {children?.({ payload, reload, setPayload })}

      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-900">Backend payload</h2>
        <PayloadViewer payload={payload} />
      </section>
    </section>
  );
}

export function IncidentPhase3Route({ activeTab = "people" }: { activeTab?: SafetyIncidentPhase3TabKey }) {
  return <SafetyIncidentPhase3 activeTab={activeTab} />;
}

export function IncidentPhase4Route() {
  return <SafetyIncidentPhase4 />;
}

export function IncidentPhase5Route() {
  return <SafetyIncidentPhase5 />;
}

export function IncidentPhase6Route() {
  return <SafetyIncidentPhase6 />;
}

export function IncidentPhase7Route() {
  return <SafetyIncidentPhase7 />;
}

export function IncidentPhase8Route() {
  return <SafetyIncidentPhase8 />;
}

export function IncidentAuditRoute() {
  return (
    <IncidentOfficeReadRoute
      area="Safety / Incident Audit"
      loader={safetyApi.getIncidentAudit}
      title="Incident Audit Trail"
    />
  );
}

export function IncidentClosureRoute() {
  return <SafetyIncidentPhase9 />;
}

export function IncidentReopenRoute() {
  return <SafetyIncidentReopenWorkspace />;
}

export function IncidentCorrectiveActionsRoute() {
  const { id } = useParams();
  const [actions, setActions] = useState<IncidentCorrectiveAction[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const reload = useMemo(
    () => async () => {
      if (!id) {
        setError("Invalid incident id.");
        setIsLoading(false);
        return;
      }
      setError(null);
      setIsLoading(true);
      try {
        const response = await safetyApi.getCorrectiveActions({ incident_id: id });
        setActions(Array.isArray(response) ? (response as IncidentCorrectiveAction[]) : []);
      } catch (caught) {
        setError(getErrorMessage(caught));
      } finally {
        setIsLoading(false);
      }
    },
    [id],
  );

  useEffect(() => {
    void reload();
  }, [reload]);

  const openCount = actions.filter((action) => action.status !== "CLOSED").length;

  if (isLoading) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 text-sm text-slate-600 shadow-sm">
        Loading corrective actions...
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Incident / Corrective Actions
        </p>
        <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Corrective Actions</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Close linked corrective actions before Phase 8 final closure.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Open actions: <span className="font-semibold text-slate-900">{openCount}</span>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link
            className="inline-flex min-h-11 items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
            to={`/safety/incidents/${id}/phase-8`}
          >
            Back to Phase 8
          </Link>
          <button
            className="inline-flex min-h-11 items-center rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            onClick={() => void reload()}
            type="button"
          >
            Refresh
          </button>
        </div>
      </header>

      {error ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          {error}
        </section>
      ) : null}

      <CorrectiveActionManager actions={actions} reload={reload} />
      <CreateCorrectiveActionForm onCreated={reload} />
    </section>
  );
}

export function IncidentPdfRoute() {
  return (
    <IncidentOfficeReadRoute
      area="Safety / Incident Export"
      loader={safetyApi.getIncidentAudit}
      title="Incident PDF Export"
    >
      {() => (
        <DownloadCard
          buttonLabel="Download incident PDF"
          downloader={safetyApi.downloadIncidentPdf}
          helperText="Requests the generated PDF from the backend. Export permission and vessel scope are enforced server-side."
        />
      )}
    </IncidentOfficeReadRoute>
  );
}

export function IncidentMscMepc3Route() {
  return (
    <IncidentOfficeReadRoute
      area="Safety / Incident Export"
      loader={safetyApi.getIncidentPhase7Preflight}
      title="MSC-MEPC.3 Export"
    >
      {() => (
        <DownloadCard
          buttonLabel="Download MSC-MEPC.3 export"
          downloader={safetyApi.downloadIncidentMscMepc3}
          helperText="DPA-only backend export route for the MSC-MEPC.3/Circ.4 report."
        />
      )}
    </IncidentOfficeReadRoute>
  );
}
