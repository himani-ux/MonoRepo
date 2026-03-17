
#Backend ---> views.py

import json
import uuid
import os
import io
import logging
import traceback
import hashlib
import requests
from datetime import datetime, timezone
from datetime import timezone as datetime_timezone
from django.http import JsonResponse
from django.db import transaction
from django.db import connection
from reportlab.lib.colors import navy, black, red, white
from django.conf import settings
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from django.utils import timezone as django_timezone 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from modules.circular.circular.models import  HRM501,  Msc2ndSubCat, MscCategory, MscData, MscPriority,MscRankAssigned,MscShipNotification,MscSubCat,MscType,MscNotification
from modules.orb.orb.models import VesselData,MasterAppliedRank,CrewOnboardingHistory
from modules.circular.circular_office.models import FinalCrewList
from .models import MscReminder,Department,  MasterRole, MappingRoleUser, User
from datetime import timezone as python_timezone 
from django.db.models.expressions import RawSQL
import csv
from django.http import HttpResponse 
from django.conf import settings
from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives 
from django.db.models import Q
from django.db.models.expressions import RawSQL
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib import colors
import datetime # Standard library datetime   
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


font_path = os.path.join(settings.BASE_DIR, "modules", "circular", "fonts", "BOOKOS.TTF")

print("FONT PATH:", font_path)
print("FILE EXISTS:", os.path.exists(font_path))

if not os.path.exists(font_path):
    raise FileNotFoundError(f"Font not found at {font_path}")

pdfmetrics.registerFont(TTFont("bookos", font_path))








# font_path = os.path.join(os.getcwd(), "Backend", "fonts", "BOOKOS.TTF")
# print("FONT PATH:", font_path)
# print("FILE EXISTS:", os.path.exists(font_path))
# pdfmetrics.registerFont(
#     TTFont('bookos', r'C:\Users\PC\OneDrive\Desktop\Circular_id_backup\backend\fonts\BOOKOS.TTF')
# )



