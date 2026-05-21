interface SafetyInvestigationDepthTriangleProps {
  depth: string | null | undefined;
  minimumToolsRequired: number;
}

export function SafetyInvestigationDepthTriangle({
  depth,
  minimumToolsRequired,
}: SafetyInvestigationDepthTriangleProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
        FEAT-SAF-INC-021
      </p>
      <h2 className="mt-1 text-xl font-semibold text-slate-900">
        Investigation Depth
      </h2>
      <div className="mt-4 rounded-3xl border border-sky-200 bg-sky-50 p-5">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-sky-800">
          {depth ?? "Pending depth"}
        </p>
        <p className="mt-2 text-sm text-sky-900">
          Minimum analysis tools required: {minimumToolsRequired}
        </p>
      </div>
    </section>
  );
}

export default SafetyInvestigationDepthTriangle;
