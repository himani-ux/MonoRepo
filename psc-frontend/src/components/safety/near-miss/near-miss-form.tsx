import { useEffect, useState, type ReactNode } from "react";

import {
  SAFETY_NEAR_MISS_SCHEMA_VERSION,
  SAFETY_NEAR_MISS_CATEGORY_TAGS,
  SAFETY_NEAR_MISS_LOSS_OPTIONS,
  SAFETY_NEAR_MISS_OTHER_PREFIX,
  SAFETY_NEAR_MISS_PLACES,
  type SafetyNearMissSubmitValues,
  type SafetyNearMissValues,
  safetyNearMissSubmitSchema,
} from "../../../schemas/safety/near-miss";
import { useAuth } from "../../../hooks/use-auth";
import { toUtcIsoTimestamp } from "../../../hooks/safety/use-msc-mepc3-position";
import {
  safetyApi,
  type SafetyNearMissGuidancePrompt,
} from "../../../lib/api/safety";
import { getSafetyDeviceFingerprint } from "../../../lib/safety/digital-signature";
import { SafetyMscatPicker } from "../shared/reference-pickers";

const OTHER_CATEGORY_SELECT_VALUE = "__OTHER_CATEGORY__";
const DEFAULT_LOSS_TYPE_ID = SAFETY_NEAR_MISS_LOSS_OPTIONS.find((option) => option.label === "Non-conformity")?.value
  ?? SAFETY_NEAR_MISS_LOSS_OPTIONS[0]?.value
  ?? 1;

interface SafetyNearMissFormProps {
  description?: string;
  showRateLimit?: boolean;
  submitDisabled?: boolean;
  submitLabel?: string;
  title?: string;
  initialValues?: Partial<SafetyNearMissValues>;
  onSubmit?: (values: SafetyNearMissSubmitValues) => void;
  afterFields?: ReactNode;
}

const defaultValues: SafetyNearMissValues = {
  incident_type_id: null,
  loss_type_primary_id: DEFAULT_LOSS_TYPE_ID,
  narrative: "",
  near_miss_immediate_action: "",
  near_miss_place: null,
  near_miss_category_tags: [],
  near_miss_incident_type_ids: [],
  near_miss_mscat_category_id: null,
  near_miss_mscat_subcode_id: null,
  near_miss_mscat_subcode_ids: [],
  near_miss_severity: null,
  near_miss_shell_tag: null,
  near_miss_suggestion: "",
  near_miss_root_cause_detail: "",
  near_miss_corrective_action: "",
  near_miss_weather_voyage_details: "",
  near_miss_equipment_details: "",
  near_miss_lessons_learned: "",
  occurred_at: "",
  reporter_device_fingerprint: "",
  reporter_name: "",
  reporter_rank: "",
  reporter_user_id: "",
  schema_version: SAFETY_NEAR_MISS_SCHEMA_VERSION,
  vessel_id: "",
};

function firstNonBlank(...values: Array<string | null | undefined>) {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }

  return "";
}

function buildReporterNameFromAuth(user: ReturnType<typeof useAuth>["user"]) {
  const combinedName = [user?.first_name, user?.surname]
    .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
    .join(" ")
    .trim();

  return firstNonBlank(
    user?.full_name,
    user?.display_name,
    combinedName,
    user?.username,
    user?.UserName,
    user?.crew_id,
  );
}

function toDateTimeLocalValue(value?: string | null) {
  if (!value) {
    return "";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }

  const timezoneOffsetMs = parsed.getTimezoneOffset() * 60_000;
  return new Date(parsed.getTime() - timezoneOffsetMs).toISOString().slice(0, 16);
}

function addLimitedValue<T>(values: T[], nextValue: T | null | undefined) {
  if (nextValue === null || nextValue === undefined || String(nextValue).trim() === "") {
    return values;
  }
  if (values.includes(nextValue)) {
    return values;
  }
  return [...values, nextValue].slice(0, 3);
}

