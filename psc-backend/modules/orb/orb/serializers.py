# logbook/serializers.py
from rest_framework import serializers
from modules.orb.orb.models import  VesselTankDetails, ORBCodes, OperationEntry, CurrentVessel
from modules.circular.circular.models import VesselData
import uuid


# --- VesselDataSerializer ---
class VesselDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = VesselData
        fields = ["id", "vesselName", "vesselCode","imonumber"]


# --- VesselTankDetailsSerializer ---
class VesselTankDetailsSerializer(serializers.ModelSerializer):
    tank_type_name = serializers.CharField(source="tank_type.tank_type", read_only=True)

    class Meta:
        model = VesselTankDetails
        fields = ['id', 'identifier', 'capacity_m3', 'frame_range', 'tank_type_name']


# --- ORBCodesSerializer ---
class ORBCodesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ORBCodes
        fields = ['id', 'code', 'part', 'description']


# --- OperationEntrySerializer (CRITICAL FIX) ---
class OperationEntrySerializer(serializers.ModelSerializer):
    #  Fix: vessel is stored as UUIDField (not ForeignKey), so we use UUIDField
    vessel = serializers.UUIDField()  # ← This is key! Not PrimaryKeyRelatedField

    # Optional fields
    created_by = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    updated_by = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    

    class Meta:
        model = OperationEntry
        fields = '__all__'

        extra_kwargs = {
            'page_no': {'required': False, 'allow_null': True}  # Allow updates
        }

    def validate_vessel(self, value):
        """Ensure vessel is a valid UUID string"""
        try:
            # Convert to UUID and back to string to normalize
            return str(uuid.UUID(str(value)))
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid UUID format for vessel")

    def validate_item_no(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Item number cannot be negative")
        return value

    # def validate_code(self, value):
    #     valid_codes = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'}
    #     if value not in valid_codes:
    #         raise serializers.ValidationError(f"Invalid ORB code: {value}")
    #     return value


# --- CurrentVesselSerializer ---
class CurrentVesselSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentVessel
        fields = '__all__'