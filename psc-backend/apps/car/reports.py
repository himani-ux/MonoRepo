"""
CAR PDF report generation using reportlab.

Source: DESIGN_SYSTEM.md Section 12 (PDF Report Styling)
Implements: PRD.md FEAT-RPT-001

Page Setup: A4 portrait, margins (top 20mm, bottom 15mm, left/right 15mm)
Fonts: Arial - body 10pt, headings 12pt bold, title 14pt bold
Tables: #D6EAF8 header, alternating white/#F8F9FA rows, 0.5pt #D1D5DB borders
"""

import io
import json
import re
from datetime import datetime
from typing import Any
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ---------------------------------------------------------------------------
# Design tokens from DESIGN_SYSTEM.md Section 12
# ---------------------------------------------------------------------------
PAGE_WIDTH, PAGE_HEIGHT = A4  # 210mm × 297mm
MARGIN_TOP = 20 * mm
MARGIN_BOTTOM = 15 * mm
MARGIN_LEFT = 15 * mm
MARGIN_RIGHT = 15 * mm

COLOR_HEADER_BG = colors.HexColor('#D6EAF8')
COLOR_ALT_ROW = colors.HexColor('#F8F9FA')
COLOR_BORDER = colors.HexColor('#D1D5DB')
COLOR_DETENTION = colors.HexColor('#FADBD8')
COLOR_TEXT = colors.HexColor('#1F2937')
COLOR_MUTED = colors.HexColor('#6B7280')

FONT_FAMILY = 'Helvetica'  # reportlab built-in (Arial equivalent)
FONT_FAMILY_BOLD = 'Helvetica-Bold'

HISTORY_HIDE_COMMENT_EVENT_TYPES = {'CAR_PIC_ACCEPTED', 'CAR_DPA_CLOSED'}
HISTORY_HIDE_COMMENT_ACTIONS = {'START_PIC_REVIEW', 'CLOSE_CAR'}
AUDIENCE_INTERNAL = 'internal'
AUDIENCE_EXTERNAL = 'external'
CORRECTIVE_ACTION_WITHHELD_PLACEHOLDER = (
    'Corrective action text withheld (internal/system content detected).'
)

INTERNAL_CORRECTIVE_ACTION_PATTERN = re.compile(
    r"""
    (
        inspection\s*create\s*(?:->|→)\s*submit\s*(?:->|→)\s*review\s*(?:->|→)\s*close
        | car\s*submit\s*(?:->|→)\s*(?:accept|accept/rework|rework)\s*(?:->|→)\s*close
        | sync\s+conflict\s+resolution
        | \b(?:PIC_REVIEW|SUBMITTED_TO_PIC|SUBMITTED_TO_DPA|RETURNED_FOR_REWORK)\b\s*(?:->|→)\s*\b[A-Z_]+\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

INTERNAL_STATE_TRANSITION_PATTERN = re.compile(
    r"\(?\b[A-Z_]{4,}\b\s*(?:->|→)\s*\b[A-Z_]{4,}\b\)?"
)


# ---------------------------------------------------------------------------
# Paragraph styles
# ---------------------------------------------------------------------------
def _build_styles():
    """Build custom paragraph styles per DESIGN_SYSTEM.md Section 12."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'ReportTitle',
        parent=styles['Normal'],
        fontName=FONT_FAMILY_BOLD,
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=COLOR_TEXT,
        spaceAfter=2 * mm,
    ))

    styles.add(ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName=FONT_FAMILY_BOLD,
        fontSize=12,
        leading=16,
        textColor=COLOR_TEXT,
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    ))

    styles.add(ParagraphStyle(
        'BodyText10',
        parent=styles['Normal'],
        fontName=FONT_FAMILY,
        fontSize=10,
        leading=14,
        textColor=COLOR_TEXT,
        wordWrap='CJK',
    ))

    styles.add(ParagraphStyle(
        'BodyBold10',
        parent=styles['Normal'],
        fontName=FONT_FAMILY_BOLD,
        fontSize=10,
        leading=14,
        textColor=COLOR_TEXT,
    ))

    styles.add(ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontName=FONT_FAMILY,
        fontSize=8,
        leading=10,
        textColor=COLOR_MUTED,
    ))

    styles.add(ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName=FONT_FAMILY,
        fontSize=9,
        leading=12,
        textColor=COLOR_TEXT,
        wordWrap='CJK',
    ))

    styles.add(ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName=FONT_FAMILY_BOLD,
        fontSize=9,
        leading=12,
        textColor=COLOR_TEXT,
    ))

    styles.add(ParagraphStyle(
        'HeaderRight',
        parent=styles['Normal'],
        fontName=FONT_FAMILY_BOLD,
        fontSize=12,
        leading=16,
        alignment=TA_RIGHT,
        textColor=COLOR_TEXT,
    ))

    styles.add(ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontName=FONT_FAMILY,
        fontSize=8,
        leading=10,
        textColor=COLOR_MUTED,
        alignment=TA_CENTER,
    ))

    return styles


