from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
from typing import Any, Mapping, Protocol


SCHEMA_VERSION = "certs-ocr-v1"

OFFICE_CONTEXT = "office"
VESSEL_CONTEXT = "vessel"

AUTO_ACCEPT = "auto_accept"
GAP_FILL = "gap_fill"
MANUAL_ENTRY = "manual_entry"

PROCESSED = "processed"
MANUAL_ENTRY_REQUIRED = "manual_entry_required"

OFFICE_AUTO_ACCEPT_THRESHOLD = 0.80
VESSEL_AUTO_ACCEPT_THRESHOLD = 0.85
MANUAL_ENTRY_THRESHOLD = 0.60

REQUIRED_FIELDS = (
    "certificate_type",
    "issuing_authority",
    "vessel_name",
    "imo_number",
    "issue_date",
    "expiry_date",
    "certificate_number",
    "place_of_issue",
)

_TEXT_PATTERNS = {
    "certificate_type": re.compile(
        r"(?:certificate\s*(?:type|name)|type\s+of\s+certificate)\s*[:\-]\s*(?P<value>.+)",
        re.IGNORECASE,
    ),
    "issuing_authority": re.compile(
        r"(?:issuing\s+authority|authority)\s*[:\-]\s*(?P<value>.+)",
        re.IGNORECASE,
    ),
    "vessel_name": re.compile(
        r"(?:vessel\s+name|name\s+of\s+(?:ship|vessel)|ship\s+name)\s*[:\-]?\s*(?P<value>.+)",
        re.IGNORECASE,
    ),
    "imo_number": re.compile(r"\bimo\s*(?:no\.?|number)?\s*[:.\-]?\s*(?P<value>\d{7})\b", re.IGNORECASE),
    "issue_date": re.compile(r"(?:issue|issued|date\s+of\s+issue)\s+date\s*[:\-]\s*(?P<value>.+)", re.IGNORECASE),
    "expiry_date": re.compile(r"(?:expiry|expiration|valid\s+until)\s+date?\s*[:\-]?\s*(?P<value>.+)", re.IGNORECASE),
    "certificate_number": re.compile(
        r"(?:certificate\s*(?:no\.?|number)|cert(?:ificate)?\s*no\.?)\s*[:.\-]?\s*(?P<value>.+)",
        re.IGNORECASE,
    ),
    "place_of_issue": re.compile(r"place\s+of\s+issue\s*[:\-]\s*(?P<value>.+)", re.IGNORECASE),
}

_MONTH_ALIASES = {
    "jan": "January",
    "january": "January",
    "feb": "February",
    "february": "February",
    "mar": "March",
    "march": "March",
    "apr": "April",
    "april": "April",
    "may": "May",
    "jun": "June",
    "june": "June",
    "jul": "July",
    "july": "July",
    "aug": "August",
    "august": "August",
    "sep": "September",
    "sept": "September",
    "september": "September",
    "oct": "October",
    "october": "October",
    "nov": "November",
    "november": "November",
    "dec": "December",
    "december": "December",
}


class OcrPipelineError(RuntimeError):
    """Base exception for Certs OCR pipeline failures."""


class OcrEngineUnavailable(OcrPipelineError):
    """Raised when the selected OCR runtime cannot be used."""


@dataclass(frozen=True)
class OcrFieldCandidate:
    value: str | None
    confidence: float


@dataclass(frozen=True)
class OcrEngineOutput:
    raw_text: str
    mean_confidence: float
    fields: Mapping[str, OcrFieldCandidate]


@dataclass(frozen=True)
class OcrThresholds:
    office_auto_accept: float = OFFICE_AUTO_ACCEPT_THRESHOLD
    vessel_auto_accept: float = VESSEL_AUTO_ACCEPT_THRESHOLD
    manual_floor: float = MANUAL_ENTRY_THRESHOLD

    @classmethod
    def from_alert_config(cls, row: Mapping[str, Any] | None) -> "OcrThresholds":
        row = row or {}
        return cls(
            office_auto_accept=_threshold_value(
                row.get("ocr_threshold_office"),
                OFFICE_AUTO_ACCEPT_THRESHOLD,
            ),
            vessel_auto_accept=_threshold_value(
                row.get("ocr_threshold_vessel"),
                VESSEL_AUTO_ACCEPT_THRESHOLD,
            ),
            manual_floor=_threshold_value(
                row.get("ocr_threshold_manual_floor"),
                MANUAL_ENTRY_THRESHOLD,
            ),
        )


