"""
Master data serializers.

Per BACKEND_STRUCTURE.md Section 10.10 - Master Data Endpoints
"""

from rest_framework import serializers
from .models import (
    MOUMaster,
    PSCActionCode,
    PICMaster,
    PSCDefCategory,
    PSCDefSubcategory,
    PSCDefCode,
    CLCCategory,
    CLCItem,
)


class MOUSerializer(serializers.ModelSerializer):
    """Serializer for MOU Master."""

    class Meta:
        model = MOUMaster
        fields = ['mou_code', 'mou_name', 'region', 'sort_order']


class PSCActionCodeSerializer(serializers.ModelSerializer):
    """Serializer for PSC Action Codes."""

    class Meta:
        model = PSCActionCode
        fields = [
            'action_code',
            'definition',
            'description',
            'is_detention',
            'requires_follow_up',
        ]


class PICSerializer(serializers.ModelSerializer):
    """Serializer for PIC Master."""

    class Meta:
        model = PICMaster
        fields = ['pic_code', 'pic_name', 'department', 'sort_order']


class PSCDefCategorySerializer(serializers.ModelSerializer):
    """Serializer for PSC Deficiency Categories."""

    class Meta:
        model = PSCDefCategory
        fields = ['category_code', 'category_name', 'sort_order']


class PSCDefSubcategorySerializer(serializers.ModelSerializer):
    """Serializer for PSC Deficiency Subcategories."""

    class Meta:
        model = PSCDefSubcategory
        fields = ['subcategory_code', 'category_code', 'subcategory_name', 'sort_order']


class PSCDefCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for PSC Deficiency Codes.
    Includes category and subcategory names for display.
    """
    category_name = serializers.SerializerMethodField()
    subcategory_name = serializers.SerializerMethodField()
    display_text = serializers.SerializerMethodField()

    class Meta:
        model = PSCDefCode
        fields = [
            'def_code',
            'def_name',
            'category_code',
            'category_name',
            'subcategory_code',
            'subcategory_name',
            'display_text',
            'sort_order',
        ]

    def get_category_name(self, obj):
        """Get category name from cache or database."""
        categories = self.context.get('categories', {})
        return categories.get(obj.category_code, '')

    def get_subcategory_name(self, obj):
        """Get subcategory name from cache or database."""
        if not obj.subcategory_code:
            return None
        subcategories = self.context.get('subcategories', {})
        return subcategories.get(obj.subcategory_code, '')

    def get_display_text(self, obj):
        """Format: '07115 - Fire-dampers'"""
        return f"{obj.def_code} - {obj.def_name}"


class CLCCategorySerializer(serializers.ModelSerializer):
    """Serializer for CLC Categories."""

    class Meta:
        model = CLCCategory
        fields = [
            'category_id',
            'category_code',
            'category_name',
            'category_type',
            'parent_id',
            'sort_order',
        ]


class CLCItemSerializer(serializers.ModelSerializer):
    """
    Serializer for CLC Items.
    Includes category info for display.
    """
    category_code = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    category_type = serializers.SerializerMethodField()
    display_text = serializers.SerializerMethodField()

    class Meta:
        model = CLCItem
        fields = [
            'clc_code',
            'item_name',
            'item_description',
            'category_id',
            'category_code',
            'category_name',
            'category_type',
            'display_text',
            'sort_order',
        ]

    def get_category_code(self, obj):
        """Get category code from cache."""
        categories = self.context.get('categories', {})
        cat = categories.get(obj.category_id, {})
        return cat.get('code', '')

    def get_category_name(self, obj):
        """Get category name from cache."""
        categories = self.context.get('categories', {})
        cat = categories.get(obj.category_id, {})
        return cat.get('name', '')

    def get_category_type(self, obj):
        """Get category type from cache."""
        categories = self.context.get('categories', {})
        cat = categories.get(obj.category_id, {})
        return cat.get('type', '')

    def get_display_text(self, obj):
        """Format: '1-1 - Violation by individual'"""
        return f"{obj.clc_code} - {obj.item_name}"


class CLCHierarchySerializer(serializers.Serializer):
    """
    Serializer for CLC data in hierarchical format.
    Used for frontend tree/accordion display.
    """
    immediate_causes = serializers.DictField()
    root_causes = serializers.DictField()
