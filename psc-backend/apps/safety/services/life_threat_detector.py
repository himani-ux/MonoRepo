from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LifeThreatScanResult:
    detected: bool
    matched_keywords: tuple[str, ...]


class LifeThreatDetector:
    severity_tokens = {"CRITICAL", "LIFE_THREAT", "LIFE THREAT"}
    keyword_patterns = (
        ("fire", re.compile(r"\bfire\b", re.IGNORECASE)),
        ("explosion", re.compile(r"\bexplosion\b", re.IGNORECASE)),
        ("electrocution", re.compile(r"\belectrocution\b", re.IGNORECASE)),
        ("gas leak", re.compile(r"\bgas leak\b", re.IGNORECASE)),
        ("toxic exposure", re.compile(r"\btoxic exposure\b", re.IGNORECASE)),
        ("confined space", re.compile(r"\bconfined space\b", re.IGNORECASE)),
        ("asphyxiation", re.compile(r"\basphyxiation\b", re.IGNORECASE)),
        ("man overboard", re.compile(r"\bman overboard\b", re.IGNORECASE)),
        ("structural failure", re.compile(r"\bstructural failure\b", re.IGNORECASE)),
        ("collapse", re.compile(r"\bcollapse\b", re.IGNORECASE)),
        ("uncontrolled flooding", re.compile(r"\buncontrolled flooding\b", re.IGNORECASE)),
        ("life-threatening", re.compile(r"\blife[- ]threatening\b", re.IGNORECASE)),
        ("fatal", re.compile(r"\bfatal(?:ity)?\b", re.IGNORECASE)),
    )

    def scan(
        self,
        *,
        severity: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> LifeThreatScanResult:
        matched: list[str] = []
        normalized_severity = str(severity or "").strip().upper()
        if normalized_severity in self.severity_tokens:
            matched.append(normalized_severity)

        haystack = " ".join(part for part in (title or "", description or "") if part).strip()
        for keyword, pattern in self.keyword_patterns:
            if pattern.search(haystack):
                matched.append(keyword)

        ordered = tuple(dict.fromkeys(matched))
        return LifeThreatScanResult(detected=bool(ordered), matched_keywords=ordered)