function primaryCategoryTag(tags: string[]) {
  const first = tags[0];
  if (!first) {
    return null;
  }
  return first.startsWith(SAFETY_NEAR_MISS_OTHER_PREFIX) ? "Others" : first;
}

function formatOtherValue(value: string) {
  const cleaned = value.trim().replace(/\s+/g, " ");
  return cleaned ? `${SAFETY_NEAR_MISS_OTHER_PREFIX} ${cleaned}` : "";
}

function resolveLossOptionByLabel(label: string) {
  const normalized = label.trim().toLowerCase();
  return SAFETY_NEAR_MISS_LOSS_OPTIONS.find((option) => option.label.toLowerCase() === normalized);
}

function removeValue<T>(values: T[], valueToRemove: T) {
  return values.filter((value) => value !== valueToRemove);
}

function SelectedValueChips({
  labels,
  onRemove,
}: {
  labels: string[];
  onRemove: (label: string, index: number) => void;
}) {
  if (!labels.length) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {labels.map((label, index) => (
        <span
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700"
          key={`${label}-${index}`}
        >
          {label}
          <button
            aria-label={`Remove ${label}`}
            className="rounded-full text-slate-500 hover:text-rose-700 focus:outline-none focus:ring-2 focus:ring-rose-200"
            onClick={() => onRemove(label, index)}
            type="button"
          >
            x
          </button>
        </span>
      ))}
    </div>
  );
}

