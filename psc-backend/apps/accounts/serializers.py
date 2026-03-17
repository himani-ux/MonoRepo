"""
Serializers for authentication and user management.

Per BACKEND_STRUCTURE.md Section 10 (API Contracts)
"""

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .backends import AuthenticatedUser


class LoginRequestSerializer(serializers.Serializer):
    """
    Serializer for login requests.
    """
    username = serializers.CharField(
        required=True,
        help_text="Username (user_id for vessel users, username for office users)"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="User password"
    )


class UserSerializer(serializers.Serializer):
    """
    Serializer for user information returned after authentication.
    """
    id = serializers.CharField(read_only=True)
    user_type = serializers.ChoiceField(choices=['VESSEL', 'OFFICE'], read_only=True)
    full_name = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)
    vessel_id = serializers.CharField(read_only=True, allow_null=True)
    vessel_name = serializers.CharField(read_only=True, allow_null=True)
    vessel_code = serializers.CharField(read_only=True, allow_null=True)
    email = serializers.CharField(read_only=True, allow_null=True)
    employee_id = serializers.CharField(read_only=True, allow_null=True)
    crew_id = serializers.CharField(read_only=True, allow_null=True)
    rank = serializers.CharField(read_only=True, allow_null=True)
    department = serializers.CharField(read_only=True, allow_null=True)
    form_ids = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        default=list,
    )
    process_ids = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        default=list,
    )
    has_global_vessel_access = serializers.BooleanField(
        read_only=True,
        allow_null=True,
        required=False,
    )
    display_name = serializers.CharField(read_only=True)
    role_name = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)
    UserName = serializers.CharField(read_only=True)
    work_side = serializers.IntegerField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    surname = serializers.CharField(read_only=True)
    is_chief = serializers.BooleanField(read_only=True)
    legacy_user_type = serializers.CharField(read_only=True)


class LoginResponseSerializer(serializers.Serializer):
    """
    Serializer for successful login response.
    """
    access = serializers.CharField(read_only=True, help_text="JWT access token")
    refresh = serializers.CharField(read_only=True, help_text="JWT refresh token")
    user = UserSerializer(read_only=True)


class TokenRefreshRequestSerializer(serializers.Serializer):
    """
    Serializer for token refresh requests.
    """
    refresh = serializers.CharField(
        required=True,
        help_text="JWT refresh token"
    )


class TokenRefreshResponseSerializer(serializers.Serializer):
    """
    Serializer for token refresh response.
    """
    access = serializers.CharField(read_only=True, help_text="New JWT access token")
    refresh = serializers.CharField(read_only=True, help_text="New JWT refresh token (if rotated)")


class PSCRefreshToken(RefreshToken):
    """
    Custom refresh token that includes PSC-specific claims.
    """

    @classmethod
    def for_user(cls, user):
        """
        Create a refresh token for an AuthenticatedUser.

        Includes custom claims:
        - user_type: VESSEL or OFFICE
        - role: PSC role code
        - vessel_id: vessel UUID (for vessel users)
        - full_name: user's display name
        """
        token = cls()

        # Set the user ID claim
        token['user_id'] = str(user.id)
        if getattr(user, 'login_id', None):
            token['login_id'] = user.login_id

        # Add custom claims
        token['user_type'] = user.user_type
        token['role'] = user.role
        token['full_name'] = user.full_name

        if user.vessel_id:
            token['vessel_id'] = user.vessel_id
            token['vessel_code'] = user.vessel_code

        if user.email:
            token['email'] = user.email

        if user.employee_id:
            token['employee_id'] = user.employee_id

        if user.crew_id:
            token['crew_id'] = user.crew_id

        if user.rank:
            token['rank'] = user.rank
        if user.department:
            token['department'] = user.department
        if user.vessel_name:
            token['vessel_name'] = user.vessel_name
        token['display_name'] = user.display_name
        token['role_name'] = user.role
        token['username'] = user.username
        token['UserName'] = user.username
        token['work_side'] = user.work_side
        token['first_name'] = user.first_name
        token['surname'] = user.surname
        token['is_chief'] = user.is_chief
        token['legacy_user_type'] = user.legacy_user_type

        if getattr(user, 'form_ids', None) is not None:
            token['form_ids'] = user.form_ids
        if getattr(user, 'process_ids', None) is not None:
            token['process_ids'] = user.process_ids
        if getattr(user, 'has_global_vessel_access', None) is not None:
            token['has_global_vessel_access'] = bool(user.has_global_vessel_access)

        return token


def generate_tokens_for_user(user: AuthenticatedUser) -> dict:
    """
    Generate JWT tokens for an authenticated user.

    Returns:
        dict with 'access' and 'refresh' tokens
    """
    refresh = PSCRefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


class ErrorResponseSerializer(serializers.Serializer):
    """
    Standard error response format per BACKEND_STRUCTURE.md Section 10.2
    """
    error = serializers.CharField(read_only=True, help_text="Error code")
    message = serializers.CharField(read_only=True, help_text="Human readable message")
    details = serializers.DictField(
        child=serializers.CharField(),
        read_only=True,
        required=False,
        help_text="Field-level error details"
    )


class SuccessResponseSerializer(serializers.Serializer):
    """
    Standard success response format per BACKEND_STRUCTURE.md Section 10.2
    """
    data = serializers.DictField(read_only=True)  # type: ignore[assignment]
    message = serializers.CharField(read_only=True, default="Success")
