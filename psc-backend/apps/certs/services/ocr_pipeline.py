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
    selected_engine = engine or PaddleOcrEngine()
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
        text_det_limit_side_len: int | None = None,
        text_recognition_batch_size: int | None = None,
    ) -> None:
        self.language = language
        self.max_pdf_pages = None if max_pdf_pages is None else max(1, int(max_pdf_pages))
        self.pdf_render_scale = max(1.0, float(pdf_render_scale))
        self.ocr_version = ocr_version
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