export function SafetyNearMissForm({
  description = "Any authorized rank may submit a near miss. Reporter details are visible to authorized users.",
  initialValues,
  onSubmit,
  afterFields,
  showRateLimit = true,
  submitDisabled = false,
  submitLabel = "Submit near miss",
  title = "Create Near Miss",
}: SafetyNearMissFormProps) {
  const { isVessel, user } = useAuth();
  const [values, setValues] = useState<SafetyNearMissValues>({
    ...defaultValues,
    ...initialValues,
  });
  const [guidancePrompts, setGuidancePrompts] = useState<SafetyNearMissGuidancePrompt[]>([]);
  const [otherCategoryText, setOtherCategoryText] = useState("");
  const [showOtherCategoryInput, setShowOtherCategoryInput] = useState(false);
  const [showOtherImmediateCauseInput, setShowOtherImmediateCauseInput] = useState(false);
  const [pendingImmediateCause, setPendingImmediateCause] = useState<{ categoryId: number | null; subcodeId: string | null }>({
    categoryId: null,
    subcodeId: null,
  });

  const narrativeLength = values.narrative.trim().length;
  const submitReady = safetyNearMissSubmitSchema.safeParse(values).success;
  const vesselIdFromAuth = firstNonBlank(user?.vessel_id);
  const vesselCodeFromAuth = firstNonBlank(user?.vessel_code);
  const vesselDisplayName = firstNonBlank(user?.vessel_name, user?.vessel_code, values.vessel_code, user?.vessel_id, values.vessel_id);
  const vesselOptions = (user?.vessel_ids ?? [])
    .map((vesselId, index) => ({
      id: String(vesselId).trim(),
      label: firstNonBlank(user?.vessel_names?.[index], String(vesselId)),
    }))
    .filter((option) => option.id);
  const reporterUserIdFromAuth = firstNonBlank(
    user?.crew_id,
    user?.username,
    user?.UserName,
    user?.id,
  );
  const reporterNameFromAuth = buildReporterNameFromAuth(user);
  const reporterRankFromAuth = firstNonBlank(
    user?.rank,
    user?.safety_role_name,
    user?.role_name,
    user?.role,
  );
  const reporterIdentityComplete = Boolean(
    reporterUserIdFromAuth && reporterNameFromAuth && reporterRankFromAuth,
  );
  const isHighSeverity = values.near_miss_severity === "HIGH";
  const categoryOptions = [
    ...SAFETY_NEAR_MISS_CATEGORY_TAGS.filter((tag) => tag.trim().toLowerCase() !== "others"),
    ...SAFETY_NEAR_MISS_LOSS_OPTIONS.map((option) => option.label),
  ].filter((label, index, options) => (
    options.findIndex((option) => option.toLowerCase() === label.toLowerCase()) === index
  ));

  useEffect(() => {
    setValues((current) => {
      if (current.reporter_device_fingerprint) {
        return current;
      }

      return {
        ...current,
        reporter_device_fingerprint: getSafetyDeviceFingerprint(),
      };
    });
  }, []);

  useEffect(() => {
    if (!isVessel) {
      return;
    }

    setValues((current) => {
      const nextVesselId = vesselIdFromAuth || current.vessel_id;
      const nextVesselCode = vesselCodeFromAuth || current.vessel_code;

      if (
        current.vessel_id === nextVesselId &&
        (current.vessel_code ?? "") === (nextVesselCode ?? "")
      ) {
        return current;
      }

      return {
        ...current,
        vessel_code: nextVesselCode,
        vessel_id: nextVesselId,
      };
    });
  }, [isVessel, vesselCodeFromAuth, vesselIdFromAuth]);

  useEffect(() => {
    setValues((current) => {
      const nextReporterUserId = reporterUserIdFromAuth || current.reporter_user_id;
      const nextReporterName = reporterNameFromAuth || current.reporter_name;
      const nextReporterRank = reporterRankFromAuth || current.reporter_rank;

      if (
        current.reporter_user_id === nextReporterUserId &&
        current.reporter_name === nextReporterName &&
        current.reporter_rank === nextReporterRank
      ) {
        return current;
      }

      return {
        ...current,
        reporter_name: nextReporterName,
        reporter_rank: nextReporterRank,
        reporter_user_id: nextReporterUserId,
      };
    });
  }, [
    reporterNameFromAuth,
    reporterRankFromAuth,
    reporterUserIdFromAuth,
  ]);

  useEffect(() => {
    let cancelled = false;
    safetyApi
      .getReferenceIncidentTypes()
      .then((options) => {
        if (!cancelled) {
          const firstActiveType = options.find((option) => option.active);
          if (firstActiveType) {
            setValues((current) => {
              const incidentTypeIds = current.near_miss_incident_type_ids.length
                ? current.near_miss_incident_type_ids
                : [firstActiveType.legacy_int_id];
              const nextIncidentTypeId = current.incident_type_id ?? incidentTypeIds[0] ?? firstActiveType.legacy_int_id;
              const nextLossTypeId = current.loss_type_primary_id ?? DEFAULT_LOSS_TYPE_ID;
              if (
                current.incident_type_id === nextIncidentTypeId
                && current.loss_type_primary_id === nextLossTypeId
                && current.near_miss_incident_type_ids.length === incidentTypeIds.length
              ) {
                return current;
              }
              return {
                ...current,
                incident_type_id: nextIncidentTypeId,
                loss_type_primary_id: nextLossTypeId,
                near_miss_incident_type_ids: incidentTypeIds,
              };
            });
          }
        }
      })
      .catch(() => {
        return undefined;
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    safetyApi
      .getNearMissGuidancePrompts({
        category_tag: values.near_miss_shell_tag,
        incident_type_id: values.incident_type_id,
      })
      .then((prompts) => {
        if (!cancelled) {
          setGuidancePrompts(prompts);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setGuidancePrompts([]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [values.incident_type_id, values.near_miss_shell_tag]);

  function updateField<K extends keyof SafetyNearMissValues>(
    field: K,
    nextValue: SafetyNearMissValues[K],
  ) {
    setValues((current) => ({ ...current, [field]: nextValue }));
  }

  function updateCategoryTags(nextTags: string[]) {
    setValues((current) => ({
      ...current,
      near_miss_category_tags: nextTags,
      near_miss_shell_tag: primaryCategoryTag(nextTags) as SafetyNearMissValues["near_miss_shell_tag"],
    }));
  }

  function addCategoryValue(rawValue: string) {
    if (rawValue === OTHER_CATEGORY_SELECT_VALUE) {
      setShowOtherCategoryInput(true);
      return;
    }

    const lossOption = resolveLossOptionByLabel(rawValue);
    const nextTags = addLimitedValue(values.near_miss_category_tags, rawValue);
    updateCategoryTags(nextTags);
    updateField("loss_type_primary_id", lossOption?.value ?? values.loss_type_primary_id ?? DEFAULT_LOSS_TYPE_ID);
  }

  function addOtherCategory() {
    const formatted = formatOtherValue(otherCategoryText);
    if (!formatted) {
      return;
    }
    updateCategoryTags(addLimitedValue(values.near_miss_category_tags, formatted));
    setOtherCategoryText("");
    setShowOtherCategoryInput(false);
    updateField("loss_type_primary_id", values.loss_type_primary_id ?? DEFAULT_LOSS_TYPE_ID);
  }

  function updateImmediateCauses(nextSubcodes: string[], categoryId?: number | null) {
    setValues((current) => ({
      ...current,
      near_miss_mscat_category_id: categoryId ?? current.near_miss_mscat_category_id,
      near_miss_mscat_subcode_id: nextSubcodes[0] ?? null,
      near_miss_mscat_subcode_ids: nextSubcodes,
    }));
  }

  function handleSubmit() {
    if (submitDisabled) {
      return;
    }

    const result = safetyNearMissSubmitSchema.safeParse(values);
    if (!result.success) {
      return;
    }

    onSubmit?.(result.data);
  }

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_55%,#e0f2fe_100%)] p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
          Safety / Near Miss
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-slate-900">
          {title}
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          {description}
        </p>
      </header>

      <div className="grid gap-6 xl:grid-cols-[1.6fr_1fr]">
        <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Vessel</span>
              {!isVessel && vesselOptions.length > 0 ? (
                <select
                  aria-label="Vessel"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                  onChange={(event) => updateField("vessel_id", event.target.value)}
                  value={values.vessel_id}
                >
                  <option value="">Select vessel</option>
                  {vesselOptions.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  aria-label="Vessel"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) => updateField("vessel_id", event.target.value)}
                  readOnly={isVessel}
                  value={isVessel ? vesselDisplayName : values.vessel_id}
                />
              )}
            </label>
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Vessel code</span>
              <input
                aria-label="Vessel code"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                onChange={(event) => updateField("vessel_code", event.target.value)}
                readOnly={isVessel}
                value={values.vessel_code ?? ""}
              />
            </label>
          </div>

          <label className="block space-y-2 text-sm text-slate-700">
            <span className="font-medium">Occurred at</span>
            <input
              aria-label="Occurred at"
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
              onChange={(event) =>
                updateField("occurred_at", toUtcIsoTimestamp(event.target.value) ?? "")
              }
              type="datetime-local"
              value={toDateTimeLocalValue(values.occurred_at)}
            />
          </label>

          <label className="block space-y-2 text-sm text-slate-700">
            <span className="font-medium">What happened</span>
            <textarea
              aria-label="What happened"
              className="min-h-[220px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
              onChange={(event) => updateField("narrative", event.target.value)}
              value={values.narrative}
            />
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500">
                Minimum 100 characters before submission.
              </span>
              <span className={narrativeLength >= 100 ? "text-emerald-700" : "text-amber-700"}>
                {narrativeLength}/100
              </span>
            </div>
          </label>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Severity</span>
              <select
                aria-label="Severity"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                onChange={(event) =>
                  updateField(
                    "near_miss_severity",
                    (event.target.value || null) as SafetyNearMissValues["near_miss_severity"],
                  )
                }
                value={values.near_miss_severity ?? ""}
              >
                <option value="">Select severity</option>
                <option value="HIGH">HIGH</option>
                <option value="MED">MED</option>
                <option value="LOW">LOW</option>
              </select>
            </label>

            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Place</span>
              <select
                aria-label="Place"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                onChange={(event) =>
                  updateField(
                    "near_miss_place",
                    (event.target.value || null) as SafetyNearMissValues["near_miss_place"],
                  )
                }
                value={values.near_miss_place ?? ""}
              >
                <option value="">Select place</option>
                {SAFETY_NEAR_MISS_PLACES.map((place) => (
                  <option key={place.value} value={place.value}>
                    {place.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <section className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Category</span>
              <select
                aria-label="Category"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                disabled={values.near_miss_category_tags.length >= 3}
                onChange={(event) => {
                  addCategoryValue(event.target.value);
                  event.currentTarget.value = "";
                }}
              >
                <option value="">
                  {values.near_miss_category_tags.length >= 3 ? "Maximum 3 selected" : "Add category"}
                </option>
                {categoryOptions
                  .filter((tag) => !values.near_miss_category_tags.includes(tag))
                  .map((tag) => (
                    <option key={tag} value={tag}>
                      {tag}
                    </option>
                  ))}
                <option value={OTHER_CATEGORY_SELECT_VALUE}>Other - Specify</option>
              </select>
              {showOtherCategoryInput ? (
                <div className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:flex-row">
                  <input
                    aria-label="Specify other category"
                    className="min-h-[40px] flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2"
                    onChange={(event) => setOtherCategoryText(event.target.value)}
                    placeholder="Type category"
                    value={otherCategoryText}
                  />
                  <button
                    className="min-h-[40px] rounded-xl bg-slate-900 px-4 text-sm font-semibold text-white disabled:bg-slate-300"
                    disabled={!otherCategoryText.trim() || values.near_miss_category_tags.length >= 3}
                    onClick={addOtherCategory}
                    type="button"
                  >
                    Add
                  </button>
                </div>
              ) : null}
              <SelectedValueChips
                labels={values.near_miss_category_tags}
                onRemove={(tag) => updateCategoryTags(removeValue(values.near_miss_category_tags, tag))}
              />
            </div>
          </section>

          <section className="block space-y-2 text-sm text-slate-700">
            <span className="font-medium">Immediate cause</span>
            <SafetyMscatPicker
              bottomOptionLabel="Other - Specify"
              key={values.near_miss_mscat_subcode_ids.join("|")}
              label="Immediate cause"
              onChange={(nextValue) => {
                setPendingImmediateCause(nextValue);
                if (nextValue.subcodeId) {
                  updateImmediateCauses(
                    addLimitedValue(values.near_miss_mscat_subcode_ids, nextValue.subcodeId),
                    nextValue.categoryId,
                  );
                  window.setTimeout(() => setPendingImmediateCause({ categoryId: null, subcodeId: null }), 0);
                }
              }}
              onBottomOptionSelect={() => setShowOtherImmediateCauseInput(true)}
              value={pendingImmediateCause}
            />
            {showOtherImmediateCauseInput ? (
              <label className="block space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700">
                <span className="font-medium">Specify other immediate cause</span>
                <textarea
                  aria-label="Specify other immediate cause"
                  className="min-h-[90px] w-full rounded-xl border border-slate-200 bg-white px-3 py-2 leading-6"
                  onChange={(event) => updateField("near_miss_root_cause_detail", event.target.value)}
                  placeholder="Type immediate cause"
                  value={values.near_miss_root_cause_detail}
                />
              </label>
            ) : null}
            <SelectedValueChips
              labels={values.near_miss_mscat_subcode_ids}
              onRemove={(subcode) => updateImmediateCauses(removeValue(values.near_miss_mscat_subcode_ids, subcode))}
            />
          </section>

          <label className="block space-y-2 text-sm text-slate-700">
            <span className="font-medium">Immediate action</span>
            <textarea
              aria-label="Immediate action"
              className="min-h-[120px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
              onChange={(event) => updateField("near_miss_immediate_action", event.target.value)}
              value={values.near_miss_immediate_action}
            />
          </label>

          <label className="block space-y-2 text-sm text-slate-700">
            <span className="font-medium">Preventive action / suggestion</span>
            <textarea
              aria-label="Preventive action / suggestion"
              className="min-h-[120px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
              onChange={(event) => updateField("near_miss_suggestion", event.target.value)}
              value={values.near_miss_suggestion}
            />
          </label>

          {isHighSeverity ? (
            <section className="space-y-4 rounded-3xl border border-rose-100 bg-rose-50 p-5">
              <h2 className="text-lg font-semibold text-slate-900">High-risk details</h2>
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Root cause detail</span>
                <textarea
                  className="min-h-[100px] w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 leading-6"
                  onChange={(event) => updateField("near_miss_root_cause_detail", event.target.value)}
                  value={values.near_miss_root_cause_detail}
                />
              </label>
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Corrective action</span>
                <textarea
                  className="min-h-[100px] w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 leading-6"
                  onChange={(event) => updateField("near_miss_corrective_action", event.target.value)}
                  value={values.near_miss_corrective_action}
                />
              </label>
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Weather / voyage details</span>
                <textarea
                  className="min-h-[90px] w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 leading-6"
                  onChange={(event) => updateField("near_miss_weather_voyage_details", event.target.value)}
                  value={values.near_miss_weather_voyage_details}
                />
              </label>
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Equipment details</span>
                <textarea
                  className="min-h-[90px] w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 leading-6"
                  onChange={(event) => updateField("near_miss_equipment_details", event.target.value)}
                  value={values.near_miss_equipment_details}
                />
              </label>
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Lessons learned</span>
                <textarea
                  className="min-h-[100px] w-full rounded-3xl border border-slate-200 bg-white px-4 py-3 leading-6"
                  onChange={(event) => updateField("near_miss_lessons_learned", event.target.value)}
                  value={values.near_miss_lessons_learned}
                />
              </label>
            </section>
          ) : null}

          {afterFields}
        </section>

        <aside className="space-y-6">
          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Reporter block</h2>
            <div className="mt-4 space-y-4">
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="font-medium text-slate-700">Reporter user ID</dt>
                  <dd className="mt-1 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-900">
                    {values.reporter_user_id || "Resolved from login/session"}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-slate-700">Reporter name</dt>
                  <dd className="mt-1 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-900">
                    {values.reporter_name || "Resolved from login/session"}
                  </dd>
                </div>
                <div>
                  <dt className="font-medium text-slate-700">Reporter rank</dt>
                  <dd className="mt-1 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-900">
                    {values.reporter_rank || "Resolved from login/session"}
                  </dd>
                </div>
              </dl>
              {!reporterIdentityComplete ? (
                <p className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800">
                  Reporter identity will be resolved from login/session; contact admin if missing.
                </p>
              ) : null}
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Submission guardrails</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              {showRateLimit
                ? "On submit, near-miss descriptions must reach 100 characters. Office comments assign LOW, MEDIUM, or HIGH priority after vessel review."
                : "On rework submit, near-miss descriptions must still reach 100 characters and required report fields must be complete before vessel review can continue."}
            </p>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {!showRateLimit ? (
                <p>Rework resubmission uses the existing near-miss record.</p>
              ) : (
                <p>You can submit as many near-miss reports as needed.</p>
              )}
            </div>
            <button
              className="mt-5 min-h-[44px] w-full rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
              disabled={!submitReady || submitDisabled}
              onClick={handleSubmit}
              type="button"
            >
              {submitLabel}
            </button>
          </section>

          {guidancePrompts.length > 0 ? (
            <section className="rounded-3xl border border-sky-100 bg-sky-50 p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Guidance</h2>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
                {guidancePrompts.slice(0, 5).map((prompt) => (
                  <li key={prompt.id}>{prompt.prompt_text}</li>
                ))}
              </ul>
            </section>
          ) : null}

        </aside>
      </div>
    </section>
  );
}

export default SafetyNearMissForm;
