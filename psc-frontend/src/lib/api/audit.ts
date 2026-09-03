import { apiClient } from './client';
import { API_BASE_URL } from '@/lib/utils/constants';
import type { AuditChecklist } from '@/schemas/audit/checklist';
import type { AuditDetail, AuditDetailEditableFields, AuditScorecardRow } from '@/schemas/audit/detail';
import type {
  AuditClauseMaster,
  AuditFindingCreatePayload,
  AuditFindingCreateResponse,
  AuditIssueCircularResponse,
} from '@/schemas/audit/finding';
import type {
  AuditNcClosure,
  AuditNcDraftPayload,
  AuditNcPartName,
  AuditNcPartPayload,
  AuditNcWorkflowAction,
  AuditNcWorkflowResponse,
  AuditRcaTemplateMaster,
} from '@/schemas/audit/nc-closure';
import type {
  AuditFailedNotificationList,
  AuditNotificationDelivery,
  AuditNotificationOfflineData,
} from '@/schemas/audit/notification';
import type { AuditObsClosure, AuditObsPartName, AuditObsPartPayload } from '@/schemas/audit/obs-closure';
import type {
  AuditPlan,
  AuditPlanAdditionalData,
  AuditPlanCancelData,
  AuditPlanExtensionDecisionData,
  AuditPlanExtensionRequestData,
  AuditPlanFlagNotificationData,
  AuditPlanFormData,
  AuditPlanList,
} from '@/schemas/audit/plan';
import type { AuditRegistrationPayload } from '@/schemas/audit/registration';
import type {
  AuditScanValidationActionData,
  AuditScanValidationAttachment,
  AuditScanValidationQueue,
} from '@/schemas/audit/scan-validation';

interface AuditApiResponse<T> {
  data: T;
  message?: string;
}

export interface AuditRegistrationResponse {
  id: string;
  inspection_id: string;
  status: string;
  audit_classification: string;
  auditee_type: string;
}

export interface RegisteredAudit {
  id: string;
  audit_plan_id: string | null;
  target_label: string;
  vessel_id: string | null;
  audit_classification: string;
  auditee_type: string;
  auditee_office_dept: string | null;
  audit_subtype: string;
  lead_auditor_name: string;
  lead_auditor_designation: string;
  audit_start_date: string;
  audit_end_date: string | null;
  status: string;
  created_date: string | null;
}

export interface RegisteredAuditList {
  count: number;
  results: RegisteredAudit[];
}

export interface AuditVesselOption {
  id: string;
  vessel_code: string;
  vessel_name: string;
  top_rank_personnel?: AuditVesselPersonnelOption[];
}

export interface AuditVesselPersonnelOption {
  crew_id?: string | null;
  crew_name: string;
  rank_code: string;
  rank_name: string;
}

export interface AuditQualifiedAuditor {
  id: string;
  user_id: string;
  display_name: string;
  designation: string;
  company: string;
  identity_source: string;
  qualification_text: string;
  qualification_date: string;
  expiry_date: string;
  scope_standards_csv: string;
  qualifying_body: string | null;
  certificate_attachment_id?: string | null;
  auditor_scope: string;
  qualified_for_seq: boolean;
  is_active: boolean;
}

export interface AuditQualifiedAuditorPayload {
  user_id: string;
  qualification_text: string;
  qualification_date: string;
  expiry_date: string;
  scope_standards_csv: string;
  qualifying_body?: string | null;
  certificate_attachment_id?: string | null;
  auditor_scope: string;
  qualified_for_seq: boolean;
  is_active: boolean;
}

export interface AuditQualifyingBody {
  id: string;
  body_name: string;
  is_active: boolean;
  is_deleted: boolean;
}

export interface AuditQualifyingBodyPayload {
  body_name: string;
  is_active: boolean;
  is_deleted?: boolean;
}

