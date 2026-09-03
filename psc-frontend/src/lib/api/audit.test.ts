import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiClientMock = vi.hoisted(() => ({
  post: vi.fn(),
}));

vi.mock('@/lib/api/client', () => ({
  apiClient: apiClientMock,
}));

vi.mock('@/lib/utils/constants', () => ({
  API_BASE_URL: 'http://localhost:8000',
}));

import { createAuditRegistration } from './audit';

describe('audit registration API', () => {
  beforeEach(() => {
    apiClientMock.post.mockReset();
  });

  it('posts external audit registration with an attached PDF as multipart data', async () => {
    apiClientMock.post.mockResolvedValue({
      data: {
        data: {
          id: 'audit-1',
          inspection_id: 'inspection-1',
          status: 'SUBMITTED',
          audit_classification: 'EXTERNAL',
          auditee_type: 'VESSEL',
        },
      },
    });
    const reportPdf = new File(['%PDF-1.4 external audit report'], 'DNV-audit-report-2026.pdf', {
      type: 'application/pdf',
    });

    await createAuditRegistration({
      vessel_id: '33333333-3333-4333-8333-333333333333',
      inspection_date: '2026-08-01',
      port_place: 'Singapore',
      country: '',
      authority: '',
      inspector_name: '',
      report_reference: 'DNV-SMC-2026-001',
      audit_classification: 'EXTERNAL',
      auditee_type: 'VESSEL',
      auditee_office_dept: '',
      audit_start_date: '2026-08-01',
      audit_end_date: '2026-08-01',
      standards: ['ISM', 'MLC'],
      external_audit_subtypes: ['SMC_RENEWAL'],
      external_audit_org_id: '44444444-4444-4444-8444-444444444444',
      external_audit_org_type: 'CLASS_SOCIETY',
      external_lead_auditor_name: 'L. Bergstrom',
      external_lead_auditor_credential: 'IMO ISM/ISPS/MLC Auditor',
      flag_state_code: '',
      cycle_year: null,
      external_report_file_name: reportPdf.name,
      external_report_file_path: reportPdf.name,
      external_report_mime_type: 'application/pdf',
      external_report_file_size: reportPdf.size,
      external_report_file: reportPdf,
      late_registration_reason: '',
    });

    expect(apiClientMock.post).toHaveBeenCalledWith(
      'http://localhost:8000/api/audit/audits/',
      expect.any(FormData),
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );

    const formData = apiClientMock.post.mock.calls[0]?.[1] as FormData;
    expect(formData.get('external_report_file')).toBe(reportPdf);
    expect(formData.get('external_report_file_name')).toBe('DNV-audit-report-2026.pdf');
    expect(formData.get('external_report_file_path')).toBe('DNV-audit-report-2026.pdf');
    expect(formData.get('external_report_file_size')).toBe(String(reportPdf.size));
    expect(formData.getAll('standards')).toEqual(['ISM', 'MLC']);
    expect(formData.getAll('external_audit_subtypes')).toEqual(['SMC_RENEWAL']);
    expect(formData.getAll('linked_cert_ids')).toEqual([]);
  });

  it('omits a blank external audit organisation id from multipart data', async () => {
    apiClientMock.post.mockResolvedValue({
      data: {
        data: {
          id: 'audit-1',
          inspection_id: 'inspection-1',
          status: 'SUBMITTED',
          audit_classification: 'EXTERNAL',
          auditee_type: 'VESSEL',
        },
      },
    });
    const reportPdf = new File(['%PDF-1.4 external audit report'], 'DNV-audit-report-2026.pdf', {
      type: 'application/pdf',
    });

    await createAuditRegistration({
      vessel_id: '33333333-3333-4333-8333-333333333333',
      inspection_date: '2026-08-01',
      port_place: 'Singapore',
      country: '',
      authority: '',
      inspector_name: '',
      report_reference: '',
      audit_classification: 'EXTERNAL',
      auditee_type: 'VESSEL',
      auditee_office_dept: '',
      audit_start_date: '2026-08-01',
      audit_end_date: '2026-08-01',
      standards: ['ISM'],
      external_audit_subtypes: ['SMC_RENEWAL'],
      external_audit_org_id: '',
      external_audit_org_type: 'CLASS_SOCIETY',
      external_lead_auditor_name: 'L. Bergstrom',
      external_lead_auditor_credential: 'IMO ISM/ISPS/MLC Auditor',
      flag_state_code: '',
      cycle_year: null,
      external_report_file_name: reportPdf.name,
      external_report_file_path: reportPdf.name,
      external_report_mime_type: 'application/pdf',
      external_report_file_size: reportPdf.size,
      external_report_file: reportPdf,
      late_registration_reason: '',
    });

    const formData = apiClientMock.post.mock.calls[0]?.[1] as FormData;
    expect(formData.has('external_audit_org_id')).toBe(false);
    expect(formData.get('external_audit_org_type')).toBe('CLASS_SOCIETY');
  });
});
