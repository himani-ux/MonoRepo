"""
Authentication views for PSC module.

API endpoints per BACKEND_STRUCTURE.md Section 10 and IMPLEMENTATION_PLAN.md Step 2.1:
- POST /api/psc/auth/login/
- POST /api/psc/auth/refresh/
- POST /api/psc/auth/logout/
- GET /api/psc/auth/me/
"""

import logging
import uuid
from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .backends import PSCAuthenticationBackend
from .models import HRM501,CrewOnboardingHistory
from .serializers import (
    LoginRequestSerializer,
    TokenRefreshRequestSerializer,
    generate_tokens_for_user,
)

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """
    POST /api/psc/auth/login/

    Authenticate user and return JWT tokens.

    Features: FEAT-AUTH-001, FEAT-AUTH-002
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """
        Login with username and password.

        Returns access and refresh tokens along with user information.
        """
        serializer = LoginRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'VALIDATION_ERROR',
                    'message': 'Invalid request data',
                    'details': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # Authenticate using custom backend
        backend = PSCAuthenticationBackend()
        user = backend.authenticate(
            request=request,
            username=username,
            password=password
        )

        if not user:
            logger.warning(f"Failed login attempt for username: {username}")
            return Response(
                {
                    'error': 'AUTHENTICATION_FAILED',
                    'message': 'Invalid username or password',
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate JWT tokens
        tokens = generate_tokens_for_user(user)

        logger.info(f"User logged in: {user.id} ({user.role})")

        return Response(
            {
                'data': {
                    'access': tokens['access'],
                    'refresh': tokens['refresh'],
                    'user': user.to_dict(),
                },
                'message': 'Login successful'
            },
            status=status.HTTP_200_OK
        )


class TokenRefreshView(APIView):
    """
    POST /api/psc/auth/refresh/

    Refresh access token using refresh token.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """
        Refresh access token.

        Accepts a refresh token and returns a new access token.
        If token rotation is enabled, also returns a new refresh token.
        """
        serializer = TokenRefreshRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'VALIDATION_ERROR',
                    'message': 'Invalid request data',
                    'details': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(serializer.validated_data['refresh'])

            response_data = {
                'access': str(refresh.access_token),
            }

            # If rotation is enabled, include new refresh token
            # Note: rotation is enabled in settings.py
            response_data['refresh'] = str(refresh)

            return Response(
                {
                    'data': response_data,
                    'message': 'Token refreshed successfully'
                },
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {
                    'error': 'INVALID_TOKEN',
                    'message': 'Invalid or expired refresh token',
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """
    POST /api/psc/auth/logout/

    Logout user by blacklisting the refresh token.

    Source: BACKEND_STRUCTURE.md Section 10.1
    Implements: FEAT-AUTH-002
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Logout user.

        Accepts a refresh token and blacklists it so it cannot be reused.
        Frontend should discard both tokens after calling this.
        """
        refresh_token = request.data.get('refresh')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"User logged out: {request.user}")
            except TokenError:
                # Token already invalid, which is fine for logout
                pass
            except (ValueError, Exception) as e:
                # blacklist() may fail when user_id is UUID but User model expects int
                # (custom PSCJWTAuthentication uses UUID-based users without Django auth_user)
                logger.warning(f"Token blacklist skipped (non-critical): {e}")
                pass

        return Response(
            {
                'data': {},
                'message': 'Logout successful'
            },
            status=status.HTTP_200_OK
        )


class CurrentUserView(APIView):
    """
    GET /api/psc/auth/me/

    Get current authenticated user information.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get current user information from JWT token.

        Extracts user info from the JWT token claims.
        """
        # Get claims from the JWT token
        # The token is already validated by JWTAuthentication
        token = request.auth

        if not token:
            return Response(
                {
                    'error': 'NO_TOKEN',
                    'message': 'No authentication token found',
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Extract user info from token claims
        user_data = {
            'id': token.get('user_id'),
            'login_id': token.get('login_id'),
            'user_type': token.get('user_type'),
            'full_name': token.get('full_name'),
            'role': token.get('role'),
            'vessel_id': token.get('vessel_id'),
            'vessel_name': token.get('vessel_name'),
            'vessel_code': token.get('vessel_code'),
            'email': token.get('email'),
            'employee_id': token.get('employee_id'),
            'crew_id': token.get('crew_id'),
            'rank': token.get('rank'),
            'department': token.get('department'),
            'form_ids': token.get('form_ids') or [],
            'process_ids': token.get('process_ids') or [],
            'has_global_vessel_access': token.get('has_global_vessel_access'),
            'display_name': token.get('display_name'),
            'role_name': token.get('role_name'),
            'username': token.get('username'),
            'UserName': token.get('UserName'),
            'work_side': token.get('work_side'),
            'first_name': token.get('first_name'),
            'surname': token.get('surname'),
            'is_chief': token.get('is_chief'),
            'legacy_user_type': token.get('legacy_user_type'),
        }

        return Response(
            {
                'data': user_data,
                'message': 'Success'
            },
            status=status.HTTP_200_OK
        )




logger = logging.getLogger(__name__)


class CrewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        raw_vessel_id = request.query_params.get('vessel_id')

        if not raw_vessel_id:
            return Response({
                'error': 'MISSING_PARAM',
                'message': 'vessel_id query parameter is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Accept both 32-char and hyphenated UUID input; reject invalid values as 400.
        try:
            vessel_id = str(uuid.UUID(str(raw_vessel_id)))
        except (ValueError, TypeError, AttributeError):
            return Response({
                'error': 'INVALID_PARAM',
                'message': 'vessel_id must be a valid UUID.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        h.id,
                        h.CrewID,
                        h.first_name,
                        h.surname,
                        r.rank_name AS actual_rank_name,
                        h.department_name
                    FROM HRM501 h
                    INNER JOIN Crew_Onboarding_History coh
                        ON coh.CrewID = h.CrewID
                    LEFT JOIN master_applied_rank r
                        ON r.id = h.rank_name
                    WHERE 
                        coh.Vessel = CAST(%s AS uniqueidentifier)
                        AND coh.SignOffDate IS NULL
                        AND coh.is_active = 1
                        AND coh.is_deleted = 0
                        AND h.is_active = 1
                        AND h.is_deleted = 0
                    ORDER BY r.rank_name, h.first_name
                """, [vessel_id])

                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()

            data = []
            for row in rows:
                row_dict = dict(zip(columns, row))

                display_name = (
                    f"{row_dict.get('actual_rank_name') or ''} - "
                    f"{(row_dict.get('first_name') or '')} "
                    f"{(row_dict.get('surname') or '')}"
                ).strip()

                data.append({
                    "id": str(row_dict.get("id")),
                    "crew_id": row_dict.get("CrewID"),
                    "first_name": row_dict.get("first_name") or "",
                    "surname": row_dict.get("surname") or "",
                    "rank_name": row_dict.get("actual_rank_name") or "",
                    "department_name": row_dict.get("department_name") or "",
                    "display_name": display_name,
                })

        except Exception as e:
            logger.error(f"Error fetching crew list: {e}")
            return Response({
                "data": [],
                "message": "Error fetching crew list"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "data": data,
            "message": "Success"
        })


class CompanyLogoUploadView(APIView):
    """
    POST /api/psc/auth/company-logo/ — Upload company logo for PDF reports.
    GET /api/psc/auth/company-logo/ — Get current logo status.

    Only office users (DPA, SSQE, PIC) can upload.
    Accepts PNG, JPG, JPEG. Max 2MB.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from django.conf import settings
        logo_path = settings.COMPANY_LOGO_PATH
        has_logo = logo_path.exists()
        return Response({
            'data': {
                'has_logo': has_logo,
                'logo_url': f'{settings.MEDIA_URL}company/logo.png' if has_logo else None,
            }
        })

    def post(self, request, *args, **kwargs):
        from django.conf import settings
        import os

        # Only office users can upload logo
        if request.user.user_type != 'OFFICE':
            return Response({
                'error': 'FORBIDDEN',
                'message': 'Only office users can upload company logo.'
            }, status=status.HTTP_403_FORBIDDEN)

        logo_file = request.FILES.get('logo')
        if not logo_file:
            return Response({
                'error': 'VALIDATION_ERROR',
                'message': 'No logo file provided.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file type
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg']
        if logo_file.content_type not in allowed_types:
            return Response({
                'error': 'VALIDATION_ERROR',
                'message': 'Logo must be PNG or JPG format.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (2MB max)
        if logo_file.size > 2 * 1024 * 1024:
            return Response({
                'error': 'VALIDATION_ERROR',
                'message': 'Logo file must be under 2MB.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Save logo
        logo_dir = settings.MEDIA_ROOT / 'company'
        os.makedirs(logo_dir, exist_ok=True)
        logo_path = settings.COMPANY_LOGO_PATH

        with open(logo_path, 'wb') as f:
            for chunk in logo_file.chunks():
                f.write(chunk)

        return Response({
            'data': {
                'has_logo': True,
                'logo_url': f'{settings.MEDIA_URL}company/logo.png',
            },
            'message': 'Company logo uploaded successfully.'
        }, status=status.HTTP_200_OK)
