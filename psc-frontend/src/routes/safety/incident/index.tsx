import { useState } from "react";
import { Link } from "react-router-dom";

import { useSafetyAuth } from "../../../hooks/safety/use-auth";
import { useSafetyIncidents } from "../../../hooks/use-safety";
import { getErrorMessage } from "../../../lib/api/client";
import { formatVesselName } from "../../../lib/safety/vessel-display";

const RISK_BAND_OPTIONS = [
  { label: "All bands", value: "" },
  { label: "Green", value: "GREEN" },
  { label: "Yellow", value: "YELLOW" },
  { label: "Red", value: "RED" },
] as const;

const STATE_OPTIONS = [
  { label: "All states", value: "" },
  { label: "Draft", value: "DRAFT" },
  { label: "Submitted", value: "SUBMITTED" },
  { label: "Sent Back", value: "SENT_BACK" },
  { label: "Closed", value: "CLOSED" },
] as const;

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

function buildIncidentRoute(id: number | string, phase: number) {
  const boundedPhase = Math.min(Math.max(phase || 1, 1), 9);
  if (boundedPhase === 3) {
    return `/safety/incidents/${id}/phase-3/people`;
  }
  if (boundedPhase === 9) {
    return `/safety/incidents/${id}/phase-9`;
  }
  return `/safety/incidents/${id}/phase-${boundedPhase}`;
}

function canCreateIncident(role: string | null, hasProcess: boolean) {
  if (!hasProcess) {
    return false;
  }
  const normalizedRole = (role ?? "").trim().toUpperCase();
  return ["MASTER", "CO", "CE", "2E", "2/E"].includes(normalizedRole);
}

export default function SafetyIncidentIndexRoute() {
  const auth = useSafetyAuth();
  const canCreate = canCreateIncident(auth.role, auth.hasProcess("SAF_P_001"));
  const [riskBand, setRiskBand] = useState("");
  const [state, setState] = useState("");
  const incidentsQuery = useSafetyIncidents({
    record_type: "INCIDENT",
    risk_band: riskBand || undefined,
    state: state || undefined,
    vessel_id: auth.isGlobal ? undefined : auth.vesselIds[0],
  });

  return (
    <section className="space-y-6">
      <header className="rounded-3xl border border-slate-200 bg-[linear-gradient(135deg,#f8fafc_0%,#ffffff_55%,#fef3c7_100%)] p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500">
              Safety / Incidents
            </p>
            <h1 className="text-3xl font-semibold text-slate-900">
              Safety Incidents
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-slate-600">
              Live incident register filtered by your current vessel scope and Safety permissions.
            </p>
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            <div>Scoped vessels: {auth.scopedVesselLabel}</div>
            <div>Role: {auth.role ?? "Unknown"}</div>
          </div>
        </div>
        {canCreate ? (
          <div className="mt-4">
            <Link
              className="inline-flex rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
              to="/safety/incidents/create"
            >
              Report incident
            </Link>
          </div>
        ) : null}
      </header>

      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">
              Investigation Register
            </h2>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
              {incidentsQuery.data?.length ?? 0} record(s)
            </span>
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">Risk band</span>
              <select
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2"
                onChange={(event) => setRiskBand(event.target.value)}
                value={riskBand}
              >
                {RISK_BAND_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2 text-sm text-slate-700">
              <span className="font-medium">State</span>
              <select
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2"
                onChange={(event) => setState(event.target.value)}
                value={state}
              >
                {STATE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {incidentsQuery.isLoading ? (
            <div className="mt-5 space-y-3" role="status">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-16 animate-pulse rounded-2xl bg-slate-100" />
              ))}
            </div>
          ) : incidentsQuery.error ? (
            <div className="mt-5 rounded-3xl border border-rose-200 bg-rose-50 px-4 py-5 text-sm text-rose-700">
              {getErrorMessage(incidentsQuery.error)}
            </div>
          ) : incidentsQuery.data && incidentsQuery.data.length > 0 ? (
            <div className="mt-5 overflow-hidden rounded-3xl border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-slate-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Reference</th>
                    <th className="px-4 py-3 font-medium">Vessel</th>
                    <th className="px-4 py-3 font-medium">Occurred</th>
                    <th className="px-4 py-3 font-medium">Band</th>
                    <th className="px-4 py-3 font-medium">State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {incidentsQuery.data.map((incident) => (
                    <tr key={incident.id}>
                      <td className="px-4 py-4">
                        <Link
                          className="font-medium text-slate-900 hover:text-slate-600 hover:underline"
                          to={buildIncidentRoute(incident.id, incident.current_phase)}
                        >
                          {incident.incident_number || incident.draft_reference || `Incident #${incident.id}`}
                        </Link>
                        <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">
                          Phase {incident.current_phase}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-slate-600">{formatVesselName(incident)}</td>
                      <td className="px-4 py-4 text-slate-600">{formatDateTime(incident.occurred_at || incident.reported_at)}</td>
                      <td className="px-4 py-4">
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                          {incident.risk_band || "UNSET"}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-slate-600">{incident.state}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-sm text-slate-600">
              No incidents matched the current filters.
            </div>
          )}
        </div>

        <aside className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Current Scope
          </h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
            <li>Incident list reads directly from <code>/api/safety/incidents/</code>.</li>
            <li>Record links open the current incident phase route for each record.</li>
            <li>Risk band and state filters are applied server-side.</li>
          </ul>
        </aside>
      </div>
    </section>
  );
}
