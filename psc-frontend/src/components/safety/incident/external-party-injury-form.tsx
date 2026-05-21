export const SAFETY_EXTERNAL_PARTY_TYPES = [
  "PILOT",
  "SHIPYARD",
  "STEVEDORE",
  "CONTRACTOR",
  "PASSENGER",
  "PORT_AGENT",
  "OTHER",
] as const;

export interface SafetyExternalPartyInjuryValues {
  company_name: string;
  notes?: string;
  party_name: string;
  party_type: (typeof SAFETY_EXTERNAL_PARTY_TYPES)[number];
  severity: string;
}

interface SafetyExternalPartyInjuryFormProps {
  enabled: boolean;
  onChange: (nextValue: SafetyExternalPartyInjuryValues | null) => void;
  value: SafetyExternalPartyInjuryValues | null | undefined;
}

const defaultExternalPartyValues: SafetyExternalPartyInjuryValues = {
  company_name: "",
  notes: "",
  party_name: "",
  party_type: "PILOT",
  severity: "",
};

export function SafetyExternalPartyInjuryForm({
  enabled,
  onChange,
  value,
}: SafetyExternalPartyInjuryFormProps) {
  const nextValue = value ?? defaultExternalPartyValues;

  function updateField<K extends keyof SafetyExternalPartyInjuryValues>(
    field: K,
    fieldValue: SafetyExternalPartyInjuryValues[K],
  ) {
    onChange({ ...nextValue, [field]: fieldValue });
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            External-Party Injury
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Capture non-crew injuries for pilots, stevedores, contractors,
            passengers, port agents, and other third parties.
          </p>
        </div>
        <label className="inline-flex min-h-[44px] items-center gap-3 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700">
          <input
            checked={enabled}
            className="h-5 w-5 rounded border-slate-300"
            onChange={(event) => onChange(event.target.checked ? nextValue : null)}
            type="checkbox"
          />
          Include external-party injury
        </label>
      </div>

      {enabled ? (
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Party name</span>
            <input
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
              onChange={(event) => updateField("party_name", event.target.value)}
              value={nextValue.party_name}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Company</span>
            <input
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
              onChange={(event) => updateField("company_name", event.target.value)}
              value={nextValue.company_name}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Party type</span>
            <select
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
              onChange={(event) =>
                updateField("party_type", event.target.value as SafetyExternalPartyInjuryValues["party_type"])
              }
              value={nextValue.party_type}
            >
              {SAFETY_EXTERNAL_PARTY_TYPES.map((partyType) => (
                <option key={partyType} value={partyType}>
                  {partyType.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-2 text-sm text-slate-700">
            <span className="font-medium">Severity</span>
            <input
              className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
              onChange={(event) => updateField("severity", event.target.value)}
              placeholder="Medical treatment / lost time / fatality"
              value={nextValue.severity}
            />
          </label>
          <label className="space-y-2 text-sm text-slate-700 md:col-span-2">
            <span className="font-medium">Notes</span>
            <textarea
              className="min-h-[120px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
              onChange={(event) => updateField("notes", event.target.value)}
              value={nextValue.notes ?? ""}
            />
          </label>
        </div>
      ) : null}
    </section>
  );
}

export default SafetyExternalPartyInjuryForm;
