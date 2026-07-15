from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from apps.certs.services.parsers.base import BaseClassParser, clean_space, first_match, row, strip_ignored_sections


BV_DATE = r"\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}"


class BVClassParser(BaseClassParser):
    class_society = "BV"
    parser_version = "bv-pdfplumber-v1"
    date_pattern = re.compile(BV_DATE)

    def parse_text(self, text: str, *, page_count: int) -> dict[str, Any]:
        lines = strip_ignored_sections([clean_space(line) for line in text.splitlines() if clean_space(line)])
        rows: list[dict[str, Any]] = []
        current_section = ""
        in_target = False

        for line in lines:
            if line == "Classification Surveys" or line == "Statutory Surveys" or line == "Statutory Audits / Inspections":
                current_section = line
                in_target = True
                continue
            if line.startswith("Conditions of Class / Statutory Recommendations"):
                in_target = False
                continue
            if line.startswith("MRV Status") or line.startswith("Planned Inspection Items"):
                in_target = False
            if not in_target or _ignore_line(line):
                continue
            parsed = _parse_line(line, current_section)
            if parsed:
                rows.append(parsed)

        return {
            "schema_version": 1,
            "parser_version": self.parser_version,
            "class_society": self.class_society,
            "source": "pdfplumber_text",
            "vessel": {
                "name": first_match(r"Ship name:\s*(.+?)\s+BV Nr", text) or first_match(r"^([A-Z][A-Z ]+)\s+Reg\. Owner", text, re.MULTILINE),
                "imo": first_match(r"IMO Number:\s*(\d{7})", text),
                "class_no": first_match(r"BV Reg\. Nr:\s*([A-Z0-9]+)", text) or first_match(r"BV Nr:\s*([A-Z0-9]+)", text),
            },
            "printed_on_date": _to_iso(first_match(r"Generated on\s+(\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4})", text)),
            "rows": rows,
            "conditions_of_class": [] if "Conditions of Class / Statutory Recommendations\nNone" in text else [],
            "unmapped_rows": [],
            "text_extraction": {"engine": "pdfplumber", "page_count": page_count, "char_count": len(text)},
        }


def _ignore_line(line: str) -> bool:
    return any(
        token in line
        for token in (
            "Survey name Last Due Date",
            "Audit / Inspection name Last Due Date",
            "Legend:",
            "Bureau Veritas Marine & Offshore",
            "Generated on",
        )
    )


def _parse_line(line: str, current_section: str) -> dict[str, Any] | None:
    dates = re.findall(BV_DATE, line)
    if not dates:
        return None
    first_date = line.find(dates[0])
    name = clean_space(line[:first_date])
    if not name or len(name) < 3:
        return None
    iso_dates = [_to_iso(date) for date in dates]
    return row(
        class_society="BV",
        class_code_or_name=name,
        source_section=current_section or "Surveys / Audits / Inspections",
        row_type="survey" if "Survey" in name or current_section.endswith("Surveys") else "audit",
        last_done_date=iso_dates[0] if len(iso_dates) > 1 else None,
        next_due_date=iso_dates[1] if len(iso_dates) > 1 else iso_dates[0],
        raw_text=line,
    )


def _to_iso(value: str | None) -> str | None:
    if not value:
        return None
    return datetime.strptime(value, "%d %b %Y").date().isoformat()
