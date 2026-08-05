import { useEffect, useMemo, useState } from 'react';

import { mastersApi } from '../../../lib/api/masters';
import {
  safetyApi,
  type SafetyInjuryDropdownOption,
} from '../../../lib/api/safety';
import { stripPhase1EstimatedCostFields } from '../../../schemas/safety/incident-phase1';
import type { CrewMember } from '../../../types';

export const SAFETY_EXTERNAL_PARTY_TYPES = [
  'PILOT',
  'SHIPYARD',
  'STEVEDORE',
  'CONTRACTOR',
  'PASSENGER',
  'PORT_AGENT',
  'OTHER',
] as const;

type InjuredPersonType = 'CREW' | 'NON_CREW';
type InjuryDropdownField =
  | 'affected_body_areas'
  | 'nature_of_injury'
  | 'source_of_injury';
type TriState = 'YES' | 'NO' | 'NA' | '';
type VesselCondition = 'LOADED' | 'BALLAST' | '';

export interface SafetyExternalPartyInjuryValues {
  affected_body_areas?: string;
  company_name: string;
  cost_deviation?: string | number | null;
  cost_doctor_visits?: string | number | null;
  cost_evacuation?: string | number | null;
  cost_man_hours_lost?: string | number | null;
  cost_medicines_onboard?: string | number | null;
  cost_miscellaneous?: string | number | null;
  cost_off_hire?: string | number | null;
  cost_repatriation?: string | number | null;
  cost_vessel_delays?: string | number | null;
  crew_activity_type?: string;
  crew_age?: string | number | null;
  crew_rank?: string;
  departure_date?: string | null;
  first_aid_details?: string;
  injured_person_type?: InjuredPersonType;
  last_port?: string;
  miscellaneous_expenses_reason?: string;
  nature_of_injury?: string;
  notes?: string;
  onboard_location?: string;
  ocimf_fatality?: boolean | null;
  ocimf_first_aid_case?: boolean | null;
  ocimf_lost_workday_case?: boolean | null;
  ocimf_medical_treatment_case?: boolean | null;
  ocimf_permanent_partial_disability?: boolean | null;
  ocimf_permanent_total_disability?: boolean | null;
  ocimf_restricted_workday_case?: boolean | null;
  party_name: string;
  party_type: (typeof SAFETY_EXTERNAL_PARTY_TYPES)[number] | '';
  prevention_action_taken_required?: string;
  regulation_or_procedure_breach?: string;
  risk_assessment_carried_out?: TriState;
  severity: string;
  shore_assistance_required?: boolean | null;
  source_of_injury?: string;
  toolbox_meeting_carried_out?: TriState;
  total_estimated_cost?: string | number | null;
  vessel_condition?: VesselCondition;
  vessel_location?: string;
  what_happened_narrative?: string;
  why_it_happened_analysis?: string;
}

interface SafetyExternalPartyInjuryFormProps {
  enabled: boolean;
  onChange: (nextValue: SafetyExternalPartyInjuryValues | null) => void;
  value: SafetyExternalPartyInjuryValues | null | undefined;
  vesselId?: string | null;
}

const defaultExternalPartyValues: SafetyExternalPartyInjuryValues = {
  company_name: '',
  injured_person_type: 'NON_CREW',
  notes: '',
  party_name: '',
  party_type: 'PILOT',
  severity: '',
};

const partyTypeLabels: Record<
  (typeof SAFETY_EXTERNAL_PARTY_TYPES)[number],
  string
> = {
  CONTRACTOR: 'Contractor',
  OTHER: 'Other',
  PASSENGER: 'Passenger',
  PILOT: 'Pilot',
  PORT_AGENT: 'Port agent',
  SHIPYARD: 'Shipyard worker',
  STEVEDORE: 'Stevedore',
};

const OTHER_DROPDOWN_VALUE = '__OTHER__';

const injuryDropdownFieldKeys: Record<
  InjuryDropdownField,
  SafetyInjuryDropdownOption['field_key']
