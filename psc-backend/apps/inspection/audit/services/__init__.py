"""Audit service-layer namespace for registration, finding, closure, and alerts."""

from .car_workflow import (
    AuditCarWorkflowContext,
    AuditCarWorkflowError,
    resolve_audit_car_workflow_context,
    validate_audit_proxy_preconditions,
)
from .finding import (
    AuditFindingCreateResult,
    AuditFindingError,
    AuditFindingStateError,
    AuditFindingValidationError,
    create_audit_finding,
)
from .audit_window import AuditWindow, AuditWindowRuleMissing, compute_window_for_plan
from .alert_engine import AuditWindowAlertEvent, AuditWindowTickResult, run_internal_audit_window_ladder
from .notification_dispatcher import (
    SUPPORTED_AUDIT_NOTIFICATION_TYPES,
    AuditNotificationDispatchResult,
    AuditNotificationRecipient,
    dispatch_audit_notification,
    resolve_audit_notification_recipients,
)
from .pdf_validation import (
    MATCHED,
    MISMATCH_FINDING,
    MISMATCH_VERSION,
    MISMATCH_VESSEL,
    NOT_APPLICABLE,
    UNREADABLE,
    accept_scan_with_reason,
    reject_scan_for_rescan,
    scan_validation_queue_queryset,
    validate_uploaded_scan,
)
from .email_relay import AuditEmailRelay, AuditEmailRelayResult, process_due_audit_email_notifications
from .slack_relay import AuditSlackRelay, AuditSlackRelayResult, process_due_audit_slack_notifications

__all__ = [
    "AuditEmailRelay",
    "AuditEmailRelayResult",
    "AuditCarWorkflowContext",
    "AuditCarWorkflowError",
    "AuditFindingCreateResult",
    "AuditFindingError",
    "AuditFindingStateError",
    "AuditFindingValidationError",
    "AuditWindow",
    "AuditWindowAlertEvent",
    "AuditWindowRuleMissing",
    "AuditWindowTickResult",
    "AuditNotificationDispatchResult",
    "AuditNotificationRecipient",
    "AuditSlackRelay",
    "AuditSlackRelayResult",
    "MATCHED",
    "MISMATCH_FINDING",
    "MISMATCH_VERSION",
    "MISMATCH_VESSEL",
    "NOT_APPLICABLE",
    "UNREADABLE",
    "accept_scan_with_reason",
    "compute_window_for_plan",
    "create_audit_finding",
    "dispatch_audit_notification",
    "process_due_audit_email_notifications",
    "process_due_audit_slack_notifications",
    "reject_scan_for_rescan",
    "resolve_audit_car_workflow_context",
    "resolve_audit_notification_recipients",
    "run_internal_audit_window_ladder",
    "scan_validation_queue_queryset",
    "SUPPORTED_AUDIT_NOTIFICATION_TYPES",
    "validate_audit_proxy_preconditions",
    "validate_uploaded_scan",
]
