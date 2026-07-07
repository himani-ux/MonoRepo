import { useEffect, useState } from 'react';

import SafetyExternalPartyInjuryForm, {
  type SafetyExternalPartyInjuryValues,
} from './external-party-injury-form';
import {
  SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION,
  type SafetyIncidentPhase1SubmitValues,
  type SafetyIncidentPhase1Values,
  safetyIncidentPhase1Schema,
  safetyIncidentPhase1SubmitSchema,
} from '../../../schemas/safety/incident-phase1';
import { useDraftAutosave } from '../../../hooks/safety/use-draft-autosave';
import { toUtcIsoTimestamp } from '../../../hooks/safety/use-msc-mepc3-position';
import { SafetySelfReportGuardModal } from './self-report-guard-modal';
import { useAuth } from '../../../hooks/use-auth';
import { useToast } from '../../../hooks/use-toast';
import { getErrorMessage } from '../../../lib/api/client';
import {
  safetyApi,
  type SafetyIncidentWeatherFieldKey,
  type SafetyIncidentWeatherOption,
} from '../../../lib/api/safety';
import { getSafetyDeviceFingerprint } from '../../../lib/safety/digital-signature';
import {
  SafetyIncidentTypeSelect,
  SafetyLossTypeMultiSelect,
} from '../shared/reference-pickers';

interface SafetyIncidentPhase1FormProps {
  incidentId?: string;
  initialValues?: Partial<SafetyIncidentPhase1Values>;
  mode: 'create' | 'edit';
  onSaveDraft?: (values: SafetyIncidentPhase1Values) => void | Promise<void>;
  onSubmitPhase?: (
    values: SafetyIncidentPhase1SubmitValues
  ) => void | Promise<void>;
}

const defaultValues: SafetyIncidentPhase1Values = {
  awaiting_daily_report_match: false,
  departure_date: null,
  last_port: '',
  latitude: null,
  longitude: null,
  narrative: '',
  onboard_location: '',
  office_notified: null,
  reporter_device_fingerprint: '',
  reporter_name: '',
  reporter_rank: '',
  reporter_user_id: '',
  schema_version: SAFETY_INCIDENT_PHASE_1_SCHEMA_VERSION,
  shore_assistance_required: null,
  vessel_condition: '',
  vessel_id: '',
  vessel_location: '',
  weather_ambient_temperature_c: null,
  weather_current_direction_id: null,
  weather_current_strength_knots: null,
  weather_ice_condition_at_sea_id: null,
  weather_ice_condition_onboard_id: null,
  weather_light_condition_id: null,
  weather_lighting_source_id: null,
  weather_precipitation_id: null,
  weather_sea_state_id: null,
  weather_visibility_id: null,
  weather_wind_direction_id: null,
  weather_wind_scale_id: null,
};

type AuthUserShape = NonNullable<ReturnType<typeof useAuth>['user']> &
  Record<string, unknown>;

const WEATHER_DROPDOWN_FIELDS = [
  {
    field: 'weather_visibility_id',
    fieldKey: 'VISIBILITY',
    label: 'Visibility',
  },
  {
    field: 'weather_precipitation_id',
    fieldKey: 'PRECIPITATION',
    label: 'Precipitation',
  },
  { field: 'weather_sea_state_id', fieldKey: 'SEA_STATE', label: 'Sea State' },
  {
    field: 'weather_wind_scale_id',
    fieldKey: 'WIND_SCALE',
    label: 'Wind Scale',
  },
  {
    field: 'weather_wind_direction_id',
    fieldKey: 'WIND_DIRECTION',
    label: 'Wind Direction',
  },
  {
    field: 'weather_lighting_source_id',
    fieldKey: 'LIGHTING_SOURCE',
    label: 'Source of Lighting',
  },
  {
    field: 'weather_current_direction_id',
    fieldKey: 'CURRENT_DIRECTION',
    label: 'Current Direction',
  },
  {
    field: 'weather_light_condition_id',
    fieldKey: 'LIGHT_CONDITION',
    label: 'Light condition',
  },
] as const satisfies ReadonlyArray<{
  field: keyof SafetyIncidentPhase1Values;
  fieldKey: SafetyIncidentWeatherFieldKey;
  label: string;
}>;