# ---------------------------------------------------------------------------
# Table styling helpers
# ---------------------------------------------------------------------------
def _base_table_style():
    """Standard table style per DESIGN_SYSTEM.md Section 12."""
    return [
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_HEADER_BG),
        ('FONTNAME', (0, 0), (-1, 0), FONT_FAMILY_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        # Body rows
        ('FONTNAME', (0, 1), (-1, -1), FONT_FAMILY),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        # Alignment & padding
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]


def _add_alternating_rows(style_cmds: list, row_count: int):
    """Add alternating row backgrounds (white / #F8F9FA)."""
    for i in range(1, row_count):
        if i % 2 == 0:
            style_cmds.append(
                ('BACKGROUND', (0, i), (-1, i), COLOR_ALT_ROW)
            )


def _info_table_style():
    """Two-column label/value table style (no header row)."""
    return [
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('FONTNAME', (0, 0), (0, -1), FONT_FAMILY_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (0, -1), COLOR_ALT_ROW),
    ]


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def _fmt_date(value) -> str:
    """Format a date/datetime string for display."""
    if not value:
        return '—'
    if isinstance(value, str):
        # Try ISO formats
        for fmt in ('%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%d'):
            try:
                dt = datetime.strptime(value, fmt)
                if 'T' in value:
                    return dt.strftime('%d %b %Y %H:%M')
                return dt.strftime('%d %b %Y')
            except ValueError:
                continue
    return str(value) if value else '—'


def _safe(value, default: str = '—') -> str:
    """Return value or default if None/empty."""
    if value is None or value == '':
        return default
    return str(value)


def _wrap(text: str, style) -> Paragraph:
    """Wrap text in a Paragraph for table cell wrapping."""
    normalized = str(text or '—')
    escaped = escape(normalized).replace('\n', '<br/>')
    return Paragraph(escaped, style)


def _wrap_link(text: str, url: str | None, style) -> Paragraph:
    """Wrap text in a clickable PDF hyperlink when a URL is available."""
    if not url:
        return _wrap(text, style)

    normalized = str(text or '—')
    escaped_text = escape(normalized).replace('\n', '<br/>')
    escaped_url = escape(str(url), quote=True)
    return Paragraph(f'<link href="{escaped_url}">{escaped_text}</link>', style)


def _normalize_audience(audience: str | None) -> str:
    """Normalize and validate export audience."""
    normalized = (audience or AUDIENCE_INTERNAL).strip().lower()
    return AUDIENCE_EXTERNAL if normalized == AUDIENCE_EXTERNAL else AUDIENCE_INTERNAL


def _resolve_vessel_name(car_data: dict[str, Any]) -> str:
    """
    Resolve vessel display name with strict fallback chain:
    inspection.vessel.name -> car.vessel.name -> car.vessel_name -> "—"
    """
    inspection = car_data.get('inspection') or {}
    inspection_vessel = inspection.get('vessel') or {}
    car_vessel = car_data.get('vessel') or {}
    return _safe(
        inspection_vessel.get('name')
        or car_vessel.get('name')
        or car_data.get('vessel_name')
    )


def _format_deficiency_label(deficiency: dict[str, Any]) -> str:
    """Format deficiency as `code - title`, falling back to code-only."""
    code = (deficiency.get('def_code') or '').strip()
    title = (
        deficiency.get('def_code_description')
        or deficiency.get('def_code_title')
        or ''
    ).strip()
    if code and title:
        return f'{code} - {title}'
    return code or '—'


