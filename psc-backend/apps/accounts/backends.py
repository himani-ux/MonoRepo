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
from django.db import DatabaseError, OperationalError, ProgrammingError, connection, models
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from .models import HRM501, OfficeUser, RoleCodes, ShipUsersLogin, CrewOnboardingHistory
from .utils import (
    office_profile_has_global_read_scope,
    resolve_current_office_permission_snapshot,
    resolve_safety_role_name,
    resolve_current_vessel_permission_snapshot,
)

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
        role_name: Optional[str] = None,
        safety_role_name: Optional[str] = None,
        vessel_ids: Optional[list[str]] = None,
        vessel_names: Optional[list[str]] = None,
        profile_id: Optional[str] = None,
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
        self.role_name = role_name or role
        self.safety_role_name = safety_role_name or self.role_name
        self.profile_id = str(profile_id) if profile_id not in (None, "") else None
        self.vessel_ids = vessel_ids or ([str(vessel_id)] if vessel_id else [])
        self.vessel_names = vessel_names or ([str(vessel_name)] if vessel_name else [])

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
            "vessel_ids": self.vessel_ids,
            "vessel_names": self.vessel_names,
            "display_name": self.display_name,
            "role_name": self.role_name,
            "safety_role_name": self.safety_role_name,
            "profile_id": self.profile_id,
            "username": self.username,
            "UserName": self.username,
            "work_side": self.work_side,
            "first_name": self.first_name,
            "surname": self.surname,
            "is_chief": self.is_chief,
            "legacy_user_type": self.legacy_user_type,
        }


def _assigned_office_vessel_ids(user: AuthenticatedUser) -> list[str]:
    if (user.user_type or "").upper() != "OFFICE":
        return list(user.vessel_ids)
    if user.has_global_vessel_access is True:
        return []

    try:
        from core.vessel_access import get_office_user_identifiers, get_office_user_vessel_ids

        vessel_ids = get_office_user_vessel_ids(get_office_user_identifiers(user))
    except Exception as exc:
        logger.warning("Failed to populate office vessel assignments for %s: %s", user.username, exc)
        return []

    if vessel_ids is None:
        return []
    return [str(vessel_id) for vessel_id in vessel_ids if vessel_id not in (None, "")]


def _lookup_vessel_names(vessel_ids: list[str]) -> list[str]:
    normalized_ids = [str(vessel_id).strip() for vessel_id in vessel_ids if str(vessel_id or "").strip()]
    if not normalized_ids:
        return []

    try:
        with connection.cursor() as cursor:
            if connection.vendor == "sqlite":
                placeholders = ",".join(["%s"] * len(normalized_ids))
                cursor.execute(
                    f"""
                    SELECT id, vesselCode, vesselName
                    FROM VesselData
                    WHERE id IN ({placeholders})
                      AND COALESCE(is_deleted, 0) = 0
                    """,
                    normalized_ids,
                )
            else:
                placeholders = ",".join(["CAST(%s AS uniqueidentifier)"] * len(normalized_ids))
                cursor.execute(
                    f"""
                    SELECT id, vesselCode, vesselName
                    FROM VesselData
                    WHERE id IN ({placeholders})
                      AND is_active = 1
                      AND is_deleted = 0
                    """,
                    normalized_ids,
                )
            rows = {
                str(row[0]).strip().lower(): " - ".join(
                    value for value in (str(row[1] or "").strip(), str(row[2] or "").strip()) if value
                )
                for row in cursor.fetchall()
            }
    except (DatabaseError, OperationalError, ProgrammingError, ValueError):
        rows = {}

    return [rows.get(vessel_id.lower(), vessel_id) for vessel_id in normalized_ids]


