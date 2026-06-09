import type { SafetyIncidentSafeguardFailure } from "../../../schemas/safety/incident-phase5";

interface SafetySafeguardFailureInterrogatoryProps {
  safeguards: SafetyIncidentSafeguardFailure[];
}

export function SafetySafeguardFailureInterrogatory({
  safeguards,
}: SafetySafeguardFailureInterrogatoryProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        Safeguard review
      </p>
      <h2 className="mt-1 text-xl font-semibold text-slate-900">
        Safeguard Failure Review
      </h2>
      <div className="mt-4 space-y-3">
        {safeguards.map((safeguard) => (
          <article
            key={safeguard.id ?? safeguard.safeguard_name}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <h3 className="text-sm font-semibold text-slate-900">
              {safeguard.safeguard_name}
            </h3>
            <div className="mt-3 grid gap-2 text-sm text-slate-600 md:grid-cols-2 xl:grid-cols-3">
              <p>Design: {safeguard.design_mscat_subcode_id}</p>
              <p>Installation: {safeguard.installation_mscat_subcode_id}</p>
              <p>Maintenance: {safeguard.maintenance_mscat_subcode_id}</p>
              <p>Operation: {safeguard.operation_mscat_subcode_id}</p>
              <p>Testing: {safeguard.testing_mscat_subcode_id}</p>
              <p>Override: {safeguard.override_mscat_subcode_id}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default SafetySafeguardFailureInterrogatory;
