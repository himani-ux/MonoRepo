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
      'PLAN-AAAAAAAA | SFC - SF CHALISA | ISM,ISPS | 2026-08-22 -> 2026-08-31 | CONFIRMED'
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
