from django.db import models
import uuid
from django.utils import timezone
from modules.orb.orb.models import VesselData,MasterAppliedRank,CrewOnboardingHistory

class MscProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # UUID primary key
    profile_id = models.UUIDField(null=False, blank=False, default=uuid.uuid4)
    profile_name = models.CharField(max_length=255, null=False, blank=False)    # Name of the profile
    work_side = models.BooleanField(null=False, blank=False)                    # Flag for work side
    form_ids = models.TextField(null=True, blank=True)                          # Store form IDs (e.g., "F_001,F_002")
    process_ids = models.TextField(null=True, blank=True)                       # Store process IDs (e.g., "P_001,P_002")
    created_on = models.DateTimeField(auto_now_add=True)                        # Timestamp of creation
    is_active = models.BooleanField(null=False, blank=False, default=True)      # Flag for active status
    is_deleted = models.BooleanField(null=False, blank=False, default=False)    # Flag for soft deletion

    def _str_(self):
        return self.profile_name # String representation of the model instance

    class Meta:
        managed = False
        # Optional: Add database table name if different from default
        db_table = 'msc_profiles'
        pass # You can add other meta options here if needed




# class VesselData(models.Model):
#     id = models.UUIDField(primary_key=True, editable=False) 
#     vesselName = models.CharField(max_length=255, null=True, blank=True)
#     vesselCode = models.CharField(max_length=50, null=True, blank=True)
#     email = models.EmailField(max_length=100, null=True, blank=True)

#     class Meta:
#         db_table = 'VesselData' # Specify the exact name of your database table
#         managed = False # Important! This tells Django not to manage the table (create/migrate it)
#         # If you want Django to manage the table, set managed = True and remove db_table or adjust it.

#     def __str__(self):
#         return f"{self.vesselName} ({self.vesselCode})"
    
#     def get_vessel_email(self):
#         return self.email
    

class MscType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'msc_type'
        managed = False

    def __str__(self):
        return self.name
    

class MscSubCat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'msc_sub_cat'
        managed = False

    def __str__(self):
        return self.name
    