def _contains_internal_system_text(text: str | None) -> bool:
    """Detect internal workflow/dev text that must not be printed in PDF."""
    normalized = (text or '').strip()
    if not normalized:
        return False
    return bool(INTERNAL_CORRECTIVE_ACTION_PATTERN.search(normalized))


def _strip_internal_state_transitions(text: str | None) -> str:
    """Remove internal state-transition notation for external reports."""
    if not text:
        return ''
    cleaned = INTERNAL_STATE_TRANSITION_PATTERN.sub('', str(text))
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    return cleaned.strip()


def _format_action_code_change_note(deficiency: dict[str, Any]) -> str:
    """Format action code change note when history metadata is available."""
    note = deficiency.get('action_code_change_note') or {}
    if not isinstance(note, dict):
        return ''
    from_code = str(note.get('from') or '').strip()
    to_code = str(note.get('to') or '').strip()
    if not from_code or not to_code or from_code == to_code:
        return ''

    changed_at = _fmt_date(note.get('changed_at'))
    changed_by = str(note.get('changed_by') or '').strip() or 'Unknown'
    return f'Changed from {from_code} to {to_code} on {changed_at} by {changed_by}'


def _fetch_clc_item_names(clc_codes: list[str]) -> dict[str, str]:
    """
    Resolve CLC code -> item_name from master data.

    Returns empty mapping on lookup failure (PDF generation should not crash).
    """
    if not clc_codes:
        return {}

    from apps.masters.models import CLCItem

    try:
        rows = CLCItem.objects.filter(
            is_active=True,
            clc_code__in=clc_codes,
        ).values_list('clc_code', 'item_name')
        return {
            str(code): str(name)
            for code, name in rows
            if code and name
        }
    except Exception:
        return {}


