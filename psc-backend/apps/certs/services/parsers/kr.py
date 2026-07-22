from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from apps.certs.services.parsers.base import (
    BaseClassParser,
    clean_space,
    condition_row,
    first_match,
    row,
    strip_ignored_sections,
)


ISO_DATE = r"\d{4}-\d{2}-\d{2}"


class KRClassParser(BaseClassParser):
    class_society = "KR"
    parser_version = "kr-pdfplumber-v1"
    date_pattern = re.compile(ISO_DATE)
    ocr_page_numbers = (5, 6, 7, 8)

    def parse_text(self, text: str, *, page_count: int) -> dict[str, Any]:
        lines = strip_ignored_sections([clean_space(line) for line in text.splitlines() if clean_space(line)])
        rows: list[dict[str, Any]] = []
        conditions: list[dict[str, Any]] = []
        current_section = ""
        current_group = ""

        for index, line in enumerate(lines):
            if line in {"Certificates", "Class Certificates", "Statutory Certificates or Documents of Compliance issued by KR"}:
                current_section = line
                continue
            if line.endswith("Surveys") or line in {"Class Surveys", "Statutory Surveys", "Cargo Handling Appliances", "Anchor Handling Appliances"}:
                current_section = line
                continue
            if _is_group_heading(line):
                current_group = line
                continue

            cert = _parse_certificate_line(line, current_section)
            if cert:
                rows.append(cert)
                continue

            survey = _parse_survey_line(line, current_section, current_group)
            if survey:
                rows.append(survey)
                continue

            condition = _parse_condition(lines, index)
            if condition:
                conditions.append(condition)
                rows.append(
                    row(
                        class_society=self.class_society,
                        class_code_or_name=condition["id"],
                        source_section="Condition of Class / Statutory Condition",
                        row_type="condition",
                        raw_text=condition["text"],
                        postponed_until=condition.get("due_date"),
                    )
                )

        return {
            "schema_version": 1,
            "parser_version": self.parser_version,
            "class_society": self.class_society,
            "source": "pdfplumber_text",
            "vessel": {
                "name": first_match(r"VESSEL STATUS FOR SHIP'S OWNER\s+(.+?)\s+Class No", text, re.IGNORECASE | re.DOTALL)
                or first_match(r"Ship Name\s+(.+?)\s+Work ID", text),
                "imo": first_match(r"IMO No\s*:\s*(\d{7})", text) or first_match(r"IMO No\.\s*(\d{7})", text),
                "class_no": first_match(r"Class No\s*:\s*([0-9]+)", text) or first_match(r"Class No\.\s*([0-9]+)", text),
            },
            "printed_on_date": _to_iso(first_match(r"Printed on\s+(\d{2}-[A-Za-z]{3}-\d{4})", text)),
            "rows": rows,
            "conditions_of_class": conditions,
            "unmapped_rows": [],
            "text_extraction": {"engine": "pdfplumber", "page_count": page_count, "char_count": len(text)},
        }


def _is_group_heading(line: str) -> bool:
    if not line or line.startswith("For ") or line.startswith("Due"):
        return False
    if re.search(ISO_DATE, line):
        return False
    if any(token in line for token in ("Survey Description", "Certificate description", "* UTN")):
        return False
    return len(line) <= 96 and any(token in line for token in ("Ship", "Pollution", "Safety", "Load Line", "Cargo", "Ballast", "Inventory", "Energy"))


def _parse_certificate_line(line: str, current_section: str) -> dict[str, Any] | None:
    if "Certificate" not in current_section and "Documents" not in current_section:
        return None
    match = re.match(
        rf"(?P<name>.+?)\s+(?P<code>[A-Z0-9()/-]+)\s+(?P<kind>Full|Permanence|-)\s+(?P<issue>{ISO_DATE})(?:\s+(?P<expiry>{ISO_DATE}|-))?\b",
        line,
        re.IGNORECASE,
    )
    if not match:
        match = re.match(
            rf"(?P<name>.+?)\s+(?P<code>[A-Z0-9()/-]+)\s+(?P<issue>{ISO_DATE})(?:\s+(?P<expiry>{ISO_DATE}|-))?\b",
            line,
            re.IGNORECASE,
        )
    if not match:
        return None
    expiry = match.groupdict().get("expiry")
    kind = match.groupdict().get("kind") or "-"
    return row(
        class_society="KR",
        class_code_or_name=match.group("code").upper(),
        source_section=current_section or "Certificates",
        row_type="certificate",
        type=kind.lower(),
        issue_date=match.group("issue"),
        expiry_date=None if not expiry or expiry == "-" else expiry,
        raw_text=line,
        display_name=match.group("name"),
    )


def _parse_survey_line(line: str, current_section: str, current_group: str) -> dict[str, Any] | None:
    dates = re.findall(ISO_DATE, line)
    if not dates or "Survey" not in line:
        return None
    first_date = line.find(dates[0])
    name = clean_space(line[:first_date])
    if not name:
        return None
    class_code_or_name = name if _is_ship_work_group(current_group) else clean_space(f"{current_group} {name}")
    return row(
        class_society="KR",
        class_code_or_name=class_code_or_name,
        source_section=current_section or "Survey Information",
        row_type="survey",
        last_done_date=_survey_last_done_date(dates),
        next_due_date=_survey_next_due_date(dates),
        raw_text=line,
    )


def _survey_last_done_date(dates: list[str]) -> str | None:
    if len(dates) == 2 or len(dates) >= 4:
        return dates[0]
    return None


def _survey_next_due_date(dates: list[str]) -> str | None:
    if len(dates) == 2 or len(dates) >= 4:
        return dates[1]
    return dates[0] if dates else None


def _is_ship_work_group(value: str) -> bool:
    return bool(re.search(r"\bShip Name\b.+\bWork ID\b", value or "", re.IGNORECASE))


def _parse_condition(lines: list[str], index: int) -> dict[str, Any] | None:
    line = lines[index]
    match = re.match(rf"(?P<id>C\.\d+)\s*(?P<issued>{ISO_DATE})\s+(?P<due>{ISO_DATE})\s+(?P<report>\S+)\s+(?P<section>\w+)", line)
    if not match:
        return None
    text = lines[index + 1] if index + 1 < len(lines) else ""
    return condition_row(match.group("id"), text, match.group("section"), match.group("due"))


def _to_iso(value: str | None) -> str | None:
    if not value:
        return None
    return datetime.strptime(value, "%d-%b-%Y").date().isoformat()
