from __future__ import annotations

from dataclasses import dataclass

from apps.safety.models import EvidenceItem, Incident, IncidentEvidence


@dataclass(frozen=True)
class EvidenceCoverage:
    covered_tabs: list[str]
    missing_tabs: list[str]


def _has_meaningful_structured_data(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    for item in value.values():
        if item in (None, "", [], {}, False):
            continue
        return True
    return False


def build_incident_evidence_coverage(incident: Incident) -> EvidenceCoverage:
    tab_rows = {row.tab_code: row for row in incident.evidence_tabs.all()}
    linked_item_counts: dict[str, int] = {}
    for tab_code in incident.evidence_items.filter(
        evidence_tab__isnull=False,
    ).values_list("evidence_tab__tab_code", flat=True):
        if tab_code:
            linked_item_counts[str(tab_code)] = linked_item_counts.get(str(tab_code), 0) + 1

    interview_count = incident.witness_interviews.count()
    covered_tabs: list[str] = []
    missing_tabs: list[str] = []
    for tab_code, _ in IncidentEvidence.TabCode.choices:
        row = tab_rows.get(tab_code)
        covered = False
        if row is not None:
            covered = (
                int(row.entry_count or 0) > 0
                or bool((row.na_justification or "").strip())
                or bool((row.summary or "").strip())
                or _has_meaningful_structured_data(row.structured_data)
            )
        if linked_item_counts.get(tab_code, 0) > 0:
            covered = True
        if tab_code == IncidentEvidence.TabCode.PEOPLE and interview_count > 0:
            covered = True

        if covered:
            covered_tabs.append(tab_code)
        else:
            missing_tabs.append(tab_code)

    return EvidenceCoverage(covered_tabs=covered_tabs, missing_tabs=missing_tabs)
