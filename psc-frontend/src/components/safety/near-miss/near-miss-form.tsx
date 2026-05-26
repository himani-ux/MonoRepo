import { useEffect, useState } from "react";

import {
  SAFETY_NEAR_MISS_SCHEMA_VERSION,
  type SafetyNearMissSubmitValues,
  type SafetyNearMissValues,
  safetyNearMissSubmitSchema,
} from "../../../schemas/safety/near-miss";
import { useAuth } from "../../../hooks/use-auth";
import { toUtcIsoTimestamp } from "../../../hooks/safety/use-msc-mepc3-position";
import { safetyApi, type SafetyNearMissRateLimitStatus } from "../../../lib/api/safety";
import { getSafetyDeviceFingerprint } from "../../../lib/safety/digital-signature";
import {
  SafetyIncidentTypeSelect,
  SafetyLossTypeSelect,
  SafetyMscatPicker,
} from "../shared/reference-pickers";

interface SafetyNearMissFormProps {
  initialValues?: Partial<SafetyNearMissValues>;
  onSubmit?: (values: SafetyNearMissSubmitValues) => void;
}

const defaultValues: SafetyNearMissValues = {
  incident_type_id: null,
  loss_type_primary_id: null,
  narrative: "",
  near_miss_immediate_action: "",
  near_miss_mscat_category_id: null,
  near_miss_mscat_subcode_id: null,
  near_miss_severity: null,
  near_miss_shell_tag: null,
  near_miss_suggestion: "",
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

export function SafetyNearMissForm({
  initialValues,
  onSubmit,
}: SafetyNearMissFormProps) {
  const { isVessel, user } = useAuth();
  const [values, setValues] = useState<SafetyNearMissValues>({
    ...defaultValues,
    ...initialValues,
  });
  const [rateLimitStatus, setRateLimitStatus] = useState<SafetyNearMissRateLimitStatus | null>(null);
  const [rateLimitError, setRateLimitError] = useState<string | null>(null);
  const [rateLimitLoading, setRateLimitLoading] = useState(false);

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
  const submissionBlockedByRateLimit = rateLimitStatus?.allowed === false;

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
    const vesselId = values.vessel_id || vesselIdFromAuth;
    if (!vesselId) {
      return;
    }

    let cancelled = false;
    setRateLimitLoading(true);
    setRateLimitError(null);

    safetyApi
      .getNearMissRateLimit({ vessel_id: vesselId })
      .then((status) => {
        if (!cancelled) {
          setRateLimitStatus(status);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRateLimitStatus(null);
          setRateLimitError("Unable to load near-miss submission allowance. Backend will still enforce the limit.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setRateLimitLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [values.vessel_id, vesselIdFromAuth]);

  function updateField<K extends keyof SafetyNearMissValues>(
    field: K,
    nextValue: SafetyNearMissValues[K],
  ) {
    setValues((current) => ({ ...current, [field]: nextValue }));
  }

  function handleSubmit() {
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
          Create Near Miss
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Any rank may submit a near miss. Reporter identity is protected and is visible only to authorized office users.
        </p>
      </header>

      <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Anonymity Boundary</h2>
        <p className="mt-2 text-sm leading-6 text-slate-700">
          Master, HOD, and other non-DPA/FM viewers will see
          {" "}
          <span className="font-semibold">Anonymous Reporter</span>
          {" "}
          instead of the stored reporter identity.
        </p>
      </section>

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
            <span className="block text-xs leading-5 text-slate-500">
              Required. Future occurrence times are not allowed.
            </span>
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
              <span className="font-medium">SHELL tag</span>
              <select
                aria-label="SHELL tag"
                className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                onChange={(event) =>
                  updateField(
                    "near_miss_shell_tag",
                    (event.target.value || null) as SafetyNearMissValues["near_miss_shell_tag"],
                  )
                }
                value={values.near_miss_shell_tag ?? ""}
              >
                <option value="">Select SHELL tag</option>
                <option value="Software">Software</option>
                <option value="Hardware">Hardware</option>
                <option value="Environment">Environment</option>
                <option value="Liveware">Liveware</option>
                <option value="Liveware-Liveware">Liveware-Liveware</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Incident type</span>
              <SafetyIncidentTypeSelect
                onChange={(nextValue) => updateField("incident_type_id", nextValue)}
                value={values.incident_type_id ?? null}
              />
            </label>
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Loss type</span>
              <SafetyLossTypeSelect
                label="Loss type"
                onChange={(nextValue) => updateField("loss_type_primary_id", nextValue)}
                value={values.loss_type_primary_id ?? null}
              />
            </label>
          </div>

          <label className="block space-y-2 text-sm text-slate-700">
            <span className="font-medium">M-SCAT code</span>
            <SafetyMscatPicker
              onChange={(nextValue) => {
                updateField("near_miss_mscat_category_id", nextValue.categoryId);
                updateField("near_miss_mscat_subcode_id", nextValue.subcodeId);
              }}
              value={{
                categoryId: values.near_miss_mscat_category_id,
                subcodeId: values.near_miss_mscat_subcode_id,
              }}
            />
          </label>

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
            <span className="font-medium">Suggestion</span>
            <textarea
              aria-label="Suggestion"
              className="min-h-[120px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
              onChange={(event) => updateField("near_miss_suggestion", event.target.value)}
              value={values.near_miss_suggestion}
            />
          </label>
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
              On submit, near-miss descriptions must
              reach 100 characters, and each crew member is capped at 5 submissions per
              vessel-local day with reset guidance at 00:00 LT. DPA triage assigns
              LOW or HIGH priority after submission.
            </p>
            <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
              {rateLimitLoading ? (
                <p>Checking near-miss submission allowance...</p>
              ) : rateLimitStatus ? (
                <p>
                  {rateLimitStatus.remaining} of {rateLimitStatus.limit} submissions remain in the current window.
                  {" "}
                  {rateLimitStatus.guidance_message}
                </p>
              ) : (
                <p>{rateLimitError ?? "Submission allowance will be checked before submit."}</p>
              )}
            </div>
            <button
              className="mt-5 min-h-[44px] w-full rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:bg-slate-300"
              disabled={!submitReady || rateLimitLoading || submissionBlockedByRateLimit}
              onClick={handleSubmit}
              type="button"
            >
              Submit near miss
            </button>
          </section>
        </aside>
      </div>
    </section>
  );
}

export default SafetyNearMissForm;
