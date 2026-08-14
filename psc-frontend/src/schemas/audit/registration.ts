import { z } from 'zod';

export const AUDIT_STANDARDS = ['ISM', 'ISPS', 'MLC', 'EMS'] as const;
export const EXTERNAL_AUDIT_STANDARDS = ['ISM', 'ISPS', 'MLC', 'EMS', 'DOC'] as const;
export const EXTERNAL_AUDIT_SUBTYPES = [
  'DOC_INITIAL',
  'DOC_INTERIM',
  'DOC_ANNUAL',
  'DOC_RENEWAL',
  'SMC_INITIAL',
  'SMC_INTERIM',
  'SMC_INTERMEDIATE',
  'SMC_RENEWAL',
  'MLC_INITIAL',
  'MLC_INTERIM',
  'MLC_INTERMEDIATE',
  'MLC_RENEWAL',
  'ISPS_INITIAL',
  'ISPS_INTERIM',
  'ISPS_INTERMEDIATE',
  'ISPS_RENEWAL',
  'ADDITIONAL',
] as const;
export const EXTERNAL_AUDIT_ORG_TYPES = ['CLASS_SOCIETY', 'FLAG_STATE', 'RO', 'OTHER'] as const;
export const AUDITEE_TYPES = ['VESSEL', 'OFFICE_DEPT'] as const;
export const OFFICE_DEPARTMENTS = ['CREW', 'TECH', 'PURCHASE', 'IT', 'MARINE', 'SEQ', 'OTHER'] as const;
export const AUDIT_TEAM_ROLES = ['CO_AUDITOR', 'OBSERVER', 'TRAINEE', 'OTHER'] as const;

const optionalText = (max: number) => z.string().max(max).optional().default('');

export const auditRegistrationSchema = z
  .object({
    vessel_id: z.string().uuid('Vessel is required'),
    inspection_date: z.string().min(1, 'Inspection date is required'),
    port_place: z.string().min(2, 'Port/Place is required').max(200),
    country: optionalText(100),
    authority: optionalText(200),
    inspector_name: optionalText(200),
    report_reference: optionalText(100),
    audit_classification: z.literal('INTERNAL'),
    auditee_type: z.enum(AUDITEE_TYPES),
    auditee_office_dept: z.enum(OFFICE_DEPARTMENTS).or(z.literal('')).optional().default(''),
    audit_subtype: z.literal('ANNUAL_INTERNAL'),
    lead_auditor_name: z.string().min(1, 'Lead auditor name is required').max(200),
    lead_auditor_designation: optionalText(200),
    lead_auditor_company: z.string().min(1, 'Lead auditor company is required').max(200),
    lead_auditor_qual: optionalText(200),
    lead_auditor_user_id: optionalText(100),
    trigger_reason: z.enum(['SCHEDULED', 'ADDITIONAL', 'FOLLOW_UP', 'OTHER']).default('SCHEDULED'),
    audit_plan_id: z.string().uuid().or(z.literal('')).optional().default(''),
    parent_audit_id: optionalText(32),
    audit_start_date: z.string().min(1, 'Audit start date is required'),
    audit_end_date: z.string().optional().default(''),
    opening_meeting_at: z.string().optional().default(''),
    closing_meeting_at: z.string().optional().default(''),
    audit_scope: optionalText(2000),
    terms_of_reference: optionalText(2000),
    prev_internal_ca_verified: z.enum(['YES', 'NO', 'NA']).or(z.literal('')).optional().default(''),
    prev_external_ca_verified: z.enum(['YES', 'NO', 'NA']).or(z.literal('')).optional().default(''),
    standards: z.array(z.enum(AUDIT_STANDARDS)).min(1, 'Select at least one standard'),
    team_members: z.array(
      z.object({
        member_name: z.string().min(1, 'Team member name is required').max(200),
        member_designation: optionalText(200),
        member_company: optionalText(200),
        member_role: z.enum(AUDIT_TEAM_ROLES).or(z.literal('')).optional().default(''),
      })
    ),
    attendees: z.array(
      z.object({
        attendee_name: z.string().min(1, 'Attendee name is required').max(200),
        attendee_rank: optionalText(100),
        opening_present: z.boolean().default(false),
        closing_present: z.boolean().default(false),
      })
    ),
    schedule_blocks: z.array(
      z.object({
        block_date: z.string().optional().default(''),
        time_from: z.string().optional().default(''),
        time_to: z.string().optional().default(''),
        activity: optionalText(300),
      })
    ),
  })
  .refine((data) => data.auditee_type !== 'OFFICE_DEPT' || Boolean(data.auditee_office_dept), {
    message: 'Office department is required for office audits',
    path: ['auditee_office_dept'],
  })
  .refine((data) => !data.audit_end_date || data.audit_end_date >= data.audit_start_date, {
    message: 'Audit end date cannot be before start date',
    path: ['audit_end_date'],
  });

