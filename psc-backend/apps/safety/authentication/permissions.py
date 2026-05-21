from __future__ import annotations

from collections.abc import Iterable
import json

from rest_framework.permissions import BasePermission

from apps.safety.authentication.roles import normalized_authority_role


def _normalize_permission_ids(value: object) -> set[str]:
    if value is None:
        return set()

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return set()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                pass
            else:
                return _normalize_permission_ids(parsed)
        return {part.strip() for part in stripped.split(",") if part.strip()}

    if isinstance(value, Iterable):
        normalized: set[str] = set()
        for item in value:
            if item is None:
                continue
            text = str(item).strip()
            if text:
                normalized.add(text)
        return normalized

    text = str(value).strip()
    return {text} if text else set()


def _get_request_permission_ids(request, attr_name: str) -> set[str]:
    user = getattr(request, "user", None)
    auth = getattr(request, "auth", None)
    auth_payload_value = None
    if hasattr(auth, "get"):
        auth_payload_value = auth.get(attr_name)

    return (
        _normalize_permission_ids(getattr(user, attr_name, None))
        | _normalize_permission_ids(getattr(auth, attr_name, None))
        | _normalize_permission_ids(auth_payload_value)
    )


def _normalized_role(user) -> str:
    return normalized_authority_role(user)


class _BaseSafetyPermission(BasePermission):
    permission_attr = ""
    required_permission_id: str | None = None
    message = "You do not have the required Safety permission."

    def __init__(self, required_permission_id: str | None = None) -> None:
        if required_permission_id is not None:
            self.required_permission_id = required_permission_id

    @classmethod
    def requiring(cls, permission_id: str):
        return type(
            f"{cls.__name__}_{permission_id}",
            (cls,),
            {"required_permission_id": permission_id},
        )

    def has_permission(self, request, view) -> bool:
        required_permission_id = self.required_permission_id
        if not required_permission_id:
            return True

        permission_ids = _get_request_permission_ids(request, self.permission_attr)
        return required_permission_id in permission_ids


class HasFormPermission(_BaseSafetyPermission):
    permission_attr = "form_ids"
    message = "You do not have access to this Safety form."


class HasProcessPermission(_BaseSafetyPermission):
    permission_attr = "process_ids"
    message = "You do not have access to this Safety action."


class HasAnyFormPermission(BasePermission):
    message = "You do not have access to this Safety form."
    required_permission_ids: tuple[str, ...] = ()

    def __init__(self, *required_permission_ids: str) -> None:
        if required_permission_ids:
            self.required_permission_ids = tuple(required_permission_ids)

    @classmethod
    def requiring_any(cls, *permission_ids: str):
        return type(
            f"{cls.__name__}_{'_'.join(permission_ids)}",
            (cls,),
            {"required_permission_ids": tuple(permission_ids)},
        )

    def has_permission(self, request, view) -> bool:
        if not self.required_permission_ids:
            return True
        permission_ids = _get_request_permission_ids(request, "form_ids")
        return any(permission_id in permission_ids for permission_id in self.required_permission_ids)


class HasAnyProcessPermission(BasePermission):
    message = "You do not have access to this Safety action."
    required_permission_ids: tuple[str, ...] = ()

    def __init__(self, *required_permission_ids: str) -> None:
        if required_permission_ids:
            self.required_permission_ids = tuple(required_permission_ids)

    @classmethod
    def requiring_any(cls, *permission_ids: str):
        return type(
            f"{cls.__name__}_{'_'.join(permission_ids)}",
            (cls,),
            {"required_permission_ids": tuple(permission_ids)},
        )

    def has_permission(self, request, view) -> bool:
        if not self.required_permission_ids:
            return True
        permission_ids = _get_request_permission_ids(request, "process_ids")
        return any(permission_id in permission_ids for permission_id in self.required_permission_ids)


class HasRolePermission(BasePermission):
    message = "You do not have the required Safety role."
    required_roles: tuple[str, ...] = ()

    def __init__(self, *required_roles: str) -> None:
        if required_roles:
            self.required_roles = tuple(role.strip().upper() for role in required_roles if role.strip())

    @classmethod
    def requiring(cls, *roles: str):
        normalized_roles = tuple(role.strip().upper() for role in roles if role.strip())
        return type(
            f"{cls.__name__}_{'_'.join(normalized_roles)}",
            (cls,),
            {"required_roles": normalized_roles},
        )

    def has_permission(self, request, view) -> bool:
        if not self.required_roles:
            return True
        return _normalized_role(getattr(request, "user", None)) in self.required_roles


class HasDpaTaxonomyWritePermission(BasePermission):
    message = "Only DPA may modify Safety taxonomy masters."

    def has_permission(self, request, view) -> bool:
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return True
        return _normalized_role(getattr(request, "user", None)) == "DPA"
