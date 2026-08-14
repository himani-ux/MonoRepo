export const AUDIT_SCAN_ACCEPT_REASON_MIN = 50;

export type AuditScanValidationStatus =
  | 'MATCHED'
  | 'MISMATCH_FINDING'
  | 'MISMATCH_VESSEL'
  | 'MISMATCH_VERSION'
  | 'UNREADABLE'
  | 'NOT_APPLICABLE'
  | string;

export interface AuditScanValidationAttachment {
  id: string;
  audit_detail_id: string;
  audit_finding_id: string | null;
  file_name: string;
  file_path: string;
  mime_type: string;
  category: string;
  attachment_version: string;
  linked_pdf_generation_id: string | null;
  pdf_hash_validation_status: AuditScanValidationStatus | null;
  validated_at: string | null;
  validator_message: string | null;
  uploaded_by: string;
  uploaded_at: string | null;
}

export interface AuditScanValidationQueue {
  count: number;
  results: AuditScanValidationAttachment[];
}

export interface AuditScanValidationActionData {
  action: 'ACCEPT_WITH_REASON' | 'REJECT_RESCAN';
  reason?: string;
}
