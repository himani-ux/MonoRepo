"""Safety services package."""
from .alarp_gate import AlarpGate
from .attachment_replace_handler import AttachmentReplaceHandler, AttachmentReplaceResult
from .band_classifier import AdvisoryBandResult, classify_band
from .blame_detector import BlameDetector, BlameEvaluation
from .ca_aging import CorrectiveActionAgingService
from .checklist_version_resolver import ChecklistVersionResolutionError, ChecklistVersionResolver
from .crew_rotation_coverage import CrewRotationCoverageService
from .crew_rank_resolver import CrewRankResolver
from .cross_record_search import CrossRecordSearchService
from .dashboard_ca_aging import DashboardCorrectiveActionAgingService
from .dashboard_soi_compliance import DashboardSOIComplianceService
from .dashboard_export import DashboardExportResult, DashboardExportService
from .deadline_pauser import DeadlinePauser
from .evidence_deadline_scheduler import EvidenceDeadlineScheduler
from .fatigue_live_join import FatigueLiveJoinService
from .fleet_alert_issuer import FleetAlertIssueError, FleetAlertIssuer
from .field_history_recorder import capture_model_state, record_field_changes
from .finding_closure import FindingClosureService
from .fts_engine import FtsSearchHit, FtsUnavailableError, SafetyFtsEngine
from .high_severity_nudge import HighSeverityNudgeResult, HighSeverityNudgeService
from .heinrich_ratio import HeinrichRatioService
from .incident_linker import DuplicateCandidate, IncidentLinkError, IncidentLinker
from .incident_circular_publisher import CircularPublishResult, IncidentCircularPublisher
from .incident_reopen import IncidentReopenService
from .life_threat_detector import LifeThreatDetector, LifeThreatScanResult
from .mscat_search import MscatSearchService
from .mscmepc3_position_fetcher import Mscmepc3PositionFetcher
from .nm_rate_limiter import NearMissRateLimiter
from .near_miss_supersede import NearMissSupersedeError, NearMissSupersedeService
from .notification_writer import NotificationDispatchResult, NotificationWriter
from .pareto_screener import ParetoScreenerService
from .phase_state_machine import PhaseStateMachine
from .pic_retention import PicRetentionService
from .purchase_fk_enforcer import PurchaseFKEnforcer, PurchaseFKEnforcerError
from .purchase_req_guard import PurchaseRequisitionGuard, PurchaseRequisitionGuardError
from .repeat_finding_detector import RepeatFindingDetector, RepeatFindingResult
from .repeat_root_radar import RepeatRootRadarService
from .section12_cycle_enforcer import Section12CycleEnforcer
from .self_report_guard import SelfReportConflictResult, check_self_report_conflict
from .signature_chain import SignatureChainService
from .soi_compliance_calculator import SOI_COMPLIANCE_LABEL, SOIComplianceCalculator
from .unique_id_allocator import UniqueIdAllocator


_LAZY_EXPORT_MODULES = {
    "IncidentPdfRenderResult": "pdf_renderer",
    "IncidentPdfRenderer": "pdf_renderer",
    "MscMepc3Circ4PdfRenderer": "pdf_renderer",
    "MscMepc3PdfRenderResult": "pdf_renderer",
    "NearMissLightweightPdfRenderer": "pdf_renderer",
    "NearMissPdfRenderResult": "pdf_renderer",
    "SCMLegacyPdfRenderer": "pdf_renderer",
    "SCMPdfRenderResult": "pdf_renderer",
    "SOISummaryPdfRenderResult": "pdf_renderer",
    "SOISummaryPdfRenderer": "pdf_renderer",
    "SOIChecklistGenerator": "soi_checklist_generator",
    "SOIChecklistRenderResult": "soi_checklist_generator",
    "SOICloseService": "soi_close_service",
}


def __getattr__(name: str):
    module_name = _LAZY_EXPORT_MODULES.get(name)
    if module_name is not None:
        from importlib import import_module

        module = import_module(f"{__name__}.{module_name}")
        return getattr(module, name)
    raise AttributeError(name)

__all__ = [
    "AdvisoryBandResult",
    "AlarpGate",
    "AttachmentReplaceHandler",
    "AttachmentReplaceResult",
    "BlameDetector",
    "BlameEvaluation",
    "ChecklistVersionResolutionError",
    "ChecklistVersionResolver",
    "CircularPublishResult",
    "CorrectiveActionAgingService",
    "CrewRotationCoverageService",
    "CrewRankResolver",
    "CrossRecordSearchService",
    "DashboardCorrectiveActionAgingService",
    "DashboardExportResult",
    "DashboardExportService",
    "DashboardSOIComplianceService",
    "DeadlinePauser",
    "DuplicateCandidate",
    "EvidenceDeadlineScheduler",
    "FatigueLiveJoinService",
    "FleetAlertIssueError",
    "FleetAlertIssuer",
    "FindingClosureService",
    "FtsSearchHit",
    "FtsUnavailableError",
    "HeinrichRatioService",
    "HighSeverityNudgeResult",
    "HighSeverityNudgeService",
    "IncidentCircularPublisher",
    "IncidentLinkError",
    "IncidentLinker",
    "IncidentPdfRenderResult",
    "IncidentPdfRenderer",
    "IncidentReopenService",
    "LifeThreatDetector",
    "LifeThreatScanResult",
    "MscatSearchService",
    "Mscmepc3PositionFetcher",
    "NearMissRateLimiter",
    "NearMissSupersedeError",
    "NearMissSupersedeService",
    "NotificationDispatchResult",
    "classify_band",
    "capture_model_state",
    "MscMepc3Circ4PdfRenderer",
    "MscMepc3PdfRenderResult",
    "NearMissLightweightPdfRenderer",
    "NearMissPdfRenderResult",
    "NotificationWriter",
    "ParetoScreenerService",
    "PicRetentionService",
    "PurchaseFKEnforcer",
    "PurchaseFKEnforcerError",
    "PurchaseRequisitionGuard",
    "PurchaseRequisitionGuardError",
    "RepeatFindingDetector",
    "RepeatFindingResult",
    "RepeatRootRadarService",
    "SCMLegacyPdfRenderer",
    "SCMPdfRenderResult",
    "SOISummaryPdfRenderResult",
    "SOISummaryPdfRenderer",
    "SafetyFtsEngine",
    "Section12CycleEnforcer",
    "record_field_changes",
    "PhaseStateMachine",
    "SignatureChainService",
    "SOI_COMPLIANCE_LABEL",
    "SOIChecklistGenerator",
    "SOIComplianceCalculator",
    "SOIChecklistRenderResult",
    "SOICloseService",
    "SelfReportConflictResult",
    "UniqueIdAllocator",
    "check_self_report_conflict",
]
