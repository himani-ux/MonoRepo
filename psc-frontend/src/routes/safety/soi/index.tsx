import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import SafetySoiCompliancePill from "../../../components/safety/shared/soi-compliance-pill";
import { formatSoiCrewDisplay } from "../../../components/safety/soi/crew-display";
import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import { useSafetySoiCompliance, useSafetySoiInspections } from "../../../hooks/use-safety";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi, type SafetySoiOfficerSetting } from "../../../lib/api/safety";

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-slate-900">{value}</div>
    </article>
  );
}

function formatDate(value: string | null) {
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

function canDownloadPaper(state: string) {
  return state !== "CLOSED";
}

function canCloseInspection(state: string) {
  return state === "REPORTED" || state === "CLOSED";
}

function normalizeSafetyRole(role: string | null | undefined) {
  return (role ?? "").trim().toUpperCase();
}

function resolveCurrentUserIds(user: ReturnType<typeof useSafetyAuth>["user"]) {
  const candidates = [
    user?.crewId,
    user?.employeeId,
    user?.login_id,
    user?.id,
    user?.userName,
  ];
  return new Set(
    candidates
      .map((value) => String(value ?? "").trim())
      .filter(Boolean),
  );
}

function isDefaultSafetyOfficerRole(role: string | null | undefined) {
  const normalized = normalizeSafetyRole(role);
  return new Set(["CO", "CHIEF OFFICER", "SO", "SAFETY OFFICER"]).has(normalized);
}

function isAlternateSafetyOfficerRole(role: string | null | undefined) {
  const normalized = normalizeSafetyRole(role);
  return new Set(["2E", "2/E", "SECOND ENGINEER"]).has(normalized);
}

function formatSoiState(state: string) {
  const labels: Record<string, string> = {
    CLOSED: "Closed",
    DOWNLOADED: "Downloaded",
    IN_FIELDWORK: "Fieldwork",
    PLANNED: "Ready to Download",
    REPORTED: "Submitted",
  };
  return labels[state] ?? state;
}

function isSafetyOfficerRole(role: string | null | undefined) {
  const normalized = (role ?? "").trim().toUpperCase();
  return new Set(["CO", "CHIEF OFFICER", "SO", "SAFETY OFFICER", "2E", "2/E", "SECOND ENGINEER"]).has(normalized);
}

function MasterAlternateOfficerPanel({
  enabled,
  vesselId,
}: {
  enabled: boolean;
  vesselId: string | null;
}) {
  const queryClient = useQueryClient();
  const [alternateEnabled, setAlternateEnabled] = useState(false);
  const [alternateCrewId, setAlternateCrewId] = useState("");
  const [reason, setReason] = useState("");
  const settingQuery = useQuery({
    queryKey: ["safety", "soi", "officer-setting", vesselId],
    queryFn: () => safetyApi.getSoiOfficerSetting(vesselId),
    enabled: enabled && Boolean(vesselId),
    staleTime: 30_000,
  });
  const updateMutation = useMutation({
    mutationFn: () =>
      safetyApi.updateSoiOfficerSetting(
        {
          alternate_enabled: alternateEnabled,
          alternate_so_crew_id: alternateEnabled ? alternateCrewId : null,
          reason,
        },
        vesselId,
      ),
    onSuccess: async (setting) => {
      setAlternateEnabled(setting.alternate_enabled);
      setAlternateCrewId(setting.alternate_so_crew_id ?? "");
      setReason(setting.reason ?? "");
      await queryClient.invalidateQueries({ queryKey: ["safety", "soi", "officer-setting", vesselId] });
    },
  });

  useEffect(() => {
    const setting: SafetySoiOfficerSetting | undefined = settingQuery.data;
    if (!setting) {
      return;
    }
    setAlternateEnabled(setting.alternate_enabled);
    setAlternateCrewId(setting.alternate_so_crew_id ?? "");
    setReason(setting.reason ?? "");
  }, [settingQuery.data]);

  if (!enabled || !vesselId) {
    return null;
  }

  const setting = settingQuery.data;
  const candidates = setting?.alternate_candidates ?? [];
  const canSave = !updateMutation.isPending && (!alternateEnabled || Boolean(alternateCrewId));

  return (
    <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">2/E alternate Safety Officer</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            Master can enable 2/E only when CO is not available. The selected 2/E can then create and handle SOI work for this vessel.
          </p>
        </div>
        {setting ? (
          <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${
            setting.alternate_enabled ? "bg-emerald-100 text-emerald-900" : "bg-slate-100 text-slate-700"
          }`}
          >
            {setting.alternate_enabled ? "Enabled" : "Disabled"}
          </span>
        ) : null}
      </div>

      {settingQuery.isLoading ? (
        <div className="mt-4 h-16 animate-pulse rounded-2xl bg-slate-100" />
      ) : settingQuery.isError ? (
        <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {getErrorMessage(settingQuery.error)}
        </div>
      ) : setting?.migration_required ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {setting.message ?? "Run Safety migrations to enable this setting."}
        </div>
      ) : (
        <div className="mt-5 grid gap-4 lg:grid-cols-[180px_minmax(0,1fr)_minmax(0,1fr)_auto] lg:items-end">
          <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-800">
            <input
              checked={alternateEnabled}
              className="h-4 w-4 rounded border-slate-300"
              onChange={(event) => setAlternateEnabled(event.target.checked)}
              type="checkbox"
            />
            Enable 2/E
          </label>
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Active 2/E</span>
            <select
              className="min-h-[44px] w-full rounded-2xl border border-slate-300 bg-white px-3 py-2 text-slate-900 disabled:bg-slate-100 disabled:text-slate-500"
              disabled={!alternateEnabled}
              onChange={(event) => setAlternateCrewId(event.target.value)}
              value={alternateCrewId}
            >
              <option value="">Select active 2/E</option>
              {candidates.map((candidate) => (
                <option key={candidate.crew_id} value={candidate.crew_id}>
                  {formatSoiCrewDisplay(candidate)}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Reason</span>
            <input
              className="min-h-[44px] w-full rounded-2xl border border-slate-300 px-3 py-2 text-slate-900"
              onChange={(event) => setReason(event.target.value)}
              placeholder="CO on leave"
              value={reason}
            />
          </label>
          <button
            className="rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={!canSave}
            onClick={() => updateMutation.mutate()}
            type="button"
          >
            {updateMutation.isPending ? "Saving..." : "Save"}
          </button>
        </div>
      )}

      {updateMutation.isError ? (
        <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {getErrorMessage(updateMutation.error)}
        </div>
      ) : null}
      {updateMutation.isSuccess ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          Alternate Safety Officer setting saved.
        </div>
      ) : null}
    </section>
  );
}

export default function SafetySoiIndexRoute() {
  const auth = useSafetyAuth();
  const normalizedRole = normalizeSafetyRole(auth.role);
  const canClose = auth.hasProcess("SAF_P_004") && normalizedRole === "MASTER";
  const canManageAlternate = auth.hasProcess("SAF_P_016") && normalizedRole === "MASTER";
  const vesselId = auth.isGlobal ? null : auth.vesselIds[0] ?? null;
  const officerSettingQuery = useQuery({
    queryKey: ["safety", "soi", "officer-setting", vesselId],
    queryFn: () => safetyApi.getSoiOfficerSetting(vesselId),
    enabled: Boolean(vesselId) && isSafetyOfficerRole(auth.role),
    staleTime: 30_000,
  });
  const currentUserIds = resolveCurrentUserIds(auth.user);
  const canCreate = auth.hasProcess("SAF_P_001")
    && (
      isDefaultSafetyOfficerRole(auth.role)
      || (
        isAlternateSafetyOfficerRole(auth.role)
        && officerSettingQuery.data?.alternate_enabled
        && currentUserIds.has(String(officerSettingQuery.data.alternate_so_crew_id ?? "").trim())
      )
    );
  const complianceQuery = useSafetySoiCompliance(vesselId);
  const inspectionsQuery = useSafetySoiInspections({
    vessel_id: vesselId ?? undefined,
  });

  return (
    <section className="space-y-6">
      <section className="rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_right,_rgba(251,191,36,0.22),_transparent_30%),linear-gradient(135deg,_#ffffff,_#f8fafc)] p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Safety Officer Inspection</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Live SOI compliance summary and inspection register for the current vessel scope.
            </p>
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            SCM sign-off blockers and dashboard compliance now read from the same SOI backend records.
          </div>
        </div>
        {canCreate ? (
          <div className="mt-4">
            <Link
              className="inline-flex rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
              to="/safety/soi/create"
            >
              Start inspection
            </Link>
          </div>
        ) : null}
      </section>

      {complianceQuery.isLoading ? (
        <div className="grid gap-3 sm:grid-cols-3" role="status">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-28 animate-pulse rounded-2xl bg-slate-100" />
          ))}
        </div>
      ) : complianceQuery.error ? (
        <section className="rounded-[1.75rem] border border-rose-200 bg-rose-50 p-5 shadow-sm text-sm text-rose-700">
          {complianceQuery.error.message}
        </section>
      ) : complianceQuery.data ? (
        <section className="grid gap-3 sm:grid-cols-3">
          <SafetySoiCompliancePill
            applicableAreaCount={complianceQuery.data.applicable_area_count}
            displayValue={complianceQuery.data.display_value}
            inspectedAreaCount={complianceQuery.data.inspected_area_count}
            label={complianceQuery.data.label}
            note={`The compliance engine currently tracks ${complianceQuery.data.areas.length} area row(s) in scope.`}
            status={complianceQuery.data.status as "GREEN" | "AMBER" | "RED" | "NA"}
          />
          <MetricCard label="Amber watch" value={String(complianceQuery.data.amber_area_count)} />
          <MetricCard label="Areas overdue" value={String(complianceQuery.data.overdue_area_count)} />
        </section>
      ) : null}

      <MasterAlternateOfficerPanel enabled={canManageAlternate} vesselId={vesselId} />

      <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Current SOI register</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Inspection register now reads directly from <code>/api/safety/soi/</code>.
            </p>
          </div>
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-amber-900">
            Live register
          </span>
        </div>

        {inspectionsQuery.isLoading ? (
          <div className="mt-5 space-y-3" role="status">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-16 animate-pulse rounded-2xl bg-slate-100" />
            ))}
          </div>
        ) : inspectionsQuery.error ? (
          <div className="mt-5 rounded-3xl border border-rose-200 bg-rose-50 px-4 py-5 text-sm text-rose-700">
            {inspectionsQuery.error.message}
          </div>
        ) : inspectionsQuery.data && inspectionsQuery.data.length > 0 ? (
          <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Reference</th>
                  <th className="px-4 py-3 font-medium">Planned date</th>
                  <th className="px-4 py-3 font-medium">Areas</th>
                  <th className="px-4 py-3 font-medium">Assistant</th>
                  <th className="px-4 py-3 font-medium">Trainees</th>
                  <th className="px-4 py-3 font-medium">State</th>
                  <th className="px-4 py-3 font-medium">Next step</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {inspectionsQuery.data.map((item) => (
                  <tr key={item.id}>
                    <td className="px-4 py-4">
                      <Link
                        className="font-medium text-slate-900 hover:text-slate-600 hover:underline"
                        to={`/safety/soi/${item.id}/findings`}
                      >
                        {item.inspection_reference}
                      </Link>
                      <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                        Inspection #{item.id}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-700">{formatDate(item.planned_date)}</td>
                    <td className="px-4 py-4 text-slate-700">{item.selected_areas.length}</td>
                    <td className="px-4 py-4 text-slate-700">{item.assistant_crew_id}</td>
                    <td className="px-4 py-4 text-slate-700">{item.trainees.length}</td>
                    <td className="px-4 py-4">
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                        {formatSoiState(item.state)}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-wrap gap-2">
                        {canCreate && canDownloadPaper(item.state) ? (
                          <Link
                            className="inline-flex items-center rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-slate-800 transition hover:border-slate-400 hover:bg-slate-100"
                            to={`/safety/soi/${item.id}/download`}
                          >
                            Download paper
                          </Link>
                        ) : null}
                        <Link
                          className="inline-flex items-center rounded-full border border-sky-300 bg-sky-50 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-sky-900 transition hover:border-sky-400 hover:bg-sky-100"
                          to={`/safety/soi/${item.id}/findings`}
                        >
                          Findings
                        </Link>
                        {canClose && canCloseInspection(item.state) ? (
                          <Link
                            className="inline-flex items-center rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-emerald-900 transition hover:border-emerald-400 hover:bg-emerald-100"
                            to={`/safety/soi/${item.id}/close`}
                          >
                            {item.state === "CLOSED" ? "View close" : "Close event"}
                          </Link>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600">
            No SOI inspections are available in the current scope.
          </div>
        )}
      </section>
    </section>
  );
}
