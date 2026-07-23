from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from io import BytesIO
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class PdfRenderResult:
    content: bytes
    content_type: str
    engine: str


class ReportLabPdfRenderer:
    """Phase 0.8 PDF renderer selected after WeasyPrint runtime verification failed."""

    content_type = "application/pdf"
    engine_name = "reportlab"

    def is_available(self) -> bool:
        return self.availability_error() is None

    def availability_error(self) -> str | None:
        try:
            import reportlab  # noqa: F401
        except ImportError:
            return "ReportLab is not installed."
        return None

    def render_html_to_pdf(
        self,
        html: str,
        *,
        title: str = "SQE S 633 - Certificates and Surveys",
    ) -> PdfRenderResult:
        runtime_error = self.availability_error()
        if runtime_error:
            raise RuntimeError(runtime_error)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=16 * mm,
            rightMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
            title=title,
        )
        styles = _build_styles()
        story = [
            Paragraph(title, styles["CertTitle"]),
            Spacer(1, 4 * mm),
        ]

        for block in _extract_text_blocks(html):
            story.append(Paragraph(block, styles["CertBody"]))
            story.append(Spacer(1, 2 * mm))

        doc.build(story)
        return PdfRenderResult(
            content=buffer.getvalue(),
            content_type=self.content_type,
            engine=self.engine_name,
        )

    def render_print_artifact(
        self,
        *,
        print_id: str,
        rows: list[dict],
        payload: dict,
        actor_id: str,
        actor_role: str,
        system_state_hash: str,
    ) -> PdfRenderResult:
        return self._render_register(
            print_id=print_id,
            rows=rows,
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            system_state_hash=system_state_hash,
            title="SQE S 633 - Certificates and Surveys",
            manifest_only=False,
        )

    def render_share_bundle_manifest(
        self,
        *,
        print_id: str,
        rows: list[dict],
        payload: dict,
        actor_id: str,
        actor_role: str,
        system_state_hash: str,
    ) -> PdfRenderResult:
        return self._render_register(
            print_id=print_id,
            rows=rows,
            payload=payload,
            actor_id=actor_id,
            actor_role=actor_role,
            system_state_hash=system_state_hash,
            title="SQE S 633 - Master Share Bundle Manifest",
            manifest_only=True,
        )

    def _render_register(
        self,
        *,
        print_id: str,
        rows: list[dict],
        payload: dict,
        actor_id: str,
        actor_role: str,
        system_state_hash: str,
        title: str,
        manifest_only: bool,
    ) -> PdfRenderResult:
        runtime_error = self.availability_error()
        if runtime_error:
            raise RuntimeError(runtime_error)

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=9 * mm,
            bottomMargin=11 * mm,
            title=title,
        )
        styles = _build_styles()
        story: list = []
        if not manifest_only:
            story.append(Paragraph(title, styles["CertTitle"]))
        story.append(Paragraph(_vessel_header(rows, payload), styles["CertBody"]))
        if manifest_only:
            story.append(Paragraph(f"Printed by: {actor_id} ({actor_role})", styles["CertSmall"]))
        else:
            story.append(Paragraph(f"Print ID: {print_id} | User: {actor_id} ({actor_role}) | Hash: {system_state_hash}", styles["CertSmall"]))
        watermark_text = _watermark_text(payload)
        if watermark_text and not manifest_only:
            story.append(Paragraph(watermark_text, styles["CertWatermark"]))
        story.append(Spacer(1, 3 * mm))
        if not manifest_only:
            story.extend(
                [
                    Paragraph("Validity: F=Full, C=Conditional, S=Short Term, P=Permanent. Status shapes are retained by text status in this web renderer.", styles["CertSmall"]),
                    Spacer(1, 3 * mm),
                ]
            )

        if not rows:
            story.append(Paragraph("No certificates match this print scope.", styles["CertBody"]))
        elif manifest_only:
            story.append(_build_manifest_table(rows, styles))
        else:
            story.append(_build_print_table(rows, styles))

        if not manifest_only:
            story.append(PageBreak())
            story.append(Paragraph("Generation Footer", styles["CertTitle"]))
            story.append(Paragraph(f"SQE S 633 | {print_id} | {actor_id} | {actor_role} | UTC generated by system | {system_state_hash}", styles["CertBody"]))
            if watermark_text:
                story.append(Paragraph(watermark_text, styles["CertWatermark"]))
        doc.build(story)
        return PdfRenderResult(content=buffer.getvalue(), content_type=self.content_type, engine=self.engine_name)