> = {
  affected_body_areas: 'AFFECTED_BODY_AREA',
  nature_of_injury: 'NATURE_OF_INJURY',
  source_of_injury: 'SOURCE_OF_INJURY',
};

const investigationTextFields = [
  ['nature_of_injury', 'Nature of Injury'],
  ['source_of_injury', 'Source of Injury'],
  ['affected_body_areas', 'Affected Areas of the Body'],
  ['first_aid_details', 'Details of First Aid Administered'],
  [
    'why_it_happened_analysis',
    'Describe Why it Happened and Analyse Basic / Underlying Causes',
  ],
  [
    'regulation_or_procedure_breach',
    'Any breach of Regulations or Company Procedures',
  ],
  [
    'prevention_action_taken_required',
    'Action Taken / Required to Prevent Similar Incident',
  ],
] as const;

const ocimfFields = [
  ['ocimf_fatality', 'Did it result in a Fatality?'],
  [
    'ocimf_permanent_total_disability',
    'Did it result in a Permanent Total Disability?',
  ],
  [
    'ocimf_permanent_partial_disability',
    'Did it result in a Permanent Partial Disability?',
  ],
  ['ocimf_lost_workday_case', 'Is it a Lost Workday Case?'],
  ['ocimf_restricted_workday_case', 'Is it a Restricted Workday Case?'],
  ['ocimf_medical_treatment_case', 'Is it a Medical Treatment Case?'],
  ['ocimf_first_aid_case', 'Is it a First Aid Case?'],
] as const;

function normalizeValues(
  value: SafetyExternalPartyInjuryValues | null | undefined
) {
  return {
    ...defaultExternalPartyValues,
    ...(value ?? {}),
    injured_person_type:
      value?.injured_person_type ??
      defaultExternalPartyValues.injured_person_type,
  };
}

function asInputValue(value: string | number | null | undefined) {
  return value === null || value === undefined ? '' : String(value);
}

function normalizeCrewMembers(response: unknown): CrewMember[] {
  const rows = Array.isArray(response)
    ? response
    : response && typeof response === 'object'
      ? (response as { data?: unknown }).data
      : undefined;

  return Array.isArray(rows) ? (rows.filter(Boolean) as CrewMember[]) : [];
}

function normalizeInjuryOptions(
  response: unknown
): SafetyInjuryDropdownOption[] {
  const rows = Array.isArray(response)
    ? response
    : response && typeof response === 'object'
      ? (response as { data?: unknown }).data
      : undefined;

  if (!Array.isArray(rows)) {
    return [];
  }

  return rows
    .filter((row): row is SafetyInjuryDropdownOption => {
      if (!row || typeof row !== 'object') {
        return false;
      }
      const option = row as Partial<SafetyInjuryDropdownOption>;
      return Boolean(
        String(option.field_key ?? '').trim() &&
          String(option.option_label ?? '').trim()
      );
    })
    .map((row) => ({
      ...row,
      field_key: String(row.field_key)
        .trim()
        .toUpperCase() as SafetyInjuryDropdownOption['field_key'],
      option_label: String(row.option_label).trim(),
    }));
}

function formatCrewOption(crew: CrewMember | null | undefined) {
  if (!crew) {
    return '';
  }
  const rank = String(crew.rank_name || '').trim();
  const displayName = String(crew.display_name || '').trim();
  const nameWithoutRank =
    rank && displayName.toLowerCase().startsWith(`${rank.toLowerCase()} - `)
      ? displayName.slice(rank.length + 3).trim()
      : displayName;
  const name =
    nameWithoutRank ||
    [crew.first_name, crew.surname].filter(Boolean).join(' ');
  return [rank, name].filter(Boolean).join(' - ');
}

function otherDropdownLabel(options: string[]) {
  return (
    options.find((option) =>
      String(option).trim().toLowerCase().startsWith('other')
    ) ?? 'Other (specify)'
  );
}

function optionLabels(options: SafetyInjuryDropdownOption[]) {
  return options
    .map((option) => String(option.option_label ?? '').trim())
    .filter(Boolean);
}

