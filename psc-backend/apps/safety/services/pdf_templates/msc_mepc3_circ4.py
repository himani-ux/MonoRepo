from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class MscMepc3Circ4PdfContext:
    incident_id: int
    incident_number: str
    generated_at: str
    appendix_titles: list[str] = field(default_factory=list)
    appendix1_rows: list[tuple[str, str]] = field(default_factory=list)
    appendix2_rows: list[tuple[str, str]] = field(default_factory=list)
    appendix3_rows: list[tuple[str, str]] = field(default_factory=list)
    appendix4_rows: list[tuple[str, str]] = field(default_factory=list)
    appendix5_rows: list[tuple[str, str, str]] = field(default_factory=list)


class MscMepc3Circ4Template:
    APPENDIX_TITLES = [
        "Appendix 1. Generic Information",
        "Appendix 2. Ship Particulars",
        "Appendix 3. Casualty Analysis",
        "Appendix 4. Supplementary Conditions",
        "Appendix 5. Standardized Field Values",
    ]

    def __init__(self) -> None:
        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "SafetyMscMepcTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceAfter=8,
            textColor=colors.HexColor("#0F172A"),
        )
        self.section_style = ParagraphStyle(
            "SafetyMscMepcSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            spaceAfter=6,
            textColor=colors.HexColor("#0F172A"),
        )
        self.body_style = ParagraphStyle(
            "SafetyMscMepcBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            spaceAfter=4,
            textColor=colors.HexColor("#1F2937"),
        )

    def render(self, context: MscMepc3Circ4PdfContext) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            title=f"{context.incident_number} MSC-MEPC.3/Circ.4",
            author="Safety Module",
        )
        story = [
            Paragraph("MSC-MEPC.3/Circ.4 Regulatory Export", self.title_style),
            Paragraph(
                (
                    "Secondary regulatory export for flag-state casualty reporting. "
                    "This handover template preserves the five-appendix structure "
                    "required by Step 6.2."
                ),
                self.body_style,
            ),
            Spacer(1, 4),
            self._build_two_column_table(
                [
                    ("Incident number", context.incident_number),
                    ("Generated at", context.generated_at),
                    ("Appendix count", str(len(context.appendix_titles))),
                ]
            ),
            Spacer(1, 12),
        ]

        story.extend(self._build_appendix_two_column(context.appendix_titles[0], context.appendix1_rows))
        story.extend(self._build_appendix_two_column(context.appendix_titles[1], context.appendix2_rows))
        story.extend(self._build_appendix_two_column(context.appendix_titles[2], context.appendix3_rows))
        story.extend(self._build_appendix_two_column(context.appendix_titles[3], context.appendix4_rows))
        story.extend(self._build_appendix_three_column(context.appendix_titles[4], context.appendix5_rows))

        document.build(story)
        return buffer.getvalue()

    def _build_appendix_two_column(self, title: str, rows: list[tuple[str, str]]) -> list[object]:
        return [
            Paragraph(title, self.section_style),
            self._build_two_column_table(rows),
            Spacer(1, 10),
        ]

    def _build_appendix_three_column(self, title: str, rows: list[tuple[str, str, str]]) -> list[object]:
        data = [("Field", "Value", "Source")]
        data.extend(rows or [("No data recorded.", "Manual completion required.", "workspace seam")])
        table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=[52 * mm, 68 * mm, 50 * mm])
        table.setStyle(self._table_style(header=True))
        return [Paragraph(title, self.section_style), table, Spacer(1, 10)]

    def _build_two_column_table(self, rows: list[tuple[str, str]]) -> Table:
        data = [("Field", "Value")]
        data.extend(rows or [("No data recorded.", "Manual completion required.")])
        table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=[58 * mm, 112 * mm])
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
