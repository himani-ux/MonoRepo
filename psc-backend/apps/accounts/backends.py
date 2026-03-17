"""
Custom authentication backend for PSC module.

Authenticates vessel users via Ship_UsersLogin and enriches via HRM501,
and office users via users table.
Does not use Django's built-in User model.
"""

import hashlib
import logging
from typing import Optional

from django.contrib.auth.backends import BaseBackend
from django.db import models
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .models import HRM501, OfficeUser, RoleCodes, ShipUsersLogin, CrewOnboardingHistory

logger = logging.getLogger(__name__)


class AuthenticatedUser:
    """
    Lightweight authenticated user object.
    Compatible with Django-style access (id, pk)
    and your custom UUID-based system (user_id).
    """

    def __init__(
        self,
        user_id: str,
        user_type: str,
        full_name: str,
        role: str,
        vessel_id: Optional[str] = None,
        vessel_name: Optional[str] = None,
        vessel_code: Optional[str] = None,
        email: Optional[str] = None,
        employee_id: Optional[str] = None,
        crew_id: Optional[str] = None,
        rank: Optional[str] = None,
        department: Optional[str] = None,
        form_ids: Optional[list[str]] = None,
        process_ids: Optional[list[str]] = None,
        login_id: Optional[str] = None,
        has_global_vessel_access: Optional[bool] = None,
    ):
        # 🔐 Primary UUID (DB relations should use this)
        self.user_id = str(user_id)
        self.login_id = login_id

        # 🔁 Backward compatibility (so old code using .id still works)
        self.id = self.user_id

        self.user_type = user_type
        self.full_name = full_name
        self.role = role

        self.vessel_id = vessel_id
        self.vessel_name = vessel_name
        self.vessel_code = vessel_code

        self.email = email
        self.employee_id = employee_id
        self.crew_id = crew_id
        self.rank = rank
        self.department = department
        self.form_ids = form_ids or []
        self.process_ids = process_ids or []
        self.has_global_vessel_access = has_global_vessel_access

        # Django-like flags
        self.is_authenticated = True
        self.is_active = True

    # ✅ Django expects .pk
    @property
    def pk(self):
        return self.user_id

    # ✅ Optional: add .user to prevent future crash
    @property
    def user(self):
        return self  # allows user.user.id safely

    @property
    def display_name(self):
        return self.full_name

    @property
    def username(self):
        return self.login_id or self.employee_id or self.crew_id or self.user_id

    @property
    def legacy_user_type(self):
        return "ship" if (self.user_type or "").upper() == "VESSEL" else "office"

    @property
    def work_side(self):
        return 1 if self.legacy_user_type == "ship" else 0

    @property
    def is_chief(self):
        normalized_role = (self.role or "").upper()
        normalized_rank = (self.rank or "").upper()
        return (
            normalized_role == "VESSEL_MASTER"
            or "MASTER" in normalized_rank
            or "CHIEF ENGINEER" in normalized_rank
            or "CHIEF OFFICER" in normalized_rank
        )

    @property
    def first_name(self):
        parts = self.full_name.strip().split()
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return " ".join(parts[:-1])

    @property
    def surname(self):
        parts = self.full_name.strip().split()
        if len(parts) <= 1:
            return ""
        return parts[-1]

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    def to_dict(self):
        return {
            "id": self.user_id,
            "user_id": self.user_id,
            "login_id": self.login_id,
            "user_type": self.user_type,
            "full_name": self.full_name,
            "role": self.role,
            "vessel_id": self.vessel_id,
            "vessel_name": self.vessel_name,
            "vessel_code": self.vessel_code,
            "email": self.email,
            "employee_id": self.employee_id,
            "crew_id": self.crew_id,
            "rank": self.rank,
            "department": self.department,
            "form_ids": self.form_ids,
            "process_ids": self.process_ids,
            "has_global_vessel_access": self.has_global_vessel_access,
            "display_name": self.display_name,
            "role_name": self.role,
            "username": self.username,
            "UserName": self.username,
            "work_side": self.work_side,
            "first_name": self.first_name,
            "surname": self.surname,
            "is_chief": self.is_chief,
            "legacy_user_type": self.legacy_user_type,
        }

# ================= JWT AUTH =================


