import { apiClient } from './client';
import { API_BASE_URL } from '@/lib/utils/constants';
import type { AuditChecklist } from '@/schemas/audit/checklist';
import type { AuditDetail, AuditDetailEditableFields, AuditScorecardRow } from '@/schemas/audit/detail';
import type {
  AuditClauseMaster,
  AuditFindingCreateFormData,
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
  return {
    ...data,
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
          cycle_year: data.cycle_year || null,
          external_report_file_size: data.external_report_file_size || null,
        }
      : {}),
  };
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
  const response = await apiClient.post<AuditApiResponse<AuditRegistrationResponse>>(
    `${API_BASE_URL}/api/audit/audits/`,
    cleanAuditRegistrationPayload(data)
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

function cleanFindingPayload(data: AuditFindingCreateFormData) {
  return {
    ...data,
    nc_category: data.finding_type === 'NC' ? data.nc_category : '',
    observation_category: data.finding_type === 'OBSERVATION' ? data.observation_category : '',
    checklist_item_id: data.checklist_item_id || null,
    certificate_impact: data.certificate_impact || '',
    certificates_at_risk: data.finding_type === 'NC' ? data.certificates_at_risk || '' : '',
    is_fleetwide_relevance: data.finding_type === 'NC' ? data.is_fleetwide_relevance : false,
    clauses: data.clauses.map((clause) => ({
      ...clause,
      rule_clause_id: clause.rule_clause_id || null,
      clause_ref_text: clause.clause_ref_text || '',
      clause_subref_text: clause.clause_subref_text || '',
    })),
  };
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
  data: AuditFindingCreateFormData
): Promise<AuditFindingCreateResponse> {
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
  createAuditRegistration,
  confirmExternalAuditCloseout,
  draftAuditNcForVessel,
  editExternalAuditCertLinks,
  getAuditClauseMaster,
  getAuditChecklist,
  getAuditNcClosure,
  getAuditObsClosure,
  getAuditPlan,
  getAuditPlans,
  getAuditRcaTemplates,
  issueAuditFindingCircular,
  getAuditDetail,
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
  updateAuditScorecard,
};
