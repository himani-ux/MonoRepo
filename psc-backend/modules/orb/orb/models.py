# logbook/models.py
import os
from django.db import models
import uuid
from django.utils import timezone



class VesselData(models.Model):
    id = models.UUIDField(primary_key=True)
    vesselName = models.CharField(max_length=500, null=True, blank=True, db_column='VesselName')
    vesselCode = models.CharField(max_length=500, null=True, blank=True)
    deadweight = models.IntegerField(null=True, blank=True)
    loa = models.CharField(max_length=500, null=True, blank=True)
    maxdraft = models.CharField(max_length=500, null=True, blank=True)
    beam = models.CharField(max_length=500, null=True, blank=True)
    grt = models.CharField(max_length=500, null=True, blank=True)
    nrt = models.CharField(max_length=500, null=True, blank=True)
    flags = models.CharField(max_length=500, null=True, blank=True)
    callsign = models.CharField(max_length=500, null=True, blank=True)
    imonumber = models.CharField(max_length=500, null=True, blank=True)
    hatchholds = models.CharField(max_length=500, null=True, blank=True)
    swl = models.CharField(max_length=500, null=True, blank=True)
    vesselothers = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)
    is_deleted = models.BooleanField(null=True, blank=True)
    created_by = models.CharField(max_length=500, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=500, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    lastportofcall = models.CharField(max_length=500, null=True, blank=True)
    piclub = models.UUIDField(null=True, blank=True)
    classificationsociety = models.CharField(max_length=500, null=True, blank=True)
    depth = models.CharField(max_length=500, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=100, null=True, blank=True)
    vesseltypeid = models.UUIDField(null=True, blank=True)
    shipowner = models.TextField(null=True, blank=True)
    shipmanagement = models.TextField(null=True, blank=True)
    propellerpitch = models.DecimalField(max_digits=9, decimal_places=3, null=True, blank=True)
    refcii = models.DecimalField(max_digits=9, decimal_places=5, null=True, blank=True)
    vlsfoemissionfactor = models.DecimalField(max_digits=9, decimal_places=3, null=True, blank=True)
    lsmgoemissionfactor = models.DecimalField(max_digits=9, decimal_places=3, null=True, blank=True)
    # vlsfoldle = models.DecimalField(max_digits=9, decimal_places=3, null=True, blank=True)
    vlsfoworking = models.DecimalField(max_digits=9, decimal_places=3, null=True, blank=True)
    lsmgoidle = models.DecimalField(max_digits=9, decimal_places=3, null=True, blank=True)
    lsmgoworking = models.DecimalField(max_digits=9, decimal_places=3, null=True, blank=True)
    company = models.UUIDField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'VesselData' 


    def __str__(self):
        return f"{self.vesselName} ({self.vesselCode})"
    
    def get_vessel_email(self):
        return self.email
      

class VesselTankType(models.Model):
    id = models.UUIDField(primary_key=True)
    tank_type_name = models.CharField(max_length=100)

    class Meta:
        db_table = "vessel_tank_type"
        managed = False

class VesselTankDetails(models.Model):
    id = models.UUIDField(primary_key=True)
    vessel = models.ForeignKey(
        VesselData, on_delete=models.DO_NOTHING, db_column='vessel_id'
    )
    tank_type = models.ForeignKey(
        'VesselTankType', on_delete=models.DO_NOTHING, db_column='tank_type'
    )
    tank_name = models.CharField(max_length=150)
    capacity = models.DecimalField(max_digits=9, decimal_places=2)
    frame_from = models.IntegerField(null=True, blank=True)
    frame_to = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'vessel_tank_details'
        managed = False



class ShipUserMaster(models.Model):
    userid = models.UUIDField(primary_key=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=100) 
    rankid = models.IntegerField()  

    class Meta:
        db_table = 'ShipUserMaster'
        managed = False 


    



class OperationEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vessel = models.UUIDField(db_column='vessel', db_index=True, null=True, blank=True)
    date = models.DateTimeField(db_column='date')
    orb_code = models.ForeignKey('ORBCodes', on_delete=models.DO_NOTHING, db_column='orb_code_id')
    item_no = models.CharField(max_length=50, db_column='item_no')
    record_of_operation = models.TextField(db_column='record_of_operation', blank=True, null=True)
    status = models.CharField(max_length=20, db_column='status', default="Draft")
    submitted_by = models.CharField(max_length=50, db_column='submitted_by', blank=True, null=True)
    submitted_at = models.DateTimeField(db_column='submitted_at', blank=True, null=True)
    approved_by = models.CharField(max_length=50, db_column='approved_by', blank=True, null=True)
    approved_at = models.DateTimeField(db_column='approved_at', blank=True, null=True)
    rejected_by = models.CharField(max_length=50, db_column='rejected_by', blank=True, null=True)
    rejected_at = models.DateTimeField(db_column='rejected_at', blank=True, null=True)
    created_at = models.DateTimeField(db_column='created_at', auto_now_add=True)
    created_by = models.CharField(max_length=100, db_column='created_by', blank=True, null=True)
    updated_at = models.DateTimeField(db_column='updated_at', auto_now=True)
    updated_by = models.CharField(max_length=50, db_column='updated_by', blank=True, null=True)
    is_deleted = models.BooleanField(db_column='is_deleted', default=False)
    entry_no = models.IntegerField(db_column='entry_no', null=True)
    page_no = models.IntegerField(null=True, blank=True)
    line_no = models.IntegerField(null=True, blank=True) 
    IP = models.CharField(max_length=255, blank=True, null=True) 
    master_print = models.DateTimeField(null=True, blank=True)   
    parent_entry_id = models.ForeignKey('self', on_delete=models.CASCADE, db_column='parent_entry_id', null=True, blank=True)

    class Meta:
        db_table = 'Operations'
        ordering = ['-created_at']
        managed = False
        

    def __str__(self):
        return f"{self.date}  | {self.orb_code_id} | {self.record_of_operation[:50]}... |  Parent ID: {self.parent_entry_id.id if self.parent_entry_id else 'Root'}"



class ORBCodes(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=1, null=False, blank=False)
    part = models.IntegerField(null=False, blank=False)
    description = models.CharField(max_length=500, null=False, blank=False)

    class Meta:
        db_table = 'ORBCodes'
        managed = False # If you want Django to manage this table

    def __str__(self):
        return f"{self.code}-{self.part}"




class MappingORBCodeTankType(models.Model):
    id = models.UUIDField(primary_key=True)
    orb_code = models.ForeignKey(ORBCodes, on_delete=models.DO_NOTHING, db_column='orb_code_id')
    tank_type_id = models.CharField(max_length=50, db_column='tank_type_id')  # ⚡ store as string, no FK

    class Meta:
        db_table = 'mapping_ORBCode_TankType'
        managed = False




class VesselType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vessel_type_code = models.CharField(max_length=255)
    vessel_type_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'vessel_type'
        managed = False  # ✅ Django won't try to create this table




class CurrentVessel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vessel_id = models.UUIDField(null=False, blank=False)  # Selected vessel
    selected_at = models.DateTimeField(auto_now_add=True)  # Timestamp when vessel was selected
    is_active = models.BooleanField(default=True)  # Optional: deactivate old selection instead of deleting

    class Meta:
        db_table = 'current_vessel'
        verbose_name = "Current Vessel"
        verbose_name_plural = "Current Vessels"
        managed = False

    def __str__(self):
        return f"User {self.user_id} selected Vessel {self.vessel_id}"





class GeneratedPDF(models.Model):
    """
    Model to store metadata about generated PDFs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255, help_text="Name of the saved PDF file.")
    filepath = models.CharField(max_length=500, help_text="Full path to the saved PDF file on the server.")
    title = models.CharField(max_length=500, help_text="Title of the PDF content (e.g., 'Approved Logbook Entries 2023-10-27').")
    description = models.TextField(blank=True, null=True, help_text="Optional description.")
    created_by = models.CharField(max_length=100, help_text="User who generated the PDF.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Time when the PDF was generated and saved.")
    vessel_id = models.UUIDField(db_column='vessel_id', db_index=True, null=True, blank=True, help_text="ID of the vessel the PDF relates to.")

    def __str__(self):
        return f"{self.title} - {self.created_at}"

    class Meta:
        db_table = 'GeneratedPDFs'
        ordering = ['-created_at'] 
        managed = False



# class ShipUsersLogin(models.Model):
#     """
#     Table for storing crew login credentials.
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     CrewID = models.CharField(max_length=50, unique=True)  # Unique identifier for the crew member
#     Password = models.CharField(max_length=100)  # Store hashed password in production!
#     is_active = models.BooleanField(default=True)
#     is_deleted = models.BooleanField(default=False)
#     Created_By = models.CharField(max_length=50, null=True, blank=True)
#     Updated_By = models.CharField(max_length=50, null=True, blank=True)
#     Created_At = models.DateTimeField(null=True, blank=True)
#     Updated_At = models.DateTimeField(null=True, blank=True)
#     Temp_Password = models.CharField(max_length=100, null=True, blank=True)

#     class Meta:
#         db_table = 'Ship_UsersLogin'
#         managed = False  # Use existing database table

    # def __str__(self):
    #     return f"User {self.CrewID}"

# class HRM501(models.Model):
#     """
#     Table containing crew details including rank.
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     auto_id = models.CharField(max_length=255, null=True, blank=True)  # This might be the primary key you mentioned
#     user_id = models.CharField(max_length=255, null=True, blank=True)  # Might be used for linking, but not directly used here
#     rank_name = models.CharField(max_length=255, null=True, blank=True)  # The actual rank name (e.g., "Master", "Chief Engineer")
#     department_name = models.CharField(max_length=255, null=True, blank=True)
#     join_date = models.CharField(max_length=50, null=True, blank=True)  # Assuming date is stored as string
#     first_name = models.CharField(max_length=255, null=True, blank=True)
#     surname = models.CharField(max_length=255, null=True, blank=True)
#     mobile = models.CharField(max_length=255, null=True, blank=True)
#     email_id = models.CharField(max_length=255, null=True, blank=True)

#     class Meta:
#         db_table = 'HRM501'
#         managed = False  # Use existing database table

#     def __str__(self):
#         return f"{self.first_name} {self.surname} - {self.rank_name}"



class FinalCrewList(models.Model):
    """
    Table that maps CrewID to Crew_ref_id.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CrewID = models.CharField(max_length=7, null=True, blank=True)  # Link to Ship_UsersLogin
    CrewName = models.CharField(max_length=100, null=True, blank=True)
    Crew_ref_id = models.UUIDField(null=True, blank=True)  # Link to HRM501.id
    Evl_ref_id = models.UUIDField(null=True, blank=True)
    Assg_Vessel = models.UUIDField(null=True, blank=True)
    Tentative_join_port = models.UUIDField(null=True, blank=True)
    Tentative_join_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    Crew_Status = models.UUIDField(null=True, blank=True)
    is_planned = models.BooleanField(default=False)

    class Meta:
        db_table = 'Final_crew_list'
        managed = False  # Use existing database table

    def __str__(self):
        return f"Crew {self.CrewID} - Ref ID: {self.Crew_ref_id}"
    



class MasterAppliedRank(models.Model):
    """
    Model for the master_applied_rank table.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rank_name = models.CharField(max_length=255, null=True, blank=True)  # varchar(max)
    rank_id = models.CharField(max_length=255, null=True, blank=True)  # varchar(max)
    rank_description = models.TextField(null=True, blank=True)  # varchar(max)
    is_active = models.BooleanField(default=True)  # bit
    is_deleted = models.BooleanField(default=False)  # bit
    created_by = models.CharField(max_length=100, null=True, blank=True)  # varchar(100)
    created_date = models.DateTimeField(null=True, blank=True)  # datetime
    updated_by = models.CharField(max_length=100, null=True, blank=True)  # varchar(100)
    updated_date = models.DateTimeField(null=True, blank=True)  # datetime
    rank_level = models.IntegerField(null=True, blank=True)  # int
    department = models.UUIDField(null=True, blank=True)  # uniqueidentifier

    class Meta:
        db_table = 'master_applied_rank'
        managed = False  # Use existing database table

    def __str__(self):
        return f"Rank: {self.rank_name} (ID: {self.id})"
    



# class OrbProfile(models.Model):
#     """
#     Model representing the orb_profiles table.
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     profile_id = models.UUIDField(db_column='profile_id') # Foreign key, stored as UUID
#     profile_name = models.CharField(max_length=255, null=True, blank=True)
#     work_side = models.BooleanField(default=False) # Maps to BIT (True/False)
#     form_ids = models.TextField(null=True, blank=True) # Maps to VARCHAR(MAX)
#     process_ids = models.TextField(null=True, blank=True) # Maps to VARCHAR(MAX)
#     created_on = models.DateTimeField(auto_now_add=True) # Defaults to creation time (UTC recommended)
#     is_active = models.BooleanField(default=True) # Maps to BIT (True/False)
#     is_deleted = models.BooleanField(default=False) # Maps to BIT (True/False)

#     class Meta:
#         db_table = 'msc_profiles' # Specify the exact table name
#         managed = False  # Set to True if Django should manage migrations for this table
#         # If the table is managed externally, set managed = False
#         # managed = False

#     def __str__(self):
#         return f"Profile: {self.profile_name or 'Unnamed'} (ID: {self.id})"



class CrewOnboardingHistory(models.Model):
    """
    Model representing the crew onboarding history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CrewID = models.CharField(max_length=255, null=True, blank=True) # Assuming varchar(max)
    Vessel = models.UUIDField(null=True, blank=True) # Assuming uniqueidentifier
    SignOnDate = models.DateTimeField(null=True, blank=True) # datetime
    SignOnPort = models.CharField(max_length=200, null=True, blank=True) # varchar(200)
    CrewStatus = models.UUIDField(null=True, blank=True) # Assuming uniqueidentifier for status
    is_active = models.BooleanField(default=True) # bit
    is_deleted = models.BooleanField(default=False) # bit
    is_verifiedByMtr = models.BooleanField(default=False) # bit
    created_by = models.CharField(max_length=255, null=True, blank=True) # varchar(max)
    created_date = models.DateTimeField(auto_now_add=True) # datetime, defaults to creation time
    updated_by = models.CharField(max_length=255, null=True, blank=True) # varchar(max)
    updated_date = models.DateTimeField(auto_now=True) # datetime, updates on save
    CycleId = models.UUIDField(null=True, blank=True) # Assuming uniqueidentifier
    Replacement_For = models.CharField(max_length=7, null=True, blank=True) # varchar(7)

    class Meta:
        db_table = 'Crew_Onboarding_History' # Specify the exact table name
        managed = False  # Set to True if Django should manage migrations for this table
        # If the table is managed externally, set managed = False
        # managed = False

    def __str__(self):
        return f"Crew Onboarding: {self.CrewID} on {self.SignOnDate or 'Unknown Date'}"

  