import { useState } from "react";

import type {
  SafetyScmCircularFeedItem,
  SafetyScmCreateAttendeeRow,
  SafetyScmCreatePayload,
  SafetyScmFormConfig,
  SafetyScmOverdueSoiArea,
} from "../../../lib/api/safety";
import {
  SAFETY_SCM_SCHEMA_VERSION,
  type SafetyScmSubmitValues,
  type SafetyScmValues,
  safetyScmLegacyFieldTemplate,
  safetyScmSectionTemplate,
  safetyScmSubmitSchema,
} from "../../../schemas/safety/scm";
import SafetyClosedSinceLastBlock from "./closed-since-last-block";
import SafetyScmAutoFeed, { type SafetyScmAutoFeedPayload } from "./soi-findings-auto-feed";

interface SafetyScmSubmitPayload extends SafetyScmSubmitValues {
  attendance_rows: SafetyScmCreatePayload["attendance_rows"];
}

interface SafetyScmTenSectionFormProps {
  autoFeedPayload?: SafetyScmAutoFeedPayload | null;
  config: SafetyScmFormConfig;
  isSubmitting?: boolean;
  mode?: "adhoc" | "regular";
  onSubmit?: (values: SafetyScmSubmitPayload) => void;
}

interface SafetyScmDraftValues extends SafetyScmValues {
  attendance_rows: SafetyScmCreateAttendeeRow[];
}

type LegacyFieldValue = string | number | boolean | null;

function populatedIndexedFieldCount(
  legacyFields: Record<string, LegacyFieldValue>,
  prefix: string,
  maxCount: number,
) {
  let count = 1;
  for (let index = 1; index <= maxCount; index += 1) {
    const value = legacyFields[`${prefix}${index}`];
    if (value !== null && value !== undefined && String(value).trim()) {
      count = index;
    }
  }
  return count;
}

