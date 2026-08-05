from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from io import BytesIO
from textwrap import wrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class IncidentPdfSignatureRow:
    label: str
    signed_at: str | None = None
    signed_by: str | None = None
    typed_name: str | None = None
    source_detail: str | None = None
    device_fingerprint: str | None = None


@dataclass(frozen=True)
class IncidentPdfDetailBlock:
    heading: str
    rows: list[tuple[str, str]]


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
    report_title: str = "Incident Report"
    section_titles: list[str] = field(default_factory=list)
    classification_rows: list[tuple[str, str]] = field(default_factory=list)
    summary_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    investigator_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    evidence_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    reporter_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    injury_detail_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    estimated_cost_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    cause_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    factor_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    action_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    lesson_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    closure_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    notification_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    appendix_blocks: list[IncidentPdfDetailBlock] = field(default_factory=list)
    included_section_keys: list[str] = field(default_factory=list)


class IncidentTenSectionTemplate:
    SECTION_LABELS = {
        "summary": "Summary",
        "reporter_details": "Reporter Details",
        "injury_details": "Injury Details",
        "root_cause": "Root Cause Analysis",
        "corrective_preventive_actions": "Corrective and Preventive Actions",
        "evidence_documents": "Evidence (Documents)",
        "lessons_learned": "Lessons Learned",
        "signature": "Signature",
        "estimated_cost": "Estimated Cost",
    }
    SECTION_TITLES = [
        "1. Incident Summary",
        "2. Reporter and Office Review",
        "3. Root Cause Analysis",
        "4. Corrective and Preventive Actions",
        "5. Evidence and Attachments",
        "6. Supporting Cause Notes",
        "7. Lessons Learned",
        "8. Signatures",
    ]

    def __init__(self) -> None:
        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "SafetyPdfTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
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
            keepWithNext=True,
            textColor=colors.HexColor("#0F172A"),
        )
        self.body_style = ParagraphStyle(
            "SafetyPdfBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            spaceAfter=4,
            wordWrap="CJK",
            textColor=colors.HexColor("#1F2937"),
        )
        self.block_heading_style = ParagraphStyle(
            "SafetyPdfBlockHeading",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            spaceBefore=4,
            spaceAfter=3,
            keepWithNext=True,
            textColor=colors.HexColor("#334155"),
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
            title=context.report_title,
            author="Safety Module",
        )
        story = []

        story.append(Paragraph(self._safe(context.report_title), self.title_style))
        if self._includes(context, "summary"):
            story.extend(self._build_cover(context))
        if self._includes(context, "reporter_details"):
            story.extend(self._build_detail_blocks_section(self.SECTION_LABELS["reporter_details"], context.reporter_blocks))
            if self._is_injury_report(context) and self._includes(context, "summary"):
                story.extend(self._build_incident_narrative_block(context))
        if self._includes(context, "injury_details"):
            story.extend(self._build_detail_blocks_section(self.SECTION_LABELS["injury_details"], context.injury_detail_blocks))
        if self._includes(context, "summary") and not (
            self._is_injury_report(context) and self._includes(context, "reporter_details")
        ):
            story.extend(self._build_incident_narrative_block(context))
        if self._includes(context, "root_cause"):
            story.extend(self._build_detail_blocks_section(self.SECTION_LABELS["root_cause"], context.cause_blocks))
        if self._includes(context, "corrective_preventive_actions"):
            story.extend(self._build_detail_blocks_section(self.SECTION_LABELS["corrective_preventive_actions"], context.action_blocks))
        if self._includes(context, "evidence_documents"):
            story.extend(self._build_detail_blocks_section(self.SECTION_LABELS["evidence_documents"], context.evidence_blocks))
        if self._includes(context, "lessons_learned"):
            story.extend(self._build_lesson_section(context))
        if self._includes(context, "signature"):
            story.extend(self._build_detail_blocks_section("Closure", context.closure_blocks))
        if self._includes(context, "signature"):
            story.extend(self._build_signature_section(context))
        if self._includes(context, "estimated_cost"):
            if len(story) > 1:
                story.append(PageBreak())
            story.extend(self._build_detail_blocks_section(self.SECTION_LABELS["estimated_cost"], context.estimated_cost_blocks))

        document.build(story)
        return buffer.getvalue()

    def _build_cover(self, context: IncidentPdfContext) -> list[object]:
        summary_rows = context.classification_rows or [
            ("Incident number", context.incident_number),
            ("Vessel", context.vessel_id),
            ("Current phase", str(context.current_phase)),
            ("Risk band", context.risk_band or "Unassigned"),
            ("Occurred at", context.occurred_at or "Not recorded"),
            ("Reported at", context.reported_at or "Not recorded"),
            ("Generated at", context.generated_at),
        ]
        summary_table = Table(
            self._paired_summary_rows(summary_rows),
            colWidths=[34 * mm, 51 * mm, 34 * mm, 51 * mm],
            hAlign="LEFT",
        )
        summary_table.setStyle(self._table_style())
        story = [
            Paragraph(self.SECTION_LABELS["summary"], self.section_style),
            Paragraph(
                "This report summarizes the incident details, root cause, evidence, actions, lessons, and signatures for Safety recordkeeping.",
                self.body_style,
            ),
            summary_table,
            Spacer(1, 12),
        ]
        story.extend(self._build_detail_blocks(context.summary_blocks))
        return story

    def _build_incident_narrative_block(self, context: IncidentPdfContext) -> list[object]:
        table = Table(
            [[self._cell("Describe What happened?"), self._paragraph_html(self._format_value(context.narrative or "Incident details not recorded."))]],
            colWidths=[42 * mm, 128 * mm],
            hAlign="LEFT",
        )
        table.setStyle(self._table_style())
        return [table, Spacer(1, 10)]

    @staticmethod
    def _is_injury_report(context: IncidentPdfContext) -> bool:
        return str(context.report_title or "").strip().lower() == "injury report"

    def _build_table_section(self, title: str, headers: list[str], rows: list[tuple[str, ...]]) -> list[object]:
        sample_row = tuple("" for _ in headers)
        body_rows = rows or [("No data recorded.", *sample_row[1:])]
        table = Table(
            [[self._cell(value) for value in row] for row in [headers, *body_rows]],
            repeatRows=1,
            hAlign="LEFT",
        )
        table.setStyle(self._table_style(header=True))
        return [Paragraph(title, self.section_style), table, Spacer(1, 10)]

    def _build_list_section(self, title: str, points: list[str]) -> list[object]:
        items = [ListItem(self._paragraph(self._safe(point))) for point in (points or ["No causal factors recorded."])]
        return [Paragraph(self._safe(title), self.section_style), ListFlowable(items, bulletType="1"), Spacer(1, 10)]

    def _build_narrative_section(self, title: str, text: str) -> list[object]:
        return [Paragraph(self._safe(title), self.section_style), self._paragraph(self._safe(text)), Spacer(1, 10)]

    def _build_lesson_section(self, context: IncidentPdfContext) -> list[object]:
        story = [Paragraph(self.SECTION_LABELS["lessons_learned"], self.section_style)]
        if context.lessons_text and not context.lesson_blocks:
            story.append(self._paragraph(self._safe(context.lessons_text)))
        story.extend(self._build_detail_blocks(context.lesson_blocks))
        if not context.lessons_text and not context.lesson_blocks:
            return []
        story.append(Spacer(1, 10))
        return story

    def _build_detail_blocks_section(
        self,
        title: str,
        blocks: list[IncidentPdfDetailBlock],
        *,
        fallback: list[IncidentPdfDetailBlock] | None = None,
    ) -> list[object]:
        if not blocks and not fallback:
            return []
        story = [Paragraph(self._safe(title), self.section_style)]
        story.extend(self._build_detail_blocks(blocks or fallback or []))
        story.append(Spacer(1, 10))
        return story

    def _build_detail_blocks(self, blocks: list[IncidentPdfDetailBlock]) -> list[object]:
        story: list[object] = []
        for block in blocks:
            if not block.rows:
                continue
            if all(not str(label or "").strip() for label, _value in block.rows):
                card_rows = [[Paragraph(self._safe(block.heading), self.block_heading_style)]]
                values = [
                    self._raw_text(value).strip()
                    for _label, value in block.rows
                    if self._raw_text(value).strip()
                ]
                for value in values or ["Not recorded"]:
                    card_rows.append([self._paragraph_html(self._format_plain_text_preserving_spacing(value))])
                table = Table(
                    card_rows,
                    colWidths=[170 * mm],
                    hAlign="LEFT",
                )
                table.setStyle(
                    TableStyle(
                        [
                            ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#CBD5E1")),
                            ("INNERGRID", (0, 1), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ("LEFTPADDING", (0, 0), (-1, -1), 7),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                            ("NOSPLIT", (0, 0), (-1, 0)),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 6))
                continue
            card_rows = [[Paragraph(self._safe(block.heading), self.block_heading_style), ""]]
            for label, value in block.rows:
                card_rows.extend(self._detail_table_rows(label, value))
            table = Table(
                card_rows,
                colWidths=[42 * mm, 128 * mm],
                hAlign="LEFT",
            )
            table.setStyle(
                TableStyle(
                    [
                        ("SPAN", (0, 0), (-1, 0)),
                        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 1), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#CBD5E1")),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                        ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#F8FAFC")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 7),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                        ("NOSPLIT", (0, 0), (-1, 1)),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 6))
        return story

    def _build_signature_section(self, context: IncidentPdfContext) -> list[object]:
        rows = [
            (
                row.label,
                row.signed_by or "Pending",
                row.signed_at or "Pending",
                row.typed_name or "Pending",
            )
            for row in context.signature_rows
        ]
        if not rows:
            return []
        table = Table(
            [[self._cell(value) for value in row] for row in [["Role", "Signed by", "Signed at", "Typed name"], *rows]],
            repeatRows=1,
            hAlign="LEFT",
        )
        table.setStyle(self._table_style(header=True))
        return [Paragraph(self.SECTION_LABELS["signature"], self.section_style), table, Spacer(1, 10)]

    @staticmethod
    def _includes(context: IncidentPdfContext, section_key: str) -> bool:
        return section_key in set(context.included_section_keys or [])

    @staticmethod
    def _rows_to_blocks(title: str, rows: list[tuple[str, str]]) -> list[IncidentPdfDetailBlock]:
        return [IncidentPdfDetailBlock(title, [(str(label), str(value)) for label, value in rows])] if rows else []

    @staticmethod
    def _tuple_rows_to_blocks(title: str, headers: list[str], rows: list[tuple[str, ...]]) -> list[IncidentPdfDetailBlock]:
        blocks: list[IncidentPdfDetailBlock] = []
        for index, row in enumerate(rows or [], start=1):
            blocks.append(
                IncidentPdfDetailBlock(
                    f"{title} {index}",
                    [(headers[pos], str(value)) for pos, value in enumerate(row[: len(headers)])],
                )
            )
        return blocks

    def _paired_summary_rows(self, rows: list[tuple[str, str]]) -> list[list[Paragraph]]:
        output: list[list[Paragraph]] = []
        for index in range(0, len(rows), 2):
            left_label, left_value = rows[index]
            if index + 1 < len(rows):
                right_label, right_value = rows[index + 1]
            else:
                right_label, right_value = "", ""
            output.append(
                [
                    self._cell(left_label),
                    self._paragraph_html(self._format_value(left_value)),
                    self._cell(right_label) if right_label else self._blank_paragraph(),
                    self._paragraph_html(self._format_value(right_value)) if right_label else self._blank_paragraph(),
                ]
            )
        return output

    def _blank_paragraph(self) -> Paragraph:
        return Paragraph("", self.body_style)

    def _detail_table_rows(self, label: str, value: str) -> list[list[Paragraph]]:
        raw_value = self._raw_text(value)
        if raw_value.startswith("PDF_LINK::"):
            return [[self._cell(label), self._paragraph_html(self._format_value(raw_value))]]

        rows: list[list[Paragraph]] = []
        for index, chunk in enumerate(self._chunk_text(raw_value)):
            rows.append(
                [
                    self._cell(label) if index == 0 else self._blank_paragraph(),
                    self._paragraph_html(self._format_value(chunk)),
                ]
            )
        return rows

    def _cell(self, value) -> Paragraph:
        return self._paragraph(self._safe(value))

    def _paragraph(self, value) -> Paragraph:
        return Paragraph(self._raw_text(value).replace("\n", "<br/>"), self.body_style)

    def _paragraph_html(self, value) -> Paragraph:
        return Paragraph(self._raw_text(value).replace("\n", "<br/>"), self.body_style)

    def _format_value(self, value) -> str:
        text = self._raw_text(value)
        if text.startswith("PDF_LINK::"):
            links: list[str] = []
            for line in text.splitlines():
                if not line.startswith("PDF_LINK::"):
                    continue
                _, href, label = line.split("::", 2)
                links.append(f'<link href="{self._safe(href)}" color="blue"><u>{self._safe(label)}</u></link>')
            return "<br/>".join(links) if links else "Not recorded"
        return self._safe(text)

    @classmethod
    def _format_plain_text_preserving_spacing(cls, value) -> str:
        text = cls._raw_text(value).replace("\t", "    ")
        escaped = escape(text)
        output: list[str] = []
        at_line_start = True
        index = 0
        while index < len(escaped):
            character = escaped[index]
            if character == "\n":
                output.append(character)
                at_line_start = True
                index += 1
                continue
            if character != " ":
                output.append(character)
                at_line_start = False
                index += 1
                continue
            end = index
            while end < len(escaped) and escaped[end] == " ":
                end += 1
            run_length = end - index
            if at_line_start:
                output.append("&#160;" * run_length)
            elif run_length == 1:
                output.append(" ")
            else:
                output.append(" " + "&#160;" * (run_length - 1))
            at_line_start = False
            index = end
        return "".join(output)

    @staticmethod
    def _safe(value) -> str:
        return escape(IncidentTenSectionTemplate._raw_text(value))

    @staticmethod
    def _chunk_text(value: str, max_chars: int = 900) -> list[str]:
        text = IncidentTenSectionTemplate._raw_text(value)
        if len(text) <= max_chars:
            return [text]
        chunks = wrap(
            text,
            width=max_chars,
            break_long_words=True,
            break_on_hyphens=False,
            drop_whitespace=False,
            replace_whitespace=False,
        )
        return [chunk.strip() for chunk in chunks if chunk.strip()] or ["Not recorded"]

    @staticmethod
    def _raw_text(value) -> str:
        if value is None:
            return "Not recorded"
        text = str(value)
        return text if text.strip() else "Not recorded"

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
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ]
        if header:
            commands.extend(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        return TableStyle(commands)