def _assigned_office_vessel_names(user: AuthenticatedUser) -> list[str]:
    if (user.user_type or "").upper() != "OFFICE":
        return list(user.vessel_names)
    if user.has_global_vessel_access is True:
        return []
    return _lookup_vessel_names(user.vessel_ids)

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

            user_type = validated_token.get("user_type", "")
            role = validated_token.get("role", "")
            full_name = validated_token.get("full_name", "")
            email = validated_token.get("email")
            employee_id = validated_token.get("employee_id")
            department = validated_token.get("department")
            rank = validated_token.get("rank")
            role_name = validated_token.get("role_name")
            safety_role_name = validated_token.get("safety_role_name")
            profile_id = validated_token.get("profile_id")
            form_ids = validated_token.get("form_ids") or []
            process_ids = validated_token.get("process_ids") or []
            has_global_vessel_access = validated_token.get("has_global_vessel_access")

            try:
                normalized_user_type = str(user_type or "").upper()
                if normalized_user_type == "OFFICE":
                    snapshot = resolve_current_office_permission_snapshot(
                        login_id=validated_token.get("login_id") or validated_token.get("username"),
                        employee_id=employee_id or user_id,
                        role=role,
                        has_global_vessel_access=has_global_vessel_access,
                        full_name=full_name,
                        email=email,
                        department=department,
                    )
                    role = snapshot.get("role") or role
                    role_name = snapshot.get("role_name") or role_name
                    safety_role_name = snapshot.get("safety_role_name") or safety_role_name
                    profile_id = snapshot.get("profile_id") or profile_id
                    full_name = snapshot.get("full_name") or full_name
                    email = snapshot.get("email") or email
                    employee_id = snapshot.get("employee_id") or employee_id
                    department = snapshot.get("department") or department
                    form_ids = snapshot.get("form_ids") or []
                    process_ids = snapshot.get("process_ids") or []
                    has_global_vessel_access = snapshot.get("has_global_vessel_access")
                elif normalized_user_type == "VESSEL":
                    snapshot = resolve_current_vessel_permission_snapshot(
                        user_type=user_type,
                        role=role,
                        rank=rank,
                        full_name=full_name,
                        department=department,
                    )
                    role_name = snapshot.get("role_name") or role_name
                    safety_role_name = snapshot.get("safety_role_name") or safety_role_name
                    full_name = snapshot.get("full_name") or full_name
                    department = snapshot.get("department") or department
                    form_ids = snapshot.get("form_ids") or []
                    process_ids = snapshot.get("process_ids") or []
            except Exception as exc:
                logger.warning(
                    "JWT permission refresh failed for user %s; using token claims: %s",
                    user_id,
                    exc,
                )

            authenticated_user = AuthenticatedUser(
                user_id=user_id,
                login_id=validated_token.get("login_id"),
                user_type=user_type,
                full_name=full_name,
                role=role,
                vessel_id=validated_token.get("vessel_id"),
                vessel_name=validated_token.get("vessel_name"),  # ✅ FIXED
                vessel_code=validated_token.get("vessel_code"),
                email=email,
                employee_id=employee_id,
                crew_id=validated_token.get("crew_id"),
                rank=rank,
                department=department,
                form_ids=form_ids,
                process_ids=process_ids,
                has_global_vessel_access=has_global_vessel_access,
                role_name=role_name,
                safety_role_name=safety_role_name,
                profile_id=profile_id,
                vessel_ids=validated_token.get("vessel_ids") or None,
                vessel_names=validated_token.get("vessel_names") or None,
            )
            authenticated_user.vessel_ids = _assigned_office_vessel_ids(authenticated_user)
            authenticated_user.vessel_names = _assigned_office_vessel_names(authenticated_user)
            return authenticated_user
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
            from .utils import get_profile_permissions, merge_audit_default_process_ids
            form_ids, process_ids = get_profile_permissions(rank_name, work_side=True)
            process_ids = merge_audit_default_process_ids(process_ids, rank_name, role)

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
                role_name=rank_name,
                safety_role_name=resolve_safety_role_name(
                    user_type='VESSEL',
                    role=role,
                    rank=rank_name,
                ),
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
            role = RoleCodes.OFFICE_PIC
            initial_safety_role_name = resolve_safety_role_name(
                user_type='OFFICE',
                role=role,
                profile_name=user.employee_role,
            )
            if mapped_global_role == RoleCodes.DPA:
                role = RoleCodes.DPA
                has_global_vessel_access = True
            elif mapped_global_role == RoleCodes.OFFICE_PIC:
                role = RoleCodes.OFFICE_PIC
                has_global_vessel_access = True
            elif initial_safety_role_name == "FM":
                has_global_vessel_access = True
            elif office_profile_has_global_read_scope(user.employee_role):
                has_global_vessel_access = True
            else:
                role = RoleCodes.OFFICE_PIC
                has_global_vessel_access = False

            safety_role_name = resolve_safety_role_name(
                user_type='OFFICE',
                role=role,
                profile_name=user.employee_role,
            )

            from .utils import (
                get_profile_permissions,
                get_office_permissions_by_mapping,
                get_office_profile_id_by_mapping,
                merge_audit_default_process_ids,
            )
            form_ids, process_ids = get_office_permissions_by_mapping(
                username=username,
                employee_id=user.employee_id,
            )
            if not form_ids and not process_ids:
                form_ids, process_ids = get_profile_permissions(user.employee_role, work_side=False)
            if not form_ids and not process_ids:
                # Fallback: some profiles are keyed by role codes (OFFICE_PIC, DPA, etc.)
                form_ids, process_ids = get_profile_permissions(role, work_side=False)
            profile_id = get_office_profile_id_by_mapping(
                username=normalized_username,
                employee_id=user.employee_id,
                profile_name=user.employee_role,
            )
            role_default = role if role == RoleCodes.DPA else None
            process_ids = merge_audit_default_process_ids(process_ids, user.employee_role, role_default)

            authenticated_user = AuthenticatedUser(
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
                role_name=user.employee_role or role,
                safety_role_name=safety_role_name,
                profile_id=profile_id,
            )
            authenticated_user.vessel_ids = _assigned_office_vessel_ids(authenticated_user)
            authenticated_user.vessel_names = _assigned_office_vessel_names(authenticated_user)
            return authenticated_user

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

        if rank in ["MASTER", "CAPTAIN", "ACTING MASTER"]:
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
