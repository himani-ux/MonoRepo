from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class NearMissPdfSignatureRow:
    label: str
    signed_at: str | None = None
    signed_by: str | None = None
    typed_name: str | None = None


@dataclass(frozen=True)
class NearMissCauseFactorPdfRow:
    factor: str
    immediate_cause: str
    root_cause: str


@dataclass(frozen=True)
class NearMissLightweightPdfContext:
    incident_id: int
    incident_number: str
    vessel_id: str
    state: str
    priority: str
    severity: str
    place: str
    categories: str
    near_miss_types: str
    possible_loss_type: str
    cause_factor_rows: list[NearMissCauseFactorPdfRow]
    occurred_at: str | None
    reported_at: str | None
    reporter_name: str
    reporter_rank: str
    what_happened: str
    suggestion_text: str
    immediate_action_text: str
    root_cause_detail: str
    corrective_action: str
    weather_voyage_details: str
    equipment_details: str
    lessons_learned: str
    vessel_review_comment: str
    office_comments: str
    closure_reason: str
    fleet_alert_issued_at: str | None
    fleet_learning_text: str
    generated_at: str
    visibility_note: str
    signature_rows: list[NearMissPdfSignatureRow] = field(default_factory=list)


class NearMissLightweightTemplate:
    SECTION_TITLES = [
        "Summary",
        "What Happened",
        "Preventive Measures",
        "Immediate Action",
        "High-risk and Learning Details",
        "Review Comments",
        "Fleet Learning",
        "Closure",
        "Signatures",
    ]

    def __init__(self) -> None:
        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "SafetyNearMissPdfTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceAfter=8,
            textColor=colors.HexColor("#0F172A"),
        )
        self.section_style = ParagraphStyle(
            "SafetyNearMissPdfSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            spaceAfter=6,
            textColor=colors.HexColor("#0F172A"),
        )
        self.body_style = ParagraphStyle(
            "SafetyNearMissPdfBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            spaceAfter=4,
            textColor=colors.HexColor("#1F2937"),
        )
        self.meta_style = ParagraphStyle(
            "SafetyNearMissPdfMeta",
            parent=self.body_style,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
        )

    def render(self, context: NearMissLightweightPdfContext) -> bytes:
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

        summary_rows = self._non_empty_detail_rows(
            [
                ("Near miss ref", context.incident_number),
                ("Vessel", context.vessel_id),
                ("State", context.state),
                ("Priority", context.priority),
                ("Severity", context.severity),
                ("Place", context.place),
                ("Category", context.categories),
                ("Near-miss type", context.near_miss_types),
                ("Possible loss type", context.possible_loss_type),
                ("Occurred at", context.occurred_at),
                ("Reported at", context.reported_at),
                ("Reported by", context.reporter_name),
                ("Reporter's rank", context.reporter_rank),
                ("Fleet alert issued", context.fleet_alert_issued_at),
            ]
        )
        summary_table = Table(
            summary_rows,
            colWidths=[42 * mm, 128 * mm],
            hAlign="LEFT",
        )
        summary_table.setStyle(self._table_style())

        story = [
            Paragraph("Near Miss Report", self.title_style),
            Spacer(1, 6),
            Paragraph(self.SECTION_TITLES[0], self.section_style),
            summary_table,
            Spacer(1, 6),
            *self._visibility_note_block(context.visibility_note),
        ]
        if context.cause_factor_rows:
            story.extend(
                [
                    Paragraph("Cause Factors", self.section_style),
                    self._cause_factors_table(context),
                    Spacer(1, 8),
                ]
            )
        story.extend(self._paragraph_section(self.SECTION_TITLES[1], context.what_happened))
        story.extend(self._paragraph_section(self.SECTION_TITLES[2], context.suggestion_text))
        story.extend(self._paragraph_section(self.SECTION_TITLES[3], context.immediate_action_text))
        high_risk_rows = self._non_empty_detail_rows(
            [
                ("Root cause detail", context.root_cause_detail),
                ("Corrective action", context.corrective_action),
                ("Weather / voyage details", context.weather_voyage_details),
                ("Equipment details", context.equipment_details),
                ("Lessons learned", context.lessons_learned),
            ]
        )
        if high_risk_rows:
            story.extend(
                [
                    Paragraph(self.SECTION_TITLES[4], self.section_style),
                    self._details_table(high_risk_rows),
                    Spacer(1, 8),
                ]
            )

        review_rows = self._non_empty_detail_rows(
            [
                ("Vessel review comment", context.vessel_review_comment),
                ("Office comments", context.office_comments),
            ]
        )
        if review_rows:
            story.extend(
                [
                    Paragraph(self.SECTION_TITLES[5], self.section_style),
                    self._details_table(review_rows),
                    Spacer(1, 8),
                ]
            )
        story.extend(self._paragraph_section(self.SECTION_TITLES[6], context.fleet_learning_text))
        story.extend(self._paragraph_section(self.SECTION_TITLES[7], context.closure_reason))
        story.extend(self._build_signature_section(context.signature_rows))

        document.build(story)
        return buffer.getvalue()

    def _build_signature_section(self, rows: list[NearMissPdfSignatureRow]) -> list[object]:
        if not rows:
            return []
        signature_rows = [
            (
                row.label,
                row.signed_by or "Awaiting signature",
                row.signed_at or "Awaiting signature",
                row.typed_name or "Awaiting signature",
            )
            for row in (rows or [NearMissPdfSignatureRow(label="Signature")])
        ]
        table = Table(
            [["Role", "Signed by", "Signed at", "Typed name"], *signature_rows],
            repeatRows=1,
            hAlign="LEFT",
        )
        table.setStyle(self._table_style(header=True))
        return [Paragraph(self.SECTION_TITLES[8], self.section_style), table, Spacer(1, 10)]

    def _cause_factors_table(self, context: NearMissLightweightPdfContext) -> Table:
        if context.cause_factor_rows:
            rows = [
                [
                    Paragraph(row.factor, self.body_style),
                    Paragraph(row.immediate_cause or "Not selected", self.body_style),
                    Paragraph(row.root_cause or "Not selected", self.body_style),
                ]
                for row in context.cause_factor_rows
            ]
        else:
            rows = [[Paragraph("Not selected", self.body_style), Paragraph("", self.body_style), Paragraph("", self.body_style)]]

        table = Table(
            [
                ["Factor", "Immediate Cause", "Root Cause"],
                *rows,
            ],
            colWidths=[34 * mm, 68 * mm, 68 * mm],
            repeatRows=1,
            hAlign="LEFT",
        )
        table.setStyle(self._table_style(header=True))
        return table

    def _visibility_note_block(self, visibility_note: str) -> list[object]:
        if not visibility_note.strip():
            return [Spacer(1, 12)]
        return [Paragraph(visibility_note, self.meta_style), Spacer(1, 12)]

    def _details_table(self, rows: list[tuple[str, str]]) -> Table:
        table = Table(
            [[label, value] for label, value in rows],
            colWidths=[46 * mm, 124 * mm],
            hAlign="LEFT",
        )
        table.setStyle(self._table_style())
        return table

    @staticmethod
    def _non_empty_detail_rows(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
        empty_values = {
            "",
            "not applicable",
            "not issued",
            "not recorded",
            "not recorded.",
            "not required",
            "not selected",
            "unset",
            "closure reason is not recorded.",
            "fleet learning / lessons are not recorded.",
            "narrative not recorded.",
            "no immediate action is recorded.",
        }
        return [
            (label, value)
            for label, value in rows
            if str(value or "").strip().lower() not in empty_values
        ]

    def _paragraph_section(self, title: str, value: str) -> list[object]:
        if not self._non_empty_detail_rows([(title, value)]):
            return []
        return [Paragraph(title, self.section_style), Paragraph(value, self.body_style), Spacer(1, 8)]

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
