from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import tempfile
from typing import Any, Protocol


SCHEMA_VERSION = "certs-ocr-v1"
DEFAULT_OCR_ENGINE_NAME = "paddleocr"

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
CERTIFICATE_OCR_MAX_PDF_PAGES = 2
CERTIFICATE_OCR_PDF_RENDER_SCALE = 1.5
CERTIFICATE_OCR_TEXT_DET_LIMIT_SIDE_LEN = 960
CERTIFICATE_OCR_TEXT_RECOGNITION_BATCH_SIZE = 64
CERTIFICATE_OCR_TEXT_DETECTION_MODEL_NAME = "PP-OCRv4_mobile_det"
CERTIFICATE_OCR_TEXT_RECOGNITION_MODEL_NAME = "en_PP-OCRv4_mobile_rec"
_DEFAULT_CERTIFICATE_OCR_ENGINE: OcrEngine | None = None

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
    selected_engine = engine or default_certificate_ocr_engine()
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


def default_certificate_ocr_engine() -> OcrEngine:
    global _DEFAULT_CERTIFICATE_OCR_ENGINE
    if _DEFAULT_CERTIFICATE_OCR_ENGINE is None:
        _DEFAULT_CERTIFICATE_OCR_ENGINE = PaddleOcrEngine(
            max_pdf_pages=CERTIFICATE_OCR_MAX_PDF_PAGES,
            pdf_render_scale=CERTIFICATE_OCR_PDF_RENDER_SCALE,
            text_detection_model_name=CERTIFICATE_OCR_TEXT_DETECTION_MODEL_NAME,
            text_recognition_model_name=CERTIFICATE_OCR_TEXT_RECOGNITION_MODEL_NAME,
            text_det_limit_side_len=CERTIFICATE_OCR_TEXT_DET_LIMIT_SIDE_LEN,
            text_recognition_batch_size=CERTIFICATE_OCR_TEXT_RECOGNITION_BATCH_SIZE,
        )
    return _DEFAULT_CERTIFICATE_OCR_ENGINE


def _threshold_value(value: Any, fallback: float) -> float:
    if value in (None, ""):
        return fallback
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(0.0, min(numeric, 1.0))


class PaddleOcrEngine:
    """PaddleOCR-backed OCR adapter selected for Certs document OCR."""

    engine_name = DEFAULT_OCR_ENGINE_NAME

    def __init__(
        self,
        *,
        language: str | None = None,
        max_pdf_pages: int | None = 5,
        pdf_render_scale: float = 2.4,
        ocr_version: str | None = None,
        text_detection_model_name: str | None = None,
        text_recognition_model_name: str | None = None,
        text_det_limit_side_len: int | None = None,
        text_recognition_batch_size: int | None = None,
    ) -> None:
        self.language = language
        self.max_pdf_pages = None if max_pdf_pages is None else max(1, int(max_pdf_pages))
        self.pdf_render_scale = max(1.0, float(pdf_render_scale))
        self.ocr_version = ocr_version
        self.text_detection_model_name = text_detection_model_name
        self.text_recognition_model_name = text_recognition_model_name
        self.text_det_limit_side_len = (
            None if text_det_limit_side_len is None else max(1, int(text_det_limit_side_len))
        )
        self.text_recognition_batch_size = (
            None if text_recognition_batch_size is None else max(1, int(text_recognition_batch_size))
        )
        self._runner: Any | None = None

    def is_available(self) -> bool:
        return self.availability_error() is None

    def availability_error(self) -> str | None:
        try:
            self._paddle_ocr_class()
        except ImportError:
            return "PaddleOCR Python package paddleocr is not installed."
        except OcrEngineUnavailable as exc:
            return str(exc)

        return None

    def extract(self, source_path: str | Path) -> OcrEngineOutput:
        path = Path(source_path)
        if path.suffix.lower() == ".pdf":
            try:
                return _extract_searchable_pdf_text(path)
            except OcrPipelineError:
                return _extract_pdf_pages_with_paddleocr(path, self)

        text, mean_confidence = self.extract_image_text(path)
        if not text.strip():
            raise OcrPipelineError("Certificate image OCR produced no readable text.")

        return OcrEngineOutput(
            raw_text=text,
            mean_confidence=mean_confidence,
            fields=dict(_parse_fields_from_text(text, mean_confidence)),
        )

    def extract_image_text(self, source_path: str | Path) -> tuple[str, float]:
        return _predict_with_paddleocr(source_path, self)

    def _predict(self, source_path: str | Path) -> Any:
        runner = self._ocr_runner()
        source = str(source_path)
        try:
            return runner.predict(source)
        except TypeError:
            try:
                return runner.predict(input=source)
            except TypeError:
                return runner.ocr(source, cls=False)
        except AttributeError:
            return runner.ocr(source, cls=False)

    def _ocr_runner(self) -> Any:
        if self._runner is not None:
            return self._runner

        PaddleOCR = self._paddle_ocr_class()
        kwargs: dict[str, Any] = {
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        }
        if self.language:
            kwargs["lang"] = self.language
        if self.ocr_version:
            kwargs["ocr_version"] = self.ocr_version
        if self.text_detection_model_name:
            kwargs["text_detection_model_name"] = self.text_detection_model_name
        if self.text_recognition_model_name:
            kwargs["text_recognition_model_name"] = self.text_recognition_model_name
        if self.text_det_limit_side_len is not None:
            kwargs["text_det_limit_side_len"] = self.text_det_limit_side_len
        if self.text_recognition_batch_size is not None:
            kwargs["text_recognition_batch_size"] = self.text_recognition_batch_size
        try:
            self._runner = PaddleOCR(**kwargs)
        except TypeError:
            fallback_kwargs: dict[str, Any] = {"use_angle_cls": False}
            if self.language:
                fallback_kwargs["lang"] = self.language
            try:
                self._runner = PaddleOCR(**fallback_kwargs)
            except Exception as exc:
                raise OcrEngineUnavailable(f"PaddleOCR runtime is not available: {exc}") from exc
        except Exception as exc:
            raise OcrEngineUnavailable(f"PaddleOCR runtime is not available: {exc}") from exc
        return self._runner

    @staticmethod
    def _paddle_ocr_class() -> Any:
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise OcrEngineUnavailable("PaddleOCR Python package paddleocr is not installed.") from exc
        return PaddleOCR


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
                if field_name == "certificate_number" and re.search(r"approval\s+no|certificate\s+no\.?\s*of\s*approval", cleaned_line, re.IGNORECASE):
                    continue
                value = _clean_field_value(match.group("value"))
                if field_name in {"issue_date", "expiry_date"}:
                    value = _normalize_ocr_date_text(value)
                    if not _contains_ocr_date(value):
                        continue
                elif field_name == "vessel_name":
                    value = _format_vessel_name(value)
                    if not _looks_like_vessel_name(value):
                        continue
                elif field_name == "certificate_number":
                    value = _clean_certificate_number(value)
                elif field_name == "place_of_issue":
                    value = _clean_place_of_issue(value)
                if not value:
                    continue
                fields[field_name] = OcrFieldCandidate(
                    value=value,
                    confidence=confidence,
                )

    for field_name, value in _parse_common_certificate_layouts(raw_text).items():
        fields.setdefault(field_name, OcrFieldCandidate(value=value, confidence=confidence))

    return fields


