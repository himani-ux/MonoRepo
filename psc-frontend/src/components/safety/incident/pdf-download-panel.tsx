interface SafetyIncidentPdfDownloadPanelProps {
  incidentNumber: string;
  generatedAt: string;
  riskBand: "GREEN" | "YELLOW" | "RED";
  sections: string[];
  signatures: string[];
}

export default function SafetyIncidentPdfDownloadPanel({
  incidentNumber,
  generatedAt,
  riskBand,
  sections,
  signatures,
}: SafetyIncidentPdfDownloadPanelProps) {
  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <header className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Formal Export
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">
            Incident 10-Section PDF
          </h2>
          <p className="mt-3 max-w-3xl text-sm text-slate-600">
            Step 6.1 formal report surface for the internal D-PDF-01 incident export. The
            real backend route now emits the file from `/api/safety/incidents/:id/pdf/`.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <div>
            Incident: <span className="font-semibold text-slate-900">{incidentNumber}</span>
          </div>
          <div className="mt-1">
            Band: <span className="font-semibold text-slate-900">{riskBand}</span>
          </div>
          <div className="mt-1 text-xs text-slate-500">Generated {generatedAt}</div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
            Included Sections
          </h3>
          <ul className="mt-4 space-y-2 text-sm text-slate-700">
            {sections.map((section) => (
              <li
                key={section}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
              >
                {section}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
            Signature Rows
          </h3>
          <ul className="mt-4 space-y-2 text-sm text-slate-700">
            {signatures.map((signature) => (
              <li
                key={signature}
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3"
              >
                {signature}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
