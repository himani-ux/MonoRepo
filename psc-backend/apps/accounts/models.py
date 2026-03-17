"""
Unmanaged models for existing database tables.

These models map to existing tables in the shared database.
DO NOT modify these tables - they are managed by other systems.

Per BACKEND_STRUCTURE.md Section 2: Existing Tables (Reference Only)
"""

import uuid
from django.db import models


class VesselData(models.Model):
    """
    Existing vessel data table.
    DO NOT MODIFY - managed by external system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    vesselName = models.CharField(max_length=255, db_column='vesselName')
    vesselCode = models.CharField(max_length=50, db_column='vesselCode')
    imoNumber = models.CharField(max_length=255, null=True, blank=True, db_column='imoNumber')
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'VesselData'

    def __str__(self):
        return f"{self.vesselCode} - {self.vesselName}"


class HRM501(models.Model):
    """
    Existing crew (vessel user) table.
    DO NOT MODIFY - managed by external HRM system.

    This table contains vessel personnel records.
    The user_id field is used for authentication (username).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    CrewID = models.CharField(max_length=7, db_column='CrewID')
    first_name = models.CharField(max_length=255, null=True, blank=True)
    surname = models.CharField(max_length=255, null=True, blank=True)
    rank_name = models.CharField(max_length=255, null=True, blank=True)
    department_name = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    # vessel_id = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'HRM501'

    def __str__(self):
        return f"{self.CrewID} - {self.first_name} {self.surname}"

    @property
    def full_name(self):
        """Return the full name of the crew member."""
        first = self.first_name or ''
        last = self.surname or ''
        return f"{first} {last}".strip() or self.CrewID


class OfficeUser(models.Model):
    """
    Existing office user table.
    DO NOT MODIFY - managed by external system.

    This table contains office personnel records (PIC, SSQE, Supt, DPA, etc.)
    """
    employee_id = models.CharField(max_length=20, primary_key=True)
    employee_name = models.CharField(max_length=100, null=True, blank=True)
    display_name = models.CharField(max_length=100, null=True, blank=True)
    email_id = models.CharField(max_length=100, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    employee_role = models.CharField(max_length=45, null=True, blank=True)
    department = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self):
        return f"{self.employee_id} - {self.display_name or self.employee_name}"

    @property
    def full_name(self):
        """Return the display name or employee name."""
        return self.display_name or self.employee_name or self.employee_id


class MasterRoleByVessel(models.Model):
    """
    Existing vessel-role assignment table for office users.
    DO NOT MODIFY - managed by external system.

    Links office users to vessels they can access.
    """
    Id = models.UUIDField(primary_key=True, db_column='Id', default=uuid.uuid4)
    VesselId = models.UUIDField(db_column='VesselId')
    RoleId = models.UUIDField(db_column='RoleId', null=True, blank=True)
    UserId = models.CharField(max_length=100, db_column='UserId')
    IsActive = models.BooleanField(default=True, db_column='IsActive')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'master_RoleByVessel'

    def __str__(self):
        return f"{self.UserId} - Vessel {self.VesselId}"