class OcrEngine(Protocol):
    engine_name: str

    def extract(self, source_path: str | Path) -> OcrEngineOutput:
        """Extract raw text and field candidates from a certificate document."""


def load_configured_ocr_thresholds() -> OcrThresholds:
    """Read FEAT-CERT-OCR-012 thresholds from settings, falling back to locked defaults."""
    try:
        from apps.certs.services.settings_repository import SettingsRepository

        rows = SettingsRepository().list_alert_configs()
    except Exception:
        return OcrThresholds()

    if not rows:
        return OcrThresholds()
    return OcrThresholds.from_alert_config(rows[0])


def classify_confidence(
    confidence: float,
    context: str,
    *,
    thresholds: OcrThresholds | None = None,
) -> str:
    """Apply D-CERT-106 / D-CERT-168 confidence thresholds."""
    normalized = max(0.0, min(float(confidence), 1.0))
    thresholds = thresholds or OcrThresholds()
    auto_accept_threshold = auto_accept_threshold_for_context(context, thresholds=thresholds)

    if normalized >= auto_accept_threshold:
        return AUTO_ACCEPT
    if normalized >= thresholds.manual_floor:
        return GAP_FILL
    return MANUAL_ENTRY


def auto_accept_threshold_for_context(
    context: str,
    *,
    thresholds: OcrThresholds | None = None,
) -> float:
    thresholds = thresholds or OcrThresholds()
    if context == OFFICE_CONTEXT:
        return thresholds.office_auto_accept
    if context == VESSEL_CONTEXT:
        return thresholds.vessel_auto_accept
    raise ValueError(f"Unknown OCR context: {context}")


def process_cert_pdf(
    source_path: str | Path,
    *,
    context: str = OFFICE_CONTEXT,
    engine: OcrEngine | None = None,
    thresholds: OcrThresholds | None = None,
) -> dict[str, object]:
    """Run the selected OCR engine and return the Certs v1 OCR payload.

    This does not write DB state. Phase 3 workers will persist this payload to
    vims_certs_pdf_blob.ocr_payload_json after blob storage is wired.
    """
    selected_engine = engine or TesseractOcrEngine()
    output = selected_engine.extract(source_path)
    detected_fields = dict(_parse_fields_from_text(output.raw_text, output.mean_confidence))
    detected_fields.update(output.fields)
    thresholds = thresholds or load_configured_ocr_thresholds()
    threshold = auto_accept_threshold_for_context(context, thresholds=thresholds)

    unprocessable = not output.raw_text.strip()
    payload_fields = {}
    for field_name in REQUIRED_FIELDS:
        candidate = detected_fields.get(field_name)
        confidence = candidate.confidence if candidate else 0.0
        raw_value = candidate.value if candidate else None
        mode = MANUAL_ENTRY if unprocessable else classify_confidence(confidence, context, thresholds=thresholds)
        payload_fields[field_name] = {
            "value": raw_value if mode != MANUAL_ENTRY else None,
            "raw_value": raw_value,
            "confidence": round(max(0.0, min(float(confidence), 1.0)), 3),
            "mode": mode,
            "threshold": threshold,
            "manual_floor": thresholds.manual_floor,
            "required": True,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "engine": selected_engine.engine_name,
        "context": context,
        "thresholds": {
            "auto_accept": threshold,
            "manual_floor": thresholds.manual_floor,
        },
        "status": MANUAL_ENTRY_REQUIRED if unprocessable else PROCESSED,
        "unprocessable": unprocessable,
        "raw_text": output.raw_text,
        "fields": payload_fields,
    }


def manual_entry_payload(
    *,
    context: str,
    engine_name: str,
    reason: str,
    thresholds: OcrThresholds | None = None,
) -> dict[str, Any]:
    thresholds = thresholds or load_configured_ocr_thresholds()
    threshold = auto_accept_threshold_for_context(context, thresholds=thresholds)
    return {
        "schema_version": SCHEMA_VERSION,
        "engine": engine_name,
        "context": context,
        "thresholds": {
            "auto_accept": threshold,
            "manual_floor": thresholds.manual_floor,
        },
        "status": MANUAL_ENTRY_REQUIRED,
        "unprocessable": True,
        "unprocessable_reason": reason,
        "raw_text": "",
        "fields": {
            field_name: {
                "value": None,
                "raw_value": None,
                "confidence": 0.0,
                "mode": MANUAL_ENTRY,
                "threshold": threshold,
                "manual_floor": thresholds.manual_floor,
                "required": True,
            }
            for field_name in REQUIRED_FIELDS
        },
    }