def _strip_clc_prefix(label: str, clc_code: str | None) -> str:
    """
    Remove internal CLC code prefixes from a display label.

    Examples:
    - "1-10 Shortcuts" -> "Shortcuts"
    - "CLC Item 2-1" -> ""
    """
    cleaned = (label or '').strip()
    if not cleaned:
        return ''

    if clc_code:
        code_pattern = rf"^\s*{re.escape(str(clc_code).strip())}\s*[-:.)]?\s*"
        cleaned = re.sub(code_pattern, '', cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(
        r"^\s*CLC\s*Item\s*[A-Za-z0-9-]*\s*[-:.)]?\s*",
        '',
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()


def _resolve_clc_labels(clc_items: list[dict[str, Any]]) -> list[str]:
    """
    Build ordered, de-duplicated human-readable CLC labels for PDF output.

    Important: never return raw CLC IDs/codes as fallback.
    """
    if not clc_items:
        return []

    codes = []
    for item in clc_items:
        code = (item.get('clc_item_id') or '').strip()
        if code:
            codes.append(code)
    name_map = _fetch_clc_item_names(codes)

    labels: list[str] = []
    seen: set[str] = set()

    for item in clc_items:
        code = (item.get('clc_item_id') or '').strip()
        custom = (item.get('custom_cause_text') or '').strip()
        name = (item.get('clc_item_name') or '').strip()
        source = custom or name or name_map.get(code, '')
        label = _strip_clc_prefix(source, code)
        if not label:
            continue

        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        labels.append(label)

    return labels


def _extract_appended_comment(event_description: str | None) -> str:
    """Extract trailing workflow comment from '... — comment' descriptions."""
    if not event_description:
        return ''
    _, sep, tail = str(event_description).partition(' — ')
    if not sep:
        return ''
    return tail.strip()


def _workflow_action_from_event(event: dict[str, Any]) -> str:
    """Best-effort extraction of workflow action key from event payload."""
    event_type = str(event.get('event_type') or '')
    prefix = 'CAR_WORKFLOW_'
    if event_type.startswith(prefix):
        return event_type[len(prefix):]

    metadata = event.get('metadata')
    if isinstance(metadata, dict):
        return str(metadata.get('action') or '')

    if isinstance(metadata, str):
        try:
            parsed = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            return ''
        if isinstance(parsed, dict):
            return str(parsed.get('action') or '')

    return ''


def _should_hide_comment_in_history(event: dict[str, Any]) -> bool:
    """Only remove appended comments for PIC and DPA office-action events."""
    event_type = str(event.get('event_type') or '')
    if event_type in HISTORY_HIDE_COMMENT_EVENT_TYPES:
        return True

    action = _workflow_action_from_event(event)
    return action in HISTORY_HIDE_COMMENT_ACTIONS


def _history_description_without_comment(event: dict[str, Any]) -> str:
    """Return event description with trailing comment removed when required."""
    description = _safe(event.get('event_description'))
    if not _should_hide_comment_in_history(event):
        return description
    base, sep, _ = description.partition(' — ')
    return base.strip() if sep else description


def _derive_dpa_comment(car_data: dict[str, Any]) -> str:
    """
    Determine DPA comment for report body with safe fallback order:
    1) dedicated dpa_comment field
    2) close-event appended comment in activity history
    3) last_action_comment only when status is CLOSED
    """
    dpa_comment = (car_data.get('dpa_comment') or '').strip()
    if dpa_comment:
        return dpa_comment

    history = car_data.get('activity_history') or []
    for event in history:
        action = _workflow_action_from_event(event)
        if action != 'CLOSE_CAR' and str(event.get('event_type') or '') != 'CAR_DPA_CLOSED':
            continue
        derived = _extract_appended_comment(event.get('event_description'))
        if derived:
            return derived

    if str(car_data.get('status') or '').upper() == 'CLOSED':
        last_comment = (car_data.get('last_action_comment') or '').strip()
        if last_comment:
            return last_comment

    return ''


def _find_activity_event(
    car_data: dict[str, Any],
    *,
    event_types: set[str],
    workflow_actions: set[str],
) -> dict[str, Any] | None:
    """Find first matching activity event from newest-first activity history."""
    history = car_data.get('activity_history') or []
    for event in history:
        event_type = str(event.get('event_type') or '')
        if event_type in event_types:
            return event
        if _workflow_action_from_event(event) in workflow_actions:
            return event
    return None


def _resolve_pic_actor_time(car_data: dict[str, Any]) -> tuple[str, Any]:
    """Resolve PIC actor/time from dedicated fields with activity-history fallback."""
    actor = (car_data.get('pic_accepted_by') or '').strip()
    performed_at = car_data.get('pic_accepted_at')
    event = _find_activity_event(
        car_data,
        event_types={'CAR_PIC_ACCEPTED'},
        workflow_actions={'START_PIC_REVIEW'},
    )
    if event:
        if not actor:
            actor = _safe(event.get('performed_by_name', event.get('performed_by')), '')
        if not performed_at:
            performed_at = event.get('performed_at')
    return actor or '—', performed_at


def _resolve_dpa_actor_time(car_data: dict[str, Any]) -> tuple[str, Any]:
    """Resolve DPA actor/time from dedicated fields with activity-history fallback."""
    actor = (car_data.get('dpa_closed_by') or '').strip()
    performed_at = car_data.get('dpa_closed_at')
    event = _find_activity_event(
        car_data,
        event_types={'CAR_DPA_CLOSED'},
        workflow_actions={'CLOSE_CAR'},
    )
    if event:
        if not actor:
            actor = _safe(event.get('performed_by_name', event.get('performed_by')), '')
        if not performed_at:
            performed_at = event.get('performed_at')
    return actor or '—', performed_at


# ---------------------------------------------------------------------------
# PDF Builder
# ---------------------------------------------------------------------------
def generate_car_pdf(car_data: dict, audience: str = AUDIENCE_INTERNAL) -> bytes:
    """
    Generate a PDF report for a single CAR.

    Args:
        car_data: Serialized CAR detail data (from CARDetailSerializer).
        audience: "internal" (default) or "external".

    Returns:
        PDF file content as bytes.

    Source: DESIGN_SYSTEM.md Section 12 (PDF Report Styling)
    Implements: PRD.md FEAT-RPT-001
    """
    buffer = io.BytesIO()
    styles = _build_styles()
    audience_mode = _normalize_audience(audience)
    payload = car_data

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        leftMargin=MARGIN_LEFT,
        rightMargin=MARGIN_RIGHT,
        title=f"CAR Report - {payload.get('car_number', '')}",
        author='VIMS Inspection System',
    )

    content_width = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    elements: list[Any] = []

    # ------------------------------------------------------------------
    # 1. HEADER
    # ------------------------------------------------------------------
    _build_header(elements, payload, styles, content_width)

    # ------------------------------------------------------------------
    # 2. CAR INFORMATION
    # ------------------------------------------------------------------
    _build_car_info(elements, payload, styles, content_width)

    # ------------------------------------------------------------------
    # 3. DEFICIENCY
    # ------------------------------------------------------------------
    _build_deficiency_section(
        elements, payload, styles, content_width, audience=audience_mode
    )

    # ------------------------------------------------------------------
    # 4. ROOT CAUSE ANALYSIS
    # ------------------------------------------------------------------
    _build_root_cause_section(elements, payload, styles, content_width)

    # ------------------------------------------------------------------
    # 5. CORRECTIVE ACTIONS
    # ------------------------------------------------------------------
    _build_corrective_actions(
        elements, payload, styles, content_width, audience=audience_mode
    )

    # ------------------------------------------------------------------
    # 6. OFFICE ACTIONS
    # ------------------------------------------------------------------
    _build_review_comments(
        elements, payload, styles, content_width, audience=audience_mode
    )

    # ------------------------------------------------------------------
    # 7. PHYSICAL VERIFICATION (only when CLOSED)
    # ------------------------------------------------------------------
    _build_physical_verification(elements, payload, styles, content_width)

    # ------------------------------------------------------------------
    # 8. EVIDENCE LIST
    # ------------------------------------------------------------------
    _build_evidence_list(elements, payload, styles, content_width)

    # ------------------------------------------------------------------
    # 9. REVIEW / APPROVAL HISTORY
    # ------------------------------------------------------------------
    if audience_mode == AUDIENCE_INTERNAL:
        _build_review_history(
            elements, payload, styles, content_width, audience=audience_mode
        )

    # Build PDF with footer callback
    car_number = payload.get('car_number', '')
    doc.build(
        elements,
        onFirstPage=lambda canvas, doc: _draw_footer(canvas, doc, car_number),
        onLaterPages=lambda canvas, doc: _draw_footer(canvas, doc, car_number),
    )

    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------
def _build_company_logo():
    """Build company logo for the PDF header.

    Uses uploaded logo from settings.COMPANY_LOGO_PATH if available,
    otherwise falls back to a simple vector placeholder.
    """
    from django.conf import settings
    from reportlab.platypus import Image as RLImage

    logo_path = settings.COMPANY_LOGO_PATH
    if logo_path.exists():
        try:
            max_width = 30 * mm
            max_height = 15 * mm
            img_reader = ImageReader(str(logo_path))
            img_w, img_h = img_reader.getSize()
            if img_w and img_h:
                scale = min(max_width / float(img_w), max_height / float(img_h))
                draw_w = float(img_w) * scale
                draw_h = float(img_h) * scale
            else:
                draw_w, draw_h = max_width, max_height

            img = RLImage(str(logo_path), width=draw_w, height=draw_h)
            img.hAlign = 'LEFT'
            return img
        except Exception:
            pass  # Fall back to vector logo

    # Fallback: simple vector placeholder
    logo_width = 30 * mm
    logo_height = 15 * mm

    drawing = Drawing(logo_width, logo_height)
    drawing.add(Rect(
        0,
        0,
        logo_width,
        logo_height,
        fillColor=COLOR_HEADER_BG,
        strokeColor=COLOR_BORDER,
        strokeWidth=0.6,
    ))
    drawing.add(Rect(
        0,
        0,
        6 * mm,
        logo_height,
        fillColor=colors.HexColor('#2563EB'),
        strokeColor=None,
    ))
    drawing.add(String(
        9 * mm,
        5.3 * mm,
        'VIMS',
        fontName=FONT_FAMILY_BOLD,
        fontSize=9,
        fillColor=COLOR_TEXT,
    ))
    return drawing


def _build_header(elements: list, car_data: dict, styles, content_width: float):
    """Header: Company logo | Title | CAR Number."""
    car_number = car_data.get('car_number', '')

    # Three-column header table
    header_data = [[
        _build_company_logo(),
        Paragraph('CORRECTIVE ACTION REPORT', styles['ReportTitle']),
        Paragraph(car_number, styles['HeaderRight']),
    ]]

    header_table = Table(
        header_data,
        colWidths=[30 * mm, content_width - 80 * mm, 50 * mm],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4 * mm),
        ('LINEBELOW', (0, 0), (-1, 0), 1, COLOR_BORDER),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))


