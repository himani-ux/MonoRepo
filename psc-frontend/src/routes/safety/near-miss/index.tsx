import { useState } from "react";
import { Link } from "react-router-dom";

import { SafetyAnonymityBadge } from "../../../components/safety/shared/anonymity-badge";
import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import { useSafetyNearMisses } from "../../../hooks/use-safety";
import { getErrorMessage } from "../../../lib/api/client";
import { formatVesselName } from "../../../lib/safety/vessel-display";

function canSeeReporter(role: string | null) {
  const normalizedRole = (role ?? "").trim().toUpperCase();
  return normalizedRole === "DPA" || normalizedRole === "FM";
}

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

export default function SafetyNearMissIndexRoute() {
  const auth = useSafetyAuth();
  const reporterVisible = canSeeReporter(auth.role);
  const canCreate = auth.hasProcess("SAF_P_001");
  const [priority, setPriority] = useState("");
  const [state, setState] = useState("");
  const nearMissQuery = useSafetyNearMisses({
    priority: priority || undefined,
    state: state || undefined,
    vessel_id: auth.isGlobal ? undefined : auth.vesselIds[0],
  });

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#eff6ff_0%,#ffffff_55%,#fef3c7_100%)] p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Safety / Near Miss
            </p>
            <h1 className="text-3xl font-semibold text-slate-900">
              Near Miss Register
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-slate-600">
              Live near-miss records with API-enforced reporter masking for non-DPA/FM viewers.
            </p>
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
            <p className="mt-1 text-sm text-slate-600">
              Results are loaded from the live near-miss list endpoint.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <select
              className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900"
              onChange={(event) => setPriority(event.target.value)}
              value={priority}
            >
              <option value="">All priorities</option>
              <option value="LOW">Low</option>
              <option value="HIGH">High</option>
            </select>
            <select
              className="rounded-2xl border border-slate-300 bg-white px-4 py-2 text-sm text-slate-900"
              onChange={(event) => setState(event.target.value)}
              value={state}
            >
              <option value="">All states</option>
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="TRIAGED">Triaged</option>
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
        ) : nearMissQuery.data && nearMissQuery.data.length > 0 ? (
          <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200">
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
                {nearMissQuery.data.map((nearMiss) => (
                  <tr key={nearMiss.id}>
                    <td className="px-4 py-4 text-slate-900">
                      <Link
                        className="font-medium hover:text-slate-600 hover:underline"
                        to={`/safety/near-miss/${nearMiss.public_id ?? nearMiss.id}`}
                      >
                        {nearMiss.incident_number || `Near Miss #${nearMiss.id}`}
                      </Link>
                    </td>
                    <td className="px-4 py-4 text-slate-600">{formatVesselName(nearMiss)}</td>
                    <td className="px-4 py-4 text-slate-600">{formatDateTime(nearMiss.occurred_at || nearMiss.reported_at)}</td>
                    <td className="px-4 py-4">
                      <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
                        {nearMiss.near_miss_priority || "Pending triage"}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-slate-700">
                          {nearMiss.reporter_name || (reporterVisible ? "Reporter hidden by source data" : "Anonymous Reporter")}
                        </span>
                        <SafetyAnonymityBadge masked={!reporterVisible} />
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-600">{nearMiss.state}</td>
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
