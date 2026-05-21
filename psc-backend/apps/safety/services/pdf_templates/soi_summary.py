from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class SOISummaryAreaRow:
    area_name: str
    area_id: int
    last_inspected_at: str | None
    status: str


@dataclass(frozen=True)
class SOISummaryFindingRow:
    title: str
    severity: str
    mscat_code: str
    shell_tag: str
    priority: str
    assignee: str
    status: str


@dataclass(frozen=True)
class SOISummaryTraineeRow:
    crew_id: str
    trainee_slot: int


@dataclass(frozen=True)
class SOISummarySignatureRow:
    label: str
    status: str
    signed_by: str | None = None
    signed_at: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class SOISummaryPdfContext:
    inspection_id: int
    inspection_reference: str
    vessel_id: str
    cycle_label: str
    state: str
    planned_date: str
    reported_at: str | None
    closed_at: str | None
    checklist_unique_id: str
    generated_at: str
    scm_feed_indicator: str
    paper_reference_note: str
    audit_footer: str
    area_rows: list[SOISummaryAreaRow] = field(default_factory=list)
    finding_rows: list[SOISummaryFindingRow] = field(default_factory=list)
    trainee_rows: list[SOISummaryTraineeRow] = field(default_factory=list)
    signature_rows: list[SOISummarySignatureRow] = field(default_factory=list)


class SOISummaryTemplate:
    SECTION_TITLES = [
        "Stamped Areas",
        "Findings",
        "Trainees",
        "Signatures",
    ]

    def __init__(self) -> None:
        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "SafetySoiPdfTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceAfter=8,
            textColor=colors.HexColor("#0F172A"),
        )
        self.section_style = ParagraphStyle(
            "SafetySoiPdfSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            spaceAfter=6,
            textColor=colors.HexColor("#0F172A"),
        )
        self.body_style = ParagraphStyle(
            "SafetySoiPdfBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            spaceAfter=4,
            textColor=colors.HexColor("#1F2937"),
        )
        self.meta_style = ParagraphStyle(
            "SafetySoiPdfMeta",
            parent=self.body_style,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
        )
        self.footer_style = ParagraphStyle(
            "SafetySoiPdfFooter",
            parent=self.meta_style,
            fontName="Helvetica-Oblique",
            spaceBefore=8,
        )

    def render(self, context: SOISummaryPdfContext) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=context.inspection_reference,
            author="Safety Module",
        )

        story: list[object] = [
            Paragraph("SOI Summary PDF", self.title_style),
            Paragraph(
                "Step 6.5 post-submission summary record for FEAT-SAF-PDF-005. This export lists stamped areas, findings, trainees, and signatures without reproducing the per-item paper checklist answers.",
                self.body_style,
            ),
            Spacer(1, 6),
            self._build_cover_table(context),
            Spacer(1, 8),
            Paragraph(context.paper_reference_note, self.meta_style),
            Spacer(1, 10),
            Paragraph(self.SECTION_TITLES[0], self.section_style),
            self._build_area_table(context.area_rows),
            Spacer(1, 10),
            Paragraph(self.SECTION_TITLES[1], self.section_style),
            self._build_finding_table(context.finding_rows),
            Spacer(1, 10),
            Paragraph(self.SECTION_TITLES[2], self.section_style),
            self._build_trainee_table(context.trainee_rows),
            Spacer(1, 10),
            Paragraph(self.SECTION_TITLES[3], self.section_style),
            self._build_signature_table(context.signature_rows),
            Spacer(1, 8),
            Paragraph(context.audit_footer, self.footer_style),
        ]

        document.build(story)
        return buffer.getvalue()

    def _build_cover_table(self, context: SOISummaryPdfContext) -> Table:
        table = Table(
            [
                ["Inspection ref", context.inspection_reference],
                ["Vessel", context.vessel_id],
                ["Cycle", context.cycle_label],
                ["State", context.state],
                ["Planned date", context.planned_date],
                ["Reported at", context.reported_at or "Not recorded"],
                ["Closed at", context.closed_at or "Awaiting Master closure"],
                ["Checklist unique ID", context.checklist_unique_id],
                ["SCM feed", context.scm_feed_indicator],
                ["Generated at", context.generated_at],
            ],
            colWidths=[42 * mm, 130 * mm],
            hAlign="LEFT",
        )
        table.setStyle(self._table_style())
        return table

    def _build_area_table(self, rows: list[SOISummaryAreaRow]) -> Table:
        table_rows = [
            ["Area", "Name", "Last inspected", "Status"],
            *[
                [
                    str(row.area_id),
                    row.area_name,
                    row.last_inspected_at or "Not stamped",
                    row.status,
                ]
                for row in rows
            ],
        ]
        table = Table(table_rows, repeatRows=1, hAlign="LEFT")
        table.setStyle(self._table_style(header=True))
        return table

    def _build_finding_table(self, rows: list[SOISummaryFindingRow]) -> Table:
        effective_rows = rows or [
            SOISummaryFindingRow(
                title="No findings recorded",
                severity="-",
                mscat_code="-",
                shell_tag="-",
                priority="-",
                assignee="-",
                status="No deviations were logged for this submission.",
            )
        ]
        table_rows = [
            ["Title", "Severity", "M-SCAT", "SHELL", "Priority", "Assignee", "Status"],
            *[
                [
                    row.title,
                    row.severity,
                    row.mscat_code,
                    row.shell_tag,
                    row.priority,
                    row.assignee,
                    row.status,
                ]
                for row in effective_rows
            ],
        ]
        table = Table(table_rows, repeatRows=1, hAlign="LEFT")
        table.setStyle(self._table_style(header=True))
        return table

    def _build_trainee_table(self, rows: list[SOISummaryTraineeRow]) -> Table:
        table_rows = [["Slot", "Crew ID"]]
        if rows:
            table_rows.extend([[str(row.trainee_slot), row.crew_id] for row in rows])
        else:
            table_rows.append(["-", "No trainees recorded for this inspection."])
        table = Table(table_rows, repeatRows=1, hAlign="LEFT", colWidths=[20 * mm, 152 * mm])
        table.setStyle(self._table_style(header=True))
        return table

    def _build_signature_table(self, rows: list[SOISummarySignatureRow]) -> Table:
        table_rows = [
            ["Role", "Status", "Signed by", "Signed at", "Note"],
            *[
                [
                    row.label,
                    row.status,
                    row.signed_by or "-",
                    row.signed_at or "-",
                    row.note or "-",
                ]
                for row in rows
            ],
        ]
        table = Table(table_rows, repeatRows=1, hAlign="LEFT")
        table.setStyle(self._table_style(header=True))
        return table

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
