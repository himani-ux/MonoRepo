export const AUDIT_NOTIFICATION_OFFLINE_REASON_MIN = 30;

export interface AuditNotificationDelivery {
  id: string;
  psc_notification_id: string;
  notification_type: string | null;
  title: string | null;
  message: string | null;
  entity_type: string | null;
  entity_id: string | null;
  vessel_id: string | null;
  recipient_type: string | null;
  recipient_id: string | null;
  channel: 'IN_SYSTEM' | 'EMAIL' | 'SLACK' | string;
  recipient_address: string | null;
  status: string;
  attempt_count: number;
  first_attempted_at: string | null;
  last_attempted_at: string | null;
  last_error: string | null;
  sent_at: string | null;
  resolved_offline_reason: string | null;
  created_date: string | null;
}

export interface AuditFailedNotificationList {
  count: number;
  results: AuditNotificationDelivery[];
}

export interface AuditNotificationOfflineData {
  reason: string;
}
