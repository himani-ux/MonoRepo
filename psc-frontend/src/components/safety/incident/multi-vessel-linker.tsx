interface SafetyMultiVesselLinkerProps {
  linkedIncidentId?: number | null;
}

export function SafetyMultiVesselLinker({
  linkedIncidentId,
}: SafetyMultiVesselLinkerProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            FEAT-SAF-INC-032
          </p>
          <h2 className="text-xl font-semibold text-slate-900">Multi-vessel link</h2>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          {linkedIncidentId ? `Linked to #${linkedIncidentId}` : "Not linked"}
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-600">
        Each vessel retains its own investigation. This Phase 4 scaffold only shows the cross-link contract for the
        handover workspace.
      </p>
      <div className="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
        Link prompt shape: <span className="font-medium text-slate-900">Link to existing incident? [Yes / No - separate events]</span>
      </div>
    </section>
  );
}

export default SafetyMultiVesselLinker;