def _parse_common_certificate_layouts(raw_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    squashed = re.sub(r"\s+", "", raw_text).lower()
    issuing_authority = _parse_issuing_authority(raw_text)
    if issuing_authority:
        fields["issuing_authority"] = issuing_authority

    certificate_type = _parse_certificate_type(raw_text)
    if certificate_type:
        fields["certificate_type"] = certificate_type

    if "bluetech" in squashed and "marineservices" in squashed:
        fields.setdefault("issuing_authority", "BLUE TECH MARINE SERVICES LLC")

    fields.update(_parse_vessel_identity(raw_text))
    certificate_number = _parse_stacked_certificate_number(raw_text)
    if certificate_number:
        fields["certificate_number"] = certificate_number
    fields.update(_parse_stacked_issue_expiry_dates(raw_text))
    compact_dates = _parse_compact_certificate_dates(raw_text)
    fields.update({key: value for key, value in compact_dates.items() if key not in fields})
    range_dates = _parse_certificate_date_ranges(raw_text)
    fields.update({key: value for key, value in range_dates.items() if key not in fields})

    regex_fields = {
        "certificate_number": [
            r"Certificate\s*No\.?\s*[:.]?\s*(?P<value>[A-Z0-9][A-Z0-9_./\- ]+)",
            r"certificateNo\.?\s*[:.]?\s*(?P<value>[A-Z0-9][A-Z0-9_./\- ]+)",
            r"\bNo\.?\s*[:.]?\s*(?P<value>[A-Z]{1,4}\d[A-Z0-9_\-/]{4,})\b",
            r"\bPOLICY\s+REFERENCE\s*[:.]?\s*(?P<value>[A-Z0-9_\-/]{5,})\b",
            r"\bPolicy\s*No\.?\s*[:.]?\s*(?P<value>\d{6,})\b",
            r"\b(?P<value>\d{6,})\s+No\.\b",
            r"\bNTVRP\s*#(?P<value>\d{4,})\b",
        ],
        "imo_number": [
            r"\bIMO\s*No\.?\s*[:.]?\s*(?P<value>\d{7})\b",
            r"\bIMO\s*Number\s*[:.]?\s*(?P<value>\d{7})\b",
            r"\bIMO\s*[:.]?\s*(?P<value>\d{7})\b",
            r"\bIMO(?P<value>\d{7})\b",
        ],
        "vessel_name": [
            r"Name\s*of\s*Ship\s*[:.]?\s*(?P<value>[^\r\n]+)",
            r"Vessel\s*Name\s*[:.]?\s*(?P<value>[^\r\n]+)",
            r"Name\s*of\s*Vessel\s*[:.]?\s*(?P<value>[^\r\n]+)",
        ],
        "expiry_date": [
            r"valid\s*until\s*(?P<value>\d{1,2}\s*[A-Za-z]{3,9}\s*\d{4})",
            r"valid\s*until\s*(?P<value>[A-Za-z]{3,9}\.?,?\s+\d{1,2},?\s+\d{4})",
            r"Expiry\s*Date\s*[:.]?\s*(?P<value>[^\r\n]+)",
        ],
        "issue_date": [
            r"\bDate\s*[:.]?\s*(?P<value>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"\bDate\s*[:.]?\s*(?P<value>\d{1,2}\s+[A-Za-z]{3,9}\.?,?\s+\d{4})",
            r"\bDate\s*[:.]?\s*(?P<value>[A-Za-z]{3,9}\.?,?\s+\d{1,2},?\s+\d{4})",
            r"\b[A-Za-z .'-]+,\s*(?P<value>\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})\s+\d+\s+Page\b",
            r"\bNTVRP\s*#\d{4,}\s+on\s+(?P<value>[A-Za-z]{3,9}\.?,?\s+\d{1,2},?\s+\d{4})",
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
                if not _looks_like_vessel_name(value):
                    continue
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


def _compact_ocr_text(raw_text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", raw_text.lower())


def _parse_issuing_authority(raw_text: str) -> str | None:
    compact = _compact_ocr_text(raw_text)
    alias_rules = (
        (("dnvuklimited", "dnvukltd"), "DNV UK Limited"),
        (("dnvas", "wwwdnvcom", "dnvlocalunit"), "DNV AS"),
        (("koreanregister", "koreanregisterofshipping"), "Korean Register"),
        (("classnk", "nipponkaijikyokai"), "ClassNK"),
        (("bureauveritas",), "Bureau Veritas"),
        (("assuranceforeningenskuld", "skuldmutualprotection"), "Assuranceforeningen Skuld"),
        (("liberiamaritimeauthority", "republicofliberia"), "Liberia Maritime Authority"),
        (("chinaclassificationsociety",), "China Classification Society"),
        (("yangzhouxintianherope",), "Yangzhou Xintianhe Rope Cable Co., Ltd."),
        (("vikinglifesavingequipment", "vikingservicebase"), "VIKING Life-Saving Equipment"),
        (("priceforbesbrokingasia",), "Price Forbes Broking Asia Pte Ltd"),
        (("westerncanadamarineresponsecorporation",), "Western Canada Marine Response Corporation"),
        (("panamamaritimeauthority",), "Panama Maritime Authority"),
        (("resolvesalvagefire",), "Resolve Salvage & Fire"),
        (("gallaghermarinesystems",), "Gallagher Marine Systems"),
        (
            ("maritimesafetyadministrationofthepeoplesrepublicofchina", "chinamsa"),
            "Maritime Safety Administration of the People's Republic of China",
        ),
        (("indianregisterofshipping", "irclass"), "Indian Register of Shipping"),
        (("lloydsregister",), "Lloyd's Register"),
        (("americanbureauofshipping",), "American Bureau of Shipping"),
        (("marinedepartment",), "Marine Department"),
        (("castrol",), "Castrol"),
    )
    for needles, authority in alias_rules:
        if any(needle in compact for needle in needles):
            return authority

    normalized = re.sub(r"\s+", " ", raw_text).strip()
    explicit_rules = (
        (r"\bissued\s+by\s+KR\b", "Korean Register"),
        (r"\bissued\s+by\s+CCS\b", "China Classification Society"),
        (r"\bissued\s+by\s+DNV\s+AS\b", "DNV AS"),
        (r"\bissued\s+by\s+DNV\s+UK\s+(?:Limited|Ltd\.?)\b", "DNV UK Limited"),
        (r"\bfor\s+DNV\s+AS\b", "DNV AS"),
        (r"\bfor\s+DNV\s+UK\s+Ltd\.?\b", "DNV UK Limited"),
    )
    for pattern, authority in explicit_rules:
        if re.search(pattern, normalized, re.IGNORECASE):
            return authority

    label_patterns = (
        r"\bIssued\s+By\s*[:.]?\s*(?P<value>[^\r\n]+)",
        r"\bIssued\s+by\s+the\s+Company\s+or\s+Master\s*[:.]?\s*(?P<value>[^\r\n]+)",
        r"\bThis\s+Certificate\s+(?:has\s+been\s+)?issued\s+by\s+(?P<value>[^\r\n]+)",
    )
    for pattern in label_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE)
        if not match:
            continue
        value = _clean_issuing_authority_value(match.group("value"))
        if value:
            return value
    return None


def _clean_issuing_authority_value(value: str) -> str | None:
    text = _clean_field_value(value)
    text = re.split(
        r"\s+\b(?:under\s+the\s+authority|based\s+on|on\s+behalf\s+of|in\s+accordance|as\s+meeting|which\s+has)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    if ":" in text and re.search(r"\b(?:company|master|issued|approved)\b", text, re.IGNORECASE):
        text = text.rsplit(":", 1)[-1]
    text = text.strip(" :.-")
    if not text or not re.search(r"[A-Za-z]", text):
        return None
    if len(text) > 100:
        return None
    if re.search(r"\b(?:administration\s+as\s+meeting|medical\s+officer|manning\s+agent|seafarer)\b", text, re.IGNORECASE):
        return None
    compact = _compact_ocr_text(text)
    normalized_names = {
        "dnvas": "DNV AS",
        "dnvuklimited": "DNV UK Limited",
        "dnvukltd": "DNV UK Limited",
        "kr": "Korean Register",
        "ccs": "China Classification Society",
    }
    return normalized_names.get(compact, text)


def _parse_certificate_type(raw_text: str) -> str | None:
    compact = _compact_ocr_text(raw_text)
    type_rules = (
        ("certificateofclassification", "Certificate of Classification"),
        ("magneticcompassdeviationstable", "Magnetic Compass Deviations Table"),
        ("shipenergyefficiencymanagementplan", "Ship Energy Efficiency Management Plan"),
        ("eexitechnicalfile", "EEXI Technical File"),
        ("agreementforshippollutionresponse", "Agreement for Ship Pollution Response"),
        ("vesselprefireplanreceiptcertificationofacceptability", "Vessel Pre-Fire Plan Receipt & Certification"),
        ("spillresponsecontractcertification", "Spill Response Contract Certification"),
        ("ballastwatermanagementplanapproval", "Ballast Water Management Plan Approval"),
        ("quarantinevessel", "Quarantine - Vessel"),
        ("declarationofcompanysecurityofficer", "Declaration of Company Security Officer"),
        ("servicingcertificateforfirefightingappliances", "Servicing Certificate for Fire Fighting Appliances"),
        ("servic1ngcertificateforfirefight1ngappliances", "Servicing Certificate for Fire Fighting Appliances"),
        ("registerofliftingappliancesandloosegear", "Register of Lifting Appliances and Loose Gear"),
        ("lubricantoilanalysis", "Lubricant Oil Analysis Report"),
        ("diagnosissatisfactoryforfurtherservice", "Lubricant Oil Analysis Report"),
        ("shipsanitationcontrolexemptioncertificate", "Ship Sanitation Control Exemption Certificate"),
        ("declarationofmaritimelabourcompliancepartii", "Declaration of Maritime Labour Compliance - Part II"),
        ("hullandmachineryinsurance", "Hull and Machinery Insurance"),
        ("shipnonbulkoilmembershipagreement", "Ship Non-Bulk Oil Membership Agreement"),
        ("juandefucashipnonbulkoilmembershipagreement", "Juan de Fuca Ship Non-Bulk Oil Membership Agreement"),
        ("surveyreport", "Survey Report"),
        ("statementofcompliancewiththeinternationalmaritimesolidbulkcargoescode", "Statement of Compliance - IMSBC Code"),
        ("statementofcomplianceforinternationalenergyefficiency", "Statement of Compliance - International Energy Efficiency"),
        ("statementofcomplianceforinternationalantifoulingsystem", "Statement of Compliance - Anti-Fouling System"),
        ("statementofcompliancedrydockinspectionfortheusepavesselgeneralpermit", "Statement of Compliance - US EPA VGP Dry Dock Inspection"),
        ("fueloilconsumptionreportingandoperationalcarbonintensityrating", "Statement of Compliance - Fuel Oil Consumption Reporting"),
        ("documentofcompliance", "Document of Compliance"),
        ("certificatestatementofcompliance", "Statement of Compliance"),
        ("certificateofinsuranceorotherfinancialsecurityinrespectofshipownersliability", "MLC Shipowners Liability Insurance Certificate"),
        ("certificateofinsuranceorotherfinancialsecurityinrespectofseafarerrepatriation", "MLC Repatriation Insurance Certificate"),
        ("certificateofinsuranceorotherfinancialsecurityinrespectofcivilliabilityforbunkeroilpollutiondamage", "Bunker Civil Liability Insurance Certificate"),
        ("certificatefurnishedasevidenceofinsurancepursuanttoarticle7oftheinternationalconventiononcivilliabilityforbunkeroilpollutiondamage", "Bunker Civil Liability Insurance Certificate"),
        ("certificateofinsuranceorotherfinancialsecurityinrespectofliabilityfortheremovalofwrecks", "Wreck Removal Liability Insurance Certificate"),
        ("certificatefurnishedasevidenceofinsurancepursuanttoarticle12ofthenairobiinternationalconventionontheremovalofwrecks", "Wreck Removal Liability Insurance Certificate"),
        ("protectionindemnityinsurance", "Protection & Indemnity Insurance"),
        ("protectionandindemnityinsurance", "Protection & Indemnity Insurance"),
        ("freightdemurragedefencecover", "Freight, Demurrage & Defence Cover"),
        ("remoteassessmentconsultationracexercisecertificateofplanaccreditation", "Certificate of Plan Accreditation"),
        ("certificateofplanaccreditation", "Certificate of Plan Accreditation"),
        ("certificateofproduct", "Certificate of Product"),
        ("certificateofreinspection", "Certificate of Re-Inspection"),
        ("registerofshipsliftingappliancesandcargohandlinggear", "Register of Ship's Lifting Appliances and Cargo Handling Gear"),
        ("certificateoftestandthoroughexaminationofliftingappliances", "Certificate of Test and Thorough Examination of Lifting Appliances"),
        ("certificateforloadinginstrument", "Certificate for Loading Instrument"),
        ("breathingapparatus", "Breathing Apparatus"),
    )
    for needle, certificate_type in type_rules:
        if needle in compact:
            return certificate_type
    header_lines = [_clean_field_value(line) for line in raw_text.splitlines() if line.strip()]
    for line in header_lines[:12]:
        if re.search(r"\b(?:certificate|statement|document|register)\b", line, re.IGNORECASE):
            return _clean_field_value(line).title()
    return None


def _parse_vessel_identity(raw_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    text = re.sub(r"\s+", " ", raw_text)
    compact = re.sub(r"\s+", "", raw_text)

    imo_match = re.search(r"I\s+M\s+O\s+NO\.?\s*[:.]?\s*(?P<value>\d{7})(?!\d)", text, re.IGNORECASE)
    if not imo_match:
        imo_match = re.search(r"I\s*M\s*O\s*(?:No\.?|Number)?(?:\s*/\s*Asset)?\s*[:.]?\s*(?P<value>\d{7})(?!\d)", text, re.IGNORECASE)
    if not imo_match:
        spaced_imo_match = re.search(r"I\s*M\s*O\s*(?:No\.?|Number)?(?:\s*/\s*Asset)?\s*[:.]?\s*(?P<value>(?:\d\s*){7,})", text, re.IGNORECASE)
        if spaced_imo_match:
            imo_digits = re.sub(r"\D", "", spaced_imo_match.group("value"))
            if len(imo_digits) >= 7:
                fields["imo_number"] = imo_digits[:7]
    if not imo_match:
        imo_match = re.search(r"\bIMO(?P<value>\d{7})(?!\d)", compact, re.IGNORECASE)
    if not imo_match:
        imo_match = re.search(r"\bHSB\d+\s+(?P<value>\d{7})(?!\d)", text, re.IGNORECASE)
    if imo_match and "imo_number" not in fields:
        fields["imo_number"] = imo_match.group("value")

    table_vessel_names: list[str] = []
    for line in raw_text.splitlines():
        clean_line = _clean_field_value(line)
        table_match = re.match(r"(?P<value>[A-Za-z][A-Za-z .'-]{3,}?)\s+\d{7}\s+\d{4}\s+[\d,]+", clean_line)
        if table_match:
            vessel_name = _format_vessel_name(table_match.group("value"))
            if _looks_like_vessel_name(vessel_name):
                table_vessel_names.append(vessel_name)
    unique_table_vessel_names = sorted(set(table_vessel_names))
    if len(unique_table_vessel_names) == 1:
        fields["vessel_name"] = unique_table_vessel_names[0]

    if "vessel_name" in fields:
        return fields

    vessel_patterns = (
        r"Ships?\s*Name\s*[:.]?\s*(?P<value>[A-Z][A-Z0-9 .'-]{2,}?)(?:\s+Call\s*Sign|\s+GT\b|\s+Sea\s+Cond\b|$)",
        r"Vessel\s*/\s*Asset\s*[:.]?\s*(?P<value>[A-Z][A-Z0-9 .'-]{2,}?)(?:\s+Sampling\s+Point\b|\s+Machinery\b|$)",
        r"\bVessel\s*[:.]?\s*(?P<value>[A-Z][A-Z0-9 .'-]{2,}?)(?:\s+IMO\b|\s+Prepared\b|\s+Flag\b|$)",
        r"Nom\s+du\s+navire\s*:?\s*(?P<value>[A-Z][A-Z0-9 .'-]{2,}?)(?:\s*Register\s+No\b|\s+N[°o]\b|\s+Call\s+Sign\b|$)",
        r"Name\s*of\s*Ship\s*[:.]?\s*(?P<value>[A-Z][A-Z0-9 .'-]{2,}?)(?:\s+Class\s*No\.?|\s+Distinctive\b|\s+Port\s+of\b|\s+Owner\b|\s+IMO\b|\s+Call\s*Sign|$)",
        r"NameofShip\s*[:.]?\s*(?P<value>[A-Z][A-Z0-9 .'-]{2,}?)(?:ClassNo|Distinctive|Portof|IMONumber|$)",
        r"NAME\s+OF\s+THE\s+SHIP\s*[:.]?\s*(?P<value>[A-Z0-9][A-Z0-9 .'-]{2,}?)(?:\s+OFFICIAL\s+NUMBER\b|\s+CALL\s+SIGN\b|$)",
        r"(?P<value>[A-Z][A-Z ]{3,})\s+Name\s*:\s*This\s+is\s+to\s+certify",
        r"\d{7}\s*(?P<value>[A-Z][A-Z ]{3,})\s+Name\s+of\s+Ship\b",
        r"(?P<value>[A-Z][A-Z ]{3,})\s+HSB\d+\s+\d{7}\b",
        r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}(?P<value>[A-Z][A-Z ]{3,})\d{7}\b",
        r"\bMV\s+(?P<value>[A-Z][A-Z ]{3,})(?:,|\s+IMO\b|$)",
    )
    for pattern in vessel_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            vessel_name = _format_vessel_name(match.group("value"))
            if _looks_like_vessel_name(vessel_name):
                fields["vessel_name"] = vessel_name
                break
        if "vessel_name" in fields:
            break
    return fields


def _parse_compact_certificate_dates(raw_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    readable_text = re.sub(r"\s+", " ", raw_text)
    compact_text = re.sub(r"\s+", "", raw_text)

    expiry_date = _extract_date_after_label(
        (readable_text, compact_text),
        labels=(
            r"certificates?\s+(?:is\s+)?issued\s+until",
            r"issued\s+until",
            r"valid\s*until",
            r"valid\s*(?:to|till|through)",
            r"valid\s+up\s+to",
            r"validity\s*until",
            r"not\s+valid\s+after",
            r"expires?\s*(?:on)?",
            r"expiry\s*date",
        ),
        window_size=260,
    )
    if expiry_date:
        fields["expiry_date"] = expiry_date

    issue_date = _extract_date_after_label(
        (readable_text, compact_text),
        labels=(r"date\s*of\s*issue", r"issue\s*date", r"issued\s*at\s*(?:on)?"),
        window_size=180,
    )
    if issue_date:
        fields["issue_date"] = issue_date

    return fields


def _parse_certificate_date_ranges(raw_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    text = re.sub(r"\s+", " ", raw_text)
    date = _ocr_date_regex_fragment()
    range_patterns = (
        rf"(?:Duration\s+of\s+Security|Period\s+of\s+validity\s+of\s+the\s+financial\s+security)\s*[:.]?\s*(?:noon\s+GMT\s+)?(?P<start>{date})\s*(?:to|-)\s*(?:noon\s+GMT\s+)?(?P<end>{date})",
        rf"(?:effective\s+as\s+from|effective\s+from)\s*[:.]?\s*(?:noon\s+GMT\s+)?(?P<start>{date})\s*(?:to|-)\s*(?:noon\s+GMT\s+)?(?P<end>{date})",
        rf"\bPERIOD\s*:\s*From\s*:\s*(?P<start>{date})(?:\s+\d{{2}}:\d{{2}})?\s*(?:to|-)\s*(?P<end>{date})",
        rf"\bfrom\s+(?P<start>{date})\s*(?:to|-)\s*(?P<end>{date})",
    )
    for pattern in range_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        start = _normalize_ocr_date_text(match.group("start"))
        end = _normalize_ocr_date_text(match.group("end"))
        if _contains_ocr_date(start):
            fields["issue_date"] = start
        if _contains_ocr_date(end):
            fields["expiry_date"] = end
        return fields
    return fields


def _extract_date_after_label(texts: tuple[str, ...], *, labels: tuple[str, ...], window_size: int) -> str | None:
    for text in texts:
        for label in labels:
            for match in re.finditer(label, text, flags=re.IGNORECASE):
                window = text[match.end() : match.end() + window_size]
                date_value = _extract_first_ocr_date(window)
                if date_value:
                    return date_value
    return None


def _extract_first_ocr_date(value: str) -> str | None:
    date_pattern = re.compile(_ocr_date_regex_fragment(), re.IGNORECASE)
    for match in date_pattern.finditer(value):
        normalized = _normalize_ocr_date_text(match.group(0))
        if _contains_ocr_date(normalized):
            return normalized
    return None


def _ocr_date_regex_fragment() -> str:
    return (
        r"(?<!\d)\d{4}-\d{1,2}-\d{1,2}(?!\d)"
        r"|(?<!\d)\d{4}年\d{1,2}月\d{1,2}日"
        r"|(?<!\d)20\d{6}(?!\d)"
        r"|(?<!\d)\d{1,2}(?:st|nd|rd|th)?[\s-]*[A-Za-z]{3,9}\.?,?[\s-]*\d{4}"
        r"|(?<!\d)[A-Za-z]{3,9}\.?,?\s+\d{1,2},?\s+\d{4}"
        r"|(?<!\d)\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?!\d)"
        r"|(?<!\d)\d{1,2}-\d{4}(?!\d)"
    )


def _parse_stacked_certificate_number(raw_text: str) -> str | None:
    lines = [_clean_field_value(line) for line in raw_text.splitlines()]
    lines = [line for line in lines if line]
    for index, line in enumerate(lines):
        if not re.fullmatch(r"certificate\s*(?:no\.?|number)", line, flags=re.IGNORECASE):
            continue
        for candidate in lines[index + 1 : index + 10]:
            if _is_stacked_certificate_number_label(candidate):
                continue
            if _is_stacked_certificate_number_value(candidate):
                return _clean_certificate_number(candidate)
    return None


def _parse_stacked_issue_expiry_dates(raw_text: str) -> dict[str, str]:
    lines = [_clean_field_value(line) for line in raw_text.splitlines()]
    lines = [line for line in lines if line]
    for index, line in enumerate(lines):
        if not re.search(r"\bdate\s+of\s+issue\b", line, flags=re.IGNORECASE):
            continue
        window = lines[index + 1 : index + 14]
        expiry_label_index = next(
            (
                offset
                for offset, candidate in enumerate(window)
                if re.search(r"\bdate\s+of\s+expir(?:y|ation)\b", candidate, flags=re.IGNORECASE)
            ),
            None,
        )
        date_candidates = [
            (offset, date_value)
            for offset, candidate in enumerate(window)
            if (date_value := _extract_stacked_date_value(candidate))
        ]
        if expiry_label_index is None:
            if len(date_candidates) >= 2:
                return {
                    "issue_date": date_candidates[0][1],
                    "expiry_date": date_candidates[1][1],
                }
            continue

        before_expiry_label = [date for offset, date in date_candidates if offset < expiry_label_index]
        after_expiry_label = [date for offset, date in date_candidates if offset > expiry_label_index]
        if before_expiry_label and after_expiry_label:
            return {
                "issue_date": before_expiry_label[0],
                "expiry_date": after_expiry_label[0],
            }
        if len(after_expiry_label) >= 2:
            return {
                "issue_date": after_expiry_label[0],
                "expiry_date": after_expiry_label[1],
            }
    return {}


def _extract_stacked_date_value(value: str) -> str | None:
    text = _clean_field_value(value)
    iso_match = re.search(r"\b(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b", text)
    if iso_match:
        try:
            return datetime(
                int(iso_match.group("year")),
                int(iso_match.group("month")),
                int(iso_match.group("day")),
            ).date().isoformat()
        except ValueError:
            return None
    normalized = _normalize_ocr_date_text(text)
    return normalized if _contains_ocr_date(normalized) else None


def _is_stacked_certificate_number_label(value: str) -> bool:
    return bool(
        re.search(
            r"\b(?:works?\s+order|product\s+description|valid\s+for|serial\s+number|date\s+of|calibration|details)\b",
            value,
            re.IGNORECASE,
        )
    )


def _is_stacked_certificate_number_value(value: str) -> bool:
    text = _clean_certificate_number(value)
    if len(text) < 4 or not re.search(r"\d", text):
        return False
    if re.search(r"[a-z]", text):
        return False
    if _contains_ocr_date(text):
        return False
    return bool(re.fullmatch(r"[A-Z0-9][A-Z0-9./\- ]{3,}", text))


def _clean_field_value(value: str | None) -> str:
    text = str(value or "").strip()
    text = re.split(r"\bTHIS\s*IS\s*TO\s*CERTIFY\b|\bTHISISTOCERTIFY\b", text, flags=re.IGNORECASE)[0]
    text = re.sub(r"\s+", " ", text).strip(" :.-")
    return text


def _format_vessel_name(value: str) -> str:
    text = _clean_field_value(value).upper()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    text = re.sub(r"^\s*NOM\s+DU\s+NAVIRE\s*:?\s*", "", text)
    text = re.sub(r"\b5F\b", "SF", text)
    text = re.sub(r"\bOARICA\b", "DARIKA", text)
    text = re.sub(r"\bCHAL\s+ISA\b", "CHALISA", text)
    text = re.split(
        r"\s+EX\.\s*NAME\b|\s+CLASS(?:IFICATION)?\s*(?:NO\.?|NUMBER)\b|\s+IMO\s*(?:NO\.?|NUMBER)?\b|\s+CALL\s*SIGN\b.*$|\s+FLAG\b.*$|\s+REGISTER\s+NO\b|\s+N[°o]\s+DE\s+REGISTRE\b",
        text,
        maxsplit=1,
    )[0].strip()
    for prefix in ("EAST", "WEST", "NORTH", "SOUTH"):
        if text.startswith(prefix) and len(text) > len(prefix) + 3 and not text.startswith(f"{prefix} "):
            return f"{prefix} {text[len(prefix):]}".strip()
    for prefix in ("SF", "YC"):
        if text.startswith(prefix) and len(text) > len(prefix) + 2 and not text.startswith(f"{prefix} "):
            return f"{prefix} {text[len(prefix):]}".strip()
    return text


def _looks_like_vessel_name(value: str) -> bool:
    text = _clean_field_value(value).upper()
    if len(text) < 4 or len(text) > 80:
        return False
    blocked = {
        "GROSS",
        "DISTINCTIVE",
        "CO-ASSURED",
        "OWNER",
        "REGISTERED OWNER",
        "POLICY OF INSURANCE",
        "TECHNICAL MANAGER",
        "OWNER/OPERATOR/AUTHORIZED AGENT",
        "NAME",
    }
    if text in blocked:
        return False
    if "_" in text or re.search(r"\b(?:OWNER|OPERATOR|AGENT|MANAGER|CO-ASSURED|FINANCIAL|SECURITY|GROSS|DISTINCTIVE|ATTACHMENT|DATE|REGISTRATION|PERSON|AUTHORIZED|ARRANGEMENT|AGREEMENT|IMO|CLASS|PORT|REGISTRY|VESSEL)\b", text):
        return False
    return bool(re.search(r"[A-Z]", text))


def _clean_certificate_number(value: str) -> str:
    text = _clean_field_value(value).strip("()[]{}")
    if re.search(r"certificate\s*no|certificateno|policy\s*no", text, re.IGNORECASE):
        text = re.split(r"certificate\s*no\.?|certificateno\.?|policy\s*no\.?", text, flags=re.IGNORECASE)[-1]
    token_matches = [
        token
        for token in re.findall(r"[A-Z0-9]{2,}(?:[-_][A-Z0-9]+){1,}[A-Z0-9]*|\b[A-Z]{1,4}\d[A-Z0-9_\-/]{4,}\b|\b\d{6,}\b", text, flags=re.IGNORECASE)
        if re.search(r"[A-Z]", token, flags=re.IGNORECASE) or token.isdigit()
    ]
    if token_matches:
        text = token_matches[-1]
    text = re.sub(r"\s+\bREISSUED\b.*$", "", text, flags=re.IGNORECASE).strip()
    return text.strip(" :.-()[]{}")


def _clean_place_of_issue(value: str) -> str:
    text = _clean_field_value(value)
    text = re.sub(r"\s+\bon\b$", "", text, flags=re.IGNORECASE)
    return text.strip()


def _normalize_ocr_date_text(value: str) -> str:
    text = _clean_field_value(value)
    text = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", text, flags=re.IGNORECASE)
    chinese_match = re.search(r"\b(?P<year>\d{4})年(?P<month>\d{1,2})月(?P<day>\d{1,2})日", text)
    if chinese_match:
        try:
            parsed = datetime(
                int(chinese_match.group("year")),
                int(chinese_match.group("month")),
                int(chinese_match.group("day")),
            )
        except ValueError:
            return text
        return parsed.strftime("%d %B %Y").lstrip("0")
    compact_match = re.search(r"\b(?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})\b", text)
    if compact_match:
        try:
            parsed = datetime(
                int(compact_match.group("year")),
                int(compact_match.group("month")),
                int(compact_match.group("day")),
            )
        except ValueError:
            return text
        return parsed.strftime("%d %B %Y").lstrip("0")
    iso_match = re.search(r"\b(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b", text)
    if iso_match:
        try:
            parsed = datetime(
                int(iso_match.group("year")),
                int(iso_match.group("month")),
                int(iso_match.group("day")),
            )
        except ValueError:
            return text
        return parsed.strftime("%d %B %Y").lstrip("0")
    month_first_match = re.search(
        r"(?P<month>[A-Za-z]{3,9})\.?,?\s+(?P<day>\d{1,2}),?\s+(?P<year>\d{4})",
        text,
        re.IGNORECASE,
    )
    if month_first_match:
        month = _MONTH_ALIASES.get(month_first_match.group("month").lower(), month_first_match.group("month").capitalize())
        return f"{int(month_first_match.group('day'))} {month} {month_first_match.group('year')}"
    month_year_match = re.search(r"\b(?P<month>\d{1,2})-(?P<year>\d{4})\b", text)
    if month_year_match:
        month = int(month_year_match.group("month"))
        year = int(month_year_match.group("year"))
        if 1 <= month <= 12:
            parsed = datetime(year, month, 1)
            return parsed.strftime("%B %Y")
    match = re.search(r"(?P<day>\d{1,2})\s*-?\s*(?P<month>[A-Za-z]{3,9})\.?,?\s*-?\s*(?P<year>\d{4})", text)
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
    return bool(
        re.search(
            r"\d{1,2}[\s-]+[A-Za-z]{3,9}\.?,?[\s-]+\d{4}|[A-Za-z]{3,9}\.?,?\s+\d{1,2},?\s+\d{4}|\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,9}\s+\d{4}",
            value,
        )
    )


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


def _extract_pdf_pages_with_paddleocr(path: Path, engine: PaddleOcrEngine) -> OcrEngineOutput:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise OcrEngineUnavailable("pypdfium2 is required to rasterize scanned certificate PDFs.") from exc

    text_chunks: list[str] = []
    confidences: list[float] = []
    document = pdfium.PdfDocument(str(path))
    try:
        page_count = len(document) if engine.max_pdf_pages is None else min(len(document), engine.max_pdf_pages)
        with tempfile.TemporaryDirectory(prefix="certs-paddleocr-") as tmp_dir:
            tmp_path = Path(tmp_dir)
            for page_index in range(page_count):
                page = document[page_index]
                try:
                    bitmap = page.render(scale=engine.pdf_render_scale)
                    image = bitmap.to_pil()
                    image_path = tmp_path / f"page-{page_index + 1}.png"
                    image.save(image_path)
                    text, confidence = engine.extract_image_text(image_path)
                    if text.strip():
                        text_chunks.append(text)
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


def _predict_with_paddleocr(source_path: str | Path, engine: PaddleOcrEngine) -> tuple[str, float]:
    result = engine._predict(source_path)
    return _paddle_prediction_to_text(result)


def _paddle_prediction_to_text(result: Any) -> tuple[str, float]:
    texts: list[str] = []
    scores: list[float] = []
    _collect_paddle_text_scores(result, texts, scores)
    text = "\n".join(item.strip() for item in texts if item and item.strip()).strip()
    confidence = sum(scores) / len(scores) if scores else 0.0
    return text, confidence


def _collect_paddle_text_scores(value: Any, texts: list[str], scores: list[float]) -> None:
    if value is None:
        return

    if isinstance(value, Mapping):
        nested = value.get("res") if isinstance(value.get("res"), Mapping) else value
        rec_texts = nested.get("rec_texts")
        if rec_texts is not None:
            rec_scores_value = nested.get("rec_scores")
            rec_scores = list(rec_scores_value) if rec_scores_value is not None else []
            rec_texts_list = list(rec_texts)
            rec_boxes = nested.get("rec_boxes")
            if rec_boxes is None:
                rec_boxes = nested.get("rec_polys")
            if rec_boxes is None:
                rec_boxes = nested.get("dt_polys")
            texts.extend(_paddle_rec_texts_to_lines(rec_texts_list, rec_boxes))
            for index, text in enumerate(rec_texts_list):
                if str(text or "").strip():
                    if index < len(rec_scores):
                        score = _numeric_score(rec_scores[index])
                        if score is not None:
                            scores.append(score)
            return
        rec_text = nested.get("rec_text")
        if rec_text is not None:
            texts.append(str(rec_text))
            score = _numeric_score(nested.get("rec_score"))
            if score is not None:
                scores.append(score)
            return
        for child in value.values():
            _collect_paddle_text_scores(child, texts, scores)
        return

    if isinstance(value, tuple) and len(value) >= 2 and isinstance(value[1], tuple) and len(value[1]) >= 2:
        text = value[1][0]
        score = _numeric_score(value[1][1])
        if str(text or "").strip():
            texts.append(str(text))
            if score is not None:
                scores.append(score)
        return

    if isinstance(value, list):
        if len(value) >= 2 and isinstance(value[1], tuple) and len(value[1]) >= 2:
            text = value[1][0]
            score = _numeric_score(value[1][1])
            if str(text or "").strip():
                texts.append(str(text))
                if score is not None:
                    scores.append(score)
            return
        for child in value:
            _collect_paddle_text_scores(child, texts, scores)
        return

    res = getattr(value, "res", None)
    if isinstance(res, Mapping):
        _collect_paddle_text_scores({"res": res}, texts, scores)
        return

    json_value = getattr(value, "json", None)
    if callable(json_value):
        try:
            _collect_paddle_text_scores(json_value(), texts, scores)
        except Exception:
            return


def _paddle_rec_texts_to_lines(rec_texts: list[Any], rec_boxes: Any) -> list[str]:
    fallback = [str(text).strip() for text in rec_texts if str(text or "").strip()]
    if rec_boxes is None:
        return fallback

    boxes = list(rec_boxes)
    items: list[dict[str, Any]] = []
    for index, text in enumerate(rec_texts):
        cleaned = str(text or "").strip()
        if not cleaned or index >= len(boxes):
            continue
        bounds = _paddle_box_bounds(boxes[index])
        if bounds is None:
            return fallback
        left, top, right, bottom = bounds
        items.append(
            {
                "text": cleaned,
                "left": left,
                "center_y": (top + bottom) / 2.0,
                "height": max(1.0, bottom - top),
            }
        )
    if not items:
        return fallback

    heights = sorted(item["height"] for item in items)
    median_height = heights[len(heights) // 2]
    row_threshold = max(8.0, median_height * 0.65)
    rows: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda value: (value["center_y"], value["left"])):
        if rows and abs(item["center_y"] - rows[-1]["center_y"]) <= row_threshold:
            row = rows[-1]
            row["items"].append(item)
            row["center_y"] = sum(child["center_y"] for child in row["items"]) / len(row["items"])
        else:
            rows.append({"center_y": item["center_y"], "items": [item]})

    return [
        " ".join(child["text"] for child in sorted(row["items"], key=lambda value: value["left"]))
        for row in rows
    ]


def _paddle_box_bounds(box: Any) -> tuple[float, float, float, float] | None:
    try:
        values = list(box)
    except TypeError:
        return None
    if len(values) == 4:
        try:
            left, top, right, bottom = (float(value) for value in values)
        except (TypeError, ValueError):
            pass
        else:
            return left, top, right, bottom

    points = [point for point in values if isinstance(point, (list, tuple)) and len(point) >= 2]
    if not points:
        return None
    try:
        xs = [float(point[0]) for point in points]
        ys = [float(point[1]) for point in points]
    except (TypeError, ValueError):
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _numeric_score(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score < 0:
        return None
    if score > 1:
        score = score / 100.0
    return max(0.0, min(score, 1.0))


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
