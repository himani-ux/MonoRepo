from __future__ import annotations

from dataclasses import dataclass

from django.core import signing


MAGIC_LINK_SALT = "apps.certs.notification_magic_link"
MAGIC_LINK_TTL_SECONDS = 24 * 60 * 60


class MagicLinkError(ValueError):
    pass


class MagicLinkExpired(MagicLinkError):
    pass


class MagicLinkInvalid(MagicLinkError):
    pass


@dataclass(frozen=True)
class MagicLinkPayload:
    notification_id: str
    recipient_id: str
    action: str = "ack"


def build_magic_link_token(*, notification_id: str, recipient_id: str, action: str = "ack") -> str:
    return signing.dumps(
        {
            "notificationId": str(notification_id),
            "recipientId": str(recipient_id),
            "action": action,
        },
        salt=MAGIC_LINK_SALT,
        compress=True,
    )


def build_magic_link_ack_path(*, notification_id: str, recipient_id: str) -> str:
    token = build_magic_link_token(notification_id=notification_id, recipient_id=recipient_id)
    return f"/api/certs/notifications/ack/{token}/"


def verify_magic_link_token(
    token: str,
    *,
    max_age_seconds: int = MAGIC_LINK_TTL_SECONDS,
) -> MagicLinkPayload:
    try:
        payload = signing.loads(token, salt=MAGIC_LINK_SALT, max_age=max_age_seconds)
    except signing.SignatureExpired as exc:
        raise MagicLinkExpired("Magic link has expired.") from exc
    except signing.BadSignature as exc:
        raise MagicLinkInvalid("Magic link is invalid.") from exc

    if payload.get("action") != "ack":
        raise MagicLinkInvalid("Magic link action is invalid.")
    notification_id = payload.get("notificationId")
    recipient_id = payload.get("recipientId")
    if not notification_id or not recipient_id:
        raise MagicLinkInvalid("Magic link payload is incomplete.")

    return MagicLinkPayload(
        notification_id=str(notification_id),
        recipient_id=str(recipient_id),
        action="ack",
    )
