import SafetySignatureBlock from "../shared/signature-block";
import type { SafetyIncidentPhase7Preflight } from "../../../schemas/safety/incident-phase7";

interface SafetyDpaAcceptancePanelProps {
  preflight: SafetyIncidentPhase7Preflight;
}

function formatBlockerLabel(value: string) {
  return value.replace(/_/g, " ");
}

export default function SafetyDpaAcceptancePanel({
  preflight,
}: SafetyDpaAcceptancePanelProps) {
  const signatureEntries = Object.entries(preflight.signature_chain_status);

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
              Phase 7
            </p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-900">
              DPA Acceptance / Report Issued
            </h2>
            <p className="mt-3 max-w-3xl text-sm text-slate-600">
              Workspace-safe Phase 7 preflight showing recommendation completeness, signature sequencing, and the current report-preview dependency.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            Closer: <span className="font-semibold text-slate-900">{preflight.closer_role}</span>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Bias Guards
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {preflight.bias_guards_resolved ? "Resolved" : "Blocked"}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Root Causes
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {preflight.root_count}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            ALARP
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {preflight.alarp_complete ? "Complete" : "Incomplete"}
          </p>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
            Process ID
          </p>
          <p className="mt-2 text-lg font-semibold text-slate-900">
            {preflight.required_process_id}
          </p>
        </article>
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
        <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900">Preflight Blockers</h3>
          {preflight.blockers.length === 0 ? (
            <p className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
              This workspace preflight is clear. The formal PDF renderer is available for the Phase 7 to Phase 8 close path.
            </p>
          ) : (
            <ul className="space-y-2 text-sm text-slate-700">
              {preflight.blockers.map((blocker) => (
                <li
                  key={blocker}
                  className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 capitalize text-amber-900"
                >
                  {formatBlockerLabel(blocker)}
                </li>
              ))}
            </ul>
          )}

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
            <p className="font-semibold text-slate-900">Draft PDF Preview</p>
            <p className="mt-2">{preflight.pdf_preview.message}</p>
            {preflight.pdf_preview.download_path ? (
              <p className="mt-2 text-xs text-slate-500">
                Download route: {preflight.pdf_preview.download_path}
              </p>
            ) : null}
          </div>
        </div>

        <div className="space-y-4">
          {signatureEntries.map(([role, status]) => (
            <SafetySignatureBlock
              key={role}
              role={role as "reporter" | "master" | "hod" | "dpa" | "fm" | "pic"}
              mode="display"
              awaitingLabel={
                status.present
                  ? "Signature requirement satisfied in the current workspace."
                  : "Awaiting required signature before the closer can issue the report."
              }
            />
          ))}
        </div>
      </section>
    </div>
  );
}