class PSCJWTAuthentication(JWTAuthentication):
    """
    Reconstruct AuthenticatedUser from JWT claims.
    """

    def get_user(self, validated_token):
        try:
            user_id = validated_token.get("user_id")
            if not user_id:
                raise InvalidToken("Token contains no user_id claim")

            return AuthenticatedUser(
                user_id=user_id,
                login_id=validated_token.get("login_id"),
                user_type=validated_token.get("user_type", ""),
                full_name=validated_token.get("full_name", ""),
                role=validated_token.get("role", ""),
                vessel_id=validated_token.get("vessel_id"),
                vessel_name=validated_token.get("vessel_name"),  # ✅ FIXED
                vessel_code=validated_token.get("vessel_code"),
                email=validated_token.get("email"),
                employee_id=validated_token.get("employee_id"),
                crew_id=validated_token.get("crew_id"),
                rank=validated_token.get("rank"),
                department=validated_token.get("department"),
                form_ids=validated_token.get("form_ids") or [],
                process_ids=validated_token.get("process_ids") or [],
                has_global_vessel_access=validated_token.get("has_global_vessel_access"),
            )
        except KeyError:
            raise InvalidToken("Token is missing required claims")


# ================= AUTH BACKEND =================


class PSCAuthenticationBackend(BaseBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        # Vessel first
        user = self._authenticate_vessel_user(username, password)
        if user:
            return user

        # Office second
        user = self._authenticate_office_user(username, password)
        if user:
            return user

        logger.warning(f"Failed login attempt for username: {username}")
        return None



# ================= VESSEL =================
  
    def _authenticate_vessel_user(self, username: str, password: str) -> Optional[AuthenticatedUser]:
        """
        Authenticate vessel user using:
        1. Ship_UsersLogin (for username + password)
        2. HRM501 (for crew details + rank)
        3. Crew_Onboarding_History (for vessel UUID)
        4. VesselData (for vessel details)
        """
        try:
            # 🔹 Step 1: Authenticate from Ship_UsersLogin
            ship_user = ShipUsersLogin.objects.filter(
                CrewID=username,
                is_active=True,
                is_deleted=False
            ).first()

            if not ship_user:
                logger.warning(f"Vessel user not found: {username}")
                return None

            # 🔹 Step 2: Verify password
            if not self._verify_password(password, ship_user.Password):
                logger.warning(f"Invalid password for user: {username}")
                return None

            # 🔹 Step 3: Get crew details
            hrm_user = HRM501.objects.filter(
                CrewID=username,
                is_active=True,
                is_deleted=False
            ).first()

            full_name = hrm_user.full_name if hrm_user else username
            department = hrm_user.department_name if hrm_user else None

            rank_name = None

            # ✅ RAW SQL rank lookup (prevents UUID conversion error)
            if hrm_user and hrm_user.rank_name:
                from django.db import connection

                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT rank_name
                            FROM master_applied_rank
                            WHERE id = %s
                            AND is_active = 1
                            AND is_deleted = 0
                            """,
                            [str(hrm_user.rank_name)]
                        )
                        row = cursor.fetchone()

                        if row:
                            rank_name = row[0]

                except Exception as e:
                    logger.error(f"Rank lookup failed for {username}: {e}")

            logger.info(f"DEBUG: Actual Rank for {username}: {rank_name}")

            # ✅ Determine role dynamically
            role = self._determine_vessel_role(rank_name)

            # Permissions from msc_profiles (ship-side)
            from .utils import get_profile_permissions
            form_ids, process_ids = get_profile_permissions(rank_name, work_side=True)

            # 🔹 Step 4: Get latest onboarding record
            onboarding = CrewOnboardingHistory.objects.filter(
                CrewID=username,
                is_deleted=False
            ).order_by('-SignOnDate').first()

            vessel_id = None
            vessel_name = None
            vessel_code = None

            if onboarding and onboarding.Vessel:
                logger.info(f"DEBUG: onboarding.Vessel for {username}: {onboarding.Vessel}")

                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, vesselName, vesselCode 
                        FROM VesselData 
                        WHERE id = %s 
                        AND is_active = 1 
                        AND is_deleted = 0
                        """,
                        [onboarding.Vessel]
                    )
                    row = cursor.fetchone()

                    if row:
                        vessel_id = str(row[0])
                        vessel_name = row[1]
                        vessel_code = row[2]
                        logger.info(
                            f"✅ Vessel found for crew {username}: "
                            f"vessel_id={vessel_id}, vessel_code={vessel_code}, vessel_name={vessel_name}"
                        )
                    else:
                        logger.error(f"❌ Vessel not found for ID: {onboarding.Vessel}")
            else:
                logger.warning(f"No onboarding record found for crew: {username}")

            # 🔹 Step 5: Return authenticated user
            user_uuid = str(hrm_user.id) if hrm_user else username

            return AuthenticatedUser(
                # Use HRM501 UUID for workflow ownership checks
                user_id=user_uuid,
                user_type='VESSEL',
                full_name=full_name,
                role=role,
                vessel_id=vessel_id,
                vessel_name=vessel_name,
                vessel_code=vessel_code,
                crew_id=username,
                rank=rank_name,
                department=department,
                form_ids=form_ids,
                process_ids=process_ids,
            )

        except Exception as e:
            logger.error(f"Error authenticating vessel user {username}: {e}", exc_info=True)
            return None



