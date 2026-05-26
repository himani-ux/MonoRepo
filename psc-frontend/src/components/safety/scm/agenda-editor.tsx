import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { safetyKeys } from "../../../hooks/use-safety";
import { safetyApi, type SafetyScmAgendaPayload, type SafetyScmAgendaRow } from "../../../lib/api/safety";
import { getErrorMessage } from "../../../lib/api/client";

interface SafetyScmAgendaEditorProps {
  payload: SafetyScmAgendaPayload;
}

interface EditableAgendaRow {
  action_assigned_crew_id: string;
  action_assigned_office_user_id: string;
  action_description: string;
  action_due_date: string;
  action_enabled: boolean;
  action_title: string;
  agenda_item_number: number;
  content: string;
  decision: string;
  id: number;
  section_label: string;
}

const statusTone: Record<string, string> = {
  CARRIED_FORWARD: "bg-amber-50 text-amber-700",
  CLOSED: "bg-emerald-50 text-emerald-700",
  IN_PROGRESS: "bg-sky-50 text-sky-700",
  OPEN: "bg-rose-50 text-rose-700",
};

function toEditableRow(row: SafetyScmAgendaRow): EditableAgendaRow {
  return {
    action_assigned_crew_id: row.action_item?.assigned_crew_id ?? "",
    action_assigned_office_user_id: row.action_item?.assigned_office_user_id ?? "",
    action_description: row.action_item?.description ?? "",
    action_due_date: row.action_item?.due_date ?? "",
    action_enabled: Boolean(row.action_item),
    action_title: row.action_item?.title ?? "",
    agenda_item_number: row.agenda_item_number,
    content: row.content ?? "",
    decision: row.decision ?? "",
    id: row.id,
    section_label: row.section_label,
  };
}

function validateRows(rows: EditableAgendaRow[]): string[] {
  const errors: string[] = [];
  for (const row of rows) {
    if (![7, 8, 9].includes(row.agenda_item_number) && !row.decision.trim()) {
      errors.push(`Section ${row.agenda_item_number} requires recommendation / suggestions.`);
    }
    if (!row.action_enabled) {
      continue;
    }
    if (row.action_title.trim().length < 5) {
      errors.push(`Section ${row.agenda_item_number} action title must be at least 5 characters.`);
    }
    if (row.action_description.trim().length < 20) {
      errors.push(`Section ${row.agenda_item_number} action description must be at least 20 characters.`);
    }
    if (!row.action_assigned_crew_id.trim() && !row.action_assigned_office_user_id.trim()) {
      errors.push(`Section ${row.agenda_item_number} action requires a crew or office owner.`);
    }
    if (!row.action_due_date) {
      errors.push(`Section ${row.agenda_item_number} action requires a due date.`);
    }
  }
  return errors;
}

