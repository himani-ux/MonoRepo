import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

const EXPECTED_INCIDENT_TYPE_NAMES = [
  'Collision',
  'Grounding',
  'Stranding',
  'Touched bottom at berth / anchorage',
  'Touched bottom in rivers / canals',
  'Allision with Jetty / Berth / Locks',
  'Allision with other Vessels',
  'Allision with ice',
  'Allision with Navigation Aids / Buoys / Other objects',
  'Foundering',
  'Capsizing / Loss of Stability',
  'Flooding',
  'Explosion',
  'Fire',
  'Cargo Damage',
  'Hull / Structural Failure',
  'The fouling or damaging by a vessel of a pipeline or submarine cable',
  'The fouling or damaging by a vessel of an aid to navigation other than allision',
  'The fouling or damaging by a vessel of a port/terminal installation',
  "Failure of ship's equipment resulting in loss of vessel's electrical power",
  "Failure of ship's equipment resulting in loss of propulsion",
  "Failure of ship's equipment resulting in loss of steering capabilities",
  "Failure of ship's equipment resulting in a delay of cargo operation of more than 6 hours",
  "Failure of ship's equipment rendering the vessel in any other way unseaworthy",
  "Failure of ship's equipment or hull resulting in cargo damage",
  'Crew Injury',
  'Pollution',
  'Breach of Local Regulations',
  'Stowaway Incident',
  'Security Incident',
  'Breach of Cyber Security',
  'Other',
];

const phase1FormMocks = vi.hoisted(() => ({
  getIncidentWeatherOptions: vi.fn(),
  getInjuryDropdownOptions: vi.fn(),
  getReferenceIncidentTypes: vi.fn(),
  getReferenceLossTypes: vi.fn(),
  getVesselCrew: vi.fn(),
  toast: vi.fn(),
}));

vi.mock('../../../hooks/use-auth', () => ({
  useAuth: () => ({
    isVessel: true,
    user: {
      crew_id: 'CRW0001',
      full_name: 'Test Master',
      rank: 'MASTER',
      role: 'VESSEL_MASTER',
      vessel_code: 'ARY',
      vessel_id: 'vessel-1',
      vessel_name: 'ARYA',
      vessel_ids: ['vessel-1'],
      vessel_names: ['ARYA'],
    },
  }),
}));

vi.mock('../../../hooks/use-toast', () => ({
  useToast: () => ({ toast: phase1FormMocks.toast }),
}));

vi.mock('../../../hooks/safety/use-draft-autosave', () => ({
  useDraftAutosave: () => ({
    lastSavedAt: null,
    saveDraftNow: vi
      .fn()
      .mockResolvedValue({ updatedAt: '2026-06-23T00:00:00Z' }),
    status: 'ready',
  }),
}));

vi.mock('../../../lib/safety/digital-signature', () => ({
  getSafetyDeviceFingerprint: () => 'test-device',
}));

vi.mock('../../../lib/api/masters', () => ({
  mastersApi: {
    getVesselCrew: phase1FormMocks.getVesselCrew,
  },
}));

vi.mock('../../../lib/api/safety', () => ({
  safetyApi: {
    getIncidentWeatherOptions: phase1FormMocks.getIncidentWeatherOptions,
    getInjuryDropdownOptions: phase1FormMocks.getInjuryDropdownOptions,
    getReferenceIncidentTypes: phase1FormMocks.getReferenceIncidentTypes,
    getReferenceLossTypes: phase1FormMocks.getReferenceLossTypes,
  },
}));

import { SafetyIncidentPhase1Form } from './phase1-form';

