from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class IncidentPdfSignatureRow:
    label: str
    signed_at: str | None = None
    signed_by: str | None = None
    typed_name: str | None = None


@dataclass(frozen=True)
class IncidentPdfContext:
    incident_id: int
    incident_number: str
    vessel_id: str
    current_phase: int
    risk_band: str | None
    imo_classifier: str | None
    occurred_at: str | None
    reported_at: str | None
    narrative: str
    generated_at: str
    cover_band_hex: str
    investigator_rows: list[tuple[str, str]]
    evidence_rows: list[tuple[str, str, str]]
    cause_rows: list[tuple[str, str, str]]
    causal_factor_points: list[str]
    action_rows: list[tuple[str, str, str]]
    lessons_text: str
    notification_rows: list[tuple[str, str, str]]
    signature_rows: list[IncidentPdfSignatureRow]
    appendix_rows: list[tuple[str, str, str]]
    section_titles: list[str] = field(default_factory=list)


class IncidentTenSectionTemplate:
    SECTION_TITLES = [
        "1. Cover + Classification",
        "2. Investigator / Team Credentials",
        "3. Evidence Collected",
        "4. Root-Cause Analysis",
        "5. Causal-Factor Enumeration",
        "6. Actions + Timeline",
        "7. Lessons Learnt Narrative",
        "8. Fleet Notification Plan",
        "9. Signatures",
        "10. Appendices",
    ]

    def __init__(self) -> None:
        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "SafetyPdfTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceAfter=8,
            textColor=colors.HexColor("#0F172A"),
        )
        self.section_style = ParagraphStyle(
            "SafetyPdfSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            spaceAfter=6,
            textColor=colors.HexColor("#0F172A"),
        )
        self.body_style = ParagraphStyle(
            "SafetyPdfBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            spaceAfter=4,
            textColor=colors.HexColor("#1F2937"),
        )

    def render(self, context: IncidentPdfContext) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=context.incident_number,
            author="Safety Module",
        )
        story = []

        story.extend(self._build_cover(context))
        story.extend(self._build_table_section(context.section_titles[1], ["Role", "Recorded detail"], context.investigator_rows))
        story.extend(self._build_table_section(context.section_titles[2], ["Source", "Summary", "Cross-reference"], context.evidence_rows))
        story.extend(self._build_table_section(context.section_titles[3], ["Layer", "Code", "Rationale"], context.cause_rows))
        story.extend(self._build_list_section(context.section_titles[4], context.causal_factor_points))
        story.extend(self._build_table_section(context.section_titles[5], ["Tier", "Action", "Timeline / status"], context.action_rows))
        story.extend(self._build_narrative_section(context.section_titles[6], context.lessons_text))
        story.extend(self._build_table_section(context.section_titles[7], ["Audience", "Status", "Timestamp"], context.notification_rows))
        story.extend(self._build_signature_section(context))
        story.extend(self._build_table_section(context.section_titles[9], ["Appendix", "Type", "Detail"], context.appendix_rows))

        document.build(story)
        return buffer.getvalue()

    def _build_cover(self, context: IncidentPdfContext) -> list[object]:
        cover_band = Table([[""]], colWidths=[170 * mm], rowHeights=[15 * mm])
        cover_band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor(context.cover_band_hex))]))
        summary_table = Table(
            [
                ["Incident number", context.incident_number],
                ["Vessel", context.vessel_id],
                ["Current phase", str(context.current_phase)],
                ["Risk band", context.risk_band or "Unassigned"],
                ["IMO classifier", context.imo_classifier or "Not assigned"],
                ["Occurred at", context.occurred_at or "Not recorded"],
                ["Reported at", context.reported_at or "Not recorded"],
                ["Generated at", context.generated_at],
            ],
            colWidths=[42 * mm, 128 * mm],
            hAlign="LEFT",
        )
        summary_table.setStyle(self._table_style())
        return [
            cover_band,
            Spacer(1, 10),
            Paragraph(self.SECTION_TITLES[0], self.section_style),
            Paragraph("Formal Incident Report", self.title_style),
            Paragraph(
                "This export follows the Step 6.1 internal 10-section contract for Safety incident filing and management review.",
                self.body_style,
            ),
            Spacer(1, 4),
            summary_table,
            Spacer(1, 12),
        ]

    def _build_table_section(self, title: str, headers: list[str], rows: list[tuple[str, ...]]) -> list[object]:
        sample_row = tuple("" for _ in headers)
        body_rows = rows or [("No data recorded.", *sample_row[1:])]
        table = Table([headers, *body_rows], repeatRows=1, hAlign="LEFT")
        table.setStyle(self._table_style(header=True))
        return [Paragraph(title, self.section_style), table, Spacer(1, 10)]

    def _build_list_section(self, title: str, points: list[str]) -> list[object]:
        items = [ListItem(Paragraph(point, self.body_style)) for point in (points or ["No causal factors recorded."])]
        return [Paragraph(title, self.section_style), ListFlowable(items, bulletType="1"), Spacer(1, 10)]

    def _build_narrative_section(self, title: str, text: str) -> list[object]:
        return [Paragraph(title, self.section_style), Paragraph(text, self.body_style), Spacer(1, 10)]

    def _build_signature_section(self, context: IncidentPdfContext) -> list[object]:
        rows = [
            (
                row.label,
                row.signed_by or "Awaiting signature",
                row.signed_at or "Awaiting signature",
                row.typed_name or "Awaiting signature",
            )
            for row in context.signature_rows
        ]
        table = Table([["Role", "Signed by", "Signed at", "Typed name"], *rows], repeatRows=1, hAlign="LEFT")
        table.setStyle(self._table_style(header=True))
        return [Paragraph(context.section_titles[8], self.section_style), table, Spacer(1, 10)]

    @staticmethod
    def _table_style(*, header: bool = False) -> TableStyle:
        commands = [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEADING", (0, 0), (-1, -1), 12),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        if header:
            commands.extend(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        return TableStyle(commands)
