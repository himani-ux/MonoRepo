from __future__ import annotations

from rest_framework import serializers


class HighSeverityPhotoValidator:
    message = "HIGH-severity SOI findings require >=1 photo (D-GAP-M24)."

    def validate(self, *, severity: str, photo_attachment_path) -> None:
        normalized_severity = str(severity or "").strip().upper()
        normalized_path = str(photo_attachment_path or "").strip()
        if normalized_severity == "HIGH" and not normalized_path:
            raise serializers.ValidationError({"photo_attachment_path": self.message})
