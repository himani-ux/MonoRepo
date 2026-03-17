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