class MasterRole(models.Model):
    """
    Office role master table.
    DO NOT MODIFY - managed by external system.
    """
    id = models.UUIDField(primary_key=True, editable=False)
    role_name = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    is_deleted = models.BooleanField(default=False, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'master_role'

    def __str__(self):
        return f"MasterRole {self.id} - {self.role_name}"


class MappingRoleUser(models.Model):
    """
    Maps office users to roles.
    DO NOT MODIFY - managed by external system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    userid = models.CharField(max_length=50, null=True, blank=True)
    role_id = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    is_deleted = models.BooleanField(default=False, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'mapping_role_user'

    def __str__(self):
        return f"MappingRoleUser {self.id} - User: {self.userid}, Role: {self.role_id}"


class MasterAppliedRank(models.Model):
    """
    Existing rank master table.
    DO NOT MODIFY - managed by external system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    rank_name = models.CharField(max_length=255, null=True, blank=True)
    rank_id = models.CharField(max_length=255, null=True, blank=True)
    department = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'master_applied_rank'

    def __str__(self):
        return self.rank_name or self.rank_id or str(self.id)


class MasterPscRole(models.Model):
    """
    PSC module-specific roles.

    This table IS managed by the PSC module (unlike the others).
    Per BACKEND_STRUCTURE.md Section 3.5

    Role types:
    - VESSEL: VESSEL_MASTER, VESSEL_CREW
    - OFFICE: OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT, DPA, PHYSICAL_VERIFIER
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_code = models.CharField(max_length=50, unique=True)
    role_name = models.CharField(max_length=100)
    role_type = models.CharField(max_length=20)  # VESSEL or OFFICE
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        # This table is managed by PSC module but may already exist
        # Set managed=False to avoid migration conflicts
        managed = False
        db_table = 'master_psc_role'

    def __str__(self):
        return f"{self.role_code} - {self.role_name}"


# Role code constants for use throughout the app
class RoleCodes:
    """PSC role codes as defined in master_psc_role."""
    VESSEL_MASTER = 'VESSEL_MASTER'
    VESSEL_CREW = 'VESSEL_CREW'
    OFFICE_PIC = 'OFFICE_PIC'
    OFFICE_SSQE = 'OFFICE_SSQE'
    OFFICE_SUPT = 'OFFICE_SUPT'
    DPA = 'DPA'
    PHYSICAL_VERIFIER = 'PHYSICAL_VERIFIER'

    VESSEL_ROLES = [VESSEL_MASTER, VESSEL_CREW]
    OFFICE_ROLES = [OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT, DPA, PHYSICAL_VERIFIER]

    # Roles that can perform PIC review actions
    PIC_REVIEWERS = [OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT]

    # Roles that can perform DPA actions
    DPA_ROLES = [DPA]


class MscProfile(models.Model):
    """
    Model for dbo.msc_profiles
    Stores form/process permissions per profile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_id = models.UUIDField(null=False, blank=False, default=uuid.uuid4)
    profile_name = models.CharField(max_length=255, null=False, blank=False)
    work_side = models.BooleanField(null=False, blank=False)
    form_ids = models.TextField(null=True, blank=True)
    process_ids = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(null=False, blank=False, default=True)
    is_deleted = models.BooleanField(null=False, blank=False, default=False)

    class Meta:
        managed = False
        db_table = 'msc_profiles'


class CrewOnboardingHistory(models.Model):
    """
    Model for dbo.Crew_Onboarding_History
    Unmanaged table (existing SQL Server table)
    """

    id = models.UUIDField(
        primary_key=True,
        db_column='id',
        default=uuid.uuid4,
        editable=False
    )

    CrewID = models.CharField(
        max_length=255,
        db_column='CrewID',
        null=True,
        blank=True
    )

    Vessel = models.UUIDField(
        db_column='Vessel',
        null=True,
        blank=True
    )

    SignOnDate = models.DateTimeField(
        db_column='SignOnDate',
        null=True,
        blank=True
    )

    SignOnPort = models.CharField(
        max_length=200,
        db_column='SignOnPort',
        null=True,
        blank=True
    )

    CrewStatus = models.UUIDField(
        db_column='CrewStatus',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        db_column='is_active',
        null=True,
        blank=True
    )

    is_deleted = models.BooleanField(
        db_column='is_deleted',
        null=True,
        blank=True
    )

    is_verifiedByMtr = models.BooleanField(
        db_column='is_verifiedByMtr',
        null=True,
        blank=True
    )

    created_by = models.CharField(
        max_length=255,
        db_column='created_by',
        null=True,
        blank=True
    )

    created_date = models.DateTimeField(
        db_column='created_date',
        null=True,
        blank=True
    )

    updated_by = models.CharField(
        max_length=255,
        db_column='updated_by',
        null=True,
        blank=True
    )

    updated_date = models.DateTimeField(
        db_column='updated_date',
        null=True,
        blank=True
    )

    CycleId = models.UUIDField(
        db_column='CycleId',
        null=True,
        blank=True
    )

    Replacement_For = models.CharField(
        max_length=7,
        db_column='Replacement_For',
        null=True,
        blank=True
    )

    SignOffDate = models.DateTimeField(
        db_column='SignOffDate',
        null=True,
        blank=True
    )

    SignOffPort = models.CharField(
        max_length=200,
        db_column='SignOffPort',
        null=True,
        blank=True
    )

    SignOffReason = models.CharField(
        max_length=250,
        db_column='SignOffReason',
        null=True,
        blank=True
    )

    SelectedSignOffReason = models.CharField(
        max_length=250,
        db_column='SelectedSignOffReason',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'Crew_Onboarding_History'
        managed = False  # VERY IMPORTANT (existing table)




class ShipUsersLogin(models.Model):
    """
    Model for dbo.Ship_UsersLogin
    Existing SQL Server table (unmanaged)
    """

    id = models.UUIDField(
        primary_key=True,
        db_column='id',
        default=uuid.uuid4,
        editable=False
    )

    CrewID = models.CharField(
        max_length=50,
        db_column='CrewID',
        null=True,
        blank=True
    )

    Password = models.CharField(
        max_length=255,
        db_column='Password',
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        db_column='is_active',
        null=True,
        blank=True
    )

    is_deleted = models.BooleanField(
        db_column='is_deleted',
        null=True,
        blank=True
    )

    Created_By = models.CharField(
        max_length=255,
        db_column='Created_By',
        null=True,
        blank=True
    )

    Updated_By = models.CharField(
        max_length=255,
        db_column='Updated_By',
        null=True,
        blank=True
    )

    Created_At = models.DateTimeField(
        db_column='Created_At',
        null=True,
        blank=True
    )

    Updated_At = models.DateTimeField(
        db_column='Updated_At',
        null=True,
        blank=True
    )

    Temp_Password = models.CharField(
        max_length=255,
        db_column='Temp_Password',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'Ship_UsersLogin'
        managed = False  # VERY IMPORTANT
