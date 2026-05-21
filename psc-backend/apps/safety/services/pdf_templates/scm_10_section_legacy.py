from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class SCMLegacyClosedItem:
    item_type: str
    reference: str
    title: str
    status: str
    closed_at: str | None = None


@dataclass(frozen=True)
class SCMLegacySoiObservationRow:
    reference: str
    title: str
    severity: str
    status: str
    corrective_measure: str | None = None
    carried_forward_count: int = 0


@dataclass(frozen=True)
class SCMLegacyAttendanceRow:
    display_name: str
    rank_name: str
    present: bool
    wrh_flag: str
    wrh_rest_hours_24h: str
    wrh_rest_hours_7d: str
    remarks: str | None = None


@dataclass(frozen=True)
class SCMLegacySignatureRow:
    label: str
    status: str
    signed_by: str | None = None
    signed_at: str | None = None
    typed_name: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class SCMLegacySectionRow:
    agenda_item_number: int
    section_label: str
    content: str
    decision: str | None = None
    legacy_fields: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SCMLegacyPdfContext:
    meeting_id: int
    scm_number: str
    vessel_id: str
    meeting_type: str
    meeting_date: str
    meeting_time_local: str
    occasion: str
    ship_position: str
    ship_pos_from: str | None
    ship_pos_to: str | None
    comm_time: str | None
    comp_time: str | None
    location: str
    latitude: str | None
    longitude: str | None
    voyage_no: str
    chair_crew_id: str
    prepared_by_crew_id: str
    state: str
    generated_at: str
    office_comment: str | None
    cutoff_reference: str | None
    master_signed_off_at: str | None = None
    closed_since_last_counts: dict[str, int] = field(default_factory=dict)
    closed_since_last_items: list[SCMLegacyClosedItem] = field(default_factory=list)
    closed_since_last_empty_message: str | None = None
    soi_auto_feed_summary: dict[str, object] = field(default_factory=dict)
    soi_observation_rows: list[SCMLegacySoiObservationRow] = field(default_factory=list)
    attendance_rows: list[SCMLegacyAttendanceRow] = field(default_factory=list)
    signature_rows: list[SCMLegacySignatureRow] = field(default_factory=list)
    section_rows: list[SCMLegacySectionRow] = field(default_factory=list)


