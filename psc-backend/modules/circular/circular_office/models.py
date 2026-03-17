# models.py
from django.db import models
import uuid




class MscReminder(models.Model):
    msc_not_id = models.UUIDField()  # FK to msc_notification.id (no enforced FK in model)
    sent_to = models.CharField(max_length=255, null=True, blank=True)
    sent_by = models.CharField(max_length=255, null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'msc_reminder'
        managed = False

    def __str__(self):
        return f"Reminder to {self.sent_to} at {self.sent_at}"
    



class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.department_name

    class Meta:
        managed = False
        db_table = 'department'  # Optional: if you want to match existing table name
        ordering = ['department_name']




class FinalCrewList(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    CrewID = models.CharField(max_length=50)
    Crew_ref_id = models.CharField(max_length=36) 

    class Meta:
        db_table = 'final_crew_list'
        managed = False  
    





class MasterRole(models.Model):
    """
    Defines roles in the system.
    """
    id = models.UUIDField(primary_key=True,  editable=False)
    role_name = models.CharField(max_length=100, null=True, blank=True) # Name of the role
    is_active = models.BooleanField(default=True, null=True, blank=True)
    is_deleted = models.BooleanField(default=False, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'master_role'  # Specify the actual database table name
        managed = False  # Set to False if you are not managing the table with Django migrations

    def __str__(self):
        return f"MasterRole {self.id} - {self.role_name}"

# models.py


class MappingRoleUser(models.Model):
    """
    Maps users to roles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    userid = models.CharField(max_length=50, null=True, blank=True) # Stores the user identifier (e.g., employee ID or username)
    role_id = models.UUIDField(null=True, blank=True) # Foreign key to the MasterRole model (if you have one)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    is_deleted = models.BooleanField(default=False, null=True, blank=True)
    created_by = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=100, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'mapping_role_user'  # Specify the actual database table name
        managed = False  # Set to False if you are not managing the table with Django migrations

    def __str__(self):
        return f"MappingRoleUser {self.id} - User: {self.userid}, Role: {self.role_id}"


class User(models.Model):
    """
    Model representing a user in the system.
    Maps to the 'users' table in the database.
    """
    employee_id = models.CharField(max_length=20, primary_key=True) # Primary key, varchar(20)
    employee_name = models.CharField(max_length=100) # varchar(100), not null
    employee_role = models.CharField(max_length=45) # varchar(45), not null
    display_name = models.CharField(max_length=100, null=True, blank=True) # varchar(100), null
    email_id = models.CharField(max_length=100) # varchar(100), not null
    username = models.CharField(max_length=100) # varchar(100), not null
    password = models.CharField(max_length=255, null=True, blank=True) # varchar(max), null (Note: Storing plain text passwords is NOT secure; use Django's built-in authentication system or hash passwords)
    location = models.CharField(max_length=45) # varchar(45), not null
    manager_employee_id = models.CharField(max_length=20, null=True, blank=True) # varchar(20), null
    manager_username = models.CharField(max_length=100, null=True, blank=True) # varchar(100), null
    manager_name = models.CharField(max_length=100, null=True, blank=True) # varchar(100), null
    cost_center = models.CharField(max_length=45, null=True, blank=True) # varchar(45), null
    department = models.CharField(max_length=255, null=True, blank=True) # varchar(max), null
    state = models.IntegerField(null=True, blank=True) # int, null
    is_active = models.BooleanField(default=True, null=True, blank=True) # bit, null
    is_deleted = models.BooleanField(default=False, null=True, blank=True) # bit, null
    created_by = models.CharField(max_length=20, null=True, blank=True) # varchar(20), null
    created_date = models.DateTimeField(null=True, blank=True) # datetime, null
    updated_by = models.CharField(max_length=20, null=True, blank=True) # varchar(20), null
    updated_date = models.DateTimeField(null=True, blank=True) # datetime, null
    upload_photo_name = models.CharField(max_length=255, null=True, blank=True) # varchar(max), null
    upload_sign_name = models.CharField(max_length=255, null=True, blank=True) # varchar(max), null
    mobile = models.CharField(max_length=15, null=True, blank=True) # varchar(15), null

    class Meta:
        db_table = 'users'  # Specify the actual database table name
        managed = False  # Set to False if you are not managing the table with Django migrations

    def __str__(self):
        return f"{self.employee_name} ({self.employee_id})" # Example string representation
