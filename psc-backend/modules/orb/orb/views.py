# logbook/views.py
import uuid
import json
import logging
from datetime import datetime
import os
import base64
import pickle

from django.conf import settings

from rest_framework.authtoken.models import Token
from django.db import connection,transaction
from django.db.models import Max, Func
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action, permission_classes,authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.core.paginator import Paginator 

from . import utils
from modules.orb.orb.models import (

    VesselTankDetails,
    ORBCodes,
    OperationEntry,
    CurrentVessel,
    GeneratedPDF
)
from modules.circular.circular.models import VesselData
from .serializers import (
    VesselDataSerializer,
    VesselTankDetailsSerializer,
    ORBCodesSerializer,
    OperationEntrySerializer,
    CurrentVesselSerializer,
)

logger = logging.getLogger(__name__)




@permission_classes([AllowAny])
class VesselDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VesselData.objects.all().only("id", "vesselName", "vesselCode", "imonumber").order_by('vesselName')
    serializer_class = VesselDataSerializer
    permission_classes = [AllowAny]

@permission_classes([AllowAny])
class VesselTankDetailsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = VesselTankDetailsSerializer

    def get_queryset(self):
        vessel_id = self.request.query_params.get('vessel_id')
        if vessel_id:
            return VesselTankDetails.objects.filter(vessel_id=vessel_id)
        return VesselTankDetails.objects.none()

    permission_classes = [AllowAny]

@permission_classes([AllowAny])
class ORBCodesViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ORBCodes.objects.all()
    serializer_class = ORBCodesSerializer
    permission_classes = [AllowAny]




@api_view(['GET'])
@permission_classes([AllowAny])
def get_vessels(request):
    vessels = VesselData.objects.all()
    serializer = VesselDataSerializer(vessels, many=True)
    return Response(serializer.data)


# Authentication logic removed - using JWT token-based authentication from core.auth

@permission_classes([AllowAny])
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]







@permission_classes([AllowAny])
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]



