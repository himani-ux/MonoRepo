interface SafetyAnonymityBadgeProps {
  masked: boolean;
}

export function SafetyAnonymityBadge({ masked }: SafetyAnonymityBadgeProps) {
  const label = masked ? "Reporter identity masked" : "Reporter identity visible";

  return (
    <span
      aria-label={label}
      className={
        masked
          ? "inline-flex items-center rounded-full border border-slate-300 bg-slate-100 px-2.5 py-1 text-xs font-medium uppercase tracking-[0.16em] text-slate-700"
          : "inline-flex items-center rounded-full border border-sky-300 bg-sky-50 px-2.5 py-1 text-xs font-medium uppercase tracking-[0.16em] text-sky-700"
      }
    >
      <span
        aria-hidden="true"
        className={
          masked
            ? "mr-2 inline-block h-2.5 w-2.5 rounded-full bg-slate-500"
            : "mr-2 inline-block h-2.5 w-2.5 rounded-full bg-sky-500"
        }
      />
      {masked ? "Masked" : "Visible"}
    </span>
  );
}

export default SafetyAnonymityBadge;
