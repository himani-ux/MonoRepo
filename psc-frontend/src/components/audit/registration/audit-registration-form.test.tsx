import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import {
  AuditRegistrationForm,
  formatAuditPlanOption,
  parsePlanStandards,
  shortAuditPlanRef,
  type AuditRegistrationPlanOption,
} from './audit-registration-form';

describe('AuditRegistrationForm plan selection', () => {
  it('labels same-vessel audit plans with a short plan reference and window', () => {
    expect(formatAuditPlanOption(planOption())).toBe(
      'PLAN-AAAAAAAA | SFC - SF CHALISA | ISM,ISPS | 2026-08-22 -> 2026-08-31 | Confirmed'
    );
    expect(shortAuditPlanRef('bbbbbbbb-2222-4222-8222-222222222222')).toBe('PLAN-BBBBBBBB');
    expect(parsePlanStandards('ISM, ISPS,UNKNOWN, MLC')).toEqual(['ISM', 'ISPS', 'MLC']);
  });

  it('blocks registration when registerable plans exist and no plan is selected', async () => {
    const onSubmit = vi.fn();

    const { container } = render(
      <AuditRegistrationForm
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        vesselOptions={[
          {
            id: '11111111-1111-4111-8111-111111111111',
            vessel_code: 'SFC',
            vessel_name: 'SF CHALISA',
          },
        ]}
        auditPlanOptions={[planOption()]}
        defaultVesselId="11111111-1111-4111-8111-111111111111"
        defaultLeadAuditorName="Capt. Harman Sandhu"
      />
    );

    fireEvent.change(screen.getByLabelText(/Port\/Place/i), { target: { value: 'Singapore' } });
    fireEvent.click(screen.getByRole('button', { name: 'Register Audit' }));

    expect(await screen.findByText('Select the exact audit plan before registering.')).toBeInTheDocument();
    await waitFor(() => {
      expect(onSubmit).not.toHaveBeenCalled();
    });
  });

  it('uses the selected plan lead auditor as read-only registration data', async () => {
    const onSubmit = vi.fn();

    const { container } = render(
      <AuditRegistrationForm
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        vesselOptions={[
          {
            id: '11111111-1111-4111-8111-111111111111',
            vessel_code: 'SFC',
            vessel_name: 'SF CHALISA',
          },
        ]}
        auditPlanOptions={[planOption()]}
        defaultVesselId="11111111-1111-4111-8111-111111111111"
        defaultLeadAuditorName="Logged In User"
      />
    );

    const auditPlanSelect = container.querySelector('select') as HTMLSelectElement;
    fireEvent.change(auditPlanSelect, { target: { value: 'aaaaaaaa-1111-4111-8111-111111111111' } });

    expect(container.querySelector('#lead_auditor_name')).toHaveValue('Capt. Harman Sandhu');
    expect(container.querySelector('#lead_auditor_name')).toHaveAttribute('readonly');
    expect(container.querySelector('#lead_auditor_designation')).toHaveValue('SEQ Manager');
    expect(container.querySelector('#lead_auditor_company')).toHaveValue('KSM');
    expect(container.querySelector('#lead_auditor_qual')).toHaveValue('ISM Lead Auditor');

    fireEvent.change(screen.getByLabelText(/Port\/Place/i), { target: { value: 'Singapore' } });
    fireEvent.click(screen.getByRole('button', { name: 'Register Audit' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
        audit_plan_id: 'aaaaaaaa-1111-4111-8111-111111111111',
        lead_auditor_user_id: 'auditor-1',
        lead_auditor_name: 'Capt. Harman Sandhu',
        lead_auditor_designation: 'SEQ Manager',
        lead_auditor_company: 'KSM',
        lead_auditor_qual: 'ISM Lead Auditor',
      }));
    });
  });

  it('syncs the visible vessel and payload to the selected plan target vessel', async () => {
    const onSubmit = vi.fn();
    const eatVesselId = '22222222-2222-4222-8222-222222222222';

    const { container } = render(
      <AuditRegistrationForm
        onSubmit={onSubmit}
        onCancel={vi.fn()}
        vesselOptions={[
          {
            id: '11111111-1111-4111-8111-111111111111',
            vessel_code: 'ARY',
            vessel_name: 'SFYC ARAYA',
          },
        ]}
        auditPlanOptions={[
          planOption({
            target_vessel_id: eatVesselId,
            target_label: 'EAT - EAST AYUTTHAYA',
            window_label: '2026-08-01 -> 2026-08-31',
            planned_window_start: '2026-08-01',
            planned_window_end: '2026-08-31',
          }),
        ]}
        defaultVesselId="11111111-1111-4111-8111-111111111111"
        defaultLeadAuditorName="Logged In User"
      />
    );

    const auditPlanSelect = container.querySelector('select') as HTMLSelectElement;
    fireEvent.change(auditPlanSelect, { target: { value: 'aaaaaaaa-1111-4111-8111-111111111111' } });

    const vesselSelect = container.querySelector('#vessel_id') as HTMLSelectElement;
    await waitFor(() => {
      expect(vesselSelect).toHaveValue('EAT - EAST AYUTTHAYA');
      expect(vesselSelect).toHaveAttribute('readonly');
    });

    fireEvent.change(screen.getByLabelText(/Port\/Place/i), { target: { value: 'Mumbai' } });
    fireEvent.click(screen.getByRole('button', { name: 'Register Audit' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
        audit_plan_id: 'aaaaaaaa-1111-4111-8111-111111111111',
        vessel_id: eatVesselId,
      }));
    });
  });

  it('uses selected vessel top-rank personnel to fill attendee rank', async () => {
    const { container } = render(
      <AuditRegistrationForm
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        vesselOptions={[
          {
            id: '11111111-1111-4111-8111-111111111111',
            vessel_code: 'SFC',
            vessel_name: 'SF CHALISA',
            top_rank_personnel: [
              {
                crew_id: 'MASTER-1',
                crew_name: 'Capt. Arun Rao',
                rank_code: 'MASTER',
                rank_name: 'Master',
              },
              {
                crew_id: 'CO-1',
                crew_name: 'Priya Menon',
                rank_code: 'CO',
                rank_name: 'Chief Officer',
              },
            ],
          },
        ]}
        auditPlanOptions={[]}
        defaultVesselId="11111111-1111-4111-8111-111111111111"
        defaultLeadAuditorName="Capt. Harman Sandhu"
      />
    );

    fireEvent.click(screen.getAllByRole('button', { name: 'Add' })[1]);
    const attendeeSelect = Array.from(container.querySelectorAll('select')).find((select) =>
      Array.from(select.options).some((option) => option.value === 'CO-1')
    ) as HTMLSelectElement;
    fireEvent.change(attendeeSelect, { target: { value: 'CO-1' } });

    expect(screen.getByLabelText('Attendee rank')).toHaveValue('Chief Officer');
  });
});

function planOption(overrides: Partial<AuditRegistrationPlanOption> = {}): AuditRegistrationPlanOption {
  return {
    id: 'aaaaaaaa-1111-4111-8111-111111111111',
    target_vessel_id: '11111111-1111-4111-8111-111111111111',
    target_office_dept: null,
    target_label: 'SFC - SF CHALISA',
    audit_standards_csv: 'ISM,ISPS',
    lead_auditor_user_id: 'auditor-1',
    lead_auditor_name: 'Capt. Harman Sandhu',
    lead_auditor_designation: 'SEQ Manager',
    lead_auditor_company: 'KSM',
    lead_auditor_qual: 'ISM Lead Auditor',
    planned_window_start: '2026-08-22',
    planned_window_end: '2026-08-31',
    window_label: '2026-08-22 -> 2026-08-31',
    extended_due_date: null,
    extension_form_ref: null,
    is_additional: false,
    additional_reason: null,
    trigger_event_type: null,
    trigger_event_ref: null,
    status: 'CONFIRMED',
    ...overrides,
  };
}
