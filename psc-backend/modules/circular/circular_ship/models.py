from django.db import models
import uuid
from django.utils import timezone





class ShipUsersLogin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CrewID = models.CharField(max_length=50, unique=True)
    Password = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    Created_By = models.CharField(max_length=50, null=True, blank=True)
    Updated_By = models.CharField(max_length=50, null=True, blank=True)
    Created_At = models.DateTimeField(default=timezone.now, null=True, blank=True)
    Updated_At = models.DateTimeField(null=True, blank=True)
    Temp_Password = models.CharField(max_length=100, null=True, blank=True)
    class Meta:
        db_table = "Ship_UsersLogin"
        managed = False

    def __str__(self):
        return f"User {self.CrewID}"




class MscAcknowledgeHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,editable=False)
    msc_sr_no = models.CharField(max_length=255, null=True, blank=True)
    read_by = models.CharField(max_length=255, null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    reminder_count = models.IntegerField(default=0)
    class Meta:
        db_table = 'msc_acknowledge_history'
        managed = False

    def __str__(self):
        return f"{self.msc_sr_no} - {self.read_by}"
    