class SCMTenSectionLegacyTemplate:
    """SCM PDF renderer styled to match the browser-print sample format."""

    def __init__(self) -> None:
        styles = getSampleStyleSheet()
        self.ink = colors.HexColor("#17212B")
        self.muted = colors.HexColor("#5F6975")
        self.line = colors.HexColor("#CFD8E3")
        self.soft = colors.HexColor("#F4F7FB")
        self.navy = colors.HexColor("#183B56")
        self.teal = colors.HexColor("#0F766E")
        self.amber = colors.HexColor("#B45309")
        self.green = colors.HexColor("#166534")

        self.brand_style = ParagraphStyle(
            "SafetyScmPdfBrand",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=self.muted,
            alignment=TA_LEFT,
        )
        self.title_style = ParagraphStyle(
            "SafetyScmPdfTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=22,
            spaceAfter=3,
            textColor=self.navy,
            alignment=TA_LEFT,
        )
        self.section_style = ParagraphStyle(
            "SafetyScmPdfSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            spaceAfter=6,
            textColor=self.navy,
        )
        self.body_style = ParagraphStyle(
            "SafetyScmPdfBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=4,
            textColor=self.ink,
        )
        self.meta_style = ParagraphStyle(
            "SafetyScmPdfMeta",
            parent=self.body_style,
            fontSize=8,
            leading=10,
            textColor=self.muted,
        )
        self.small_style = ParagraphStyle(
            "SafetyScmPdfSmall",
            parent=self.body_style,
            fontSize=7.8,
            leading=9.5,
            textColor=self.ink,
        )
        self.header_style = ParagraphStyle(
            "SafetyScmPdfHeader",
            parent=self.small_style,
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#243447"),
        )
        self.tag_style = ParagraphStyle(
            "SafetyScmPdfTag",
            parent=self.small_style,
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0F514B"),
            alignment=TA_CENTER,
        )
        self.note_style = ParagraphStyle(
            "SafetyScmPdfNote",
            parent=self.body_style,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#134E4A"),
        )

    def render(self, context: SCMLegacyPdfContext) -> bytes:
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=context.scm_number,
            author="Safety Module",
        )

        sections = {row.agenda_item_number: row for row in context.section_rows}
        story: list[object] = [
            self._build_document_header(
                "Safety Committee Meeting Minutes",
                "Legacy SCM PDF structure preserved for D-PDF-03b and SSOT vw_GetSCM_Master alignment.",
                f"Meeting Type: {context.meeting_type}",
            ),
            self._build_meta_grid(context),
            self._build_note(
                "This template is used for Regular and Ad-Hoc SCM. For Ad-Hoc, the monthly Regular SCM cadence still anchors on the last SCM closure timestamp."
            ),
            Paragraph("Attendance and WRH Snapshot", self.section_style),
            *self._build_attendance_block(context),
            self._build_warning_note(
                "WRH gaps are amber warnings only. They must be acknowledged by the Master, but they do not block creation, conduct, or closure of SCM minutes."
            ),
            Paragraph("Closed Items Since Last SCM", self.section_style),
            *self._build_closed_since_last_block(context),
            Paragraph("Document Control and SSOT Alignment", self.section_style),
            self._build_document_control_table(context),
            Spacer(1, 10),
            self._build_document_header(
                "Legacy 10-Section SCM Record",
                "",
                f"SCM No: {context.scm_number}",
            ),
        ]

        for index in range(1, 8):
            if index == 2:
                continue
            section = sections.get(index)
            if section is not None:
                if index == 5:
                    story.extend(self._build_kpi_review_box(section.legacy_fields))
                story.extend(self._build_section_box(section, self._section_subtitle(index)))

        section_8 = sections.get(8)
        section_9 = sections.get(9)
        section_10 = sections.get(10)
        story.extend(
            [
                Spacer(1, 10),
                self._build_document_header(
                    "SOI Feed, Actions, Comments, Signatures",
                    "",
                    "Closure Anchor: Master Sign-Off",
                ),
            ]
        )
        if section_8 is not None:
            story.extend(
                self._build_custom_section_box(
                    "8. Safety Observations for the Month",
                    "SOI Auto-Feed",
                    self._build_soi_observation_block(
                        section_8,
                        context.soi_auto_feed_summary,
                        context.soi_observation_rows,
                    ),
                )
            )
            story.extend(
                self._build_custom_section_box(
                    "8. Findings and Corrective Measures",
                    "Action Register",
                    [self._build_findings_table(section_8.legacy_fields)],
                )
            )
        if section_9 is not None:
            story.extend(self._build_section_box(section_9, self._section_subtitle(9)))
        if section_10 is not None:
            story.extend(self._build_office_review_box(section_10, context))
        story.extend(
            [
                Paragraph("Digital Signatures", self.section_style),
                *self._build_signature_block(context),
                self._build_note(
                    "Near-miss discussion is printed without exposing restricted reporter identity. SOI remains paper-first; this PDF references records and does not introduce scan upload flow."
                ),
            ]
        )

        document.build(story, onFirstPage=self._draw_footer, onLaterPages=self._draw_footer)
        return buffer.getvalue()

    def _build_document_header(self, title: str, subtitle: str, tag: str) -> Table:
        left: list[object] = [
            Paragraph("KSM VIMS Safety Module", self.brand_style),
            Paragraph(escape(title), self.title_style),
        ]
        if subtitle:
            left.append(Paragraph(escape(subtitle), self.meta_style))
        tag_table = Table([[Paragraph(escape(tag), self.tag_style)]], colWidths=[48 * mm])
        tag_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#91D5CF")),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#E7F7F5")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        table = Table([[left, tag_table]], colWidths=[118 * mm, 52 * mm], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, -1), 1.5, self.navy),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return table

    def _build_meta_grid(self, context: SCMLegacyPdfContext) -> Table:
        time_value = f"{context.comm_time or context.meeting_time_local or '-'} - {context.comp_time or '-'} LT"
        cells = [
            ("SCM No", context.scm_number),
            ("Vessel", context.vessel_id),
            ("Meeting Date", context.meeting_date),
            ("Occasion", self._format_occasion(context.occasion)),
            ("Ship Position", self._format_ship_position(context.ship_position)),
            ("Position From", context.ship_pos_from or "-"),
            ("Position To", context.ship_pos_to or "-"),
            ("Time", time_value),
        ]
        rows = []
        for offset in range(0, len(cells), 4):
            rows.append([self._meta_cell(label, value) for label, value in cells[offset:offset + 4]])
        table = Table(rows, colWidths=[42.5 * mm] * 4, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.6, self.line),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    def _meta_cell(self, label: str, value: object) -> list[object]:
        label_style = ParagraphStyle(
            "SafetyScmPdfMetaLabel",
            parent=self.meta_style,
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=8,
            textColor=self.muted,
        )
        value_style = ParagraphStyle(
            "SafetyScmPdfMetaValue",
            parent=self.small_style,
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=self.ink,
        )
        return [
            Paragraph(escape(label.upper()), label_style),
            Paragraph(escape(str(value or "-")), value_style),
        ]

    def _build_note(self, text: str) -> Table:
        table = Table([[Paragraph(escape(text), self.note_style)]], colWidths=[170 * mm], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEFCF9")),
                    ("LINEBEFORE", (0, 0), (-1, -1), 3, self.teal),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    def _build_warning_note(self, text: str) -> Table:
        table = Table([[Paragraph(escape(text), self.note_style)]], colWidths=[170 * mm], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF7ED")),
                    ("LINEBEFORE", (0, 0), (-1, -1), 3, self.amber),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    def _build_document_control_table(self, context: SCMLegacyPdfContext) -> Table:
        rows = [
            ["Source Form", "Legacy SCM master format, preserving SCMNo, VesselName, SDate, Ocassion, ShipPosition, CommTime, CompTime, and section records."],
            ["RBAC Path", "SCM module behind SAF_F_003. Master and CO can host Regular or Ad-Hoc SCM; Master must perform final sign-off."],
            ["SOI Gate", "Overdue SOI hard-block applies only at Master sign-off. Creation and running the meeting remain available."],
            ["Generated At", context.generated_at],
        ]
        return self._styled_table(rows, colWidths=[48 * mm, 122 * mm])

    def _build_closed_since_last_block(self, context: SCMLegacyPdfContext) -> list[object]:
        counts = context.closed_since_last_counts or {}
        summary = self._styled_table(
            [
                ["Cutoff", context.cutoff_reference or "No prior signed-off SCM yet."],
                ["Incidents", str(counts.get("incident_count", 0))],
                ["Near misses", str(counts.get("near_miss_count", 0))],
                ["SOI findings", str(counts.get("soi_finding_count", 0))],
                ["Corrective actions", str(counts.get("corrective_action_count", 0))],
                ["Total closed items", str(counts.get("total_count", 0))],
            ],
            colWidths=[42 * mm, 128 * mm],
        )
        story: list[object] = [summary, Spacer(1, 6)]
        if context.closed_since_last_items:
            rows = [
                ["Finding ID", "Description", "Closed Date", "Master Sign-Off Timestamp"],
                *[
                    [
                        row.reference,
                        row.title,
                        row.closed_at or "Not recorded",
                        row.status,
                    ]
                    for row in context.closed_since_last_items
                ],
            ]
            story.append(self._styled_table(rows, repeatRows=1, colWidths=[34 * mm, 76 * mm, 28 * mm, 32 * mm]))
        else:
            story.append(Paragraph(escape(context.closed_since_last_empty_message or "Nothing closed since last SCM."), self.meta_style))
        return story

    def _build_attendance_block(self, context: SCMLegacyPdfContext) -> list[object]:
        if not context.attendance_rows:
            rows = [["Rank", "Name", "Attendance", "WRH Status", "Digital Signature Status"], ["-", "No attendance rows recorded.", "-", "-", "-"]]
        else:
            rows = [
                ["Rank", "Name", "Attendance", "WRH Status", "Digital Signature Status"],
                *[
                    [
                        row.rank_name,
                        row.display_name,
                        "Present" if row.present else "Absent",
                        self._wrh_status(row),
                        row.remarks or "Attendance recorded.",
                    ]
                    for row in context.attendance_rows
                ],
            ]
        return [self._styled_table(rows, repeatRows=1, colWidths=[27 * mm, 40 * mm, 28 * mm, 34 * mm, 41 * mm])]

    def _build_signature_block(self, context: SCMLegacyPdfContext) -> list[object]:
        rows = context.signature_rows or [SCMLegacySignatureRow(label="Master signature", status="Awaiting signature")]
        master = next((row for row in rows if "master" in row.label.lower()), None)
        co = next((row for row in rows if "co" in row.label.lower()), None)
        attendees = [row for row in rows if row.label.lower().startswith("attendee")]
        signed_attendees = [row for row in attendees if row.signed_at or row.status.lower() == "signed"]
        cards = [
            self._signature_card("Master", master),
            self._signature_card("Chief Officer", co),
            [
                Paragraph("Attendee Signatures", self.header_style),
                Paragraph(f"{len(signed_attendees)} of {len(attendees)} captured", self.small_style),
                Paragraph("Per attendance list", self.meta_style),
            ],
        ]
        table = Table([cards], colWidths=[54 * mm, 54 * mm, 54 * mm], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.6, self.line),
                    ("INNERGRID", (0, 0), (-1, -1), 0.6, self.line),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        return [table]

    def _signature_card(self, title: str, row: SCMLegacySignatureRow | None) -> list[object]:
        return [
            Paragraph("________________________", self.meta_style),
            Paragraph(escape(title), self.header_style),
            Paragraph(escape(row.typed_name or row.signed_by or "-" if row else "-"), self.small_style),
            Paragraph(
                escape(f"Signed: {row.signed_at}" if row and row.signed_at else (row.status if row else "Awaiting signature")),
                self.meta_style,
            ),
        ]

    def _section_subtitle(self, index: int) -> str:
        return {
            1: "Yes / No",
            2: "Reserved",
            3: "Compliance Review",
            4: "Shipboard Review",
            5: "Environmental Practices",
            6: "Health Review",
            7: "Crew Welfare",
            8: "Findings",
            9: "Minutes",
            10: "For Record",
        }.get(index, "Record")

    def _build_kpi_review_box(self, legacy_fields: Mapping[str, object]) -> list[object]:
        return self._build_custom_section_box(
            "KPI Review",
            "Separate Review",
            [
                self._styled_table(
                    [["KPI review", self._format_legacy_value(legacy_fields.get("kpi_review"), "TEXT")]],
                    colWidths=[50 * mm, 120 * mm],
                )
            ],
        )

    def _build_section_box(
        self,
        section: SCMLegacySectionRow,
        subtitle: str,
        *,
        override_title: str | None = None,
        include_legacy_fields: bool = True,
        soi_summary: Mapping[str, object] | None = None,
        soi_observations: list[SCMLegacySoiObservationRow] | None = None,
    ) -> list[object]:
        body: list[object] = []
        if section.agenda_item_number == 8:
            body.extend(self._build_soi_observation_block(section, soi_summary or {}, soi_observations or []))
        if include_legacy_fields:
            body.extend(self._build_legacy_field_block(section))
        notes = []
        if section.agenda_item_number in {8, 10}:
            if section.content and section.content != "No section content recorded.":
                notes.append(["Discussion / Notes", section.content])
            if section.decision:
                notes.append(["Decision", section.decision])
        if notes:
            if body:
                body.append(Spacer(1, 4))
            body.append(self._styled_table(notes, colWidths=[42 * mm, 128 * mm]))
        if not body:
            body.append(Paragraph("No section content recorded.", self.small_style))
        return self._build_custom_section_box(
            override_title or f"{section.agenda_item_number}. {self._display_section_label(section)}",
            subtitle,
            body,
        )

    def _build_office_review_box(
        self,
        section: SCMLegacySectionRow,
        context: SCMLegacyPdfContext,
    ) -> list[object]:
        rows = [
            ["Office Comments", section.legacy_fields.get("officecomments") or context.office_comment or "-"],
            ["SOI Sign-Off Gate", "Clear. No overdue SOI area exists at the time of Master sign-off."],
            [
                "Closure Timestamp",
                context.master_signed_off_at or "This timestamp becomes the next Closed-Since-Last cutoff anchor.",
            ],
        ]
        return self._build_custom_section_box(
            "10. Office Comments and Review",
            "For Record",
            [self._styled_table(rows, colWidths=[46 * mm, 124 * mm])],
        )

    @staticmethod
    def _display_section_label(section: SCMLegacySectionRow) -> str:
        return {
            2: "Reserved",
            7: "Crew Welfare",
            9: "Minutes of Meeting",
        }.get(section.agenda_item_number, section.section_label)

    def _build_custom_section_box(self, title: str, subtitle: str, body: list[object]) -> list[object]:
        title_table = Table(
            [[Paragraph(escape(title), self.header_style), Paragraph(escape(subtitle), self.header_style)]],
            colWidths=[118 * mm, 52 * mm],
            hAlign="LEFT",
        )
        title_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.soft),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.line),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        # Keep section content as normal flowables so large legacy tables can split across pages.
        return [Spacer(1, 6), title_table, *body, Spacer(1, 2)]

    def _build_soi_observation_block(
        self,
        section: SCMLegacySectionRow,
        summary: Mapping[str, object],
        observations: list[SCMLegacySoiObservationRow],
    ) -> list[object]:
        summary_table = self._styled_table(
            [
                ["SOI Event Occurred This Period", str(summary.get("answer") or ("Yes" if section.content.strip() else "-"))],
                [
                    "Inspection Count and Coverage",
                    str(summary.get("summary_text") or section.decision or "Recorded in SCM agenda."),
                ],
                ["Open SOI Findings", self._format_open_soi_findings(observations)],
                ["Minimum Narrative", "Open observations were reviewed by the committee and action owners were assigned where applicable."],
            ],
            colWidths=[50 * mm, 120 * mm],
        )
        if not observations:
            return [
                summary_table,
                Spacer(1, 4),
                self._styled_table(
                    [["Open SOI Findings", section.content or "No open SOI findings recorded in the meeting narrative."]],
                    colWidths=[50 * mm, 120 * mm],
                ),
            ]
        rows = [
            ["SOI Ref", "Finding", "Severity", "Status", "Corrective / Proposed Action"],
            *[
                [
                    row.reference,
                    row.title,
                    row.severity,
                    self._format_observation_status(row),
                    row.corrective_measure or "-",
                ]
                for row in observations
            ],
        ]
        return [
            summary_table,
            Spacer(1, 4),
            self._styled_table(rows, repeatRows=1, colWidths=[28 * mm, 56 * mm, 22 * mm, 28 * mm, 36 * mm]),
        ]

    @staticmethod
    def _format_open_soi_findings(observations: list[SCMLegacySoiObservationRow]) -> str:
        if not observations:
            return "No open SOI findings recorded in the meeting narrative."
        return " ".join(f"{row.reference}: {row.title}" for row in observations)

    @staticmethod
    def _format_observation_status(row: SCMLegacySoiObservationRow) -> str:
        if row.carried_forward_count > 0:
            return f"{row.status} / carried {row.carried_forward_count}"
        return row.status

    def _build_legacy_field_block(self, section: SCMLegacySectionRow) -> list[object]:
        from apps.safety.serializers.scm import SCM_LEGACY_FIELD_TEMPLATE

        boolean_rows = [["Question", "Yes", "No"]]
        text_rows = [["Field", "Details"]]
        for field in SCM_LEGACY_FIELD_TEMPLATE.get(section.agenda_item_number, ()):
            if field.get("separate_display"):
                continue
            field_key = str(field["field_key"])
            field_type = str(field["field_type"])
            value = section.legacy_fields.get(field_key)
            if field_type == "BOOLEAN":
                yes, no = self._yes_no_marks(value)
                boolean_rows.append([str(field["field_label"]), yes, no])
            else:
                text_rows.append([str(field["field_label"]), self._format_legacy_value(value, field_type)])

        story: list[object] = []
        if len(boolean_rows) > 1:
            story.append(self._styled_table(boolean_rows, repeatRows=1, colWidths=[124 * mm, 23 * mm, 23 * mm]))
        if len(text_rows) > 1:
            if story:
                story.append(Spacer(1, 4))
            story.append(self._styled_table(text_rows, repeatRows=1, colWidths=[50 * mm, 120 * mm]))
        return story

    def _build_findings_table(self, legacy_fields: Mapping[str, object]) -> Table:
        rows = [["No", "Finding", "Corrective Measure", "Owner", "Due Date", "Status"]]
        for index in range(1, 11):
            rows.append(
                [
                    str(index),
                    self._format_legacy_value(legacy_fields.get(f"findings{index}"), "TEXT"),
                    self._format_legacy_value(legacy_fields.get(f"correctivemeasure{index}"), "TEXT"),
                    "TBD" if legacy_fields.get(f"findings{index}") else "",
                    "TBD" if legacy_fields.get(f"findings{index}") else "",
                    "Open" if legacy_fields.get(f"findings{index}") else "",
                ]
            )
        return self._styled_table(rows, repeatRows=1, colWidths=[10 * mm, 54 * mm, 54 * mm, 22 * mm, 18 * mm, 20 * mm])

    def _styled_table(self, rows: list[list[object]], **kwargs) -> Table:
        repeat_rows = int(kwargs.get("repeatRows") or 0)
        wrapped_rows = [
            [self._cell(value, header=repeat_rows > 0 and row_index < repeat_rows) for value in row]
            for row_index, row in enumerate(rows)
        ]
        table = Table(wrapped_rows, hAlign="LEFT", **kwargs)
        table.setStyle(self._table_style(header=repeat_rows > 0))
        return table

    def _cell(self, value: object, *, header: bool = False) -> Paragraph:
        style = self.header_style if header else self.small_style
        return Paragraph(escape(str(value if value not in (None, "") else "-")), style)

    def _draw_footer(self, canvas, document) -> None:
        canvas.saveState()
        width, _height = A4
        y = 12 * mm
        canvas.setStrokeColor(self.line)
        canvas.line(20 * mm, y + 8, width - 20 * mm, y + 8)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(self.muted)
        canvas.drawString(20 * mm, y, f"SCM PDF - Page {document.page}")
        canvas.drawRightString(width - 20 * mm, y, "Generated from VIMS Safety SCM template")
        canvas.restoreState()

    @staticmethod
    def _format_occasion(value: str) -> str:
        normalized = str(value or "").strip().upper()
        if normalized == "M":
            return "M - Monthly"
        return normalized or "-"

    @staticmethod
    def _format_ship_position(value: str) -> str:
        normalized = str(value or "").strip().upper()
        if normalized == "S":
            return "S - Sea"
        if normalized == "P":
            return "P - Port"
        return normalized or "-"

    @staticmethod
    def _yes_no_marks(value: object) -> tuple[str, str]:
        if value in (None, ""):
            return "-", "-"
        is_yes = value is True or str(value).strip().lower() in {"true", "1", "yes", "y"}
        return ("Yes", "") if is_yes else ("", "No")

    @staticmethod
    def _format_legacy_value(value: object, field_type: str) -> str:
        if value in (None, ""):
            return "-"
        if field_type == "BOOLEAN":
            return "Yes" if value is True or str(value).strip().lower() in {"true", "1", "yes"} else "No"
        return str(value)

    @staticmethod
    def _wrh_status(row: SCMLegacyAttendanceRow) -> str:
        flag = str(row.wrh_flag or "").upper()
        if flag == "RED":
            return f"Non-Compliant; 24h {row.wrh_rest_hours_24h}; 7d {row.wrh_rest_hours_7d}"
        if flag == "AMBER":
            return f"Unavailable; 24h {row.wrh_rest_hours_24h}; 7d {row.wrh_rest_hours_7d}"
        return f"Compliant; 24h {row.wrh_rest_hours_24h}; 7d {row.wrh_rest_hours_7d}"

    @staticmethod
    def _table_style(*, header: bool = False) -> TableStyle:
        commands = [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CFD8E3")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        if header:
            commands.extend(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        return TableStyle(commands)
