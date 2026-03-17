### 4.5 CAR Transition Matrix (Source of Truth)

| From | Action | To | Actor(s) | Comment Required |
|---|---|---|---|---|
| ALLOTTED | START_WORK | IN_PROGRESS | owner, master | No |
| IN_PROGRESS | MARK_COMPLETED | PENDING_CE_REVIEW | owner, master | No |
| PENDING_CE_REVIEW | APPROVE_AND_FORWARD | PENDING_MASTER_REVIEW | reviewer, master | No |
| PENDING_CE_REVIEW | RETURN_FOR_REWORK | IN_PROGRESS | reviewer, master | Yes |
| PENDING_MASTER_REVIEW | SUBMIT_TO_PIC | SUBMITTED_TO_PIC | master | No |
| PENDING_MASTER_REVIEW | RETURN_FOR_REWORK | IN_PROGRESS | master | Yes |
| SUBMITTED_TO_PIC | START_PIC_REVIEW | PIC_REVIEW | pic | No |
| SUBMITTED_TO_PIC | REQUEST_REWORK | PENDING_MASTER_REVIEW | pic, dpa | Yes |
| PIC_REVIEW | SUBMIT_TO_DPA | SUBMITTED_TO_DPA | pic | No |
| PIC_REVIEW | REQUEST_REWORK | PENDING_MASTER_REVIEW | pic, dpa | Yes |
| SUBMITTED_TO_DPA | CLOSE_CAR | CLOSED | dpa | Yes |
| SUBMITTED_TO_DPA | REQUEST_REWORK | PENDING_MASTER_REVIEW | dpa | Yes |
| CLOSED | REOPEN_CAR | PENDING_MASTER_REVIEW | dpa | Yes |




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