class MscPriority(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'msc_priority'
        managed = False

    def __str__(self):
        return self.name





# class CrewOnboardingHistory(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     CrewID = models.CharField(max_length=255, null=True, blank=True)
#     Vessel = models.UUIDField(null=True, blank=True)
#     SignOnDate = models.DateTimeField(null=True, blank=True)
#     SignOnPort = models.CharField(max_length=200, null=True, blank=True)
#     CrewStatus = models.UUIDField(null=True, blank=True)
#     is_active = models.BooleanField(default=True, null=True, blank=True)
#     is_deleted = models.BooleanField(default=False, null=True, blank=True)
#     is_verifiedByMtr = models.BooleanField(null=True, blank=True)
#     created_by = models.CharField(max_length=255, null=True, blank=True)
#     created_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
#     updated_by = models.CharField(max_length=255, null=True, blank=True)
#     updated_date = models.DateTimeField(null=True, blank=True)
#     CycleId = models.UUIDField(null=True, blank=True)
#     Replacement_For = models.CharField(max_length=7, null=True, blank=True)
#     class Meta:
#         db_table = "Crew_Onboarding_History"
#         managed = False



class HRM501(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_id = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    rank_name = models.CharField(max_length=255, null=True, blank=True)
    department_name = models.CharField(max_length=255, null=True, blank=True)
    join_date = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    surname = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=255, null=True, blank=True)
    email_id = models.CharField(max_length=255, null=True, blank=True)
    selected_role = models.CharField(max_length=255, null=True, blank=True)
    selected_location = models.CharField(max_length=255, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    alternate_mobile = models.CharField(max_length=255, null=True, blank=True)
    place_of_birth = models.CharField(max_length=255, null=True, blank=True)
    date_of_birth = models.DateTimeField(null=True, blank=True)
    gender = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)
    marital_status = models.CharField(max_length=255, null=True, blank=True)
    full_address = models.TextField(null=True, blank=True)
    eng_spoken = models.CharField(max_length=255, null=True, blank=True)
    eng_written = models.CharField(max_length=255, null=True, blank=True)
    eng_understanding = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(null=True, blank=True)
    is_deleted = models.BooleanField(null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)
    upload_photo_name = models.CharField(max_length=255, null=True, blank=True)
    is_accepted = models.BooleanField(null=True, blank=True)
    is_verified_forwarded = models.BooleanField(null=True, blank=True)
    forwarded_to = models.CharField(max_length=255, null=True, blank=True)
    forwarded_by = models.CharField(max_length=255, null=True, blank=True)
    is_rejected = models.CharField(max_length=255, null=True, blank=True)
    upload_sign_name = models.CharField(max_length=255, null=True, blank=True)
    skypeID = models.CharField(max_length=255, null=True, blank=True)
    ProfileCompletionContainer = models.CharField(max_length=3, null=True, blank=True)
    notificationCount = models.CharField(max_length=255, null=True, blank=True)
    CrewID = models.CharField(max_length=7, null=True, blank=True)

    class Meta:
        db_table = 'HRM501'
        managed = False

    def __str__(self):
        return f"{self.first_name} {self.surname} - {self.rank_name}"    



# class MasterAppliedRank(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     rank_name = models.CharField(max_length=255, null=True, blank=True)
#     rank_id = models.CharField(max_length=255, null=True, blank=True)
#     rank_description = models.TextField(null=True, blank=True)
#     is_active = models.BooleanField(null=True, blank=True)
#     is_deleted = models.BooleanField(default=False, null=True, blank=True)
#     created_by = models.CharField(max_length=100, null=True, blank=True)
#     created_date = models.DateTimeField(default=timezone.now, null=True,blank=True)
#     updated_by = models.CharField(max_length=100, null=True, blank=True)
#     updated_date = models.DateTimeField(null=True, blank=True)
#     rank_level = models.IntegerField(null=True, blank=True)
#     class Meta:
#         db_table = "master_applied_rank"
#         managed = False        



class Msc2ndSubCat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department_id = models.UUIDField()  # stores the department.id from department table
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'msc_2nd_sub_cat'
        managed = False

    def __str__(self):
        return f"{self.name}"
    

class MscCategory(models.Model):
    """
    Represents a category for MSC notifications (e.g., 'Internal', 'External').
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True) 
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'msc_category'
        managed = False 

    def __str__(self):
        return self.name
    

class MscData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sr_no = models.CharField(max_length=255, null=True, blank=True)
    msc_type = models.ForeignKey(MscType, on_delete=models.SET_NULL, null=True, blank=True, db_column='msc_type') # Links to MscType.id
    dept =  models.UUIDField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    sub_category = models.ForeignKey(MscSubCat, on_delete=models.SET_NULL, null=True, blank=True, db_column='sub_category')
    second_sub_category = models.ForeignKey(Msc2ndSubCat, on_delete=models.SET_NULL, null=True, blank=True, db_column='second_sub_category') # Links to Msc2ndSubCat.id
    office_instructions = models.TextField(null=True, blank=True)
    hashtags = models.CharField(max_length=255, null=True, blank=True)
    attachment_name = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    publish_status = models.IntegerField()
    publish_comment = models.TextField( null=True, blank=True)
    published_by = models.CharField(max_length=255, null=True, blank=True)
    published_on = models.DateTimeField(null=True, blank=True)
    is_superseeded = models.BooleanField(null=True, default=False)
    superseeded_by = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(null=True, default=True)
    is_deleted = models.BooleanField(null=True, default=False)
    priority = models.ForeignKey(MscPriority, on_delete=models.SET_NULL, null=True, blank=True, db_column='priority') # Links to MscPriority.id
    attachment_path = models.CharField(max_length=500, null=True, blank=True)
    title = models.TextField(blank=True, null=True)
    vessel_id = models.TextField(blank=True, null=True)
    

    class Meta:
        db_table = 'msc_data'
        managed = False
         # Optional helper: convert vessel_id CSV to list

    def __str__(self):
        return self.sr_no or str(getattr(self, 'id', 'NoID')) # Use getattr in case 'id' field is not defined yet

    # Optional helper: convert vessel_id CSV to list
    def vessel_id_list(self):
        if self.vessel_id:
            return [v.strip() for v in self.vessel_id.split(',')]
        return []

    # Optional helper: save list of UUIDs easily
    def set_vessel_ids(self, uuid_list):
        self.vessel_id = ', '.join(str(u) for u in uuid_list)
        self.save()

    def generate_formatted_id(self):
        """Generates KSM/{type}/{dept_display_name}/{YYYY}-{serial:04d}"""
        if not self.msc_type or self.dept is None or not self.created_at:
            return None
        
        try:
            # Map numeric dept value to display name
            if self.dept == 0:
                dept_display_name = 'SEQ'
            elif self.dept == 1:
                dept_display_name = 'Technical'
            else:
                dept_display_name = 'Unknown'
            
            # Extract serial number from sr_no if it exists and has the expected format
            if self.sr_no and '-' in self.sr_no:
                serial = int(self.sr_no.split('-')[-1])
                year = self.created_at.year
                # Use the related object's name for the formatted ID
                return f"KSM/{self.msc_type.name if self.msc_type else 'Unknown'}/{dept_display_name}/{year}-{serial:04d}"
            else:
                # If sr_no doesn't have expected format, reconstruct from available data
                # Get the next serial number for this type and year
                # Use the related object's name for filtering
                last_record = MscData.objects.filter(
                    msc_type=self.msc_type, # Use the related object
                    created_at__year=self.created_at.year,
                    sr_no__isnull=False
                ).order_by('sr_no').last()
                
                if last_record and last_record.sr_no:
                    try:
                        last_serial = int(last_record.sr_no.split('-')[-1])
                        next_serial = last_serial + 1
                    except (ValueError, IndexError):
                        next_serial = 1
                else:
                    next_serial = 1
                    
                year = self.created_at.year
                # Use the related object's name for the formatted ID
                return f"KSM/{self.msc_type.name if self.msc_type else 'Unknown'}/{dept_display_name}/{year}-{next_serial:04d}"
                
        except (ValueError, IndexError, AttributeError, Exception):
            # Fallback: return sr_no if available, otherwise basic format
            if self.sr_no:
                return self.sr_no
            return f"KSM/{self.msc_type.name if self.msc_type else 'Unknown'}/{'SEQ' if self.dept == 0 else 'Technical' if self.dept == 1 else 'Unknown'}/{self.created_at.year}-0001"    
        





    


class MscShipNotification(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    msc_sr_no_val = models.CharField(max_length=255, null=True, blank=True, db_column='msc_sr_no_')
    vessel_link = models.ForeignKey(VesselData, on_delete=models.CASCADE, db_column='vessel_id')
    delivered_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    


    class Meta:
        db_table = 'msc_ship_notification' 
        managed = False
    def __str__(self):
        return f"{self.msc_sr_no_val} on {self.vessel_id}"
    




# class MasterAppliedRank(models.Model):
#     """
#     Model for the master_applied_rank table.
#     Stores information about different ranks with their IDs and names.
#     """
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     rank_name = models.CharField(max_length=255, null=True, blank=True)
#     rank_id = models.CharField(max_length=50, null=True, blank=True) 

#     class Meta:
#         db_table = 'master_applied_rank' 
#         managed = False 
#     def __str__(self):
#         return f"{self.rank_name} ({self.rank_id})"







class MscRankAssigned(models.Model):
    """
    Links a notification (by SR No) to a specific rank for distribution.
    Tracks assignment date and active/deleted status.
    
    """
  
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    msc_sr_no = models.CharField(max_length=255, null=True, blank=True) 
    rank_id = models.UUIDField(null=True, blank=True)
    assigned_date = models.DateTimeField(auto_now_add=True) 
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'msc_rank_assigned' 
        managed = False

    def __str__(self):
        return f"Assignment: {self.msc_sr_no} -> {self.rank_id}"





class MscNotification(models.Model):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    msc_sr_no = models.CharField(max_length=255, null=True, blank=True)
    crew_id = models.CharField(max_length=255)  # NVARCHAR(255)
    delivered_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_count= models.IntegerField()

    class Meta:
        db_table = 'msc_notification'
        managed = False

    def __str__(self):
        return f"{self.msc_sr_no} - {self.crew_id}"