@permission_classes([AllowAny])
class OperationEntryViewSet(viewsets.ModelViewSet):
    queryset = OperationEntry.objects.all()

    serializer_class = OperationEntrySerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # 1. Get vessel_id: from request or fallback to CurrentVessel
        vessel_id = data.get("vessel")
        if not vessel_id:
            active_vessel = CurrentVessel.objects.filter(is_active=True).first()
            if not active_vessel:
                return Response({"error": "No active vessel found"}, status=status.HTTP_400_BAD_REQUEST)
            vessel_id = str(active_vessel.vessel_id)

        # 2. Clean and validate vessel_id as UUID
        try:
            clean_uuid = uuid.UUID(str(vessel_id).strip())
            vessel_id = str(clean_uuid)
        except (ValueError, AttributeError):
            return Response({
                "error": f"Invalid vessel ID format: {vessel_id}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Extract other fields
        officer = data.get("created_by", "Unknown")
        date_str = data.get("date") # Get the date string from the request
        code = data.get("code")
        item_no = data.get("item_no")
        record_of_operation = str(data.get("record_of_operation", "")).strip().upper()
        status_val = data.get("status", "Draft")
        is_deleted = data.get("is_deleted", False)

        # Convert date string to datetime object for validation and insertion
        date_obj = None
        if date_str:
            try:
                # Attempt to parse ISO format with microseconds and Zulu time
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Attempt without microseconds
                    date_obj = datetime.strptime(date_str.replace('Z', '+00:00'), "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    # Attempt without timezone, assuming it's in the format YYYY-MM-DDTHH:MM
                    # Append ":00" for seconds if missing
                    if len(date_str) == 16: # Length of "YYYY-MM-DDTHH:MM"
                        date_str_with_seconds = date_str + ":00"
                    else:
                        date_str_with_seconds = date_str
                    date_obj = datetime.fromisoformat(date_str_with_seconds)


        # 4. Validate required fields
        if not date_obj or not code or not record_of_operation:
            return Response({
                "error": "Missing required fields: date, code, record_of_operation"
            }, status=status.HTTP_400_BAD_REQUEST)

        # --- NEW: Validate Date Against Latest Entry ---
        try:
            # Query to find the most recent entry date/time for the given vessel
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT MAX(date) -- Get the latest date
                    FROM dbo.Operations
                    WHERE vessel = %s AND is_deleted = 0 -- Exclude deleted entries
                """, [vessel_id])
                latest_row = cursor.fetchone()

                if latest_row and latest_row[0]:
                    latest_entry_date_db = latest_row[0] # This will be a datetime object from the DB
                    print(f"DEBUG: Latest entry date from DB for vessel {vessel_id}: {latest_entry_date_db}")

                    # Compare dates
                    # Compare the datetimes
                    if date_obj < latest_entry_date_db:
                        return Response({
                            "error": f"Entry date/time ({date_obj}) cannot be earlier than the latest existing entry date/time ({latest_entry_date_db})."
                        }, status=status.HTTP_400_BAD_REQUEST) # Bad Request
                    else:
                        print(f"DEBUG: Incoming date {date_obj} is valid (>= latest {latest_entry_date_db}).")

        except Exception as e:
            # Log the error for debugging, but decide how to handle failure
            print(f"Error validating date against latest entry: {e}")
            # Decide whether to fail the request or proceed cautiously
            # For now, let's fail the request if validation itself fails critically
            return Response({
                "error": "Internal error during date validation."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # --- END NEW: Validate Date Against Latest Entry ---


        # 5. Get orb_code_id from ORBCodes table
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM dbo.ORBCodes WHERE code = %s", [code])
            row = cursor.fetchone()
            if not row:
                return Response({"error": f"Invalid ORB Code: {code}"}, status=status.HTTP_400_BAD_REQUEST)
            orb_code_id = str(row[0])

        # 5. Handle item_no
        if item_no is not None:
            try:
                item_no = float(item_no)
            except (ValueError, TypeError):
                return Response({"error": "Invalid item_no. Must be a number."}, status=400)

        # 6. Get next entry_no
        with connection.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(entry_no), 0) FROM dbo.Operations")
            row = cursor.fetchone()
            next_entry_no = (row[0] or 0) + 1

        # 7. Debug: Log the values
        print("🔧 INSERTING INTO OPERATIONS:")
        print("  vessel:", vessel_id)
        print("  date:", date_obj) # Use the datetime object
        print("  code:", code)
        print("  orb_code_id:", orb_code_id)
        print("  item_no:", item_no)
        print("  record_of_operation:", record_of_operation[:100])
        print("  created_by:", officer)
        print("  entry_no:", next_entry_no)

        #  8. Raw SQL insert with entry_no
        # Pass the date_obj (Python datetime) to the query
        with connection.cursor() as cursor:
            try:
                operation_id = uuid.uuid4()
                cursor.execute("""
                    INSERT INTO dbo.Operations (
                        id, vessel, date, orb_code_id, item_no, record_of_operation,
                        status, created_by, is_deleted, created_at, entry_no
                    )
                    OUTPUT INSERTED.id
                    VALUES (
                        CAST(%s AS UNIQUEIDENTIFIER),
                        CAST(%s AS UNIQUEIDENTIFIER),
                        %s, -- Pass the Python datetime object directly
                        CAST(%s AS UNIQUEIDENTIFIER), %s, %s, %s, %s, %s, SYSUTCDATETIME(), %s
                    )
                """, [
                    str(operation_id),
                    vessel_id,
                    date_obj, # Pass the Python datetime object
                    orb_code_id,
                    item_no,
                    record_of_operation,
                    status_val,
                    officer,
                    int(is_deleted),
                    next_entry_no
                ])

                result = cursor.fetchone()
                operation_id = str(result[0]) if result else str(operation_id)

                return Response({
                    "id": operation_id,
                    "vessel": vessel_id,
                    "date": date_obj.isoformat(), # Return the date in ISO format
                    "code": code,
                    "item_no": item_no,
                    "record_of_operation": record_of_operation,
                    "status": status_val,
                    "created_by": officer,
                    "is_deleted": bool(is_deleted),
                    "entry_no": next_entry_no
                }, status=status.HTTP_201_CREATED)

            except Exception as e:
                print("❌ SQL INSERT FAILED:", str(e))
                return Response({
                    "error": "Failed to save entry",
                    "detail": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.info(f"PATCH data received: {request.data}")
        logger.info(f"Current page_no: {instance.page_no}")

        #  Manually set page_no before saving
        if 'page_no' in request.data:
            instance.page_no = request.data['page_no']
            logger.info(f"Manually setting page_no to: {instance.page_no}")

        response = super().update(request, *args, **kwargs)

        # Re-fetch to check
        instance.refresh_from_db()
        logger.info(f"Updated page_no: {instance.page_no}")

        return response


    def get_object(self):
        pk_string = self.kwargs['pk']
        try:
            pk_uuid = uuid.UUID(pk_string)
        except ValueError:
            from django.http import Http404
            raise Http404("Invalid UUID format")

        print(f"DEBUG: Looking up ID as UUID object: {pk_uuid}, Type: {type(pk_uuid)}") # Add this line

        return get_object_or_404(self.queryset, pk=pk_uuid)

    def partial_update(self, request, *args, **kwargs):
        """
        Handles PATCH requests, specifically for updating is_deleted using raw SQL.
        """
        # Get the pk string from the URL kwargs
        pk_string = self.kwargs['pk']
        try:
            # Convert the string to a UUID object
            entry_id = uuid.UUID(pk_string)
        except ValueError:
            # If the string is not a valid UUID format, return 404
            return Response(
                {"error": f"Invalid entry ID format: {pk_string}. Must be a valid UUID."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        is_deleted_flag = data.get('is_deleted')

        if is_deleted_flag is not None:
            try:
                is_deleted_bool = bool(is_deleted_flag)
                user = request.user
                username = getattr(user, 'username', 'Unknown User')

                with connection.cursor() as cursor:
                    # Use raw SQL UPDATE with CAST to ensure the string ID is treated as UNIQUEIDENTIFIER
                    # Also update updated_by and updated_at
                    cursor.execute("""
                        UPDATE dbo.Operations
                        SET is_deleted = %s, updated_by = %s, updated_at = SYSUTCDATETIME()
                        WHERE id = CAST(%s AS UNIQUEIDENTIFIER)
                    """, [is_deleted_bool, username, str(entry_id)]) # Pass entry_id as string, CAST in SQL

                    rows_affected = cursor.rowcount

                    if rows_affected == 0:
                        # No rows matched the ID, meaning the entry didn't exist
                        return Response(
                            {"error": f"Entry with ID {pk_string} not found."},
                            status=status.HTTP_404_NOT_FOUND
                        )
                    else:
                        # Successfully updated one row
                        print(f"Entry {entry_id} soft-deleted by {username}.") # Log the action
                        return Response(
                            {"id": str(entry_id), "is_deleted": is_deleted_bool, "message": "Entry soft-deleted successfully."},
                            status=status.HTTP_200_OK
                        )

            except Exception as e:
                print(f"❌ SQL UPDATE FAILED in partial_update: {str(e)}")
                return Response(
                    {"error": "Failed to update entry due to a database error."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # If 'is_deleted' is not provided in the request data
        return Response(
             {"error": "Only 'is_deleted' field updates are handled by this PATCH handler."},
             status=status.HTTP_400_BAD_REQUEST
         )

    @action(detail=True, methods=['patch', 'put'], url_path='update-group')
    def update_group(self, request, pk=None):
        """
        Updates a single ORB entry (old format) by deleting the old entry
        and creating a new one based on the provided single entry object.
        Expects the pk to be the ID of the single entry to update.
        Expects request.data to be a single entry object (like the 'payload' in the old format).
        """
        try:
            entry_id = uuid.UUID(pk)
        except ValueError:
            return Response(
                {"error": f"Invalid entry ID format: {pk}. Must be a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure request.data is a dictionary
        if not isinstance(request.data, dict):
            return Response(
                {"error": "Request body must be a single entry object for the old format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        entry_data = request.data

        with connection.cursor() as cursor:
            # 1. Find the existing entry first to confirm it exists
            cursor.execute("""
                SELECT id FROM dbo.Operations WHERE id = CAST(%s AS UNIQUEIDENTIFIER)
            """, [str(entry_id)])
            existing_row = cursor.fetchone()
            if not existing_row:
                 return Response(
                     {"error": f"Entry with ID {pk} not found."},
                     status=status.HTTP_404_NOT_FOUND
                 )

            user = request.user
            username = getattr(user, 'username', 'Unknown User')

            # 2. Soft delete the existing single entry
            cursor.execute("""
                UPDATE dbo.Operations
                SET is_deleted = 1, updated_by = %s, updated_at = SYSUTCDATETIME()
                WHERE id = CAST(%s AS UNIQUEIDENTIFIER)
            """, [username, str(entry_id)])
            rows_deleted = cursor.rowcount
            print(f"DEBUG: Soft-deleted {rows_deleted} entry for ID {entry_id}.")

        # 3. Create the new entry using the existing 'create' logic or replicate it.
        # Since the request.data is a single entry object (like the old 'payload'),
        # we can replicate the core INSERT logic from the 'create' method for consistency.

        # --- REPLICATE CORE CREATE LOGIC START ---
        # Extract fields from the incoming entry_data (the new payload)
        # Note: The keys in entry_data should match the structure of the 'payload' object from the frontend.
        # e.g., { vessel, date, code, orb_code_id, item_no, record_of_operation, status, created_by, ... }
        # Ensure the frontend sends the payload structure correctly.
        vessel_id_str = entry_data.get("vessel")
        date_str = entry_data.get("date")
        code_str = entry_data.get("code")
        orb_code_id_str = entry_data.get("orb_code_id")
        item_no_val = entry_data.get("item_no")
        record_of_operation_str = entry_data.get("record_of_operation")
        status_val = entry_data.get("status", "Draft") # Default if not provided
        created_by_str = entry_data.get("created_by", "Unknown")
        submitted_by_str = entry_data.get("submitted_by", "Unknown")
        submitted_at_str = entry_data.get("submitted_at")
        is_deleted_flag = entry_data.get("is_deleted", False)
        approved_by_str = entry_data.get("approved_by")
        approved_at_str = entry_data.get("approved_at")
        rejected_by_str = entry_data.get("rejected_by")
        rejected_at_str = entry_data.get("rejected_at")

        # Validate essential fields again (as they might be modified by the frontend)
        if not date_str or not code_str or not record_of_operation_str:
            return Response({
                "error": "Missing required fields in the updated entry: date, code, record_of_operation"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate vessel_id as UUID
        try:
            clean_vessel_uuid = uuid.UUID(str(vessel_id_str).strip())
            vessel_id_for_db = str(clean_vessel_uuid)
        except (ValueError, AttributeError):
            return Response({
                "error": f"Invalid vessel ID format: {vessel_id_str}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate orb_code_id as UUID
        try:
            clean_orb_code_uuid = uuid.UUID(str(orb_code_id_str).strip())
            orb_code_id_for_db = str(clean_orb_code_uuid)
        except (ValueError, AttributeError):
            return Response({
                "error": f"Invalid orb_code_id format: {orb_code_id_str}"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Handle item_no conversion if it's not None/empty
        item_no_for_db = item_no_val
        if item_no_val is not None and item_no_val != "":
            try:
                item_no_for_db = float(item_no_val)
            except (ValueError, TypeError):
                return Response({"error": "Invalid item_no. Must be a number."}, status=400)

        # Get next entry_no
        with connection.cursor() as cursor:
            cursor.execute("SELECT COALESCE(MAX(entry_no), 0) FROM dbo.Operations")
            row = cursor.fetchone()
            next_entry_no = (row[0] or 0) + 1

        # Perform the INSERT for the new entry
        with connection.cursor() as cursor:
            try:
                new_operation_id = uuid.uuid4()
                cursor.execute("""
                    INSERT INTO dbo.Operations (
                        id, vessel, date, orb_code_id, item_no, record_of_operation,
                        status, created_by, submitted_by, submitted_at,
                        is_deleted, approved_by, approved_at, rejected_by, rejected_at,
                        created_at, entry_no -- Assuming parent_entry_id is not needed in old format INSERT
                    )
                    OUTPUT INSERTED.id
                    VALUES (
                        CAST(%s AS UNIQUEIDENTIFIER), CAST(%s AS UNIQUEIDENTIFIER), %s, CAST(%s AS UNIQUEIDENTIFIER),
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, SYSUTCDATETIME(), %s
                    )
                """, [
                    str(new_operation_id), vessel_id_for_db, date_str, orb_code_id_for_db,
                    item_no_for_db, record_of_operation_str, status_val,
                    created_by_str, submitted_by_str, submitted_at_str,
                    int(is_deleted_flag), approved_by_str, approved_at_str,
                    rejected_by_str, rejected_at_str, next_entry_no
                ])
                result = cursor.fetchone()
                new_operation_id = str(result[0]) if result else str(new_operation_id)

                print(f"DEBUG: Successfully created new entry with ID {new_operation_id}.")

                # Return success response
                return Response(
                    {
                        "message": f"Entry with ID {pk} updated successfully (deleted old, created new).",
                        "new_entry_id": new_operation_id
                    },
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                print(f"❌ SQL INSERT FAILED in update_group: {str(e)}")
                return Response({
                    "error": "Failed to create the updated entry due to a database error.",
                    "detail": str(e) # Include detail for debugging, remove in production
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # --- REPLICATE CORE CREATE LOGIC END ---


    @action(detail=True, methods=['delete'], url_path='delete-group') # Or just @action(detail=True, methods=['delete']) if you prefer /id/
    def delete_group(self, request, pk=None):
        """
        Soft deletes an entire ORB entry group (root + all its children).
        Expects the pk to be the ID of the root entry of the group.
        """
        try:
            root_id = uuid.UUID(pk)
        except ValueError:
            return Response(
                {"error": f"Invalid root entry ID format: {pk}. Must be a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:
            try:
                # Find the root entry first to confirm it exists
                cursor.execute("""
                    SELECT id FROM dbo.Operations WHERE id = CAST(%s AS UNIQUEIDENTIFIER) AND parent_entry_id IS NULL
                """, [str(root_id)])
                root_row = cursor.fetchone()
                if not root_row:
                     return Response(
                         {"error": f"Root entry with ID {pk} not found or is not a root entry."},
                         status=status.HTTP_404_NOT_FOUND
                     )

                # Soft delete the root entry and all its children
                # This updates both entries where id = root_id AND entries where parent_entry_id = root_id
                user = request.user
                username = getattr(user, 'username', 'Unknown User')

                cursor.execute("""
                    UPDATE dbo.Operations
                    SET is_deleted = 1, updated_by = %s, updated_at = SYSUTCDATETIME()
                    WHERE id = CAST(%s AS UNIQUEIDENTIFIER) OR parent_entry_id = CAST(%s AS UNIQUEIDENTIFIER)
                """, [username, str(root_id), str(root_id)])

                rows_affected = cursor.rowcount

                if rows_affected == 0:
                    # Should not happen if root_row check passed, but good safety net
                    return Response(
                        {"error": f"No entries found for group ID {pk}."}, # This shouldn't occur now
                        status=status.HTTP_404_NOT_FOUND
                    )

                print(f"Group with root ID {root_id} soft-deleted by {username}. {rows_affected} entries affected.")
                return Response(
                    {"message": f"Group with root ID {pk} soft-deleted successfully.", "entries_affected": rows_affected},
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                print(f"❌ SQL DELETE GROUP FAILED: {str(e)}")
                return Response(
                    {"error": "Failed to delete entry group due to a database error."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )



    def operations_list(request):
        vessel_id = request.GET.get('vessel_id')
        status = request.GET.get('status')
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')

        if not vessel_id:
            return JsonResponse({"error": "vessel_id is required"}, status=400)

        # Base filter
        queryset = OperationEntry.objects.filter(vessel_id=vessel_id, is_deleted=False)

        if status:
            queryset = queryset.filter(status=status)

        # Filter by date only (ignore time)
        if from_date:
            try:
                # Convert string to date object
                from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__date__gte=from_date_obj)
            except ValueError:
                return JsonResponse({"error": "Invalid from_date format. Use YYYY-MM-DD"}, status=400)

        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__date__lte=to_date_obj)
            except ValueError:
                return JsonResponse({"error": "Invalid to_date format. Use YYYY-MM-DD"}, status=400)

        # Serialize
        data = list(queryset.values())
        return JsonResponse(data, safe=False)
    
    
            
            #  OVERRIDE list() TO JOIN WITH ORBCodes AND RETURN 'code' LETTER
    def list(self, request, *args, **kwargs):
                vessel_id = request.query_params.get('vessel_id')
                is_deleted = request.query_params.get('is_deleted', '0')
                status_filter = request.query_params.get('status')

                # Convert 'false' → 0, 'true' → 1
                is_deleted = 1 if is_deleted.lower() == 'true' else 0

                if not vessel_id:
                    return Response({"error": "vessel_id is required"}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    with connection.cursor() as cursor:
                        sql = """
                            SELECT 
                                o.id,
                                o.date,
                                c.code,
                                o.item_no,
                                o.record_of_operation,
                                o.status,
                                o.created_by,
                                o.is_deleted,
                                o.master_print,       
                                o.entry_no
                                       
                            FROM dbo.Operations o
                            INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id
                            WHERE o.vessel = %s AND o.is_deleted = %s
                        """
                        params = [vessel_id, is_deleted]

                        if status_filter:
                            sql += " AND o.status = %s"
                            params.append(status_filter)

                        sql += " ORDER BY o.date DESC"
                        cursor.execute(sql, params)
                        rows = dictfetchall(cursor)
                    return Response(rows)
                except Exception as e:
                    print("❌ Error in list:", str(e))
                    return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
     # --- NEW DELETION FUNCTION ---
    def soft_delete_entry(self, request, pk=None): # pk is the entry's ID from the URL
        """
        Handles soft deletion of an ORB entry by setting is_deleted = 1 using raw SQL.
        This function is designed for the old format where each logical ORB entry is one row.
        """
        user = request.user # Get the user making the request (if using authentication)
        username = getattr(user, 'username', 'Unknown User') # Get username or default

        try:
            # Validate the provided ID (pk) is a valid UUID string
            entry_id = uuid.UUID(pk)
        except ValueError:
            return Response(
                {"error": f"Invalid entry ID format: {pk}. Must be a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Use raw SQL to update the is_deleted flag
        with connection.cursor() as cursor:
            try:
                # The SQL UPDATE statement
                # CAST(%s AS UNIQUEIDENTIFIER) ensures the string ID is treated as a UUID in SQL Server
                # %s is a placeholder for the entry_id parameter, preventing SQL injection
                cursor.execute("""
                    UPDATE dbo.Operations
                    SET is_deleted = 1, updated_by = %s, updated_at = SYSUTCDATETIME()
                    WHERE id = CAST(%s AS UNIQUEIDENTIFIER)
                """, [username, str(entry_id)]) # Pass parameters safely

                # Check how many rows were affected by the UPDATE
                rows_affected = cursor.rowcount

                if rows_affected == 0:
                    # No rows matched the ID, meaning the entry didn't exist or was already deleted
                    # It's often better to return 404 if the resource isn't found
                    return Response(
                        {"error": f"Entry with ID {pk} not found or already deleted."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    # Successfully updated one row
                    print(f"Entry {entry_id} soft-deleted by {username}.") # Log the action
                    return Response(
                        {"message": f"Entry {pk} soft-deleted successfully.", "id": pk},
                        status=status.HTTP_200_OK
                    )

            except Exception as e:
                # Handle any database errors during the update
                print(f"❌ SQL UPDATE FAILED in soft_delete_entry: {str(e)}")
                return Response(
                    {"error": "Failed to delete entry due to a database error."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
    # --- END NEW DELETION FUNCTION ---


logger = logging.getLogger(__name__)



@permission_classes([AllowAny])
def retrieve_operation(request, pk):
    """
    Custom view to safely retrieve an operation by ID using raw SQL
    Bypasses Django ORM bug with UUID in mssql-django
    """
    # Clean and validate PK
    if not pk:
        return JsonResponse({"error": "ID required"}, status=400)

    clean_pk = str(pk).strip().split('/')[0].strip('"\'').upper()

    try:
        uuid.UUID(clean_pk)
    except ValueError:
        return JsonResponse({"error": "Invalid ID format"}, status=400)

    #Use raw SQL with CAST to UNIQUEIDENTIFIER
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    o.id,
                    o.date,
                    c.code,
                    o.item_no,
                    o.record_of_operation,
                    o.status,
                    o.created_by,
                    o.is_deleted,
                    o.entry_no,
                    o.line_no,
                    o.master_print,       
                    o.page_no
                FROM dbo.Operations o
                INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id
                WHERE o.id = CAST(%s AS UNIQUEIDENTIFIER)
            """, [clean_pk])

            row = cursor.fetchone()
            if not row:
                return JsonResponse({"error": "Entry not found"}, status=404)

            columns = [col[0] for col in cursor.description]
            result = dict(zip(columns, row))

            # Format response
            return JsonResponse(result)

    except Exception as e:
        logger.error(f"Database error retrieving entry {clean_pk}: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
        




@permission_classes([AllowAny])
def get_last_page_number(request):
    vessel_id = request.GET.get("vessel_id")
        
    if not vessel_id:
        return JsonResponse({"error": "vessel_id is required"}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT max(page_no) as pg
            FROM [dbo].[Operations]
            WHERE vessel = %s
        """, [vessel_id])
        row = cursor.fetchone()

    return JsonResponse({"last_page": row[0]})




@permission_classes([AllowAny])
@api_view(['GET'])
def get_operations(request):
    vessel_id = request.GET.get('vessel_id')
    is_deleted = request.GET.get('is_deleted', '0')

    print(" get_operations called with:")
    print("  vessel_id:", vessel_id)
    print("  is_deleted:", is_deleted)

    try:
            with connection.cursor() as cursor:
                #  Run the query manually
                cursor.execute("""
                    SELECT 
                        o.id,
                        o.date,
                        c.code ,  
                        o.item_no,
                        o.record_of_operation,
                        o.status,
                        o.created_by,
                        o.is_deleted,
                        o.master_print,       
                        o.entry_no
                    FROM dbo.Operations o
                    INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id
                    WHERE o.vessel = %s AND o.is_deleted = %s
                    ORDER BY o.date DESC
                """, [vessel_id, int(is_deleted)])

                # Fetch and inspect raw rows
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                print("📋 Columns returned by query:", columns)
                print("📊 Raw rows from DB:", rows)

                #Convert to dict
                result = [dict(zip(columns, row)) for row in rows]
                print("✅ Final JSON response:", result)

            return Response(result)
    except Exception as e:
            print("❌ Error in get_operations:", str(e))
            return Response({"error": "Internal server error"}, status=500)

                



@permission_classes([AllowAny])
class CurrentVesselViewSet(viewsets.ModelViewSet):
        queryset = CurrentVessel.objects.all()
        serializer_class = CurrentVesselSerializer
        permission_classes = [AllowAny]

        def create(self, request, *args, **kwargs):
            vessel_id = request.data.get("vessel_id")
            if not vessel_id:
                return Response({"error": "vessel_id is required"}, status=400)

            try:
                uuid.UUID(str(vessel_id))
            except ValueError:
                return Response({"error": "Invalid vessel_id format"}, status=400)

            # Delete all first (keep only one)
            CurrentVessel.objects.all().delete()

            #  Create new
            current_vessel = CurrentVessel.objects.create(vessel_id=vessel_id)
            serializer = self.get_serializer(current_vessel)
            return Response(serializer.data, status=201)
    




@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def current_vessel_handler(request):
    """
    GET: Return vessel_id if any record exists
    POST: Delete all, create new record
    """
    if request.method == 'GET':
        current = CurrentVessel.objects.first()
        if current:
            return Response({"vessel_id": str(current.vessel_id)})
        else:
            return Response({"vessel_id": None}, status=404)

    elif request.method == 'POST':
        vessel_id = request.data.get("vessel_id")
        if not vessel_id:
            return Response({"error": "vessel_id is required"}, status=400)

        try:
            uuid.UUID(str(vessel_id))
        except ValueError:
            return Response({"error": "Invalid vessel_id format"}, status=400)

        # Delete all first
        CurrentVessel.objects.all().delete()

        # Create new
        current_vessel = CurrentVessel.objects.create(vessel_id=vessel_id)
        return Response({
            "vessel_id": str(current_vessel.vessel_id)
        }, status=201)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_tanks_for_orb_code(request):
    try:
        vessel_id = request.GET.get("vessel_id")
        orb_code = request.GET.get("orb_code")

        if not vessel_id or not orb_code:
            return Response({"error": "vessel_id and orb_code are required"}, status=400)

        # Validate UUID format
        try:
            uuid.UUID(str(vessel_id))
        except ValueError:
            return Response({"error": "Invalid vessel_id format"}, status=400)

        with connection.cursor() as cursor:
            # Get allowed tank types for ORB code
            cursor.execute("""
                SELECT m.tank_type_id
                FROM dbo.mapping_ORBCode_TankType m
                INNER JOIN dbo.ORBCodes o ON m.orb_code_id = o.id
                WHERE o.code = %s AND m.is_active = 1
            """, [orb_code])
            allowed_types = [row[0] for row in cursor.fetchall()]

            if not allowed_types:
                return Response([])

            # Fetch tanks
            placeholders = ','.join(['%s'] * len(allowed_types))
            query = f"""
                SELECT t.id, t.tank_name, t.capacity, t.location, t.tank_type, t.frame_from, t.frame_to
                FROM dbo.vessel_tank_details t
                WHERE t.vessel_id = %s
                  AND t.tank_type IN ({placeholders})
                  AND t.is_active = 1
                  AND t.is_deleted = 0
            """
            cursor.execute(query, [vessel_id, *allowed_types])
            rows = cursor.fetchall()

        results = [
            {
                "id": str(row[0]),
                "tank_name": row[1],
                "capacity": float(row[2]),
                "location": row[3],
                "tank_type": str(row[4]),
                "frame_from": row[5], 
                "frame_to": row[6] 
            }
            for row in rows
        ]
        return Response(results)

    except Exception as e:
        print("Error in get_tanks_for_orb_code:", str(e))
        return Response({"error": "Internal server error"}, status=500)




@api_view(['POST'])
def create_current_vessel(request):
    vessel_id = request.data.get("vessel_id")
    if not vessel_id:
        return Response({"error": "vessel_id is required"}, status=400)

    try:
        uuid.UUID(str(vessel_id))
    except ValueError:
        return Response({"error": "Invalid vessel_id format"}, status=400)

    # Delete all first
    CurrentVessel.objects.all().delete()

    # Create new
    current_vessel = CurrentVessel.objects.create(vessel_id=vessel_id)
    return Response({
        "vessel_id": str(current_vessel.vessel_id)
    }, status=201)








@api_view(["PATCH"])
@permission_classes([AllowAny])
def approve_operation(request, id):
    """
    Approves an operation entry using the approved_by string sent from the frontend.
    """
    try:
        # Get the approved_by string from the request body
        data = json.loads(request.body.decode('utf-8'))
        approved_by = data.get('approved_by')

        if not approved_by:
            return JsonResponse({"error": "Approved by information required"}, status=400)

        with connection.cursor() as cursor:
            # 1. Get the entry being approved
            cursor.execute("""
                SELECT id, vessel FROM dbo.Operations
                WHERE id = %s AND is_deleted = 0
            """, [id])
            row = cursor.fetchone()
            if not row:
                return JsonResponse({"error": "Entry not found"}, status=404)

            entry_id, vessel_id = row

            # 2. Get all already-approved entries for this vessel
            cursor.execute("""
                SELECT id FROM dbo.Operations
                WHERE vessel = %s AND is_deleted = 0 AND status = 'Approved'
                ORDER BY date ASC, created_at ASC
            """, [vessel_id])

            approved_ids = [r[0] for r in cursor.fetchall()]

            # 3. Add current entry if not present
            entry_uuid_upper = str(entry_id).upper()
            if entry_uuid_upper not in [str(uid).upper() for uid in approved_ids]:
                approved_ids.append(entry_id)

            # Re-fetch full data for all approved entries
            if approved_ids:
                format_strings = ','.join(['%s'] * len(approved_ids))
                cursor.execute(f"""
                    SELECT id, record_of_operation FROM dbo.Operations
                    WHERE id IN ({format_strings}) AND status = 'Approved' AND is_deleted = 0
                    ORDER BY date ASC, created_at ASC
                """, approved_ids)

                all_approved_entries = cursor.fetchall()

                #  4. Calculate line numbers
                current_line = 1
                entry_updates = []

                for eid, record in all_approved_entries:
                    lines = [line.strip() for line in record.split('\n') if line.strip()]
                    num_lines = len(lines)
                    if num_lines > 0:
                        page_no = (current_line - 1) // 20 + 1
                        entry_updates.append((current_line, page_no, str(eid)))  # Ensure ID is string
                        current_line += num_lines

                #  5. Update ALL approved entries with correct line_no and page_no
                for line_no, page_no, eid in entry_updates:
                    cursor.execute("""
                        UPDATE dbo.Operations
                        SET line_no = %s, page_no = %s
                        WHERE id = CAST(%s AS UNIQUEIDENTIFIER)
                    """, [line_no, page_no, eid])

            #  6. Approve the requested entry
            cursor.execute("""
                UPDATE dbo.Operations
                SET status = 'Approved',
                    approved_by = %s,
                    approved_at = GETUTCDATE()
                WHERE id = CAST(%s AS UNIQUEIDENTIFIER)
            """, [approved_by, id])

        return JsonResponse({
            "success": True,
            "message": "Entry approved successfully",
            "assigned_line_no": next((ln for ln, pn, eid in entry_updates if eid.upper() == str(entry_id).upper()), None),
            "assigned_page_no": next((pn for ln, pn, eid in entry_updates if eid.upper() == str(entry_id).upper()), None)
        })

    except Exception as e:
        print("Error in approve_operation:", str(e))
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": "Internal server error"}, status=500)








@api_view(["PATCH"])
@permission_classes([AllowAny])
def reject_operation(request, id):
    """
    Rejects an operation entry using the rejected_by string sent from the frontend.
    """
    try:
        # Get the rejected_by string from the request body
        data = json.loads(request.body.decode('utf-8'))
        rejected_by = data.get('rejected_by')

        if not rejected_by:
            return JsonResponse({"error": "Rejected by information required"}, status=400)

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE dbo.Operations
                SET status = 'Rejected',
                    rejected_by = %s,
                    rejected_at = GETUTCDATE()
                WHERE id = %s
            """, [rejected_by, id])

            if cursor.rowcount == 0:
                return JsonResponse({"error": "No entry found with this ID"}, status=404)

        return JsonResponse({"success": True, "message": "Entry rejected successfully"})

    except Exception as e:
        print("Error in reject_operation:", str(e))
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": "Internal server error"}, status=500)


def get_csrf_token(request):
    # CSRF token endpoint removed - using JWT token-based authentication
    return JsonResponse({'error': 'CSRF tokens not used - using JWT authentication'}, status=403)






@permission_classes([AllowAny])
@api_view(['GET'])
def list_for_chief(request):
    vessel_id = request.GET.get('vessel_id')
    if not vessel_id:
        return Response({"error": "vessel_id is required"}, status=400)

    with connection.cursor() as cursor:
        # Get pending entries with code letter
        cursor.execute("""
            SELECT o.*, c.code
            FROM dbo.Operations o
            INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id
            WHERE o.vessel_id = %s AND o.status = 'Pending' AND o.is_deleted = 0
            ORDER BY o.date DESC
        """, [vessel_id])
        pending = dictfetchall(cursor)

        # Get approved entries with code letter
        cursor.execute("""
            SELECT o.*, c.code
            FROM dbo.Operations o
            INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id
            WHERE o.vessel_id = %s AND o.status = 'Approved' AND o.is_deleted = 0
            ORDER BY o.date DESC
        """, [vessel_id])
        approved = dictfetchall(cursor)

    return Response({"pending": pending, "approved": approved})


# Assuming your dictfetchall function is defined here or imported

@permission_classes([AllowAny])
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# --- INDEPENDENT FUNCTION TO FETCH NON-DELETED ENTRIES ---

@permission_classes([AllowAny])
def get_non_deleted_entries_view(request):
    """
    Independent view function to fetch all entries where is_deleted = False (0).
    Includes related ORBCodes information.
    Expects 'vessel_id' as a query parameter.
    """
    vessel_id = request.GET.get('vessel_id')

    if not vessel_id:
        return JsonResponse({"error": "vessel_id is required"}, status=400)

    try:
        # Convert vessel_id string to UUID object for the query
        vessel_uuid = uuid.UUID(vessel_id)
    except ValueError:
        return JsonResponse({"error": "Invalid vessel_id format"}, status=400)

    try:
        # Use raw SQL to fetch non-deleted entries and join with ORBCodes
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    o.id,
                    o.date,
                    c.code, -- Get the code letter from ORBCodes
                    o.item_no,
                    o.record_of_operation,
                    o.status,
                    o.created_by,
                    o.is_deleted,
                    o.master_print,
                    o.entry_no,
                    o.approved_by,
                    o.approved_at
                FROM dbo.Operations o
                INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id -- Join to get code letter
                WHERE o.vessel = CAST(%s AS UNIQUEIDENTIFIER) AND o.is_deleted = 0 -- Filter non-deleted
                ORDER BY o.date DESC -- Order by date descending
            """, [str(vessel_uuid)])
            rows = dictfetchall(cursor) # Use your existing dictfetchall helper

        return JsonResponse(rows, safe=False) # safe=False allows serializing lists

    except Exception as e:
        print("❌ Error in get_non_deleted_entries_view:", str(e))
        return JsonResponse({"error": "Internal server error"}, status=500)

# --- END INDEPENDENT FUNCTION ---

# --- INDEPENDENT FUNCTION TO FETCH DELETED ENTRIES ---


@permission_classes([AllowAny])
def get_deleted_entries_view(request):
    """
    Independent view function to fetch all entries where is_deleted = True (1).
    Includes related ORBCodes information.
    Expects 'vessel_id' as a query parameter.
    """
    vessel_id = request.GET.get('vessel_id')

    if not vessel_id:
        return JsonResponse({"error": "vessel_id is required"}, status=400)

    try:
        # Convert vessel_id string to UUID object for the query
        vessel_uuid = uuid.UUID(vessel_id)
    except ValueError:
        return JsonResponse({"error": "Invalid vessel_id format"}, status=400)

    try:
        # Use raw SQL to fetch deleted entries and join with ORBCodes
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    o.id,
                    o.date,
                    c.code, -- Get the code letter from ORBCodes
                    o.item_no,
                    o.record_of_operation,
                    o.status,
                    o.created_by,
                    o.is_deleted,
                    o.entry_no,
                    o.master_print,
                    o.updated_by,       -- Include updated_by (who performed the soft delete)
                    o.updated_at        -- Include updated_at (when it was soft deleted)
                FROM dbo.Operations o
                INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id -- Join to get code letter
                WHERE o.vessel = CAST(%s AS UNIQUEIDENTIFIER) AND o.is_deleted = 1 -- Filter deleted
                ORDER BY o.date DESC -- Order by date descending
            """, [str(vessel_uuid)])
            rows = dictfetchall(cursor) # Use your existing dictfetchall helper

        return JsonResponse(rows, safe=False) # safe=False allows serializing lists

    except Exception as e:
        print("❌ Error in get_deleted_entries_view:", str(e))
        return JsonResponse({"error": "Internal server error"}, status=500)

# --- END INDEPENDENT FUNCTION ---



@permission_classes([AllowAny])
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# --- INDEPENDENT FUNCTION TO FETCH REJECTED ENTRIES ---


@permission_classes([AllowAny])
def get_rejected_entries_view(request):
    """
    Independent view function to fetch all entries where status = 'Rejected'.
    Includes related ORBCodes information.
    Expects 'vessel_id' as a query parameter.
    """
    vessel_id = request.GET.get('vessel_id')

    if not vessel_id:
        return JsonResponse({"error": "vessel_id is required"}, status=400)

    try:
        vessel_uuid = uuid.UUID(vessel_id)
    except ValueError:
        return JsonResponse({"error": "Invalid vessel_id format"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    o.id,
                    o.date,
                    c.code,
                    o.item_no,
                    o.record_of_operation,
                    o.status,
                    o.created_by,
                    o.is_deleted,
                    o.entry_no,
                    o.master_print,
                    o.rejected_by,      -- Include rejected_by
                    o.rejected_at       -- Include rejected_at
                FROM dbo.Operations o
                INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id
                WHERE o.vessel = CAST(%s AS UNIQUEIDENTIFIER) AND o.status = 'Rejected' -- Filter rejected
                ORDER BY o.date DESC
            """, [str(vessel_uuid)])
            rows = dictfetchall(cursor)

        return JsonResponse(rows, safe=False)

    except Exception as e:
        print("❌ Error in get_rejected_entries_view:", str(e))
        return JsonResponse({"error": "Internal server error"}, status=500)

# --- END INDEPENDENT FUNCTION ---


@permission_classes([AllowAny])
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# --- INDEPENDENT FUNCTION TO FETCH APPROVED ENTRIES ---

@permission_classes([AllowAny])
def get_approved_entries_view(request):
    """
    Independent view function to fetch all entries where status = 'Approved'.
    Includes related ORBCodes information.
    Expects 'vessel_id' as a query parameter.
    """
    vessel_id = request.GET.get('vessel_id')

    if not vessel_id:
        return JsonResponse({"error": "vessel_id is required"}, status=400)

    try:
        # Convert vessel_id string to UUID object for the query
        vessel_uuid = uuid.UUID(vessel_id)
    except ValueError:
        return JsonResponse({"error": "Invalid vessel_id format"}, status=400)

    try:
        # Use raw SQL to fetch approved entries and join with ORBCodes
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    o.id,
                    o.date,
                    c.code, -- Get the code letter from ORBCodes
                    o.item_no,
                    o.record_of_operation,
                    o.status,
                    o.created_by,
                    o.is_deleted,
                    o.entry_no,
                    o.master_print,
                    o.approved_by,      -- Include approved_by
                    o.approved_at       -- Include approved_at
                FROM dbo.Operations o
                INNER JOIN dbo.ORBCodes c ON o.orb_code_id = c.id -- Join to get code letter
                WHERE o.vessel = CAST(%s AS UNIQUEIDENTIFIER) AND o.status = 'Approved' -- Filter approved
                ORDER BY o.date DESC -- Order by date descending
            """, [str(vessel_uuid)])
            rows = dictfetchall(cursor) # Use your existing dictfetchall helper

        return JsonResponse(rows, safe=False) # safe=False allows serializing lists

    except Exception as e:
        print("❌ Error in get_approved_entries_view:", str(e))
        return JsonResponse({"error": "Internal server error"}, status=500)



@api_view(["POST"])
@permission_classes([AllowAny])
def update_print_status(request):
    """
    Handles the request to update IP and master_print for specific entries using raw SQL.
    Expects a JSON payload with 'entries' (list of IDs), 'ip' (string), and 'master_print' (ISO datetime string).
    """
    try:
        data = json.loads(request.body)
        entry_ids = data.get('entries', [])
        client_ip = data.get('ip')
        print_timestamp_str = data.get('master_print')

        if not isinstance(entry_ids, list) or not client_ip or not print_timestamp_str:
             return JsonResponse({"error": "Missing required fields: entries, ip, master_print."}, status=400)

        # Validate and convert string IDs to UUID objects for parameter safety
        valid_entry_uuids = []
        for eid in entry_ids:
            try:
                valid_uuid = uuid.UUID(str(eid))
                valid_entry_uuids.append(str(valid_uuid)) # Keep as string for SQL parameters, but validated
            except ValueError:
                print(f"❌ Invalid UUID in list received from frontend: {eid}")
                return JsonResponse({"error": f"Invalid UUID: {eid}"}, status=400)

        if not valid_entry_uuids:
            return JsonResponse({"error": "No valid entry IDs provided."}, status=400)

        # Use raw SQL with explicit CAST
        # Build the IN clause dynamically based on the number of IDs
        # This is safer than string formatting for the values, but the number of placeholders needs to match.
        placeholders = ','.join(['%s'] * len(valid_entry_uuids))
        sql_query = f"""
            UPDATE dbo.Operations
            SET IP = %s, master_print = %s
            WHERE id IN ({placeholders})
        """

        try:
            with connection.cursor() as cursor:
                # Pass parameters: client_ip, print_timestamp_str, and the list of UUID strings
                # The mssql backend should handle the UUID string to UNIQUEIDENTIFIER conversion for each %s in the IN clause.
                params = [client_ip, print_timestamp_str] + valid_entry_uuids
                cursor.execute(sql_query, params)
                rows_affected = cursor.rowcount
                print(f"✅ Raw SQL update affected {rows_affected} rows.")

        except Exception as e:
            print(f"❌ Error during raw SQL database update: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": "Internal server error during raw SQL update."}, status=500)

        return JsonResponse({
            "message": f"Successfully updated print status for {rows_affected} entries using raw SQL.",
            "entries_updated": valid_entry_uuids
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body."}, status=400)
    except Exception as e:
        print(f"Error in update_print_status initial processing: {str(e)}")
        return JsonResponse({"error": "Internal server error during request processing."}, status=500)



@permission_classes([AllowAny])
def get_client_internal_ip(request):
    """
    Returns the LOCAL IP address of the machine running the Django SERVER.
    This is the private IP address (e.g., 192.168.x.x) of the system where
    the Django development server is running, NOT the IP of the client browser.
    """
    # Get the local IP of the server machine using the Python utility function
    local_ip = utils.get_local_ip()
    print(f"Django Server's reported Local IP: {local_ip}") # Log the IP for debugging
    return JsonResponse({'internal_ip': local_ip})


@api_view(['POST'])
@permission_classes([AllowAny])
def save_pdf_metadata(request):
    """
    Expects JSON payload:
    {
        "filename": "unique_filename.pdf", // Just the filename
        "title": "PDF Title",
        "description": "Optional description",
        "created_by": "User Name",
        "vessel_id": "UUID", // Must be a valid UUID string
        "pdf_data": "base64_encoded_pdf_string" // The actual PDF content
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        print(f"DEBUG: Received data: {data}") # Log the received data

        # Decode the base64 PDF data
        pdf_base64 = data.get('pdf_data')
        if not pdf_base64:
             print("DEBUG: Missing 'pdf_data' field") # Log missing field
             return JsonResponse({'error': "Missing required field: 'pdf_data'"}, status=400)

        pdf_content = base64.b64decode(pdf_base64)
        print(f"DEBUG: Decoded PDF content length: {len(pdf_content)} bytes") # Log content length

        # Define the relative path and full path
        filename = data['filename']
        print(f"DEBUG: Filename: {filename}") # Log filename
        relative_path = os.path.join('orb', 'pdfs', filename)
        print(f"DEBUG: Relative path: {relative_path}") # Log relative path

        # Validate filename to prevent directory traversal (basic check)
        if '..' in filename or filename.startswith('/'):
            print("DEBUG: Invalid filename detected") # Log invalid filename
            return JsonResponse({'error': 'Invalid filename'}, status=400)

        full_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        print(f"DEBUG: Full path: {full_path}") # Log full path

        # Ensure the subdirectory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        print(f"DEBUG: Ensured directory exists: {os.path.dirname(full_path)}") # Log directory creation

        # Write the PDF content to the file
        with open(full_path, 'wb') as f:
            f.write(pdf_content)
        print(f"DEBUG: File saved successfully: {full_path}") # Log file save

        # Validate and convert vessel_id to UUID object
        vessel_id_str = data.get('vessel_id')
        print(f"DEBUG: Raw vessel_id_str from request: {vessel_id_str}, Type: {type(vessel_id_str)}") # Log raw value and type

        validated_vessel_uuid_str = None
        if vessel_id_str:
            try:
                # Validate the string format and create a UUID object
                vessel_uuid_obj = uuid.UUID(vessel_id_str)
                # Convert the UUID object back to a string for passing to SQL
                validated_vessel_uuid_str = str(vessel_uuid_obj)
                print(f"DEBUG: Parsed and validated vessel_uuid_str: {validated_vessel_uuid_str}, Type: {type(validated_vessel_uuid_str)}") # Log parsed UUID string
            except ValueError as ve:
                # If conversion fails, it's not a valid UUID string
                print(f"DEBUG: ValueError during UUID conversion: {ve}") # Log the ValueError
                os.remove(full_path) # Clean up the saved file
                print(f"Cleaned up file {full_path} due to invalid vessel_id format: {vessel_id_str}")
                return JsonResponse({'error': f"Invalid vessel_id format: {vessel_id_str}. Must be a valid UUID."}, status=400)
        else:
            print("DEBUG: vessel_id_str is None or empty, setting validated_vessel_uuid_str to None") # Log if vessel_id is missing

        print(f"DEBUG: Final validated_vessel_uuid_str for SQL: {validated_vessel_uuid_str}") # Log final value before SQL call

        # --- RAW SQL INSERT ---
        with connection.cursor() as cursor:
            # Use raw SQL INSERT
            # The SQL Server driver should handle the string representation of the UUID correctly if the column is UNIQUEIDENTIFIER
            # We cast the string parameter explicitly to UNIQUEIDENTIFIER in the query
            cursor.execute("""
                INSERT INTO dbo.GeneratedPDFs (
                    id, filename, filepath, title, description, created_by, created_at, vessel_id
                )
                OUTPUT INSERTED.id
                VALUES (
                    NEWID(), %s, %s, %s, %s, %s, SYSDATETIME(), CAST(%s AS UNIQUEIDENTIFIER)
                )
            """, [
                filename,
                relative_path,
                data['title'],
                data.get('description'), # Optional field, can be None
                data['created_by'],
                validated_vessel_uuid_str # Pass the validated string, cast in SQL
            ])
            result = cursor.fetchone()
            if result:
                inserted_id = str(result[0]) # Get the ID of the inserted row
                print(f"DEBUG: Raw SQL insert successful, ID: {inserted_id}") # Log success
            else:
                # This shouldn't happen if the INSERT was successful, but good to check
                print("DEBUG: Raw SQL insert did not return an ID")
                # Clean up the file if insert failed for some reason
                os.remove(full_path)
                print(f"Cleaned up file {full_path} due to potential insert failure.")
                return JsonResponse({'error': 'Database insert failed'}, status=500)

        # Return success response including the new ID
        return JsonResponse({'message': 'PDF metadata and file saved successfully', 'id': inserted_id}, status=201)

    except json.JSONDecodeError:
        print("DEBUG: JSON Decode Error") # Log JSON error
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except KeyError as e:
        print(f"DEBUG: KeyError: {e}") # Log KeyError
        # Clean up the file if it was saved before the KeyError
        # This is tricky without knowing full_path beforehand, but the main try handles file save first
        # Let's assume the error happens before file save or handle it here if full_path exists
        if 'full_path' in locals() and os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"Cleaned up file {full_path} due to KeyError.")
            except OSError:
                pass # Ignore errors during cleanup
        return JsonResponse({'error': f'Missing required field: {e}'}, status=400)
    except Exception as e:
        print(f"DEBUG: General Error saving PDF metadata or file: {e}") # Log the general error
        import traceback
        traceback.print_exc() # Print full traceback for detailed error info
        # Optionally, clean up the file if DB creation fails (and file was saved)
        # Check if full_path exists and try to remove it
        if 'full_path' in locals() and os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"Cleaned up file {full_path} due to DB error.")
            except OSError:
                pass # Ignore errors during cleanup
        return JsonResponse({'error': 'Internal server error'}, status=500)



@api_view(['GET'])
@permission_classes([AllowAny])
def list_pdfs(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        vessel_id = request.GET.get('vessel_id')
        pdfs = GeneratedPDF.objects.all()

        if vessel_id:
            # 1️⃣ Validate UUID (Python side only)
            try:
                uuid.UUID(vessel_id)
            except ValueError:
                return JsonResponse({'error': 'Invalid vessel ID format'}, status=400)

            # 2️⃣ SQL Server–safe filtering
            pdfs = pdfs.extra(
                where=["vessel_id = CAST(%s AS uniqueidentifier)"],
                params=[vessel_id]
            )

        # Pagination
        page_number = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 10))

        paginator = Paginator(pdfs, page_size)
        page_obj = paginator.get_page(page_number)

        pdf_list = []
        for pdf in page_obj:
            pdf_list.append({
                'id': str(pdf.id),
                'filename': pdf.filename,
                'title': pdf.title,
                'description': pdf.description,
                'created_by': pdf.created_by,
                'created_at': pdf.created_at.isoformat(),
                'vessel_id': str(pdf.vessel_id) if pdf.vessel_id else None,
                'download_url': f'/api/download-pdf/{pdf.id}/'
            })

        return JsonResponse({
            'pdfs': pdf_list,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_prev': page_obj.has_previous(),
        })

    except Exception as e:
        print("Error listing PDFs:", e)
        return JsonResponse({'error': 'Internal server error'}, status=500)



@permission_classes([AllowAny])
def download_pdf(request, pdf_id):
    """
    Serves the PDF file identified by pdf_id.
    Uses raw SQL to avoid ORM conversion issues with UUID.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        # Use raw SQL to fetch the filepath and filename
        with connection.cursor() as cursor:
            # Query using the pdf_id parameter (which should be a valid UUID string)
            # Cast the parameter explicitly to UNIQUEIDENTIFIER in the query
            cursor.execute("""
                SELECT filename, filepath
                FROM dbo.GeneratedPDFs
                WHERE id = CAST(%s AS UNIQUEIDENTIFIER)
            """, [pdf_id]) # Pass pdf_id as a single-item list for the parameter

            row = cursor.fetchone()

        if row is None:
            # No entry found with the given ID
            raise Http404("PDF not found")

        filename, filepath = row # Unpack the result

        # Ensure the filepath is safe and within the intended directory
        # e.g., MEDIA_ROOT or a specific PDF storage directory
        full_file_path = os.path.join(settings.MEDIA_ROOT, filepath) # Assuming filepath is relative to MEDIA_ROOT

        # Prevent directory traversal
        if not full_file_path.startswith(settings.MEDIA_ROOT):
             print(f"Attempted to access file outside MEDIA_ROOT: {full_file_path}")
             raise Http404("File not found")

        if not os.path.exists(full_file_path):
            print(f"File not found on disk: {full_file_path}")
            raise Http404("File not found")

        # Serve the file
        with open(full_file_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

    except Http404:
        raise
    except Exception as e:
        print(f"Error downloading PDF: {e}") # Log the error
        import traceback
        traceback.print_exc() # Print full traceback
        # Return a generic error for other exceptions
        return JsonResponse({'error': 'Internal server error'}, status=500)





@permission_classes([AllowAny])
@api_view(["GET"])
def get_all_crew_onboarding_history(request):
    """
    Fetch all entries from the Crew_Onboarding_History table.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, CrewID, Vessel, SignOnDate, SignOnPort, CrewStatus, is_active, is_deleted, is_verifiedByMtr, created_by, created_date, updated_by, updated_date, CycleId, Replacement_For
                FROM dbo.Crew_Onboarding_History
                WHERE is_deleted = 0
                ORDER BY created_date DESC
            """)
            rows = cursor.fetchall()

            # Convert rows to list of dictionaries
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]

        return JsonResponse({"success": True, "data": results})

    except Exception as e:
        print("Error fetching crew onboarding history:", str(e))
        return JsonResponse({"error": "Internal server error"}, status=500)



@permission_classes([AllowAny])
@api_view(["GET"])
def get_vessel_id_for_current_user(request):
    """
    Fetches the vessel ID for the currently logged-in user based on their CrewID
    by querying the Crew_Onboarding_History table.
    Requires session-based authentication (or adapt for token if needed).
    """
    # --- NEW: Session Authentication (or adapt for Token) ---
    if not request.session.get('logged_in'):
        return JsonResponse({"error": "Authentication required"}, status=401)

    # Get user's CrewID from session (or derive from token user if using tokens)
    # Assuming you stored CrewID in session during login (as CrewID is used for login)
    crew_id = request.session.get('user_crew_id') # Use the key you stored it under in user_login

    if not crew_id:
        return JsonResponse({"error": "Crew ID not found in session"}, status=403)
    # --- END NEW: Session Authentication ---

    try:
        with connection.cursor() as cursor:
            # Fetch the vessel ID from Crew_Onboarding_History for the given CrewID
            # Assumes 'is_active' or similar flag exists, or we take the latest entry by date
            cursor.execute("""
                SELECT Vessel
                FROM dbo.Crew_Onboarding_History
                WHERE CrewID = %s AND is_active = 1 AND is_deleted = 0
                ORDER BY SignOnDate DESC -- Order by sign-on date descending to get the most recent
                OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY -- Limit to 1 row (the most recent)
            """, [crew_id])
            vessel_row = cursor.fetchone()

            if not vessel_row:
                 # Optional: Try without is_active filter if the latest record might not be marked active yet
                 # Or handle the case differently based on your business logic
                 cursor.execute("""
                     SELECT Vessel
                     FROM dbo.Crew_Onboarding_History
                     WHERE CrewID = %s AND is_deleted = 0
                     ORDER BY SignOnDate DESC
                     OFFSET 0 ROWS FETCH NEXT 1 ROWS ONLY
                 """, [crew_id])
                 vessel_row = cursor.fetchone()


            if vessel_row:
                assigned_vessel_id = str(vessel_row[0]) # Convert UUID to string if necessary
                print(f"DEBUG: API - Returned vessel ID for user {crew_id} from Crew_Onboarding_History: {assigned_vessel_id}")
                return JsonResponse({"success": True, "vessel_id": assigned_vessel_id})
            else:
                # No active vessel found for the user
                print(f"WARNING: API - No active vessel found in Crew_Onboarding_History for user {crew_id}.")
                return JsonResponse({"error": "No active vessel assigned for this user."}, status=404)

    except Exception as e:
        print(f"Error in get_vessel_id_for_current_user for CrewID {crew_id}:", str(e))
        import traceback
        traceback.print_exc() # Print full traceback
        return JsonResponse({"error": "Internal server error"}, status=500)



@api_view(["GET"])
@authentication_classes([])     
@permission_classes([AllowAny])
def get_latest_entry_date(request):
    """
    Fetches the date of the latest non-deleted entry for a given vessel.
    Uses the correct column name 'vessel' as per the dbo.Operations table schema.
    """
    vessel_id = request.GET.get('vessel_id')

    if not vessel_id:
        return JsonResponse({"error": "Vessel ID is required"}, status=400)

    try:
        with connection.cursor() as cursor:
            # Query to find the most recent entry date/time for the given vessel
            # ✅ Use the correct column name 'vessel' instead of 'vessel_id'
            cursor.execute("""
                SELECT MAX(date) -- Get the latest date
                FROM dbo.Operations
                WHERE vessel = %s AND is_deleted = 0 -- Exclude deleted entries
            """, [vessel_id])
            latest_row = cursor.fetchone()

            if latest_row and latest_row[0]:
                latest_entry_date_db = latest_row[0] # This will be a datetime object from the DB
                # Convert datetime object to ISO string for JSON response
                latest_date_iso = latest_entry_date_db.isoformat()
                return JsonResponse({"latest_date": latest_date_iso})
            else:
                # Return null or a specific message if no entries exist
                return JsonResponse({"latest_date": None, "message": "No entries found for this vessel."}, status=404)

    except Exception as e:
        print(f"Error fetching latest entry date: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)