def _build_car_info(elements: list, car_data: dict, styles, content_width: float):
    """CAR information grid — key/value pairs."""
    elements.append(Paragraph('CAR Information', styles['SectionHeading']))

    inspection = car_data.get('inspection') or {}

    cell = styles['CellText']

    info_data = [
        [_wrap('CAR Number', styles['CellBold']), _wrap(car_data.get('car_number', ''), cell),
         _wrap('Status', styles['CellBold']), _wrap(car_data.get('status_display', ''), cell)],
        [_wrap('Vessel', styles['CellBold']), _wrap(_resolve_vessel_name(car_data), cell),
         _wrap('Target Date', styles['CellBold']), _wrap(_fmt_date(car_data.get('target_date')), cell)],
        [_wrap('Inspection Type', styles['CellBold']), _wrap(inspection.get('inspection_type', ''), cell),
         _wrap('Inspection Date', styles['CellBold']), _wrap(_fmt_date(inspection.get('inspection_date')), cell)],
        [_wrap('Port', styles['CellBold']), _wrap(inspection.get('port_place', ''), cell),
         _wrap('Created', styles['CellBold']), _wrap(_fmt_date(car_data.get('created_date')), cell)],
    ]

    col_w = content_width / 4
    info_table = Table(info_data, colWidths=[col_w] * 4)
    info_table.setStyle(TableStyle(_info_table_style() + [
        ('BACKGROUND', (2, 0), (2, -1), COLOR_ALT_ROW),
    ]))

    elements.append(info_table)


