"""Safety API views package."""
from .auditor_export import AuditorBundleExportView
from .corrective_action import (
    CorrectiveActionDetailView,
    CorrectiveActionLinkPurchaseView,
    CorrectiveActionListCreateView,
    CorrectiveActionPhysicalVerifyView,
    CorrectiveActionTransitionView,
)
from .dashboard import (
    DashboardCompositeView,
    DashboardHeinrichView,
    DashboardParetoView,
    DashboardRepeatRootCauseView,
)
from .field_history import FieldHistoryView, IncidentAuditView
from .fleet_alert import FleetAlertIssueView
from .finding_closure import (
    SOIFindingApproveClosureView,
    SOIFindingDetailView,
    SOIFindingPendingClosureView,
)
from .incident import IncidentDetailView, IncidentListCreateView, IncidentTransitionView
from .incident_circular import IncidentCircularPublishView
from .incident_draft import IncidentDraftSaveView
from .incident_external_party import IncidentExternalPartyInjuryView
from .incident_pdf import IncidentPDFDownloadView
from .msc_mepc3_export import MscMepc3ExportView
from .incident_phase1 import IncidentPhase1CreateView, IncidentPhase1SubmitView, IncidentPhase1UpdateView
from .incident_phase2 import IncidentPhase2SubmitView, IncidentPhase2UpdateView
from .incident_phase3 import (
    IncidentPhase3ChainOfCustodyView,
    IncidentPhase3EvidenceMatrixView,
    IncidentPhase3EvidenceView,
    IncidentPhase3InterviewView,
)
from .incident_phase4 import IncidentPhase4EvidenceSourceListView
from .incident_phase6 import (
    IncidentPhase6WorkspaceView,
    IncidentRecommendationDetailView,
    IncidentRecommendationListCreateView,
    RecommendationThemeListView,
)
from .incident_phase7 import (
    IncidentPhase7AcceptView,
    IncidentPhase7ApproveRedView,
    IncidentPhase7PreflightView,
    IncidentPhase7SendBackView,
)
from .incident_phase8 import IncidentPhase8CloseView, IncidentPhase8VerifyView, IncidentPhase8WorkspaceView
from .incident_reopen import IncidentReopenView
from .near_miss import NearMissDetailView, NearMissListCreateView
from .near_miss_analysis import (
    NearMissAnalysisFactDetailView,
    NearMissAnalysisFactListCreateView,
    NearMissAnalysisWorkspaceView,
)
from .near_miss_pdf import NearMissPDFDownloadView
from .near_miss_triage import NearMissTriageView
from .phase_log import PhaseLogView
from .root import safety_api_root
from .search import SafetyCrossRecordSearchView
from .soi import SOIApplicabilityView, SOIDetailView, SOIListCreateView
from .soi_applicability_approve import SOIApplicabilityApproveView
from .soi_applicability_request import SOIApplicabilityRequestView
from .soi_close import SOICloseView
from .soi_create import SOICreateConfigView
from .soi_pdf import SOISummaryPDFDownloadView
from .soi_pick_areas import SOIPickAreasView
from .soi_trainees import SOITraineeView
from .scm_pdf import SCMPDFDownloadView
from .taxonomy_admin import (
    CaseStudyHelpDrawerListView,
    ReferenceBiasGuardListView,
    ReferenceCaseStudyDetailView,
    ReferenceCaseStudyListCreateView,
    ReferenceImmediateCauseDetailView,
    ReferenceImmediateCauseListView,
    ReferenceIncidentTypeDetailView,
    ReferenceIncidentTypeListView,
    ReferenceLossTypeDetailView,
    ReferenceLossTypeListView,
    ReferenceMscatDetailView,
    ReferenceMscatListView,
    ReferenceSOIAreaDetailView,
    ReferenceSOIAreaListView,
    ReferenceSOIChecklistVersionDetailView,
    ReferenceSOIChecklistVersionListView,
    ReferenceSOIItemDetailView,
    ReferenceSOIItemListView,
)

__all__ = [
    "AuditorBundleExportView",
    "CorrectiveActionDetailView",
    "CorrectiveActionLinkPurchaseView",
    "CorrectiveActionListCreateView",
    "CorrectiveActionPhysicalVerifyView",
    "CorrectiveActionTransitionView",
    "DashboardCompositeView",
    "DashboardHeinrichView",
    "DashboardParetoView",
    "DashboardRepeatRootCauseView",
    "FieldHistoryView",
    "FleetAlertIssueView",
    "IncidentAuditView",
    "IncidentCircularPublishView",
    "IncidentDraftSaveView",
    "IncidentDetailView",
    "IncidentExternalPartyInjuryView",
    "IncidentListCreateView",
    "IncidentPDFDownloadView",
    "IncidentPhase1CreateView",
    "IncidentPhase1SubmitView",
    "IncidentPhase1UpdateView",
    "IncidentPhase2SubmitView",
    "IncidentPhase2UpdateView",
    "IncidentPhase3ChainOfCustodyView",
    "IncidentPhase3EvidenceMatrixView",
    "IncidentPhase3EvidenceView",
    "IncidentPhase3InterviewView",
    "IncidentPhase4EvidenceSourceListView",
    "IncidentPhase6WorkspaceView",
    "IncidentPhase7AcceptView",
    "IncidentPhase7ApproveRedView",
    "IncidentPhase7PreflightView",
    "IncidentPhase7SendBackView",
    "IncidentPhase8CloseView",
    "IncidentPhase8VerifyView",
    "IncidentPhase8WorkspaceView",
    "IncidentReopenView",
    "IncidentRecommendationDetailView",
    "IncidentRecommendationListCreateView",
    "IncidentTransitionView",
    "NearMissDetailView",
    "NearMissListCreateView",
    "NearMissAnalysisFactDetailView",
    "NearMissAnalysisFactListCreateView",
    "NearMissAnalysisWorkspaceView",
    "NearMissPDFDownloadView",
    "NearMissTriageView",
    "MscMepc3ExportView",
    "PhaseLogView",
    "RecommendationThemeListView",
    "SCMPDFDownloadView",
    "SafetyCrossRecordSearchView",
    "CaseStudyHelpDrawerListView",
    "ReferenceBiasGuardListView",
    "ReferenceCaseStudyDetailView",
    "ReferenceCaseStudyListCreateView",
    "ReferenceImmediateCauseDetailView",
    "ReferenceImmediateCauseListView",
    "ReferenceIncidentTypeDetailView",
    "ReferenceIncidentTypeListView",
    "ReferenceLossTypeDetailView",
    "ReferenceLossTypeListView",
    "ReferenceMscatDetailView",
    "ReferenceMscatListView",
    "ReferenceSOIAreaDetailView",
    "ReferenceSOIAreaListView",
    "ReferenceSOIChecklistVersionDetailView",
    "ReferenceSOIChecklistVersionListView",
    "ReferenceSOIItemDetailView",
    "ReferenceSOIItemListView",
    "SOIApplicabilityApproveView",
    "SOIApplicabilityRequestView",
    "SOIApplicabilityView",
    "SOICloseView",
    "SOICreateConfigView",
    "SOIDetailView",
    "SOISummaryPDFDownloadView",
    "SOIFindingApproveClosureView",
    "SOIFindingDetailView",
    "SOIFindingPendingClosureView",
    "SOIListCreateView",
    "SOIPickAreasView",
    "SOITraineeView",
    "safety_api_root",
]