describe('SafetyIncidentPhase1Form injury section', () => {
  it('does not show internal incident id or autosave badges in the phase 1 header', async () => {
    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.getVesselCrew.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([]);

    render(
      <SafetyIncidentPhase1Form
        incidentId="21b10f68-b0b2-4d72-9d3f-7efa925d0f52"
        mode="edit"
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: 'Tell Us What Happened' })
      ).toBeTruthy();
    });

    expect(
      screen.queryByText(/Incident 21b10f68-b0b2-4d72-9d3f-7efa925d0f52/i)
    ).toBeNull();
    expect(screen.queryByText(/Auto-save ready/i)).toBeNull();
    expect(screen.queryByText(/Auto-saved/i)).toBeNull();
    expect(screen.queryByText(/Draft restored/i)).toBeNull();
  });

  it('auto-fills and disables vessel identity fields while preserving save payload values', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue(undefined);
    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.getVesselCrew.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([]);

    render(
      <SafetyIncidentPhase1Form
        initialValues={{
          schema_version: 1,
          vessel_code: 'ARY',
          vessel_id: 'vessel-1',
        }}
        mode="edit"
        onSaveDraft={onSaveDraft}
      />
    );

    const vesselField = await screen.findByLabelText('Vessel');
    const vesselCodeField = screen.getByLabelText('Vessel code');

    expect(vesselField).toBeDisabled();
    expect(vesselField).toHaveValue('vessel-1');
    expect(vesselCodeField).toBeDisabled();
    expect(vesselCodeField).toHaveValue('ARY');

    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => {
      expect(onSaveDraft).toHaveBeenCalled();
    });
    expect(onSaveDraft.mock.calls[0][0]).toMatchObject({
      vessel_code: 'ARY',
      vessel_id: 'vessel-1',
    });
  });

  it('shows the current incident type dropdown list and hides retired options', async () => {
    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([
      {
        active: true,
        description: 'Removed option',
        id: 'missing-type',
        imo_reportable: true,
        legacy_int_id: 9,
        type_code: 'IMO_MISSING_VESSEL',
        type_name: 'Missing vessel',
      },
      ...EXPECTED_INCIDENT_TYPE_NAMES.map((typeName, index) => ({
        active: true,
        description: 'Current option',
        id: `incident-type-${index + 1}`,
        imo_reportable: true,
        legacy_int_id: index + 1,
        type_code: `INC_TEST_${index + 1}`,
        type_name: typeName,
      })),
    ]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.getVesselCrew.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([]);

    render(<SafetyIncidentPhase1Form mode="create" />);

    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Other' })).toBeTruthy();
    });

    const incidentTypeSelect = screen.getByRole('combobox', {
      name: 'What type of incident?',
    });
    const renderedOptions = Array.from(
      incidentTypeSelect.querySelectorAll('option')
    ).map((option) => option.textContent);

    expect(renderedOptions).toEqual([
      'Select incident type',
      ...EXPECTED_INCIDENT_TYPE_NAMES,
    ]);
    expect(screen.queryByRole('option', { name: 'Missing vessel' })).toBeNull();

    expect(screen.queryByLabelText('Specify other incident type')).toBeNull();
    await userEvent.selectOptions(incidentTypeSelect, String(EXPECTED_INCIDENT_TYPE_NAMES.length));
    expect(screen.getByLabelText('Specify other incident type')).toBeTruthy();
  }, 10000);

  it('shows simplified office, position, reporting, and weather fields on the incident report', async () => {
    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.getVesselCrew.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([]);

    render(<SafetyIncidentPhase1Form mode="create" />);

    await waitFor(() => {
      expect(
        screen.getByRole('option', { name: 'Select incident type' })
      ).toBeTruthy();
      expect(
        screen.getByRole('button', { name: 'What was affected?' }).textContent
      ).toContain('Select what was affected');
      expect(
        screen.getByRole('option', { name: 'Good: More than 5 nautical miles' })
      ).toBeTruthy();
    });
    expect(
      screen.getByRole('combobox', { name: 'Was office informed?' })
    ).toBeTruthy();
    expect(screen.queryByLabelText('Was office told?')).toBeNull();

    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: 'Was office informed?' }),
      'YES'
    );
    expect(
      screen.getByRole('combobox', { name: 'How was office informed?' })
    ).toBeTruthy();
    expect(screen.queryByRole('option', { name: 'On WhatsApp' })).toBeNull();
    expect(screen.queryByLabelText('How was office told?')).toBeNull();

    expect(
      screen.getByRole('combobox', {
        name: 'Was a Risk Assessment carried out?',
      })
    ).toBeTruthy();
    expect(
      screen.getByRole('combobox', {
        name: 'Was Toolbox Meeting carried out?',
      })
    ).toBeTruthy();
    expect(
      screen.getByRole('combobox', { name: 'Was a Permit Issue?' })
    ).toBeTruthy();
    expect(screen.getByLabelText('Type of Activity')).toBeTruthy();
    expect(screen.getByLabelText('Describe What happened?')).toBeTruthy();

    const reportTimeInput = screen.getByLabelText('Report time');
    const shoreAssistanceInput = screen.getByRole('combobox', {
      name: 'Shore Assistance Required',
    });
    const reportContextRow = reportTimeInput.closest('div');
    const latitudeInput = screen.getByRole('spinbutton', { name: 'Latitude' });
    const longitudeInput = screen.getByRole('spinbutton', {
      name: 'Longitude',
    });
    const coordinateRow = latitudeInput.closest('div');

    expect(reportTimeInput).toBeTruthy();
    expect(shoreAssistanceInput).toBeTruthy();
    expect(reportContextRow).toContainElement(shoreAssistanceInput);
    expect(latitudeInput).toBeTruthy();
    expect(longitudeInput).toBeTruthy();
    expect(coordinateRow).toContainElement(longitudeInput);
    expect(coordinateRow).not.toContainElement(shoreAssistanceInput);
    const vesselLocationSelect = screen.getByRole('combobox', {
      name: 'Location of Vessel',
    });
    expect(vesselLocationSelect).toBeTruthy();
    expect(
      screen.getByRole('option', { name: 'At Sea (Open sea condition)' })
    ).toBeTruthy();
    expect(
      screen.getByRole('option', { name: 'At Sea (Coastal passage)' })
    ).toBeTruthy();
    expect(screen.getByRole('option', { name: 'In Port' })).toBeTruthy();
    expect(screen.getByRole('option', { name: 'At Anchorage' })).toBeTruthy();
    expect(screen.queryByLabelText('Specify Location of Vessel')).toBeNull();
    await userEvent.selectOptions(vesselLocationSelect, 'In Port');
    expect(screen.getByLabelText('Specify Location of Vessel')).toBeTruthy();
    expect(screen.getByLabelText('Location on Board')).toBeTruthy();
    expect(screen.queryByLabelText('Last Port')).toBeNull();
    expect(screen.getByLabelText('Departure Date')).toBeTruthy();
    expect(
      screen
        .getByLabelText('Location on Board')
        .compareDocumentPosition(
          screen.getByLabelText('Was a Risk Assessment carried out?')
        ) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    expect(
      screen
        .getByLabelText('Type of Activity')
        .compareDocumentPosition(screen.getByLabelText('Departure Date')) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    expect(
      screen.getByRole('combobox', { name: 'Vessel Condition' })
    ).toBeTruthy();
    expect(screen.queryByLabelText('Ice condition on-board')).toBeNull();
    expect(screen.queryByLabelText('Ice condition at sea')).toBeNull();
  }, 10000);

  it('omits hidden legacy phase 1 fields from save payloads', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue(undefined);

    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.getVesselCrew.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([]);

    render(
      <SafetyIncidentPhase1Form
        initialValues={{
          last_port: 'Singapore',
          office_notification_mode: 'WHATSAPP',
          office_notified: true,
          vessel_id: 'vessel-1',
          weather_ice_condition_at_sea_id: 'ice-sea',
          weather_ice_condition_onboard_id: 'ice-board',
        }}
        mode="edit"
        onSaveDraft={onSaveDraft}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save changes' })).toBeTruthy();
    });

    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => {
      expect(onSaveDraft).toHaveBeenCalled();
    });

    const payload = onSaveDraft.mock.calls[0][0];
    expect(payload).not.toHaveProperty('last_port');
    expect(payload).not.toHaveProperty('weather_ice_condition_at_sea_id');
    expect(payload).not.toHaveProperty('weather_ice_condition_onboard_id');
    expect(payload.office_notification_mode).toBeNull();
  });

  it('saves changes when a legacy Phase 1 injury only has removed estimated-cost fields', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue(undefined);

    phase1FormMocks.toast.mockClear();
    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.getVesselCrew.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([]);

    render(
      <SafetyIncidentPhase1Form
        initialValues={{
          external_party_injury: {
            cost_medicines_onboard: '125',
            injured_person_type: 'NON_CREW',
            miscellaneous_expenses_reason: 'Legacy cost note',
          },
          schema_version: 1,
          vessel_id: 'vessel-1',
        }}
        mode="edit"
        onSaveDraft={onSaveDraft}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save changes' })).toBeTruthy();
    });

    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => {
      expect(onSaveDraft).toHaveBeenCalled();
    });

    expect(onSaveDraft.mock.calls[0][0].external_party_injury).toBeNull();
    expect(phase1FormMocks.toast).not.toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Some details are missing' })
    );
  });

  it('saves changes when legacy Phase 1 injury optional text fields are null', async () => {
    const onSaveDraft = vi.fn().mockResolvedValue(undefined);

    phase1FormMocks.toast.mockClear();
    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.getVesselCrew.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([]);

    render(
      <SafetyIncidentPhase1Form
        initialValues={{
          external_party_injury: {
            company_name: 'Harbor Services',
            first_aid_details: null,
            injured_person_type: 'NON_CREW',
            notes: null,
            party_name: 'Alex Pilot',
            party_type: 'PILOT',
            severity: 'First aid',
            what_happened_narrative: null,
          } as never,
          schema_version: 1,
          vessel_id: 'vessel-1',
        }}
        mode="edit"
        onSaveDraft={onSaveDraft}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save changes' })).toBeTruthy();
    });

    await userEvent.click(screen.getByRole('button', { name: 'Save changes' }));

    await waitFor(() => {
      expect(onSaveDraft).toHaveBeenCalled();
    });

    const injuryPayload = onSaveDraft.mock.calls[0][0].external_party_injury;
    expect(injuryPayload).toMatchObject({
      company_name: 'Harbor Services',
      party_name: 'Alex Pilot',
      party_type: 'PILOT',
      severity: 'First aid',
    });
    expect(injuryPayload).not.toHaveProperty('notes');
    expect(injuryPayload).not.toHaveProperty('first_aid_details');
    expect(injuryPayload).not.toHaveProperty('what_happened_narrative');
    expect(phase1FormMocks.toast).not.toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Some details are missing' })
    );
  });

  it('keeps the create form visible when injury is enabled and Crew is selected', async () => {
    phase1FormMocks.getIncidentWeatherOptions.mockResolvedValue([]);
    phase1FormMocks.getReferenceIncidentTypes.mockResolvedValue([]);
    phase1FormMocks.getReferenceLossTypes.mockResolvedValue([]);
    phase1FormMocks.getVesselCrew.mockResolvedValue([]);
    phase1FormMocks.getInjuryDropdownOptions.mockResolvedValue([
      {
        active: true,
        display_order: 1,
        field_key: 'TYPE_OF_ACTIVITY',
        field_label: 'Type of Activity',
        id: 'activity-other',
        option_label: 'Others(Specify)',
      },
      {
        active: true,
        display_order: 1,
        field_key: 'NATURE_OF_INJURY',
        field_label: 'Nature of Injury',
        id: 'nature-other',
        option_label: 'Other (specify)',
      },
    ]);

    render(<SafetyIncidentPhase1Form mode="create" />);

    expect(screen.queryByText('First Checks')).toBeNull();

    await userEvent.click(
      screen.getByRole('button', { name: 'Record injury' })
    );
    await userEvent.click(screen.getByRole('radio', { name: 'Crew' }));

    await waitFor(() => {
      expect(screen.getByText('Rank of person')).toBeTruthy();
    });
    expect(screen.getByText('Tell Us What Happened')).toBeTruthy();
  });
});