def _build_deficiency_section(
    elements: list,
    car_data: dict,
    styles,
    content_width: float,
    audience: str = AUDIENCE_INTERNAL,
):
    """Deficiency details with DefCode prominent."""
    del audience
    elements.append(Paragraph('Deficiency Details', styles['SectionHeading']))

    deficiency = car_data.get('deficiency') or {}
    cell = styles['CellText']
    deficiency_label = _format_deficiency_label(deficiency)
    initial_action_code = deficiency.get('initial_action_code') or deficiency.get('action_code')
    current_action_code = deficiency.get('current_action_code') or deficiency.get('action_code')
    action_change_note = _format_action_code_change_note(deficiency)

    def_data: list[list[Any]] = [
        [_wrap('Deficiency', styles['CellBold']),
         _wrap(deficiency_label, styles['CellBold'])],
        [_wrap('Description', styles['CellBold']),
         _wrap(deficiency.get('description', ''), cell)],
        [_wrap('Action Code at Inspection', styles['CellBold']),
         _wrap(_safe(initial_action_code), cell)],
        [_wrap('Current Action Code', styles['CellBold']),
         _wrap(_safe(current_action_code), cell)],
        [_wrap('Cleared', styles['CellBold']),
         _wrap('Yes' if deficiency.get('is_cleared') else 'No', cell)],
    ]
    if action_change_note:
        def_data.insert(
            4,
            [_wrap('Action Code Change', styles['CellBold']), _wrap(action_change_note, cell)],
        )

    def_table = Table(def_data, colWidths=[40 * mm, content_width - 40 * mm])
    def_table.setStyle(TableStyle(_info_table_style()))

    elements.append(def_table)


def _build_root_cause_section(elements: list, car_data: dict, styles, content_width: float):
    """Root cause analysis: CLC codes and summary."""
    elements.append(Paragraph('Root Cause Analysis', styles['SectionHeading']))

    # Human-readable CLC labels only (no internal IDs/codes/prefixes)
    clc_items = car_data.get('clc_items') or []
    labels = _resolve_clc_labels(clc_items)
    if labels:
        elements.append(Paragraph('Root Cause Analysis:', styles['BodyBold10']))
        elements.append(Spacer(1, 2 * mm))
        for label in labels:
            elements.append(Paragraph(f'* {escape(label)}', styles['BodyText10']))
        elements.append(Spacer(1, 3 * mm))
    else:
        elements.append(Paragraph('No root cause labels recorded.', styles['BodyText10']))
        elements.append(Spacer(1, 3 * mm))

    # Root cause summary
    summary = car_data.get('root_cause_summary') or 'Not provided.'
    elements.append(Paragraph('Root Cause Summary:', styles['BodyBold10']))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(summary, styles['BodyText10']))


