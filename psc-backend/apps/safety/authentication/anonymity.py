from __future__ import annotations


ANONYMITY_PLACEHOLDER = "Reporter not recorded"
NEAR_MISS_RECORD_TYPE = "NEAR_MISS"
REPORTER_VISIBLE_ROLES = {"DPA", "FM"}
MASKED_NULL_FIELDS = (
    "reporter_id",
    "reporter_user_id",
    "reporter_rank",
    "reporter_email",
    "reporter_department",
    "reporter_device_fingerprint",
    "created_by",
    "updated_by",
)


def _read_attr(source: object, key: str):
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _normalized_role(user) -> str:
    role_name = getattr(user, "safety_role_name", None) or getattr(user, "role_name", None) or getattr(user, "role", None) or ""
    return str(role_name).strip().upper()


def _normalized_user_id(user) -> str | None:
    for attr_name in ("id", "user_id", "pk"):
        value = getattr(user, attr_name, None)
        if value is not None:
            return str(value)
    return None


def can_see_reporter(user, record) -> bool:
    return user is not None


class AnonymityMixin:
    """Serializer mixin that masks reporter identity for near-miss viewers."""

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        record = representation if isinstance(instance, dict) else instance
        record_type = str(
            _read_attr(record, "record_type") or representation.get("record_type", "")
        ).upper()
        if record_type != NEAR_MISS_RECORD_TYPE:
            return representation

        request = self.context.get("request") if hasattr(self, "context") else None
        user = getattr(request, "user", None) if request is not None else None
        if user is None and hasattr(self, "context"):
            user = self.context.get("user")

        if can_see_reporter(user, instance):
            return representation

        if "reporter_name" in representation:
            representation["reporter_name"] = ANONYMITY_PLACEHOLDER

        for field_name in MASKED_NULL_FIELDS:
            if field_name in representation:
                representation[field_name] = None

        return representation
