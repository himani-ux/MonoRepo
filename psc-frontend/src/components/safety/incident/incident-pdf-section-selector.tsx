export const INCIDENT_PDF_SECTION_OPTIONS = [
  { key: "summary", label: "Summary" },
  { key: "reporter_details", label: "Reporter Details" },
  { key: "injury_details", label: "Injury Details" },
  { key: "estimated_cost", label: "Estimated Cost" },
  { key: "root_cause", label: "Root Cause" },
  { key: "evidence_documents", label: "Evidence (Documents)" },
  { key: "corrective_preventive_actions", label: "Corrective and Preventive Actions" },
  { key: "signature", label: "Signature" },
] as const;

export type IncidentPdfSectionKey = (typeof INCIDENT_PDF_SECTION_OPTIONS)[number]["key"];

export const DEFAULT_INCIDENT_PDF_SECTION_KEYS = INCIDENT_PDF_SECTION_OPTIONS.map(
  (option) => option.key,
) as IncidentPdfSectionKey[];

export function IncidentPdfSectionSelector({
  disabled,
  onChange,
  value,
}: {
  disabled?: boolean;
  onChange: (nextValue: IncidentPdfSectionKey[]) => void;
  value: IncidentPdfSectionKey[];
}) {
  function toggleSection(sectionKey: IncidentPdfSectionKey, checked: boolean) {
    if (checked) {
      onChange(Array.from(new Set([...value, sectionKey])));
      return;
    }
    onChange(value.filter((selectedKey) => selectedKey !== sectionKey));
  }

  return (
    <fieldset className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <legend className="text-lg font-semibold text-slate-900">Select PDF content</legend>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Choose the sections to include in the exported PDF. All sections are selected by default.
      </p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {INCIDENT_PDF_SECTION_OPTIONS.map((option) => (
          <label
            className="flex min-h-11 items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-800"
            key={option.key}
          >
            <input
              checked={value.includes(option.key)}
              className="h-4 w-4 rounded border-slate-300"
              disabled={disabled}
              onChange={(event) => toggleSection(option.key, event.target.checked)}
              type="checkbox"
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
