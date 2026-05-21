from __future__ import annotations

from rest_framework_simplejwt.authentication import JWTAuthentication


class SafetyJWTAuthentication(JWTAuthentication):
    """Thin Safety wrapper around the platform SimpleJWT authentication flow."""

