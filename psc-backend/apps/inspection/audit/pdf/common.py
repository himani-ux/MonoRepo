"""Shared ReportLab helpers for Audit PDF generators."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
import hashlib
import json
from html import escape
from typing import Callable, Iterable
from uuid import UUID

from django.db import transaction
from django.db.models import Max
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


PAGE_SIZE = A4
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_TOP = 18 * mm
MARGIN_BOTTOM = 16 * mm
MARGIN_LEFT = 15 * mm
MARGIN_RIGHT = 15 * mm

COLOR_HEADER_BG = colors.HexColor("#D6EAF8")
COLOR_SECTION_BG = colors.HexColor("#EEF2F7")
COLOR_BORDER = colors.HexColor("#D1D5DB")
COLOR_TEXT = colors.HexColor("#1F2937")
COLOR_MUTED = colors.HexColor("#6B7280")
COLOR_WHITE = colors.white
COLOR_DRAFT = colors.HexColor("#9CA3AF")
COLOR_ADDITIONAL = colors.HexColor("#E84F4F")
COLOR_ADDITIONAL_BG = colors.HexColor("#FDE2E2")

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


@dataclass(frozen=True)
class AuditPdfResult:
    content: bytes
    file_name: str
    content_type: str = "application/pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "AuditTitle",
            parent=styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            textColor=COLOR_TEXT,
            spaceAfter=4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "AuditSubTitle",
            parent=styles["Normal"],
            fontName=FONT,
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=COLOR_MUTED,
            spaceAfter=4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "AuditSection",
            parent=styles["Normal"],
            fontName=FONT_BOLD,
            fontSize=10,
            leading=13,
            textColor=COLOR_TEXT,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            "AuditBody",
            parent=styles["Normal"],
            fontName=FONT,
            fontSize=8.7,
            leading=11.5,
            textColor=COLOR_TEXT,
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            "AuditBodyBold",
            parent=styles["AuditBody"],
            fontName=FONT_BOLD,
        )
    )
    styles.add(
        ParagraphStyle(
            "AuditSmall",
            parent=styles["Normal"],
            fontName=FONT,
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_MUTED,
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            "AuditCell",
            parent=styles["Normal"],
            fontName=FONT,
            fontSize=8,
            leading=10,
            textColor=COLOR_TEXT,
            wordWrap="CJK",
        )
    )
    styles.add(
        ParagraphStyle(
            "AuditCellBold",
            parent=styles["AuditCell"],
            fontName=FONT_BOLD,
        )
    )
    return styles


STYLES = build_styles()


def text(value: object, fallback: str = "-") -> str:
    if value is None:
        return fallback
    rendered = str(value).strip()
    return rendered if rendered else fallback


def paragraph(value: object, style_name: str = "AuditBody") -> Paragraph:
    return Paragraph(escape(text(value)), STYLES[style_name])


def section(title: str) -> list:
    return [Paragraph(escape(title), STYLES["AuditSection"])]


def spacer(height_mm: float = 2) -> Spacer:
    return Spacer(1, height_mm * mm)


def format_date(value: object) -> str:
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d-%b-%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d-%b-%Y")
    if isinstance(value, time):
        return value.strftime("%H:%M")
    return text(value)


def format_date_range(start: object, end: object) -> str:
    if not start and not end:
        return "-"
    if not end or start == end:
        return format_date(start)
    return f"{format_date(start)} to {format_date(end)}"


def format_time(value: object) -> str:
    if not value:
        return "-"
    if isinstance(value, time):
        return value.strftime("%H:%M")
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    return text(value)


def join_csv(values: Iterable[object]) -> str:
    parts = [text(value, "") for value in values]
    return ", ".join(part for part in parts if part) or "-"


def info_table(rows: Iterable[tuple[str, object]], *, widths: tuple[float, float] = (45, 135)) -> Table:
    data = [
        [paragraph(label, "AuditCellBold"), paragraph(value, "AuditCell")]
        for label, value in rows
    ]
    table = Table(data, colWidths=[widths[0] * mm, widths[1] * mm], repeatRows=0)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                ("BACKGROUND", (0, 0), (0, -1), COLOR_SECTION_BG),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def grid_table(headers: list[str], rows: list[list[object]], *, col_widths: list[float] | None = None) -> Table:
    data = [[paragraph(header, "AuditCellBold") for header in headers]]
    data.extend([[paragraph(value, "AuditCell") for value in row] for row in rows])
    if not rows:
        data.append([paragraph("-", "AuditCell") for _header in headers])
    table = Table(data, colWidths=[width * mm for width in col_widths] if col_widths else None, repeatRows=1)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_HEADER_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]
    for index in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, index), (-1, index), colors.HexColor("#F8F9FA")))
    table.setStyle(TableStyle(style))
    return table


def signature_table(labels: list[str]) -> Table:
    rows = [[paragraph(label, "AuditCellBold"), paragraph("Name / Date", "AuditSmall")] for label in labels]
    table = Table(rows, colWidths=[92 * mm, 92 * mm])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                ("LINEABOVE", (1, 0), (1, -1), 0.8, COLOR_TEXT),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def sms_header(form_no: str, revision: str, filing_ref: str, title: str) -> list:
    return [
        Paragraph("KSM SMS Controlled Form", STYLES["AuditSubTitle"]),
        Paragraph(title, STYLES["AuditTitle"]),
        info_table(
            [
                ("Form", form_no),
                ("Revision", revision),
                ("SMS Filing Ref", filing_ref),
            ],
            widths=(38, 142),
        ),
        spacer(2),
    ]


def additional_audit_banner(plan) -> list:
    if not plan or not getattr(plan, "is_additional", False):
        return []
    reason = text(getattr(plan, "additional_reason", None), "")[:200]
    trigger = text(getattr(plan, "trigger_event_type", None), "-")
    body = "ADDITIONAL AUDIT - DPA AUTHORISED"
    if reason:
        body = f"{body} | {trigger} | {reason}"
    else:
        body = f"{body} | {trigger}"
    table = Table([[paragraph(body, "AuditCellBold")]], colWidths=[180 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_ADDITIONAL),
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_ADDITIONAL_BG),
                ("TEXTCOLOR", (0, 0), (-1, -1), COLOR_ADDITIONAL),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [table, spacer(2)]


def is_audit_detail_draft(audit_detail) -> bool:
    return getattr(audit_detail, "status", None) in {"PLANNED", "CONFIRMED", "IN_PROGRESS"}


def is_nc_pdf_draft(closure) -> bool:
    return getattr(closure, "final_closure_status", None) != "LEAD_AUDITOR_CLOSED"


def is_obs_pdf_draft(closure) -> bool:
    return getattr(closure, "closure_status", None) != "MASTER_CLOSED"


def draw_footer(canvas, document, *, form_no: str, filing_ref: str, qr_payload: str | None = None) -> None:
    canvas.saveState()
    canvas.setFont(FONT, 7)
    canvas.setFillColor(COLOR_MUTED)
    footer = f"{form_no} | SMS Filing Ref {filing_ref} | Page {canvas.getPageNumber()}"
    canvas.drawCentredString(PAGE_WIDTH / 2, 8 * mm, footer)
    if qr_payload:
        _draw_qr(canvas, qr_payload)
    canvas.restoreState()


def draw_draft_watermark(canvas) -> None:
    canvas.saveState()
    if hasattr(canvas, "setFillAlpha"):
        canvas.setFillAlpha(0.18)
    canvas.setFillColor(COLOR_DRAFT)
    canvas.setFont(FONT_BOLD, 72)
    canvas.translate(PAGE_WIDTH / 2, PAGE_HEIGHT / 2)
    canvas.rotate(42)
    canvas.drawCentredString(0, 0, "DRAFT")
    canvas.restoreState()


def _draw_qr(canvas, qr_payload: str) -> None:
    payload = qr_payload[:1200]
    qr_size = 18 * mm
    x = PAGE_WIDTH - MARGIN_RIGHT - qr_size
    y = 5 * mm
    qr_code = QrCodeWidget(payload)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(
        qr_size,
        qr_size,
        transform=[qr_size / width, 0, 0, qr_size / height, 0, 0],
    )
    drawing.add(qr_code)
    renderPDF.draw(drawing, canvas, x, y)
    canvas.setFont(FONT, 5.5)
    canvas.setFillColor(COLOR_MUTED)
    marker = _qr_marker(payload)
    canvas.drawRightString(x - 2 * mm, 6 * mm, marker)


def _qr_marker(qr_payload: str) -> str:
    try:
        payload = json.loads(qr_payload)
    except json.JSONDecodeError:
        return "QR payload"
    return f"QR {payload.get('pdf_kind', '-')} v{payload.get('pdf_version', '-')} hash {str(payload.get('content_hash', '-'))[:12]}"


def build_pdf(
    story: list,
    *,
    form_no: str,
    filing_ref: str,
    is_draft: bool = False,
    qr_payload: str | None = None,
) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        rightMargin=MARGIN_RIGHT,
        leftMargin=MARGIN_LEFT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
    )
    def draw_page(canvas, doc) -> None:
        if is_draft:
            draw_draft_watermark(canvas)
        draw_footer(canvas, doc, form_no=form_no, filing_ref=filing_ref, qr_payload=qr_payload)

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
    )
    return buffer.getvalue()


def build_pdf_with_provenance(
    story_factory: Callable[[], list],
    *,
    form_no: str,
    filing_ref: str,
    pdf_kind: str,
    audit_detail_id,
    finding_id=None,
    generated_by: object = None,
    is_draft: bool = False,
) -> tuple[bytes, dict]:
    base_content = build_pdf(
        story_factory(),
        form_no=form_no,
        filing_ref=filing_ref,
        is_draft=is_draft,
    )
    content_hash = hashlib.sha256(base_content).hexdigest()
    pdf_version = _next_pdf_version(
        audit_detail_id=audit_detail_id,
        finding_id=finding_id,
        pdf_kind=pdf_kind,
    )
    payload = {
        "finding_id": str(finding_id) if finding_id else None,
        "audit_detail_id": str(audit_detail_id),
        "pdf_kind": pdf_kind,
        "pdf_version": pdf_version,
        "content_hash": content_hash,
    }
    qr_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content = build_pdf(
        story_factory(),
        form_no=form_no,
        filing_ref=filing_ref,
        is_draft=is_draft,
        qr_payload=qr_payload,
    )
    _record_pdf_generation(
        audit_detail_id=audit_detail_id,
        finding_id=finding_id,
        pdf_kind=pdf_kind,
        pdf_version=pdf_version,
        content_hash=content_hash,
        qr_payload=qr_payload,
        generated_by=generated_by,
    )
    return content, payload


def _next_pdf_version(*, audit_detail_id, finding_id, pdf_kind: str) -> int:
    from apps.inspection.audit.models import AuditPdfGeneration

    filters = _generation_filters(audit_detail_id=audit_detail_id, finding_id=finding_id, pdf_kind=pdf_kind)
    latest = AuditPdfGeneration.objects.filter(**filters).aggregate(max_version=Max("pdf_version"))["max_version"]
    return int(latest or 0) + 1


def _record_pdf_generation(
    *,
    audit_detail_id,
    finding_id,
    pdf_kind: str,
    pdf_version: int,
    content_hash: str,
    qr_payload: str,
    generated_by: object,
) -> None:
    from apps.inspection.audit.models import AuditPdfGeneration

    filters = _generation_filters(audit_detail_id=audit_detail_id, finding_id=finding_id, pdf_kind=pdf_kind)
    with transaction.atomic():
        AuditPdfGeneration.objects.filter(**filters, is_superseded=False).update(is_superseded=True)
        AuditPdfGeneration.objects.create(
            audit_detail_id=audit_detail_id,
            audit_finding_id=finding_id,
            pdf_kind=pdf_kind,
            pdf_version=pdf_version,
            content_hash=content_hash,
            qr_payload=qr_payload,
            generated_by=_generated_by_value(generated_by),
        )


def _generation_filters(*, audit_detail_id, finding_id, pdf_kind: str) -> dict:
    return {
        "audit_detail_id": _uuid_value(audit_detail_id),
        "audit_finding_id": _uuid_value(finding_id) if finding_id else None,
        "pdf_kind": pdf_kind,
    }


def _uuid_value(value):
    if value is None or isinstance(value, UUID):
        return value
    return UUID(str(value))


def _generated_by_value(value: object) -> str:
    if value is None:
        return "system"
    for attr in ("id", "pk", "username"):
        attr_value = getattr(value, attr, None)
        if attr_value:
            return str(attr_value)[:100]
    return str(value)[:100] or "system"
