import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
  type ReactNode,
  type RefObject,
} from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { getErrorMessage } from '../../../lib/api/client';
import { mastersApi } from '../../../lib/api/masters';
import {
  safetyApi,
  type SafetyOfficeWorkflowPayload,
} from '../../../lib/api/safety';
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
} from '../../../schemas/safety/incident-phase3';
import type { CrewMember } from '../../../types';
import SafetyEvidenceDeadlineTasks from './evidence-deadline-tasks';
import SafetyEvidenceMatrix from './evidence-matrix';
import SafetyInterviewModule from './interview-module';

export type SafetyIncidentPhase3TabKey =
  | 'people'
  | 'position'
  | 'parts'
  | 'paper'
  | 'electronic'
  | 'matrix'
  | 'interviews';

type EvidenceTabKey = Extract<
  SafetyIncidentPhase3TabKey,
  'people' | 'position' | 'parts' | 'paper' | 'electronic'
>;

interface SafetyEvidenceAttachmentMetadata {
  description: string;
  title: string;
}

type SafetyEvidenceAttachmentRecord = Record<string, unknown>;

interface SafetyIncidentPhase3Props {
  activeTab?: SafetyIncidentPhase3TabKey;
  routeBase?: 'phase-3' | 'phase-4';
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
    key: 'paper',
    label: 'Documents',
    prompt:
      'Add each evidence document with a title, description, and attachment.',
    route: 'paper',
  },
];

const workspaceTabs: Array<{
  key: SafetyIncidentPhase3TabKey;
  label: string;
  route: string;
}> = [
  ...evidenceTabs.map(({ key, label, route }) => ({ key, label, route })),
  { key: 'matrix', label: 'Evidence Check', route: 'evidence-matrix' },
  { key: 'interviews', label: 'Witness Statement', route: 'interviews' },
];

const tabCodeByKey: Record<
  EvidenceTabKey,
  SafetyIncidentPhase3Tab['tab_code']
> = {
  electronic: 'ELECTRONIC',
  paper: 'PAPER',
  parts: 'PARTS',
  people: 'PEOPLE',
  position: 'POSITION',
};

const hiddenStructuredDataKeys = new Set([
  'attachments',
  'cargo_overlay_items',
  'health_fatigue',
  'marine_document_other_enabled',
  'marine_document_other_text',
]);

const defaultState: SafetyIncidentPhase3State = {
  chainOfCustody: [],
  deadlineTasks: [],
  evidenceMatrix: [],
  interviews: [],
  tabs: {
    electronic: createDefaultEvidenceTab('electronic'),
    paper: createDefaultEvidenceTab('paper'),
    parts: createDefaultEvidenceTab('parts'),
    people: createDefaultEvidenceTab('people'),
    position: createDefaultEvidenceTab('position'),
  },
};

