from django.urls import path

from apps.safety.views.corrective_action import (
    CorrectiveActionDetailView,
    CorrectiveActionLinkPurchaseView,
    CorrectiveActionListCreateView,
    CorrectiveActionPhysicalVerifyView,
    CorrectiveActionTransitionView,
)
from apps.safety.views.auditor_export import AuditorBundleExportView
from apps.safety.views.dashboard import (
    DashboardCAAgingView,
    DashboardCompositeView,
    DashboardHeinrichView,
    DashboardParetoView,
    DashboardRepeatRootCauseView,
    DashboardSOIComplianceView,
)
from apps.safety.views.dashboard_export import DashboardExportView
from apps.safety.views.field_history import FieldHistoryView, IncidentAuditView
from apps.safety.views.incident import (
    IncidentDetailView,
    IncidentListCreateView,
    IncidentPositionPrefillView,
    IncidentTransitionView,
)
from apps.safety.views.incident_closure import IncidentClosureView
from apps.safety.views.incident_circular import IncidentCircularPublishView
from apps.safety.views.incident_draft import IncidentDraftSaveView
from apps.safety.views.incident_external_party import IncidentExternalPartyInjuryView
from apps.safety.views.incident_pdf import IncidentPDFDownloadView
from apps.safety.views.msc_mepc3_export import MscMepc3ExportView
from apps.safety.views.incident_phase1 import (
    IncidentPhase1CreateView,
    IncidentPhase1SubmitView,
    IncidentPhase1UpdateView,
)
from apps.safety.views.incident_phase2 import IncidentPhase2SubmitView, IncidentPhase2UpdateView
from apps.safety.views.incident_phase3 import (
    IncidentPhase3AttachmentUploadView,
    IncidentPhase3ChainOfCustodyView,
    IncidentPhase3DeadlineTaskView,
    IncidentPhase3EvidenceMatrixView,
    IncidentPhase3EvidenceView,
    IncidentPhase3InterviewView,
)
from apps.safety.views.incident_phase4 import (
    IncidentLinkActionView,
    IncidentPhase4EvidenceSourceListView,
    IncidentPhase4FactContradictionView,
    IncidentPhase4FactDetailView,
    IncidentPhase4FactListCreateView,
    IncidentPhase4GateView,
    IncidentPhase4FactReorderView,
)
from apps.safety.views.incident_phase5 import (
    IncidentBiasGuardChecklistView,
    IncidentBlameOverrideView,
    IncidentMscatSearchView,
    IncidentPhase5CauseDetailView,
    IncidentPhase5CauseListCreateView,
    IncidentPhase5SafeguardDetailView,
    IncidentPhase5SafeguardListCreateView,
    IncidentPhase5WorkspaceView,
)
from apps.safety.views.incident_phase6 import (
    IncidentPhase6WorkspaceView,
    IncidentRecommendationDetailView,
    IncidentRecommendationListCreateView,
    RecommendationThemeListView,
)
from apps.safety.views.incident_phase7 import (
    IncidentPhase7AcceptView,
    IncidentPhase7ApproveRedView,
    IncidentPhase7HodSignatureView,
    IncidentPhase7PreflightView,
    IncidentPhase7SendBackView,
)
from apps.safety.views.incident_phase8 import (
    IncidentPhase8CloseView,
    IncidentPhase8VerifyView,
    IncidentPhase8WorkspaceView,
)
from apps.safety.views.incident_reopen import IncidentReopenView
from apps.safety.views.fleet_alert import FleetAlertIssueView
from apps.safety.views.finding_closure import (
    SOIFindingApproveClosureView,
    SOIFindingDetailView,
    SOIFindingPendingClosureView,
    SOIFindingReopenView,
)
from apps.safety.views.near_miss import NearMissDetailView, NearMissListCreateView, NearMissRateLimitView
from apps.safety.views.near_miss_analysis import (
    NearMissAnalysisEvidenceSourceCreateView,
    NearMissAnalysisEvidencePhotoView,
    NearMissAnalysisFactDetailView,
    NearMissAnalysisFactListCreateView,
    NearMissAnalysisWorkspaceView,
)
from apps.safety.views.near_miss_closure import NearMissAuditView, NearMissClosureView
from apps.safety.views.near_miss_pdf import NearMissPDFDownloadView
from apps.safety.views.near_miss_review import NearMissReviewView, NearMissReworkSubmitView
from apps.safety.views.near_miss_triage import NearMissTriageView
from apps.safety.views.phase_log import PhaseLogView
from apps.safety.views.root import safety_api_root
from apps.safety.views.search import SafetyCrossRecordSearchView
from apps.safety.views.scm import SCMCreateRegularView, SCMDetailView, SCMListCreateView, SCMSubmitView
from apps.safety.views.scm_adhoc import SCMCreateAdHocView
from apps.safety.views.scm_agenda import SCMAgendaView
from apps.safety.views.scm_attendance import SCMAttendanceAcknowledgeView, SCMAttendanceListCreateView
from apps.safety.views.scm_closed_since import SCMClosedSinceLastMeetingView, SCMClosedSinceLastVesselView
from apps.safety.views.scm_office_comment import SCMOfficeCommentView
from apps.safety.views.scm_pdf import SCMPDFDownloadView
from apps.safety.views.scm_signoff import SCMSignOffPreflightView, SCMSignOffView
from apps.safety.views.scm_signature import SCMSignatureView
from apps.safety.views.scm_soi_feed import SCMSoIAutoFeedMeetingView, SOIOpenFindingsVesselView
from apps.safety.views.soi import SOIApplicabilityView, SOIDetailView, SOIListCreateView
from apps.safety.views.soi_applicability_approve import SOIApplicabilityApproveView
from apps.safety.views.soi_applicability_request import SOIApplicabilityRequestView
from apps.safety.views.soi_checklist_version import SOIActiveChecklistVersionView
from apps.safety.views.soi_compliance import SOIComplianceView
from apps.safety.views.soi_create import SOICreateConfigView, SOISection12StatusView
from apps.safety.views.soi_close import SOICloseView
from apps.safety.views.soi_download import SOIDownloadView
from apps.safety.views.soi_finding import SOIFindingListCreateView, SOIFindingPhotoUploadView, SOISubmitFindingsView
from apps.safety.views.soi_officer_setting import SOIOfficerSettingView
from apps.safety.views.soi_pick_areas import SOIPickAreasView
from apps.safety.views.soi_pdf import SOISummaryPDFDownloadView
from apps.safety.views.soi_reprint import SOIReprintView
from apps.safety.views.soi_trainees import SOITraineeView
from apps.safety.views.taxonomy_admin import (
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

app_name = "safety"

urlpatterns = [
    path("", safety_api_root, name="api-root"),
    path("dashboard/composite/", DashboardCompositeView.as_view(), name="dashboard-composite"),
    path("dashboard/heinrich/", DashboardHeinrichView.as_view(), name="dashboard-heinrich"),
    path(
        "dashboard/repeat-root-cause/",
        DashboardRepeatRootCauseView.as_view(),
        name="dashboard-repeat-root-cause",
    ),
    path("dashboard/pareto/", DashboardParetoView.as_view(), name="dashboard-pareto"),
    path("dashboard/soi-compliance/", DashboardSOIComplianceView.as_view(), name="dashboard-soi-compliance"),
    path("dashboard/ca-aging/", DashboardCAAgingView.as_view(), name="dashboard-ca-aging"),
    path("dashboard/export/", DashboardExportView.as_view(), name="dashboard-export"),
    path("search/", SafetyCrossRecordSearchView.as_view(), name="search"),
    path("master/case-studies/", CaseStudyHelpDrawerListView.as_view(), name="master-case-studies"),
    path("reference/mscat/", ReferenceMscatListView.as_view(), name="reference-mscat-list"),
    path("reference/mscat/<str:subcode_id>/", ReferenceMscatDetailView.as_view(), name="reference-mscat-detail"),
    path(
        "reference/immediate-causes/",
        ReferenceImmediateCauseListView.as_view(),
        name="reference-immediate-causes-list",
    ),
    path(
        "reference/immediate-causes/<str:pk>/",
        ReferenceImmediateCauseDetailView.as_view(),
        name="reference-immediate-causes-detail",
    ),
    path("reference/loss-types/", ReferenceLossTypeListView.as_view(), name="reference-loss-types-list"),
    path("reference/loss-types/<str:pk>/", ReferenceLossTypeDetailView.as_view(), name="reference-loss-types-detail"),
    path("reference/soi-areas/", ReferenceSOIAreaListView.as_view(), name="reference-soi-areas-list"),
    path("reference/soi-areas/<str:pk>/", ReferenceSOIAreaDetailView.as_view(), name="reference-soi-areas-detail"),
    path("reference/soi-items/", ReferenceSOIItemListView.as_view(), name="reference-soi-items-list"),
    path("reference/soi-items/<str:pk>/", ReferenceSOIItemDetailView.as_view(), name="reference-soi-items-detail"),
    path(
        "reference/soi-checklist-versions/",
        ReferenceSOIChecklistVersionListView.as_view(),
        name="reference-soi-checklist-versions-list",
    ),
    path(
        "reference/soi-checklist-versions/<str:pk>/",
        ReferenceSOIChecklistVersionDetailView.as_view(),
        name="reference-soi-checklist-versions-detail",
    ),
    path("reference/bias-guards/", ReferenceBiasGuardListView.as_view(), name="reference-bias-guards-list"),
    path(
        "reference/incident-types/",
        ReferenceIncidentTypeListView.as_view(),
        name="reference-incident-types-list",
    ),
    path(
        "reference/incident-types/<str:pk>/",
        ReferenceIncidentTypeDetailView.as_view(),
        name="reference-incident-types-detail",
    ),
    path(
        "reference/case-studies/",
        ReferenceCaseStudyListCreateView.as_view(),
        name="reference-case-studies-list",
    ),
    path(
        "reference/case-studies/<slug:slug>/",
        ReferenceCaseStudyDetailView.as_view(),
        name="reference-case-studies-detail",
    ),
    path("incidents/", IncidentListCreateView.as_view(), name="incident-list"),
    path("scm/", SCMListCreateView.as_view(), name="scm-list"),
    path("scm/closed-since-last/", SCMClosedSinceLastVesselView.as_view(), name="scm-closed-since-last-vessel"),
    path("scm/create-regular/", SCMCreateRegularView.as_view(), name="scm-create-regular"),
    path("scm/create-adhoc/", SCMCreateAdHocView.as_view(), name="scm-create-adhoc"),
    path("scm/<str:id>/", SCMDetailView.as_view(), name="scm-detail"),
    path("scm/<str:id>/auto-feed/", SCMSoIAutoFeedMeetingView.as_view(), name="scm-auto-feed"),
    path("scm/<str:id>/agenda/", SCMAgendaView.as_view(), name="scm-agenda"),
    path("scm/<str:id>/attendance/", SCMAttendanceListCreateView.as_view(), name="scm-attendance"),
    path("scm/<str:id>/attendance/acknowledge/", SCMAttendanceAcknowledgeView.as_view(), name="scm-attendance-ack"),
    path("scm/<str:id>/closed-since-last/", SCMClosedSinceLastMeetingView.as_view(), name="scm-closed-since-last"),
    path("scm/<str:id>/preflight/", SCMSignOffPreflightView.as_view(), name="scm-preflight"),
    path("scm/<str:id>/office-comment/", SCMOfficeCommentView.as_view(), name="scm-office-comment"),
    path("scm/<str:id>/pdf/", SCMPDFDownloadView.as_view(), name="scm-pdf"),
    path("scm/<str:id>/sign-off/", SCMSignOffView.as_view(), name="scm-signoff"),
    path("scm/<str:id>/signatures/", SCMSignatureView.as_view(), name="scm-signatures"),
    path("scm/<str:id>/submit/", SCMSubmitView.as_view(), name="scm-submit"),
    path("soi/", SOIListCreateView.as_view(), name="soi-list"),
    path("soi/compliance/", SOIComplianceView.as_view(), name="soi-compliance"),
    path("soi/create/", SOICreateConfigView.as_view(), name="soi-create-config"),
    path("soi/officer-setting/", SOIOfficerSettingView.as_view(), name="soi-officer-setting"),
    path("soi/section-12-status/", SOISection12StatusView.as_view(), name="soi-section12-status"),
    path("soi/applicability/", SOIApplicabilityView.as_view(), name="soi-applicability"),
    path(
        "master/soi-checklist-version/active/",
        SOIActiveChecklistVersionView.as_view(),
        name="soi-checklist-version-active",
    ),
    path("soi/<str:id>/", SOIDetailView.as_view(), name="soi-detail"),
    path("soi/<str:id>/checklist/download/", SOIDownloadView.as_view(), name="soi-checklist-download"),
    path("soi/<str:id>/close/", SOICloseView.as_view(), name="soi-close"),
    path(
        "soi/<str:id>/applicability/request/",
        SOIApplicabilityRequestView.as_view(),
        name="soi-applicability-request",
    ),
    path(
        "soi/<str:id>/applicability/approve/",
        SOIApplicabilityApproveView.as_view(),
        name="soi-applicability-approve",
    ),
    path("soi/<str:id>/findings/", SOIFindingListCreateView.as_view(), name="soi-findings"),
    path("soi/<str:id>/findings/photo/", SOIFindingPhotoUploadView.as_view(), name="soi-finding-photo-upload"),
    path("soi/findings/<str:finding_id>/", SOIFindingDetailView.as_view(), name="soi-finding-detail"),
    path(
        "soi/findings/<str:finding_id>/pending-closure/",
        SOIFindingPendingClosureView.as_view(),
        name="soi-finding-pending-closure",
    ),
    path(
        "soi/findings/<str:finding_id>/approve-closure/",
        SOIFindingApproveClosureView.as_view(),
        name="soi-finding-approve-closure",
    ),
    path(
        "soi/findings/<str:finding_id>/reopen/",
        SOIFindingReopenView.as_view(),
        name="soi-finding-reopen",
    ),
    path("soi/<str:id>/lost-paper/recover/", SOIReprintView.as_view(), name="soi-lost-paper-recover"),
    path("soi/<str:id>/pick-areas/", SOIPickAreasView.as_view(), name="soi-pick-areas"),
    path("soi/<str:id>/submit/", SOISubmitFindingsView.as_view(), name="soi-submit"),
    path("soi/<str:id>/pdf/", SOISummaryPDFDownloadView.as_view(), name="soi-pdf"),
    path("soi/<str:id>/pdf/summary/", SOISummaryPDFDownloadView.as_view(), name="soi-pdf-summary"),
    path("soi/<str:id>/trainees/", SOITraineeView.as_view(), name="soi-trainees"),
    path("soi/open-findings/", SOIOpenFindingsVesselView.as_view(), name="soi-open-findings"),
    path("near-miss/", NearMissListCreateView.as_view(), name="near-miss-list"),
    path("near-miss/rate-limit/", NearMissRateLimitView.as_view(), name="near-miss-rate-limit"),
    path("near-miss/<str:id>/", NearMissDetailView.as_view(), name="near-miss-detail"),
    path("near-miss/<str:id>/review/", NearMissReviewView.as_view(), name="near-miss-review"),
    path("near-miss/<str:id>/rework/", NearMissReworkSubmitView.as_view(), name="near-miss-rework-submit"),
    path("near-miss/<str:id>/triage/", NearMissTriageView.as_view(), name="near-miss-triage"),
    path("near-miss/<str:id>/fleet-alert/", FleetAlertIssueView.as_view(), name="near-miss-fleet-alert"),
    path("near-miss/<str:id>/pdf/", NearMissPDFDownloadView.as_view(), name="near-miss-pdf"),
    path("near-miss/<str:id>/closure/", NearMissClosureView.as_view(), name="near-miss-closure"),
    path("near-miss/<str:id>/audit/", NearMissAuditView.as_view(), name="near-miss-audit"),
    path("near-miss/<str:id>/analysis/", NearMissAnalysisWorkspaceView.as_view(), name="near-miss-analysis"),
    path(
        "near-miss/<str:id>/analysis/evidence/",
        NearMissAnalysisEvidenceSourceCreateView.as_view(),
        name="near-miss-analysis-evidence",
    ),
    path(
        "near-miss/<str:id>/analysis/evidence/<str:evidence_id>/photo/",
        NearMissAnalysisEvidencePhotoView.as_view(),
        name="near-miss-analysis-evidence-photo",
    ),
    path(
        "near-miss/<str:id>/analysis/facts/",
        NearMissAnalysisFactListCreateView.as_view(),
        name="near-miss-analysis-facts",
    ),
    path(
        "near-miss/<str:id>/analysis/facts/<str:fact_id>/",
        NearMissAnalysisFactDetailView.as_view(),
        name="near-miss-analysis-fact-detail",
    ),
    path(
        "incidents/position-prefill/",
        IncidentPositionPrefillView.as_view(),
        name="incident-position-prefill",
    ),
    path("corrective-actions/", CorrectiveActionListCreateView.as_view(), name="corrective-action-list"),
    path("corrective-actions/<str:id>/", CorrectiveActionDetailView.as_view(), name="corrective-action-detail"),
    path(
        "corrective-actions/<str:id>/link-pr/",
        CorrectiveActionLinkPurchaseView.as_view(),
        name="corrective-action-link-pr",
    ),
    path(
        "corrective-actions/<str:id>/transition/",
        CorrectiveActionTransitionView.as_view(),
        name="corrective-action-transition",
    ),
    path(
        "corrective-actions/<str:id>/verify/",
        CorrectiveActionPhysicalVerifyView.as_view(),
        name="corrective-action-verify",
    ),
    path("incidents/phase-1/", IncidentPhase1CreateView.as_view(), name="incident-phase-1-create"),
    path("incidents/<str:id>/", IncidentDetailView.as_view(), name="incident-detail"),
    path("incidents/<str:id>/pdf/", IncidentPDFDownloadView.as_view(), name="incident-pdf"),
    path("export/incident/<str:id>/pdf/", IncidentPDFDownloadView.as_view(), name="incident-pdf-export"),
    path("export/near-miss/<str:id>/pdf/", NearMissPDFDownloadView.as_view(), name="near-miss-pdf-export"),
    path("export/scm/<str:id>/pdf/", SCMPDFDownloadView.as_view(), name="scm-pdf-export"),
    path("export/auditor-bundle/", AuditorBundleExportView.as_view(), name="auditor-bundle-export"),
    path("export/msc-mepc-3/<str:id>/", MscMepc3ExportView.as_view(), name="msc-mepc3-export"),
    path("incidents/<str:id>/closure/", IncidentClosureView.as_view(), name="incident-closure"),
    path(
        "circular/from-incident/<str:id>/",
        IncidentCircularPublishView.as_view(),
        name="incident-circular-publish",
    ),
    path("incidents/<str:id>/phase-1/", IncidentPhase1UpdateView.as_view(), name="incident-phase-1-update"),
    path("incidents/<str:id>/phase-1/submit/", IncidentPhase1SubmitView.as_view(), name="incident-phase-1-submit"),
    path(
        "incidents/<str:id>/external-party/",
        IncidentExternalPartyInjuryView.as_view(),
        name="incident-external-party",
    ),
    path("incidents/<str:id>/phase-2/", IncidentPhase2UpdateView.as_view(), name="incident-phase-2-update"),
    path("incidents/<str:id>/phase-2/submit/", IncidentPhase2SubmitView.as_view(), name="incident-phase-2-submit"),
    path("incidents/<str:id>/draft/", IncidentDraftSaveView.as_view(), name="incident-draft-save"),
    path("incidents/<str:id>/evidence/", IncidentPhase3EvidenceView.as_view(), name="incident-phase-3-evidence"),
    path(
        "incidents/<str:id>/evidence/attachments/",
        IncidentPhase3AttachmentUploadView.as_view(),
        name="incident-phase-3-attachment-upload",
    ),
    path(
        "incidents/<str:id>/chain-of-custody/",
        IncidentPhase3ChainOfCustodyView.as_view(),
        name="incident-phase-3-chain-of-custody",
    ),
    path(
        "incidents/<str:id>/evidence-matrix/",
        IncidentPhase3EvidenceMatrixView.as_view(),
        name="incident-phase-3-evidence-matrix",
    ),
    path("incidents/<str:id>/interviews/", IncidentPhase3InterviewView.as_view(), name="incident-phase-3-interviews"),
    path(
        "incidents/<str:id>/evidence/deadline-tasks/<str:task_id>/",
        IncidentPhase3DeadlineTaskView.as_view(),
        name="incident-phase-3-deadline-task",
    ),
    path("incidents/<str:id>/facts/", IncidentPhase4FactListCreateView.as_view(), name="incident-phase-4-facts"),
    path(
        "incidents/<str:id>/facts/sources/",
        IncidentPhase4EvidenceSourceListView.as_view(),
        name="incident-phase-4-fact-sources",
    ),
    path(
        "incidents/<str:id>/facts/gate/",
        IncidentPhase4GateView.as_view(),
        name="incident-phase-4-gate",
    ),
    path(
        "incidents/<str:id>/facts/<str:fact_id>/",
        IncidentPhase4FactDetailView.as_view(),
        name="incident-phase-4-fact-detail",
    ),
    path(
        "incidents/<str:id>/facts/reorder/",
        IncidentPhase4FactReorderView.as_view(),
        name="incident-phase-4-fact-reorder",
    ),
    path(
        "incidents/<str:id>/facts/contradictions/",
        IncidentPhase4FactContradictionView.as_view(),
        name="incident-phase-4-fact-contradiction",
    ),
    path("incidents/<str:id>/analysis/", IncidentPhase5WorkspaceView.as_view(), name="incident-phase-5-workspace"),
    path("incidents/<str:id>/analysis/mscat/", IncidentMscatSearchView.as_view(), name="incident-phase-5-mscat"),
    path(
        "incidents/<str:id>/analysis/causes/",
        IncidentPhase5CauseListCreateView.as_view(),
        name="incident-phase-5-causes",
    ),
    path(
        "incidents/<str:id>/analysis/causes/<str:cause_id>/",
        IncidentPhase5CauseDetailView.as_view(),
        name="incident-phase-5-cause-detail",
    ),
    path(
        "incidents/<str:id>/analysis/safeguards/",
        IncidentPhase5SafeguardListCreateView.as_view(),
        name="incident-phase-5-safeguards",
    ),
    path(
        "incidents/<str:id>/analysis/safeguards/<str:safeguard_id>/",
        IncidentPhase5SafeguardDetailView.as_view(),
        name="incident-phase-5-safeguard-detail",
    ),
    path("incidents/<str:id>/bias-guards/", IncidentBiasGuardChecklistView.as_view(), name="incident-bias-guards"),
    path("incidents/<str:id>/override-blame/", IncidentBlameOverrideView.as_view(), name="incident-override-blame"),
    path(
        "incidents/<str:id>/phase-6/",
        IncidentPhase6WorkspaceView.as_view(),
        name="incident-phase-6-workspace",
    ),
    path(
        "incidents/<str:id>/recommendations/",
        IncidentRecommendationListCreateView.as_view(),
        name="incident-recommendations",
    ),
    path(
        "incidents/<str:id>/recommendations/<str:recommendation_id>/",
        IncidentRecommendationDetailView.as_view(),
        name="incident-recommendation-detail",
    ),
    path(
        "incidents/<str:id>/phase-7/preflight/",
        IncidentPhase7PreflightView.as_view(),
        name="incident-phase-7-preflight",
    ),
    path(
        "incidents/<str:id>/phase-7/accept/",
        IncidentPhase7AcceptView.as_view(),
        name="incident-phase-7-accept",
    ),
    path(
        "incidents/<str:id>/phase-7/hod-signature/",
        IncidentPhase7HodSignatureView.as_view(),
        name="incident-phase-7-hod-signature",
    ),
    path(
        "incidents/<str:id>/phase-7/approve-red/",
        IncidentPhase7ApproveRedView.as_view(),
        name="incident-phase-7-approve-red",
    ),
    path(
        "incidents/<str:id>/phase-7/send-back/",
        IncidentPhase7SendBackView.as_view(),
        name="incident-phase-7-send-back",
    ),
    path(
        "incidents/<str:id>/phase-8/",
        IncidentPhase8WorkspaceView.as_view(),
        name="incident-phase-8-workspace",
    ),
    path(
        "incidents/<str:id>/phase-8/verify/",
        IncidentPhase8VerifyView.as_view(),
        name="incident-phase-8-verify",
    ),
    path(
        "incidents/<str:id>/phase-8/close/",
        IncidentPhase8CloseView.as_view(),
        name="incident-phase-8-close",
    ),
    path("incidents/<str:id>/reopen/", IncidentReopenView.as_view(), name="incident-reopen"),
    path(
        "master/recommendation-themes/",
        RecommendationThemeListView.as_view(),
        name="recommendation-themes",
    ),
    path("incidents/<str:id>/link/", IncidentLinkActionView.as_view(), name="incident-link-action"),
    path("incidents/<str:id>/transition/", IncidentTransitionView.as_view(), name="incident-transition"),
    path("incidents/<str:id>/audit/", IncidentAuditView.as_view(), name="incident-audit"),
    path("incidents/<str:id>/audit/phase-log/", PhaseLogView.as_view(), name="incident-phase-log"),
    path("incidents/<str:id>/audit/field-history/", FieldHistoryView.as_view(), name="incident-field-history"),
]
