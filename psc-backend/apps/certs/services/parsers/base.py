from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
from typing import Any


class ClassSnapshotParseError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParsedClassSnapshot:
    payload: dict[str, Any]
    parser_version: str
    parse_status: str


@dataclass(frozen=True)
class ExtractedClassSnapshotText:
    text: str
    page_count: int
    engine: str


class BaseClassParser:
    class_society = "UNKNOWN"
    parser_version = "class-parser-v1"
    date_pattern = re.compile(r"$^")

    def parse(self, pdf_path: str | Path) -> ParsedClassSnapshot:
        extracted = extract_pdf_text(pdf_path)
        text = extracted.text
        if not text.strip():
            raise ClassSnapshotParseError("Class status PDF did not expose a text layer and OCR fallback read no text.")
        payload = self.parse_text(text, page_count=extracted.page_count)
        stamp_text_extraction_metadata(payload, extracted)
        return ParsedClassSnapshot(
            payload=payload,
            parser_version=self.parser_version,
            parse_status="success" if payload["rows"] else "partial",
        )

    def parse_text(self, text: str, *, page_count: int) -> dict[str, Any]:
        raise NotImplementedError


def extract_pdf_text(pdf_path: str | Path) -> ExtractedClassSnapshotText:
    try:
        import pdfplumber
    except ImportError as exc:
        raise ClassSnapshotParseError("pdfplumber is required for class status text extraction.") from exc

    path = Path(pdf_path)
    if not path.exists():
        raise ClassSnapshotParseError(f"Class status PDF not found: {path}")
    pages: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text(x_tolerance=1, y_tolerance=3) or "")
        page_count = len(pdf.pages)
    text = "\n".join(pages)
    if text.strip():
        return ExtractedClassSnapshotText(text=text, page_count=page_count, engine="pdfplumber")
    ocr_text = extract_pdf_image_ocr_text(path)
    return ExtractedClassSnapshotText(text=ocr_text, page_count=page_count, engine="tesseract_ocr_fallback")


def extract_pdf_image_ocr_text(pdf_path: str | Path) -> str:
    try:
        from PIL import Image
        import pytesseract
        from PyPDF2 import PdfReader
    except ImportError as exc:
        raise ClassSnapshotParseError("Pillow, pytesseract, and PyPDF2 are required for class status OCR fallback.") from exc

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # pragma: no cover - PyPDF2 exception classes vary by version.
        raise ClassSnapshotParseError("Class status OCR fallback could not open this PDF.") from exc

    page_text: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        image_text: list[str] = []
        for image in iter_pdf_page_images(page, Image):
            if image.width * image.height < 50_000:
                continue
            try:
                text = pytesseract.image_to_string(image.convert("RGB"))
            except pytesseract.pytesseract.TesseractNotFoundError as exc:
                raise ClassSnapshotParseError("Tesseract is required for class status OCR fallback.") from exc
            if text.strip():
                image_text.append(text)
        if image_text:
            page_text.append(f"--- PAGE {page_number} OCR ---\n" + "\n".join(image_text))
    return "\n\n".join(page_text)


def iter_pdf_page_images(page: Any, image_module: Any):
    resources = page.get("/Resources") or {}
    xobjects = resources.get("/XObject")
    if not xobjects:
        return
    for _name, obj in sorted(xobjects.get_object().items(), key=lambda item: str(item[0])):
        stream = obj.get_object()
        if stream.get("/Subtype") != "/Image":
            continue
        try:
            image = image_module.open(BytesIO(stream.get_data()))
            image.load()
        except Exception:
            continue
        yield image


def stamp_text_extraction_metadata(payload: dict[str, Any], extracted: ExtractedClassSnapshotText) -> None:
    if extracted.engine != "pdfplumber":
        payload["source"] = "ocr_text"
    payload["text_extraction"] = {
        "engine": extracted.engine,
        "page_count": extracted.page_count,
        "char_count": len(extracted.text),
    }


def parse_class_snapshot_pdf(pdf_path: str | Path, class_society: str | None = None) -> ParsedClassSnapshot:
    parser = parser_for(class_society, pdf_path)
    return parser.parse(pdf_path)


def parser_for(class_society: str | None, pdf_path: str | Path) -> BaseClassParser:
    society = (class_society or "").upper().strip()
    if society == "KR":
        from apps.certs.services.parsers.kr import KRClassParser

        return KRClassParser()
    if society == "NK":
        from apps.certs.services.parsers.nk import NKClassParser

        return NKClassParser()
    if society == "BV":
        from apps.certs.services.parsers.bv import BVClassParser

        return BVClassParser()

    extracted = extract_pdf_text(pdf_path)
    sample = extracted.text
    upper = sample[:3000].upper()
    if "KOREAN REGISTER" in upper:
        from apps.certs.services.parsers.kr import KRClassParser

        return KRClassParser()
    if "NIPPON KAIJI KYOKAI" in upper or "NK-SHIPS" in upper:
        from apps.certs.services.parsers.nk import NKClassParser

        return NKClassParser()
    if "BUREAU VERITAS" in upper or "MOVE FLEET" in upper:
        from apps.certs.services.parsers.bv import BVClassParser

        return BVClassParser()
    raise ClassSnapshotParseError("Unsupported class status PDF format.")


def first_match(pattern: str, text: str, flags: int = re.IGNORECASE) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def clean_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_utc_date(value: str | None) -> str | None:
    if not value or value == "-":
        return None
    return value


def condition_row(condition_id: str, text: str, section: str | None = None, due_date: str | None = None) -> dict[str, Any]:
    return {
        "id": condition_id,
        "section": section,
        "due_date": due_date,
        "text": clean_space(text),
    }


def row(
    *,
    class_society: str,
    class_code_or_name: str,
    source_section: str,
    row_type: str,
    confidence: float = 1.0,
    raw_text: str = "",
    **fields: Any,
) -> dict[str, Any]:
    data = {
        "class_society": class_society,
        "class_code_or_name": clean_space(class_code_or_name),
        "source_section": clean_space(source_section),
        "row_type": row_type,
        "confidence": round(float(confidence), 3),
        "raw_text": clean_space(raw_text),
    }
    data.update({key: value for key, value in fields.items() if value not in ("", None)})
    return data


def strip_ignored_sections(lines: list[str]) -> list[str]:
    ignored_tokens = (
        "PSC Regime",
        "Paris MoU",
        "ParisMoU",
        "Tokyo MoU",
        "TokyoMoU",
        "USCG",
        "Particulars of Ship",
        "Ship Particulars",
        "Owner / Manager Information",
        "Cargo & Ballast Capacities",
    )
    return [line for line in lines if not any(token.lower() in line.lower() for token in ignored_tokens)]
