from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogSectionSeed:
    section_id: int
    section_code: str
    display_name: str
    sort_order: int


CATALOG_SECTIONS: tuple[CatalogSectionSeed, ...] = (
    CatalogSectionSeed(1, "CLASS", "Class Certificates", 1),
    CatalogSectionSeed(2, "STATUTORY", "Statutory & Flag", 2),
    CatalogSectionSeed(3, "TRADE", "Trade & Commercial", 3),
    CatalogSectionSeed(4, "EQUIPMENT", "Equipment LSA/FFA/Nav/GMDSS", 4),
    CatalogSectionSeed(5, "CALIBRATIONS", "Calibrations", 5),
    CatalogSectionSeed(6, "TESTS", "Tests & Analyses", 6),
    CatalogSectionSeed(7, "TYPE_APPROVAL", "Type Approvals", 7),
    CatalogSectionSeed(8, "APPROVED_PLANS", "Approved Plans", 8),
    CatalogSectionSeed(9, "MISC", "Other/Misc", 9),
)