class _HtmlTextExtractor(HTMLParser):
    _BLOCK_TAGS = {"h1", "h2", "h3", "p", "div", "li", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._current: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in self._BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self._current.append(text)

    def _flush(self) -> None:
        text = " ".join(self._current).strip()
        if text:
            self.blocks.append(text)
        self._current = []

    def close(self) -> None:
        super().close()
        self._flush()


def _extract_text_blocks(html: str) -> Iterable[str]:
    parser = _HtmlTextExtractor()
    parser.feed(html)
    parser.close()
    return parser.blocks or ["No printable content."]


def _build_styles() -> dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "CertTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "CertBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1F2937"),
        )
    )
    styles.add(
        ParagraphStyle(
            "CertSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            "CertWatermark",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            alignment=1,
            textColor=colors.HexColor("#B91C1C"),
        )
    )
    return styles


def _build_print_table(rows: list[dict], styles: dict[str, ParagraphStyle]) -> Table:
    header = ["Section", "Sub No.", "Certificate / Survey", "Cert No.", "Issued By", "Issue", "Expiry", "Last Done", "Next Due", "Validity", "Status"]
    data = [header]
    for index, row in enumerate(_ordered_rows(rows), start=1):
        data.append(
            [
                _para(row.get("catalog_section_name") or row.get("catalog_section_code") or "", styles),
                str(index),
                _para(row.get("catalog_display_name") or row.get("catalog_code") or "", styles),
                _para(row.get("certificate_number") or "", styles),
                _para(row.get("issuing_authority") or "", styles),
                _date_text(row.get("issue_date")),
                _date_text(row.get("expiry_date")) or "PERM",
                _date_text(row.get("last_done_date")),
                _date_text(row.get("next_due_date")),
                _validity_code(row.get("validity_type")),
                _para(str(row.get("status") or ""), styles),
            ]
        )
    table = Table(data, repeatRows=1, colWidths=[24 * mm, 12 * mm, 52 * mm, 25 * mm, 24 * mm, 20 * mm, 20 * mm, 20 * mm, 20 * mm, 14 * mm, 24 * mm])
    table.setStyle(_table_style())
    return table


def _build_manifest_table(rows: list[dict], styles: dict[str, ParagraphStyle]) -> Table:
    data = [["#", "Certificate / Survey", "Issue", "Expiry", "File"]]
    for index, row in enumerate(_ordered_rows(rows), start=1):
        data.append(
            [
                str(index),
                _para(row.get("catalog_display_name") or row.get("catalog_code") or "", styles),
                _date_text(row.get("issue_date")),
                _date_text(row.get("expiry_date")) or "PERM",
                _para(row.get("blob_filename") or "certificate.pdf", styles),
            ]
        )
    table = Table(data, repeatRows=1, colWidths=[12 * mm, 88 * mm, 28 * mm, 28 * mm, 70 * mm])
    table.setStyle(_table_style())
    return table


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6),
            ("LEADING", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ]
    )


def _para(value: object, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(str(value or "").replace("&", "&amp;"), styles["CertSmall"])


def _ordered_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda row: (str(row.get("vessel_name") or ""), int(row.get("catalog_print_order") or 0), str(row.get("tracked_item_id") or "")))


def _vessel_header(rows: list[dict], payload: dict) -> str:
    if not rows:
        return f"Scope: {payload.get('scope')}"
    vessel_names = sorted({str(row.get("vessel_name") or row.get("vessel_imo") or row.get("vessel_id") or "Vessel") for row in rows})
    if len(vessel_names) == 1:
        row = rows[0]
        return f"Vessel: {vessel_names[0]} | IMO {row.get('vessel_imo') or 'N/A'} | Flag {row.get('vessel_flag') or 'N/A'} | Class {row.get('class_society') or 'N/A'}"
    return f"Fleet scope: {len(vessel_names)} vessels"


def _watermark_text(payload: dict) -> str:
    watermark = str(payload.get("watermarkApplied") or payload.get("watermark_applied") or "NONE").upper()
    recipient = str(payload.get("watermarkRecipient") or payload.get("watermark_recipient") or "").strip()
    if watermark in {"", "NONE"}:
        return ""
    if watermark == "AUDIT_COPY":
        return f"AUDIT COPY - {recipient}" if recipient else "AUDIT COPY"
    if watermark == "MASTER_COPY":
        return f"MASTER COPY - {recipient}" if recipient else "MASTER COPY"
    if watermark == "DRAFT":
        return "DRAFT - NOT FINAL"
    return watermark


def _date_text(value: object) -> str:
    return str(value or "")[:10]


def _validity_code(value: object) -> str:
    mapping = {"full": "F", "conditional": "C", "short_term": "S", "permanent": "P"}
    return mapping.get(str(value or "").lower(), str(value or ""))