const WEATHER_FALLBACK_OPTIONS = [
  ['VISIBILITY', 'Good: More than 5 nautical miles'],
  ['VISIBILITY', 'Moderate: Between 2 and 5 nautical miles'],
  ['VISIBILITY', 'Poor: Between 1000 meters and 2 nautical miles'],
  ['VISIBILITY', 'Very Poor: Less than 1000 meters'],
  ['PRECIPITATION', 'No Rain / Hail / Snow'],
  ['PRECIPITATION', 'Rain Showers'],
  ['PRECIPITATION', 'Light Rain'],
  ['PRECIPITATION', 'Heavy Rain'],
  ['PRECIPITATION', 'Rain Storm'],
  ['PRECIPITATION', 'Light Hail'],
  ['PRECIPITATION', 'Heavy Hail'],
  ['PRECIPITATION', 'Hail Storm'],
  ['PRECIPITATION', 'Light Snow'],
  ['PRECIPITATION', 'Heavy Snow'],
  ['PRECIPITATION', 'Snow Storm'],
  ['SEA_STATE', '0: Calm (Glassy)'],
  ['SEA_STATE', '1: Calm (Rippled)'],
  ['SEA_STATE', '2: Smooth'],
  ['SEA_STATE', '3: Slight'],
  ['SEA_STATE', '4: Moderate'],
  ['SEA_STATE', '5: Rough'],
  ['SEA_STATE', '6: Very Rough'],
  ['SEA_STATE', '7: High'],
  ['SEA_STATE', '8: Very High'],
  ['SEA_STATE', '9: Phenomenal'],
  ['WIND_SCALE', '0: Calm'],
  ['WIND_SCALE', '1: Light Air'],
  ['WIND_SCALE', '2: Light Breeze'],
  ['WIND_SCALE', '3: Gentle Breeze'],
  ['WIND_SCALE', '4: Moderate Breeze'],
  ['WIND_SCALE', '5: Fresh Breeze'],
  ['WIND_SCALE', '6: Strong Breeze'],
  ['WIND_SCALE', '7: High Wind / Moderate Gale / Near Gale'],
  ['WIND_SCALE', '8: Gale / Fresh Gale'],
  ['WIND_SCALE', '9: Strong Gale'],
  ['WIND_SCALE', '10: Storm / Whole Gale'],
  ['WIND_SCALE', '11: Violent Storm'],
  ['WIND_SCALE', '12: Hurricane Force'],
  ['WIND_DIRECTION', 'N'],
  ['WIND_DIRECTION', 'NE'],
  ['WIND_DIRECTION', 'E'],
  ['WIND_DIRECTION', 'SE'],
  ['WIND_DIRECTION', 'S'],
  ['WIND_DIRECTION', 'SW'],
  ['WIND_DIRECTION', 'W'],
  ['WIND_DIRECTION', 'NW'],
  ['CURRENT_DIRECTION', 'N'],
  ['CURRENT_DIRECTION', 'NE'],
  ['CURRENT_DIRECTION', 'E'],
  ['CURRENT_DIRECTION', 'SE'],
  ['CURRENT_DIRECTION', 'S'],
  ['CURRENT_DIRECTION', 'SW'],
  ['CURRENT_DIRECTION', 'W'],
  ['CURRENT_DIRECTION', 'NW'],
  ['LIGHTING_SOURCE', 'Artificial'],
  ['LIGHTING_SOURCE', 'Natural'],
  ['LIGHTING_SOURCE', 'Darkness'],
  ['ICE_CONDITION_ONBOARD', 'No ice'],
  ['ICE_CONDITION_ONBOARD', 'Light'],
  ['ICE_CONDITION_ONBOARD', 'Moderate'],
  ['ICE_CONDITION_ONBOARD', 'Heavy'],
  ['ICE_CONDITION_AT_SEA', 'Open Water'],
  ['ICE_CONDITION_AT_SEA', 'Bergy Water'],
  ['ICE_CONDITION_AT_SEA', 'Brash (ice fragments < 2 m)'],
  ['ICE_CONDITION_AT_SEA', 'New Ice (N)'],
  ['ICE_CONDITION_AT_SEA', 'Nilas, Ice Rind'],
  ['ICE_CONDITION_AT_SEA', 'Grey Ice (G)'],
  ['ICE_CONDITION_AT_SEA', 'Grey-White Ice (GW)'],
  ['ICE_CONDITION_AT_SEA', 'Thin First-Year Ice - 1st Stage'],
  ['ICE_CONDITION_AT_SEA', 'Thin First-Year Ice - 2nd Stage'],
  ['ICE_CONDITION_AT_SEA', 'Thin First-Year Ice (FY)'],
  ['ICE_CONDITION_AT_SEA', 'Medium First-Year Ice (MFY)'],
  ['ICE_CONDITION_AT_SEA', 'Thick First-Year Ice (TFY)'],
  ['ICE_CONDITION_AT_SEA', 'Second-Year Ice (SY)'],
  ['ICE_CONDITION_AT_SEA', 'Old / Multi-Year Ice (MY)'],
  ['LIGHT_CONDITION', 'Full light'],
  ['LIGHT_CONDITION', 'Full dark'],
  ['LIGHT_CONDITION', 'Dusk'],
  ['LIGHT_CONDITION', 'Dawn'],
] as const satisfies ReadonlyArray<
  readonly [SafetyIncidentWeatherFieldKey, string]
>;

function buildWeatherFallbackOptions(): SafetyIncidentWeatherOption[] {
  return WEATHER_FALLBACK_OPTIONS.map(([fieldKey, optionLabel], index) => ({
    active: true,
    display_order: index + 1,
    field_key: fieldKey,
    field_label:
      WEATHER_DROPDOWN_FIELDS.find((field) => field.fieldKey === fieldKey)
        ?.label ?? fieldKey,
    id: `00000000-0000-4000-8000-${(index + 1).toString(16).padStart(12, '0')}`,
    option_label: optionLabel,
  }));
}

