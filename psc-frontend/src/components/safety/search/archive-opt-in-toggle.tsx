interface SafetyArchiveOptInToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export default function SafetyArchiveOptInToggle({
  checked,
  onChange,
}: SafetyArchiveOptInToggleProps) {
  return (
    <label className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
      <input
        checked={checked}
        className="mt-1 h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
      <span>
        <span className="block text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          Include archived records
        </span>
        <span className="mt-1 block leading-6">
          Opt in to records held in the soft-archive window before the retention job hard-deletes them.
        </span>
      </span>
    </label>
  );
}