export interface AuditOfficeUserOption {
  employee_id: string;
  display_name: string | null;
  employee_name: string | null;
  username: string | null;
  employee_role: string | null;
  department: string | null;
  role_name: string | null;
}

export interface AuditMasterList<T> {
  count: number;
  results: T[];
}

export interface AuditHodAssignment {
  id: string;
  dept: string;
  user_id: string;
  display_name: string;
  designation: string;
  company: string;
  is_acting: boolean;
  effective_from: string;
  effective_to: string | null;
}

export interface AuditHodAssignmentPayload {
  dept: string;
  user_id: string;
  effective_from: string;
  effective_to: string;
}

export interface AuditExternalAuditOrg {
  id: string;
  name: string;
  org_type: 'CLASS_SOCIETY' | 'FLAG_STATE' | 'RO' | 'OTHER' | string;
  country: string | null;
  linked_class_society_ref: string | null;
  is_active: boolean;
}

export interface ExternalAuditCloseoutPayload {
  certificate_impact: 'NONE' | 'CERT_VALID' | 'RENEWAL_AT_RISK' | 'SUSPENDED' | 'WITHDRAWN';
  is_cycle_resetting?: boolean;
  cycle_reset_reason?: string;
  typed_cert_number?: string;
  flag_notified_to?: string;
  flag_notification_ref?: string;
}

export interface ExternalCertLinkPayload {
  linked_cert_ids: string[];
  reason: string;
}

function cleanAuditRegistrationPayload(data: AuditRegistrationPayload) {
  const { external_report_file: _externalReportFile, ...registrationData } = data as AuditRegistrationPayload & {
    external_report_file?: File;
  };

  return {
    ...registrationData,
    audit_plan_id: 'audit_plan_id' in data ? data.audit_plan_id || null : null,
    audit_end_date: data.audit_end_date || null,
    opening_meeting_at: 'opening_meeting_at' in data ? data.opening_meeting_at || null : null,
    closing_meeting_at: 'closing_meeting_at' in data ? data.closing_meeting_at || null : null,
    prev_internal_ca_verified: 'prev_internal_ca_verified' in data ? data.prev_internal_ca_verified || '' : '',
    prev_external_ca_verified: 'prev_external_ca_verified' in data ? data.prev_external_ca_verified || '' : '',
    team_members:
      'team_members' in data
        ? data.team_members.map((member) => ({
            ...member,
            member_role: member.member_role || '',
          }))
        : [],
    attendees: 'attendees' in data ? data.attendees : [],
    schedule_blocks:
      'schedule_blocks' in data
        ? data.schedule_blocks.map((block) => ({
            ...block,
            block_date: block.block_date || null,
            time_from: block.time_from || null,
            time_to: block.time_to || null,
          }))
        : [],
    ...(data.audit_classification === 'EXTERNAL'
      ? {
          external_audit_org_id: data.external_audit_org_id || null,
          cycle_year: data.cycle_year || null,
          external_report_file_size: data.external_report_file_size || null,
        }
      : {}),
  };
}

function getExternalReportFile(data: AuditRegistrationPayload): File | undefined {
  if (data.audit_classification !== 'EXTERNAL' || !('external_report_file' in data)) {
    return undefined;
  }
  return data.external_report_file;
}

function buildAuditRegistrationFormData(data: AuditRegistrationPayload, externalReportFile: File): FormData {
  const formData = new FormData();
  const payload = cleanAuditRegistrationPayload(data);

  Object.entries(payload).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null) {
          formData.append(key, typeof item === 'object' ? JSON.stringify(item) : String(item));
        }
      });
      return;
    }

    formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
  });

  formData.append('external_report_file', externalReportFile);
  return formData;
}

function cleanAuditPlanPayload(data: AuditPlanFormData) {
  return {
    ...data,
    target_vessel_id: data.target_vessel_id || null,
    target_office_dept: data.target_office_dept || '',
    planned_window_start: data.planned_window_start || null,
    planned_window_end: data.planned_window_end || null,
  };
}