function InjuryDropdownWithOther({
  label,
  onChange,
  options,
  value,
}: {
  label: string;
  onChange: (nextValue: string) => void;
  options: string[];
  value: string | undefined;
}) {
  const currentValue = String(value ?? '');
  const normalizedOptions = useMemo(
    () => options.map((option) => String(option ?? '').trim()).filter(Boolean),
    [options]
  );
  const otherLabel = useMemo(
    () => otherDropdownLabel(normalizedOptions),
    [normalizedOptions]
  );
  const regularOptions = useMemo(
    () =>
      normalizedOptions.filter(
        (option) => !option.toLowerCase().startsWith('other')
      ),
    [normalizedOptions]
  );
  const hasOtherOption = options.length !== regularOptions.length;
  const [showOtherInput, setShowOtherInput] = useState(false);
  const [otherValue, setOtherValue] = useState('');

  useEffect(() => {
    if (currentValue && regularOptions.includes(currentValue)) {
      setShowOtherInput(false);
      setOtherValue('');
      return;
    }

    if (currentValue && currentValue !== otherLabel) {
      setShowOtherInput(true);
      setOtherValue(currentValue);
    }
  }, [currentValue, otherLabel, regularOptions]);

  const selectedValue = showOtherInput ? OTHER_DROPDOWN_VALUE : currentValue;

  return (
    <div className="space-y-3">
      <label className="space-y-2 text-sm text-slate-700">
        <span className="font-medium">{label}</span>
        <select
          className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
          onChange={(event) => {
            const nextSelectedValue = event.target.value;
            if (nextSelectedValue === OTHER_DROPDOWN_VALUE) {
              setShowOtherInput(true);
              setOtherValue('');
              onChange('');
              return;
            }

            setShowOtherInput(false);
            setOtherValue('');
            onChange(nextSelectedValue);
          }}
          value={selectedValue}
        >
          <option value="">Select</option>
          {regularOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
          {hasOtherOption ? (
            <option value={OTHER_DROPDOWN_VALUE}>{otherLabel}</option>
          ) : null}
        </select>
      </label>
      {showOtherInput && hasOtherOption ? (
        <label className="space-y-2 text-sm text-slate-700">
          <span className="font-medium">Specify other</span>
          <input
            className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
            onChange={(event) => {
              setOtherValue(event.target.value);
              onChange(event.target.value);
            }}
            value={otherValue}
          />
        </label>
      ) : null}
    </div>
  );
}

function BooleanChoice({
  label,
  onChange,
  value,
}: {
  label: string;
  onChange: (nextValue: boolean | null) => void;
  value: boolean | null | undefined;
}) {
  return (
    <fieldset className="space-y-2 text-sm text-slate-700">
      <legend className="font-medium">{label}</legend>
      <div className="flex min-h-[44px] overflow-hidden rounded-2xl border border-slate-200 bg-white">
        {[
          ['Yes', true],
          ['No', false],
        ].map(([optionLabel, optionValue]) => (
          <button
            aria-pressed={value === optionValue}
            className={`flex flex-1 cursor-pointer items-center justify-center px-3 py-2 text-sm font-semibold ${
              value === optionValue
                ? 'bg-slate-900 text-white'
                : 'text-slate-700'
            }`}
            key={optionLabel as string}
            onClick={() => onChange(optionValue as boolean)}
            type="button"
          >
            {optionLabel as string}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export function SafetyExternalPartyInjuryForm({
  enabled,
  onChange,
  value,
  vesselId,
}: SafetyExternalPartyInjuryFormProps) {
  const [crewMembers, setCrewMembers] = useState<CrewMember[]>([]);
  const [crewStatus, setCrewStatus] = useState<'idle' | 'loading' | 'error'>(
    'idle'
  );
  const [injuryOptions, setInjuryOptions] = useState<
    SafetyInjuryDropdownOption[]
  >([]);
  const [injuryOptionsStatus, setInjuryOptionsStatus] = useState<
    'idle' | 'loading' | 'ready' | 'error'
  >('idle');
  const [activityOptions, setActivityOptions] = useState<
    SafetyInjuryDropdownOption[]
  >([]);
  const [activityOptionsStatus, setActivityOptionsStatus] = useState<
    'idle' | 'loading' | 'ready' | 'error'
  >('idle');
  const nextValue = stripPhase1EstimatedCostFields(normalizeValues(value));

  useEffect(() => {
    let cancelled = false;
    if (!enabled || nextValue.injured_person_type !== 'CREW' || !vesselId) {
      setCrewMembers([]);
      setCrewStatus('idle');
      return;
    }
    setCrewStatus('loading');
    mastersApi
      .getVesselCrew(vesselId)
      .then((rows) => {
        if (!cancelled) {
          setCrewMembers(normalizeCrewMembers(rows));
          setCrewStatus('idle');
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCrewMembers([]);
          setCrewStatus('error');
        }
      });

    return () => {
      cancelled = true;
    };
  }, [enabled, nextValue.injured_person_type, vesselId]);

  useEffect(() => {
    let cancelled = false;
    if (!enabled || nextValue.injured_person_type !== 'CREW') {
      setInjuryOptions([]);
      setInjuryOptionsStatus('idle');
      return;
    }
    setInjuryOptionsStatus('loading');
    safetyApi
      .getInjuryDropdownOptions()
      .then((options) => {
        if (!cancelled) {
          setInjuryOptions(normalizeInjuryOptions(options));
          setInjuryOptionsStatus('ready');
        }
      })
      .catch(() => {
        if (!cancelled) {
          setInjuryOptions([]);
          setInjuryOptionsStatus('error');
        }
      });

    return () => {
      cancelled = true;
    };
  }, [enabled, nextValue.injured_person_type]);

  useEffect(() => {
    let cancelled = false;
    if (!enabled || nextValue.injured_person_type !== 'CREW') {
      setActivityOptions([]);
      setActivityOptionsStatus('idle');
      return;
    }
    setActivityOptionsStatus('loading');
    safetyApi
      .getInjuryDropdownOptions('TYPE_OF_ACTIVITY')
      .then((options) => {
        if (!cancelled) {
          setActivityOptions(normalizeInjuryOptions(options));
          setActivityOptionsStatus('ready');
        }
      })
      .catch(() => {
        if (!cancelled) {
          setActivityOptions([]);
          setActivityOptionsStatus('error');
        }
      });

    return () => {
      cancelled = true;
    };
  }, [enabled, nextValue.injured_person_type]);

  const crewRanks = useMemo(() => {
    const ranks = new Map<string, string>();
    crewMembers.forEach((crew) => {
      const rank = String(crew.rank_name || '').trim();
      if (rank) {
        ranks.set(rank.toUpperCase(), rank);
      }
    });
    return Array.from(ranks.values()).sort((left, right) =>
      left.localeCompare(right)
    );
  }, [crewMembers]);

  const injuryOptionsByField = useMemo(() => {
    return injuryOptions.reduce<Record<InjuryDropdownField, string[]>>(
      (groupedOptions, option) => {
        const field = (Object.entries(injuryDropdownFieldKeys).find(
          ([, fieldKey]) => fieldKey === option.field_key
        )?.[0] ?? null) as InjuryDropdownField | null;
        if (field) {
          groupedOptions[field].push(option.option_label);
        }
        return groupedOptions;
      },
      {
        affected_body_areas: [],
        nature_of_injury: [],
        source_of_injury: [],
      }
    );
  }, [injuryOptions]);
  const activityOptionLabels = useMemo(
    () => optionLabels(activityOptions),
    [activityOptions]
  );

  function updateField<K extends keyof SafetyExternalPartyInjuryValues>(
    field: K,
    fieldValue: SafetyExternalPartyInjuryValues[K]
  ) {
    onChange(
      stripPhase1EstimatedCostFields({ ...nextValue, [field]: fieldValue })
    );
  }

  function updatePersonType(injuredPersonType: InjuredPersonType) {
    onChange(
      stripPhase1EstimatedCostFields({
        ...nextValue,
        injured_person_type: injuredPersonType,
        party_type:
          injuredPersonType === 'NON_CREW'
            ? nextValue.party_type || 'PILOT'
            : '',
      })
    );
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Injury Details
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Record crew or non-crew injury information for this incident.
          </p>
        </div>
        <button
          aria-pressed={enabled}
          className={`inline-flex min-h-[44px] items-center gap-3 rounded-full border px-4 py-2 text-sm font-semibold transition ${
            enabled
              ? 'border-slate-900 bg-slate-900 text-white'
              : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-white'
          }`}
          onClick={() => onChange(enabled ? null : nextValue)}
          type="button"
        >
          <span
            aria-hidden="true"
            className={`flex h-5 w-5 items-center justify-center rounded-full border ${
              enabled ? 'border-white bg-white' : 'border-slate-300 bg-white'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${enabled ? 'bg-slate-900' : 'bg-transparent'}`}
            />
          </span>
          Record injury
        </button>
      </div>

      {enabled ? (
        <div className="mt-5 space-y-6">
          <div
            aria-label="Injured person type"
            className="rounded-3xl border border-slate-200 bg-slate-100/80 p-1.5"
            role="radiogroup"
          >
            <div className="grid gap-1.5 sm:grid-cols-2">
              {[
                ['CREW', 'Crew', 'Vessel crew member'],
                [
                  'NON_CREW',
                  'Non-crew',
                  'Pilot, contractor, visitor, or other third party',
                ],
              ].map(([optionValue, optionLabel, optionDescription]) => {
                const selected = nextValue.injured_person_type === optionValue;
                return (
                  <button
                    aria-checked={selected}
                    aria-label={optionLabel}
                    className={`flex min-h-[64px] cursor-pointer items-center gap-3 rounded-2xl border px-4 py-3 text-left transition focus-within:ring-2 focus-within:ring-slate-400 ${
                      selected
                        ? 'border-slate-900 bg-white text-slate-950 shadow-sm'
                        : 'border-transparent bg-transparent text-slate-600 hover:bg-white/70 hover:text-slate-900'
                    }`}
                    key={optionValue}
                    onClick={() =>
                      updatePersonType(optionValue as InjuredPersonType)
                    }
                    role="radio"
                    type="button"
                  >
                    <span
                      aria-hidden="true"
                      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                        selected
                          ? 'border-slate-900 bg-slate-900'
                          : 'border-slate-300 bg-white'
                      }`}
                    >
                      <span
                        className={`h-2 w-2 rounded-full ${selected ? 'bg-white' : 'bg-transparent'}`}
                      />
                    </span>
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold">
                        {optionLabel}
                      </span>
                      <span
                        className={`mt-0.5 block text-xs ${selected ? 'text-slate-600' : 'text-slate-500'}`}
                      >
                        {optionDescription}
                      </span>
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {nextValue.injured_person_type === 'NON_CREW' ? (
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Person name</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('party_name', event.target.value)
                  }
                  value={nextValue.party_name}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Company</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('company_name', event.target.value)
                  }
                  value={nextValue.company_name}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Who is this person?</span>
                <select
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField(
                      'party_type',
                      event.target
                        .value as SafetyExternalPartyInjuryValues['party_type']
                    )
                  }
                  value={nextValue.party_type || 'PILOT'}
                >
                  {SAFETY_EXTERNAL_PARTY_TYPES.map((partyType) => (
                    <option key={partyType} value={partyType}>
                      {partyTypeLabels[partyType]}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Injury level</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('severity', event.target.value)
                  }
                  placeholder="First aid / medical treatment / lost time / fatal"
                  value={nextValue.severity}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700 md:col-span-2">
                <span className="font-medium">More details</span>
                <textarea
                  className="min-h-[120px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
                  onChange={(event) => updateField('notes', event.target.value)}
                  value={nextValue.notes ?? ''}
                />
              </label>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Rank of person</span>
                <select
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('crew_rank', event.target.value)
                  }
                  value={nextValue.crew_rank ?? ''}
                >
                  <option value="">
                    {crewStatus === 'loading'
                      ? 'Loading ranks...'
                      : crewRanks.length
                        ? 'Select rank'
                        : 'No rank loaded for this vessel'}
                  </option>
                  {crewRanks.map((rank) => (
                    <option key={rank} value={rank}>
                      {rank}
                    </option>
                  ))}
                </select>
                {crewMembers.length ? (
                  <span className="block text-xs text-slate-500">
                    Crew list loaded:{' '}
                    {crewMembers.map(formatCrewOption).filter(Boolean).length}{' '}
                    people
                  </span>
                ) : null}
                {crewStatus === 'error' ? (
                  <span className="block text-xs text-amber-700">
                    Crew ranks could not be loaded.
                  </span>
                ) : null}
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Age</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  min={0}
                  onChange={(event) =>
                    updateField('crew_age', event.target.value)
                  }
                  type="number"
                  value={asInputValue(nextValue.crew_age)}
                />
              </label>
              <div className="space-y-2 text-sm text-slate-700">
                <InjuryDropdownWithOther
                  label="Type of Activity"
                  onChange={(nextFieldValue) =>
                    updateField('crew_activity_type', nextFieldValue)
                  }
                  options={activityOptionLabels}
                  value={String(nextValue.crew_activity_type ?? '')}
                />
                {activityOptionsStatus === 'error' ? (
                  <span className="block text-xs text-amber-700">
                    Activity options could not be loaded.
                  </span>
                ) : null}
              </div>
            </div>
          )}

          <section className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-base font-semibold text-slate-900">
              Investigation - Narrative
            </h3>
            {injuryOptionsStatus === 'error' ? (
              <p className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                Injury dropdown master data could not be loaded.
              </p>
            ) : null}
            <div className="grid gap-4 md:grid-cols-2">
              {investigationTextFields.map(([field, label]) => (
                <div
                  className={`space-y-2 text-sm text-slate-700 ${
                    field === 'why_it_happened_analysis'
                      ? 'md:col-span-2'
                      : ''
                  }`}
                  key={field}
                >
                  {field in injuryDropdownFieldKeys ? (
                    <InjuryDropdownWithOther
                      label={label}
                      onChange={(nextFieldValue) =>
                        updateField(field, nextFieldValue)
                      }
                      options={
                        injuryOptionsByField[field as InjuryDropdownField]
                      }
                      value={String(nextValue[field] ?? '')}
                    />
                  ) : (
                    <label className="space-y-2 text-sm text-slate-700">
                      <span className="font-medium">{label}</span>
                      <textarea
                        className="min-h-[110px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 leading-6"
                        onChange={(event) =>
                          updateField(field, event.target.value)
                        }
                        value={String(nextValue[field] ?? '')}
                      />
                    </label>
                  )}
                </div>
              ))}
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">
                  Was a Risk Assessment carried out?
                </span>
                <select
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                  onChange={(event) =>
                    updateField(
                      'risk_assessment_carried_out',
                      event.target.value as TriState
                    )
                  }
                  value={nextValue.risk_assessment_carried_out ?? ''}
                >
                  <option value="">Select</option>
                  <option value="YES">Yes</option>
                  <option value="NO">No</option>
                  <option value="NA">NA</option>
                </select>
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">
                  Was Toolbox Meeting carried out?
                </span>
                <select
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                  onChange={(event) =>
                    updateField(
                      'toolbox_meeting_carried_out',
                      event.target.value as TriState
                    )
                  }
                  value={nextValue.toolbox_meeting_carried_out ?? ''}
                >
                  <option value="">Select</option>
                  <option value="YES">Yes</option>
                  <option value="NO">No</option>
                  <option value="NA">NA</option>
                </select>
              </label>
            </div>
          </section>

          <section className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-base font-semibold text-slate-900">
              OCIMF Reporting
            </h3>
            <div className="grid gap-4 md:grid-cols-2">
              {ocimfFields.map(([field, label]) => (
                <BooleanChoice
                  key={field}
                  label={label}
                  onChange={(nextBoolean) => updateField(field, nextBoolean)}
                  value={nextValue[field]}
                />
              ))}
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}

export default SafetyExternalPartyInjuryForm;
