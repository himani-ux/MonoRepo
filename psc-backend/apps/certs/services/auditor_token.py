from __future__ import annotations

from dataclasses import dataclass
import hashlib
import secrets

from django.core import signing


AUDITOR_SESSION_SALT = "apps.certs.external_auditor_session"


class AuditorTokenError(ValueError):
    pass


class AuditorTokenInvalid(AuditorTokenError):
    pass


@dataclass(frozen=True)
class AuditorSessionToken:
    grant_id: str
    token_secret_hash: str


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(str(raw_token).encode("utf-8")).hexdigest()


def generate_raw_token() -> str:
    return secrets.token_urlsafe(32)


def build_signup_path(raw_token: str) -> str:
    return f"/api/auditor/signup/{raw_token}/"


def build_session_token(*, grant_id: str, raw_secret: str) -> str:
    return signing.dumps(
        {
            "grantId": str(grant_id),
            "secret": str(raw_secret),
        },
        salt=AUDITOR_SESSION_SALT,
        compress=True,
    )


def verify_session_token(token: str) -> tuple[str, str]:
    try:
        payload = signing.loads(token, salt=AUDITOR_SESSION_SALT)
    except signing.BadSignature as exc:
        raise AuditorTokenInvalid("Auditor access token is invalid.") from exc

    grant_id = payload.get("grantId")
    secret = payload.get("secret")
    if not grant_id or not secret:
        raise AuditorTokenInvalid("Auditor access token payload is incomplete.")
    return str(grant_id), hash_token(str(secret))
