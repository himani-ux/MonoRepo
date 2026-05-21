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
class NearMissLightweightPdfContext:
    incident_id: int
    incident_number: str
    vessel_id: str
    state: str
    priority: str
    severity: str
    occurred_at: str | None
    reported_at: str | None
    reporter_name: str
    reporter_rank: str
    what_happened: str
    suggestion_text: str
    immediate_action_text: str
    closure_reason: str
    fleet_alert_due_by: str | None
    fleet_alert_issued_at: str | None
    fleet_alert_status: str
    fleet_learning_text: str
    generated_at: str
    visibility_note: str
    signature_rows: list[NearMissPdfSignatureRow] = field(default_factory=list)


class NearMissLightweightTemplate:
    SECTION_TITLES = [
        "What Happened",
        "Preventive Measures",
        "Immediate Action",
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

        summary_table = Table(
            [
                ["Near miss ref", context.incident_number],
                ["Vessel", context.vessel_id],
                ["State", context.state],
                ["Priority", context.priority],
                ["Severity", context.severity],
                ["Occurred at", context.occurred_at or "Not recorded"],
                ["Reported at", context.reported_at or "Not recorded"],
                ["Reporter", context.reporter_name],
                ["Reporter rank", context.reporter_rank],
                ["Fleet alert SLA", context.fleet_alert_status],
                ["Fleet alert due", context.fleet_alert_due_by or "Not applicable"],
                ["Fleet alert issued", context.fleet_alert_issued_at or "Not issued"],
                ["Generated at", context.generated_at],
            ],
            colWidths=[42 * mm, 128 * mm],
            hAlign="LEFT",
        )
        summary_table.setStyle(self._table_style())

        story = [
            Paragraph("Near Miss Lightweight PDF", self.title_style),
            Paragraph(
                "Step 6.3 export surface for FEAT-SAF-PDF-003. This lightweight template intentionally excludes investigation and deep causal-analysis sections.",
                self.body_style,
            ),
            Spacer(1, 6),
            summary_table,
            Spacer(1, 6),
            Paragraph(context.visibility_note, self.meta_style),
            Spacer(1, 12),
            Paragraph(self.SECTION_TITLES[0], self.section_style),
            Paragraph(context.what_happened, self.body_style),
            Spacer(1, 8),
            Paragraph(self.SECTION_TITLES[1], self.section_style),
            Paragraph(context.suggestion_text, self.body_style),
            Spacer(1, 8),
            Paragraph(self.SECTION_TITLES[2], self.section_style),
            Paragraph(context.immediate_action_text, self.body_style),
            Spacer(1, 8),
            Paragraph(self.SECTION_TITLES[3], self.section_style),
            Paragraph(context.fleet_learning_text, self.body_style),
            Spacer(1, 8),
            Paragraph(self.SECTION_TITLES[4], self.section_style),
            Paragraph(context.closure_reason, self.body_style),
            Spacer(1, 8),
        ]
        story.extend(self._build_signature_section(context.signature_rows))

        document.build(story)
        return buffer.getvalue()

    def _build_signature_section(self, rows: list[NearMissPdfSignatureRow]) -> list[object]:
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
        return [Paragraph(self.SECTION_TITLES[5], self.section_style), table, Spacer(1, 10)]

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