def _threshold_value(value: Any, fallback: float) -> float:
    if value in (None, ""):
        return fallback
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(0.0, min(numeric, 1.0))


class TesseractOcrEngine:
    """Tesseract-backed OCR adapter selected for Phase 0.7."""

    engine_name = "tesseract"

    def __init__(
        self,
        *,
        language: str = "eng",
        timeout_seconds: float = 30.0,
        max_pdf_pages: int = 5,
        pdf_render_scale: float = 2.4,
    ) -> None:
        self.language = language
        self.timeout_seconds = timeout_seconds
        self.max_pdf_pages = max(1, int(max_pdf_pages))
        self.pdf_render_scale = max(1.0, float(pdf_render_scale))

    def is_available(self) -> bool:
        return self.availability_error() is None

    def availability_error(self) -> str | None:
        try:
            import pytesseract
        except ImportError:
            return "Tesseract OCR Python package pytesseract is not installed."

        _configure_tesseract_command(pytesseract)
        try:
            pytesseract.get_tesseract_version()
        except Exception as exc:  # pytesseract raises several runtime-specific errors.
            return f"Tesseract OCR runtime is not available: {exc}"

        return None

    def extract(self, source_path: str | Path) -> OcrEngineOutput:
        path = Path(source_path)
        if path.suffix.lower() == ".pdf":
            try:
                return _extract_searchable_pdf_text(path)
            except OcrPipelineError:
                return _extract_pdf_pages_with_tesseract(path, self)

        try:
            import pytesseract
        except ImportError as exc:
            raise OcrEngineUnavailable(
                "Tesseract OCR Python package pytesseract is not installed."
            ) from exc

        _configure_tesseract_command(pytesseract)
        runtime_error = self.availability_error()
        if runtime_error:
            raise OcrEngineUnavailable(runtime_error)

        text = pytesseract.image_to_string(
            str(path),
            lang=self.language,
            timeout=self.timeout_seconds,
        )
        mean_confidence = _mean_tesseract_confidence(
            pytesseract.image_to_data(str(path), lang=self.language, timeout=self.timeout_seconds)
        )

        return OcrEngineOutput(
            raw_text=text,
            mean_confidence=mean_confidence,
            fields=dict(_parse_fields_from_text(text, mean_confidence)),
        )


def _parse_fields_from_text(
    raw_text: str,
    confidence: float,
) -> Mapping[str, OcrFieldCandidate]:
    fields = {}
    for line in raw_text.splitlines():
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        for field_name, pattern in _TEXT_PATTERNS.items():
            if field_name in fields:
                continue
            match = pattern.search(cleaned_line)
            if match:
                value = _clean_field_value(match.group("value"))
                if field_name in {"issue_date", "expiry_date"}:
                    value = _normalize_ocr_date_text(value)
                    if not _contains_ocr_date(value):
                        continue
                elif field_name == "certificate_number":
                    value = _clean_certificate_number(value)
                elif field_name == "place_of_issue":
                    value = _clean_place_of_issue(value)
                fields[field_name] = OcrFieldCandidate(
                    value=value,
                    confidence=confidence,
                )

    for field_name, value in _parse_common_certificate_layouts(raw_text).items():
        fields.setdefault(field_name, OcrFieldCandidate(value=value, confidence=confidence))

    return fields