function firstNonBlank(...values: unknown[]) {
  for (const value of values) {
    if (value === null || value === undefined) {
      continue;
    }
    if (Array.isArray(value)) {
      const nested = firstNonBlank(...value);
      if (nested) {
        return nested;
      }
      continue;
    }
    const text = String(value).trim();
    if (text) {
      return text;
    }
  }

  return '';
}

function readAuthField(
  user: ReturnType<typeof useAuth>['user'],
  ...keys: string[]
) {
  const source = (user ?? {}) as Record<string, unknown>;
  return keys.map((key) => source[key]);
}

function buildReporterNameFromAuth(user: ReturnType<typeof useAuth>['user']) {
  const source = (user ?? {}) as AuthUserShape;
  const combinedName = [
    source.first_name,
    source.firstName,
    source.surname,
    source.last_name,
    source.lastName,
  ]
    .map((value) => firstNonBlank(value))
    .filter((value) => value.length > 0)
    .join(' ')
    .trim();

  return firstNonBlank(
    ...readAuthField(
      user,
      'full_name',
      'fullName',
      'display_name',
      'displayName',
      'name'
    ),
    combinedName,
    ...readAuthField(
      user,
      'username',
      'userName',
      'UserName',
      'crew_id',
      'crewId',
      'employee_id',
      'employeeId'
    )
  );
}

function isVesselAuthUser(
  isVessel: boolean,
  user: ReturnType<typeof useAuth>['user']
) {
  const source = (user ?? {}) as AuthUserShape;
  const normalizedUserType = firstNonBlank(
    source.user_type,
    source.userType,
    source.legacy_user_type,
    source.legacyUserType
  ).toUpperCase();
  const normalizedRole = firstNonBlank(
    source.role,
    source.role_name,
    source.roleName,
    source.safety_role_name
  ).toUpperCase();
  const workSide = firstNonBlank(
    source.work_side,
    source.workSide
  ).toUpperCase();

  return (
    isVessel ||
    normalizedUserType === 'VESSEL' ||
    normalizedUserType === 'SHIP' ||
    workSide === '1' ||
    normalizedRole === 'VESSEL_MASTER' ||
    normalizedRole === 'VESSEL_CREW' ||
    normalizedRole === 'MASTER' ||
    normalizedRole === 'CHIEF OFFICER' ||
    normalizedRole === 'CHIEF ENGINEER' ||
    normalizedRole === 'CO' ||
    normalizedRole === 'CE'
  );
}

function toDateTimeLocalValue(value?: string | null) {
  if (!value) {
    return '';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return '';
  }

  const timezoneOffsetMs = parsed.getTimezoneOffset() * 60_000;
  return new Date(parsed.getTime() - timezoneOffsetMs)
    .toISOString()
    .slice(0, 16);
}

function toNumberInputValue(value?: number | null) {
  return value === null || value === undefined ? '' : String(value);
}

function toNullableNumber(value: string) {
  const trimmedValue = value.trim();
  if (!trimmedValue) {
    return null;
  }

  const parsedValue = Number(trimmedValue);
  return Number.isFinite(parsedValue) ? parsedValue : null;
}

function describeValidationIssue(
  issue: { message: string; path: Array<string | number> } | undefined
) {
  if (!issue) {
    return 'Please fill the required details before continuing.';
  }

  const fieldLabels: Record<string, string> = {
    incident_type_id: 'Incident type',
    loss_type_primary_id: 'What was affected',
    narrative: 'What happened',
    occurred_at: 'Incident time',
    office_notification_mode: 'How was office informed?',
    office_notified: 'Was office informed?',
    pic_candidate_id: 'Person in charge',
    reported_at: 'Report time',
    reporter_device_fingerprint: 'Reporter device',
    reporter_name: 'Reporter name',
    reporter_rank: 'Reporter rank',
    reporter_user_id: 'Reporter user ID',
    risk_band: 'Risk level',
    vessel_code: 'Vessel code',
    vessel_id: 'Vessel',
  };

  const fieldKey = String(issue.path[0] ?? '');
  const fieldLabel = fieldLabels[fieldKey];
  if (fieldLabel) {
    return `${fieldLabel}: ${issue.message}`;
  }

  return issue.message;
}

function derivedInvestigationDepthLabel(
  riskBand?: SafetyIncidentPhase1Values['risk_band']
) {
  if (riskBand === 'RED') {
    return 'High detail check';
  }
  if (riskBand === 'YELLOW') {
    return 'Medium detail check';
  }
  if (riskBand === 'GREEN') {
    return 'Basic check';
  }
  return 'Select risk level';
}

function currentPhase1PayloadValues(values: SafetyIncidentPhase1Values) {
  const {
    last_port: _lastPort,
    weather_ice_condition_at_sea_id: _iceAtSea,
    weather_ice_condition_onboard_id: _iceOnBoard,
    ...visibleValues
  } = values;

  return {
    ...visibleValues,
    office_notification_mode:
      values.office_notification_mode === 'WHATSAPP'
        ? null
        : values.office_notification_mode,
  };
}

