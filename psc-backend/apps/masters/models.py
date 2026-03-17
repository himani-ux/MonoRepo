"""
Master data models - Unmanaged (read-only from existing tables).

Tables from:
- Docs/CAR_Database_Schema_v4.sql: MOU_Master, PSC_Action_Codes, PIC_Master, CLC_Category, CLC_Item
- Docs/PSC_Def_Code_Master.sql: PSC_Def_Category, PSC_Def_Subcategory, PSC_Def_Code
"""

from django.db import models


class MOUMaster(models.Model):
    """
    Memorandum of Understanding regions for Port State Control.
    Table: MOU_Master
    """
    mou_code = models.CharField(max_length=20, primary_key=True, db_column='MOU_Code')
    mou_name = models.CharField(max_length=100, db_column='MOU_Name')
    region = models.CharField(max_length=50, null=True, blank=True, db_column='Region')
    is_active = models.BooleanField(default=True, db_column='Is_Active')
    sort_order = models.IntegerField(default=0, db_column='Sort_Order')

    class Meta:
        managed = False
        db_table = 'MOU_Master'
        ordering = ['sort_order', 'mou_name']

    def __str__(self):
        return f"{self.mou_code} - {self.mou_name}"


class PSCActionCode(models.Model):
    """
    PSC Action Taken Codes - what action was taken regarding a deficiency.
    Table: PSC_Action_Codes
    """
    action_code = models.IntegerField(primary_key=True, db_column='Action_Code')
    definition = models.CharField(max_length=100, db_column='Definition')
    description = models.CharField(max_length=500, null=True, blank=True, db_column='Description')
    is_detention = models.BooleanField(default=False, db_column='Is_Detention')
    requires_follow_up = models.BooleanField(default=False, db_column='Requires_Follow_Up')
    is_active = models.BooleanField(default=True, db_column='Is_Active')

    class Meta:
        managed = False
        db_table = 'PSC_Action_Codes'
        ordering = ['action_code']

    def __str__(self):
        return f"{self.action_code} - {self.definition}"


class PICMaster(models.Model):
    """
    Person In Charge codes - who is responsible for action.
    Table: PIC_Master
    """
    pic_code = models.CharField(max_length=10, primary_key=True, db_column='PIC_Code')
    pic_name = models.CharField(max_length=50, db_column='PIC_Name')
    department = models.CharField(max_length=20, null=True, blank=True, db_column='Department')
    sort_order = models.IntegerField(default=0, db_column='Sort_Order')

    class Meta:
        managed = False
        db_table = 'PIC_Master'
        ordering = ['sort_order', 'pic_name']

    def __str__(self):
        return f"{self.pic_code} - {self.pic_name}"


class PSCDefCategory(models.Model):
    """
    PSC Deficiency Category - top level grouping (01-18, 99).
    Table: PSC_Def_Category
    """
    category_code = models.CharField(max_length=2, primary_key=True, db_column='Category_Code')
    category_name = models.CharField(max_length=100, db_column='Category_Name')
    sort_order = models.IntegerField(default=0, db_column='Sort_Order')
    is_active = models.BooleanField(default=True, db_column='Is_Active')

    class Meta:
        managed = False
        db_table = 'PSC_Def_Category'
        ordering = ['sort_order', 'category_code']

    def __str__(self):
        return f"{self.category_code} - {self.category_name}"


class PSCDefSubcategory(models.Model):
    """
    PSC Deficiency Subcategory - second level grouping (011, 012, 091, etc.).
    Table: PSC_Def_Subcategory
    """
    subcategory_code = models.CharField(max_length=3, primary_key=True, db_column='Subcategory_Code')
    category_code = models.CharField(max_length=2, db_column='Category_Code')
    subcategory_name = models.CharField(max_length=100, db_column='Subcategory_Name')
    sort_order = models.IntegerField(default=0, db_column='Sort_Order')
    is_active = models.BooleanField(default=True, db_column='Is_Active')

    class Meta:
        managed = False
        db_table = 'PSC_Def_Subcategory'
        ordering = ['sort_order', 'subcategory_code']

    def __str__(self):
        return f"{self.subcategory_code} - {self.subcategory_name}"


class PSCDefCode(models.Model):
    """
    PSC Deficiency Code - the actual deficiency codes (5-digit).
    Table: PSC_Def_Code
    """
    def_code = models.CharField(max_length=5, primary_key=True, db_column='Def_Code')
    category_code = models.CharField(max_length=2, db_column='Category_Code')
    subcategory_code = models.CharField(max_length=3, null=True, blank=True, db_column='Subcategory_Code')
    def_name = models.CharField(max_length=200, db_column='Def_Name')
    sort_order = models.IntegerField(default=0, db_column='Sort_Order')
    is_active = models.BooleanField(default=True, db_column='Is_Active')

    class Meta:
        managed = False
        db_table = 'PSC_Def_Code'
        ordering = ['def_code']

    def __str__(self):
        return f"{self.def_code} - {self.def_name}"


class CLCCategory(models.Model):
    """
    Comprehensive List of Causes - Category hierarchy.
    Table: CLC_Category

    Structure:
    - Immediate Causes - Actions (1-4)
    - Immediate Causes - Conditions (5-8)
    - Root Causes - Personal Factors (P1-P6)
    - Root Causes - Job Factors (J7-J15)
    """
    category_id = models.IntegerField(primary_key=True, db_column='Category_ID')
    category_code = models.CharField(max_length=50, db_column='Category_Code')
    category_name = models.CharField(max_length=100, db_column='Category_Name')
    category_type = models.CharField(max_length=50, null=True, blank=True, db_column='Category_Type')
    parent_id = models.IntegerField(null=True, blank=True, db_column='Parent_ID')
    sort_order = models.IntegerField(default=0, db_column='Sort_Order')

    class Meta:
        managed = False
        db_table = 'CLC_Category'
        ordering = ['sort_order', 'category_id']

    def __str__(self):
        return f"{self.category_code} - {self.category_name}"


class CLCItem(models.Model):
    """
    Comprehensive List of Causes - Individual cause items.
    Table: CLC_Item
    """
    clc_code = models.CharField(max_length=10, primary_key=True, db_column='CLC_Code')
    category_id = models.IntegerField(db_column='Category_ID')
    item_name = models.CharField(max_length=200, db_column='Item_Name')
    item_description = models.CharField(max_length=500, null=True, blank=True, db_column='Item_Description')
    sort_order = models.IntegerField(default=0, db_column='Sort_Order')
    is_active = models.BooleanField(default=True, db_column='Is_Active')

    class Meta:
        managed = False
        db_table = 'CLC_Item'
        ordering = ['clc_code']

    def __str__(self):
        return f"{self.clc_code} - {self.item_name}"