# ================= OFFICE =================

    def _authenticate_office_user(
        self, username: str, password: str
    ) -> Optional[AuthenticatedUser]:
        try:
            normalized_username = (username or '').strip()
            user = OfficeUser.objects.filter(
                is_active=True,
                is_deleted=False,
            ).filter(
                models.Q(username__iexact=normalized_username) |
                models.Q(employee_id__iexact=normalized_username)
            ).first()

            if not user:
                return None

            if not self._verify_password(password, user.password):
                return None

            # Global reviewer role logic:
            # - DPA when profile_id is mapped in Mapping_CrewAssReviewers.DPA_RoleId
            # - PIC when profile_id is mapped in Mapping_CrewAssReviewers.PIC_RoleId
            # - Otherwise default to OFFICE_PIC (non-global scope)
            mapped_global_role = self._get_global_office_reviewer_role(
                username=normalized_username,
                employee_id=user.employee_id,
            )
            if mapped_global_role == RoleCodes.DPA:
                role = RoleCodes.DPA
                has_global_vessel_access = True
            elif mapped_global_role == RoleCodes.OFFICE_PIC:
                role = RoleCodes.OFFICE_PIC
                has_global_vessel_access = True
            else:
                role = RoleCodes.OFFICE_PIC
                has_global_vessel_access = False

            from .utils import get_profile_permissions, get_office_permissions_by_mapping
            form_ids, process_ids = get_office_permissions_by_mapping(
                username=username,
                employee_id=user.employee_id,
            )
            if not form_ids and not process_ids:
                form_ids, process_ids = get_profile_permissions(user.employee_role, work_side=False)
            if not form_ids and not process_ids:
                # Fallback: some profiles are keyed by role codes (OFFICE_PIC, DPA, etc.)
                form_ids, process_ids = get_profile_permissions(role, work_side=False)

            return AuthenticatedUser(
                user_id=str(user.employee_id),
                login_id=normalized_username,
                user_type="OFFICE",
                full_name=user.full_name,
                role=role,
                email=user.email_id,
                employee_id=user.employee_id,
                department=user.department,
                form_ids=form_ids,
                process_ids=process_ids,
                has_global_vessel_access=has_global_vessel_access,
            )

        except Exception as e:
            logger.error(f"Error authenticating office user: {e}")
            return None

    def _get_global_office_reviewer_role(
        self, username: Optional[str], employee_id: Optional[str]
    ) -> Optional[str]:
        """
        Resolve global office reviewer role from Mapping_CrewAssReviewers.
        Returns RoleCodes.DPA, RoleCodes.OFFICE_PIC, or None.
        """
        from .utils import get_office_global_reviewer_role

        return get_office_global_reviewer_role(
            username=username,
            employee_id=employee_id,
        )






    # ================= PASSWORD =================

    def _verify_password(self, plain_password: str, stored_password: Optional[str]) -> bool:
        if not stored_password:
            return False

        stored_password = stored_password.strip()

        # Plain text
        if plain_password == stored_password:
            return True

        # MD5 legacy
        md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
        if md5_hash.lower() == stored_password.lower():
            return True

        # Django hash
        try:
            if check_password(plain_password, stored_password):
                return True
        except Exception:
            pass

        return False


    # ================= ROLE MAPPING =================

    def _determine_vessel_role(self, rank_name: Optional[str]) -> str:
        if not rank_name:
            return RoleCodes.VESSEL_CREW

        rank = rank_name.strip().upper()

        if rank in ["MASTER", "CAPTAIN"]:
            return RoleCodes.VESSEL_MASTER

        return RoleCodes.VESSEL_CREW

    def _determine_office_role(self, employee_role: Optional[str]) -> str:
        if not employee_role:
            return RoleCodes.OFFICE_PIC

        role_lower = employee_role.lower()

        if "dpa" in role_lower or "designated person" in role_lower:
            return RoleCodes.DPA

        if "ssqe" in role_lower or "safety" in role_lower or "quality" in role_lower:
            return RoleCodes.OFFICE_SSQE

        if "supt" in role_lower or "superintendent" in role_lower:
            return RoleCodes.OFFICE_SUPT

        if "verifier" in role_lower or "pv" in role_lower:
            return RoleCodes.PHYSICAL_VERIFIER

        return RoleCodes.OFFICE_PIC

    # ================= SESSION SUPPORT =================

    def get_user(self, user_id):
        return None