function cleanAuditPlanAdditionalPayload(data: AuditPlanAdditionalData) {
  return {
    ...cleanAuditPlanPayload(data),
    additional_reason: data.additional_reason,
    trigger_event_type: data.trigger_event_type,
    trigger_event_ref: data.trigger_event_ref,
  };
}

export async function createAuditRegistration(
  data: AuditRegistrationPayload
): Promise<AuditRegistrationResponse> {
  const externalReportFile = getExternalReportFile(data);
  if (externalReportFile) {
    const response = await apiClient.post<AuditApiResponse<AuditRegistrationResponse>>(
      `${API_BASE_URL}/api/audit/audits/`,
      buildAuditRegistrationFormData(data, externalReportFile),
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data.data;
  }

  const response = await apiClient.post<AuditApiResponse<AuditRegistrationResponse>>(
    `${API_BASE_URL}/api/audit/audits/`,
    cleanAuditRegistrationPayload(data)
  );
  return response.data.data;
}

export async function getRegisteredAudits(): Promise<RegisteredAuditList> {
  const response = await apiClient.get<AuditApiResponse<RegisteredAuditList>>(
    `${API_BASE_URL}/api/audit/audits/`
  );
  return response.data.data;
}

export async function getAuditPlans(isAdditional?: boolean): Promise<AuditPlanList> {
  const response = await apiClient.get<AuditApiResponse<AuditPlanList>>(
    `${API_BASE_URL}/api/audit/plans/`,
    { params: isAdditional === undefined ? undefined : { is_additional: isAdditional } }
  );
  return response.data.data;
}

export async function getAuditVessels(): Promise<AuditVesselOption[]> {
  const response = await apiClient.get<AuditApiResponse<AuditVesselOption[]>>(
    `${API_BASE_URL}/api/audit/vessels/`
  );
  return response.data.data;
}

export async function getAuditQualifiedAuditors(params?: {
  standards?: string;
  target_office_dept?: string;
  eligible?: boolean;
  include_inactive?: boolean;
}): Promise<AuditMasterList<AuditQualifiedAuditor>> {
  const response = await apiClient.get<AuditApiResponse<AuditMasterList<AuditQualifiedAuditor>>>(
    `${API_BASE_URL}/api/audit/masters/qualified-auditors/`,
    {
      params: {
        ...params,
        eligible: params?.eligible ? 'true' : undefined,
        include_inactive: params?.include_inactive ? 'true' : undefined,
      },
    }
  );
  return response.data.data;
}

export async function getAuditOfficeUsers(): Promise<AuditMasterList<AuditOfficeUserOption>> {
  const response = await apiClient.get<AuditApiResponse<AuditMasterList<AuditOfficeUserOption>>>(
    `${API_BASE_URL}/api/audit/masters/office-users/`
  );
  return response.data.data;
}

export async function getAuditQualifyingBodies(
  includeInactive = false
): Promise<AuditMasterList<AuditQualifyingBody>> {
  const response = await apiClient.get<AuditApiResponse<AuditMasterList<AuditQualifyingBody>>>(
    `${API_BASE_URL}/api/audit/masters/qualifying-bodies/`,
    { params: includeInactive ? { include_inactive: 'true' } : undefined }
  );
  return response.data.data;
}

export async function createAuditQualifyingBody(
  data: AuditQualifyingBodyPayload
): Promise<AuditQualifyingBody> {
  const response = await apiClient.post<AuditApiResponse<AuditQualifyingBody>>(
    `${API_BASE_URL}/api/audit/masters/qualifying-bodies/`,
    data
  );
  return response.data.data;
}

export async function updateAuditQualifyingBody(
  id: string,
  data: Partial<AuditQualifyingBodyPayload>
): Promise<AuditQualifyingBody> {
  const response = await apiClient.patch<AuditApiResponse<AuditQualifyingBody>>(
    `${API_BASE_URL}/api/audit/masters/qualifying-bodies/${id}/`,
    data
  );
  return response.data.data;
}

export async function createAuditQualifiedAuditor(
  data: AuditQualifiedAuditorPayload
): Promise<AuditQualifiedAuditor> {
  const response = await apiClient.post<AuditApiResponse<AuditQualifiedAuditor>>(
    `${API_BASE_URL}/api/audit/masters/qualified-auditors/`,
    data
  );
  return response.data.data;
}

export async function updateAuditQualifiedAuditor(
  id: string,
  data: Partial<AuditQualifiedAuditorPayload>
): Promise<AuditQualifiedAuditor> {
  const response = await apiClient.patch<AuditApiResponse<AuditQualifiedAuditor>>(
    `${API_BASE_URL}/api/audit/masters/qualified-auditors/${id}/`,
    data
  );
  return response.data.data;
}

export async function getAuditHodCoverage(): Promise<AuditMasterList<AuditHodAssignment>> {
  const response = await apiClient.get<AuditApiResponse<AuditMasterList<AuditHodAssignment>>>(
    `${API_BASE_URL}/api/audit/admin/hod-coverage/`
  );
  return response.data.data;
}

export async function getAuditExternalAuditOrgs(): Promise<AuditMasterList<AuditExternalAuditOrg>> {
  const response = await apiClient.get<AuditApiResponse<AuditMasterList<AuditExternalAuditOrg>>>(
    `${API_BASE_URL}/api/audit/masters/external-audit-orgs/`
  );
  return response.data.data;
}

export async function createAuditHodAssignment(data: AuditHodAssignmentPayload): Promise<AuditHodAssignment> {
  const response = await apiClient.post<AuditApiResponse<AuditHodAssignment>>(
    `${API_BASE_URL}/api/audit/admin/hod-coverage/`,
    data
  );
  return response.data.data;
}

export async function expireAuditHodAssignment(id: string): Promise<AuditHodAssignment> {
  const response = await apiClient.post<AuditApiResponse<AuditHodAssignment>>(
    `${API_BASE_URL}/api/audit/admin/hod-coverage/${id}/expire/`,
    {}
  );
  return response.data.data;
}

export async function getFailedAuditNotifications(): Promise<AuditFailedNotificationList> {
  const response = await apiClient.get<AuditApiResponse<AuditFailedNotificationList>>(
    `${API_BASE_URL}/api/audit/dpa/notifications/failed/`
  );
  return response.data.data;
}

export async function retryAuditNotification(id: string): Promise<AuditNotificationDelivery> {
  const response = await apiClient.post<AuditApiResponse<AuditNotificationDelivery>>(
    `${API_BASE_URL}/api/audit/notifications/${id}/retry/`,
    {}
  );
  return response.data.data;
}

export async function markAuditNotificationOffline(
  id: string,
  data: AuditNotificationOfflineData
): Promise<AuditNotificationDelivery> {
  const response = await apiClient.post<AuditApiResponse<AuditNotificationDelivery>>(
    `${API_BASE_URL}/api/audit/notifications/${id}/offline/`,
    data
  );
  return response.data.data;
}

export async function getAuditScanValidationQueue(): Promise<AuditScanValidationQueue> {
  const response = await apiClient.get<AuditApiResponse<AuditScanValidationQueue>>(
    `${API_BASE_URL}/api/audit/dpa/scan-validation-queue/`
  );
  return response.data.data;
}

export async function validateAuditScanAction(
  id: string,
  data: AuditScanValidationActionData
): Promise<AuditScanValidationAttachment> {
  const response = await apiClient.post<AuditApiResponse<AuditScanValidationAttachment>>(
    `${API_BASE_URL}/api/audit/attachments/${id}/validate/`,
    data
  );
  return response.data.data;
}

export async function getAuditPlan(id: string): Promise<AuditPlan> {
  const response = await apiClient.get<AuditApiResponse<AuditPlan>>(
    `${API_BASE_URL}/api/audit/plans/${id}/`
  );
  return response.data.data;
}

export async function createAuditPlan(data: AuditPlanFormData): Promise<AuditPlan> {
  const response = await apiClient.post<AuditApiResponse<AuditPlan>>(
    `${API_BASE_URL}/api/audit/plans/`,
    cleanAuditPlanPayload(data)
  );
  return response.data.data;
}

export async function updateAuditPlan(id: string, data: AuditPlanFormData): Promise<AuditPlan> {
  const response = await apiClient.patch<AuditApiResponse<AuditPlan>>(
    `${API_BASE_URL}/api/audit/plans/${id}/`,
    cleanAuditPlanPayload(data)
  );
  return response.data.data;
}

export async function requestAuditPlanExtension(
  id: string,
  data: AuditPlanExtensionRequestData
): Promise<AuditPlan> {
  const response = await apiClient.post<AuditApiResponse<AuditPlan>>(
    `${API_BASE_URL}/api/audit/plans/${id}/extension/`,
    data
  );
  return response.data.data;
}

export async function decideAuditPlanExtension(
  id: string,
  data: AuditPlanExtensionDecisionData
): Promise<AuditPlan> {
  const response = await apiClient.post<AuditApiResponse<AuditPlan>>(
    `${API_BASE_URL}/api/audit/plans/${id}/extension/decide/`,
    data
  );
  return response.data.data;
}

export async function recordAuditPlanFlagNotification(
  id: string,
  data: AuditPlanFlagNotificationData
): Promise<AuditPlan> {
  const response = await apiClient.post<AuditApiResponse<AuditPlan>>(
    `${API_BASE_URL}/api/audit/plans/${id}/flag-notify/`,
    data
  );
  return response.data.data;
}

export async function cancelAuditPlan(id: string, data: AuditPlanCancelData): Promise<AuditPlan> {
  const response = await apiClient.post<AuditApiResponse<AuditPlan>>(
    `${API_BASE_URL}/api/audit/plans/${id}/cancel/`,
    data
  );
  return response.data.data;
}

export async function createAdditionalAuditPlan(data: AuditPlanAdditionalData): Promise<AuditPlan> {
  const response = await apiClient.post<AuditApiResponse<AuditPlan>>(
    `${API_BASE_URL}/api/audit/plans/additional/`,
    cleanAuditPlanAdditionalPayload(data)
  );
  return response.data.data;
}

export async function getAuditDetail(id: string): Promise<AuditDetail> {
  const response = await apiClient.get<AuditApiResponse<AuditDetail>>(
    `${API_BASE_URL}/api/audit/audits/${id}/`
  );
  return response.data.data;
}

export async function getAuditChecklist(id: string): Promise<AuditChecklist> {
  const response = await apiClient.get<AuditApiResponse<AuditChecklist>>(
    `${API_BASE_URL}/api/audit/masters/checklists/`,
    { params: { audit_id: id } }
  );
  return response.data.data;
}

function cleanFindingPayload(data: AuditFindingCreatePayload) {
  const { evidence_files: _evidenceFiles, ...payloadData } = data;
  return {
    ...payloadData,
    nc_category: payloadData.finding_type === 'NC' ? payloadData.nc_category : '',
    observation_category: payloadData.finding_type === 'OBSERVATION' ? payloadData.observation_category : '',
    checklist_item_id: payloadData.checklist_item_id || null,
    original_due_date: payloadData.original_due_date || null,
    certificates_at_risk: payloadData.certificates_at_risk || '',
    is_fleetwide_relevance: payloadData.finding_type === 'NC' ? payloadData.is_fleetwide_relevance : false,
    clauses: payloadData.clauses.map((clause) => ({
      ...clause,
      rule_clause_id: clause.rule_clause_id || null,
      clause_ref_text: clause.clause_ref_text || '',
      clause_subref_text: clause.clause_subref_text || '',
    })),
  };
}

function buildAuditFindingFormData(data: AuditFindingCreatePayload): FormData {
  const formData = new FormData();
  const payload = cleanFindingPayload(data);

  Object.entries(payload).forEach(([key, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    formData.append(key, typeof value === 'object' ? JSON.stringify(value) : String(value));
  });

  (data.evidence_files || []).forEach((file) => {
    formData.append('evidence_files', file);
  });

  return formData;
}

export async function issueAuditFindingCircular(findingId: string): Promise<AuditIssueCircularResponse> {
  const response = await apiClient.post<AuditApiResponse<AuditIssueCircularResponse>>(
    `${API_BASE_URL}/api/audit/findings/${findingId}/issue-circular/`,
    {}
  );
  return response.data.data;
}

export async function createAuditFinding(
  id: string,
  data: AuditFindingCreatePayload
): Promise<AuditFindingCreateResponse> {
  if (data.evidence_files?.length) {
    const response = await apiClient.post<AuditApiResponse<AuditFindingCreateResponse>>(
      `${API_BASE_URL}/api/audit/audits/${id}/findings/`,
      buildAuditFindingFormData(data),
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return response.data.data;
  }

  const response = await apiClient.post<AuditApiResponse<AuditFindingCreateResponse>>(
    `${API_BASE_URL}/api/audit/audits/${id}/findings/`,
    cleanFindingPayload(data)
  );
  return response.data.data;
}

export async function getAuditClauseMaster(book: string): Promise<AuditClauseMaster> {
  const response = await apiClient.get<AuditApiResponse<AuditClauseMaster>>(
    `${API_BASE_URL}/api/audit/masters/clauses/${book}/`
  );
  return response.data.data;
}

export async function getAuditNcClosure(findingId: string): Promise<AuditNcClosure> {
  const response = await apiClient.get<AuditApiResponse<AuditNcClosure>>(
    `${API_BASE_URL}/api/audit/findings/${findingId}/nc/`
  );
  return response.data.data;
}

export async function getAuditRcaTemplates(category?: string): Promise<AuditRcaTemplateMaster> {
  const response = await apiClient.get<AuditApiResponse<AuditRcaTemplateMaster>>(
    `${API_BASE_URL}/api/audit/masters/rca-templates/`,
    { params: category ? { category } : undefined }
  );
  return response.data.data;
}

export async function updateAuditNcPart(
  findingId: string,
  part: AuditNcPartName,
  data: AuditNcPartPayload
): Promise<AuditNcClosure> {
  const response = await apiClient.put<AuditApiResponse<AuditNcClosure>>(
    `${API_BASE_URL}/api/audit/findings/${findingId}/nc/${part}/`,
    data
  );
  return response.data.data;
}

export async function getAuditObsClosure(findingId: string): Promise<AuditObsClosure> {
  const response = await apiClient.get<AuditApiResponse<AuditObsClosure>>(
    `${API_BASE_URL}/api/audit/findings/${findingId}/obs/`
  );
  return response.data.data;
}

export async function updateAuditObsPart(
  findingId: string,
  part: AuditObsPartName,
  data: AuditObsPartPayload
): Promise<AuditObsClosure> {
  const response = await apiClient.put<AuditApiResponse<AuditObsClosure>>(
    `${API_BASE_URL}/api/audit/findings/${findingId}/obs/${part}/`,
    data
  );
  return response.data.data;
}

export async function draftAuditNcForVessel(
  findingId: string,
  data: AuditNcDraftPayload
): Promise<AuditNcClosure> {
  const response = await apiClient.post<AuditApiResponse<AuditNcClosure>>(
    `${API_BASE_URL}/api/audit/findings/${findingId}/nc/draft/`,
    data
  );
  return response.data.data;
}

export async function transitionAuditFindingCar(
  findingId: string,
  action: AuditNcWorkflowAction,
  comment?: string
): Promise<AuditNcWorkflowResponse> {
  const response = await apiClient.post<AuditApiResponse<AuditNcWorkflowResponse>>(
    `${API_BASE_URL}/api/audit/findings/${findingId}/car/workflow/`,
    { action, comment: comment || '' }
  );
  return response.data.data;
}

export async function updateAuditDetail(
  id: string,
  data: AuditDetailEditableFields
): Promise<AuditDetail> {
  const response = await apiClient.patch<AuditApiResponse<AuditDetail>>(
    `${API_BASE_URL}/api/audit/audits/${id}/`,
    data
  );
  return response.data.data;
}

export async function updateAuditScorecard(
  id: string,
  rows: Pick<AuditScorecardRow, 'area_code' | 'status' | 'remarks'>[]
): Promise<AuditDetail> {
  const response = await apiClient.put<AuditApiResponse<AuditDetail>>(
    `${API_BASE_URL}/api/audit/audits/${id}/scorecard/`,
    { rows }
  );
  return response.data.data;
}

export async function submitAuditReport(id: string): Promise<AuditDetail> {
  const response = await apiClient.post<AuditApiResponse<AuditDetail>>(
    `${API_BASE_URL}/api/audit/audits/${id}/submit/`,
    {}
  );
  return response.data.data;
}

export async function acknowledgeAuditReport(id: string): Promise<AuditDetail> {
  const response = await apiClient.post<AuditApiResponse<AuditDetail>>(
    `${API_BASE_URL}/api/audit/audits/${id}/acknowledge/`,
    {}
  );
  return response.data.data;
}

export async function confirmExternalAuditCloseout(
  id: string,
  data: ExternalAuditCloseoutPayload
): Promise<AuditDetail> {
  const response = await apiClient.post<AuditApiResponse<AuditDetail>>(
    `${API_BASE_URL}/api/audit/audits/${id}/external/close/`,
    data
  );
  return response.data.data;
}

export async function editExternalAuditCertLinks(
  id: string,
  data: ExternalCertLinkPayload
): Promise<AuditDetail> {
  const response = await apiClient.post<AuditApiResponse<AuditDetail>>(
    `${API_BASE_URL}/api/audit/audits/${id}/certs/link/`,
    data
  );
  return response.data.data;
}

export const auditApi = {
  acknowledgeAuditReport,
  cancelAuditPlan,
  createAdditionalAuditPlan,
  createAuditPlan,
  createAuditFinding,
  createAuditHodAssignment,
  createAuditQualifyingBody,
  createAuditQualifiedAuditor,
  createAuditRegistration,
  confirmExternalAuditCloseout,
  draftAuditNcForVessel,
  editExternalAuditCertLinks,
  expireAuditHodAssignment,
  getRegisteredAudits,
  getAuditClauseMaster,
  getAuditChecklist,
  getAuditNcClosure,
  getAuditObsClosure,
  getAuditPlan,
  getAuditPlans,
  getAuditQualifyingBodies,
  getAuditQualifiedAuditors,
  getAuditOfficeUsers,
  getAuditHodCoverage,
  getAuditVessels,
  getAuditRcaTemplates,
  issueAuditFindingCircular,
  getAuditDetail,
  getAuditExternalAuditOrgs,
  getFailedAuditNotifications,
  getAuditScanValidationQueue,
  markAuditNotificationOffline,
  decideAuditPlanExtension,
  recordAuditPlanFlagNotification,
  requestAuditPlanExtension,
  retryAuditNotification,
  validateAuditScanAction,
  submitAuditReport,
  transitionAuditFindingCar,
  updateAuditNcPart,
  updateAuditObsPart,
  updateAuditDetail,
  updateAuditPlan,
  updateAuditQualifyingBody,
  updateAuditQualifiedAuditor,
  updateAuditScorecard,
};
