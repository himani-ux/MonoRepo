from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from apps.certs.services.parsers.base import BaseClassParser, clean_space, first_match, row, strip_ignored_sections


NK_DATE = r"\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4}"


class NKClassParser(BaseClassParser):
    class_society = "NK"
    parser_version = "nk-pdfplumber-v1"
    date_pattern = re.compile(NK_DATE)

    def parse_text(self, text: str, *, page_count: int) -> dict[str, Any]:
        normalized = "\n".join(_maybe_undouble_line(line) for line in text.splitlines())
        metadata_text = _collapse_doubled_numeric_runs(normalized)
        status_text = normalized.split("Survey History", 1)[0]
        lines = strip_ignored_sections([clean_space(line) for line in status_text.splitlines() if clean_space(line)])
        rows: list[dict[str, Any]] = []
        current_section = ""

        in_status_section = False
        for line in lines:
            if any(token in line for token in ("Survey Status:: Class", "Survey Status:: Statutory", "Current Statutory Certificates")):
                current_section = line.replace("NK-SHIPS::", "").strip(": ")
                in_status_section = True
                continue
            if line.startswith("Condition & Note") or line.startswith("Survey Status:: Installation"):
                in_status_section = False
            if not in_status_section or _ignore_line(line):
                continue
            parsed = _parse_status_line(line, current_section)
            if parsed:
                rows.append(parsed)

        return {
            "schema_version": 1,
            "parser_version": self.parser_version,
            "class_society": self.class_society,
            "source": "pdfplumber_text",
            "vessel": {
                "name": first_match(r"Name of Ship:\s*(.+?)\s+Class No", metadata_text)
                or first_match(r"Information Service\s+(.+?)\s+Class No", metadata_text),
                "imo": first_match(r"IMO No\.+\s*:?\s*(\d{7})", metadata_text),
                "class_no": first_match(r"Class No\.+\s*:?\s*NK\s*([0-9]+)", metadata_text),
            },
            "printed_on_date": _to_iso(first_match(r"Printed on\s+(\d{2}\.+[A-Za-z]{3}\.+\d{4})", metadata_text)),
            "rows": rows,
            "conditions_of_class": [],
            "unmapped_rows": [],
            "text_extraction": {"engine": "pdfplumber", "page_count": page_count, "char_count": len(text)},
        }


def _maybe_undouble_line(line: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]", "", line)
    if len(compact) < 8:
        return line
    adjacent_pairs = sum(1 for left, right in zip(compact, compact[1:]) if left == right)
    if adjacent_pairs < max(4, len(compact) // 4):
        return line
    output: list[str] = []
    index = 0
    while index < len(line):
        if index + 1 < len(line) and line[index].isalpha() and line[index] == line[index + 1]:
            output.append(line[index])
            index += 2
        else:
            output.append(line[index])
            index += 1
    return "".join(output)


def _collapse_doubled_numeric_runs(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if len(token) % 2:
            return token
        midpoint = len(token) // 2
        if all(token[index] == token[index + 1] for index in range(0, len(token), 2)):
            return "".join(token[index] for index in range(0, len(token), 2))
        if token[:midpoint] == token[midpoint:]:
            return token[:midpoint]
        return token

    return re.sub(r"\d{4,}", replace, value)


def _ignore_line(line: str) -> bool:
    tokens = (
        "Planned Machinery Survey",
        "Continuous Machinery Survey",
        "System applied",
        "Survey History",
        "Kind of Survey Status Due Date",
        "Certificate Kind Expiry Date",
        "NIPPON KAIJI KYOKAI",
        "NK-SHIPS Information Service",
    )
    return any(token.lower() in line.lower() for token in tokens)


def _parse_status_line(line: str, current_section: str) -> dict[str, Any] | None:
    dates = re.findall(NK_DATE, line)
    if not dates:
        return None
    first_date = line.find(dates[0])
    name = clean_space(line[:first_date])
    if not name or len(name) < 3:
        return None
    if "Survey Office" in line or "Record Number" in line:
        return None
    iso_dates = [_to_iso(date) for date in dates]
    return row(
        class_society="NK",
        class_code_or_name=name,
        source_section=current_section or "Survey Status",
        row_type="survey" if "Survey" in name else "certificate",
        expiry_date=iso_dates[0],
        next_due_date=iso_dates[0],
        raw_text=line,
    )


def _to_iso(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.replace(".", " ")
    return datetime.strptime(cleaned, "%d %b %Y").date().isoformat()
