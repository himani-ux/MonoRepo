interface SafetyRepeatFindingBadgeProps {
  badgeText?: string | null;
  occurrenceCount?: number | null;
}

export default function SafetyRepeatFindingBadge({
  badgeText,
  occurrenceCount,
}: SafetyRepeatFindingBadgeProps) {
  if (!badgeText || !occurrenceCount || occurrenceCount < 2) {
    return null;
  }

  return (
    <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-amber-900">
      {badgeText}
    </span>
  );
}