function blankLegacyFields(agendaItemNumber: number): Record<string, LegacyFieldValue> {
  const fields = safetyScmLegacyFieldTemplate[
    agendaItemNumber as keyof typeof safetyScmLegacyFieldTemplate
  ] ?? [];
  return Object.fromEntries(fields.map((field) => [field.field_key, null]));
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "Not recorded";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString("en-GB", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatShortDate(value: string | null | undefined) {
  if (!value) {
    return "Not recorded";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatRestHours(value: number | string | null | undefined) {
  if (value === null || value === undefined) {
    return "Unavailable";
  }

  const normalized = typeof value === "number" ? value : Number(value);
  return Number.isFinite(normalized) ? `${normalized.toFixed(1)} h` : "Unavailable";
}

const defaultValues = (
  config: SafetyScmFormConfig,
  mode: "adhoc" | "regular",
): SafetyScmDraftValues => ({
  ad_hoc_trigger_reason: "",
  attendance_rows: config.attendee_rows.map((row) => ({ ...row })),
  chair_crew_id: config.chair?.crew_id ?? config.prepared_by?.crew_id ?? "",
  latitude: "",
  location: "",
  longitude: "",
  occasion: "M",
  ship_position: "P",
  ship_pos_from: "",
  ship_pos_to: "",
  comm_time: "10:00",
  comp_time: "",
  meeting_date: config.meeting_date_default,
  meeting_time_local: "10:00",
  meeting_type: mode === "adhoc" ? "AD_HOC" : "REGULAR",
  sections: config.sections.map((section) => ({
    agenda_item_number: section.agenda_item_number,
    content: section.content,
    decision: section.decision ?? "",
    legacy_fields: {
      ...blankLegacyFields(section.agenda_item_number),
      ...(section.legacy_fields ?? {}),
    },
    section_label: section.section_label,
  })),
  schema_version: SAFETY_SCM_SCHEMA_VERSION,
  vessel_code: config.vessel.vessel_code,
  vessel_id: config.vessel.id,
  voyage_no: "",
});

export function SafetyScmTenSectionForm({
  autoFeedPayload = null,
  config,
  isSubmitting = false,
  mode = "regular",
  onSubmit,
}: SafetyScmTenSectionFormProps) {
  const [values, setValues] = useState<SafetyScmDraftValues>(() => defaultValues(config, mode));
  const [visibleQualityTopicCount, setVisibleQualityTopicCount] = useState(() => {
    const section = defaultValues(config, mode).sections.find((row) => row.agenda_item_number === 3);
    return populatedIndexedFieldCount(section?.legacy_fields ?? {}, "quality_safety_topic_", 10);
  });
  const [visibleFindingCount, setVisibleFindingCount] = useState(() => {
    const section = defaultValues(config, mode).sections.find((row) => row.agenda_item_number === 8);
    return populatedIndexedFieldCount(section?.legacy_fields ?? {}, "findings", 10);
  });
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const coreValues: SafetyScmValues = {
    ad_hoc_trigger_reason: values.ad_hoc_trigger_reason,
    chair_crew_id: values.chair_crew_id,
    latitude: values.latitude,
    location: values.location,
    longitude: values.longitude,
    occasion: values.occasion,
    ship_position: values.ship_position,
    ship_pos_from: values.ship_pos_from,
    ship_pos_to: values.ship_pos_to,
    comm_time: values.comm_time,
    comp_time: values.comp_time,
    meeting_date: values.meeting_date,
    meeting_time_local: values.meeting_time_local,
    meeting_type: values.meeting_type,
    sections: values.sections,
    schema_version: values.schema_version,
    vessel_code: values.vessel_code,
    vessel_id: values.vessel_id,
    voyage_no: values.voyage_no,
  };
  const validationResult = safetyScmSubmitSchema.safeParse(coreValues);
  const attendanceErrors = values.attendance_rows
    .filter((row) => !row.present && !row.absence_reason?.trim())
    .map((row) => `${row.display_name || row.crew_id}: absence reason is required.`);
  const validationMessages = [
    ...(validationResult.success ? [] : validationResult.error.issues.map((issue) => issue.message)),
    ...attendanceErrors,
  ];
  const submitReady = validationResult.success && attendanceErrors.length === 0;

  function updateField<K extends keyof SafetyScmDraftValues>(
    field: K,
    nextValue: SafetyScmDraftValues[K],
  ) {
    setValues((current) => ({ ...current, [field]: nextValue }));
  }

  function updateSection(
    agendaItemNumber: number,
    field: "content" | "decision",
    nextValue: string,
  ) {
    setValues((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.agenda_item_number === agendaItemNumber
          ? { ...section, [field]: nextValue }
          : section,
      ),
    }));
  }

  function updateLegacyField(
    agendaItemNumber: number,
    fieldKey: string,
    nextValue: LegacyFieldValue,
  ) {
    setValues((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.agenda_item_number === agendaItemNumber
          ? {
              ...section,
              legacy_fields: {
                ...section.legacy_fields,
                [fieldKey]: nextValue,
              },
            }
          : section,
      ),
    }));
  }

  function updateAttendanceRow(
    crewId: string,
    patch: Partial<SafetyScmCreateAttendeeRow>,
  ) {
    setValues((current) => ({
      ...current,
      attendance_rows: current.attendance_rows.map((row) => {
        if (row.crew_id !== crewId) {
          return row;
        }

        const nextRow = { ...row, ...patch };
        if (patch.present === true) {
          nextRow.absence_reason = null;
        }
        return nextRow;
      }),
    }));
  }

  function handleSubmit() {
    setSubmitAttempted(true);
    if (!validationResult.success) {
      return;
    }

    if (attendanceErrors.length > 0) {
      return;
    }

    onSubmit?.({
      ...validationResult.data,
      attendance_rows: values.attendance_rows.map((row) => ({
        absence_reason: row.present ? null : row.absence_reason?.trim() || null,
        crew_id: row.crew_id,
        display_name: row.display_name,
        present: row.present,
        rank_name: row.rank_name,
        remarks: row.remarks?.trim() || null,
        schema_version: row.schema_version,
      })),
    });
  }

  const isAdHoc = values.meeting_type === "AD_HOC";
  const title = isAdHoc ? "Create Ad-Hoc SCM" : "Create Regular SCM";
  const summary = isAdHoc
    ? "Master-triggered 10-section committee record using the standard SCM format and current vessel safety inputs."
    : "CO-prepared monthly committee record with vessel scope, crew roster, WRH warnings, and current safety summaries.";

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_55%,#dcfce7_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / SCM
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{summary}</p>
      </header>

      <section className="grid gap-4 xl:grid-cols-4">
        <DetailCard label="Vessel" value={`${config.vessel.vessel_code} - ${config.vessel.vessel_name}`} />
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <label className="space-y-2 text-sm text-slate-700">
            <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Meeting type
            </span>
            <select
              aria-label="Meeting type to host"
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2 text-base font-semibold text-slate-900"
              onChange={(event) =>
                updateField("meeting_type", event.target.value as "REGULAR" | "AD_HOC")
              }
              value={values.meeting_type}
            >
              <option value="REGULAR">Regular</option>
              <option value="AD_HOC">Ad-Hoc</option>
            </select>
          </label>
        </article>
        <DetailCard
          label="Prepared by"
          value={config.prepared_by ? `${config.prepared_by.crew_name} (${config.prepared_by.rank || config.prepared_by.crew_id})` : "Not resolved"}
        />
        <DetailCard
          label="Generated at"
          value={formatDateTime(config.generated_at)}
        />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Cadence status</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                Monthly cadence stays warning-only at CO preparation stage. Master sign-off still enforces the overdue SOI hard block later.
              </p>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                config.cadence_status.is_overdue ? "bg-amber-50 text-amber-700" : "bg-emerald-50 text-emerald-700"
              }`}
            >
              {config.cadence_status.is_overdue ? "Overdue" : "On cycle"}
            </span>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            <DetailCard
              label="Last regular closure"
              value={formatDateTime(config.cadence_status.last_regular_closed_at)}
            />
            <DetailCard
              label="Next due date"
              value={formatShortDate(config.cadence_status.next_due_date)}
            />
            <DetailCard
              label="Days since closure"
              value={config.cadence_status.days_since_last_regular_closure?.toString() ?? "First cycle"}
            />
          </div>

          {config.cadence_warning ? (
            <div className="mt-4 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {config.cadence_warning.message}
            </div>
          ) : null}
        </article>

        <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Generated roles</h2>
          <dl className="mt-4 space-y-3 text-sm text-slate-700">
            <RoleRow
              label="Prepared by"
              value={config.prepared_by ? `${config.prepared_by.crew_name} - ${config.prepared_by.rank || config.prepared_by.crew_id}` : "Not resolved"}
            />
            <RoleRow
              label="Chair"
              value={config.chair ? `${config.chair.crew_name} - ${config.chair.rank || config.chair.crew_id}` : "Not resolved"}
            />
            <RoleRow
              label="Department"
              value={config.prepared_by?.department || "Not resolved"}
            />
            <RoleRow
              label="Vessel scope"
              value={config.vessel.vessel_name || config.vessel.vessel_code || config.vessel.id}
            />
          </dl>
        </article>
      </section>

      {config.overdue_soi_areas.length > 0 ? (
        <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-rose-950">Overdue SOI warning</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-rose-900">
                This does not block CO meeting creation, but it will block Master sign-off until the overdue SOI areas are cleared.
              </p>
            </div>
            <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-rose-700">
              {config.overdue_soi_areas.length} overdue area{config.overdue_soi_areas.length === 1 ? "" : "s"}
            </span>
          </div>
          <div className="mt-4 grid gap-3 xl:grid-cols-2">
            {config.overdue_soi_areas.map((area) => (
              <OverdueAreaCard area={area} key={area.area_id} />
            ))}
          </div>
        </section>
      ) : null}

      <SafetyClosedSinceLastBlock payload={config.closed_since_last} title="Closed since previous SCM sign-off" />

      {autoFeedPayload ? <SafetyScmAutoFeed payload={autoFeedPayload} /> : null}

      <SafetyScmCircularFeed
        items={config.latest_circulars ?? []}
      />

      <section className="grid gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:grid-cols-2 xl:grid-cols-6">
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Meeting date</span>
          <input
            aria-label="Meeting date"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("meeting_date", event.target.value)}
            type="date"
            value={values.meeting_date}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Meeting time</span>
          <input
            aria-label="Meeting time"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => {
              updateField("meeting_time_local", event.target.value);
              updateField("comm_time", event.target.value);
            }}
            type="time"
            value={values.meeting_time_local}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Ocassion</span>
          <select
            aria-label="Ocassion"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("occasion", event.target.value)}
            value={values.occasion}
          >
            <option value="M">Monthly</option>
            <option value="S">Superintendent visit</option>
          </select>
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">ShipPosition</span>
          <select
            aria-label="ShipPosition"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("ship_position", event.target.value as "S" | "P")}
            value={values.ship_position}
          >
            <option value="P">Port</option>
            <option value="S">Sea</option>
          </select>
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Location</span>
          <input
            aria-label="Location"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("location", event.target.value)}
            value={values.location}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Voyage number</span>
          <input
            aria-label="Voyage number"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("voyage_no", event.target.value)}
            value={values.voyage_no}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">ShipPosFrom</span>
          <input
            aria-label="ShipPosFrom"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("ship_pos_from", event.target.value)}
            value={values.ship_pos_from}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">ShipPosTo</span>
          <input
            aria-label="ShipPosTo"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("ship_pos_to", event.target.value)}
            value={values.ship_pos_to}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Latitude</span>
          <input
            aria-label="Latitude"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("latitude", event.target.value)}
            value={values.latitude}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Longitude</span>
          <input
            aria-label="Longitude"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("longitude", event.target.value)}
            value={values.longitude}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">CommTime</span>
          <input
            aria-label="CommTime"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("comm_time", event.target.value)}
            type="time"
            value={values.comm_time}
          />
        </label>
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">CompTime</span>
          <input
            aria-label="CompTime"
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
            onChange={(event) => updateField("comp_time", event.target.value)}
            type="time"
            value={values.comp_time}
          />
        </label>
        {isAdHoc ? (
          <label className="space-y-2 text-sm text-slate-700 md:col-span-2 xl:col-span-6">
            <span className="font-medium">Ad-Hoc trigger reason</span>
            <textarea
              aria-label="Ad-Hoc trigger reason"
              className="min-h-[120px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
              onChange={(event) => updateField("ad_hoc_trigger_reason", event.target.value)}
              value={values.ad_hoc_trigger_reason}
            />
          </label>
        ) : null}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Crew attendance confirmation</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Crew list, rank, department, and WRH status come from current crew and rest-hour records. Present/absent confirmation and comments stay editable for CO/Master.
            </p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            Warn, don&apos;t block
          </span>
        </div>

        {values.attendance_rows.length === 0 ? (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center text-sm text-slate-600">
            No live crew roster was resolved for this vessel.
          </div>
        ) : (
          <div className="mt-5 overflow-x-auto rounded-3xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Crew</th>
                  <th className="px-4 py-3 font-medium">Rank / Dept</th>
                  <th className="px-4 py-3 font-medium">Present</th>
                  <th className="px-4 py-3 font-medium">WRH</th>
                  <th className="px-4 py-3 font-medium">Comments</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {values.attendance_rows.map((row) => (
                  <tr key={row.crew_id}>
                    <td className="px-4 py-4 text-slate-700">
                      <div className="font-medium text-slate-900">{row.display_name}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                        {row.crew_id}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-700">
                      <div className="font-medium text-slate-900">{row.rank_name || "Unranked"}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                        {row.department || "Unassigned department"}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-700">
                      <label className="flex items-center gap-2 text-sm">
                        <input
                          checked={row.present}
                          onChange={(event) => updateAttendanceRow(row.crew_id, { present: event.target.checked })}
                          type="checkbox"
                        />
                        Present
                      </label>
                      {!row.present ? (
                        <input
                          aria-label={`Absence reason for ${row.display_name}`}
                          className="mt-3 min-h-[40px] w-full rounded-2xl border border-slate-200 px-3 py-2 text-sm"
                          onChange={(event) => updateAttendanceRow(row.crew_id, { absence_reason: event.target.value })}
                          placeholder="Reason required when absent"
                          value={row.absence_reason ?? ""}
                        />
                      ) : null}
                    </td>
                    <td className="px-4 py-4 text-slate-700">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-medium ${
                          row.wrh_flag === "GREEN"
                            ? "bg-emerald-50 text-emerald-700"
                            : row.wrh_flag === "YELLOW"
                              ? "bg-amber-50 text-amber-700"
                              : "bg-rose-50 text-rose-700"
                        }`}
                      >
                        {row.wrh_flag}
                      </span>
                      <div className="mt-2 text-xs text-slate-500">
                        24h: {formatRestHours(row.wrh_rest_hours_24h)}
                      </div>
                      <div className="text-xs text-slate-500">
                        7d: {formatRestHours(row.wrh_rest_hours_7d)}
                      </div>
                      {row.warnings.length > 0 ? (
                        <div className="mt-2 space-y-1">
                          {row.warnings.map((warning) => (
                            <div className="text-xs text-amber-700" key={`${row.crew_id}-${warning}`}>
                              {warning}
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </td>
                    <td className="px-4 py-4 text-slate-700">
                      <textarea
                        aria-label={`Comments for ${row.display_name}`}
                        className="min-h-[110px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
                        onChange={(event) => updateAttendanceRow(row.crew_id, { remarks: event.target.value })}
                        placeholder="Comments or WRH explanation"
                        value={row.remarks ?? ""}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Open previous action items</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Unfinished SCM action items carry forward automatically so the committee does not need to recreate them manually in this month&apos;s discussion.
            </p>
          </div>
          <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
            {config.unresolved_previous_actions.length} carried forward
          </span>
        </div>

        {config.unresolved_previous_actions.length === 0 ? (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center text-sm text-slate-600">
            No unresolved previous SCM action items.
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
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {config.unresolved_previous_actions.map((item) => (
                  <tr key={item.id}>
                    <td className="px-4 py-4 text-slate-700">
                      <div className="font-medium text-slate-900">{item.source_scm_number}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                        Section {item.agenda_item_number} - {item.section_label}
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
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              KPI Review
            </p>
            <h2 className="text-xl font-semibold text-slate-900">KPI Review</h2>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
            Separate from Section 5
          </span>
        </div>
        <label className="mt-4 block space-y-2 text-sm text-slate-700">
          <span className="font-medium">KPI review</span>
          <textarea
            aria-label="KPI review"
            className="min-h-[110px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
            onChange={(event) => updateLegacyField(5, "kpi_review", event.target.value)}
            value={String(values.sections.find((section) => section.agenda_item_number === 5)?.legacy_fields.kpi_review ?? "")}
          />
        </label>
      </section>

      <section className="space-y-4">
        {values.sections.filter((section) => section.agenda_item_number !== 10 && section.agenda_item_number !== 2).map((section) => {
          return (
            <article
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
              key={section.agenda_item_number}
            >
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
                    Section {section.agenda_item_number}
                  </p>
                  <h2 className="text-xl font-semibold text-slate-900">{section.section_label}</h2>
                </div>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                  Legacy fields
                </span>
              </div>

              <div className="mt-4">
                <LegacySectionFields
                  legacyFields={section.legacy_fields}
                  onChange={(fieldKey, nextValue) =>
                    updateLegacyField(section.agenda_item_number, fieldKey, nextValue)
                  }
                  onAddFinding={() => setVisibleFindingCount((current) => Math.min(10, current + 1))}
                  onAddQualityTopic={() => setVisibleQualityTopicCount((current) => Math.min(10, current + 1))}
                  sectionNumber={section.agenda_item_number}
                  visibleFindingCount={visibleFindingCount}
                  visibleQualityTopicCount={visibleQualityTopicCount}
                />
              </div>
              <div className="mt-4">
                <label className="space-y-2 text-sm text-slate-700">
                  <span className="font-medium">Decision / action</span>
                  <textarea
                    aria-label={`${section.section_label} decision`}
                    className="min-h-[110px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
                    onChange={(event) =>
                      updateSection(section.agenda_item_number, "decision", event.target.value)
                    }
                    value={section.decision}
                  />
                </label>
              </div>
            </article>
          );
        })}
        <article className="rounded-3xl border border-slate-200 bg-slate-50 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Section 10
          </p>
          <h2 className="mt-1 text-xl font-semibold text-slate-900">Office Review</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            OFFICECOMMENTS and IsReviewed are completed by shore office review after vessel submission. They are not required during vessel SCM creation.
          </p>
        </article>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="max-w-3xl space-y-3">
            <p className="text-sm leading-6 text-slate-600">
              Vessel details, SCM type, preparer, chair, crew roster, WRH flags, previous closeout summary, SOI findings, and carried-forward actions are filled from current records. Complete attendance, discussion notes, decisions, actions, and remarks before finalizing.
            </p>
            {submitAttempted && validationMessages.length > 0 ? (
              <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                <p className="font-semibold">Complete these items before creating the meeting:</p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  {validationMessages.map((message, index) => (
                    <li key={`${message}-${index}`}>{message}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
          <button
            className="min-h-[44px] shrink-0 rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={isSubmitting}
            onClick={handleSubmit}
            type="button"
          >
            {isSubmitting
              ? "Creating..."
              : isAdHoc
                ? "Create Ad-Hoc Meeting"
                : "Create Regular Meeting"}
          </button>
        </div>
      </section>
    </section>
  );
}

function LegacySectionFields({
  legacyFields,
  onChange,
  onAddFinding,
  onAddQualityTopic,
  sectionNumber,
  visibleFindingCount,
  visibleQualityTopicCount,
}: {
  legacyFields: Record<string, LegacyFieldValue>;
  onChange: (fieldKey: string, nextValue: LegacyFieldValue) => void;
  onAddFinding: () => void;
  onAddQualityTopic: () => void;
  sectionNumber: number;
  visibleFindingCount: number;
  visibleQualityTopicCount: number;
}) {
  const allFields = safetyScmLegacyFieldTemplate[
    sectionNumber as keyof typeof safetyScmLegacyFieldTemplate
  ] ?? [];
  const fields = allFields.filter((field) => {
    if (sectionNumber === 5 && field.field_key === "kpi_review") {
      return false;
    }
    if (sectionNumber === 3 && field.field_key.startsWith("quality_safety_topic_")) {
      const index = Number(field.field_key.replace("quality_safety_topic_", ""));
      return index <= visibleQualityTopicCount;
    }
    return true;
  });

  if (sectionNumber === 8) {
    return (
      <div className="space-y-4">
        <div className="overflow-x-auto rounded-3xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="w-16 px-4 py-3 font-medium">No.</th>
                <th className="px-4 py-3 font-medium">Findings</th>
                <th className="px-4 py-3 font-medium">Corrective measure</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {Array.from({ length: visibleFindingCount }, (_, index) => {
                const itemNumber = index + 1;
                return (
                  <tr key={itemNumber}>
                    <td className="px-4 py-3 font-medium text-slate-700">{itemNumber}</td>
                    <td className="px-4 py-3">
                      <textarea
                        aria-label={`Findings ${itemNumber}`}
                        className="min-h-[84px] w-full rounded-2xl border border-slate-200 px-3 py-2 leading-6"
                        onChange={(event) => onChange(`findings${itemNumber}`, event.target.value)}
                        value={String(legacyFields[`findings${itemNumber}`] ?? "")}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <textarea
                        aria-label={`Corrective Measure ${itemNumber}`}
                        className="min-h-[84px] w-full rounded-2xl border border-slate-200 px-3 py-2 leading-6"
                        onChange={(event) => onChange(`correctivemeasure${itemNumber}`, event.target.value)}
                        value={String(legacyFields[`correctivemeasure${itemNumber}`] ?? "")}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {visibleFindingCount < 10 ? (
          <button
            className="min-h-[40px] rounded-full border border-slate-300 px-4 text-sm font-semibold text-slate-700"
            onClick={onAddFinding}
            type="button"
          >
            Add finding
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {fields.map((field) => {
        const value = legacyFields[field.field_key];
        if (field.field_type === "BOOLEAN") {
          return (
            <label className="space-y-2 text-sm text-slate-700" key={field.field_key}>
              <span className="font-medium">{field.field_label}</span>
              <select
                aria-label={field.field_label}
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) =>
                  onChange(field.field_key, event.target.value === "" ? null : event.target.value === "true")
                }
                value={value === null || value === undefined ? "" : value ? "true" : "false"}
              >
                <option value="">Select</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </label>
          );
        }

        if (field.field_type === "INTEGER") {
          return (
            <label className="space-y-2 text-sm text-slate-700" key={field.field_key}>
              <span className="font-medium">{field.field_label}</span>
              <input
                aria-label={field.field_label}
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) =>
                  onChange(field.field_key, event.target.value ? Number(event.target.value) : null)
                }
                type="number"
                value={value === null || value === undefined ? "" : String(value)}
              />
            </label>
          );
        }

        return (
          <label className="space-y-2 text-sm text-slate-700 md:col-span-2" key={field.field_key}>
            <span className="font-medium">{field.field_label}</span>
            <textarea
              aria-label={field.field_label}
              className="min-h-[110px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
              onChange={(event) => onChange(field.field_key, event.target.value)}
              value={String(value ?? "")}
            />
          </label>
        );
      })}
      {sectionNumber === 3 && visibleQualityTopicCount < 10 ? (
        <button
          className="min-h-[40px] rounded-full border border-slate-300 px-4 text-sm font-semibold text-slate-700 md:col-span-2"
          onClick={onAddQualityTopic}
          type="button"
        >
          Add Q&S topic
        </button>
      ) : null}
    </div>
  );
}

function SafetyScmCircularFeed({
  items,
}: {
  items: SafetyScmCircularFeedItem[];
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Latest circulars / safety alerts</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Published MSC records from msc_data are shown here for Section 4 discussion.
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
          {items.length} published
        </span>
      </div>

      {items.length === 0 ? (
        <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center text-sm text-slate-600">
          No published circulars or safety alerts were found for this vessel/fleet scope.
        </div>
      ) : (
        <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Reference</th>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Date issued</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {items.map((item) => (
                <tr key={item.id || item.sr_no || item.title}>
                  <td className="px-4 py-4 text-slate-700">
                    <div className="font-medium text-slate-900">{item.sr_no || "No reference"}</div>
                  </td>
                  <td className="px-4 py-4 text-slate-700">
                    <div className="font-medium text-slate-900">{item.title || "Untitled circular"}</div>
                  </td>
                  <td className="px-4 py-4 text-slate-600">
                    {formatShortDate(item.published_on || item.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function DetailCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-900">{value}</p>
    </article>
  );
}

function RoleRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-medium text-slate-900">{value}</dd>
    </div>
  );
}

function OverdueAreaCard({ area }: { area: SafetyScmOverdueSoiArea }) {
  return (
    <article className="rounded-2xl border border-rose-200 bg-white px-4 py-3">
      <p className="text-sm font-semibold text-rose-950">{area.area_name || `Area ${area.area_id}`}</p>
      <p className="mt-2 text-sm text-rose-900">{area.message}</p>
      <div className="mt-2 text-xs uppercase tracking-[0.18em] text-rose-600">
        Due {formatShortDate(area.due_at)} · {area.overdue_days} day{area.overdue_days === 1 ? "" : "s"} overdue
      </div>
    </article>
  );
}

export default SafetyScmTenSectionForm;