export default function SafetyScmAgendaEditor({
  payload,
}: SafetyScmAgendaEditorProps) {
  const queryClient = useQueryClient();
  const [rows, setRows] = useState<EditableAgendaRow[]>(() => payload.rows.map(toEditableRow));
  const [saveAttempted, setSaveAttempted] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const validationErrors = useMemo(() => validateRows(rows), [rows]);
  const isLocked = payload.meeting_state === "SIGNED_OFF";

  const mutation = useMutation({
    mutationFn: () =>
      safetyApi.updateScmAgenda(payload.meeting_id, {
        rows: rows.map((row) => ({
          agenda_item_number: row.agenda_item_number,
          content: row.content,
          decision: row.decision.trim() || null,
          action_item: {
            assigned_crew_id: row.action_assigned_crew_id.trim() || null,
            assigned_office_user_id: row.action_assigned_office_user_id.trim() || null,
            description: row.action_description.trim(),
            due_date: row.action_due_date || null,
            enabled: row.action_enabled,
            title: row.action_title.trim(),
          },
        })),
      }),
    onSuccess: async (updated) => {
      setRows(updated.rows.map(toEditableRow));
      setSaveAttempted(false);
      setMessage("Agenda recommendations and action items saved.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmAgenda(payload.meeting_id) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmMeeting(payload.meeting_id) }),
        queryClient.invalidateQueries({ queryKey: safetyKeys.scmSignoffPreflight(payload.meeting_id) }),
      ]);
    },
  });

  function updateRow(rowId: number, patch: Partial<EditableAgendaRow>) {
    setRows((current) =>
      current.map((row) => (row.id === rowId ? { ...row, ...patch } : row)),
    );
  }

  function handleSave() {
    setSaveAttempted(true);
    setMessage(null);
    if (validationErrors.length > 0) {
      return;
    }
    mutation.mutate();
  }

  return (
    <section className="space-y-6">
      <section className="grid gap-3 sm:grid-cols-3">
        <SummaryCard label="Current action items" value={payload.summary.current_action_item_count} />
        <SummaryCard label="Open action items" value={payload.summary.open_action_item_count} />
        <SummaryCard label="Carried forward" value={payload.summary.carried_forward_count} />
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Agenda recommendations and action items</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Edit the fixed SCM agenda, record recommendations/suggestions, and create or update section-linked corrective actions.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <div className="font-medium text-slate-900">Meeting context</div>
            <div className="mt-1">
              {payload.meeting_type} / {payload.meeting_state}
            </div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
              {payload.meeting_date}
            </div>
          </div>
        </div>

        <div className="mt-5 space-y-4">
          {rows.map((row) => (
            <article className="rounded-3xl border border-slate-200 bg-slate-50 p-4" key={row.id}>
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                    Section {row.agenda_item_number}
                  </p>
                  <h3 className="mt-1 text-base font-semibold text-slate-900">{row.section_label}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{row.content || "No section content recorded."}</p>
                </div>
                <StatusPill value={payload.rows.find((item) => item.id === row.id)?.action_item?.display_status ?? "No action"} />
              </div>

              {[7, 8, 9].includes(row.agenda_item_number) ? null : (
              <label className="mt-4 block">
                <span className="text-sm font-semibold text-slate-900">Recommendation / Suggestions</span>
                <textarea
                  className="mt-2 min-h-[96px] w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 disabled:bg-slate-100"
                  disabled={isLocked}
                  onChange={(event) => updateRow(row.id, { decision: event.target.value })}
                  value={row.decision}
                />
              </label>
              )}

              <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4">
                <label className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <input
                    checked={row.action_enabled}
                    disabled={isLocked}
                    onChange={(event) => updateRow(row.id, { action_enabled: event.target.checked })}
                    type="checkbox"
                  />
                  Create / update corrective action for this section
                </label>

                {row.action_enabled ? (
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    <label className="block md:col-span-2">
                      <span className="text-sm font-medium text-slate-700">Action title</span>
                      <input
                        className="mt-2 min-h-[44px] w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
                        disabled={isLocked}
                        onChange={(event) => updateRow(row.id, { action_title: event.target.value })}
                        value={row.action_title}
                      />
                    </label>
                    <label className="block md:col-span-2">
                      <span className="text-sm font-medium text-slate-700">Action description</span>
                      <textarea
                        className="mt-2 min-h-[96px] w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
                        disabled={isLocked}
                        onChange={(event) => updateRow(row.id, { action_description: event.target.value })}
                        value={row.action_description}
                      />
                    </label>
                    <label className="block">
                      <span className="text-sm font-medium text-slate-700">Crew owner ID</span>
                      <input
                        className="mt-2 min-h-[44px] w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
                        disabled={isLocked}
                        onChange={(event) => updateRow(row.id, { action_assigned_crew_id: event.target.value })}
                        value={row.action_assigned_crew_id}
                      />
                    </label>
                    <label className="block">
                      <span className="text-sm font-medium text-slate-700">Office owner ID</span>
                      <input
                        className="mt-2 min-h-[44px] w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
                        disabled={isLocked}
                        onChange={(event) => updateRow(row.id, { action_assigned_office_user_id: event.target.value })}
                        value={row.action_assigned_office_user_id}
                      />
                    </label>
                    <label className="block">
                      <span className="text-sm font-medium text-slate-700">Due date</span>
                      <input
                        className="mt-2 min-h-[44px] w-full rounded-2xl border border-slate-300 px-3 py-2 text-sm disabled:bg-slate-100"
                        disabled={isLocked}
                        onChange={(event) => updateRow(row.id, { action_due_date: event.target.value })}
                        type="date"
                        value={row.action_due_date}
                      />
                    </label>
                  </div>
                ) : null}
              </div>
            </article>
          ))}
        </div>

        {saveAttempted && validationErrors.length > 0 ? (
          <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <p className="font-semibold">Complete these items before saving:</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              {validationErrors.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {mutation.isError ? (
          <p className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-900">
            {getErrorMessage(mutation.error)}
          </p>
        ) : null}

        {message ? (
          <p className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
            {message}
          </p>
        ) : null}

        <button
          className="mt-5 min-h-[44px] rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
          disabled={isLocked || mutation.isPending}
          onClick={handleSave}
          type="button"
        >
          {mutation.isPending ? "Saving agenda..." : "Save agenda changes"}
        </button>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Carried-forward open items</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Open SCM-linked corrective actions remain visible on the next agenda route so accountability persists between meetings.
            </p>
          </div>
          <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
            Auto carry-forward
          </span>
        </div>

        {payload.carried_forward_items.length === 0 ? (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center text-sm text-slate-600">
            No carried-forward action items for this meeting.
          </div>
        ) : (
          <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Source SCM</th>
                  <th className="px-4 py-3 font-medium">Action item</th>
                  <th className="px-4 py-3 font-medium">Owner</th>
                  <th className="px-4 py-3 font-medium">Due</th>
                  <th className="px-4 py-3 font-medium">State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {payload.carried_forward_items.map((item) => (
                  <tr key={item.id}>
                    <td className="px-4 py-4 text-slate-700">
                      <div className="font-medium text-slate-900">{item.source_scm_number}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                        Section {item.agenda_item_number} / {item.section_label}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-700">
                      <div className="font-medium text-slate-900">{item.title}</div>
                      <div className="mt-1 text-sm leading-6 text-slate-600">{item.description}</div>
                    </td>
                    <td className="px-4 py-4 text-slate-600">
                      {item.assigned_crew_id ?? item.assigned_office_user_id ?? "Unassigned"}
                    </td>
                    <td className="px-4 py-4 text-slate-600">{item.due_date ?? "Not set"}</td>
                    <td className="px-4 py-4">
                      <StatusPill value={item.display_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
    </article>
  );
}

function StatusPill({ value }: { value: string }) {
  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${statusTone[value] ?? "bg-slate-100 text-slate-600"}`}>
      {value}
    </span>
  );
}