def _build_review_comments(
    elements: list,
    car_data: dict,
    styles,
    content_width: float,
    audience: str = AUDIENCE_INTERNAL,
):
    """Main-body office actions with actor/time/comment (PIC and DPA)."""
    elements.append(Paragraph('Office Actions', styles['SectionHeading']))

    def _build_review_details(actor: str, performed_at: Any, comment: str) -> Table:
        """Render actor, datetime, and comment in dedicated rows for readable wrapping."""
        details_width = max(content_width - (40 * mm) - 8, 60 * mm)
        label_width = min(24 * mm, details_width * 0.3)
        value_width = max(details_width - label_width, 30 * mm)
        detail_data = [
            [_wrap('Name:', styles['CellBold']), _wrap(actor, styles['CellText'])],
            [_wrap('Datetime:', styles['CellBold']), _wrap(_fmt_date(performed_at), styles['CellText'])],
            [_wrap('Comment:', styles['CellBold']), _wrap(comment, styles['CellText'])],
        ]
        detail_table = Table(detail_data, colWidths=[label_width, value_width])
        detail_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        return detail_table

    pic_actor, pic_performed_at = _resolve_pic_actor_time(car_data)
    dpa_actor, dpa_performed_at = _resolve_dpa_actor_time(car_data)
    pic_comment = (car_data.get('pic_comment') or '').strip()
    dpa_comment = _derive_dpa_comment(car_data)
    if (
        _normalize_audience(audience) == AUDIENCE_EXTERNAL
        and not (car_data.get('dpa_comment') or '').strip()
    ):
        dpa_comment = _strip_internal_state_transitions(dpa_comment)
    pic_comment = pic_comment or '—'
    dpa_comment = dpa_comment or '—'

    comments_data = [
        [
            _wrap('PIC', styles['CellBold']),
            _build_review_details(pic_actor, pic_performed_at, pic_comment),
        ],
        [
            _wrap('DPA', styles['CellBold']),
            _build_review_details(dpa_actor, dpa_performed_at, dpa_comment),
        ],
    ]

    comments_table = Table(comments_data, colWidths=[40 * mm, content_width - 40 * mm])
    comments_table.setStyle(TableStyle(_info_table_style()))
    elements.append(comments_table)


def _build_corrective_actions(
    elements: list,
    car_data: dict,
    styles,
    content_width: float,
    audience: str = AUDIENCE_INTERNAL,
):
    """
    Corrective actions as narrative sections.

    Mirrors current CAR screen model: Immediate Actions + Long-term / Preventive Actions.
    Intentionally does NOT print internal workflow fields (due date/completed/pending).
    """
    del content_width  # Section uses paragraph flow, no table widths needed.
    del audience
    elements.append(Paragraph('Corrective Actions', styles['SectionHeading']))

    actions = car_data.get('corrective_actions') or []
    immediate_items: list[str] = []
    long_term_items: list[str] = []

    for action in actions:
        description = (action.get('description') or '').strip()
        if not description:
            continue
        if _contains_internal_system_text(description):
            description = CORRECTIVE_ACTION_WITHHELD_PLACEHOLDER
        action_type = str(action.get('action_type') or '').upper()
        if action_type == 'IMMEDIATE':
            immediate_items.append(description)
        else:
            long_term_items.append(description)

    def _render_action_block(title: str, items: list[str]):
        elements.append(Paragraph(title, styles['BodyBold10']))
        elements.append(Spacer(1, 1.5 * mm))
        if not items:
            elements.append(Paragraph('No corrective actions recorded.', styles['BodyText10']))
            elements.append(Spacer(1, 2.5 * mm))
            return

        for idx, text in enumerate(items, 1):
            elements.append(Paragraph(f'{idx}. {escape(text)}', styles['BodyText10']))
        elements.append(Spacer(1, 2.5 * mm))

    _render_action_block('Immediate Actions:', immediate_items)
    _render_action_block('Long-term / Preventive Actions:', long_term_items)