export type AuditRegistrationFormData = z.infer<typeof auditRegistrationSchema>;

export const externalAuditRegistrationSchema = z
  .object({
    vessel_id: z.string().uuid('Vessel is required'),
    inspection_date: z.string().min(1, 'Completion date is required'),
    port_place: z.string().min(2, 'Port/Place is required').max(200),
    country: optionalText(100),
    authority: optionalText(200),
    inspector_name: optionalText(200),
    report_reference: z.string().min(1, 'Report reference is required').max(100),
    audit_classification: z.literal('EXTERNAL'),
    auditee_type: z.enum(AUDITEE_TYPES),
    auditee_office_dept: z.enum(OFFICE_DEPARTMENTS).or(z.literal('')).optional().default(''),
    audit_start_date: z.string().min(1, 'Audit start date is required'),
    audit_end_date: z.string().optional().default(''),
    standards: z.array(z.enum(EXTERNAL_AUDIT_STANDARDS)).min(1, 'Select at least one standard'),
    external_audit_subtypes: z.array(z.enum(EXTERNAL_AUDIT_SUBTYPES)).min(1, 'Select at least one subtype'),
    external_audit_org_id: z.string().uuid('External audit organisation is required'),
    external_audit_org_type: z.enum(EXTERNAL_AUDIT_ORG_TYPES),
    external_lead_auditor_name: z.string().min(1, 'External lead auditor is required').max(200),
    external_lead_auditor_credential: z.string().min(1, 'External auditor credential is required').max(200),
    flag_state_code: optionalText(10),
    cycle_year: z.number().int().positive().nullable().optional(),
    linked_cert_ids: z.array(z.string().uuid()).optional().default([]),
    external_report_file_name: z.string().min(1, 'External report PDF name is required').max(255),
    external_report_file_path: z.string().min(1, 'External report PDF path is required').max(500),
    external_report_mime_type: z.string().min(1, 'External report MIME type is required').max(100),
    external_report_file_size: z.number().int().positive().nullable().optional(),
    late_registration_reason: z.string().optional().default(''),
  })
  .refine((data) => !data.audit_end_date || data.audit_end_date >= data.audit_start_date, {
    message: 'Audit end date cannot be before start date',
    path: ['audit_end_date'],
  })
  .refine(
    (data) =>
      !data.external_audit_subtypes.some((subtype) => subtype.startsWith('DOC_')) ||
      (Boolean(data.flag_state_code) && Boolean(data.cycle_year)),
    {
      message: 'Flag state and DOC cycle year are required for DOC audits',
      path: ['flag_state_code'],
    }
  );

export type ExternalAuditRegistrationFormData = z.infer<typeof externalAuditRegistrationSchema>;
export type AuditRegistrationPayload = AuditRegistrationFormData | ExternalAuditRegistrationFormData;

export const auditRegistrationDefaults: AuditRegistrationFormData = {
  vessel_id: '',
  inspection_date: new Date().toISOString().slice(0, 10),
  port_place: '',
  country: '',
  authority: '',
  inspector_name: '',
  report_reference: '',
  audit_classification: 'INTERNAL',
  auditee_type: 'VESSEL',
  auditee_office_dept: '',
  audit_subtype: 'ANNUAL_INTERNAL',
  lead_auditor_name: '',
  lead_auditor_designation: '',
  lead_auditor_company: 'KSM',
  lead_auditor_qual: '',
  lead_auditor_user_id: '',
  trigger_reason: 'SCHEDULED',
  audit_plan_id: '',
  parent_audit_id: '',
  audit_start_date: new Date().toISOString().slice(0, 10),
  audit_end_date: '',
  opening_meeting_at: '',
  closing_meeting_at: '',
  audit_scope: '',
  terms_of_reference: '',
  prev_internal_ca_verified: '',
  prev_external_ca_verified: '',
  standards: ['ISM', 'ISPS', 'MLC', 'EMS'],
  team_members: [],
  attendees: [],
  schedule_blocks: [],
};
