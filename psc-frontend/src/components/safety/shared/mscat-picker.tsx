interface SafetyMScatPickerProps {
  query: string;
  results: Array<{
    category_name: string;
    mscat_description: string;
    mscat_subcode_id: string;
  }>;
}

export function SafetyMScatPicker({
  query,
  results,
}: SafetyMScatPickerProps) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            FEAT-SAF-INC-017
          </p>
          <h2 className="text-xl font-semibold text-slate-900">M-SCAT Picker</h2>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
          Search: {query}
        </span>
      </div>
      <div className="mt-4 space-y-3">
        {results.map((result) => (
          <article
            key={result.mscat_subcode_id}
            className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium uppercase text-slate-700">
                {result.mscat_subcode_id}
              </span>
              <span className="text-sm font-medium text-slate-700">
                {result.category_name}
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-900">{result.mscat_description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export default SafetyMScatPicker;
