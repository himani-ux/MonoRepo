interface SafetyCargoSpecificOverlayProps {
  items: Array<{ code: string; status: string }>;
}

export function SafetyCargoSpecificOverlay({
  items,
}: SafetyCargoSpecificOverlayProps) {
  return (
    <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-700">
        Cargo evidence
      </p>
      <h2 className="mt-1 text-xl font-semibold text-amber-950">
        Cargo-Specific Evidence
      </h2>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {items.length > 0 ? (
          items.map((item) => (
            <div
              key={`${item.code}-${item.status}`}
              className="rounded-2xl border border-amber-200 bg-white/70 p-3 text-sm text-amber-900"
            >
              <span className="font-medium">{item.code}</span>
              <span className="ml-2 text-amber-700">{item.status}</span>
            </div>
          ))
        ) : (
          <p className="text-sm text-amber-800">No cargo evidence prompts are active.</p>
        )}
      </div>
    </section>
  );
}

export default SafetyCargoSpecificOverlay;