export function SafetyIncidentPhase1Form({
  incidentId,
  initialValues,
  mode,
  onSaveDraft,
  onSubmitPhase,
}: SafetyIncidentPhase1FormProps) {
  const { isVessel, user } = useAuth();
  const { toast } = useToast();
  const [values, setValues] = useState<SafetyIncidentPhase1Values>({
    ...defaultValues,
    ...initialValues,
  });
  const [showConflictGuard, setShowConflictGuard] = useState(false);
  const [weatherOptions, setWeatherOptions] = useState<
    SafetyIncidentWeatherOption[]
  >([]);
  const [weatherOptionsStatus, setWeatherOptionsStatus] = useState<
    'idle' | 'loading' | 'ready' | 'error'
  >('idle');
  const isVesselUser = isVesselAuthUser(isVessel, user);
  const vesselIdFromAuth = firstNonBlank(
    ...readAuthField(
      user,
      'vessel_id',
      'vesselId',
      'VesselId',
      'VesselID',
      'vessel_ids',
      'vesselIds'
    )
  );
  const vesselCodeFromAuth = firstNonBlank(
    ...readAuthField(
      user,
      'vessel_code',
      'vesselCode',
      'VesselCode',
      'ship_code',
      'shipCode',
      'vessel_codes',
      'vesselCodes'
    )
  );
  const vesselDisplayName = firstNonBlank(
    ...readAuthField(user, 'vessel_name', 'vesselName', 'VesselName'),
    vesselCodeFromAuth,
    values.vessel_code,
    vesselIdFromAuth,
    values.vessel_id
  );
  const authVesselIds = ((user as AuthUserShape | null)?.vessel_ids ??
    (user as AuthUserShape | null)?.vesselIds ??
    []) as unknown[];
  const authVesselNames = ((user as AuthUserShape | null)?.vessel_names ??
    (user as AuthUserShape | null)?.vesselNames ??
    []) as unknown[];
  const authVesselCodes = ((user as AuthUserShape | null)?.vessel_codes ??
    (user as AuthUserShape | null)?.vesselCodes ??
    []) as unknown[];
  const vesselOptions = authVesselIds
    .map((vesselId, index) => ({
      code: firstNonBlank(authVesselCodes[index]),
      id: String(vesselId).trim(),
      label: firstNonBlank(authVesselNames[index], String(vesselId)),
    }))
    .filter((option) => option.id);
  const selectedVesselOption = vesselOptions.find(
    (option) => option.id === values.vessel_id
  );
  const singleVesselId = vesselOptions.length === 1 ? vesselOptions[0].id : '';
  const singleVesselCode =
    vesselOptions.length === 1 ? vesselOptions[0].code : '';
  const preferredVesselId = firstNonBlank(vesselIdFromAuth, singleVesselId);
  const preferredVesselCode = firstNonBlank(
    vesselCodeFromAuth,
    singleVesselCode
  );
  const shouldAutofillVesselIdentity =
    mode === 'create' &&
    Boolean(preferredVesselId) &&
    (isVesselUser || vesselOptions.length === 1);
  const vesselIdentityLocked =
    isVesselUser ||
    mode === 'edit' ||
    (mode === 'create' && vesselOptions.length === 1);
  const vesselInputDisplayValue = firstNonBlank(
    selectedVesselOption?.label,
    isVesselUser ? vesselDisplayName : '',
    values.vessel_id
  );
  const vesselCodeDisplayValue = firstNonBlank(
    values.vessel_code,
    selectedVesselOption?.code,
    preferredVesselCode
  );
  const reporterUserIdFromAuth = firstNonBlank(
    ...readAuthField(
      user,
      'crew_id',
      'crewId',
      'login_id',
      'loginId',
      'username',
      'userName',
      'UserName',
      'employee_id',
      'employeeId',
      'id'
    )
  );
  const reporterNameFromAuth = buildReporterNameFromAuth(user);
  const reporterRankFromAuth = firstNonBlank(
    ...readAuthField(
      user,
      'rank',
      'Rank',
      'safety_role_name',
      'safetyRoleName',
      'role_name',
      'roleName',
      'role'
    )
  );
  const createDraftRecordId = [
    'draft-phase-1',
    vesselIdFromAuth || vesselCodeFromAuth || 'no-vessel',
    reporterUserIdFromAuth || 'no-reporter',
  ].join(':');
  const { saveDraftNow } = useDraftAutosave({
    enabled: mode === 'create',
    onRestore: (restoredValues) =>
      setValues((current) => {
        const nextValues = { ...current, ...restoredValues };

        if (shouldAutofillVesselIdentity) {
          nextValues.vessel_id = firstNonBlank(
            preferredVesselId,
            nextValues.vessel_id
          );
          nextValues.vessel_code = firstNonBlank(
            preferredVesselCode,
            nextValues.vessel_code
          );
        }

        if (isVesselUser && mode === 'create') {
          nextValues.reporter_user_id = firstNonBlank(
            reporterUserIdFromAuth,
            nextValues.reporter_user_id
          );
          nextValues.reporter_name = firstNonBlank(
            reporterNameFromAuth,
            nextValues.reporter_name
          );
          nextValues.reporter_rank = firstNonBlank(
            reporterRankFromAuth,
            nextValues.reporter_rank
          );
        }

        return nextValues;
      }),
    phase: 1,
    recordId: incidentId ?? createDraftRecordId,
    values,
  });

  useEffect(() => {
    if (!initialValues) {
      return;
    }

    setValues({
      ...defaultValues,
      ...initialValues,
    });
  }, [initialValues]);

  const narrativeLength = values.narrative.trim().length;
  const submitReady =
    safetyIncidentPhase1SubmitSchema.safeParse(
      currentPhase1PayloadValues(values)
    ).success;

  const weatherOptionsByField = WEATHER_DROPDOWN_FIELDS.reduce(
    (groups, item) => {
      groups[item.fieldKey] = weatherOptions.filter(
        (option) => option.field_key === item.fieldKey && option.active
      );
      return groups;
    },
    {} as Record<SafetyIncidentWeatherFieldKey, SafetyIncidentWeatherOption[]>
  );

  useEffect(() => {
    setValues((current) => {
      if (current.reporter_device_fingerprint) {
        return current;
      }
      return {
        ...current,
        reporter_device_fingerprint: getSafetyDeviceFingerprint(),
      };
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    setWeatherOptionsStatus('loading');
    safetyApi
      .getIncidentWeatherOptions()
      .then((options) => {
        if (cancelled) {
          return;
        }
        setWeatherOptions(
          options.length ? options : buildWeatherFallbackOptions()
        );
        setWeatherOptionsStatus('ready');
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setWeatherOptions(buildWeatherFallbackOptions());
        setWeatherOptionsStatus('ready');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!shouldAutofillVesselIdentity) {
      return;
    }

    setValues((current) => {
      const nextVesselId = preferredVesselId || current.vessel_id;
      const nextVesselCode = preferredVesselCode || current.vessel_code;

      if (
        current.vessel_id === nextVesselId &&
        (current.vessel_code ?? '') === (nextVesselCode ?? '')
      ) {
        return current;
      }

      return {
        ...current,
        vessel_code: nextVesselCode,
        vessel_id: nextVesselId,
      };
    });
  }, [
    preferredVesselCode,
    preferredVesselId,
    shouldAutofillVesselIdentity,
  ]);

  useEffect(() => {
    if (!isVesselUser || mode !== 'create') {
      return;
    }

    setValues((current) => {
      const nextReporterUserId =
        reporterUserIdFromAuth || current.reporter_user_id;
      const nextReporterName = reporterNameFromAuth || current.reporter_name;
      const nextReporterRank = reporterRankFromAuth || current.reporter_rank;

      if (
        current.reporter_user_id === nextReporterUserId &&
        current.reporter_name === nextReporterName &&
        current.reporter_rank === nextReporterRank
      ) {
        return current;
      }

      return {
        ...current,
        reporter_name: nextReporterName,
        reporter_rank: nextReporterRank,
        reporter_user_id: nextReporterUserId,
      };
    });
  }, [
    isVesselUser,
    mode,
    reporterNameFromAuth,
    reporterRankFromAuth,
    reporterUserIdFromAuth,
  ]);

  function updateField<K extends keyof SafetyIncidentPhase1Values>(
    field: K,
    nextValue: SafetyIncidentPhase1Values[K]
  ) {
    setValues((current) => ({ ...current, [field]: nextValue }));
  }

  function updateWeatherDropdownField(
    field: (typeof WEATHER_DROPDOWN_FIELDS)[number]['field'],
    nextValue: string | null
  ) {
    setValues((current) => ({ ...current, [field]: nextValue }));
  }

  function updateExternalParty(
    nextValue: SafetyExternalPartyInjuryValues | null
  ) {
    setValues((current) => ({ ...current, external_party_injury: nextValue }));
  }

  function updateLossTypes(nextValue: {
    lossTypeIds: number[];
    otherSelected: boolean;
    otherText: string;
  }) {
    setValues((current) => ({
      ...current,
      loss_type_other: nextValue.otherSelected ? nextValue.otherText : null,
      loss_type_primary_id: nextValue.lossTypeIds[0] ?? null,
      loss_type_secondary_id: nextValue.lossTypeIds[1] ?? null,
      loss_type_tertiary_id: nextValue.lossTypeIds[2] ?? null,
    }));
  }

  async function handleSaveDraft() {
    const result = safetyIncidentPhase1Schema.safeParse(
      currentPhase1PayloadValues(values)
    );
    if (!result.success) {
      const issue = result.error.issues[0];
      toast({
        title: 'Some details are missing',
        description: describeValidationIssue(issue),
        variant: 'warning',
      });
      return;
    }

    try {
      if (mode === 'edit' && !onSaveDraft) {
        throw new Error('Save handler unavailable for this incident.');
      }

      await onSaveDraft?.(result.data);
      const draft = mode === 'create' ? await saveDraftNow() : null;
      toast({
        title: mode === 'create' ? 'Draft saved' : 'Changes saved',
        description:
          mode === 'create' && draft
            ? `Draft saved at ${draft.updatedAt}.`
            : 'Phase 1 changes were saved to the incident.',
        variant: 'success',
      });
    } catch (error) {
      toast({
        title:
          mode === 'create' ? 'Unable to save draft' : 'Unable to save changes',
        description:
          getErrorMessage(error) ||
          'Try again after checking the incident details.',
        variant: 'destructive',
      });
    }
  }

  async function handleSubmit() {
    const result = safetyIncidentPhase1SubmitSchema.safeParse(
      currentPhase1PayloadValues(values)
    );
    if (!result.success) {
      const issue = result.error.issues[0];
      toast({
        title: 'Some details are missing',
        description: describeValidationIssue(issue),
        variant: 'warning',
      });
      return;
    }

    if (
      values.pic_candidate_id &&
      values.pic_candidate_id === values.reporter_user_id
    ) {
      setShowConflictGuard(true);
      return;
    }

    try {
      await onSubmitPhase?.(result.data);
    } catch (error) {
      toast({
        title: 'Unable to submit report',
        description:
          getErrorMessage(error) ||
          'Try again after checking the incident details.',
        variant: 'destructive',
      });
    }
  }

  return (
    <>
      <section className="space-y-6">
        <header className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                Incident Report
              </p>
              <h1 className="text-3xl font-semibold text-slate-900">
                Tell Us What Happened
              </h1>
              <p className="max-w-3xl text-sm leading-6 text-slate-600">
                Fill this form in simple words. Write what happened, when it
                happened, and what you did first.
              </p>
            </div>
          </div>
        </header>

        <section className="space-y-6">
          <div className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">What type of incident?</span>
                <SafetyIncidentTypeSelect
                  onChange={(nextValue) =>
                    updateField('incident_type_id', nextValue)
                  }
                  value={values.incident_type_id ?? null}
                />
              </label>
              <div className="md:col-span-2">
                <SafetyLossTypeMultiSelect
                  onChange={updateLossTypes}
                  otherText={values.loss_type_other ?? ''}
                  values={{
                    lossTypeIds: [
                      values.loss_type_primary_id,
                      values.loss_type_secondary_id,
                      values.loss_type_tertiary_id,
                    ].filter(
                      (value): value is number => typeof value === 'number'
                    ),
                    otherSelected:
                      values.loss_type_other !== null &&
                      values.loss_type_other !== undefined,
                  }}
                />
              </div>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Risk level</span>
                <select
                  aria-label="Risk level"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                  onChange={(event) =>
                    updateField(
                      'risk_band',
                      (event.target.value ||
                        null) as SafetyIncidentPhase1Values['risk_band']
                    )
                  }
                  value={values.risk_band ?? ''}
                >
                  <option value="">Select risk level</option>
                  <option value="GREEN">Low</option>
                  <option value="YELLOW">Medium</option>
                  <option value="RED">High</option>
                </select>
                <span className="block text-xs text-slate-500">
                  Check needed:{' '}
                  {derivedInvestigationDepthLabel(values.risk_band)}
                </span>
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Was office informed?</span>
                <select
                  aria-label="Was office informed?"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                  onChange={(event) => {
                    const nextValue =
                      event.target.value === ''
                        ? null
                        : event.target.value === 'YES';
                    setValues((current) => ({
                      ...current,
                      office_notification_mode: nextValue
                        ? current.office_notification_mode
                        : null,
                      office_notified: nextValue,
                    }));
                  }}
                  value={
                    values.office_notified === null ||
                    values.office_notified === undefined
                      ? ''
                      : values.office_notified
                        ? 'YES'
                        : 'NO'
                  }
                >
                  <option value="">Select</option>
                  <option value="YES">Yes</option>
                  <option value="NO">No</option>
                </select>
              </label>
              {values.office_notified ? (
                <label className="space-y-2 text-sm text-slate-700">
                  <span className="font-medium">How was office informed?</span>
                  <select
                    aria-label="How was office informed?"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                    onChange={(event) =>
                      updateField(
                        'office_notification_mode',
                        (event.target.value ||
                          null) as SafetyIncidentPhase1Values['office_notification_mode']
                      )
                    }
                    value={values.office_notification_mode ?? ''}
                  >
                    <option value="">Select how</option>
                    <option value="ON_CALL">On call</option>
                    <option value="EMAIL">On email</option>
                  </select>
                </label>
              ) : null}
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Vessel</span>
                {vesselOptions.length > 0 ? (
                  <select
                    aria-label="Vessel"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-600"
                    disabled={vesselIdentityLocked}
                    onChange={(event) => {
                      const nextVesselId = event.target.value;
                      const nextOption = vesselOptions.find(
                        (option) => option.id === nextVesselId
                      );
                      setValues((current) => ({
                        ...current,
                        vessel_code: nextOption?.code ?? '',
                        vessel_id: nextVesselId,
                      }));
                    }}
                    value={values.vessel_id}
                  >
                    <option value="">Select vessel</option>
                    {vesselOptions.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    aria-label="Vessel"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-600"
                    disabled={vesselIdentityLocked}
                    onChange={(event) =>
                      updateField('vessel_id', event.target.value)
                    }
                    value={
                      vesselIdentityLocked
                        ? vesselInputDisplayValue
                        : values.vessel_id
                    }
                  />
                )}
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Vessel code</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-600"
                  disabled
                  readOnly
                  value={vesselCodeDisplayValue}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Incident time</span>
                <input
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField(
                      'occurred_at',
                      toUtcIsoTimestamp(event.target.value) ?? null
                    )
                  }
                  type="datetime-local"
                  value={toDateTimeLocalValue(values.occurred_at)}
                />
              </label>
              <div className="grid gap-4 md:col-span-2 md:grid-cols-2">
                <label className="space-y-2 text-sm text-slate-700">
                  <span className="font-medium">Report time</span>
                  <input
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                    onChange={(event) =>
                      updateField(
                        'reported_at',
                        toUtcIsoTimestamp(event.target.value) ?? null
                      )
                    }
                    type="datetime-local"
                    value={toDateTimeLocalValue(values.reported_at)}
                  />
                </label>
                <label className="space-y-2 text-sm text-slate-700">
                  <span className="font-medium">
                    Shore Assistance Required
                  </span>
                  <select
                    aria-label="Shore Assistance Required"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                    onChange={(event) =>
                      updateField(
                        'shore_assistance_required',
                        event.target.value === ''
                          ? null
                          : event.target.value === 'YES'
                      )
                    }
                    value={
                      values.shore_assistance_required === null ||
                      values.shore_assistance_required === undefined
                        ? ''
                        : values.shore_assistance_required
                          ? 'YES'
                          : 'NO'
                    }
                  >
                    <option value="">Select</option>
                    <option value="YES">Yes</option>
                    <option value="NO">No</option>
                  </select>
                </label>
              </div>
              <div className="grid gap-4 md:col-span-2 md:grid-cols-2">
                <label className="space-y-2 text-sm text-slate-700">
                  <span className="font-medium">Latitude</span>
                  <input
                    aria-label="Latitude"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                    max={90}
                    min={-90}
                    onChange={(event) =>
                      updateField(
                        'latitude',
                        toNullableNumber(event.target.value)
                      )
                    }
                    placeholder="e.g. 19.0760"
                    step="0.000001"
                    type="number"
                    value={toNumberInputValue(values.latitude)}
                  />
                </label>
                <label className="space-y-2 text-sm text-slate-700">
                  <span className="font-medium">Longitude</span>
                  <input
                    aria-label="Longitude"
                    className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                    max={180}
                    min={-180}
                    onChange={(event) =>
                      updateField(
                        'longitude',
                        toNullableNumber(event.target.value)
                      )
                    }
                    placeholder="e.g. 72.8777"
                    step="0.000001"
                    type="number"
                    value={toNumberInputValue(values.longitude)}
                  />
                </label>
              </div>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Location of Vessel</span>
                <input
                  aria-label="Location of Vessel"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('vessel_location', event.target.value)
                  }
                  value={values.vessel_location ?? ''}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Location on Board</span>
                <input
                  aria-label="Location on Board"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('onboard_location', event.target.value)
                  }
                  value={values.onboard_location ?? ''}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Departure Date</span>
                <input
                  aria-label="Departure Date"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('departure_date', event.target.value || null)
                  }
                  type="date"
                  value={values.departure_date ?? ''}
                />
              </label>
              <label className="space-y-2 text-sm text-slate-700">
                <span className="font-medium">Vessel Condition</span>
                <select
                  aria-label="Vessel Condition"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                  onChange={(event) =>
                    updateField(
                      'vessel_condition',
                      event.target
                        .value as SafetyIncidentPhase1Values['vessel_condition']
                    )
                  }
                  value={values.vessel_condition ?? ''}
                >
                  <option value="">Select</option>
                  <option value="LOADED">Loaded</option>
                  <option value="BALLAST">Ballast</option>
                </select>
              </label>
            </div>

            <section className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">
                    Weather Condition
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    Add weather and sea details at the time of the incident.
                  </p>
                </div>
                {weatherOptionsStatus === 'error' ? (
                  <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
                    Options not loaded
                  </span>
                ) : null}
              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">
                {WEATHER_DROPDOWN_FIELDS.map((item) => {
                  const options = weatherOptionsByField[item.fieldKey] ?? [];
                  return (
                    <label
                      className="space-y-2 text-sm text-slate-700"
                      key={item.field}
                    >
                      <span className="font-medium">{item.label}</span>
                      <select
                        aria-label={item.label}
                        className="min-h-[44px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2"
                        onChange={(event) =>
                          updateWeatherDropdownField(
                            item.field,
                            event.target.value || null
                          )
                        }
                        value={
                          (values[item.field] as string | null | undefined) ??
                          ''
                        }
                      >
                        <option value="">
                          {weatherOptionsStatus === 'loading'
                            ? 'Loading options...'
                            : options.length
                              ? `Select ${item.label}`
                              : 'No options added yet'}
                        </option>
                        {options.map((option) => (
                          <option key={option.id} value={option.id}>
                            {option.option_label}
                          </option>
                        ))}
                      </select>
                    </label>
                  );
                })}

                <label className="space-y-2 text-sm text-slate-700">
                  <span className="font-medium">Current Strength (knots)</span>
                  <textarea
                    aria-label="Current Strength knots"
                    className="min-h-[96px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 leading-6"
                    onChange={(event) =>
                      updateField(
                        'weather_current_strength_knots',
                        event.target.value || null
                      )
                    }
                    value={values.weather_current_strength_knots ?? ''}
                  />
                </label>

                <label className="space-y-2 text-sm text-slate-700">
                  <span className="font-medium">
                    Ambient Temperature (Deg C)
                  </span>
                  <textarea
                    aria-label="Ambient Temperature Deg C"
                    className="min-h-[96px] w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 leading-6"
                    onChange={(event) =>
                      updateField(
                        'weather_ambient_temperature_c',
                        event.target.value || null
                      )
                    }
                    value={values.weather_ambient_temperature_c ?? ''}
                  />
                </label>
              </div>
            </section>

            <label className="block space-y-2 text-sm text-slate-700">
              <span className="font-medium">What happened?</span>
              <textarea
                aria-label="What happened"
                className="min-h-[220px] w-full rounded-3xl border border-slate-200 px-4 py-3 leading-6"
                onChange={(event) =>
                  updateField('narrative', event.target.value)
                }
                value={values.narrative}
              />
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-500">
                  Write at least 200 characters. Use simple words.
                </span>
                <span
                  className={
                    narrativeLength >= 200
                      ? 'text-emerald-700'
                      : 'text-amber-700'
                  }
                >
                  {narrativeLength}/200
                </span>
              </div>
            </label>

            <SafetyExternalPartyInjuryForm
              enabled={Boolean(values.external_party_injury)}
              onChange={updateExternalParty}
              value={values.external_party_injury ?? null}
              vesselId={values.vessel_id}
            />
          </div>

          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Reporter Details
                </h2>
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  These details are used for the report record and follow-up
                  responsibility.
                </p>
              </div>
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Reporter user ID</span>
                <input
                  aria-label="Reporter user ID"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('reporter_user_id', event.target.value)
                  }
                  readOnly={isVesselUser}
                  value={values.reporter_user_id}
                />
              </label>
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Reporter name</span>
                <input
                  aria-label="Reporter name"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('reporter_name', event.target.value)
                  }
                  readOnly={isVesselUser}
                  value={values.reporter_name}
                />
              </label>
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Reporter rank</span>
                <input
                  aria-label="Reporter rank"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('reporter_rank', event.target.value)
                  }
                  readOnly={isVesselUser}
                  value={values.reporter_rank}
                />
              </label>
              <label className="block space-y-2 text-sm text-slate-700">
                <span className="font-medium">Person in charge</span>
                <input
                  aria-label="Person in charge"
                  className="min-h-[44px] w-full rounded-2xl border border-slate-200 px-3 py-2"
                  onChange={(event) =>
                    updateField('pic_candidate_id', event.target.value)
                  }
                  value={values.pic_candidate_id ?? ''}
                />
              </label>
            </div>
          </section>

          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Save or Submit
                </h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {mode === 'create'
                    ? 'Save if you want to finish later. Submit when all required details are filled.'
                    : 'Save changes to update the existing incident before office approval.'}
                </p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                {mode === 'create' ? (
                  <button
                    className="min-h-[44px] rounded-full border border-slate-300 px-5 py-2 text-sm font-medium text-slate-700"
                    onClick={handleSaveDraft}
                    type="button"
                  >
                    Save draft
                  </button>
                ) : null}
                <button
                  aria-disabled={!submitReady}
                  className="min-h-[44px] rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white"
                  onClick={mode === 'create' ? handleSubmit : handleSaveDraft}
                  type="button"
                >
                  {mode === 'create' ? 'Submit report' : 'Save changes'}
                </button>
              </div>
            </div>
          </section>
        </section>
      </section>

      <SafetySelfReportGuardModal
        message="The reporter and person in charge are the same person."
        onAcknowledge={() => {
          setShowConflictGuard(false);
          const result = safetyIncidentPhase1SubmitSchema.safeParse(
            currentPhase1PayloadValues(values)
          );
          if (result.success) {
            onSubmitPhase?.(result.data);
          }
        }}
        onCancel={() => setShowConflictGuard(false)}
        open={showConflictGuard}
        requiredApproverRole="MASTER"
      />
    </>
  );
}
