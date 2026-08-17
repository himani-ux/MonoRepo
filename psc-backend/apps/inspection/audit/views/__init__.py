"""Audit view namespace; DRF views land with their owning APIs."""

from .car_workflow import AuditFindingCarWorkflowView
from .checklist import AuditChecklistMasterView
from .clause import AuditClauseMasterView, AuditRcaTemplateMasterView
from .detail import AuditDetailView, AuditScorecardView
from .external import AuditExternalCertLinkView, AuditExternalCloseoutView
from .finding import AuditFindingCreateView, AuditFindingIssueCircularView
from .nc_closure import AuditFindingNcClosureView, AuditFindingNcDraftView, AuditFindingNcPartView
from .notification import (
    AuditFailedNotificationListView,
    AuditNotificationOfflineResolveView,
    AuditNotificationRetryView,
)
from .obs_closure import AuditFindingObsClosureView, AuditFindingObsPartView
from .pdf import AuditFindingNcPdfView, AuditFindingObsPdfView, AuditPlanPdfView, AuditReportPdfView
from .plan import (
    AuditPlanAdditionalView,
    AuditPlanCancelView,
    AuditPlanDetailView,
    AuditPlanExtensionDecideView,
    AuditPlanExtensionRequestView,
    AuditPlanFlagNotifyView,
    AuditPlanListCreateView,
)
from .registration import AuditRegistrationView
from .scan_validation import AuditAttachmentValidateView, AuditScanValidationQueueView
from .submit import AuditAcknowledgeView, AuditSubmitView
from .vessels import AuditVesselOptionListView

__all__ = [
    "AuditAcknowledgeView",
    "AuditAttachmentValidateView",
    "AuditChecklistMasterView",
    "AuditClauseMasterView",
    "AuditDetailView",
    "AuditExternalCertLinkView",
    "AuditExternalCloseoutView",
    "AuditFindingCarWorkflowView",
    "AuditFindingCreateView",
    "AuditFindingIssueCircularView",
    "AuditFindingNcClosureView",
    "AuditFindingNcDraftView",
    "AuditFindingNcPartView",
    "AuditFailedNotificationListView",
    "AuditNotificationOfflineResolveView",
    "AuditNotificationRetryView",
    "AuditFindingObsClosureView",
    "AuditFindingObsPartView",
    "AuditFindingNcPdfView",
    "AuditFindingObsPdfView",
    "AuditPlanPdfView",
    "AuditReportPdfView",
    "AuditPlanDetailView",
    "AuditPlanAdditionalView",
    "AuditPlanCancelView",
    "AuditPlanExtensionDecideView",
    "AuditPlanExtensionRequestView",
    "AuditPlanFlagNotifyView",
    "AuditPlanListCreateView",
    "AuditRegistrationView",
    "AuditRcaTemplateMasterView",
    "AuditScanValidationQueueView",
    "AuditScorecardView",
    "AuditSubmitView",
    "AuditVesselOptionListView",
]