function createDefaultEvidenceTab(
  key: EvidenceTabKey
): SafetyIncidentPhase3Tab {
  return {
    entry_count: 0,
    na_justification: null,
    status_chip: '',
    structured_data: {},
    summary: '',
    tab_code: tabCodeByKey[key],
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function normalizeCrewMembers(response: unknown): CrewMember[] {
  const rows = Array.isArray(response)
    ? response
    : response && typeof response === 'object'
      ? (response as { data?: unknown }).data
      : undefined;

  return Array.isArray(rows) ? (rows.filter(Boolean) as CrewMember[]) : [];
}

function formatCrewOption(crew: CrewMember | null | undefined) {
  if (!crew) {
    return '';
  }
  const rank = String(crew.rank_name || '').trim();
  const displayName = String(crew.display_name || '').trim();
  const nameWithoutRank =
    rank && displayName.toLowerCase().startsWith(`${rank.toLowerCase()} - `)
      ? displayName.slice(rank.length + 3).trim()
      : displayName;
  const name = String(
    nameWithoutRank ||
      [crew.first_name, crew.surname].filter(Boolean).join(' ') ||
      crew.crew_id ||
      ''
  ).trim();
  return [rank, name].filter(Boolean).join(' - ');
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () =>
      reject(new Error('Signature image could not be read.'));
    reader.onload = () => resolve(String(reader.result || ''));
    reader.readAsDataURL(file);
  });
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function parseEvidenceTab(
  key: EvidenceTabKey,
  value: unknown
): SafetyIncidentPhase3Tab {
  const parsed = safetyIncidentPhase3TabSchema.safeParse(value);
  return parsed.success ? parsed.data : createDefaultEvidenceTab(key);
}

function parseRows<T>(
  rows: unknown,
  parser: {
    safeParse: (
      row: unknown
    ) => { success: true; data: T } | { success: false };
  }
): T[] {
  return asArray(rows)
    .map((row) => parser.safeParse(row))
    .filter((result) => result.success)
    .map((result) => result.data);
}

function buildWorkspaceState(
  evidencePayload: unknown,
  chainPayload: unknown,
  matrixPayload: unknown,
  interviewPayload: unknown
): SafetyIncidentPhase3State {
  const payload = asRecord(evidencePayload);

  return {
    chainOfCustody: parseRows(
      asArray(chainPayload).length > 0
        ? chainPayload
        : payload.chain_of_custody,
      safetyChainOfCustodyRowSchema
    ),
    deadlineTasks: parseRows(
      payload.deadline_tasks,
      safetyEvidenceDeadlineTaskSchema
    ),
    evidenceMatrix: parseRows(
      asArray(matrixPayload).length > 0
        ? matrixPayload
        : payload.evidence_matrix,
      safetyEvidenceMatrixRowSchema
    ),
    interviews: parseRows(
      asArray(interviewPayload).length > 0
        ? interviewPayload
        : (payload.interviews ?? payload.witness_interviews),
      safetyWitnessInterviewSchema
    ),
    tabs: {
      electronic: parseEvidenceTab('electronic', payload.electronic),
      paper: parseEvidenceTab('paper', payload.paper),
      parts: parseEvidenceTab('parts', payload.parts),
      people: parseEvidenceTab('people', payload.people),
      position: parseEvidenceTab('position', payload.position),
    },
  };
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') {
    return 'Not recorded';
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (Array.isArray(value)) {
    return `${value.length} item${value.length === 1 ? '' : 's'}`;
  }
  if (typeof value === 'object') {
    return `${Object.keys(value).length} field${Object.keys(value).length === 1 ? '' : 's'}`;
  }
  return String(value);
}

function readableKey(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatFileSize(value: unknown): string {
  const bytes = Number(value);
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return '';
  }
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatUploadedAt(value: unknown): string {
  if (!value) {
    return '';
  }
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return date.toLocaleString();
}

function getEvidenceAttachments(
  tab: SafetyIncidentPhase3Tab
): Array<Record<string, unknown>> {
  return asArray(asRecord(tab.structured_data).attachments)
    .map((item) => asRecord(item))
    .filter(
      (item) => item.file_name || item.original_name || item.attachment_path
    );
}

function hasHandledEvidenceSection(tab: SafetyIncidentPhase3Tab): boolean {
  return Boolean(
    (tab.summary || '').trim() ||
      (tab.na_justification || '').trim() ||
      getEvidenceAttachments(tab).length > 0
  );
}

function getTabHref(id: string | undefined, routeBase: string, route: string) {
  return `/safety/incidents/${id ?? ''}/${routeBase}/${route}`;
}

function SafetySimpleDisclosure({
  children,
  count,
  defaultOpen = false,
  title,
}: {
  children: ReactNode;
  count?: number;
  defaultOpen?: boolean;
  title: string;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <details
      className={`overflow-hidden rounded-3xl border bg-white shadow-sm transition ${
        isOpen
          ? 'border-slate-300 shadow-md'
          : 'border-slate-200 hover:border-slate-300 hover:shadow-md'
      }`}
      onToggle={(event) => setIsOpen(event.currentTarget.open)}
      open={isOpen}
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4 text-sm font-semibold text-slate-900">
        <span className="flex min-w-0 items-center gap-3">
          <span
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-base leading-none transition ${
              isOpen ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'
            }`}
            aria-hidden="true"
          >
            {isOpen ? '-' : '+'}
          </span>
          <span className="truncate text-base">{title}</span>
        </span>
        <span className="flex shrink-0 items-center gap-2">
          {typeof count === 'number' ? (
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">
              {count}
            </span>
          ) : null}
          <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">
            {isOpen ? 'Hide' : 'Open'}
          </span>
        </span>
      </summary>
      <div className="border-t border-slate-100 bg-slate-50/60 p-5">
        {children}
      </div>
    </details>
  );
}

function SafetyEvidenceTypePicker({
  activeTab,
  id,
  routeBase,
}: {
  activeTab: SafetyIncidentPhase3TabKey;
  id?: string;
  routeBase: string;
}) {
  if (evidenceTabs.length <= 1) {
    return null;
  }

  return (
    <nav
      aria-label="Evidence type"
      className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5"
    >
      {evidenceTabs.map((tab) => {
        const isActive = activeTab === tab.key;
        return (
          <Link
            className={`rounded-2xl border p-4 text-left transition ${
              isActive
                ? 'border-slate-900 bg-slate-900 text-white shadow-sm'
                : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
            }`}
            key={tab.key}
            to={getTabHref(id, routeBase, tab.route)}
          >
            <span
              className={`block text-sm font-semibold ${isActive ? 'text-white' : 'text-slate-900'}`}
            >
              {tab.label}
            </span>
            <span
              className={`mt-2 block text-xs leading-5 ${isActive ? 'text-slate-200' : 'text-slate-500'}`}
            >
              {tab.prompt}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}

function SafetyLoadingState() {
  return (
    <section className="space-y-4">
      {Array.from({ length: 4 }).map((_, index) => (
        <div
          key={index}
          className="h-24 animate-pulse rounded-3xl bg-slate-100"
        />
      ))}
    </section>
  );
}

function SafetyTabSummaryCard({ tab }: { tab: SafetyIncidentPhase3Tab }) {
  if (!hasHandledEvidenceSection(tab)) {
    return null;
  }

  return (
    <article className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            {tab.tab_code}
          </p>
          <h2 className="mt-1 text-base font-semibold text-slate-900">
            Saved note
          </h2>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium uppercase text-slate-700">
          {tab.status_chip || `${tab.entry_count} entries`}
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-700">
        {tab.summary || 'No investigation note captured yet.'}
      </p>
      {tab.na_justification ? (
        <p className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {tab.na_justification}
        </p>
      ) : null}
    </article>
  );
}

function SafetyStructuredDataPanel({
  data,
}: {
  data: Record<string, unknown>;
}) {
  const entries = Object.entries(data).filter(
    ([key]) => !hiddenStructuredDataKeys.has(key)
  );

  if (entries.length === 0) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
      <h2 className="text-base font-semibold text-slate-900">Saved details</h2>
      <dl className="mt-3 grid gap-3 md:grid-cols-2">
        {entries.map(([key, value]) => (
          <div
            key={key}
            className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2"
          >
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              {readableKey(key)}
            </dt>
            <dd className="mt-1 text-sm text-slate-800">
              {formatValue(value)}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function SafetyEvidenceAttachmentList({
  disabled,
  incidentId,
  onEditAttachment,
  onDeleteAttachment,
  tab,
}: {
  disabled: boolean;
  incidentId?: string;
  onEditAttachment?: (attachment: SafetyEvidenceAttachmentRecord) => void;
  onDeleteAttachment: (attachmentPath: string) => Promise<void>;
  tab: SafetyIncidentPhase3Tab;
}) {
  const attachments = getEvidenceAttachments(tab);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [deletingPath, setDeletingPath] = useState<string | null>(null);

  async function openAttachmentPreview(attachment: Record<string, unknown>) {
    const attachmentPath = String(attachment.attachment_path || '').trim();
    if (!incidentId || !attachmentPath) {
      setPreviewError('Attachment preview is not available.');
      return;
    }

    const previewWindow = window.open('', '_blank');
    try {
      setPreviewError(null);
      const blob = await safetyApi.getIncidentPhase3AttachmentBlob(
        incidentId,
        attachmentPath
      );
      const previewUrl = URL.createObjectURL(blob);
      if (previewWindow) {
        previewWindow.location.href = previewUrl;
      } else {
        window.open(previewUrl, '_blank');
      }
      window.setTimeout(() => URL.revokeObjectURL(previewUrl), 60_000);
    } catch (caught) {
      previewWindow?.close();
      setPreviewError(getErrorMessage(caught));
    }
  }

  async function deleteAttachment(attachment: Record<string, unknown>) {
    const attachmentPath = String(attachment.attachment_path || '').trim();
    if (!attachmentPath) {
      setPreviewError(
        'Attachment cannot be removed because its path is missing.'
      );
      return;
    }
    setDeletingPath(attachmentPath);
    try {
      setPreviewError(null);
      await onDeleteAttachment(attachmentPath);
    } catch (caught) {
      setPreviewError(getErrorMessage(caught));
    } finally {
      setDeletingPath(null);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-slate-900">
          Saved documents
        </h2>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium uppercase text-slate-700">
          {attachments.length}
        </span>
      </div>
      {attachments.length > 0 ? (
        <div className="mt-4 grid gap-3">
          {attachments.map((attachment, index) => {
            const name = String(
              attachment.original_name ||
                attachment.file_name ||
                attachment.attachment_path ||
                `Attachment ${index + 1}`
            );
            const title = String(attachment.title || name);
            const description = String(attachment.description || '').trim();
            const attachmentPath = String(
              attachment.attachment_path || ''
            ).trim();
            const previewHref =
              incidentId && attachmentPath
                ? safetyApi.getIncidentPhase3AttachmentPreviewUrl(
                    incidentId,
                    attachmentPath
                  )
                : '#';
            const fileSize = formatFileSize(attachment.byte_size);
            const uploadedAt = formatUploadedAt(attachment.uploaded_at);
            return (
              <article
                className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3"
                key={String(
                  attachment.attachment_path || attachment.file_name || index
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <a
                    className="font-medium text-blue-700 underline-offset-4 hover:text-blue-900 hover:underline"
                    href={previewHref}
                    onClick={(event) => {
                      event.preventDefault();
                      void openAttachmentPreview(attachment);
                    }}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {title}
                  </a>
                  <div className="flex shrink-0 items-center gap-2">
                    {onEditAttachment ? (
                      <button
                        aria-label={`Edit ${title}`}
                        className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                        disabled={disabled}
                        onClick={() => onEditAttachment(attachment)}
                        type="button"
                      >
                        Edit
                      </button>
                    ) : null}
                    <button
                      aria-label={`Remove ${title}`}
                      className="flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-white text-base font-semibold leading-none text-slate-500 hover:border-rose-200 hover:bg-rose-50 hover:text-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={disabled || deletingPath === attachmentPath}
                      onClick={() => void deleteAttachment(attachment)}
                      title="Remove attachment"
                      type="button"
                    >
                      x
                    </button>
                  </div>
                </div>
                {description ? (
                  <p className="mt-2 text-sm leading-6 text-slate-700">
                    {description}
                  </p>
                ) : null}
                <div className="mt-1 flex flex-wrap gap-3 text-xs font-medium text-slate-500">
                  {fileSize ? <span>{fileSize}</span> : null}
                  {uploadedAt ? <span>{uploadedAt}</span> : null}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-500">No documents added yet.</p>
      )}
      {previewError ? (
        <p className="mt-3 text-sm font-medium text-rose-700">{previewError}</p>
      ) : null}
    </section>
  );
}

function SafetyEvidenceAttachmentUpload({
  disabled,
  editingAttachment,
  onCancelEdit,
  onUpload,
  onUpdate,
  tabKey,
}: {
  disabled: boolean;
  editingAttachment?: SafetyEvidenceAttachmentRecord | null;
  onCancelEdit?: () => void;
  onUpload: (
    tabKey: EvidenceTabKey,
    file: File,
    metadata: SafetyEvidenceAttachmentMetadata
  ) => Promise<void>;
  onUpdate: (
    tabKey: EvidenceTabKey,
    attachmentPath: string,
    metadata: SafetyEvidenceAttachmentMetadata
  ) => Promise<void>;
  tabKey: EvidenceTabKey;
}) {
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const editingAttachmentPath = String(
    editingAttachment?.attachment_path || ''
  ).trim();

  useEffect(() => {
    if (!editingAttachment) {
      return;
    }
    setDescription(String(editingAttachment.description || ''));
    setError(null);
    setFileInputKey((current) => current + 1);
    setSelectedFile(null);
    setTitle(
      String(
        editingAttachment.title ||
          editingAttachment.original_name ||
          editingAttachment.file_name ||
          ''
      )
    );
  }, [editingAttachment]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    setSelectedFile(file ?? null);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const cleanedTitle = title.trim();
    const cleanedDescription = description.trim();
    if (!cleanedTitle) {
      setError('Enter a title before adding the attachment.');
      return;
    }
    if (editingAttachmentPath) {
      setIsUploading(true);
      try {
        await onUpdate(tabKey, editingAttachmentPath, {
          description: cleanedDescription,
          title: cleanedTitle,
        });
        setDescription('');
        setSelectedFile(null);
        setTitle('');
        setFileInputKey((current) => current + 1);
        onCancelEdit?.();
      } catch (caught) {
        setError(getErrorMessage(caught));
      } finally {
        setIsUploading(false);
      }
      return;
    }
    if (!selectedFile) {
      setError('Select an attachment before adding it.');
      return;
    }
    setIsUploading(true);
    try {
      await onUpload(tabKey, selectedFile, {
        description: cleanedDescription,
        title: cleanedTitle,
      });
      setDescription('');
      setSelectedFile(null);
      setTitle('');
      setFileInputKey((current) => current + 1);
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form
      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={handleSubmit}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <h2 className="text-lg font-semibold text-slate-900">
          {editingAttachmentPath ? 'Edit document' : 'New document'}
        </h2>
        {editingAttachmentPath ? (
          <button
            className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
            onClick={() => {
              setDescription('');
              setError(null);
              setFileInputKey((current) => current + 1);
              setSelectedFile(null);
              setTitle('');
              onCancelEdit?.();
            }}
            type="button"
          >
            Cancel edit
          </button>
        ) : null}
      </div>
      <div className="mt-5 grid gap-4">
        <label className="block text-sm font-medium text-slate-700">
          Title
          <input
            className="mt-2 min-h-11 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
            disabled={disabled || isUploading}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Engine log extract"
            value={title}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Description
          <textarea
            className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 px-4 py-3 text-sm text-slate-900"
            disabled={disabled || isUploading}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Short note"
            value={description}
          />
        </label>
        {editingAttachmentPath ? (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
            Attachment file stays unchanged.
          </div>
        ) : (
          <label className="block rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm font-medium text-slate-700">
            Attachment
            <span className="mt-1 block text-xs font-normal leading-5 text-slate-500">
              JPG, JPEG, PNG, or PDF. Maximum 3MB.
            </span>
            <input
              accept="image/jpeg,image/jpg,image/png,application/pdf,.pdf"
              aria-label="Attachment"
              className="mt-3 w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 file:mr-4 file:rounded-full file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
              disabled={disabled || isUploading}
              key={fileInputKey}
              onChange={handleFileChange}
              type="file"
            />
          </label>
        )}
      </div>
      {isUploading ? (
        <span className="mt-3 block text-sm font-medium text-slate-600">
          {editingAttachmentPath
            ? 'Updating document...'
            : 'Uploading attachment...'}
        </span>
      ) : null}
      {error ? (
        <span className="mt-3 block text-sm font-medium text-rose-700">
          {error}
        </span>
      ) : null}
      <button
        className="mt-5 inline-flex min-h-11 items-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        disabled={disabled || isUploading}
        type="submit"
      >
        {isUploading
          ? 'Saving...'
          : editingAttachmentPath
            ? 'Update document'
            : 'Add document'}
      </button>
    </form>
  );
}

function SafetyChainOfCustodyCreateForm({
  disabled,
  onCreate,
}: {
  disabled: boolean;
  onCreate: (payload: SafetyOfficeWorkflowPayload) => Promise<void>;
}) {
  const [description, setDescription] = useState('');
  const [collectorName, setCollectorName] = useState('');
  const [storageLocation, setStorageLocation] = useState('');
  const [witnessSignature, setWitnessSignature] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const cleanedDescription = description.trim();
    const cleanedCollectorName = collectorName.trim();
    const cleanedStorageLocation = storageLocation.trim();
    const cleanedWitnessSignature = witnessSignature.trim();
    if (
      !cleanedDescription ||
      !cleanedCollectorName ||
      !cleanedStorageLocation ||
      !cleanedWitnessSignature
    ) {
      setError(
        'Please fill Description, Collector, Storage location and Witness signature before adding custody item.'
      );
      return;
    }
    setIsSubmitting(true);
    try {
      await onCreate({
        collection_timestamp: new Date().toISOString(),
        collector_name: cleanedCollectorName,
        collector_signature: cleanedCollectorName,
        current_holder: cleanedCollectorName,
        description: cleanedDescription,
        storage_location: cleanedStorageLocation,
        witness_signature: cleanedWitnessSignature,
      });
      setDescription('');
      setCollectorName('');
      setStorageLocation('');
      setWitnessSignature('');
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  const canSubmit = Boolean(
    description.trim() &&
      collectorName.trim() &&
      storageLocation.trim() &&
      witnessSignature.trim()
  );

  return (
    <form
      className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={handleSubmit}
    >
      <h2 className="text-xl font-semibold text-slate-900">Add Custody Item</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700">
          Description
          <input
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
            onChange={(event) => setDescription(event.target.value)}
            required
            value={description}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Collector
          <input
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
            onChange={(event) => setCollectorName(event.target.value)}
            required
            value={collectorName}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Storage location
          <input
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
            onChange={(event) => setStorageLocation(event.target.value)}
            required
            value={storageLocation}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Witness signature
          <input
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
            onChange={(event) => setWitnessSignature(event.target.value)}
            required
            value={witnessSignature}
          />
        </label>
      </div>
      {error ? (
        <p className="mt-3 text-sm font-medium text-rose-700">{error}</p>
      ) : null}
      <button
        className="mt-4 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:bg-slate-400"
        disabled={disabled || isSubmitting || !canSubmit}
        type="submit"
      >
        {isSubmitting ? 'Adding...' : 'Add custody item'}
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
  const [finding, setFinding] = useState('');
  const [proEvidence, setProEvidence] = useState('');
  const [conEvidence, setConEvidence] = useState('');
  const [sourceLabel, setSourceLabel] = useState('');
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
      setFinding('');
      setProEvidence('');
      setConEvidence('');
      setSourceLabel('');
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={handleSubmit}
    >
      <h2 className="text-xl font-semibold text-slate-900">Add Matrix Row</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm font-medium text-slate-700">
          Finding
          <input
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
            onChange={(event) => setFinding(event.target.value)}
            value={finding}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Source
          <input
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
            onChange={(event) => setSourceLabel(event.target.value)}
            value={sourceLabel}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Pro evidence
          <textarea
            className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3"
            onChange={(event) => setProEvidence(event.target.value)}
            value={proEvidence}
          />
        </label>
        <label className="block text-sm font-medium text-slate-700">
          Con evidence
          <textarea
            className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3"
            onChange={(event) => setConEvidence(event.target.value)}
            value={conEvidence}
          />
        </label>
      </div>
      {error ? (
        <p className="mt-3 text-sm font-medium text-rose-700">{error}</p>
      ) : null}
      <button
        className="mt-4 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:bg-slate-400"
        disabled={disabled || isSubmitting}
        type="submit"
      >
        {isSubmitting ? 'Adding...' : 'Add matrix row'}
      </button>
    </form>
  );
}

function SafetyInterviewCreateForm({
  disabled,
  editingInterview,
  onCancelEdit,
  onCreate,
  onUpdate,
  vesselId,
}: {
  disabled: boolean;
  editingInterview?: SafetyWitnessInterview | null;
  onCancelEdit?: () => void;
  onCreate: (payload: SafetyOfficeWorkflowPayload) => Promise<void>;
  onUpdate: (
    interviewId: string,
    payload: SafetyOfficeWorkflowPayload
  ) => Promise<void>;
  vesselId?: string | null;
}) {
  const [crewMembers, setCrewMembers] = useState<CrewMember[]>([]);
  const [crewStatus, setCrewStatus] = useState<'idle' | 'loading' | 'error'>(
    'idle'
  );
  const [witnessSelection, setWitnessSelection] = useState('');
  const [otherWitnessName, setOtherWitnessName] = useState('');
  const [conclusionNotes, setConclusionNotes] = useState('');
  const [signatureFileName, setSignatureFileName] = useState('');
  const [witnessSignature, setWitnessSignature] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function resetForm() {
    setWitnessSelection('');
    setOtherWitnessName('');
    setConclusionNotes('');
    setWitnessSignature(null);
    setSignatureFileName('');
  }

  useEffect(() => {
    if (!vesselId) {
      setCrewMembers([]);
      setCrewStatus('idle');
      return;
    }

    let cancelled = false;
    setCrewStatus('loading');
    mastersApi
      .getVesselCrew(vesselId)
      .then((rows) => {
        if (cancelled) {
          return;
        }
        setCrewMembers(normalizeCrewMembers(rows));
        setCrewStatus('idle');
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setCrewMembers([]);
        setCrewStatus('error');
      });

    return () => {
      cancelled = true;
    };
  }, [vesselId]);

  useEffect(() => {
    if (!editingInterview) {
      return;
    }
    const witnessName = editingInterview.witness_name ?? '';
    const matchingCrew = crewMembers
      .map(formatCrewOption)
      .find((label) => label === witnessName);
    setConclusionNotes(editingInterview.conclusion_notes ?? '');
    setError(null);
    setWitnessSignature(editingInterview.witness_signature ?? null);
    setSignatureFileName(
      editingInterview.witness_signature ? 'Existing witness statement' : ''
    );
    if (matchingCrew) {
      setOtherWitnessName('');
      setWitnessSelection(matchingCrew);
    } else {
      setOtherWitnessName(witnessName);
      setWitnessSelection('OTHER');
    }
  }, [crewMembers, editingInterview]);

  const witnessName =
    witnessSelection === 'OTHER' ? otherWitnessName : witnessSelection;
  const canSubmit = Boolean(witnessName.trim() && conclusionNotes.trim());

  async function handleSignatureChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    setError(null);
    if (!file) {
      setWitnessSignature(null);
      setSignatureFileName('');
      return;
    }
    try {
      setWitnessSignature(await readFileAsDataUrl(file));
      setSignatureFileName(file.name);
    } catch (caught) {
      setWitnessSignature(null);
      setSignatureFileName('');
      setError(getErrorMessage(caught));
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const payload = {
        conclusion_notes: conclusionNotes,
        copy_to_witness_recorded: false,
        interview_type: 'INFORMAL',
        introduction_notes: '',
        make_acquaintance_notes: '',
        meeting_notes: '',
        question_rows: [],
        read_back_confirmed: false,
        reason_formal_impossible:
          'Simplified witness statement recorded from Phase 4.',
        witness_signature: witnessSignature,
        witness_name: witnessName,
      };
      if (editingInterview?.id) {
        await onUpdate(editingInterview.id, payload);
        onCancelEdit?.();
      } else {
        await onCreate(payload);
      }
      resetForm();
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"
      onSubmit={handleSubmit}
    >
      <div>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              {editingInterview?.id
                ? 'Edit witness statement'
                : 'New witness statement'}
            </p>
            <h2 className="mt-1 text-xl font-semibold text-slate-900">
              {editingInterview?.id
                ? 'Edit Witness Statement'
                : 'Add Witness Statement'}
            </h2>
          </div>
          {editingInterview?.id ? (
            <button
              className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700"
              onClick={() => {
                resetForm();
                onCancelEdit?.();
              }}
              type="button"
            >
              Cancel edit
            </button>
          ) : null}
        </div>
      </div>
      <div className="mt-5 grid gap-4">
        <label className="block text-sm font-medium text-slate-700">
          Witness name
          <select
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
            disabled={disabled || crewStatus === 'loading'}
            onChange={(event) => {
              setWitnessSelection(event.target.value);
              if (event.target.value !== 'OTHER') {
                setOtherWitnessName('');
              }
            }}
            value={witnessSelection}
          >
            <option value="">
              {crewStatus === 'loading' ? 'Loading crew...' : 'Select witness'}
            </option>
            {crewMembers.map((crew) => {
              const label = formatCrewOption(crew);
              return (
                <option key={crew.crew_id || crew.id || label} value={label}>
                  {label}
                </option>
              );
            })}
            <option value="OTHER">Other</option>
          </select>
        </label>
        {crewStatus === 'error' ? (
          <p className="text-sm text-amber-700">
            Crew list could not be loaded. Select Other to type the witness
            name.
          </p>
        ) : null}
        {witnessSelection === 'OTHER' ? (
          <label className="block text-sm font-medium text-slate-700">
            Specify witness name
            <input
              className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
              onChange={(event) => setOtherWitnessName(event.target.value)}
              value={otherWitnessName}
            />
          </label>
        ) : null}
        <label className="block text-sm font-medium text-slate-700">
          Upload witness statement
          <input
            accept="image/*,.pdf"
            className="mt-2 w-full rounded-2xl border border-slate-300 px-3 py-2"
            onChange={handleSignatureChange}
            type="file"
          />
        </label>
        {signatureFileName ? (
          <p className="text-sm text-slate-600">
            Witness statement selected: {signatureFileName}
          </p>
        ) : null}
        <label className="block text-sm font-medium text-slate-700">
          Remark
          <textarea
            className="mt-2 min-h-24 w-full rounded-2xl border border-slate-300 p-3"
            onChange={(event) => setConclusionNotes(event.target.value)}
            value={conclusionNotes}
          />
        </label>
      </div>
      {error ? (
        <p className="mt-3 text-sm font-medium text-rose-700">{error}</p>
      ) : null}
      <button
        className="mt-4 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:bg-slate-400"
        disabled={disabled || isSubmitting || !canSubmit}
        type="submit"
      >
        {isSubmitting
          ? 'Saving...'
          : editingInterview?.id
            ? 'Update witness statement'
            : 'Save witness statement'}
      </button>
    </form>
  );
}

function SafetyEvidenceSourcePanel({
  disabled,
  incidentId,
  onAttachmentUpload,
  onAttachmentUpdate,
  onDeleteAttachment,
  savedContentRef,
  tabKey,
  tab,
}: {
  disabled: boolean;
  incidentId?: string;
  onAttachmentUpload: (
    tabKey: EvidenceTabKey,
    file: File,
    metadata: SafetyEvidenceAttachmentMetadata
  ) => Promise<void>;
  onAttachmentUpdate: (
    tabKey: EvidenceTabKey,
    attachmentPath: string,
    metadata: SafetyEvidenceAttachmentMetadata
  ) => Promise<void>;
  onDeleteAttachment: (attachmentPath: string) => Promise<void>;
  savedContentRef?: RefObject<HTMLDivElement>;
  tabKey: EvidenceTabKey;
  tab: SafetyIncidentPhase3Tab;
}) {
  const structuredData = asRecord(tab.structured_data);
  const hasLegacyStructuredData = Object.keys(structuredData).some(
    (key) => !hiddenStructuredDataKeys.has(key)
  );
  const hasLegacyDetails = Boolean(
    tab.summary?.trim() || tab.na_justification || hasLegacyStructuredData
  );
  const [editingAttachment, setEditingAttachment] =
    useState<SafetyEvidenceAttachmentRecord | null>(null);
  const documentFormRef = useRef<HTMLDivElement>(null);

  function startEditingAttachment(attachment: SafetyEvidenceAttachmentRecord) {
    setEditingAttachment(attachment);
    window.setTimeout(() => {
      documentFormRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 100);
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="space-y-4">
          <div className="scroll-mt-24" ref={documentFormRef}>
            <SafetyEvidenceAttachmentUpload
              disabled={disabled}
              editingAttachment={editingAttachment}
              onCancelEdit={() => setEditingAttachment(null)}
              onUpdate={async (nextTabKey, attachmentPath, metadata) => {
                await onAttachmentUpdate(nextTabKey, attachmentPath, metadata);
                setEditingAttachment(null);
              }}
              onUpload={onAttachmentUpload}
              tabKey={tabKey}
            />
          </div>
          {hasLegacyDetails ? (
            <SafetySimpleDisclosure title="Saved notes">
              <div className="space-y-4">
                <SafetyTabSummaryCard tab={tab} />
                <SafetyStructuredDataPanel data={structuredData} />
              </div>
            </SafetySimpleDisclosure>
          ) : null}
        </div>
        <aside className="space-y-4 xl:sticky xl:top-4 xl:self-start">
          <div
            className="scroll-mt-24 outline-none"
            ref={savedContentRef}
            tabIndex={-1}
          >
            <SafetyEvidenceAttachmentList
              disabled={disabled}
              incidentId={incidentId}
              onEditAttachment={startEditingAttachment}
              onDeleteAttachment={onDeleteAttachment}
              tab={tab}
            />
          </div>
        </aside>
      </div>
    </div>
  );
}

export function SafetyIncidentPhase3({
  activeTab = 'paper',
  routeBase = 'phase-3',
}: SafetyIncidentPhase3Props) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [workspace, setWorkspace] =
    useState<SafetyIncidentPhase3State>(defaultState);
  const [error, setError] = useState<string | null>(null);
  const [phaseAdvanceError, setPhaseAdvanceError] = useState<string | null>(
    null
  );
  const [loadWarnings, setLoadWarnings] = useState<string[]>([]);
  const [incidentVesselId, setIncidentVesselId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMutating, setIsMutating] = useState(false);
  const [saveNotice, setSaveNotice] = useState<string | null>(null);
  const checklistRef = useRef<HTMLDivElement>(null);
  const savedDocumentsRef = useRef<HTMLDivElement>(null);
  const savedWitnessNotesRef = useRef<HTMLDivElement>(null);
  const witnessFormRef = useRef<HTMLDivElement>(null);
  const [editingInterview, setEditingInterview] =
    useState<SafetyWitnessInterview | null>(null);

  const evidenceCheckEnabled = routeBase !== 'phase-4';
  const availableWorkspaceTabs = useMemo(
    () =>
      workspaceTabs.filter(
        (tab) => evidenceCheckEnabled || tab.key !== 'matrix'
      ),
    [evidenceCheckEnabled]
  );
  const currentTab = availableWorkspaceTabs.some((tab) => tab.key === activeTab)
    ? activeTab
    : 'paper';
  const isAdvancedTab = currentTab === 'matrix' || currentTab === 'interviews';

  const phase4Blockers = useMemo(() => {
    return [];
  }, []);

  const reload = useCallback(async () => {
    if (!id) {
      setError('Invalid incident id.');
      setIsLoading(false);
      return;
    }

    setError(null);
    setIsLoading(true);
    const [phase1, evidence, chain, matrix, interviews] =
      await Promise.allSettled([
        safetyApi.getIncidentPhase1(id),
        safetyApi.getIncidentPhase3Evidence(id),
        safetyApi.getIncidentPhase3ChainOfCustody(id),
        evidenceCheckEnabled
          ? safetyApi.getIncidentPhase3EvidenceMatrix(id)
          : Promise.resolve([]),
        safetyApi.getIncidentPhase3Interviews(id),
      ]);

    if (evidence.status === 'rejected') {
      const message = getErrorMessage(evidence.reason);
      setError(message);
      setIsLoading(false);
      return;
    }

    const warnings = [
      phase1.status === 'rejected'
        ? 'Incident vessel could not be loaded for witness selection.'
        : null,
      chain.status === 'rejected'
        ? 'Chain of custody could not be refreshed.'
        : null,
      evidenceCheckEnabled && matrix.status === 'rejected'
        ? 'Evidence matrix could not be refreshed.'
        : null,
      interviews.status === 'rejected'
        ? 'Interviews could not be refreshed.'
        : null,
    ].filter(Boolean) as string[];

    setIncidentVesselId(
      phase1.status === 'fulfilled' && phase1.value.vessel_id
        ? String(phase1.value.vessel_id)
        : null
    );
    setWorkspace(
      buildWorkspaceState(
        evidence.value,
        chain.status === 'fulfilled' ? chain.value : undefined,
        matrix.status === 'fulfilled' ? matrix.value : undefined,
        interviews.status === 'fulfilled' ? interviews.value : undefined
      )
    );
    setLoadWarnings(warnings);
    setIsLoading(false);
  }, [evidenceCheckEnabled, id, navigate]);

  useEffect(() => {
    void reload();
  }, [reload]);

  function showSaveNotice(
    message: string,
    targetRef?: RefObject<HTMLDivElement>
  ) {
    setSaveNotice(message);
    window.setTimeout(() => {
      const target = targetRef?.current;
      if (!target) {
        return;
      }
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      target.focus({ preventScroll: true });
    }, 0);
  }

  async function uploadEvidenceAttachment(
    tabKey: EvidenceTabKey,
    file: File,
    metadata: SafetyEvidenceAttachmentMetadata
  ) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      const response = await safetyApi.uploadIncidentPhase3Attachment(
        id,
        tabKey,
        file,
        metadata
      );
      setWorkspace(
        buildWorkspaceState(
          response.workspace,
          workspace.chainOfCustody,
          workspace.evidenceMatrix,
          workspace.interviews
        )
      );
      showSaveNotice(
        'Document saved. Review it under Saved documents.',
        savedDocumentsRef
      );
    } finally {
      setIsMutating(false);
    }
  }

  async function updateEvidenceAttachmentMetadata(
    tabKey: EvidenceTabKey,
    attachmentPath: string,
    metadata: SafetyEvidenceAttachmentMetadata
  ) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      const response = await safetyApi.updateIncidentPhase3AttachmentMetadata(
        id,
        attachmentPath,
        metadata
      );
      setWorkspace(
        buildWorkspaceState(
          response.workspace,
          workspace.chainOfCustody,
          workspace.evidenceMatrix,
          workspace.interviews
        )
      );
      showSaveNotice(
        'Document updated. Review it under Saved documents.',
        savedDocumentsRef
      );
    } finally {
      setIsMutating(false);
    }
  }

  async function deleteEvidenceAttachment(attachmentPath: string) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      const response = await safetyApi.deleteIncidentPhase3Attachment(
        id,
        attachmentPath
      );
      setWorkspace(
        buildWorkspaceState(
          response.workspace,
          workspace.chainOfCustody,
          workspace.evidenceMatrix,
          workspace.interviews
        )
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
      showSaveNotice(
        'Witness statement saved. Review it under Saved Witness Statements.',
        savedWitnessNotesRef
      );
    } finally {
      setIsMutating(false);
    }
  }

  async function updateInterview(
    interviewId: string,
    payload: SafetyOfficeWorkflowPayload
  ) {
    if (!id) {
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.updateIncidentPhase3Interview(id, interviewId, payload);
      setEditingInterview(null);
      await reload();
      showSaveNotice(
        'Witness statement updated. Review it under Saved Witness Statements.',
        savedWitnessNotesRef
      );
    } finally {
      setIsMutating(false);
    }
  }

  function startEditingInterview(interview: SafetyWitnessInterview) {
    setEditingInterview(interview);
    window.setTimeout(() => {
      witnessFormRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 100);
  }

  async function completeDeadlineTask(
    task: SafetyEvidenceDeadlineTask,
    justification: string
  ) {
    if (!id || !task.id) {
      return;
    }
    setIsMutating(true);
    try {
      await safetyApi.updateIncidentPhase3DeadlineTask(id, task.id, {
        justification: justification.trim() || null,
        status: 'COMPLETED',
      });
      await reload();
      showSaveNotice('Checklist saved.', checklistRef);
    } finally {
      setIsMutating(false);
    }
  }

  async function createFactsFromInvestigationNotes() {
    if (!id) {
      return;
    }
    const hasHandledEvidence = evidenceTabs.some((tabConfig) =>
      hasHandledEvidenceSection(workspace.tabs[tabConfig.key])
    );
    const existingFacts = await safetyApi.getIncidentPhase4Facts(id);
    const existingSourceIds = new Set(
      existingFacts.map((fact) => String(fact.source_evidence_id))
    );

    const factDrafts = evidenceTabs
      .map((tabConfig) => {
        const tab = workspace.tabs[tabConfig.key];
        const factText = (tab.summary || '').trim();
        return tab.id && factText && !existingSourceIds.has(String(tab.id))
          ? {
              confidence: 'MEDIUM',
              fact_text: factText,
              source_evidence_id: tab.id,
            }
          : null;
      })
      .filter(
        (
          draft
        ): draft is {
          confidence: string;
          fact_text: string;
          source_evidence_id: string;
        } => Boolean(draft)
      );

    if (factDrafts.length === 0) {
      if (hasHandledEvidence) {
        return;
      }
      throw new Error(
        'Please add evidence, upload an attachment, or enter N/A justification in at least one evidence section.'
      );
    }

    for (const draft of factDrafts) {
      await safetyApi.createIncidentPhase4Fact(id, draft);
    }
  }

  async function continueToActions() {
    if (!id) {
      return;
    }
    if (phase4Blockers.length > 0) {
      setPhaseAdvanceError(
        `Before you continue, ${phase4Blockers.join(' and ')}.`
      );
      return;
    }
    setPhaseAdvanceError(null);
    setIsMutating(true);
    try {
      await createFactsFromInvestigationNotes();
      let alreadyAtNextActions = false;
      try {
        await safetyApi.transitionIncident(id, { target_phase: 5 });
      } catch (caught) {
        const message = getErrorMessage(caught);
        if (message.includes('Phase 6 to Phase 5')) {
          alreadyAtNextActions = true;
        } else if (!message.includes('Phase 5 to Phase 5')) {
          throw caught;
        }
      }
      if (!alreadyAtNextActions) {
        await safetyApi.transitionIncident(id, { target_phase: 6 });
      }
      navigate(`/safety/incidents/${id}/phase-3`);
    } catch (caught) {
      setPhaseAdvanceError(getErrorMessage(caught));
    } finally {
      setIsMutating(false);
    }
  }

  function renderActiveTab() {
    if (currentTab === 'matrix' && evidenceCheckEnabled) {
      return (
        <div className="space-y-5">
          <SafetyEvidenceMatrix rows={workspace.evidenceMatrix} />
          <SafetyEvidenceMatrixCreateForm
            disabled={isMutating}
            onCreate={createMatrixRow}
          />
        </div>
      );
    }
    if (currentTab === 'interviews') {
      return (
        <div className="space-y-5">
          <div
            className="scroll-mt-24 outline-none"
            ref={savedWitnessNotesRef}
            tabIndex={-1}
          >
            <SafetyInterviewModule
              interviews={workspace.interviews}
              onEditInterview={startEditingInterview}
            />
          </div>
          <div className="scroll-mt-24" ref={witnessFormRef}>
            <SafetyInterviewCreateForm
              disabled={isMutating}
              editingInterview={editingInterview}
              onCancelEdit={() => setEditingInterview(null)}
              onCreate={createInterview}
              onUpdate={updateInterview}
              vesselId={incidentVesselId}
            />
          </div>
        </div>
      );
    }

    return (
      <SafetyEvidenceSourcePanel
        disabled={isMutating}
        incidentId={id}
        onAttachmentUpload={uploadEvidenceAttachment}
        onAttachmentUpdate={updateEvidenceAttachmentMetadata}
        onDeleteAttachment={deleteEvidenceAttachment}
        savedContentRef={savedDocumentsRef}
        tab={workspace.tabs[currentTab]}
        tabKey={currentTab}
      />
    );
  }

  return (
    <section className="space-y-6">
      <SafetyEvidenceTypePicker
        activeTab={currentTab}
        id={id}
        routeBase={routeBase}
      />

      {loadWarnings.length > 0 ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          {loadWarnings.join(' ')}
        </section>
      ) : null}

      {saveNotice ? (
        <section
          className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-900"
          role="status"
        >
          {saveNotice}
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
          {workspace.deadlineTasks.length > 0 ? (
            <div
              className="scroll-mt-24 outline-none"
              ref={checklistRef}
              tabIndex={-1}
            >
              <SafetySimpleDisclosure
                count={workspace.deadlineTasks.length}
                title="Checklist"
              >
                <SafetyEvidenceDeadlineTasks
                  disabled={isMutating}
                  onComplete={completeDeadlineTask}
                  tasks={workspace.deadlineTasks}
                />
              </SafetySimpleDisclosure>
            </div>
          ) : null}
          {renderActiveTab()}
          {!isAdvancedTab ? (
            <div className="grid gap-3">
              <Link
                className="rounded-3xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
                to={getTabHref(id, routeBase, 'interviews')}
              >
                <span className="block text-base font-semibold text-slate-950">
                  Witness Statement
                </span>
                <span className="mt-1 block text-sm text-slate-500">
                  Record or edit witness remarks and uploaded statement.
                </span>
              </Link>
              {evidenceCheckEnabled ? (
                <Link
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm font-semibold text-slate-900 hover:border-slate-300 hover:bg-white"
                  to={getTabHref(id, routeBase, 'evidence-matrix')}
                >
                  Evidence check
                </Link>
              ) : null}
            </div>
          ) : null}
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
          onClick={continueToActions}
          type="button"
        >
          {isMutating ? 'Saving...' : 'Save and Continue'}
        </button>
      </div>
      {phaseAdvanceError ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
          {phaseAdvanceError}
        </section>
      ) : phase4Blockers.length > 0 ? (
        <section className="rounded-3xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          Before you continue, {phase4Blockers.join(' and ')}.
        </section>
      ) : null}
    </section>
  );
}

export default SafetyIncidentPhase3;
