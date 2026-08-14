import { z } from 'zod';

export const FINDING_TYPES = ['NC', 'OBSERVATION'] as const;
export const NC_CATEGORIES = ['MAJOR_NC', 'MINOR_NC'] as const;
export const OBSERVATION_CATEGORIES = ['OBSERVATION', 'IMPROVEMENT_SUGGESTION', 'OFI'] as const;
export const RULE_BOOK_TYPES = ['ISM', 'ISPS', 'MLC', 'SOLAS', 'STCW', 'MARPOL', 'COLREG', 'KSM_SMS', 'FLAG', 'OTHER'] as const;
export const FINDING_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const;
export const CERTIFICATE_IMPACTS = ['NONE', 'CERT_VALID', 'RENEWAL_AT_RISK', 'SUSPENDED', 'WITHDRAWN'] as const;

export interface AuditClauseMasterRow {
  id: string;
  code: string;
  title: string;
  code_version: string;
}

export interface AuditClauseMaster {
  rule_book_type: string;
  clauses: AuditClauseMasterRow[];
}

export const auditFindingClauseSchema = z.object({
  rule_book_type: z.enum(RULE_BOOK_TYPES),
  rule_clause_id: z.string().uuid().or(z.literal('')).optional().default(''),
  clause_ref_text: z.string().max(200).optional().default(''),
  clause_subref_text: z.string().max(200).optional().default(''),
  is_primary: z.boolean().default(false),
});

export const auditFindingCreateSchema = z
  .object({
    finding_type: z.enum(FINDING_TYPES),
    nc_category: z.enum(NC_CATEGORIES).or(z.literal('')).optional().default(''),
    observation_category: z.enum(OBSERVATION_CATEGORIES).or(z.literal('')).optional().default('OBSERVATION'),
    standard_code: z.string().max(20).optional().default('ISM'),
    description: z.string().min(1, 'Description is required'),
    objective_evidence: z.string().optional().default(''),
    def_code_id: z.string().min(1, 'DefCode is required').max(5),
    checklist_item_id: z.string().uuid().or(z.literal('')).optional().default(''),
    priority: z.enum(FINDING_PRIORITIES).optional().default('MEDIUM'),
    certificate_impact: z.enum(CERTIFICATE_IMPACTS).or(z.literal('')).optional().default(''),
    certificates_at_risk: z.string().max(100).optional().default(''),
    is_fleetwide_relevance: z.boolean().optional().default(false),
    clauses: z.array(auditFindingClauseSchema).min(1, 'At least one clause reference is required'),
  })
  .refine((data) => (data.finding_type === 'NC' ? Boolean(data.nc_category) : true), {
    message: 'NC category is required',
    path: ['nc_category'],
  })
  .refine((data) => (data.finding_type === 'OBSERVATION' ? Boolean(data.observation_category) : true), {
    message: 'Observation category is required',
    path: ['observation_category'],
  })
  .refine((data) => (data.finding_type === 'NC' ? true : !data.is_fleetwide_relevance), {
    message: 'Fleet-wide relevance is available only for NC findings',
    path: ['is_fleetwide_relevance'],
  })
  .refine((data) => data.clauses.filter((clause) => clause.is_primary).length === 1, {
    message: 'Exactly one clause reference must be primary',
    path: ['clauses'],
  })
  .refine(
    (data) =>
      data.clauses.every((clause) => {
        if (clause.rule_book_type === 'OTHER' || clause.rule_book_type === 'FLAG') {
          const length = clause.clause_ref_text.trim().length;
          return length >= 5 && length <= 200 && !clause.rule_clause_id;
        }
        return Boolean(clause.rule_clause_id);
      }),
    {
      message: 'Select a seeded clause, or enter 5-200 characters for OTHER/FLAG.',
      path: ['clauses'],
    }
  );

export type AuditFindingCreateFormData = z.infer<typeof auditFindingCreateSchema>;

export interface AuditFindingCreateResponse {
  id: string;
  audit_detail_id: string;
  finding_type: 'NC' | 'OBSERVATION' | string;
  nc_category: string | null;
  observation_category: string | null;
  standard_code: string | null;
  rule_book_type: string | null;
  rule_clause_id: string | null;
  clause_ref_text: string | null;
  description: string;
  objective_evidence: string | null;
  priority: string;
  certificates_at_risk: string | null;
  is_fleetwide_relevance: boolean;
  linked_circular_id: string | null;
  psc_deficiency_id: string;
  car_id: string;
  car_number: string;
  car_status: string;
  created: boolean;
}

export interface AuditIssueCircularResponse {
  status: string;
  circular_id: string;
  detail_url: string;
  payload: Record<string, unknown>;
}

export function findingDefaults(checklistItemId?: string): AuditFindingCreateFormData {
  return {
    finding_type: 'NC',
    nc_category: 'MINOR_NC',
    observation_category: 'OBSERVATION',
    standard_code: 'ISM',
    description: '',
    objective_evidence: '',
    def_code_id: '10101',
    checklist_item_id: checklistItemId || '',
    priority: 'MEDIUM',
    certificate_impact: '',
    certificates_at_risk: '',
    is_fleetwide_relevance: false,
    clauses: [
      {
        rule_book_type: 'ISM',
        rule_clause_id: '',
        clause_ref_text: '',
        clause_subref_text: '',
        is_primary: true,
      },
    ],
  };
}