def _configure_tesseract_command(pytesseract_module: Any) -> None:
    current = str(getattr(getattr(pytesseract_module, "pytesseract", None), "tesseract_cmd", "") or "")
    if current and Path(current).exists():
        return

    candidates = [
        os.environ.get("TESSERACT_CMD"),
        os.environ.get("TESSERACT_EXE"),
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        candidate_path = Path(str(candidate))
        if candidate_path.exists():
            pytesseract_module.pytesseract.tesseract_cmd = str(candidate_path)
            return


def _parse_common_certificate_layouts(raw_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    squashed = re.sub(r"\s+", "", raw_text).lower()

    if "koreanregister" in squashed:
        fields["issuing_authority"] = "Korean Register"
    elif "classnk" in squashed or "nipponkaijikyokai" in squashed:
        fields["issuing_authority"] = "ClassNK"
    elif "bureauveritas" in squashed:
        fields["issuing_authority"] = "Bureau Veritas"

    if "certificateofclassification" in squashed:
        fields["certificate_type"] = "Certificate of Classification"
    elif "breathingapparatus" in squashed:
        fields["certificate_type"] = "Breathing Apparatus"

    if "bluetech" in squashed and "marineservices" in squashed:
        fields.setdefault("issuing_authority", "BLUE TECH MARINE SERVICES LLC")

    regex_fields = {
        "certificate_number": [
            r"Certificate\s*No\.?\s*[:.]?\s*(?P<value>[A-Z0-9][A-Z0-9./\- ]+)",
            r"certificateNo\.?\s*[:.]?\s*(?P<value>[A-Z0-9][A-Z0-9./\- ]+)",
        ],
        "imo_number": [
            r"\bIMO\s*No\.?\s*[:.]?\s*(?P<value>\d{7})\b",
            r"\bIMO\s*Number\s*[:.]?\s*(?P<value>\d{7})\b",
            r"\bIMO\s*[:.]?\s*(?P<value>\d{7})\b",
        ],
        "vessel_name": [
            r"\bVessel\s+(?P<value>[^|\r\n]+)",
            r"Name\s*of\s*Ship\s*[:.]?\s*(?P<value>[^\r\n]+)",
            r"Vessel\s*Name\s*[:.]?\s*(?P<value>[^\r\n]+)",
            r"Name\s*of\s*Vessel\s*[:.]?\s*(?P<value>[^\r\n]+)",
        ],
        "expiry_date": [
            r"valid\s*until\s*(?P<value>\d{1,2}\s*[A-Za-z]{3,9}\s*\d{4})",
            r"Expiry\s*Date\s*[:.]?\s*(?P<value>[^\r\n]+)",
        ],
        "issue_date": [
            r"\bDate\s*[:.]?\s*(?P<value>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ],
        "place_of_issue": [
            r"Place\s+of\s+Service\s*\|?\s*(?P<value>[^\r\n]+)",
        ],
    }

    for field_name, patterns in regex_fields.items():
        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if not match:
                continue
            value = _clean_field_value(match.group("value"))
            if field_name == "vessel_name":
                value = _format_vessel_name(value)
            if field_name == "certificate_number":
                value = _clean_certificate_number(value)
            if field_name.endswith("_date"):
                value = _normalize_ocr_date_text(value)
                if not _contains_ocr_date(value):
                    continue
            if field_name == "place_of_issue":
                value = _clean_place_of_issue(value)
            fields.setdefault(field_name, value)
            break

    issued_match = re.search(
        r"Issued\s*at\s*(?:on)?\s*(?P<place>[A-Za-z][A-Za-z .'-]*?)\s*(?P<date>\d{1,2}\s*[A-Za-z]{3,9}\s*\d{4})",
        raw_text,
        re.IGNORECASE,
    )
    if issued_match:
        fields.setdefault("place_of_issue", _clean_place_of_issue(issued_match.group("place")))
        fields.setdefault("issue_date", _normalize_ocr_date_text(issued_match.group("date")))

    if "expiry_date" not in fields and re.search(r"valid\s+for[\s-]*one\.?\s+year\s+from\s+the\s+date\s+of\s+issue", raw_text, re.IGNORECASE):
        expiry_date = _add_year_to_ocr_date(fields.get("issue_date"))
        if expiry_date:
            fields["expiry_date"] = expiry_date

    return {key: value for key, value in fields.items() if value}


def _clean_field_value(value: str | None) -> str:
    text = str(value or "").strip()
    text = re.split(r"\bTHIS\s*IS\s*TO\s*CERTIFY\b|\bTHISISTOCERTIFY\b", text, flags=re.IGNORECASE)[0]
    text = re.sub(r"\s+", " ", text).strip(" :.-")
    return text


def _format_vessel_name(value: str) -> str:
    text = _clean_field_value(value).upper()
    text = re.sub(r"\s+", " ", text)
    for prefix in ("EAST", "WEST", "NORTH", "SOUTH"):
        if text.startswith(prefix) and len(text) > len(prefix) + 3 and not text.startswith(f"{prefix} "):
            return f"{prefix} {text[len(prefix):]}".strip()
    return text


def _clean_certificate_number(value: str) -> str:
    return _clean_field_value(value).strip("()[]{}")


def _clean_place_of_issue(value: str) -> str:
    text = _clean_field_value(value)
    text = re.sub(r"\s+\bon\b$", "", text, flags=re.IGNORECASE)
    return text.strip()


def _normalize_ocr_date_text(value: str) -> str:
    text = _clean_field_value(value)
    match = re.search(r"(?P<day>\d{1,2})\s*(?P<month>[A-Za-z]{3,9})\s*(?P<year>\d{4})", text)
    if not match:
        slash_match = re.search(r"(?P<day>\d{1,2})[/-](?P<month>\d{1,2})[/-](?P<year>\d{2,4})", text)
        if not slash_match:
            return text
        year = int(slash_match.group("year"))
        if year < 100:
            year += 2000
        try:
            parsed = datetime(year, int(slash_match.group("month")), int(slash_match.group("day")))
        except ValueError:
            return text
        return parsed.strftime("%d %B %Y").lstrip("0")
    month = _MONTH_ALIASES.get(match.group("month").lower(), match.group("month").capitalize())
    return f"{int(match.group('day'))} {month} {match.group('year')}"


def _contains_ocr_date(value: str) -> bool:
    return bool(re.search(r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", value))


def _add_year_to_ocr_date(value: str | None) -> str | None:
    text = _normalize_ocr_date_text(str(value or ""))
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            parsed = datetime.strptime(text, fmt)
            break
        except ValueError:
            parsed = None
    if parsed is None:
        return None
    try:
        next_year = parsed.replace(year=parsed.year + 1)
    except ValueError:
        next_year = parsed.replace(month=2, day=28, year=parsed.year + 1)
    return next_year.strftime("%d %B %Y").lstrip("0")


def _mean_tesseract_confidence(tsv_output: str) -> float:
    confidences = []
    for row in tsv_output.splitlines()[1:]:
        columns = row.split("\t")
        if len(columns) < 11:
            continue
        try:
            confidence = float(columns[10])
        except ValueError:
            continue
        if confidence >= 0:
            confidences.append(confidence / 100.0)

    if not confidences:
        return 0.0

    return sum(confidences) / len(confidences)


def _extract_pdf_pages_with_tesseract(path: Path, engine: TesseractOcrEngine) -> OcrEngineOutput:
    try:
        import pytesseract
    except ImportError as exc:
        raise OcrEngineUnavailable("Tesseract OCR Python package pytesseract is not installed.") from exc

    runtime_error = engine.availability_error()
    if runtime_error:
        raise OcrEngineUnavailable(runtime_error)

    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise OcrEngineUnavailable("pypdfium2 is required to rasterize scanned certificate PDFs.") from exc

    text_chunks: list[str] = []
    confidences: list[float] = []
    document = pdfium.PdfDocument(str(path))
    try:
        page_count = min(len(document), engine.max_pdf_pages)
        for page_index in range(page_count):
            page = document[page_index]
            try:
                bitmap = page.render(scale=engine.pdf_render_scale)
                image = bitmap.to_pil()
                text_chunks.append(
                    pytesseract.image_to_string(
                        image,
                        lang=engine.language,
                        timeout=engine.timeout_seconds,
                    )
                )
                confidence = _mean_tesseract_confidence(
                    pytesseract.image_to_data(
                        image,
                        lang=engine.language,
                        timeout=engine.timeout_seconds,
                    )
                )
                if confidence > 0:
                    confidences.append(confidence)
            finally:
                close = getattr(page, "close", None)
                if callable(close):
                    close()
    finally:
        close_document = getattr(document, "close", None)
        if callable(close_document):
            close_document()

    raw_text = "\n".join(chunk.strip() for chunk in text_chunks if chunk.strip()).strip()
    if not raw_text:
        raise OcrPipelineError("Certificate PDF OCR produced no readable text.")

    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return OcrEngineOutput(
        raw_text=raw_text,
        mean_confidence=mean_confidence,
        fields=dict(_parse_fields_from_text(raw_text, mean_confidence)),
    )


def _extract_searchable_pdf_text(path: Path) -> OcrEngineOutput:
    try:
        from PyPDF2 import PdfReader
    except ImportError as exc:
        raise OcrEngineUnavailable("PyPDF2 is required to read searchable certificate PDFs.") from exc

    reader = PdfReader(str(path))
    raw_text = "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    if not raw_text:
        raise OcrPipelineError(
            "Certificate PDF has no searchable text layer; PDF page rasterization lands with the OCR worker."
        )
    return OcrEngineOutput(
        raw_text=raw_text,
        mean_confidence=0.95,
        fields=dict(_parse_fields_from_text(raw_text, 0.95)),
    )
