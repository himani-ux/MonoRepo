"""Safety authentication helpers package.

Keep this module import-light so tests can bootstrap Django explicitly before
loading auth backends or DRF/SimpleJWT dependencies.
"""

__all__ = [
    "AnonymityMixin",
    "HasFormPermission",
    "HasProcessPermission",
    "SafetyJWTAuthentication",
    "can_see_reporter",
    "filter_by_vessel_scope",
    "get_scoped_vessel_ids",
    "has_global_vessel_scope",
    "user_has_vessel_access",
]
