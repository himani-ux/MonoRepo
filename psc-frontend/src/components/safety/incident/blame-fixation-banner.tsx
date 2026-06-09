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
        Analysis review
      </p>
      <h2 className="mt-1 text-xl font-semibold">
        {overrideBy ? "Review accepted" : "Review required"}
      </h2>
      <p className="mt-3 text-sm">
        {overrideBy
          ? `Approval already recorded by ${overrideBy}.`
          : "The analysis is focusing too much on individual blame. Add system or process causes, or record an approved reason."}
      </p>
      {triggerTerms.length > 0 ? (
        <p className="mt-2 text-sm">
          Words to review: {triggerTerms.join(", ")}
        </p>
      ) : null}
    </section>
  );
}

export default SafetyBlameFixationBanner;
