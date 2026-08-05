import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { useState } from 'react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

const injuryFormMocks = vi.hoisted(() => ({
  getInjuryDropdownOptions: vi.fn(),
  getVesselCrew: vi.fn(),
}));

vi.mock('../../../lib/api/masters', () => ({
  mastersApi: {
    getVesselCrew: injuryFormMocks.getVesselCrew,
  },
}));

vi.mock('../../../lib/api/safety', () => ({
  safetyApi: {
    getInjuryDropdownOptions: injuryFormMocks.getInjuryDropdownOptions,
  },
}));

import {
  SafetyExternalPartyInjuryForm,
  type SafetyExternalPartyInjuryValues,
} from './external-party-injury-form';

describe('SafetyExternalPartyInjuryForm', () => {
  it('renders crew injury dropdown fields from master options', async () => {
    injuryFormMocks.getVesselCrew.mockResolvedValue([]);
    injuryFormMocks.getInjuryDropdownOptions.mockImplementation(
      (fieldKey?: string) => {
        if (fieldKey === 'TYPE_OF_ACTIVITY') {
          return Promise.resolve([]);
        }

        return Promise.resolve([
          {
            id: 'nature-1',
            field_key: 'NATURE_OF_INJURY',
            field_label: 'Nature of Injury',
            option_label: 'Amputation',
            display_order: 1,
            active: true,
          },
          {
            id: 'nature-other',
            field_key: 'NATURE_OF_INJURY',
            field_label: 'Nature of Injury',
            option_label: 'Other (specify)',
            display_order: 2,
            active: true,
          },
          {
            id: 'source-1',
            field_key: 'SOURCE_OF_INJURY',
            field_label: 'Source of Injury',
            option_label: 'Electricity',
            display_order: 1,
            active: true,
          },
          {
            id: 'body-1',
            field_key: 'AFFECTED_BODY_AREA',
            field_label: 'Affected Areas of the Body',
            option_label: 'Head',
            display_order: 1,
            active: true,
          },
        ]);
      }
    );

    render(
      <SafetyExternalPartyInjuryForm
        enabled
        onChange={vi.fn()}
        value={{
          company_name: '',
          injured_person_type: 'CREW',
          party_name: '',
          party_type: '',
          severity: '',
        }}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Amputation' })).toBeTruthy();
    });
    expect(screen.getByRole('option', { name: 'Electricity' })).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Head' })).toBeTruthy();
  });

  it('keeps the crew injury screen visible after clicking a Yes option', async () => {
    injuryFormMocks.getVesselCrew.mockResolvedValue([]);
    injuryFormMocks.getInjuryDropdownOptions.mockImplementation(
      (fieldKey?: string) => {
        if (fieldKey === 'TYPE_OF_ACTIVITY') {
          return Promise.resolve([]);
        }

        return Promise.resolve([
          {
            id: 'nature-1',
            field_key: 'NATURE_OF_INJURY',
            field_label: 'Nature of Injury',
            option_label: 'Amputation',
            display_order: 1,
            active: true,
          },
        ]);
      }
    );

    function ControlledInjuryForm() {
      const [value, setValue] =
        useState<SafetyExternalPartyInjuryValues | null>({
          company_name: '',
          injured_person_type: 'CREW',
          party_name: '',
          party_type: '',
          severity: '',
        });

      return (
        <SafetyExternalPartyInjuryForm
          enabled={Boolean(value)}
          onChange={setValue}
          value={value}
        />
      );
    }

    render(<ControlledInjuryForm />);

    const yesButtons = screen.getAllByRole('button', { name: 'Yes' });
    for (const yesButton of yesButtons) {
      await userEvent.click(yesButton);
    }

    expect(screen.getByText('Investigation - Narrative')).toBeTruthy();
    expect(screen.queryByText('Describe What Happened')).toBeNull();
    expect(screen.getByText('OCIMF Reporting')).toBeTruthy();
    expect(screen.queryByText('Estimated Costs')).toBeNull();
  });

  it('does not render or emit legacy Phase 1 estimated cost fields', async () => {
    const onChange = vi.fn();

    render(
      <SafetyExternalPartyInjuryForm
        enabled
        onChange={onChange}
        value={{
          company_name: '',
          cost_medicines_onboard: '125',
          injured_person_type: 'NON_CREW',
          miscellaneous_expenses_reason: 'Taxi receipt',
          party_name: '',
          party_type: 'PILOT',
          severity: '',
        }}
      />
    );

    expect(screen.queryByText('Estimated Costs')).toBeNull();
    expect(
      screen.queryByRole('group', {
        name: 'Do you want to add estimated cost details?',
      })
    ).toBeNull();
    expect(screen.queryByLabelText('Cost for Medicines Given Onboard')).toBe(
      null
    );

    fireEvent.change(screen.getByLabelText('Person name'), {
      target: { value: 'Alex' },
    });

    const lastValue = onChange.mock.calls.at(-1)?.[0];
    expect(lastValue).toMatchObject({ party_name: 'Alex' });
    expect(lastValue).not.toHaveProperty('cost_medicines_onboard');
    expect(lastValue).not.toHaveProperty('miscellaneous_expenses_reason');
  });

  it('does not crash when crew lookup returns a malformed payload after switching to crew', async () => {
    injuryFormMocks.getVesselCrew.mockResolvedValueOnce(
      null as unknown as never
    );
    injuryFormMocks.getInjuryDropdownOptions.mockImplementation(
      (fieldKey?: string) => {
        if (fieldKey === 'TYPE_OF_ACTIVITY') {
          return Promise.resolve([]);
        }

        return Promise.resolve([]);
      }
    );

    function ControlledInjuryForm() {
      const [value, setValue] =
        useState<SafetyExternalPartyInjuryValues | null>({
          company_name: '',
          injured_person_type: 'NON_CREW',
          party_name: '',
          party_type: 'PILOT',
          severity: '',
        });

      return (
        <SafetyExternalPartyInjuryForm
          enabled={Boolean(value)}
          onChange={setValue}
          value={value}
          vesselId="vessel-1"
        />
      );
    }

    render(<ControlledInjuryForm />);

    await userEvent.click(screen.getByRole('radio', { name: 'Crew' }));

    await waitFor(() => {
      expect(
        screen.getByRole('combobox', { name: 'Type of Activity' })
      ).toBeTruthy();
    });
  });

  it('does not crash when injury dropdown payloads contain malformed options after switching to crew', async () => {
    injuryFormMocks.getVesselCrew.mockResolvedValue([]);
    injuryFormMocks.getInjuryDropdownOptions.mockImplementation(
      (fieldKey?: string) => {
        if (fieldKey === 'TYPE_OF_ACTIVITY') {
          return Promise.resolve([
            { id: 'broken-activity', field_key: 'TYPE_OF_ACTIVITY' },
            {
              id: 'act-1',
              field_key: 'TYPE_OF_ACTIVITY',
              option_label: 'Hot work',
              display_order: 1,
              active: true,
            },
          ]);
        }

        return Promise.resolve([
          { id: 'broken-nature', field_key: 'NATURE_OF_INJURY' },
          {
            id: 'nature-1',
            field_key: 'NATURE_OF_INJURY',
            option_label: 'Cuts / Lacerations',
            display_order: 1,
            active: true,
          },
        ]);
      }
    );

    function ControlledInjuryForm() {
      const [value, setValue] =
        useState<SafetyExternalPartyInjuryValues | null>({
          company_name: '',
          injured_person_type: 'NON_CREW',
          party_name: '',
          party_type: 'PILOT',
          severity: '',
        });

      return (
        <SafetyExternalPartyInjuryForm
          enabled={Boolean(value)}
          onChange={setValue}
          value={value}
          vesselId="vessel-1"
        />
      );
    }

    render(<ControlledInjuryForm />);

    await userEvent.click(screen.getByRole('radio', { name: 'Crew' }));

    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Hot work' })).toBeTruthy();
    });
    expect(screen.getByText('Investigation - Narrative')).toBeTruthy();
    expect(screen.queryByText('Describe What Happened')).toBeNull();
  });

  it('keeps shared reporting context fields out of the injury subsection', async () => {
    injuryFormMocks.getVesselCrew.mockResolvedValue([]);
    injuryFormMocks.getInjuryDropdownOptions.mockResolvedValue([]);

    render(
      <SafetyExternalPartyInjuryForm
        enabled
        onChange={vi.fn()}
        value={{
          company_name: '',
          injured_person_type: 'NON_CREW',
          party_name: '',
          party_type: 'PILOT',
          severity: '',
        }}
      />
    );

    expect(
      screen.queryByRole('heading', { name: 'Injury Reporting' })
    ).toBeNull();
    expect(screen.queryByLabelText('Shore Assistance Required')).toBeNull();
    expect(screen.queryByLabelText('Location of Vessel')).toBeNull();
    expect(screen.queryByLabelText('Location on Board')).toBeNull();
    expect(screen.queryByLabelText('Last Port')).toBeNull();
    expect(screen.queryByLabelText('Departure Date')).toBeNull();
    expect(screen.queryByLabelText('Vessel Condition')).toBeNull();
    expect(
      screen.queryByRole('combobox', { name: 'Type of Activity' })
    ).toBeNull();
  });

  it('keeps crew injury screen visible when restored draft has custom dropdown values', async () => {
    injuryFormMocks.getVesselCrew.mockResolvedValue([]);
    injuryFormMocks.getInjuryDropdownOptions.mockImplementation(
      (fieldKey?: string) => {
        if (fieldKey === 'TYPE_OF_ACTIVITY') {
          return Promise.resolve([
            {
              id: 'act-other',
              field_key: 'TYPE_OF_ACTIVITY',
              field_label: 'Type of Activity',
              option_label: 'Others(Specify)',
              display_order: 1,
              active: true,
            },
          ]);
        }

        return Promise.resolve([
          {
            id: 'nature-other',
            field_key: 'NATURE_OF_INJURY',
            field_label: 'Nature of Injury',
            option_label: 'Other (specify)',
            display_order: 1,
            active: true,
          },
        ]);
      }
    );

    function ControlledInjuryForm() {
      const [value, setValue] =
        useState<SafetyExternalPartyInjuryValues | null>({
          company_name: '',
          crew_activity_type: 'Custom restored activity',
          injured_person_type: 'NON_CREW',
          nature_of_injury: 'Custom restored injury',
          party_name: '',
          party_type: 'PILOT',
          severity: '',
        });

      return (
        <SafetyExternalPartyInjuryForm
          enabled={Boolean(value)}
          onChange={setValue}
          value={value}
          vesselId="vessel-1"
        />
      );
    }

    render(<ControlledInjuryForm />);

    await userEvent.click(screen.getByRole('radio', { name: 'Crew' }));

    await waitFor(() => {
      expect(screen.getByDisplayValue('Custom restored activity')).toBeTruthy();
    });
    expect(screen.getByText('Investigation - Narrative')).toBeTruthy();
    expect(screen.queryByText('Describe What Happened')).toBeNull();
  });

  it('renders type of activity as a master-backed dropdown with others specify support', async () => {
    injuryFormMocks.getVesselCrew.mockResolvedValue([]);
    injuryFormMocks.getInjuryDropdownOptions.mockImplementation(
      (fieldKey?: string) => {
        if (fieldKey === 'TYPE_OF_ACTIVITY') {
          return Promise.resolve([
            {
              id: 'act-1',
              field_key: 'TYPE_OF_ACTIVITY',
              field_label: 'Type of Activity',
              option_label: 'Anchoring',
              display_order: 1,
              active: true,
            },
            {
              id: 'act-other',
              field_key: 'TYPE_OF_ACTIVITY',
              field_label: 'Type of Activity',
              option_label: 'Others(Specify)',
              display_order: 2,
              active: true,
            },
          ]);
        }

        return Promise.resolve([]);
      }
    );

    function ControlledInjuryForm() {
      const [value, setValue] =
        useState<SafetyExternalPartyInjuryValues | null>({
          company_name: '',
          injured_person_type: 'NON_CREW',
          party_name: '',
          party_type: 'PILOT',
          severity: '',
        });

      return (
        <SafetyExternalPartyInjuryForm
          enabled={Boolean(value)}
          onChange={setValue}
          value={value}
          vesselId="vessel-1"
        />
      );
    }

    render(<ControlledInjuryForm />);

    await userEvent.click(screen.getByRole('radio', { name: 'Crew' }));

    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'Anchoring' })).toBeTruthy();
    });

    await userEvent.selectOptions(
      screen.getByRole('combobox', { name: 'Type of Activity' }),
      'Others(Specify)'
    );
    const otherInput = screen.getByRole('textbox', { name: 'Specify other' });
    await userEvent.clear(otherInput);
    await userEvent.type(otherInput, 'Watchkeeping');

    expect(
      (
        screen.getByRole('textbox', {
          name: 'Specify other',
        }) as HTMLInputElement
      ).value
    ).toBe('Watchkeeping');
  });
});
