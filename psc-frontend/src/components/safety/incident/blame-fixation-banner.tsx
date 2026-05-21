interface SafetyBlameFixationBannerProps {
  blocked: boolean;
  overrideBy?: string | null;
  triggerTerms: string[];
}

export function SafetyBlameFixationBanner({
  blocked,
  overrideBy,
  triggerTerms,
}: SafetyBlameFixationBannerProps) {
  if (!blocked && !overrideBy) {
    return null;
  }

  return (
    <section
      className={`rounded-3xl border p-5 shadow-sm ${
        overrideBy
          ? "border-sky-200 bg-sky-50 text-sky-900"
          : "border-rose-300 bg-rose-50 text-rose-900"
      }`}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.2em]">
        FEAT-SAF-INC-025
      </p>
      <h2 className="mt-1 text-xl font-semibold">
        Blame-Fixation {overrideBy ? "Override" : "Hard Block"}
      </h2>
      <p className="mt-3 text-sm">
        {overrideBy
          ? `Override already recorded by ${overrideBy}.`
          : "The analysis language or root-cause pattern is clustering around blame-only conclusions."}
      </p>
      {triggerTerms.length > 0 ? (
        <p className="mt-2 text-sm">
          Trigger terms: {triggerTerms.join(", ")}
        </p>
      ) : null}
    </section>
  );
}

export default SafetyBlameFixationBanner;
