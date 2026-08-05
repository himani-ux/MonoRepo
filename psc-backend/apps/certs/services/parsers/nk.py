from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from apps.certs.services.parsers.base import BaseClassParser, clean_space, condition_row, first_match, row, strip_ignored_sections


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
        conditions = _parse_conditions(lines)
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

        for condition in conditions:
            rows.append(_condition_to_row(condition))

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
            "conditions_of_class": conditions,
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


def _parse_conditions(lines: list[str]) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []
    target_sections = {"condition of class"}
    stop_sections = target_sections | {"condition of installation", "condition of statutory survey"}
    for index, line in enumerate(lines):
        section_key = clean_space(line).lower()
        if section_key not in target_sections:
            continue
        section = clean_space(line)
        content: list[str] = []
        for next_line in lines[index + 1 :]:
            cleaned = clean_space(next_line)
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered == "note" or lowered in stop_sections or re.match(r"^\d+\.\.?\s+", cleaned):
                break
            if cleaned.startswith("NK-SHIPS") or cleaned.startswith("NIPPON KAIJI KYOKAI") or cleaned.startswith("Page "):
                break
            content.append(cleaned)
        text = clean_space(" ".join(content))
        if not text or _is_nil_condition(text):
            continue
        due_date = _condition_due_date(text)
        text_without_due = clean_space(re.sub(r"\(?\s*DueDate\s*:\s*[^)]+\)?", "", text, flags=re.IGNORECASE))
        condition_id = f"NK-{re.sub(r'[^A-Z0-9]+', '-', section.upper()).strip('-')}-{len(conditions) + 1}"
        conditions.append(condition_row(condition_id, text_without_due or text, section, due_date))
    return conditions


def _condition_to_row(condition: dict[str, Any]) -> dict[str, Any]:
    return row(
        class_society="NK",
        class_code_or_name=condition["id"],
        source_section=condition.get("section") or "Condition of Class",
        row_type="condition",
        raw_text=condition["text"],
        due_date=condition.get("due_date"),
        postponed_until=condition.get("due_date"),
        condition_id=condition["id"],
        display_name=condition.get("section") or condition["id"],
    )


def _condition_due_date(text: str) -> str | None:
    match = re.search(r"DueDate\s*:\s*([0-9]{1,2}\s+[A-Z][a-z]{2}\s+[0-9]{4}|--)", text)
    if not match or match.group(1) == "--":
        return None
    return _to_iso(match.group(1))


def _is_nil_condition(text: str) -> bool:
    cleaned = re.sub(r"\(?\s*DueDate\s*:\s*--\s*\)?", "", text, flags=re.IGNORECASE)
    return clean_space(cleaned).strip(".- ").lower() in {"nil", "none", "n/a", "na"}


def _to_iso(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.replace(".", " ")
    return datetime.strptime(cleaned, "%d %b %Y").date().isoformat()