@api_view(['POST'])
@permission_classes([AllowAny])
def create_notification(request):
    print("=== create_notification: Starting function ===")
    if request.method != 'POST':
        print("create_notification: Invalid method, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    # --- Helper function to clean UUID strings ---
    def clean_uuid_string(value, field_name):
        """Clean and validate a UUID string. Returns cleaned string or None."""
        if not value:
            return None
        cleaned = value.strip().strip("'\"()[] ")
        if not cleaned:
            return None
        try:
            validated = uuid.UUID(cleaned)
            return str(validated)
        except ValueError as e:
            print(f"create_notification: Invalid UUID format for {field_name}: '{value}'. Error: {e}")
            return None
    
    # --- Helper to check if UUID exists in table and get name ---
    def get_uuid_and_name(table_name, uuid_str, field_name):
        """Check if UUID exists in table using raw SQL. Returns (uuid_str, name) or (None, None)."""
        if not uuid_str:
            return None, None
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT CAST(id AS NVARCHAR(36)), name FROM {table_name} WHERE id = CAST(%s AS UNIQUEIDENTIFIER)",
                    [uuid_str]
                )
                row = cursor.fetchone()
            
            if row:
                print(f"create_notification: Found in {table_name}: {row[1]} (UUID: {row[0]})")
                return row[0], row[1]  # Returns UUID as string and name
            else:
                print(f"create_notification: UUID {uuid_str} not found in {table_name}")
                return None, None
        except Exception as e:
            print(f"create_notification: Error looking up {table_name}: {e}")
            import traceback
            traceback.print_exc()
            return None, None
       
    try:
        # --- 1. Handle multipart form data ---
        title = request.POST.get('title', 'Untitled')
        body = request.POST.get('body', '')
        
        # --- Clean all UUID strings ---
        doc_type_uuid = clean_uuid_string(request.POST.get('type'), 'type')
        priority_uuid = clean_uuid_string(request.POST.get('priority'), 'priority')
        
        # Handle sub_cat and second_sub_cat - take first value if list
        sub_cat_raw = request.POST.getlist('sub_cat')
        second_sub_cat_raw = request.POST.getlist('second_sub_cat')
        
        sub_cat_uuid = clean_uuid_string(sub_cat_raw[0] if sub_cat_raw else None, 'sub_cat')
        second_sub_cat_uuid = clean_uuid_string(second_sub_cat_raw[0] if second_sub_cat_raw else None, 'second_sub_cat')
        
        print(f"create_notification: Cleaned UUIDs - type: {doc_type_uuid}, priority: {priority_uuid}")
        print(f"create_notification: Cleaned sub_cat: {sub_cat_uuid}, second_sub_cat: {second_sub_cat_uuid}")
        
        # --- Validate UUIDs exist in their tables and get names ---
        doc_type_uuid_verified, doc_type_display_name = get_uuid_and_name('msc_type', doc_type_uuid, 'type')
        priority_uuid_verified, priority_name = get_uuid_and_name('msc_priority', priority_uuid, 'priority')
        sub_cat_uuid_verified, sub_cat_name = get_uuid_and_name('msc_sub_cat', sub_cat_uuid, 'sub_category')
        second_sub_cat_uuid_verified, second_sub_cat_name = get_uuid_and_name('msc_2nd_sub_cat', second_sub_cat_uuid, 'second_sub_category')
        
        if not doc_type_display_name:
            doc_type_display_name = 'Unknown'
        
        # --- Validate required fields ---
         # --- Validate required fields ---
        # Get the department ID as a string (UUID)
        dept_id_string = request.POST.get('department') # Get the UUID string directly from the frontend
        print(f"create_notification: Received department ID string from frontend: {dept_id_string}")

        # You might want to validate the UUID format here
        # try:
        #     uuid.UUID(dept_id_string)
        # except ValueError:
        #     print(f"create_notification: Invalid UUID format for department: {dept_id_string}")
        #     return JsonResponse({'error': 'Invalid department ID format'}, status=400)

        # DO NOT convert dept_id_string to int
        # dept_value = int(dept_value) # ❌ Remove this line

        if not doc_type_uuid_verified or not dept_id_string: # Check for the string, not an integer
            print("create_notification: Missing type or department, returning 400")
            return JsonResponse({'error': 'type and department are required'}, status=400)

        # Determine the department display name based on the received UUID string
        # This mapping should ideally come from the database or a config file,
        # but for now, let's keep it here as a constant.
        DEPT_ID_TO_DISPLAY_NAME = {
            '8949308c-aa8a-ee11-987c-7413ea3d6a70': 'SEQ', # Assuming this UUID maps to 'SEQ'
            '8a49308c-aa8a-ee11-987c-7413ea3d6a70': 'Technical', # Assuming this UUID maps to 'Technical'
            # Add other mappings if needed
        }
        dept_display_name = DEPT_ID_TO_DISPLAY_NAME.get(dept_id_string, 'Unknown Dept') # Get display name, default to 'Unknown Dept' if UUID not found in map
        print(f"create_notification: Mapped department ID {dept_id_string} to display name: {dept_display_name}")

        current_year = datetime.datetime.now().year
        print(f"create_notification: dept_display_name: {dept_display_name}, current_year: {current_year}")

        # --- 2. Get next serial number using raw SQL ---
        print("create_notification: Calculating next serial number...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1 sr_no FROM msc_data 
                WHERE msc_type = CAST(%s AS UNIQUEIDENTIFIER) 
                AND YEAR(created_at) = %s 
                AND sr_no IS NOT NULL 
                ORDER BY sr_no DESC
                """,
                [doc_type_uuid_verified, current_year]
            )
            last_row = cursor.fetchone()

        if last_row and last_row[0]:
            try:
                last_serial = int(last_row[0].split('-')[-1])
                next_serial = last_serial + 1
                print(f"create_notification: Last serial was {last_serial}, next will be {next_serial}")
            except (ValueError, IndexError):
                next_serial = 1
                print("create_notification: Error parsing last serial, defaulting to 1")
        else:
            next_serial = 1
            print("create_notification: No previous records found, starting with 1")

       
        now = django_timezone.now()
        formatted_id = f"KSM/{doc_type_display_name}/{dept_display_name}/{current_year}-{next_serial:04d}"
        print(f"create_notification: Generated SR No: {formatted_id}")

        # --- Get created_by ---
        created_by_employee_id = request.POST.get('created_by')
        print(f"create_notification: created_by: {created_by_employee_id}")

        # --- Get Initial Publish Status ---
        initial_publish_status = int(request.POST.get('publish_status', 0))
        print(f"create_notification: publish_status: {initial_publish_status}")
        
        # --- Initialize publisher variables ---
        published_by_id = None
        published_on_datetime = None
        
        # --- Handle Direct Publish (Status 2) ---
        if initial_publish_status == 2:
            published_by_id = request.POST.get('published_by')
            published_on_iso_string = request.POST.get('published_on')
            print(f"create_notification: Direct publish - published_by: {published_by_id}, published_on: {published_on_iso_string}")

            if published_on_iso_string:
                try:
                    if published_on_iso_string.endswith('Z'):
                        published_on_datetime = datetime.datetime.fromisoformat(published_on_iso_string[:-1] + '+00:00')
                    else:
                        published_on_datetime = datetime.datetime.fromisoformat(published_on_iso_string)

                    if settings.USE_TZ and django_timezone.is_naive(published_on_datetime):
                        published_on_datetime = django_timezone.make_aware(published_on_datetime, django_timezone.utc)
                except ValueError as e:
                    print(f"create_notification: Invalid published_on format: {e}")
                    published_on_datetime = django_timezone.now()

        # --- Supersede Logic ---
        superseding_old_notification_sr_no = request.POST.get('superseded_id')
        print(f"create_notification: superseded_id: {superseding_old_notification_sr_no}")

        # --- Handle file attachment ---
        attachment_path = None
        attachment_name = None
        
        if request.FILES.get('attachment'):
            uploaded_file = request.FILES['attachment']
            print("create_notification: Processing file attachment...")
            
            pdf_data = {
                'title': request.POST.get('title', ''),
                'body': request.POST.get('body', ''),
                'doc_type_name': doc_type_display_name,
                'formatted_id': formatted_id,
                'current_date': now.strftime('%d-%m-%Y'),
                'superseding_old_notification_sr_no': superseding_old_notification_sr_no,
                'created_by_employee_id': created_by_employee_id,
            }
            
            merged_pdf_buffer = generate_pdf_with_cover_and_original(uploaded_file, pdf_data)
            
            filename = f"merged_{formatted_id.replace('/', '_')}.pdf"
            media_path = os.path.join(settings.MEDIA_ROOT, 'circular', 'attachments')
            os.makedirs(media_path, exist_ok=True)
            filepath = os.path.join(media_path, filename)
            
            with open(filepath, 'wb') as f:
                f.write(merged_pdf_buffer.getvalue())
            
            attachment_path = filepath
            attachment_name = filename
            print(f"create_notification: PDF saved at {filepath}")

        # --- Get and clean Vessel IDs ---
        received_vessel_ids = request.POST.getlist('vessel_ids')
        cleaned_vessel_ids = []
        for v_id in received_vessel_ids:
            cleaned = clean_uuid_string(v_id, 'vessel_id')
            if cleaned:
                cleaned_vessel_ids.append(cleaned)
        
        vessel_id_str = ', '.join(cleaned_vessel_ids) if cleaned_vessel_ids else None
        print(f"create_notification: vessel_ids: {vessel_id_str}")

        # --- Create notification record using RAW SQL ---
        received_title = request.POST.get('title', '')   
        print(f"create_notification: Creating MscData record using raw SQL...")
        
        # Format datetime for SQL Server
        created_at_str = now.strftime('%Y-%m-%d %H:%M:%S')
        published_on_str = published_on_datetime.strftime('%Y-%m-%d %H:%M:%S') if published_on_datetime else None
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO msc_data (
                    sr_no, msc_type, dept, category, sub_category, second_sub_category,
                    title, office_instructions, hashtags, created_by, created_at,
                    publish_status, published_by, published_on, is_active, is_deleted,
                    priority, attachment_name, attachment_path, vessel_id
                ) VALUES (
                    %s,
                    CAST(%s AS UNIQUEIDENTIFIER),
                    %s, %s, -- dept is now the UUID string, category is a string
                    CAST(%s AS UNIQUEIDENTIFIER),
                    CAST(%s AS UNIQUEIDENTIFIER),
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    CAST(%s AS UNIQUEIDENTIFIER),
                    %s, %s, %s
                )
                """,
                [
                    formatted_id,
                    doc_type_uuid_verified, # UUID string for msc_type_id
                    dept_id_string,         # UUID string for dept (changed from dept_value)
                    request.POST.get('category'), # String for category
                    sub_cat_uuid_verified,  # UUID string for sub_category_id
                    second_sub_cat_uuid_verified, # UUID string for second_sub_category_id
                    received_title,
                    body,
                    request.POST.get('hashtags'),
                    created_by_employee_id,
                    created_at_str,
                    initial_publish_status,
                    published_by_id,
                    published_on_str,
                    True,  # is_active
                    False, # is_deleted
                    priority_uuid_verified, # UUID string for priority_id
                    attachment_name,
                    attachment_path,
                    vessel_id_str
                ]
            )
        print(f"create_notification: Record inserted - SR No: {formatted_id}")

        # --- Finalize Supersede ---
        if superseding_old_notification_sr_no:
            print(f"create_notification: Finalizing supersede...")
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE msc_data 
                        SET is_superseeded = 1, superseeded_by = %s 
                        WHERE sr_no = %s
                        """,
                        [superseding_old_notification_sr_no, formatted_id]
                    )
                print(f"create_notification: Supersede updated")
            except Exception as e:
                print(f"create_notification: Supersede error: {e}")

        # --- Store Delivery Records (for published notifications) ---
        if initial_publish_status == 2:
            print(f"create_notification: Creating delivery records...")
            try:
                dept_name_for_crews = 'Deck' if dept_value == 0 else 'Engine' if dept_value == 1 else None
                if dept_name_for_crews:
                    DEPARTMENT_NAME_TO_UUID = {
                        'Deck': '8949308c-aa8a-ee11-987c-7413ea3d6a70',
                        'Engine': '8a49308c-aa8a-ee11-987c-7413ea3d6a70'
                    }
                    dept_uuid = DEPARTMENT_NAME_TO_UUID.get(dept_name_for_crews)

                    if dept_uuid:
                        hrm_records_for_dept = HRM501.objects.filter(department_name=dept_uuid)
                        hrm_ids_for_dept = [rec.id for rec in hrm_records_for_dept]

                        if hrm_ids_for_dept:
                            final_crew_list_for_dept = FinalCrewList.objects.filter(Crew_ref_id__in=hrm_ids_for_dept)
                            final_crew_ids_for_dept = [crew.CrewID for crew in final_crew_list_for_dept]

                            relevant_final_crew_ids = final_crew_ids_for_dept
                            if cleaned_vessel_ids:
                                try:
                                    uuid_vessel_ids = [uuid.UUID(v_id) for v_id in cleaned_vessel_ids]
                                    onboardings_for_vessels = CrewOnboardingHistory.objects.filter(
                                        CrewID__in=final_crew_ids_for_dept,
                                        vessel__in=uuid_vessel_ids
                                    )
                                    relevant_final_crew_ids = list(onboardings_for_vessels.values_list('CrewID', flat=True))
                                except ValueError as ve:
                                    print(f"create_notification: Vessel UUID error: {ve}")

                            if relevant_final_crew_ids:
                                print(f"create_notification: {len(relevant_final_crew_ids)} crews to notify")

            except Exception as e:
                print(f"create_notification: Delivery records error: {e}")
                import traceback
                traceback.print_exc()

        # --- Get the inserted record's ID ---
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM msc_data WHERE sr_no = %s",
                [formatted_id]
            )
            id_row = cursor.fetchone()
            notification_id = id_row[0] if id_row else 'unknown'

        print("=== create_notification: Completed successfully ===")
        return JsonResponse({
            'success': True,
            'id': str(notification_id),
            'sr_no': formatted_id
        }, status=201)
    
    except Exception as e:
        print(f"❌ Error in create_notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Database error'}, status=400)
    
# ================ ADD THESE FUNCTIONS AFTER YOUR MAIN FUNCTION ================


def generate_pdf_with_cover_and_original(uploaded_file, notification_data):
    """
    Generate PDF with cover page + multi-page content, then merge with original PDF.
    """
    # Create in-memory PDF
    cover_buffer = io.BytesIO()
    c = canvas.Canvas(cover_buffer, pagesize=letter)
    width, height = letter
    margin = 50

    # Logo settings
    logo_width = 30
    logo_height = 50
    logo_path =  os.path.join(settings.BASE_DIR, "static", "ksm-logo.png")

    # ===============================
    # PAGE 1 HEADER  (UPDATED)
    # ===============================
    divider_y = draw_pdf_header(
        c, width, height, margin,
        logo_path, logo_width, logo_height
    )

    # -------------------------------
    # Document Title
    # -------------------------------
    c.setFont("Helvetica-Bold", 16)
    title_y = divider_y - 45
    dynamic_title_text = _get_dynamic_title(notification_data['doc_type_name'])
    c.drawCentredString(width / 2, title_y, dynamic_title_text)

    # -------------------------------
    # Serial + Date
    # -------------------------------
    c.setFont("Helvetica", 10)
    ref_date_y = title_y - 30
    c.drawString(margin, ref_date_y, f"Serial_no. : {notification_data['formatted_id']}")
    c.drawRightString(width - margin, ref_date_y, f"Date: {notification_data['current_date']}")

    # Supersedes
    if notification_data.get('superseding_old_notification_sr_no'):
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(1, 0, 0)
        c.drawRightString(
            width - margin, ref_date_y + 10,
            f"This letter Supersedes {notification_data['superseding_old_notification_sr_no']}"
        )
        c.setFillColorRGB(0, 0, 0)

    # Subject
    c.setFont("Helvetica-Bold", 12)
    subject_y = ref_date_y - 35
    c.drawString(margin, subject_y, f"SUBJECT: {notification_data['title']}")

    # ===============================
    # BODY CONTENT
    # ===============================
    c.setFont("Helvetica", 11)
    body_start_y = subject_y - 40
    y_position = body_start_y

    body_lines = _wrap_text_simple(
        c, notification_data['body'],
        width - 2 * margin, "Helvetica", 11
    )

    FOOTER_HEIGHT = 80
    BOTTOM_MARGIN = 40
    available_bottom_space = FOOTER_HEIGHT + BOTTOM_MARGIN

    page_number = 1
    last_body_y_position = y_position

    for line in body_lines:

        if y_position > (available_bottom_space + margin):
            c.drawString(margin, y_position, line)
            y_position -= 15
            last_body_y_position = y_position

        else:
            # FOOTER for current page
            _add_footer_to_page(
                c, width, margin, notification_data,
                page_number, last_body_y_position
            )

            # NEW PAGE
            c.showPage()
            page_number += 1

            # ===============================
            # REUSE EXACT SAME HEADER HERE
            # ===============================
            divider_y = draw_pdf_header(
                c, width, height, margin,
                logo_path, logo_width, logo_height
            )

            # Document Info
            c.setFont("Helvetica", 10)
            c.drawString(margin, divider_y - 20, f"Document: {notification_data['formatted_id']}")
            c.drawRightString(width - margin, divider_y - 20, f"Page {page_number}")

            # Divider under doc info
            c.setStrokeColorRGB(0, 0, 0.5)
            c.line(margin, divider_y - 40, width - margin, divider_y - 40)
            c.setStrokeColorRGB(0, 0, 0)

            # Continue body
            y_position = divider_y - 60
            c.setFont("Helvetica", 11)
            c.drawString(margin, y_position, line)
            y_position -= 15
            last_body_y_position = y_position

    # Final footer
    _add_footer_to_page(
        c, width, margin, notification_data,
        page_number, last_body_y_position
    )

    c.save()
    cover_buffer.seek(0)

    # ===============================
    # MERGE WITH ORIGINAL PDF
    # ===============================
    writer = PdfWriter()

    cover_pdf = PdfReader(cover_buffer)
    for p in cover_pdf.pages:
        writer.add_page(p)

    try:
        original_pdf = PdfReader(uploaded_file)
        for p in original_pdf.pages:
            writer.add_page(p)
    except:
        print("Original PDF unreadable, continuing with only generated pages.")

    final_buffer = io.BytesIO()
    writer.write(final_buffer)
    final_buffer.seek(0)
    return final_buffer


def _wrap_text_simple(canvas_obj, text, max_width, font_name, font_size):
    """Simple text wrapping function"""
    lines = []
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if canvas_obj.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    return lines


def _get_dynamic_title(doc_type_name):
    """Get dynamic title based on document type"""
    title_mapping = {
        'alert': 'SAFETY ALERT',
        'circular': 'CIRCULAR LETTER',
        'workinstruction': 'WORK INSTRUCTION LETTER'
    }
    return title_mapping.get(doc_type_name.lower(), f"{doc_type_name.upper()} LETTER")


def draw_pdf_header(c, width, height, margin, logo_path, logo_width, logo_height):
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0, 0, 0.5)  # navy

    text_baseline_y = height - margin
    text_height = 12

    # Perfect center alignment for ALL pages
    text_center_y = text_baseline_y - (text_height / 2)
    logo_y = text_center_y - (logo_height / 2)

    # Draw logo
    try:
        c.drawImage(logo_path, margin, logo_y,
                    width=logo_width, height=logo_height, mask='auto')
        company_x = margin + logo_width + 8
    except:
        company_x = margin

    # Company name
    c.drawString(company_x, text_baseline_y, "KAIZEN SHIP MANAGEMENT CO. LTD")
    c.setFillColorRGB(0, 0, 0)

    # Divider line
    divider_y = text_baseline_y - 40
    c.setStrokeColorRGB(0, 0, 0.5)
    c.line(margin, divider_y, width - margin, divider_y)
    c.setStrokeColorRGB(0, 0, 0)

    return divider_y

def _add_footer_to_page(canvas_obj, width, margin, notification_data, page_number, last_body_y):
    """
    Add footer to the current page, positioned below the last body text with proper spacing
    """
    # Calculate footer position based on the last body text position
    # Add significant padding (e.g., 40 points) below the last body text to avoid overlap
    footer_y = last_body_y - 40  # Increased from 20 to 40 for better spacing
    
    # If the calculated footer position is too low (close to bottom), adjust it
    min_footer_y = 50  # Minimum Y position for footer (adjust as needed)
    if footer_y < min_footer_y:
        footer_y = min_footer_y
    
    # Draw a horizontal line above the footer for visual separation
    canvas_obj.setStrokeColorRGB(0, 0, 0.5)  # navy
    canvas_obj.line(margin, footer_y + 10, width - margin, footer_y + 10)
    canvas_obj.setStrokeColorRGB(0, 0, 0)  # black
    
    canvas_obj.setFont("Helvetica", 9)
    created_by_part = f"Created By: {notification_data.get('created_by_employee_id', 'Unknown User')}"
    footer_text = f"Sr. No: {notification_data['formatted_id']} | {created_by_part}"
    
    # Draw footer text
    canvas_obj.drawString(margin, footer_y, footer_text)
    canvas_obj.drawRightString(width - margin, footer_y, f"Created At: {notification_data['current_date']} | Page {page_number}")



@api_view(['GET'])
@permission_classes([AllowAny])
def get_notifications(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET allowed'}, status=405)
    
    # --- Start: Add sorting logic ---
    # Get optional query parameters for sorting
    sort_by_param = request.GET.get('sort_by', 'created_at') # Default sort column
    sort_order_param = request.GET.get('sort_order', 'desc').lower() # Default sort order
    
    # Whitelist allowed sort columns to prevent SQL injection
    allowed_sort_columns = [
        'id', 'sr_no', 'msc_type', 'dept', 'category', 'created_at', 
        'publish_status', 'created_by', 'priority', 'published_by', 'published_at',
        # Add more if needed
    ]
    
    # Sanitize sort_by
    if sort_by_param not in allowed_sort_columns:
        sort_by_db = 'created_at' # Fallback to default if invalid
    else:
        sort_by_db = sort_by_param
        
    # Sanitize sort_order
    if sort_order_param not in ['asc', 'desc']:
        sort_order_db = 'DESC' # Fallback to descending if invalid
    else:
        sort_order_db = 'ASC' if sort_order_param == 'asc' else 'DESC'
        
    # Construct the ORDER BY clause safely
    order_clause = f"{sort_by_db} {sort_order_db}"
    # --- End: Add sorting logic ---

    # --- NEW: Add publish_status filtering logic ---
    publish_status_filter = request.GET.get('publish_status')
    publish_status_in_filter = request.GET.get('publish_status__in')
    
    # Start with base queryset and always filter for publish_status 1, 2, 3
    # --- CHANGED: Remove 'category' from select_related ---
    notifications_queryset = MscData.objects.filter(
        publish_status__in=[1, 2, 3],
        is_deleted=False
    ).select_related(
        'msc_type', #  this is a ForeignKey
        'sub_category', #  this is a ForeignKey
        'second_sub_category', #  this is a ForeignKey
        'priority' # this is a ForeignKey
    ) 
    
    # Apply additional publish_status filter if provided via query parameter
    if publish_status_filter:
        try:
            status = int(publish_status_filter)
            # Only apply if the specific status is one of 1, 2, or 3
            if status in [1, 2, 3]:
                notifications_queryset = notifications_queryset.filter(publish_status=status)
        except ValueError:
            # Handle invalid status - ignore filter or return error
            pass # Ignore invalid filter for now
    
    # Apply publish_status__in filter if provided via query parameter
    elif publish_status_in_filter:
        try:
            # Split comma-separated string and convert to integers
            statuses = [int(s.strip()) for s in publish_status_in_filter.split(',') if s.strip()]
            if statuses:
                # Only include statuses that are in our allowed range [1, 2, 3]
                filtered_statuses = [s for s in statuses if s in [1, 2, 3]]
                if filtered_statuses:
                    notifications_queryset = notifications_queryset.filter(publish_status__in=filtered_statuses)
        except ValueError:
            # Handle invalid statuses - ignore filter or return error
            pass # Ignore invalid filter for now
    # --- END: Add publish_status filtering logic ---

    # --- Use Django ORM for better sorting and filtering ---
    # Apply ordering using Django ORM
    # Prefix with '-' for descending order in ORM
    orm_ordering = f"-{sort_by_db}" if sort_order_db == 'DESC' else sort_by_db
    notifications_queryset = notifications_queryset.order_by(orm_ordering)
    # --- End Django ORM sorting ---
    
    # Use .values() on the (potentially filtered and ordered) queryset
    # --- CHANGED: Use values() only for fields that are NOT ForeignKeys ---
    # Or, iterate over the queryset objects (n) and access related object properties directly.
    # Since you are using select_related, iterating over objects is fine.
    # notifications = notifications_queryset.values(...) # If using values()

    result = []
    # --- CHANGED: Iterate over objects (n) instead of .values() ---
    for n in notifications_queryset:
        n_dict = {
            'id': str(n.id),
            'sr_no': n.sr_no,
            'msc_type': n.msc_type.name if n.msc_type else None, # Access the name via the ForeignKey
            'dept': n.dept,
            # --- CHANGED: Access 'category' as a string ---
            'category': n.category, # n.category is the string name, not an object
            'sub_category': n.sub_category.name if n.sub_category else None, # Access the name via the ForeignKey
            'second_sub_category': n.second_sub_category.name if n.second_sub_category else None, # Access the name via the ForeignKey
            'office_instructions': n.office_instructions,
            'hashtags': n.hashtags,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'publish_status': n.publish_status,
            'priority': n.priority.name if n.priority else None, # Access the name via the ForeignKey
            'attachment_name': n.attachment_name,
            'attachment_path': n.attachment_path,
            'created_by': n.created_by,
            'published_by': n.published_by,
            'published_on': n.published_on.isoformat() if n.published_on else None,
            # Add other fields as needed
            
        }
        # Generate full URL from attachment_name
        if n_dict.get('attachment_name'):
            n_dict['attachment_url'] = f"{settings.MEDIA_URL}circular/attachments/{n_dict['attachment_name']}"
        else:
            n_dict['attachment_url'] = None
        result.append(n_dict)

    print(f"get_notifications: Returning {len(result)} notifications.")
    return JsonResponse(result, safe=False)  


@api_view(['GET'])
@permission_classes([AllowAny])
def get_notification_details(request, sr_no):
    """
    Returns the details of a single notification by its SR No.
    Expects the SR No in the URL.
    Uses filter().first() to handle potential non-uniqueness of sr_no.
    Includes attachment_url generation.
    Assumes category is a CharField storing a name string, while msc_type, sub_category, second_sub_category, priority are ForeignKey fields.
    """
    print(f"=== get_notification_details: Starting for SR No {sr_no} ===")

    if request.method != 'GET':
        print("get_notification_details: Invalid method, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    try:
        # Use filter().first() to get one record, even if sr_no is not unique
        # This avoids MultipleObjectsReturned error, but might lead to fetching the wrong record if sr_no is duplicated.
        # The ideal fix is to make sr_no unique in the database.
        # --- CHANGED: Only select_related for ACTUAL ForeignKey fields ---
        # 'category' is a CharField, so it's excluded from select_related.
        notification = MscData.objects.filter(
            sr_no=sr_no, is_deleted=False
        ).select_related(
            'msc_type', 'sub_category', 'second_sub_category', 'priority' # Only these are ForeignKeys
        ).first()

        if not notification:
             print(f"get_notification_details: Notification with SR No {sr_no} not found or is deleted.")
             return JsonResponse({'error': f'Notification with SR No {sr_no} not found or is deleted.'}, status=404)

        print(f"get_notification_details: Found notification. ID: {notification.id}, SR No: {notification.sr_no}")

        # --- SAFE ACCESS FOR FOREIGN KEY FIELDS (with error handling) ---
        # Access related object names with error handling during serialization
        # This handles cases where the *_id column might contain an invalid UUID or point to a non-existent record.
        def safe_get_fk_name(obj, field_name, display_name):
            """
            Safely gets the name of a related object.
            Returns the name string if successful, an error message if the lookup fails.
            """
            try:
                related_obj = getattr(obj, field_name)
                if related_obj:
                    return related_obj.name
                else:
                    # If the ForeignKey field is nullable and the value is NULL
                    return f"No {display_name} assigned"
            except AttributeError as ae:
                # This happens if the related object doesn't exist (e.g., ID in DB doesn't match any MscType record)
                # The error occurs when trying to access obj.msc_type.name if obj.msc_type (the related object fetch) itself fails.
                # The initial select_related should have prevented this AttributeError for the object access itself,
                # but if the related object exists but lacks a 'name' attribute, this catches that.
                print(f"get_notification_details: AttributeError accessing {display_name} name for notification {obj.sr_no}: {ae}")
                # Attempt to get the raw ID field name (e.g., 'msc_type_id' for field 'msc_type')
                id_field_name = f"{field_name}_id"
                raw_id = getattr(obj, id_field_name, 'N/A')
                return f"Error fetching {display_name} (ID: {raw_id}): Attribute Error"
            except Exception as e: # Catch any other potential errors during access
                print(f"get_notification_details: Error accessing {display_name} for notification {obj.sr_no}: {e}")
                # Attempt to get the raw ID field name (e.g., 'msc_type_id' for field 'msc_type')
                id_field_name = f"{field_name}_id"
                raw_id = getattr(obj, id_field_name, 'N/A')
                return f"Error fetching {display_name}: {type(e).__name__} - {e} (ID: {raw_id})"

        # --- END SAFE ACCESS ---

        # Serialize the notification data to JSON
        # You can customize this to include only the fields you need
        notification_data = {
            'id': str(notification.id), # Convert UUID to string for JSON serialization (if id is UUIDField)
            'sr_no': notification.sr_no,
            # --- CHANGED: Use safe access for ForeignKey names ---
            'msc_type': safe_get_fk_name(notification, 'msc_type', 'MscType'),
            'dept': notification.dept,
            # --- CHANGED: Access 'category' as a direct CharField (name string) ---
            'category': notification.category, # Access the name string directly
            # --- END CHANGED ---
            'sub_category': safe_get_fk_name(notification, 'sub_category', 'MscSubCat'),
            'second_sub_category': safe_get_fk_name(notification, 'second_sub_category', 'Msc2ndSubCat'),
            'office_instructions': notification.office_instructions,
            'hashtags': notification.hashtags,
            'created_by': notification.created_by,
            'created_at': notification.created_at.isoformat() if notification.created_at else None,
            'publish_status': notification.publish_status,
            'publish_comment': notification.publish_comment,
            'published_by': notification.published_by,
            'published_on': notification.published_on.isoformat() if notification.published_on else None,
            'is_superseeded': notification.is_superseeded,
            'superseeded_by': notification.superseeded_by,
            'is_active': notification.is_active,
            'is_deleted': notification.is_deleted,
            'priority': safe_get_fk_name(notification, 'priority', 'MscPriority'),
            'attachment_name': notification.attachment_name,
            'attachment_path': notification.attachment_path,
            # --- NEW: Generate attachment_url ---
            'attachment_url': f"{settings.MEDIA_URL}circular/attachments/{notification.attachment_name}" if notification.attachment_name else None,
            # --- END NEW ---
            # Add any other fields you need for the vessel list logic or display
        }

        print("get_notification_details: Returning notification data.")
        return JsonResponse(notification_data)

    except Exception as e:
        print(f"get_notification_details: Error occurred - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_notifications(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET allowed'}, status=405)
    
    created_by_id = request.GET.get('created_by')
    if not created_by_id:
        return JsonResponse({'error': 'created_by parameter is required'}, status=400)

    try:
        # --- Use Django ORM for consistency and ease of access to fields ---
        # Filter using ORM
        notifications_queryset = MscData.objects.filter(
            created_by=created_by_id,
            publish_status__in=[2, 3] # Approved or Rejected
        ).order_by('-created_at') # Default sort

        # Use .values() to get specific fields, including attachment_name
        notifications = notifications_queryset.values(
            'id', 'sr_no', 'msc_type', 'dept', 'category',
            'sub_category', 'second_sub_category', 'office_instructions',
            'hashtags', 'created_at',  'publish_status', 'priority',
            'attachment_path', 'attachment_name', 'created_by', 'published_by', 'published_on', 'publish_comment', 'is_deleted',
        )
        # --- End ORM usage ---

        result = []
        for n in notifications:
            n_dict = dict(n)
            
            # --- CORRECTED: Generate full URL from attachment_name (like get_notifications) ---
            if n_dict.get('attachment_name'):
                # Use the same logic as get_notifications
                n_dict['attachment_url'] = f"{settings.MEDIA_URL}circular/attachments/{n_dict['attachment_name']}"
            else:
                n_dict['attachment_url'] = None
            # --- END CORRECTED ---
                
            result.append(n_dict)

        return JsonResponse(result, safe=False)

    except Exception as e:
        print(f"Error in get_user_notifications: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_notification_status(request, notification_sr_no):
    """
    Updates the status of a notification identified by its SR No.
    Handles approval (status=2), rejection (status=3), and PDF cover update.
    NO VESSEL/CREW DELIVERY RECORD CREATION HERE.
    That logic is handled by link_notification_to_ranks.
    """
    print(f"=== update_notification_status: Starting for SR No {notification_sr_no} ===")

    if request.method != 'POST':
        print(f"update_notification_status: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        new_status = data.get('publish_status')
        comment = data.get('publish_comment')

        if new_status not in [2, 3]: # Assuming 2 is approve, 3 is reject
            print(f"update_notification_status: Invalid status received: {new_status}")
            return JsonResponse({'error': 'Invalid status for update. Must be 2 (approve) or 3 (reject).'}, status=400)

        print(f"update_notification_status: Data received -> {data}")

        published_by_id = None
        published_on_datetime = None

        # === Handle APPROVAL (Status 2) ===
        if new_status == 2:
            published_by_id = data.get('published_by')
            published_on_iso_string = data.get('published_on')

            if published_on_iso_string:
                try:
                    if published_on_iso_string.endswith('Z'):
                        published_on_datetime = datetime.datetime.fromisoformat(published_on_iso_string[:-1] + '+00:00')
                    else:
                        published_on_datetime = datetime.datetime.fromisoformat(published_on_iso_string)

                    if django_settings.USE_TZ and django_timezone.is_naive(published_on_datetime):
                        published_on_datetime = django_timezone.make_aware(published_on_datetime, django_timezone_utc)
                except ValueError as e:
                    print(f"⚠️ Warning: Invalid published_on format '{published_on_iso_string}': {e}")
                    published_on_datetime = django_timezone.now()
            else:
                published_on_datetime = django_timezone.now()

            print(f"   Setting published_by to: {published_by_id}")
            print(f"   Setting published_on to: {published_on_datetime}")

        # === Fetch Notification for Department Info (for PDF update) ===
        # This is still needed for the PDF cover generation logic below
        notification_for_dept = MscData.objects.filter(sr_no=notification_sr_no).first()
        if not notification_for_dept:
            print(f"update_notification_status: Notification with SR No {notification_sr_no} not found.")
            return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)

        dept_name_for_crews = 'Deck' if notification_for_dept.dept == 0 else 'Engine' if notification_for_dept.dept == 1 else 'Unknown'
        print(f"update_notification_status: Department determined from notification details: {dept_name_for_crews} (Dept Value: {notification_for_dept.dept})")

        # Get vessel IDs from the request data (sent during approval)
        # We still receive them in the request, but we don't process them here anymore
        vessel_ids_from_request = data.get('vessel_ids', []) # Expecting a list of vessel UUID strings
        print(f"update_notification_status: Received vessel_ids from request (will be handled by link_notification_to_ranks): {vessel_ids_from_request}")

        # Get rank IDs from the request data (sent during approval)
        # We still receive them in the request data, but we don't process them here anymore
        rank_ids_from_request = data.get('rank_ids', []) # Expecting a list of rank UUID strings
        print(f"update_notification_status: Received rank_ids from request (will be handled by link_notification_to_ranks): {rank_ids_from_request}")

        # --- NEW: Update PDF Cover (if Approved and Attachment exists) ---
        # It REPLACES the existing first page (cover) with an updated one containing approval info.
                 # --- NEW: Update PDF Cover (if Approved and Attachment exists) ---
        # It REPLACES the existing first page (cover) with an updated one containing approval info.
        if new_status == 2:  # Only update cover if status is changing to 2 (approved)
            print(f"update_notification_status: Status is 2, checking for PDF to update cover for {notification_sr_no}")
            try:
                # Find the notification object again to get its current state and attachment path
                notification_to_update = MscData.objects.filter(sr_no=notification_sr_no).first()
                if not notification_to_update:
                    print(f"update_notification_status: Notification {notification_sr_no} not found for PDF update.")
                    # Continue with the status update even if PDF update fails
                elif not notification_to_update.attachment_path:
                    print(f"update_notification_status: Notification {notification_sr_no} has no attachment path, skipping PDF cover update.")
                    # Continue with the status update even if PDF update fails
                else:
                    print(f"update_notification_status: Found notification with attachment path: {notification_to_update.attachment_path}")
                    print("update_notification_status: Reading existing PDF for cover replacement...")

                    # 1. Read the existing PDF (this is the original PDF created by create_notification)
                    original_pdf_reader = PdfReader(notification_to_update.attachment_path)

                    # 2. Generate the UPDATED COVER PAGE (with approval info and body) - NOW GENERATE ALL PAGES
                    print("update_notification_status: Generating updated cover page with approval info and body...")

                    # Create a new PDF buffer for the NEWLY GENERATED PAGES (cover + body text + footer)
                    cover_buffer = io.BytesIO()
                    c = canvas.Canvas(cover_buffer, pagesize=letter)
                    width, height = letter
                    margin = 50
                    
                    # Define constants for spacing
                    FOOTER_HEIGHT = 80      # space footer occupies
                    BOTTOM_PADDING = 40     # extra gap between text & footer
                    STOP_Y = FOOTER_HEIGHT + BOTTOM_PADDING
                    
                    page_number = 1  # Track page number for headers

                    # --- Page 1: Header and Title ---
                    # Company Header (with Logo)
                    c.setFont("Helvetica-Bold", 12)
                    c.setFillColor(navy)

                    logo_path = os.path.join(settings.BASE_DIR, "static", "ksm-logo.png")
                    logo_width = 30
                    logo_height = 50
                    
                    # Calculate the vertical center for the logo based on the text baseline
                    # The text is drawn at height - margin, and text height is approximately 12 points
                    text_baseline_y = height - margin
                    text_height = 12  # Approximate font height
                    text_vertical_center = text_baseline_y - (text_height / 2)
                    
                    # Position the logo so its vertical center aligns with the text's vertical center
                    logo_y = text_vertical_center - (logo_height / 2)
                    logo_x = margin  # Keep at left margin

                    try:
                        c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, mask='auto')
                        company_name_x = logo_x + logo_width + 8  # Position text to the right of logo
                    except Exception as logo_err:
                        print(f"⚠️ Could not load or draw logo for updated cover: {logo_err}")
                        company_name_x = margin  # If logo fails, start text at margin

                    # Draw the company name at the baseline
                    c.drawString(company_name_x, height - margin, "KAIZEN SHIP MANAGEMENT CO. LTD")
                    c.setFillColor(black)

                    # Divider Line - Adjust this to be closer to the company name
                    divider_y = height - margin - 40  # This puts it 30 points below the text baseline
                    c.setStrokeColor(navy)
                    c.line(margin, divider_y, width - margin, divider_y)
                    c.setStrokeColor(black)

                    # Document Title
                    c.setFont("Helvetica-Bold", 16)
                    title_y = divider_y - 45

                    # --- CRITICAL FIX: Safely access msc_type name ---
                                        # --- NEW: Extract Document Type Name from SR No (Robust Fallback) ---
                    # SR No format: KSM/{Type}/{Department}/{Year}-{Serial}
                    # Example: KSM/Alert/Technical/2025-0004
                    sr_no_parts = notification_to_update.sr_no.split('/')
                    if len(sr_no_parts) >= 2: # Ensure the format is correct and has at least 'KSM' and 'Type'
                        extracted_type_name_from_sr_no = sr_no_parts[1] # The second part is the type name
                        print(f"update_notification_status: Extracted document type name '{extracted_type_name_from_sr_no}' from SR No '{notification_to_update.sr_no}'.")
                    else:
                        print(f"❌ update_notification_status: Could not extract document type from SR No '{notification_to_update.sr_no}'. Expected format: prefix/type/department/year-serial. Using fallback logic or default.")
                        extracted_type_name_from_sr_no = "UnknownType" # Fallback if parsing fails
                    # --- END NEW ---

                    doc_title_map = {
                        'Alert': ' SAFETY ALERT ',
                        'Circular': 'CIRCULAR LETTER',
                        'WorkInstruction': 'WORK INSTRUCTION LETTER',
                        'alert': ' SAFETY ALERT ',
                        'circular': 'CIRCULAR LETTER',
                        'workinstruction': 'WORK INSTRUCTION LETTER',
                    }
                    doc_title = "UNKNOWN DOCUMENT TYPE" # Default in case of error
                    try:
                        doc_title = doc_title_map.get(extracted_type_name_from_sr_no, f"{extracted_type_name_from_sr_no.upper()} LETTER")
                        print(f"update_notification_status: Determined document title for PDF cover: '{doc_title}' using SR No derived name.")
                    except Exception as e: # This block might be less critical now, but keep it for safety if there are other unforeseen errors
                        print(f"update_notification_status: Unexpected error determining document title for notification {notification_to_update.sr_no} using extracted name '{extracted_type_name_from_sr_no}': {e}. Using default title.")
                        # The doc_title is already set to the default "UNKNOWN DOCUMENT TYPE" if the map lookup fails silently.
                        # Or, you could use the extracted name directly as a fallback:
                        doc_title = f"{extracted_type_name_from_sr_no.upper()} LETTER" # Use the extracted name as a fallback title
                        # This assumes you have a way to access the raw string value if the ForeignKey lookup fails.
                        # If the field in the database is indeed a VARCHAR holding the name, and the model is incorrectly defined as ForeignKey,
                        # this will still fail. If the model is correctly a ForeignKey but the DB column has invalid UUIDs, this handles the error.
                        # A more robust approach might involve fetching the raw column value directly using raw SQL if the ORM fails.
                        # For now, let's use the default title.
                        # You could also attempt to get the raw ID field name (e.g., 'msc_type_id') and use that as the 'name' if it's actually the string.
                        # raw_id_value = getattr(notification_to_update, 'msc_type_id', 'N/A')
                        # doc_title = f"{raw_id_value.upper()} LETTER" # Use the raw ID value if it's the name string
                        # Or just stick with the default:
                        # doc_title = "ERROR FETCHING DOCUMENT TYPE" # Already set as default

                    c.drawCentredString(width / 2, title_y, doc_title)
                    # --- END CRITICAL FIX ---

                    # Ref & Date
                    c.setFont("Helvetica", 10)
                    ref_date_y = title_y - 30
                    c.drawString(margin, ref_date_y, f"Serial_no. : {notification_to_update.sr_no}")
                    c.drawRightString(width - margin, ref_date_y,
                                    f"Date: {notification_to_update.created_at.strftime('%d-%m-%Y') if notification_to_update.created_at else 'N/A'}")

                    # Supersedes Text (optional)
                    if notification_to_update.superseeded_by:
                        supersede_y = ref_date_y + 10
                        c.setFont("Helvetica-Bold", 10)
                        c.setFillColor(red)
                        c.drawRightString(width - margin, supersede_y,
                                        f"This letter Supersedes {notification_to_update.superseeded_by}")
                        c.setFillColor(black)
                        print(f"🖨️ Added 'Supersedes {notification_to_update.superseeded_by}' to cover.")
                    else :
                         print("🖨️ No 'superseeded_by' found on notification object, skipping 'Supersedes' text.")
                    
                    # Subject
                    c.setFont("Helvetica-Bold", 12)
                    subject_y = ref_date_y - 35
                    c.drawString(margin, subject_y, f"SUBJECT: {notification_to_update.title or notification_to_update.sr_no}")

                    # Office Instructions (Main Body Content)
                    print("--- START: Office Instructions Generation (Update/Approval) ---")
                    c.setFont("Helvetica", 11)
                    body_start_y = subject_y - 40
                    y_position = body_start_y

                    body_text = notification_to_update.office_instructions or ""
                    print(f"update_notification_status: Adding body content: {body_text[:50]}...") # Log first 50 chars

                    if body_text:
                        # Prepare the body text for multi-page handling
                        body_lines = _wrap_text_simple(c, body_text, width - 2 * margin, "Helvetica", 11)
                        
                        # Variable to track the last Y position of body text on each page
                        last_body_y_position = y_position

                        for line in body_lines:
                            if y_position > STOP_Y:
                                c.drawString(margin, y_position, line)
                                y_position -= 15  # Move down for the next line
                                last_body_y_position = y_position  # Update the last Y position
                            else:
                                # Not enough space on current page, add footer and start new page
                                _add_footer_to_page_update(c, width, margin, notification_to_update, page_number, last_body_y_position, published_by_id, published_on_datetime)
                                
                                c.showPage()
                                page_number += 1
                                
                                # Reset for the new page - add header again
                                # Use the same header drawing logic as page 1
                                c.setFont("Helvetica-Bold", 12)
                                c.setFillColor(navy)
                                try:
                                    logo_path = os.path.join(settings.BASE_DIR, "static", "ksm-logo.png")
                                    c.drawImage(logo_path, margin, height - margin - 50, width=logo_width, height=logo_height, mask='auto')
                                    company_name_x = margin + logo_width + 8
                                except:
                                    company_name_x = margin
                                c.drawString(company_name_x, height - margin, "KAIZEN SHIP MANAGEMENT CO. LTD")
                                c.setFillColor(black)

                                # Divider
                                divider_y = height - margin - 40
                                c.setStrokeColor(navy)
                                c.line(margin, divider_y, width - margin, divider_y)
                                c.setStrokeColor(black)

                                # Document info
                                c.setFont("Helvetica", 10)
                                c.drawString(margin, divider_y - 20, f"Document: {notification_to_update.sr_no}")
                                c.drawRightString(width - margin, divider_y - 20, f"Page {page_number}")

                                # Divider below document info
                                c.setStrokeColor(navy)
                                c.line(margin, divider_y - 40, width - margin, divider_y - 40)
                                c.setStrokeColor(black)

                                # Subject (only on first page of body content, maybe skip on subsequent pages or add a different header)
                                # For simplicity, let's add a continuation header instead of repeating subject
                                c.setFont("Helvetica-Bold", 12)
                                c.drawString(margin, divider_y - 50, f"Continued from previous page...") # Or just continue content
                                
                                # Reset Y position for content on the new page
                                y_position = divider_y - 70  # Start below the new header/subject area
                                c.setFont("Helvetica", 11)  # Reset font for body text
                                c.drawString(margin, y_position, line) # Add the current line that didn't fit on the previous page
                                y_position -= 15  # Move down for the next line
                                last_body_y_position = y_position  # Update the last Y position

                        # After all body lines are processed, add the final footer for the last page of body content
                        _add_footer_to_page_update(c, width, margin, notification_to_update, page_number, last_body_y_position, published_by_id, published_on_datetime)
                        
                    else:
                         print("--- END: Office Instructions Generation (Update/Approval) ---")
                    # --- END 6. Office Instructions (Multi-Page Support - Updated Logic) ---
                    # Finalize the CANVAS BUFFER for the newly generated pages (cover + body)
                    c.save()
                    cover_buffer.seek(0)

                    # 3. CREATE A NEW PDF WRITER and MERGE the newly generated pages with the original PDF *CONTENT* pages
                    print("update_notification_status: Merging newly generated cover pages with original PDF *content* pages...")
                    merger = PdfWriter()

                    # Add ALL pages from the newly generated cover/body PDF
                    new_cover_reader = PdfReader(cover_buffer)
                    for page in new_cover_reader.pages:
                        merger.add_page(page)

                    # Add ALL *remaining* pages from the original uploaded file
                    # This logic assumes the *original* file content starts from page index 1 of the `original_pdf_reader`
                    # If the `original_pdf_reader` contains only the original uploaded file content (e.g., from `create_notification` where the cover was already added),
                    # then appending its pages starting from index 1 is correct.
                    # If `original_pdf_reader` contained the *entire* previously generated PDF (cover + original content),
                    # then appending pages from index 1 would mean the *old* cover page is removed, and the *new* cover is added via `new_cover_reader`,
                    # followed by the *original* content pages (which might have been page 1, 2, ... of the `original_pdf_reader`).
                    # This logic aims to replace the *initial* cover generated during `create_notification` with the *new* cover generated here.
                    print(f"update_notification_status: Appending original PDF pages starting from index 1 (skipping old cover page if it existed at index 0)...")
                    for i in range(1, len(original_pdf_reader.pages)): # Start from page 1, skipping the first page (old cover)
                        merger.add_page(original_pdf_reader.pages[i])

                    # 4. Save the MERGED PDF (overwrite the original attachment path)
                    output_path = notification_to_update.attachment_path

                    with open(output_path, 'wb') as output_file:
                        merger.write(output_file)

                    print(f"update_notification_status:  Successfully updated PDF cover and preserved original content at {output_path}")

            except FileNotFoundError:
                print(f"update_notification_status: Original PDF not found at {notification_to_update.attachment_path} during update.")
                # Continue with the status update even if the PDF file is missing
            except Exception as pdf_update_error:
                print(f"update_notification_status: 💥 Error updating PDF cover for {notification_sr_no}: {pdf_update_error}")
                import traceback
                traceback.print_exc()
                # Log the error but continue with the status update itself.
                # The notification status is more critical than the PDF cover update.
                print("update_notification_status: ⚠️ PDF cover update failed, but status update will proceed.")
                # You might choose to return an error here if PDF cover update is mandatory for approval.

        # --- END NEW: Update PDF Cover ---

        # === Update Notification Record in Database ===
        print(f"update_notification_status: Attempting database update for notification {notification_sr_no}")
        sql_params = [new_status, comment]
        sql_set_clauses = ["publish_status = %s", "publish_comment = %s"]

        if new_status == 2:
            sql_params.extend([published_by_id, published_on_datetime])
            sql_set_clauses.extend(["published_by = %s", "published_on = %s"])

        # Join the list of SET clauses into a single string separated by commas
        set_clause_string = ", ".join(sql_set_clauses)
        print(f"update_notification_status: Constructed SET clause string: {set_clause_string}")

        # Use parameterized query for all fields being updated
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE msc_data SET {set_clause_string} WHERE sr_no = %s AND is_deleted = 0", # Use sr_no for the WHERE clause, add is_deleted check
                sql_params + [notification_sr_no] # Add the SR No (notification_id from URL) to the end of parameters
            )
            rows_affected = cursor.rowcount

        print(f"   Rows affected by update: {rows_affected}")

        if rows_affected == 0:
            print(f" ❌ Warning: No rows updated. Notification with SR No {notification_sr_no} might not exist or be deleted.")
            return JsonResponse({'error': 'Notification not found or could not be updated.'}, status=404)

        message = f'Notification status updated to {new_status}'
        if comment:
            message += f" with comment: {comment[:50]}{'...' if len(comment) > 50 else ''}" # Truncate for log
        print(f"✅ {message}")
        return JsonResponse({'success': True, 'message': message})

    except json.JSONDecodeError as je:
        print(f"   ❌ JSON Decode Error: {je}")
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except Exception as e:
        print(f"   ❌ Unexpected Error in update_notification_status: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


def _wrap_text_simple(canvas_obj, text, max_width, font_name, font_size):
    """Simple text wrapping function"""
    lines = []
    paragraphs = text.split('\n')
    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if canvas_obj.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    return lines


def _add_footer_to_page_update(canvas_obj, width, margin, notification_obj, page_number, last_body_y, published_by_id, published_on_datetime):
    """
    Add footer to the current page, positioned below the last body text with proper spacing
    """
    # Calculate footer position based on the last body text position
    # Add significant padding (e.g., 40 points) below the last body text to avoid overlap
    footer_y = last_body_y - 40  # Increased from 20 to 40 for better spacing
    
    # If the calculated footer position is too low (close to bottom), adjust it
    min_footer_y = 50  # Minimum Y position for footer (adjust as needed)
    if footer_y < min_footer_y:
        footer_y = min_footer_y
    
    # Draw a horizontal line above the footer for visual separation
    canvas_obj.setStrokeColorRGB(0, 0, 0.5)  # navy
    canvas_obj.line(margin, footer_y + 10, width - margin, footer_y + 10)
    canvas_obj.setStrokeColorRGB(0, 0, 0)  # black
    
    canvas_obj.setFont("Helvetica", 9)
    
    # Get the original creator (from the notification object)
    created_by_part = f"Created By: {notification_obj.created_by}" if notification_obj.created_by else "Created By: Unknown User"
    # Get the new approver (from the function parameters)
    approved_by_part = f"Approved By: {published_by_id}" if published_by_id else "Approved By: Pending"
    # Use the approval timestamp (from the function parameters)
    approved_at_part = f"Approved At: {published_on_datetime.strftime('%d-%m-%Y %H:%M:%S') if published_on_datetime else django_timezone.now().strftime('%d-%m-%Y %H:%M:%S')}"

    # Combine parts for the footer text
    footer_middle_text = f"{created_by_part}, {approved_by_part}"

    # Draw footer text
    canvas_obj.drawString(margin, footer_y, f"Sr. No: {notification_obj.sr_no}")
    canvas_obj.drawCentredString(width / 2, footer_y, footer_middle_text)
    canvas_obj.drawRightString(width - margin, footer_y, approved_at_part)
    
def add_cover_to_pdf(original_pdf_path, output_pdf_path, logo_path, company_name, address):
    # Read original PDF
    reader = PdfReader(original_pdf_path)
    writer = PdfWriter()

    # Fixed positions (same for all pages)
    LOGO_X = 40       # left margin
    LOGO_Y = 850      # distance from bottom (adjust as needed)
    LOGO_WIDTH = 80
    LOGO_HEIGHT = 80

    COMPANY_X = 140   # text right to logo
    COMPANY_Y = 790

    ADDRESS_X = 140
    ADDRESS_Y = 770

    # Loop through all pages and add header
    for page in reader.pages:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Draw logo
        try:
            logo = ImageReader(logo_path)
            can.drawImage(logo, LOGO_X, LOGO_Y, width=LOGO_WIDTH, height=LOGO_HEIGHT, mask='auto')
        except Exception as e:
            print("Logo drawing error:", e)

        # Header text
        can.setFont("Helvetica-Bold", 14)
        can.drawString(COMPANY_X, COMPANY_Y, company_name)

        can.setFont("Helvetica", 10)
        can.drawString(ADDRESS_X, ADDRESS_Y, address)

        can.save()
        packet.seek(0)

        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        # Merge overlay with the actual PDF page
        page.merge_page(overlay_page)
        writer.add_page(page)

    # Save the final PDF
    with open(output_pdf_path, "wb") as f:
        writer.write(f)

    return True


def draw_header(c, width, height, margin, logo_path, logo_w=40, logo_h=40, font_size=12):
    from reportlab.lib.colors import navy, black

    c.setFont("Helvetica-Bold", font_size)
    c.setFillColor(navy)

    text_height = font_size  # because font size ≈ text height in ReportLab
    text_baseline_y = height - margin
    text_center_y = text_baseline_y - (text_height / 2)

    # Option A: Logo vertically centered with text baseline
    logo_y = text_center_y - (logo_h / 2)

    # Draw logo
    try:
        c.drawImage(logo_path, margin, logo_y, width=logo_w, height=logo_h, mask='auto')
        company_x = margin + logo_w + 8
    except:
        company_x = margin

    # Draw company name
    c.drawString(company_x, text_baseline_y, "KAIZEN SHIP MANAGEMENT CO. LTD")

    # Divider
    divider_y = text_baseline_y - 40
    c.setStrokeColor(navy)
    c.line(margin, divider_y, width - margin, divider_y)

    # Reset
    c.setStrokeColor(black)
    c.setFillColor(black)
    c.setFont("Helvetica", 10)

    return divider_y



@api_view(['GET'])
@permission_classes([AllowAny])
def get_document_types(request):
    types = list( MscType.objects.values_list('id','name'))
    return JsonResponse(types, safe=False)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_departments(request):
    departments = list(Department.objects.values_list('id','department_name'))
    return JsonResponse(departments, safe=False)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_priorities(request):
    priorities = list(MscPriority.objects.values_list('id','name'))
    return JsonResponse(priorities, safe=False)

def get_sub_categories(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET allowed'}, status=405)
    
    sub_cats = MscSubCat.objects.filter(
        is_active=True,
        is_deleted=False
    ).values('id', 'name')
    
    return JsonResponse(list(sub_cats), safe=False)



@api_view(['GET'])
@permission_classes([AllowAny])
def get_second_sub_categories(request):
    # Get all second sub-categories with name and department_id
    second_sub_cats = list(Msc2ndSubCat.objects.values('id','name', 'department_id'))
    return JsonResponse(second_sub_cats, safe=False)




logger = logging.getLogger(__name__)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_master_roles(request):
    """
    Fetches all records from the 'master_role' table.
    Returns id, role_name, is_active, and is_deleted fields.
    """
    print("=== get_master_roles: Starting function ===")

    if request.method != 'GET':
        print(f"get_master_roles: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    try:
        print("get_master_roles: Fetching all MasterRole records from database...")
        # Fetch all MasterRole objects from the database
        roles = MasterRole.objects.all()

        # Prepare the response data list
        response_data = []
        for role in roles:
            role_dict = {
                'id': str(role.id), # Convert UUID to string for JSON serialization
                'role_name': role.role_name, # Get the role name string
                'is_active': role.is_active, # Get the active status (boolean)
                'is_deleted': role.is_deleted # Get the deleted status (boolean)
            }
            response_data.append(role_dict)
            print(f"get_master_roles: Processed role {role.role_name} (ID: {role.id}, Active: {role.is_active}, Deleted: {role.is_deleted})")

        print(f"get_master_roles: Returning {len(response_data)} roles.")
        return JsonResponse({'success': True, 'data': response_data}, status=200)

    except Exception as e:
        print(f"get_master_roles: Error occurred - {type(e).__name__}: {str(e)}")
        logger.exception(f"get_master_roles: Unhandled exception") # Log the full traceback
        return JsonResponse({'error': 'Internal server error'}, status=500)




logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_mapping_role_users(request):
    """
    Fetches all records from the mapping_role_user table.
    Returns id, user id, role id, is_active, is_deleted.
    """
    print("=== get_mapping_role_users: Starting function ===")
    try:
        # Get all records from the mapping_role_user table
        mapping_records = MappingRoleUser.objects.all()

        # Prepare the response data
        response_data = []
        for record in mapping_records:
            response_data.append({
                'id': str(record.id), # Convert UUID to string for JSON serialization
                'userid': record.userid, # Get the user ID string
                'role_id': str(record.role_id) if record.role_id else None, # Convert UUID to string for JSON serialization, handle NULL
                'is_active': record.is_active,
                'is_deleted': record.is_deleted
            })

        print(f"get_mapping_role_users: Fetched {len(response_data)} records.")
        return JsonResponse({'success': True, 'data': response_data}, status=200)

    except Exception as e:
        print(f"❌ Error in get_mapping_role_users: {str(e)}")
        logger.exception(f"get_mapping_role_users: Unhandled exception") # Log the full traceback
        return JsonResponse({'error': 'Internal server error'}, status=500)



logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_users(request):
    """
    Fetches all records from the users table.
    Returns employee_id, employee_name, display_name, username, password, is_active, is_deleted.
    """
    print("=== get_users: Starting function ===")
    try:
        # Get all records from the users table
        users = User.objects.all()

        # Prepare the response data
        response_data = []
        for user in users:
            user_dict = {
                'employee_id': user.employee_id, # String
                'employee_name': user.employee_name, # String
                'display_name': user.display_name, # String (can be None)
                'username': user.username, # String
                'password': user.password, # String (can be None - Note: This is insecure!)
                'is_active': user.is_active, # Boolean
                'is_deleted': user.is_deleted # Boolean
            }
            response_data.append(user_dict)
            print(f"get_users: Processed user {user.employee_name} (ID: {user.employee_id}, Active: {user.is_active}, Deleted: {user.is_deleted})")

        print(f"get_users: Returning {len(response_data)} users.")
        return JsonResponse({'success': True, 'data': response_data}, status=200)

    except Exception as e:
        print(f"get_users: Error occurred - {type(e).__name__}: {str(e)}")
        logger.exception(f"get_users: Unhandled exception") # Log the full traceback
        return JsonResponse({'error': 'Internal server error'}, status=500)



# PDF GENERATION LOGIC
def create_cover_page(sr_no, title, body):
    """Generate a PDF cover page with sr_no, title, and body"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 100, "Circular / Alert / Work Instruction")

    # SR No
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 140, f"SR. No: {sr_no}")

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 180, f"Title: {title}")

    # Body/Instruction
    c.setFont("Helvetica", 11)
    text = c.beginText(50, height - 220)
    text.setFont("Helvetica", 11)
    for line in body.split('\n'):
        wrapped_lines = []
        while len(line) > 100:  # Wrap long lines
            split_pos = line.rfind(' ', 0, 100)
            if split_pos == -1:
                split_pos = 100
            wrapped_lines.append(line[:split_pos])
            line = line[split_pos:].lstrip()
        wrapped_lines.append(line)
        for wrapped_line in wrapped_lines:
            text.textLine(wrapped_line)
    c.drawText(text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer




@api_view(['GET'])
@permission_classes([AllowAny])
def get_crews_by_department(request):
    """
    Fetches crew members belonging to a specific department.
    Expects 'department' query parameter.
    Returns them as JSON.
    """
    print("=== get_crews_by_department: Starting function ===")

    if request.method != 'GET':
        print(f"get_crews_by_department: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    dept_name = request.GET.get('department')
    if not dept_name:
        print("get_crews_by_department: Missing 'department' query parameter")
        return JsonResponse({'error': 'Department name is required'}, status=400)

    print(f"get_crews_by_department: Fetching crews for department: {dept_name}")

    try:
        # --- Map department names to UUIDs (as stored in HRM501.department_name) ---
        DEPARTMENT_NAME_TO_UUID = {
            'Deck': '8949308c-aa8a-ee11-987c-7413ea3d6a70',
            'Engine': '8a49308c-aa8a-ee11-987c-7413ea3d6a70'
        }

        dept_uuid = DEPARTMENT_NAME_TO_UUID.get(dept_name)
        if not dept_uuid:
            print(f"get_crews_by_department: Invalid department name: {dept_name}")
            return JsonResponse({'error': f'Invalid department name: {dept_name}'}, status=400)

        print(f"get_crews_by_department: Looking up crews for department '{dept_name}' (UUID: {dept_uuid})")

        # --- NEW LOGIC: Join HRM501 and FinalCrewList ---
        # 1. Find HRM501 records for the department
        hrm_records = HRM501.objects.filter(department_name=dept_uuid)
        hrm_ids = [record.id for record in hrm_records] # Get the list of HRM501.id strings
        print(f"get_crews_by_department: Found {len(hrm_ids)} HRM501 records for department '{dept_name}'")

        if not hrm_ids:
            print(f"get_crews_by_department: No HRM501 records found for department '{dept_name}', returning empty list.")
            return JsonResponse([], safe=False)

        # 2. Find FinalCrewList records linked to those HRM IDs
        crews = FinalCrewList.objects.filter(Crew_ref_id__in=hrm_ids)
        print(f"get_crews_by_department: Found {crews.count()} FinalCrewList records for department '{dept_name}'")

        # --- Format response ---
        result = []
        for crew in crews:
            result.append({
                'CrewID': crew.CrewID, # Use the CrewID field from FinalCrewList
                'Crew_ref_id': crew.Crew_ref_id, # The HRM501.id string this crew links to
                'name': crew.CrewID, # Or use a name field if available in FinalCrewList
                'employee_id': crew.CrewID, # Or use an employee_id field if available
                'department_name': dept_name,
                # Add other fields from FinalCrewList if needed
            })

        print(f"get_crews_by_department: Returning {len(result)} crews for department '{dept_name}'")
        return JsonResponse(result, safe=False)
        # --- End Format response ---

    except Exception as e:
        print(f"get_crews_by_department: Error occurred - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)




@api_view(['GET'])
@permission_classes([AllowAny])
def get_crews_by_department_and_vessel(request):
    """
    Fetches ALL crew members belonging to a specific department (based on notification.dept),
    regardless of which vessel they are currently on.
    Joins HRM501 and FinalCrewList.
    Expects 'department' query parameter (e.g., 'Deck' or 'Engine').
    Assumes HRM501.department_name links to Department.id.
    Returns the list sorted by rank_name from HRM501.
    """
    print("=== get_crews_by_department_and_vessel: Starting function (fetching all crews for department, sorted by rank) ===")

    if request.method != 'GET':
        print(f"get_crews_by_department_and_vessel: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    # Get department from query parameters (this should now be the department NAME like 'Deck' or 'Engine')
    dept_name = request.GET.get('department')

    if not dept_name:
        print(f"get_crews_by_department_and_vessel: Missing required query parameter - department")
        return JsonResponse({'error': 'Department name is required'}, status=400)

    print(f"get_crews_by_department_and_vessel: Looking up crews for department '{dept_name}'")

    try:
        # --- Map department names to UUIDs (as stored in HRM501.department_name) ---
        DEPARTMENT_NAME_TO_UUID = {
            'Deck': '8949308c-aa8a-ee11-987c-7413ea3d6a70',
            'Engine': '8a49308c-aa8a-ee11-987c-7413ea3d6a70'
        }

        dept_uuid = DEPARTMENT_NAME_TO_UUID.get(dept_name)
        if not dept_uuid:
            print(f"get_crews_by_department_and_vessel: Invalid department name: {dept_name}")
            return JsonResponse({'error': f'Invalid department name: {dept_name}'}, status=400)

        print(f"get_crews_by_department_and_vessel: Mapped department '{dept_name}' to UUID: {dept_uuid}")

        # --- NEW LOGIC: Join HRM501 and FinalCrewList (for all vessels in department) ---
        # 1. Find HRM501 records for the department (including user_id and rank_name)
        print("get_crews_by_department_and_vessel: Fetching HRM501 records for department...")
        hrm_records_for_dept = HRM501.objects.filter(department_name=dept_uuid)
        hrm_ids_for_dept = [record.id for record in hrm_records_for_dept] # Get the list of HRM501.id strings (UUIDs stored as strings)
        print(f"get_crews_by_department_and_vessel: Found {len(hrm_ids_for_dept)} HRM501 records for department '{dept_name}'.")

        if not hrm_ids_for_dept:
            print(f"get_crews_by_department_and_vessel: No HRM501 records found for department '{dept_name}', returning empty list.")
            return JsonResponse([], safe=False)

        # 2. Find ALL FinalCrewList records linked to those HRM IDs (regardless of vessel)
        print("get_crews_by_department_and_vessel: Fetching FinalCrewList records linked to HRM IDs...")
        final_crew_list_for_dept = FinalCrewList.objects.filter(Crew_ref_id__in=hrm_ids_for_dept)
        print(f"get_crews_by_department_and_vessel: Found {final_crew_list_for_dept.count()} FinalCrewList records linked to department '{dept_name}'.")

        if not final_crew_list_for_dept.exists():
            print(f"get_crews_by_department_and_vessel: No FinalCrewList records found linked to HRM501 records for department '{dept_name}', returning empty list.")
            return JsonResponse([], safe=False)

        # 3. Get the HRM501 details for the crews found in FinalCrewList to get their rank_name
        print("get_crews_by_department_and_vessel: Fetching HRM501 details for crews to get rank_name...")
        # Use select_related for efficiency if HRM501 is linked via ForeignKey (unlikely here, as FinalCrewList links via Crew_ref_id string)
        # Use prefetch_related if HRM501 has a reverse FK from FinalCrewList (also unlikely based on field names)
        # Since FinalCrewList.Crew_ref_id seems to be a string matching HRM501.id,
        # we'll fetch the HRM records separately based on the Crew_ref_id values from FinalCrewList.
        crew_ref_ids_from_final = final_crew_list_for_dept.values_list('Crew_ref_id', flat=True).distinct()
        hrm_records_for_crews = HRM501.objects.filter(id__in=crew_ref_ids_from_final)

        # --- NEW: Sort the HRM records by rank_name ---
        # Sort the queryset using the rank_name field from HRM501
        # Use the database's native sorting capability for efficiency
        sorted_hrm_records = hrm_records_for_crews.order_by('rank_name') # Sort by rank_name ascending
        # If you want descending order, use: order_by('-rank_name')
        print(f"get_crews_by_department_and_vessel: Sorted HRM records by rank_name.")
        # --- END NEW ---

        print(f"get_crews_by_department_and_vessel: Found {sorted_hrm_records.count()} HRM501 records matching crews in department '{dept_name}', sorted by rank.")

        # --- Format response (using HRM501 data + FinalCrewList CrewID) ---
        result = []
        for hrm_record in sorted_hrm_records: # Iterate through the SORTED HRM records
            # Find the corresponding FinalCrewList record to get the CrewID string
            # There might be multiple FinalCrewList records per HRM501.id if a crew member has multiple entries
            # We'll pick the first one found for this example, or you might want to return all related ones
            final_crew_record = final_crew_list_for_dept.filter(Crew_ref_id=hrm_record.id).first() # Get first related record

            crew_data = {
                'id': str(hrm_record.id), # HRM501 database ID (UUID as string)
                'user_id': hrm_record.user_id, # The user ID from HRM501
                'rank_name': hrm_record.rank_name, # The rank name from HRM501 (used for sorting)
                'CrewID': final_crew_record.CrewID if final_crew_record else 'Unknown', # The CrewID string from FinalCrewList
                'name': hrm_record.user_id, # Or use a name field if available in HRM501 or FinalCrewList
                'employee_id': hrm_record.user_id, # Or use an employee_id field if available
                'department_name': dept_name,
                # Note: vessel_id is not included here as we are fetching ALL crews for the department, not specific to one vessel
            }
            result.append(crew_data)

        print(f"get_crews_by_department_and_vessel: Returning {len(result)} crews for department '{dept_name}', sorted by rank.")
        return JsonResponse(result, safe=False)
        # --- END Format response ---

    except Exception as e:
        print(f"get_crews_by_department_and_vessel: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc() # Print the full traceback for debugging
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_single_notification(request, notification_id):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET allowed'}, status=405)
    
    try:
        # Use .get() to fetch a single object
        notification = MscData.objects.get(id=notification_id)
        
        # Serialize the object
        notification_data = {
            'id': str(notification.id),
            'sr_no': notification.sr_no,
            'msc_type': notification.msc_type,
            'dept': notification.dept,
            'category': notification.category,
            'sub_category': notification.sub_category,
            'second_sub_category': notification.second_sub_category,
            'office_instructions': notification.office_instructions,
            'hashtags': notification.hashtags,
            'title': notification.title, # If you have a title field
            'priority': notification.priority,
            'publish_status': notification.publish_status,
            'created_by': notification.created_by,
            'created_at': notification.created_at.isoformat() if notification.created_at else None,
            'publish_comment': notification.publish_comment,
            'attachment_url': f"{settings.MEDIA_URL}circular/attachments/{notification.attachment_name}" if notification.attachment_name else None,
            # Add other fields as needed
        }
        
        return JsonResponse(notification_data)
        
    except MscData.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)
    except Exception as e:
        print(f"Error fetching notification {notification_id}:", str(e))
        return JsonResponse({'error': 'Internal server error'}, status=500)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def get_notifications_draft(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET allowed'}, status=405)
    
    # Get optional query parameters for sorting
    sort_by_param = request.GET.get('sort_by', 'created_at')
    sort_order_param = request.GET.get('sort_order', 'desc').lower()
    
    # Whitelist allowed sort columns to prevent SQL injection
    allowed_sort_columns = [
        'id', 'sr_no', 'msc_type', 'dept', 'category', 'created_at', 
        'publish_status', 'created_by', 'priority', 'published_by', 'published_at'
    ]
    
    # Sanitize sort parameters
    sort_by_db = sort_by_param if sort_by_param in allowed_sort_columns else 'created_at'
    sort_order_db = 'ASC' if sort_order_param == 'asc' else 'DESC'
    
    # Base queryset - only fetch records with publish_status 0
    notifications_queryset = MscData.objects.filter(publish_status=0)
    
    # Apply ordering using Django ORM
    orm_ordering = f"-{sort_by_db}" if sort_order_db == 'DESC' else sort_by_db
    notifications_queryset = notifications_queryset.order_by(orm_ordering)
    
    # Use .values() on the filtered and ordered queryset
    notifications = notifications_queryset.values(
        'id', 'sr_no', 'msc_type', 'dept', 'category',
        'sub_category', 'second_sub_category', 'office_instructions',
        'hashtags', 'created_at',  'publish_status', 'priority',
        'attachment_path', 'attachment_name', 'created_by', 'publish_comment',
        'published_by', 'published_on' 
    )

    result = []
    for n in notifications:
        n_dict = dict(n)
        
        # Generate full URL from attachment_name
        if n_dict.get('attachment_name'):
            n_dict['attachment_url'] = f"{settings.MEDIA_URL}circular/attachments/{n_dict['attachment_name']}"
        else:
            n_dict['attachment_url'] = None
            
        result.append(n_dict)
    
    return JsonResponse(result, safe=False)



@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_drafts(request):
    print("=== get_user_drafts: Starting function ===")
    if request.method != 'GET':
        print(f"get_user_drafts: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)
    
    created_by_id = request.GET.get('created_by')
    print(f"get_user_drafts: received created_by_id = {created_by_id}")
    
    if not created_by_id:
        print("get_user_drafts: No created_by parameter provided")
        return JsonResponse({'error': 'created_by parameter is required'}, status=400)

    try:
        print(f"get_user_drafts: Filtering for user {created_by_id}")
        # Filter for drafts (publish_status = 0) that are not deleted
        notifications_queryset = MscData.objects.filter(
            created_by=created_by_id,
            publish_status=0,
            is_deleted=False  # Only show non-deleted drafts
        ).order_by('-created_at')
        
        print(f"get_user_drafts: Found {notifications_queryset.count()} draft notifications")

        notifications = notifications_queryset.values(
            'id', 'sr_no', 'msc_type', 'dept', 'category',
            'sub_category', 'second_sub_category', 'office_instructions',
            'hashtags', 'created_at','publish_status', 'priority',
            'attachment_path', 'attachment_name', 'created_by', 'published_by', 'published_on', 'publish_comment'
        )

        result = []
        for n in notifications:
            n_dict = dict(n)
            print(f"Processing notification ID: {n_dict['id']}, Attachment: {n_dict.get('attachment_name')}")
            
            if n_dict.get('attachment_name'):
                n_dict['attachment_url'] = f"{settings.MEDIA_URL}circular/attachments/{n_dict['attachment_name']}"
                print(f"  - Generated attachment URL: {n_dict['attachment_url']}")
            else:
                n_dict['attachment_url'] = None
                print(f"  - No attachment for ID: {n_dict['id']}")
                
            result.append(n_dict)
        
        print(f"get_user_drafts: Returning {len(result)} draft notifications")
        return JsonResponse(result, safe=False)

    except Exception as e:
        print(f"get_user_drafts: Error occurred - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_draft_by_sr_no(request, sr_no):
    """Fetch a specific draft by SR No for editing"""
    print(f"=== get_draft_by_sr_no: Starting function for sr_no = {sr_no} ===")
    if request.method != 'GET':
        print(f"get_draft_by_sr_no: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)
    
    try:
        print(f"get_draft_by_sr_no: Looking for draft with SR No {sr_no}")
        draft = MscData.objects.get(
            sr_no=sr_no,
            publish_status=0,  # Only drafts
            is_deleted=False   # Only non-deleted
        )
        
        print(f"get_draft_by_sr_no: Found draft with SR No {draft.sr_no}, created_by: {draft.created_by}")
        
        draft_data = {
            'id': str(draft.id),  # Convert UUID back to string for JSON serialization
            'sr_no': draft.sr_no,
            'msc_type': str(draft.msc_type_id) if draft.msc_type_id else None, # ✅ Access the raw UUID string
            'dept': str(draft.dept) if draft.dept else None, # ✅ Access the raw UUID string
            'category': draft.category,
            'sub_category': str(draft.sub_category_id) if draft.sub_category_id else None, # ✅ Access the raw UUID string
            'second_sub_category': str(draft.second_sub_category_id) if draft.second_sub_category_id else None, # ✅ Access the raw UUID string
            'office_instructions': draft.office_instructions,
            'hashtags': draft.hashtags,
            'priority': str(draft.priority_id) if draft.priority_id else None, # ✅ Access the raw UUID string
            'attachment_name': draft.attachment_name,
            'attachment_path': draft.attachment_path,
            'publish_comment': draft.publish_comment,
            'created_by': draft.created_by,
        }
        
        if draft.attachment_name:
            draft_data['attachment_url'] = f"{settings.MEDIA_URL}circular/attachments/{draft.attachment_name}"
            print(f"get_draft_by_sr_no: Generated attachment URL: {draft_data['attachment_url']}")
        else:
            draft_data['attachment_url'] = None
            print(f"get_draft_by_sr_no: No attachment for draft SR No {draft.sr_no}")
            
        print(f"get_draft_by_sr_no: Returning draft data for SR No {draft.sr_no}")
        return JsonResponse(draft_data, safe=False)
        
    except MscData.DoesNotExist:
        print(f"get_draft_by_sr_no: Draft with SR No {sr_no} not found")
        return JsonResponse({'error': 'Draft not found'}, status=404)
    except Exception as e:
        print(f"get_draft_by_sr_no: Error occurred - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)

@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_draft_by_sr_no(request, sr_no):
    """Soft delete a draft by setting is_deleted to True using SR No"""
    print(f"=== delete_draft_by_sr_no: Starting function for sr_no = {sr_no} ===")
    
    if request.method != 'POST':
        print(f"delete_draft_by_sr_no: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)
    
    try:
        print(f"delete_draft_by_sr_no: Looking for draft with SR No {sr_no} to soft-delete")
        
        # CRITICAL: Query by sr_no field, NOT by id field
        # Use update() on the QuerySet to avoid loading the object and calling save()
        updated_count = MscData.objects.filter(
            sr_no=sr_no,           # Use sr_no, not id
            publish_status=0,      # Only drafts
            is_deleted=False       # Only non-deleted
        ).update(is_deleted=True) # Perform the update directly in the DB
        
        if updated_count > 0:
            print(f"delete_draft_by_sr_no: Successfully soft-deleted 1 draft with SR No {sr_no}")
            return JsonResponse({'success': True, 'message': 'Draft deleted successfully'})
        else:
            # If no rows were updated, it means the draft was not found with the given criteria
            print(f"delete_draft_by_sr_no: Draft with SR No {sr_no} not found or already deleted for status=pending, is_deleted=False")
            return JsonResponse({'error': 'Draft not found'}, status=404)
        
    except Exception as e:
        print(f"delete_draft_by_sr_no: Error occurred during deletion - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)

@api_view(['PUT'])
@permission_classes([AllowAny])
def update_draft_by_sr_no(request, sr_no):
    """Update an existing draft by its SR No."""
    print(f"=== update_draft_by_sr_no: Starting function for sr_no = {sr_no} ===")
    
    if request.method != 'POST': # Use POST for updates
        print(f"update_draft_by_sr_no: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # Find the existing draft record using sr_no
        print(f"update_draft_by_sr_no: Looking for draft with SR No {sr_no} to update")
        draft = MscData.objects.get(
            sr_no=sr_no,
            publish_status=0,  # Only update drafts (status 0)
            is_deleted=False   # Only update non-deleted drafts
        )
        
        print(f"update_draft_by_sr_no: Found draft ID {draft.id} (SR No: {draft.sr_no})")

        # Get form data from the request
        # You'll need to handle both regular form data and files
        title = request.POST.get('title', draft.title) # Use existing value if not provided
        body = request.POST.get('body', draft.office_instructions) # Map body to office_instructions
        hashtags = request.POST.get('hashtags', draft.hashtags)
        priority = request.POST.get('priority', draft.priority)
        msc_type = request.POST.get('type', draft.msc_type)
        dept = request.POST.get('department', draft.dept)
        category = request.POST.get('category', draft.category)
        sub_category_str = request.POST.get('sub_cat', draft.sub_category)
        second_sub_category_str = request.POST.get('second_sub_cat', draft.second_sub_category)
        
        # Update the draft object with new data
        draft.title = title
        draft.office_instructions = body # Map body to office_instructions
        draft.hashtags = hashtags
        draft.priority = priority
        draft.msc_type = msc_type
        draft.dept = int(dept) if dept else draft.dept
        draft.category = category
        draft.sub_category = sub_category_str
        draft.second_sub_category = second_sub_category_str
        draft.print_type = int(print_type) if print_type else draft.print_type
        
        # Handle file attachment if provided (optional)
        if 'attachment' in request.FILES:
            draft.attachment = request.FILES['attachment']
            draft.attachment_name = request.FILES['attachment'].name
            # Update attachment_path if needed based on your logic

        # CRITICAL: Change publish_status from 0 (draft) to 1 (pending/approved)
        draft.publish_status = 1
        print(f"update_draft_by_sr_no: Changed publish_status to 1 for draft {draft.sr_no}")

        # Save the updated draft
        draft.save()
        print(f"update_draft_by_sr_no: Successfully updated draft {draft.sr_no}")

        # Return success response
        return JsonResponse({
            'success': True, 
            'message': 'Draft updated and submitted successfully',
            'updated_sr_no': draft.sr_no
        })

    except MscData.DoesNotExist:
        print(f"update_draft_by_sr_no: Draft with SR No {sr_no} not found or not a draft (status != 0)")
        return JsonResponse({'error': 'Draft not found or not editable'}, status=404)
    except Exception as e:
        print(f"update_draft_by_sr_no: Error occurred during update - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['PUT'])
@permission_classes([AllowAny])
def update_draft_by_id(request, draft_id):
    """
    Updates an existing draft record identified by its database ID.
    Changes publish_status from 0 to 1 and updates other fields if provided.
    Expects form data (for file uploads).
    """
    print(f"=== update_draft_by_id: Starting for draft_id = {draft_id} ===")

    if request.method != 'POST':
        print(f"update_draft_by_id: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # Find the specific record by its database ID
        print(f"update_draft_by_id: Looking for draft with database ID {draft_id}")
        draft_record = MscData.objects.get(id=draft_id)

        print(f"update_draft_by_id: Found draft SR No {draft_record.sr_no}, current status: {draft_record.publish_status}")

        # Only allow updating drafts (status 0)
        if draft_record.publish_status != 0:
            print(f"update_draft_by_id: Record {draft_record.sr_no} is not a draft (status {draft_record.publish_status}), cannot update via this method.")
            return JsonResponse({'error': 'Only draft records (status 0) can be updated via this method.'}, status=400)

        # Get updated data from the form
        title = request.POST.get('title', draft_record.title)
        body = request.POST.get('body', draft_record.office_instructions) # Map body to office_instructions
        hashtags = request.POST.get('hashtags', draft_record.hashtags)
        msc_type = request.POST.get('type', draft_record.msc_type)
        dept_str = request.POST.get('department', draft_record.dept)
        category = request.POST.get('category', draft_record.category)
        priority = request.POST.get('priority', draft_record.priority)
        # created_by = request.POST.get('created_by', draft_record.created_by) # Usually don't change creator
        sub_cat_list = request.POST.getlist('sub_cat')
        second_sub_cat_list = request.POST.getlist('second_sub_cat')

        # Update the record object with new data
        draft_record.title = title
        draft_record.office_instructions = body # Map body to office_instructions
        draft_record.hashtags = hashtags
        draft_record.msc_type = msc_type
        try:
            draft_record.dept = int(dept_str) if dept_str else draft_record.dept
        except (ValueError, TypeError):
            print(f"update_draft_by_id: Warning - could not convert dept '{dept_str}' to int, keeping original value {draft_record.dept}")
        draft_record.category = category
        draft_record.priority = priority
        try:
            draft_record.print_type = int(print_type_str) if print_type_str else draft_record.print_type
        except (ValueError, TypeError):
            print(f"update_draft_by_id: Warning - could not convert print_type '{print_type_str}' to int, keeping original value {draft_record.print_type}")

        if sub_cat_list:
            draft_record.sub_category = ','.join(sub_cat_list) if sub_cat_list else None
        if second_sub_cat_list:
            draft_record.second_sub_category = ','.join(second_sub_cat_list) if second_sub_cat_list else None

        # CRITICAL: Change publish_status from 0 (draft) to 1 (pending/approved)
        draft_record.publish_status = 1
        print(f"update_draft_by_id: Changed publish_status to 1 for draft {draft_record.sr_no}")

        # Handle file attachment if provided (optional during update)
        if 'attachment' in request.FILES:
            draft_record.attachment = request.FILES['attachment']
            draft_record.attachment_name = request.FILES['attachment'].name
            # Update attachment_path if needed based on your logic

        # Save the updated record to the database
        draft_record.save()
        print(f"update_draft_by_id: Successfully updated draft record ID {draft_record.id} (SR No: {draft_record.sr_no})")

        # Return success response
        return JsonResponse({
            'success': True,
            'message': 'Draft record updated and submitted successfully',
            'updated_sr_no': draft_record.sr_no
        })

    except MscData.DoesNotExist:
        print(f"update_draft_by_id: Draft with ID {draft_id} not found")
        return JsonResponse({'error': 'Draft record not found'}, status=404)
    except Exception as e:
        print(f"update_draft_by_id: Error occurred during update - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)



@api_view(['GET'])
@permission_classes([AllowAny])
def get_approved_notifications(request):
    """
    Fetches all approved notifications (publish_status = 2) that are not deleted (is_deleted = False).
    Includes attachment URL generation.
    """
    try:
        print("get_approved_notifications: Fetching approved notifications (publish_status=2, is_deleted=False)...")

        # --- Use Django ORM for consistency ---
        # Filter for approved notifications (status 2) AND not deleted (is_deleted=False)
        notifications_queryset = MscData.objects.filter(
            publish_status=2,
            is_deleted=False # Add the is_deleted filter
        ).order_by('-created_at') # Order by newest first

        # Use .values() to get specific fields, including attachment_name
        notifications = notifications_queryset.values(
            'id', 'sr_no', 'msc_type', 'dept', 'category',
            'sub_category', 'second_sub_category', 'office_instructions',
            'hashtags', 'created_at', 'publish_status', 'priority',
            'attachment_path', 'attachment_name', 'created_by', 'published_by', 'published_on', 'publish_comment','is_superseeded'
        )
        # --- End ORM usage ---

        result = []
        for n in notifications:
            n_dict = dict(n)

            # --- Generate full URL from attachment_name (like get_notifications) ---
            if n_dict.get('attachment_name'):
                # Use the same logic as get_notifications
                n_dict['attachment_url'] = f"{settings.MEDIA_URL}circular/attachments/{n_dict['attachment_name']}"
            else:
                n_dict['attachment_url'] = None
            # --- END CORRECTED ---

            result.append(n_dict)

        print(f"get_approved_notifications: Returning {len(result)} approved and non-deleted notifications")
        return JsonResponse(result, safe=False)

    except Exception as e:
        print(f"Error in get_approved_notifications: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)




@api_view(['POST'])
@permission_classes([AllowAny])
def delete_notification(request, sr_no):
    """
    Marks a notification as deleted by setting is_deleted=True.
    Uses a direct database update query based on sr_no to avoid ORM instance issues.
    Expects the SR No in the URL.
    """
    print(f"=== delete_notification: Starting for SR No {sr_no} ===")
    try:
        # --- NEW APPROACH: Direct Database Update ---
        # Use filter to find the record(s) and update() to change fields directly in the DB.
        # This bypasses loading the potentially problematic object instance into Python.
        # filter(sr_no=sr_no) targets the correct row(s).
        # update(is_deleted=True) sets the field directly in the database.
        # It returns the number of rows affected.
        
        print(f"delete_notification: Attempting direct database update for sr_no='{sr_no}'")
        rows_affected = MscData.objects.filter(sr_no=sr_no).update(is_deleted=True)
        print(f"delete_notification: Database update completed. Rows affected: {rows_affected}")

        # --- Check the result ---
        if rows_affected > 0:
            # Success: At least one row was updated.
            print(f"delete_notification: Successfully marked notification with sr_no='{sr_no}' as deleted.")
            return JsonResponse({
                'success': True, 
                'message': f'Notification with SR No {sr_no} deleted successfully.',
                'rows_affected': rows_affected # Optional: inform frontend how many were changed
            })
        else:
            # Failure: No rows matched the sr_no filter, meaning the record wasn't found.
            print(f"delete_notification: Notification with sr_no='{sr_no}' not found in database.")
            return JsonResponse({
                'error': f'Notification with SR No {sr_no} not found.'
            }, status=404) # 404 Not Found is the appropriate HTTP status

    except Exception as e:
        # Catch any unexpected errors during the database operation
        print(f"delete_notification: UNEXPECTED ERROR during database update - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc() # Print the full traceback for debugging
        # Return a 500 Internal Server Error response
        return JsonResponse({
            'error': f'Internal server error while deleting notification: {str(e)}'
        }, status=500)





@api_view(['POST'])
@permission_classes([AllowAny])
def supersede_notification(request, sr_no):
    """
    Marks a notification as superseded by setting is_superseeded=True.
    Expects the SR No of the notification to be superseded in the URL.
    The SR No of the NEW superseding notification should be sent in the request body.
    The created_by (user ID) of the new notification is stored in superseeded_by.
    """
    print(f"=== supersede_notification: Starting for SR No {sr_no} ===")
    try:
        # --- 1. Get the SR No of the NEW notification from the request body ---
        # This comes from the frontend after creating the new one
        try:
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)
            superseding_sr_no = body_data.get('superseding_sr_no')
            # Also get the created_by (user ID) of the new notification
            created_by_user_id = body_data.get('created_by') # This should be the employee_id
            print(f"supersede_notification: Superseding SR No from request body: {superseding_sr_no}")
            print(f"supersede_notification: Created by User ID: {created_by_user_id}")
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
            print("supersede_notification: Could not get required data from request body.")
            return JsonResponse({'error': 'Invalid request data.'}, status=400)

        # --- 2. Perform a direct database update based on the old SR No ---
        # Use filter(sr_no=sr_no) to target the correct row(s) and update() to change fields directly in the DB.
        # This bypasses loading the potentially corrupted object instance into Python.
        # It returns the number of rows affected.
        
        print(f"supersede_notification: Attempting direct database update for old SR No='{sr_no}'")
        # Update the is_superseeded and superseeded_by fields
        # Set is_superseeded to True and superseeded_by to the USER ID of the person who created the new notification
        update_data = {
            'is_superseeded': True,
            'superseeded_by': created_by_user_id  # Store the USER ID here
        }

        rows_affected = MscData.objects.filter(sr_no=sr_no).update(**update_data)
        print(f"supersede_notification: Database update completed. Rows affected: {rows_affected}")

        # --- Check the result ---
        if rows_affected > 0:
            # Success: At least one row was updated.
            print(f"supersede_notification: Successfully marked notification with sr_no='{sr_no}' as superseded.")
            return JsonResponse({
                'success': True, 
                'message': f'Notification with SR No {sr_no} marked as superseded.',
                'rows_affected': rows_affected,
                'superseding_sr_no': superseding_sr_no, # Optional: inform frontend
                'updated_by_user_id': created_by_user_id # Optional: confirm what was stored
            })
        else:
            # Failure: No rows matched the sr_no filter, meaning the record wasn't found.
            print(f"supersede_notification: Notification with sr_no='{sr_no}' not found in database.")
            return JsonResponse({
                'error': f'Notification with SR No {sr_no} not found.'
            }, status=404) # 404 Not Found is the appropriate HTTP status

    except Exception as e:
        # Catch any unexpected errors during the database operation
        print(f"supersede_notification: UNEXPECTED ERROR during database update - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc() # Print the full traceback for debugging
        # Return a 500 Internal Server Error response
        return JsonResponse({
            'error': f'Internal server error while marking notification as superseded: {str(e)}'
        }, status=500)





@api_view(['GET'])
@permission_classes([AllowAny])
def get_vessels(request):
    """
    Fetches all vessels from the VesselData table.
    Returns them as a JSON array.
    """
    try:
        # Query all VesselData records
        vessels = VesselData.objects.all()

        # Convert to list of dictionaries for JSON serialization
        vessel_list = []
        for vessel in vessels:
            vessel_list.append({
                'id': str(vessel.id), # Convert UUID to string for JSON
                'vesselName': vessel.vesselName,
                'vesselCode': vessel.vesselCode,
                'vesselEmail':vessel.email,
            })

        print(f"get_vessels: Fetched {len(vessel_list)} vessels.")
        return JsonResponse(vessel_list, safe=False) # safe=False because we're returning a list

    except Exception as e:
        print(f"Error in get_vessels: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)
    



@api_view(['GET'])
@permission_classes([AllowAny])
def get_approved_notifications_csv(request):

    print("=== get_approved_notifications_pdf: Starting function ===")

    if request.method != 'GET':
        return HttpResponse('Only GET allowed', status=405)

    # Get filter/sort/search params
    created_by = request.GET.get('created_by')
    department_name_uuid = request.GET.get('department')
    msc_type = request.GET.get('type')
    priority = request.GET.get('priority')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort_by', 'created_at')
    sort_order = request.GET.get('sort_order', 'desc')

    try:
        # Base query
        notifications_queryset = MscData.objects.filter(
            publish_status=2,
            is_deleted=False
        )

        # Apply filters
        if created_by:
            notifications_queryset = notifications_queryset.filter(created_by=created_by)

        if department_name_uuid:
            notifications_queryset = notifications_queryset.filter(dept=department_name_uuid)

        if msc_type:
            notifications_queryset = notifications_queryset.filter(msc_type__name__icontains=msc_type)

        if priority:
            notifications_queryset = notifications_queryset.filter(priority__name__icontains=priority)

        if search_query:
            notifications_queryset = notifications_queryset.filter(
                Q(title__icontains=search_query) |
                Q(sr_no__icontains=search_query) |
                Q(hashtags__icontains=search_query) |
                Q(office_instructions__icontains=search_query) |
                Q(msc_type__name__icontains=search_query) |
                Q(priority__name__icontains=search_query)
            )

        allowed_sort_fields = ['created_at', 'sr_no', 'msc_type', 'priority', 'dept']
        if sort_by not in allowed_sort_fields:
            sort_by = 'created_at'

        order_prefix = '-' if sort_order == 'desc' else ''
        notifications_queryset = notifications_queryset.order_by(order_prefix + sort_by)

        notifications = notifications_queryset.values(
            'id', 'sr_no', 'msc_type', 'category', 'sub_category', 'second_sub_category',
            'title', 'office_instructions', 'hashtags', 'created_at', 'publish_status',
            'priority', 'attachment_path', 'attachment_name', 'created_by',
            'published_by', 'published_on', 'publish_comment'
        )

        # PDF generation setup
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []

        styles = getSampleStyleSheet()

        # -----------------------------------------------
        # UPDATED STYLISH HEADER
        # -----------------------------------------------
        title_style = ParagraphStyle(
            name='KSMTitle',
            fontName='bookos',
            fontSize=22,
            leading=26,
            alignment=1,            # CENTER
            textColor=colors.HexColor("#1F3247"),
            spaceAfter=20,
            spaceBefore=20
        )

        logo_path = os.path.join(settings.BASE_DIR, "static", "ksm-logo.png")
        
        header_data = [
            [
                Image(logo_path, width=1.2*inch, height=1.5*inch),
                Paragraph("KAIZEN SHIP MANAGEMENT", title_style)

            ]
        ]

        header_table = Table(header_data, colWidths=[1.7*inch, 4.8*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))

        story.append(header_table)
        story.append(Spacer(1, 20))

        # -----------------------------------------------
        # NOTE SECTION (FULLY BOLD) — kept as requested
        # -----------------------------------------------
        note_text = None

        if msc_type and priority:
            note_text = f"This is the list of {priority.lower()} {msc_type.lower()} published by KSM."
        elif msc_type:
            note_text = f"This is the list of {msc_type.lower()} published by KSM."
        elif priority:
            note_text = f"This is the list of {priority.lower()} notifications published by KSM."

        if note_text:
            note_para = Paragraph(f"NOTE: {note_text}", styles['Normal'])
            story.append(note_para)
            story.append(Spacer(1, 12))

        # -----------------------------------------------
        # TABLE DATA
        # -----------------------------------------------

        header_style = ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontName='bookos',
        fontSize=10,
        textColor=colors.white   
    )
        table_data = [
    [
        Paragraph('SR No.', header_style),
        Paragraph('Description', header_style),
        Paragraph('Issued on', header_style)
    ]
]

        body_style = ParagraphStyle(
            name='Body',
            parent=styles['Normal'],
            fontName="bookos",
            fontSize=9,
            leading=11
        )

        for n in notifications:
            row = [
                Paragraph(n['sr_no'], body_style),
                Paragraph(n['title'], body_style),
                Paragraph(
                    n['published_on'].strftime('%Y-%m-%d') if n['published_on'] else '',
                    body_style
                )
            ]
            table_data.append(row)

        usable_width = doc.width
        col_widths = [
            0.25 * usable_width,
            0.55 * usable_width,
            0.20 * usable_width
        ]

        table = Table(table_data, colWidths=col_widths)



        # -----------------------------------------------
        # UPDATED STYLISH TABLE THEME
        # -----------------------------------------------
        table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),

        # HEADER
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d2237')),  # navy blue
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),                 # header text white
        ('FONTNAME', (0, 0), (-1, 0), 'bookos'),             # simple bookman

        # BODY
        ('FONTNAME', (0, 1), (-1, -1), 'bookos'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

        story.append(table)

        doc.build(story)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="KSM_Library_Report.pdf"'
        return response

    except Exception as e:
        traceback.print_exc()
        return HttpResponse('Internal server error', status=500)




@api_view(['POST'])
@permission_classes([AllowAny])
def create_delivery_records(request):
    """
    Creates MscNotification records for a specific notification and a list of crew IDs.
    Expects JSON data containing 'notification_sr_no' and 'crew_ids'.
    """
    print("=== create_delivery_records: Starting function ===")
    print(f"create_delivery_records: Request body: {request.body.decode('utf-8', errors='ignore')}")

    if request.method != 'POST':
        print(f"create_delivery_records: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # Get request data (assuming JSON body)
        data = json.loads(request.body)
        notification_sr_no = data.get('notification_sr_no')
        crew_ids = data.get('crew_ids', []) # Expecting a list of crew IDs (e.g., ['KSM0110', 'KSM0111', ...])

        if not notification_sr_no or not crew_ids:
            print(f"create_delivery_records: Missing required data - notification_sr_no: {notification_sr_no}, crew_ids: {crew_ids}")
            return JsonResponse({'error': 'notification_sr_no and crew_ids are required'}, status=400)

        print(f"create_delivery_records: Received request for notification {notification_sr_no} and {len(crew_ids)} crew IDs: {crew_ids}")

        # Verify the notification exists
        try:
            notification = MscData.objects.get(sr_no=notification_sr_no)
            print(f"create_delivery_records: Found notification {notification.sr_no} (ID: {notification.id}) to link delivery records to.")
        except MscData.DoesNotExist:
            print(f"create_delivery_records: Notification with SR No {notification_sr_no} not found.")
            return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)

        # Create MscNotification records for each crew ID
        created_records_count = 0
        for crew_id in crew_ids:
            delivery_record = MscNotification(
                msc_sr_no=notification_sr_no, # Link to the SR No of the approved notification
                crew_id=crew_id,              # Use the specific crew ID
                delivered_at=django_timezone.now() # Set the delivery timestamp
                # seen_at and reminder_sent_at remain NULL initially
            )
            delivery_record.save()
            created_records_count += 1
            print(f"  - Created delivery record for crew {crew_id} linked to notification {notification_sr_no}")

        print(f"create_delivery_records: Successfully created {created_records_count} delivery records for notification {notification_sr_no}")

        return JsonResponse({
            'success': True,
            'message': f'Created {created_records_count} delivery records for notification {notification_sr_no}.',
            'notification_sr_no': notification_sr_no,
            'crew_ids_processed': len(crew_ids)
        })

    except json.JSONDecodeError as je:
        print(f"create_delivery_records: JSON Decode Error: {je}")
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except Exception as e:
        print(f"create_delivery_records: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)




@api_view(['GET'])
@permission_classes([AllowAny])
def get_notification_details_by_sr_no(request, notification_sr_no): #  Changed parameter name to reflect SR No
    """
    Fetches details of a single notification by its Serial Number (SR No).
    Expects the notification SR No (e.g., 'KSM/Alert/Technical/2025-0004') in the URL.
    Used primarily for fetching details (like department) when approving/rejecting based on SR No.
    """
    print(f"=== get_notification_details_by_sr_no: Starting for SR No {notification_sr_no} ===") # ✅ Updated log message

    if request.method != 'GET':
        print(f"get_notification_details_by_sr_no: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    try:
        # No need to convert sr_no to UUID as it's a string
        print(f"get_notification_details_by_sr_no: Attempting to fetch notification by SR No {notification_sr_no}") # ✅ Updated log message

        # Find the notification by its Serial Number (sr_no) field
        # Use .filter().first() to handle potential non-uniqueness gracefully if sr_no is not enforced as unique in DB
        # If sr_no is intended to be unique, .get() is fine.
        # For now, let's use .get() assuming it's unique.
        notification = MscData.objects.get(sr_no=notification_sr_no) # ✅ Query by sr_no instead of id

        print(f"get_notification_details_by_sr_no: Found notification. ID (DB): {notification.id}, SR No: {notification.sr_no}") # ✅ Updated log message

        # Prepare the response data (include fields needed for crew list logic, like 'dept')
        notification_data = {
            'id': str(notification.id), # Keep the database ID for internal use if needed (convert UUID to string)
            'sr_no': notification.sr_no, # ✅ Include the SR No
            'msc_type': notification.msc_type,
            'dept': notification.dept, # This is the crucial field for fetching crews
            'category': notification.category,
            'sub_category': notification.sub_category,
            'second_sub_category': notification.second_sub_category,
            'office_instructions': notification.office_instructions,
            'hashtags': notification.hashtags,
            'created_at': notification.created_at.isoformat() if notification.created_at else None,
            'publish_status': notification.publish_status,
            'priority': notification.priority,
            'created_by': notification.created_by,
            'published_by': notification.published_by,
            'published_on': notification.published_on.isoformat() if notification.published_on else None,
            'is_superseeded': notification.is_superseeded,
            'superseeded_by': notification.superseeded_by,
            'is_active': notification.is_active,
            'is_deleted': notification.is_deleted,
            'attachment_name': notification.attachment_name,
            'attachment_path': notification.attachment_path,
            # Add other fields as needed
        }

        # Add attachment URL if available
        if notification.attachment_name:
            notification_data['attachment_url'] = f"{settings.MEDIA_URL}circular/attachments/{notification.attachment_name}"
        else:
            notification_data['attachment_url'] = None

        print(f"get_notification_details_by_sr_no: Returning notification data for SR No {notification.sr_no}") # ✅ Updated log message
        return JsonResponse(notification_data, safe=False)

    except MscData.DoesNotExist:
        print(f"get_notification_details_by_sr_no: Notification with SR No {notification_sr_no} not found.") # ✅ Updated log message
        return JsonResponse({'error': 'Notification not found.'}, status=404)
    except MscData.MultipleObjectsReturned:
        # This handles the case where sr_no is not unique in the database
        print(f"get_notification_details_by_sr_no: Multiple notifications found with SR No {notification_sr_no}.") # ✅ Updated log message
        return JsonResponse({'error': 'Multiple notifications found with this SR No. Please contact your system administrator.'}, status=500) # 500 might be appropriate, or 400 depending on your workflow
    except Exception as e:
        print(f"get_notification_details_by_sr_no: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}") # ✅ Updated log message
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
    




logger = logging.getLogger(__name__)
@api_view(['POST'])
@permission_classes([AllowAny])
def send_emails_to_vessels(request):
    """
    Fetches vessel details by their IDs, sends an email to each vessel's contact,
    and stores the delivery record in msc_ship_notification table.
    Expects JSON data containing notification SR No and a list of vessel IDs.
    """
    print("=== send_emails_to_vessels: Starting function ===")
    print(f"send_emails_to_vessels: Request body: {request.body.decode('utf-8', errors='ignore')}")

    if request.method != 'POST':
        print(f"send_emails_to_vessels: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        notification_sr_no = data.get('notification_sr_no') # The SR No of the notification to send
        vessel_ids_list = data.get('vessel_ids', []) # A list of vessel UUID strings

        if not notification_sr_no or not vessel_ids_list:
            print(f"send_emails_to_vessels: Missing required data - notification_sr_no: {notification_sr_no}, vessel_ids: {vessel_ids_list}")
            return JsonResponse({'error': 'notification_sr_no and vessel_ids list are required'}, status=400)

        # Fetch the notification details to get its title, and attachment path (for email attachment if needed)
        try:
            notification_details = MscData.objects.get(sr_no=notification_sr_no)
            print(f"send_emails_to_vessels: Found notification {notification_details.sr_no} (ID: {notification_details.id}) to send emails.")
        except MscData.DoesNotExist:
            print(f"send_emails_to_vessels: Notification with SR No {notification_sr_no} not found.")
            return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)

        print(f"send_emails_to_vessels: Processing {len(vessel_ids_list)} vessel IDs for notification {notification_sr_no}")

        # --- NEW: Extract Document Type Name from SR No ---
        # SR No format: KSM/{Type}/{Department}/{Year}-{Serial}
        # Example: KSM/Alert/Technical/2025-0004
        sr_no_parts = notification_sr_no.split('/')
        if len(sr_no_parts) >= 2: # Ensure the format is correct and has at least 'KSM' and 'Type'
            extracted_type_name = sr_no_parts[1] # The second part is the type name
            print(f"send_emails_to_vessels: Extracted document type name '{extracted_type_name}' from SR No '{notification_sr_no}'.")
        else:
            print(f"❌ send_emails_to_vessels: Could not extract document type from SR No '{notification_sr_no}'. Expected format: prefix/type/department/year-serial.")
            extracted_type_name = "Unknown Type" # Fallback if parsing fails
        # --- END NEW ---

        # Iterate through each vessel ID to fetch its email and send the notification
        emails_sent_count = 0
        delivery_records_created_count = 0
        for vessel_id_str in vessel_ids_list:
            try:
                print(f"send_emails_to_vessels: Processing vessel ID: {vessel_id_str}")

                # --- CRITICAL: Convert String ID to UUID Object for Validation, then use RawSQL with CAST for Query ---
                # This ensures the database receives the string correctly as a uniqueidentifier
                try:
                    # Convert the string ID received from the frontend to a Python UUID object
                    # This validates the format and ensures it's a UUID.
                    vessel_uuid_object = uuid.UUID(vessel_id_str)
                    print(f"send_emails_to_vessels: Converted vessel_id_str '{vessel_id_str}' to UUID object: {vessel_uuid_object}")

                    # Convert the UUID object BACK to a string for the ORM query.
                    # This often resolves issues with SQL Server ODBC drivers expecting the string representation.
                    vessel_uuid_string_for_query = str(vessel_uuid_object)
                    print(f"send_emails_to_vessels: Using string '{vessel_uuid_string_for_query}' for database query.")

                except ValueError as ve:
                    print(f"send_emails_to_vessels: Error converting vessel_id_str '{vessel_id_str}' to UUID: {ve}")
                    # Skip this vessel ID if it's invalid
                    continue
                # --- END CRITICAL ---

                # Use RawSQL with CAST to explicitly convert the string ID to uniqueidentifier for the database query
                # This bypasses potential ORM issues with UUID field types in SQL Server
                print(f"send_emails_to_vessels: Attempting to fetch vessel details using RawSQL with CAST for ID: {vessel_uuid_string_for_query}")
                # from django.db.models import Q # Ensure this import is present at the top of the file
                # from django.db.models.expressions import RawSQL # Ensure this import is present at the top of the file

                # Create a Q object using RawSQL to handle the UUID conversion explicitly in SQL
                vessel_query_filter = Q(id=RawSQL("CAST(%s AS UNIQUEIDENTIFIER)", [vessel_uuid_string_for_query]))

                # Use the filter to get the vessel details
                vessel_details = VesselData.objects.filter(vessel_query_filter).first() # Use .first() to handle potential non-uniqueness gracefully

                if not vessel_details:
                    print(f"⚠️ send_emails_to_vessels: Vessel with ID {vessel_uuid_string_for_query} not found in VesselData table. Skipping email and delivery record for this vessel.")
                    continue # Skip to the next vessel ID in the loop

                print(f"send_emails_to_vessels: ✅ Found vessel {vessel_details.vesselName} ({vessel_details.vesselCode}) with email: {vessel_details.email}")

                # --- NEW: Send Email ---
                if vessel_details.email: # Only send if an email address exists
                    # Get notification details for the email content
                    # Use the notification object fetched earlier (notification_details)
                    # Use the extracted_type_name from the SR No
                    notification_type_name = extracted_type_name # Use the name extracted from the SR No

                    # Compose the email
                    subject = f"New {notification_type_name} Notification: {notification_details.sr_no}" 
                    body_text = f"""
Hello,

You have a new {notification_type_name.lower()} notification: 

SR No: {notification_details.sr_no}
Title: {notification_details.title}

Please find the attached document for details.

Best regards,
Kaizen Ship Management
                    """.strip()

                    print(f"send_emails_to_vessels: Preparing to send email to {vessel_details.email} for vessel {vessel_details.vesselName}")

                    # Create email message
                    email_message = EmailMultiAlternatives(
                        subject=subject,
                        body=body_text,
                        # Use the default sender configured in settings
                        from_email=django_settings.DEFAULT_FROM_EMAIL, # This should be 'your_actual_email@gmail.com'
                        to=[vessel_details.email],
                    )

                    # # Attach the PDF file if available
                    # if attachment_path_for_email and os.path.exists(attachment_path_for_email):
                    #     print(f"send_emails_to_vessels: Attaching file {attachment_path_for_email} to email for {vessel_details.email}")
                    #     email_message.attach_file(attachment_path_for_email) # Attach the PDF file
                    # else:
                    #     print(f"⚠️ send_emails_to_vessels: No attachment file found at {attachment_path_for_email} for notification {notification_sr_no_for_email}. Sending email without attachment.")
                    #     # Consider if you want to abort sending the email if no attachment exists.
                    #     # For now, let's proceed with sending the email without the attachment.

                    # Send the email
                    email_message.send() # This line triggers the SMTPSenderRefused error
                    print(f"✅ send_emails_to_vessels: Email sent successfully to {vessel_details.email} for vessel {vessel_details.vesselName} regarding notification {notification_sr_no}")
                    emails_sent_count += 1

                    # --- NEW: Store Notification Delivery Record in msc_ship_notification (using Raw SQL) ---
                    # Create a record in the msc_ship_notification table for this email delivery.
                    # Uses raw SQL to insert the data, bypassing potential ORM issues with UUID foreign keys.

                    # 1. Fetch the VesselData object corresponding to the vessel_id_str
                    # (This part remains the same as the previous correction for fetching vessel details)
                    try:
                        # Use the UUID string to find the VesselData object
                        print(f"send_emails_to_vessels: Fetching VesselData object for ID {vessel_id_str}")
                        # Convert string to UUID object for validation
                        vessel_uuid_object = uuid.UUID(vessel_id_str)
                        print(f"send_emails_to_vessels: Converted vessel_id_str '{vessel_id_str}' to UUID object: {vessel_uuid_object}")

                        # Use RawSQL to explicitly cast the string ID to uniqueidentifier for the database query
                        print(f"send_emails_to_vessels: Attempting to fetch vessel details using RawSQL with CAST for ID: {vessel_uuid_object}")
                        # from django.db.models import Q # Ensure this import is present at the top of the file
                        # from django.db.models.expressions import RawSQL # Ensure this import is present at the top of the file

                        # Create a Q object using RawSQL to handle the UUID conversion explicitly in SQL
                        vessel_query_filter = Q(id=RawSQL("CAST(%s AS UNIQUEIDENTIFIER)", [str(vessel_uuid_object)]))

                        # Use the filter to get the vessel details
                        vessel_obj = VesselData.objects.filter(vessel_query_filter).first() # Use .first() to handle potential non-uniqueness gracefully

                        if not vessel_obj:
                             print(f"⚠️ send_emails_to_vessels: Vessel with ID {vessel_uuid_object} not found in VesselData table. Cannot create delivery record for this vessel.")
                             continue # Skip to the next vessel ID in the loop

                        print(f"send_emails_to_vessels: Found VesselData object: {vessel_obj.vesselName} ({vessel_obj.vesselCode})")

                    except ValueError as ve:
                        print(f"⚠️ send_emails_to_vessels: Invalid UUID format for vessel ID '{vessel_id_str}': {ve}")
                        # Continue to the next vessel ID, don't break the loop for one error
                        continue
                    except Exception as vessel_fetch_error:
                        print(f"⚠️ send_emails_to_vessels: Error fetching VesselData object for ID {vessel_id_str}: {vessel_fetch_error}")
                        import traceback
                        traceback.print_exc()
                        # Continue to the next vessel ID, don't break the loop for one error
                        continue

                    # 2. Create the MscShipNotification record using Raw SQL
                    print(f"send_emails_to_vessels: Creating MscShipNotification record for notification {notification_details.sr_no} and vessel {vessel_obj.id} using raw SQL...")

                    # Import connection for raw SQL execution
                    # from django.db import connection # Ensure this import is present at the top of the file

                    try:
                        with connection.cursor() as cursor:
                            # Prepare the SQL INSERT statement
                            # Use the CORRECT table name 'msc_ship_notification' and column names as defined in your DATABASE schema
                            # Based on your MscShipNotification model:
                            # - msc_sr_no_val maps to db_column 'msc_sr_no_'
                            # - vessel_link (ForeignKey to VesselData) maps to db_column 'vessel_id'
                            # The 'id' field (primary key) of MscShipNotification is auto-generated by the database.
                            sql_insert = """
                                INSERT INTO msc_ship_notification (msc_sr_no_, vessel_id, delivered_at)
                                VALUES (%s, CAST(%s AS UNIQUEIDENTIFIER), %s)
                            """
                            # Prepare the parameters for the INSERT
                            # The 'id' field of MscShipNotification is auto-generated by the database
                            # because it's a UUIDField with default=uuid.uuid4 (if it were defined as such in the model, which it isn't explicitly shown but implied by Django's default for PK)
                            sql_params = [
                                notification_details.sr_no, # Value for msc_sr_no_ column (string)
                                str(vessel_obj.id),         # Value for vessel_id column (UUID string from VesselData, cast explicitly)
                                django_timezone.now()       # Value for delivered_at column (DateTime)
                            ]

                            print(f"send_emails_to_vessels: Executing raw SQL: {sql_insert}")
                            print(f"send_emails_to_vessels: Parameters: {sql_params}")

                            # Execute the raw SQL INSERT
                            cursor.execute(sql_insert, sql_params)

                        print(f"  - ✅ Created delivery record in msc_ship_notification for notification {notification_details.sr_no} and vessel {vessel_obj.vesselName} (DB ID: {vessel_obj.id}) using raw SQL.")
                        delivery_records_created_count += 1 # Increment the counter for successful inserts

                    except Exception as raw_sql_error:
                        print(f"❌ send_emails_to_vessels: Error executing raw SQL INSERT for notification {notification_details.sr_no} and vessel {vessel_obj.id}: {raw_sql_error}")
                        import traceback
                        traceback.print_exc()
                        # Continue to the next vessel ID, don't break the loop for one error
                        # You might want to log this specific failure
                        continue
                    # --- END NEW: Store Notification Delivery Record (using Raw SQL) ---

            except ValueError as ve:
                print(f"⚠️ send_emails_to_vessels: Invalid UUID format for vessel ID '{vessel_id_str}': {ve}")
                # Continue to the next vessel ID, don't break the loop for one error
                continue
            except VesselData.DoesNotExist:
                print(f"⚠️ send_emails_to_vessels: Vessel with ID {vessel_id_str} not found in database during processing loop. This should not happen if the initial fetch was correct.")
                # Continue to the next vessel ID, don't break the loop for one error
                continue
            except Exception as single_vessel_error:
                print(f"⚠️ send_emails_to_vessels: Error processing vessel {vessel_id_str} for email or delivery record: {single_vessel_error}")
                import traceback
                traceback.print_exc()
                # Continue to the next vessel ID, don't break the loop for one error
                continue

        print(f"send_emails_to_vessels: Successfully sent {emails_sent_count} emails and created {delivery_records_created_count} delivery records out of {len(vessel_ids_list)} requested for notification {notification_sr_no}")
        return JsonResponse({
            'success': True,
            'message': f'Emails sent successfully to {emails_sent_count} vessels and {delivery_records_created_count} delivery records created.',
            'emails_sent': emails_sent_count,
            'delivery_records_created': delivery_records_created_count,
            'total_requested': len(vessel_ids_list)
        })

    except json.JSONDecodeError as je:
        print(f"send_emails_to_vessels: JSON Decode Error: {je}")
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except MscData.DoesNotExist:
        print(f"send_emails_to_vessels: Notification with SR No {notification_sr_no} not found for department lookup or update.")
        return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)
    except Exception as e:
        print(f"send_emails_to_vessels: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_master_applied_ranks(request):
    """
    Returns a list of all records from the master_applied_rank table.
    Returns JSON with id, rank_name, and rank_id for each record.
    """
    print("=== get_master_applied_ranks: Starting ===")

    try:
        # Fetch all records from the master_applied_rank table
        # Use .values() to select only the fields we need
        ranks = MasterAppliedRank.objects.values('id', 'rank_name', 'rank_id')

        # Convert the QuerySet to a list of dictionaries
        ranks_list = list(ranks)

        print(f"get_master_applied_ranks: Fetched {len(ranks_list)} records.")
        return JsonResponse({'success': True, 'ranks': ranks_list})

    except Exception as e:
        print(f"get_master_applied_ranks: Error fetching ranks: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)






@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_ranks(request):
    """
    Fetches all ranks from the MasterAppliedRank table.
    Does NOT group them by department as department info is not directly available on this model.
    Returns JSON array of rank objects with id, name, and rank_id.
    """
    print("=== get_all_ranks: Starting function ===")

    if request.method != 'GET':
        print(f"get_all_ranks: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    try:
        print("get_all_ranks: Fetching all ranks from MasterAppliedRank table...")
        ranks_queryset = MasterAppliedRank.objects.all()

        # Prepare response data - NO department info added here
        ranks_data = []
        for rank in ranks_queryset:
            ranks_data.append({
                'id': str(rank.id), # Convert UUID to string for JSON serialization
                'rank_name': rank.rank_name,
                'rank_id': rank.rank_id,
                # 'department': dept_display_name, # This line was causing the error and is removed
            })

        print(f"get_all_ranks: Returning {len(ranks_data)} ranks.")
        return JsonResponse(ranks_data, safe=False)

    except Exception as e:
        print(f"get_all_ranks: Error occurred - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)




@api_view(['POST'])
@permission_classes([AllowAny])
def link_notification_to_ranks(request, notification_sr_no):
    """
    Fetches crew members belonging to specific ranks (without department filtering)
    and creates delivery records linking them to the notification using their unique CrewID from FinalCrewList.
    Also creates entries in MscRankAssigned table linking the notification to the selected ranks.
    Expects the notification SR No (string) in the URL and JSON data containing
    selected rank UUIDs in the body.
    """
    print(f"=== link_notification_to_ranks: Starting for notification SR No {notification_sr_no} ===")
    print(f"link_notification_to_ranks: Request body: {request.body.decode('utf-8', errors='ignore')}")

    if request.method != 'POST':
        print(f"link_notification_to_ranks: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # Get request data (assuming JSON body)
        data = json.loads(request.body)
        selected_rank_uuids = data.get('selected_rank_ids', []) # Expecting a list of rank UUID strings

        if not selected_rank_uuids:
            print(f"link_notification_to_ranks: No selected_rank_ids (UUIDs) provided in request body.")
            return JsonResponse({'error': 'selected_rank_ids list is required'}, status=400)

        print(f"link_notification_to_ranks: Received selected rank UUIDs: {selected_rank_uuids}")
        print(f"link_notification_to_ranks: Associated notification SR No (from URL): {notification_sr_no}")

        # Find the notification object using the SR No () to get its details (e.g., for logging)
        try:
            notification = MscData.objects.get(sr_no=notification_sr_no)
            print(f"link_notification_to_ranks: Found notification object. ID: {notification.id},  Attachment Path: {notification.attachment_path}")
        except MscData.DoesNotExist:
            print(f"link_notification_to_ranks: Notification with SR No {notification_sr_no} not found.")
            return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)

        # --- NEW: Fetch Crew IDs based ONLY on selected Rank UUIDs (no department filter) ---
        # 1. Validate the selected_rank_uuids (optional but good practice)
        valid_selected_rank_uuids = []
        for rank_uuid_str in selected_rank_uuids:
             try:
                 # Validate each UUID string
                 uuid.UUID(rank_uuid_str)
                 valid_selected_rank_uuids.append(rank_uuid_str)
             except ValueError:
                 print(f"link_notification_to_ranks: Invalid UUID format in selected_rank_ids: {rank_uuid_str}")
                 # Continue with other valid IDs
                 continue

        if not valid_selected_rank_uuids:
             print(f"link_notification_to_ranks: No valid rank UUIDs provided.")
             return JsonResponse({'error': 'No valid rank UUIDs provided.'}, status=400)

        print(f"link_notification_to_ranks: Validated selected rank UUIDs: {valid_selected_rank_uuids}")

        # 2. Find HRM501 records matching ONLY the selected rank UUIDs (no department filter)
        # Since HRM501.rank_name stores the UUID of the MasterAppliedRank record,
        # we can directly filter by rank_name__in=valid_selected_rank_uuids
        print(f"link_notification_to_ranks: Fetching HRM501 records for rank UUIDs: {valid_selected_rank_uuids}")
        hrm_crews_matching_ranks = HRM501.objects.filter(
            rank_name__in=valid_selected_rank_uuids #  Filter HRM501 records where rank_name matches one of the selected rank UUIDs
        )

        print(f"link_notification_to_ranks: Found {hrm_crews_matching_ranks.count()} HRM501 records matching selected rank UUIDs.")

        if hrm_crews_matching_ranks.count() == 0: # Use == instead of ===
             print(f"link_notification_to_ranks: No HRM501 records found matching the selected rank UUIDs for notification {notification.sr_no}.")
             # Even if no crews are found, we might still want to record that the *ranks* were selected for this notification.
             # Let's proceed to create the rank assignment records.
             # return JsonResponse({'success': True, 'message': 'No crews found for the selected rank UUIDs.', 'crews_found': 0}, status=200)

        # 3. Find the corresponding FinalCrewList records using the HRM501 IDs found in step 2
        # The link is HRM501.id (UUID string) -> FinalCrewList.Crew_ref_id (UUID string)
        # Get the database IDs (UUID strings) of the matching HRM501 records
        hrm_ids_found = [hrm_crew.id for hrm_crew in hrm_crews_matching_ranks]
        print(f"link_notification_to_ranks: Found HRM501 IDs (UUIDs) to link to FinalCrewList: {hrm_ids_found}")

        print(f"link_notification_to_ranks: Fetching FinalCrewList records linked to HRM501 IDs: {hrm_ids_found}")
        final_crew_records = FinalCrewList.objects.filter(
            Crew_ref_id__in=hrm_ids_found #  Filter FinalCrewList where Crew_ref_id matches one of the HRM501 IDs
        )
        print(f"link_notification_to_ranks: Found {final_crew_records.count()} FinalCrewList records linked to matching HRM501 records.")

        # --- NEW: Create MscNotification Records for Each Crew (using FinalCrewList.CrewID) ---
        # Iterate through the FinalCrewList records found in step 3
        # Each FinalCrewList record has a CrewID (e.g., 'KSM001') which should be the crew_id in MscNotification
        created_notification_records_count = 0
        for final_crew_record in final_crew_records:
            # Get the unique CrewID string (e.g., 'KSM001') from FinalCrewList
            unique_crew_id = final_crew_record.CrewID
            # Get the HRM501.id string that this FinalCrewList record links to (for logging/debugging)
            linked_hrm_id = final_crew_record.Crew_ref_id

            print(f"link_notification_to_ranks: Processing crew ID {unique_crew_id} (linked to HRM ID {linked_hrm_id}) for notification {notification.sr_no}")

            # Create an MscNotification record linking the notification to the crew using the unique CrewID
            delivery_record = MscNotification(
                msc_sr_no=notification.sr_no, # Link to the SR No STRING of the *approved* notification
                crew_id=unique_crew_id, #  Use the unique CrewID string from FinalCrewList (e.g., 'KSM001')
                delivered_at=django_timezone.now(),
                reminder_count=1
                  # Set the delivery timestamp (to the time of this notification)
                # seen_at and reminder_sent_at remain NULL initially
            )
            delivery_record.save()
            created_notification_records_count += 1
            print(f"  - Created delivery record for crew {unique_crew_id} (linked to HRM {linked_hrm_id}) linked to notification {notification.sr_no}")

        print(f"link_notification_to_ranks: Successfully created {created_notification_records_count} delivery records in MscNotification table for notification {notification.sr_no} based on selected rank UUIDs.")



        created_rank_assignment_records_count = 0
        print(f"link_notification_to_ranks: Attempting to create rank assignment records in msc_rank_assigned table for notification {notification.sr_no} and ranks {valid_selected_rank_uuids}.")

        # Import connection for raw SQL execution
        # from django.db import connection # Ensure this import is present at the top of the file

        for rank_uuid_str in valid_selected_rank_uuids:
            print(f"link_notification_to_ranks: Creating rank assignment record for notification {notification.sr_no} and rank {rank_uuid_str}")

            # --- RAW SQL INSERT (OMIT EXPLICIT CAST) ---
            try:
                with connection.cursor() as cursor:
              
                    sql_insert = """
                        INSERT INTO msc_rank_assigned (msc_sr_no, rank_id, assigned_date, is_active, is_deleted)
                        VALUES (%s, %s, %s, %s, %s) -- No CAST for rank_id
                    """
                
                    sql_params = [
                        notification.sr_no, # Value for msc_sr_no_ column (string)
                        rank_uuid_str,      # Value for rank_id column (UUID string, let ODBC convert)
                        django_timezone.now(), # Value for assigned_date column (DateTime)
                        1,                  # Value for is_active column (BIT, True=1)
                        0                   # Value for is_deleted column (BIT, False=0)
                    ]

                    print(f"link_notification_to_ranks: Executing raw SQL INSERT: {sql_insert}")
                    print(f"link_notification_to_ranks: Parameters: {sql_params}")

                    # Execute the raw SQL INSERT
                    cursor.execute(sql_insert, sql_params)

                print(f"  - ✅ Created rank assignment record in msc_rank_assigned for notification {notification.sr_no} linked to rank {rank_uuid_str} using raw SQL.")
                created_rank_assignment_records_count += 1 # Increment the counter for successful inserts

            except Exception as raw_sql_error:
                print(f"❌ link_notification_to_ranks: Error executing raw SQL INSERT for notification {notification.sr_no} and rank {rank_uuid_str}: {raw_sql_error}")
                import traceback
                traceback.print_exc()
                # Continue to the next rank ID, don't break the loop for one error
                # You might want to log this specific failure
                continue
            # --- END RAW SQL INSERT ---

        print(f"link_notification_to_ranks: Successfully created {created_rank_assignment_records_count} rank assignment records in msc_rank_assigned table for notification {notification.sr_no}.")

        # --- END NEW: Store Rank Assignment Records (using Raw SQL) ---

        return JsonResponse({
            'success': True,
            'message': f'Notifications sent to {created_notification_records_count} crew members based on selected rank UUIDs. {created_rank_assignment_records_count} rank assignments recorded.',
            'crews_found': final_crew_records.count(),
            'records_created': created_notification_records_count,
            'rank_assignments_created': created_rank_assignment_records_count, # Include this count in the response
            'notification_sr_no': notification.sr_no # Include the SR No in the response for clarity
        })

    except json.JSONDecodeError as je:
        print(f"   ❌ JSON Decode Error: {je}")
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except MscData.DoesNotExist:
        print(f"link_notification_to_ranks: Notification with SR No {notification_sr_no} not found for department lookup or update.")
        return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)
    except Exception as e:
        print(f"link_notification_to_ranks: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)




@api_view(['GET'])
@permission_classes([AllowAny])
def get_crew_ids_and_status_by_notification_sr_no(request, notification_sr_no):
    """
    Fetches the list of crew IDs and their seen_at and reminder_sent_at status
    from the msc_notification table for a specific notification SR No.
    Expects the notification SR No in the URL path.
    Returns a JSON array of objects containing crew_id, seen_at, and reminder_sent_at.
    """
    print(f"=== get_crew_ids_and_status_by_notification_sr_no: Starting for notification SR No {notification_sr_no} ===")

    if request.method != 'GET':
        print(f"get_crew_ids_and_status_by_notification_sr_no: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    try:
        # Find all MscNotification records matching the specific msc_sr_no
        print(f"get_crew_ids_and_status_by_notification_sr_no: Fetching crew delivery records for notification SR No '{notification_sr_no}' from msc_notification table...")
        notification_records = MscNotification.objects.filter(msc_sr_no=notification_sr_no)

        # Prepare the response data as a list of dictionaries
        result = []
        for record in notification_records:
            result.append({
                'crew_id': record.crew_id, # The crew member's ID
                'seen_at': record.seen_at.isoformat() if record.seen_at else None, # Convert datetime to ISO string or None
                'reminder_sent_at': record.reminder_sent_at.isoformat() if record.reminder_sent_at else None, # Convert datetime to ISO string or None
                # Add other fields if needed, e.g., 'delivered_at': record.delivered_at.isoformat() if record.delivered_at else None,
            })

        print(f"get_crew_ids_and_status_by_notification_sr_no: Found {len(result)} delivery records for notification {notification_sr_no}")

        # Prepare the final response object
        response_data = {
            'notification_sr_no': notification_sr_no,
            'delivery_records': result, # The list of crew IDs and their status
            'count': len(result)
        }

        print(f"get_crew_ids_and_status_by_notification_sr_no: Returning {response_data['count']} delivery records for notification {notification_sr_no}")
        return JsonResponse(response_data, safe=False) # safe=False is needed for dictionary response

    except Exception as e:
        print(f"get_crew_ids_and_status_by_notification_sr_no: Error occurred - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
    



@api_view(['POST'])
@permission_classes([AllowAny])
def send_individual_notification_reminder(request, notification_sr_no):
    """
    Updates the reminder_sent_at field for a specific crew member associated
    with a specific notification SR No in the msc_notification table using raw SQL.
    Expects the notification SR No in the URL and the crew_id in the request body.
    """
    print(f"=== send_individual_notification_reminder: Starting for notification SR No {notification_sr_no} ===")

    if request.method != 'POST':
        print(f"send_individual_notification_reminder: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # Get the crew_id from the request body
        data = json.loads(request.body)
        crew_id_to_update = data.get('crew_id')
        if not crew_id_to_update:
            print("send_individual_notification_reminder: Missing 'crew_id' in request body.")
            return JsonResponse({'error': 'crew_id is required.'}, status=400)

        print(f"send_individual_notification_reminder: Received request to update reminder for notification {notification_sr_no} and crew {crew_id_to_update}")
        print(f"send_individual_notification_reminder: Request  {data}")

        update_sql = """
            UPDATE msc_notification
            SET reminder_sent_at = %s -- Use the current time as the value
            WHERE msc_sr_no = %s  -- Match the notification SR No
            AND crew_id = %s       -- Match the specific crew ID
            -- Optionally, you could add more conditions like AND is_deleted = 0
            -- if you want to ensure you're not updating records marked as deleted.
            -- AND is_deleted = 0
        """

        # Get the current time for the update
        current_time = django_timezone.now()
        print(f"send_individual_notification_reminder: Current time for reminder update: {current_time}")

        # Execute the raw SQL update query
        print(f"send_individual_notification_reminder: Executing raw SQL update for notification {notification_sr_no} and crew {crew_id_to_update}")
        with connection.cursor() as cursor:
            cursor.execute(update_sql, [current_time, notification_sr_no, crew_id_to_update]) # Pass parameters in the correct order
            rows_affected = cursor.rowcount

        print(f"send_individual_notification_reminder: Raw SQL update affected {rows_affected} rows.")

        if rows_affected == 0: # Use == instead of ===
             print(f"⚠️ send_individual_notification_reminder: No rows matched the criteria for notification {notification_sr_no} and crew {crew_id_to_update}. Perhaps the record doesn't exist or has already been updated.")
             # Decide: Return an error or a success message with 0 affected rows?
             # For now, let's return a success message but indicate no changes were made.
             return JsonResponse({
                 'success': True, # Considered successful if the operation ran without DB error
                 'message': f'No delivery records found for notification {notification_sr_no} and crew {crew_id_to_update}. Reminder not sent.',
                 'notification_sr_no': notification_sr_no,
                 'crew_id': crew_id_to_update,
                 'rows_affected': rows_affected
             }, status=200)

        print(f"✅ send_individual_notification_reminder: Successfully updated reminder_sent_at for crew {crew_id_to_update} on notification {notification_sr_no}.")

        return JsonResponse({
            'success': True,
            'message': f'Reminder sent successfully to crew {crew_id_to_update} for notification {notification_sr_no}.',
            'notification_sr_no': notification_sr_no,
            'crew_id': crew_id_to_update,
            'rows_affected': rows_affected,
            'reminder_sent_at': current_time.isoformat() # Include the timestamp in the response
        })

    except json.JSONDecodeError as je:
        print(f"send_individual_notification_reminder: JSON Decode Error: {je}")
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except Exception as e:
        print(f"send_individual_notification_reminder: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)




@api_view(['PUT'])
@permission_classes([AllowAny])
def edit_pending_notification(request, notification_id): #Parameter name is 'notification_id' but represents 'sr_no' string
    """
    Updates the details of an existing notification that is in the 'pending' state (publish_status = 1).
    Uses the notification's SR No (string) for identification.
    Does NOT change the publish_status itself unless explicitly provided in the request.
    Expects the notification SR No (string) in the URL and form data in the body.
    """
    print(f"=== edit_pending_notification: Starting for notification SR No {notification_id} ===") # ✅ Updated log
    print(f"edit_pending_notification: Request body keys: {list(request.POST.keys())}")
    print(f"edit_pending_notification: Request files: {list(request.FILES.keys())}")

    if request.method != 'POST':
        print(f"edit_pending_notification: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        # Find the specific notification record by its SR No (string) - ✅ Changed from 'id' to 'sr_no'
        print(f"edit_pending_notification: Attempting to find notification by SR No: {notification_id}")
        notification = MscData.objects.get(sr_no=notification_id) # ✅ Use sr_no for fetching
        print(f"edit_pending_notification: Found notification {notification.sr_no} (DB ID: {notification.id}). Current status: {notification.publish_status}")

        # Ensure the notification is in the pending state (status 1) before allowing edit
        if notification.publish_status != 1:
             print(f"edit_pending_notification: Notification {notification.sr_no} is not in pending status (status {notification.publish_status}). Cannot edit via this endpoint.")
             return JsonResponse({'error': f'Notification {notification.sr_no} is not in a pending state for editing.'}, status=400)

        # Get updated data from the form (only update fields if provided in the request)
        # This allows partial updates if desired.
        if request.POST.get('title') is not None:
            notification.title = request.POST.get('title')
            print(f"edit_pending_notification: Updated title to: {notification.title}")
        if request.POST.get('body') is not None:
            notification.office_instructions = request.POST.get('body') # Map body to office_instructions
            print(f"edit_pending_notification: Updated body to: {notification.office_instructions}")
        if request.POST.get('hashtags') is not None:
            notification.hashtags = request.POST.get('hashtags')
            print(f"edit_pending_notification: Updated hashtags to: {notification.hashtags}")
        if request.POST.get('type') is not None:
            notification.msc_type = request.POST.get('type')
            print(f"edit_pending_notification: Updated type to: {notification.msc_type}")
        if request.POST.get('department') is not None:
            try:
                notification.dept = int(request.POST.get('department'))
                print(f"edit_pending_notification: Updated department to: {notification.dept}")
            except ValueError:
                print(f"edit_pending_notification: Invalid department value received: {request.POST.get('department')}")
                return JsonResponse({'error': 'Invalid department value.'}, status=400)
        if request.POST.get('category') is not None:
            notification.category = request.POST.get('category')
            print(f"edit_pending_notification: Updated category to: {notification.category}")
        if request.POST.get('priority') is not None:
            notification.priority = request.POST.get('priority')
            print(f"edit_pending_notification: Updated priority to: {notification.priority}")
       
        # Handle sub-categories if provided
        sub_cat_list = request.POST.getlist('sub_cat') # Get list of sub categories
        if sub_cat_list:
             notification.sub_category = ', '.join(sub_cat_list)
             print(f"edit_pending_notification: Updated sub_category to: {notification.sub_category}")
        second_sub_cat_list = request.POST.getlist('second_sub_cat') # Get list of second sub categories
        if second_sub_cat_list:
             notification.second_sub_category = ', '.join(second_sub_cat_list)
             print(f"edit_pending_notification: Updated second_sub_category to: {notification.second_sub_category}")

        # Handle file attachment if provided
        if request.FILES.get('attachment'):
            uploaded_file = request.FILES['attachment']
            print(f"edit_pending_notification: New attachment provided: {uploaded_file.name}")


            # 1. Read the existing PDF (if one exists)
            original_pdf_reader = None
            if notification.attachment_path and os.path.exists(notification.attachment_path):
                 print("edit_pending_notification: Original attachment found, starting PDF cover regeneration...")
                 original_pdf_reader = PdfReader(notification.attachment_path)

                 # 2. Generate the UPDATED COVER PAGE (with new details)
                 cover_buffer = io.BytesIO()
                 c = canvas.Canvas(cover_buffer, pagesize=letter)
                 width, height = letter
                 margin = 50
                 top_section_y_start = height - 50

                 # --- 1. Company Header (with Logo - Conditional) ---
                 c.setFont("Helvetica-Bold", 12)
                 c.setFillColor(navy) # Dark blue for header

                 # Define logo dimensions and position (adjust as needed)
                 logo_path = os.path.join(settings.BASE_DIR, "static", "ksm-logo.png")
                 logo_width = 30
                 logo_height = 50
                 logo_x = margin
                 logo_y = top_section_y_start - (logo_height / 2)

                 try:
                     c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height, mask='auto')
                     print("✅ Logo added to updated cover.")
                     company_name_x = logo_x + logo_width + 8 # Adjust based on logo width and desired padding
                 except Exception as logo_err:
                     print(f"⚠️ Could not load or draw logo for updated cover: {logo_err}")
                     company_name_x = margin # Fallback to original position

                 c.drawString(company_name_x, top_section_y_start, "KAIZEN SHIP MANAGEMENT CO. LTD")
                 c.setFillColor(black) # Reset to black

                 # --- 2. Divider Line ---
                 divider_y = top_section_y_start - 15
                 c.setStrokeColor(navy)
                 c.line(margin, divider_y, width - margin, divider_y)
                 c.setStrokeColor(black) # Reset

                 # --- 3. Document Title (Dynamic) ---
                 c.setFont("Helvetica-Bold", 16)
                 title_y = divider_y - 40
                 # Use notification.msc_type, notification.dept, etc., to determine title
                 # Example logic from create_notification (adapt as needed):
                 doc_title_map = {
                     'Alert': 'SAFETY ALERT',
                     'Circular': 'CIRCULAR LETTER',
                     'WorkInstruction': 'WORK INSTRUCTION LETTER',
                     'alert': 'SAFETY ALERT',
                     'circular': 'CIRCULAR LETTER',
                     'workinstruction': 'WORK INSTRUCTION LETTER',
                 }
                 doc_title = doc_title_map.get(notification.msc_type, f"{notification.msc_type.upper()} LETTER")
                 c.drawCentredString(width / 2, title_y, doc_title)

                 # --- 4. Ref & Date ---
                 c.setFont("Helvetica", 10)
                 ref_date_y = title_y - 30
                 c.drawString(margin, ref_date_y, f"serial_no. : {notification.sr_no}")
                 c.drawRightString(width - margin, ref_date_y,
                                 f"Date: {notification.created_at.strftime('%d-%m-%Y') if notification.created_at else 'N/A'}")


                 if notification.superseeded_by:
                     # Position: Slightly above the date line
                     supersede_y = ref_date_y + 10 # Move up by 10 points
                     c.setFont("Helvetica-Bold", 10) # Smaller font for subtle emphasis
                     c.setFillColor(red) # Set color to red
                     c.drawRightString(width - margin, supersede_y, f"This letter Supersedes {notification.superseeded_by}")
                     c.setFillColor(black) # Reset to black for subsequent text
                     print(f"🖨️ PDF Cover Generation: Added 'Supersedes {notification.superseeded_by}' in RED at top right (during edit).")
                 else :
                      print("🖨️ PDF Cover Generation: No 'superseeded_by' found on notification object (during edit), skipping 'Supersedes' text on PDF cover.")
                 
                 # --- END NEW ---

                 # --- 5. Subject ---
                 c.setFont("Helvetica-Bold", 12)
                 subject_y = ref_date_y - 35 # Adjusted spacing to accommodate the Supersedes text if present
                 c.drawString(margin, subject_y, f"SUBJECT: {notification.title or notification.sr_no}")

                 # --- 6. Office Instructions (Main Body Content) (Multi-Page Support - DEBUGGED) ---
                 print("--- START: Office Instructions Generation (Update/Edit - DEBUG) ---")
                 c.setFont("Helvetica", 11)
                 body_start_y = subject_y - 40 # More space after subject
                 y_position = body_start_y
                 print(f"Office Instructions: Initial y_position: {y_position}, subject_y: {subject_y}, body_start_y: {body_start_y}")

                 body_text = notification.office_instructions or ""
                 print(f"edit_pending_notification: Adding body content: {body_text[:50]}...") # Log first 50 chars

                 if body_text:
                      # Simple text wrapping and drawing with multi-page support
                      text_object = c.beginText(margin, y_position)
                      text_object.setFont("Helvetica", 11)
                      max_width = width - 2 * margin
                      leading = 15 # Increased line spacing for readability
                      footer_threshold = 150 # Define the threshold before footer explicitly
                      print(f"Office Instructions: max_width: {max_width}, leading: {leading}, footer_threshold: {footer_threshold}")

                      lines = body_text.split('\n')
                      print(f"Office Instructions: Split body into {len(lines)} lines.")
                      for line_index, line in enumerate(lines):
                         #  print(f"  Processing body line {line_index + 1}: '{line[:50]}...'") # Log first 50 chars of line
                          # Basic wrapping logic
                          words = line.split(' ')
                          current_line = ""
                          for word_index, word in enumerate(words): # Add enumerate for index
                             #  print(f"    Processing word {word_index + 1}: '{word}'")
                              test_line = f"{current_line} {word}".strip()
                              test_line_width = c.stringWidth(test_line, "Helvetica", 11)
                             #  print(f"      Test line: '{test_line}', Width: {test_line_width}, Max allowed: {max_width}")

                              if test_line_width < max_width:
                                  current_line = test_line
                                 #  print(f"      - Added word to current_line. New current_line: '{current_line}'")
                              else:
                                  if current_line:
                                     #  print(f"      - Current line '{current_line}' exceeds max width, finalizing line.")
                                      # Check if we are running out of space on the current page
                                      next_line_y_pos = y_position - leading
                                     #  print(f"      Next line would be at y={next_line_y_pos}. Footer threshold is {footer_threshold}. Space remaining: {next_line_y_pos - footer_threshold}")
                                      if next_line_y_pos < footer_threshold: # Threshold before footer on current page
                                          print(f"      >>> NEED TO INSERT NEW PAGE HERE (during edit) <<<")
                                          # Draw the remaining part of the current line on the current page
                                          text_object.textLine(current_line)
                                          y_position -= leading
                                         #  print(f"      Drew '{current_line}' on current page. y_position now: {y_position}")

                                          # Finalize the current page's text object
                                          c.drawText(text_object)
                                         #  print(f"      Finalized text object for current page.")

                                          # Start a new page
                                          c.showPage()
                                          print(f"      Started new page (during edit).")

                                          # Reset for the new page
                                          y_position = height - 100 # Start near the top with some margin
                                         #  print(f"      Reset y_position for new page to: {y_position}")
                                          text_object = c.beginText(margin, y_position) # Create new text object for new page
                                          text_object.setFont("Helvetica", 11)
                                         #  print(f"      Created new text object for new page at y={y_position}")

                                      # Add the completed line to the text object
                                     #  print(f"      Adding completed line '{current_line}' to text object.")
                                      text_object.textLine(current_line)
                                      y_position -= leading # Move down for next line
                                     #  print(f"      Moved y_position down by {leading}. New y_position: {y_position}")
                                  else:
                                     #  print(f"      - Current line was empty, starting new line with word '{word}'")
                                        print("nothing")
                                  current_line = word # Start a new line with the current word
                                 #  print(f"      - Set current_line to word: '{current_line}'")
                          if current_line:
                             #  print(f"    Finalizing part of line '{current_line}'")
                              # Check space on current page before drawing final part of line
                              next_line_y_pos = y_position - leading
                              print(f"      Final part of line would be at y={next_line_y_pos}. Footer threshold is hardcoded to 150. Space remaining: {next_line_y_pos - 150}")
                              if next_line_y_pos < footer_threshold: # Threshold before footer
                                  print(f"      >>> NEED TO INSERT NEW PAGE FOR FINAL PART HERE (during edit) <<<")
                                  # Draw the final part of the current line on the current page
                                  text_object.textLine(current_line)
                                  y_position -= leading
                                  print(f"      Drew final part '{current_line}' on current page. y_position now: {y_position}")

                                  # Finalize the current page's text object
                                  c.drawText(text_object)
                                  print(f"      Finalized text object for current page (during edit).")

                                  # Start a new page
                                  c.showPage()
                                  print(f"      Started new page (during edit).")

                                  # Reset for the new page
                                  y_position = height - 100 # Start near the top
                                 #  print(f"      Reset y_position for new page to: {y_position}")
                                  text_object = c.beginText(margin, y_position) # Create new text object for new page
                                  text_object.setFont("Helvetica", 11)
                                 #  print(f"      Created new text object for new page at y={y_position}")

                             #  print(f"    Adding final part of line '{current_line}' to text object.")
                              # Add the final part of the line to the text object
                              text_object.textLine(current_line)
                              y_position -= leading # Move down for next line
                             #  print(f"    Moved y_position down by {leading}. New y_position: {y_position}")

                      # Finalize the last page's text object
                      print(f"Office Instructions: Finalizing text object on final page at y_position {y_position}")
                      c.drawText(text_object)
                      print("--- END: Office Instructions Generation (Update/Edit - DEBUG) ---")
                 else :
                      print("--- END: Office Instructions Generation (Update/Edit - DEBUG) ---")
                  # --- END 6. Office Instructions (Multi-Page Support - DEBUGGED) ---


                 footer_top_y = 100
                 c.setFont("Helvetica", 9) # Consistent smaller footer font

                 # Get the original creator (from the notification object)
                 created_by_part = f"Created By: {notification.created_by}" if notification.created_by else "Created By: Unknown User"
               
                 approved_by_part = f"Approved By: {notification.published_by}" if notification.published_by else "Approved By: Pending"
               
                 edited_at_part = f"Edited At: {django_timezone.now().strftime('%d-%m-%Y %H:%M:%S')}"

                
                 footer_middle_text = f"{created_by_part}, {approved_by_part}"

                 c.drawString(margin, footer_top_y, f"Sr. No: {notification.sr_no}")
                 c.drawCentredString(width / 2, footer_top_y, footer_middle_text)
                 c.drawRightString(width - margin, footer_top_y, edited_at_part) # Use edited timestamp

                 # Finalize page
                 c.showPage()
                 c.save()
                 cover_buffer.seek(0)
                 # ===== END: EMBEDDED COVER PAGE GENERATION =====


            
                 print("edit_pending_notification: Merging updated cover with original content...")
                 new_cover_reader = PdfReader(cover_buffer)
                 merger = PdfWriter()

           
                 merger.add_page(new_cover_reader.pages[0])

        
                 for i in range(1, len(original_pdf_reader.pages)):
                     merger.add_page(original_pdf_reader.pages[i])

            
                 output_path = notification.attachment_path # Overwrite the original file path

                 with open(output_path, 'wb') as output_file:
                     merger.write(output_file)

                 print(f"edit_pending_notification: ✅ Successfully updated PDF cover at {output_path}")

            else :
                 print("edit_pending_notification: No original attachment found or path invalid, creating new PDF with cover only.")
            

        notification.save(update_fields=[
            'title', 'office_instructions', 'hashtags', 'msc_type', 'dept', 'category',
            'sub_category', 'second_sub_category', 'priority', 'attachment_name', 'attachment_path'
        ])
        print(f"edit_pending_notification: ✅ Successfully updated notification {notification.sr_no} (DB ID: {notification.id}).")

        return JsonResponse({
            'success': True,
            'message': f'Notification {notification.sr_no} updated successfully.',
            'updated_sr_no': notification.sr_no,
            'updated_id': str(notification.id)
        })

    except MscData.DoesNotExist:
        print(f"edit_pending_notification: Notification with SR No {notification_id} not found.")
        return JsonResponse({'error': f'Notification with SR No {notification_id} not found.'}, status=404)
    except Exception as e:
        print(f"edit_pending_notification: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)