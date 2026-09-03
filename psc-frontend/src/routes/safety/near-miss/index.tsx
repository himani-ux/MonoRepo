import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import { useSafetyIncidentRegisterVessels, useSafetyNearMisses } from "../../../hooks/use-safety";
import { getErrorMessage } from "../../../lib/api/client";
import { formatVesselName } from "../../../lib/safety/vessel-display";

function formatDateTime(value: string | null) {
  if (!value) {
    return "Not recorded";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("en-US", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatNearMissState(value: unknown) {
  const state = String(value ?? "").trim().toUpperCase();
  switch (state) {
    case "READY_FOR_OFFICE_COMMENTS":
      return "Ready for Office Comments";
    case "OFFICE_COMMENTS_COMPLETED":
      return "Office Comments Completed";
    case "PENDING_VESSEL_REVIEW":
      return "Pending Vessel Review";
    case "REWORK_REQUIRED":
      return "Rework Required";
    default:
      return state ? state.replace(/_/g, " ") : "Not recorded";
  }
}

function formatNearMissPriority(value: unknown) {
  const priority = String(value ?? "").trim().toUpperCase();
  switch (priority) {
    case "HIGH":
      return "High";
    case "MED":
    case "MEDIUM":
      return "Medium";
    case "LOW":
      return "Low";
    default:
      return priority ? priority.replace(/_/g, " ") : "Pending office comments";
  }
}

function getNearMissPriorityBadgeClass(value: unknown) {
  const priority = String(value ?? "").trim().toUpperCase();
  const base = "inline-flex rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset";
  switch (priority) {
    case "HIGH":
      return `${base} bg-rose-50 text-rose-700 ring-rose-200`;
    case "MED":
    case "MEDIUM":
      return `${base} bg-amber-50 text-amber-700 ring-amber-200`;
    case "LOW":
      return `${base} bg-emerald-50 text-emerald-700 ring-emerald-200`;
    default:
      return `${base} bg-slate-100 text-slate-600 ring-slate-200`;
  }
}

function buildVesselOptionLabel(vessel: {
  id: string;
  vessel_code?: string | null;
  vessel_name?: string | null;
}) {
  return [vessel.vessel_code, vessel.vessel_name].filter(Boolean).join(" - ") || vessel.id;
}

function hasDraftReferencePrefix(value: unknown) {
  return String(value ?? "").trim().toUpperCase().startsWith("DRAFT-");
}

export default function SafetyNearMissIndexRoute() {
  const auth = useSafetyAuth();
  const canCreate = auth.hasProcess("SAF_P_001");
  const [priority, setPriority] = useState("");
  const [state, setState] = useState("");
  const [selectedVesselId, setSelectedVesselId] = useState("");
  const vesselOptionsQuery = useSafetyIncidentRegisterVessels();
  const authVesselOptions = useMemo(
    () =>
      auth.vesselIds.map((vesselId, index) => ({
        id: String(vesselId),
        vessel_code: "",
        vessel_name: auth.vesselNames[index] ?? String(vesselId),
      })),
    [auth.vesselIds, auth.vesselNames]
  );
  const vesselOptions =
    vesselOptionsQuery.data && vesselOptionsQuery.data.length > 0
      ? vesselOptionsQuery.data
      : authVesselOptions;
  const effectiveVesselId = auth.isGlobal
    ? selectedVesselId || undefined
    : auth.vesselIds[0] ? String(auth.vesselIds[0]) : undefined;
  const isDraftReferenceFilter = state === "DRAFT";
  const nearMissQuery = useSafetyNearMisses({
    priority: priority || undefined,
    state: isDraftReferenceFilter ? undefined : state || undefined,
    vessel_id: effectiveVesselId,
  });
  const visibleNearMisses = useMemo(() => {
    const records = nearMissQuery.data ?? [];
    if (!isDraftReferenceFilter) {
      return records;
    }
    return records.filter((nearMiss) => hasDraftReferencePrefix(nearMiss.incident_number));
  }, [isDraftReferenceFilter, nearMissQuery.data]);

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#eff6ff_0%,#ffffff_55%,#fef3c7_100%)] p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <h1 className="text-3xl font-semibold text-slate-900">
              Near Miss Register
            </h1>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm">
            <div>Scoped vessels: {auth.scopedVesselLabel}</div>
            <div>Role: {auth.role ?? "Unknown"}</div>
          </div>
        </div>
        {canCreate ? (
          <div className="mt-4">
            <Link
              className="inline-flex rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
              to="/safety/near-miss/create"
            >
              Report near miss
            </Link>
          </div>
        ) : null}
      </header>

      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Current register</h2>
          </div>
          <div className="flex flex-wrap gap-3">
            {auth.isGlobal ? (
              <select
                aria-label="Near miss vessel filter"
                className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900"
                disabled={vesselOptionsQuery.isLoading && vesselOptions.length === 0}
                onChange={(event) => setSelectedVesselId(event.target.value)}
                value={selectedVesselId}
              >
                <option value="">All vessels</option>
                {vesselOptions.map((vessel) => (
                  <option key={vessel.id} value={vessel.id}>
                    {buildVesselOptionLabel(vessel)}
                  </option>
                ))}
              </select>
            ) : null}
            <select
              aria-label="Near miss priority filter"
              className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900"
              onChange={(event) => setPriority(event.target.value)}
              value={priority}
            >
              <option value="">All priorities</option>
              <option value="LOW">Low</option>
              <option value="HIGH">High</option>
            </select>
            <select
              aria-label="Near miss state filter"
              className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900"
              onChange={(event) => setState(event.target.value)}
              value={state}
            >
              <option value="">All states</option>
              <option value="DRAFT">Draft</option>
              <option value="PENDING_VESSEL_REVIEW">Pending Vessel Review</option>
              <option value="READY_FOR_OFFICE_COMMENTS">Ready for Office Comments</option>
              <option value="REWORK_REQUIRED">Rework Required</option>
              <option value="REJECTED">Rejected</option>
              <option value="OFFICE_COMMENTS_COMPLETED">Office Comments Completed</option>
              <option value="SUPERSEDED">Superseded</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>
        </div>

        {nearMissQuery.isLoading ? (
          <div className="mt-5 space-y-3" role="status">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-16 animate-pulse rounded-2xl bg-slate-100" />
            ))}
          </div>
        ) : nearMissQuery.error ? (
          <div className="mt-5 rounded-3xl border border-rose-200 bg-rose-50 px-4 py-5 text-sm text-rose-700">
            {getErrorMessage(nearMissQuery.error)}
          </div>
        ) : visibleNearMisses.length > 0 ? (
          <div
            className="mt-5 max-h-[65vh] overflow-auto rounded-3xl border border-slate-200 [scrollbar-gutter:stable]"
            data-testid="near-miss-register-scroll-region"
          >
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-3 font-medium">Ref</th>
                  <th className="px-4 py-3 font-medium">Vessel</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                  <th className="px-4 py-3 font-medium">Priority</th>
                  <th className="px-4 py-3 font-medium">Reporter</th>
                  <th className="px-4 py-3 font-medium">State</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {visibleNearMisses.map((nearMiss) => (
                  <tr key={nearMiss.id}>
                    <td className="px-4 py-4 text-slate-900">
                      <Link
                        className="font-medium hover:text-slate-600 hover:underline"
                        to={`/safety/near-miss/${nearMiss.id}`}
                      >
                        {nearMiss.incident_number || `Near Miss #${nearMiss.id}`}
                      </Link>
                    </td>
                    <td className="px-4 py-4 text-slate-600">{formatVesselName(nearMiss)}</td>
                    <td className="px-4 py-4 text-slate-600">{formatDateTime(nearMiss.occurred_at || nearMiss.reported_at)}</td>
                    <td className="px-4 py-4">
                      <span className={getNearMissPriorityBadgeClass(nearMiss.near_miss_priority)}>
                        {formatNearMissPriority(nearMiss.near_miss_priority)}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-slate-700">
                          {nearMiss.reporter_name || "Reporter not recorded"}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-600">{formatNearMissState(nearMiss.state)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600">
            No near-miss records matched the current filters.
          </div>
        )}
      </section>
    </section>
  );
}