def _build_evidence_list(elements: list, car_data: dict, styles, content_width: float):
    """Evidence list table — filenames only, NOT embedded images per FEAT-RPT-001."""
    elements.append(Paragraph('Evidence', styles['SectionHeading']))

    evidence_list = car_data.get('evidence') or []
    if not evidence_list:
        elements.append(Paragraph('No evidence uploaded.', styles['BodyText10']))
        return

    cell = styles['CellText']
    col_widths = [8 * mm, 22 * mm, 45 * mm, content_width - 100 * mm, 25 * mm]
    table_data: list[list[Any]] = [['#', 'Type', 'File Name', 'Description', 'Uploaded']]

    for idx, ev in enumerate(evidence_list, 1):
        table_data.append([
            str(idx),
            _wrap(_safe(ev.get('evidence_type_display', ev.get('evidence_type'))), cell),
            _wrap_link(_safe(ev.get('file_name')), ev.get('report_preview_url'), cell),
            _wrap(_safe(ev.get('description')), cell),
            _wrap(_fmt_date(ev.get('uploaded_at')), cell),
        ])

    ev_table = Table(table_data, colWidths=col_widths)
    style_cmds = _base_table_style()
    _add_alternating_rows(style_cmds, len(table_data))
    ev_table.setStyle(TableStyle(style_cmds))
    elements.append(ev_table)


def _build_review_history(
    elements: list,
    car_data: dict,
    styles,
    content_width: float,
    audience: str = AUDIENCE_INTERNAL,
):
    """Review/approval history — activity timeline."""
    if _normalize_audience(audience) == AUDIENCE_EXTERNAL:
        return
    elements.append(Paragraph('Review / Approval History', styles['SectionHeading']))

    history = car_data.get('activity_history') or []
    if not history:
        elements.append(Paragraph('No activity recorded.', styles['BodyText10']))
        return

    cell = styles['CellText']
    col_widths = [35 * mm, content_width - 70 * mm, 35 * mm]
    table_data: list[list[Any]] = [['Date', 'Event', 'Performed By']]

    for event in history:
        history_event = _history_description_without_comment(event)
        table_data.append([
            _wrap(_fmt_date(event.get('performed_at')), cell),
            _wrap(history_event, cell),
            _wrap(_safe(event.get('performed_by_name', event.get('performed_by'))), cell),
        ])

    hist_table = Table(table_data, colWidths=col_widths)
    style_cmds = _base_table_style()
    _add_alternating_rows(style_cmds, len(table_data))
    hist_table.setStyle(TableStyle(style_cmds))
    elements.append(hist_table)


def _build_physical_verification(elements: list, car_data: dict, styles, content_width: float):
    """Physical verification section — only shown when the PV status is CLOSED."""
    pv = car_data.get('physical_verification')
    if not pv:
        return
    if str(pv.get('status') or '').upper() != 'CLOSED':
        return

    elements.append(Paragraph('Physical Verification', styles['SectionHeading']))

    cell = styles['CellText']
    verifier = _safe(pv.get('verifier_user_id') or pv.get('verifier_crew_id'))
    pv_data = [
        [_wrap('Status', styles['CellBold']),
         _wrap(_safe(pv.get('status_display', pv.get('status'))), cell)],
        [_wrap('Scheduled Date', styles['CellBold']),
         _wrap(_fmt_date(pv.get('scheduled_date')), cell)],
        [_wrap('Visit Date', styles['CellBold']),
         _wrap(_fmt_date(pv.get('visit_date')), cell)],
        [_wrap('Visit Port', styles['CellBold']),
         _wrap(_safe(pv.get('visit_port')), cell)],
        [_wrap('Verifier', styles['CellBold']),
         _wrap(verifier, cell)],
        [_wrap('Comments', styles['CellBold']),
         _wrap(_safe(pv.get('comments')), cell)],
        [_wrap('Closed By', styles['CellBold']),
         _wrap(_safe(pv.get('closed_by')), cell)],
        [_wrap('Closed At', styles['CellBold']),
         _wrap(_fmt_date(pv.get('closed_at')), cell)],
    ]

    pv_table = Table(pv_data, colWidths=[40 * mm, content_width - 40 * mm])
    pv_table.setStyle(TableStyle(_info_table_style()))
    elements.append(pv_table)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def _draw_footer(canvas, doc, car_number: str):
    """Draw page footer with page number and generation timestamp."""
    canvas.saveState()
    canvas.setFont(FONT_FAMILY, 8)
    canvas.setFillColor(COLOR_MUTED)

    page_num = canvas.getPageNumber()
    footer_text = f"{car_number}  |  Page {page_num}  |  Generated {datetime.now().strftime('%d %b %Y %H:%M')}"

    canvas.drawCentredString(PAGE_WIDTH / 2, 8 * mm, footer_text)
    canvas.restoreState()