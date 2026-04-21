# ksm_backend ----->  views.py
import json
import os
import io
import uuid
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from modules.circular.circular.models import  HRM501, Msc2ndSubCat, MscCategory, MscData, MscPriority,MscRankAssigned,MscShipNotification,MscSubCat,MscType,MscNotification
from modules.circular.circular_ship.models import ShipUsersLogin
from modules.circular.circular.models import VesselData,MasterAppliedRank,CrewOnboardingHistory
from .models import MscAcknowledgeHistory
from django.db import connection,transaction
from django.core.mail import EmailMessage, get_connection
from django.db.models import F
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
import logging
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,  # minimum level to capture
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def _normalize_circular_role(role_value):
    return str(role_value or '').strip().upper()


def _is_circular_master_role(role_value):
    normalized_role = _normalize_circular_role(role_value)
    return normalized_role == 'MASTER' or normalized_role.endswith('_MASTER')


def _sortable_notification_dt(value):
    return value.isoformat() if value else ''


def _select_ack_notification_record(notification_rows):
    rows = list(notification_rows)
    if not rows:
        return None

    return max(
        rows,
        key=lambda row: (
            row.reminder_count if row.reminder_count is not None else -1,
            _sortable_notification_dt(row.reminder_sent_at),
            _sortable_notification_dt(row.delivered_at),
            _sortable_notification_dt(row.seen_at),
        ),
    )


# Regular font
FONT_REG = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'BOOKOS.TTF')

try:
    pdfmetrics.getFont('BookmanOldStyle')
except:
    if os.path.exists(FONT_REG):
        pdfmetrics.registerFont(TTFont('BookmanOldStyle', FONT_REG))

# Bold font
FONT_BOLD = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'BOOKOSB.TTF')

try:
    pdfmetrics.getFont('BookmanOldStyle-Bold')
except:
    if os.path.exists(FONT_BOLD):
        pdfmetrics.registerFont(TTFont('BookmanOldStyle-Bold', FONT_BOLD))




@api_view(['GET'])
@permission_classes([AllowAny])
def get_master_notifications(request):
    try:
        crew_id = request.GET.get('crew_id')
        if not crew_id:
            return JsonResponse({'error': 'crew_id is required'}, status=400)

        logging.info("Fetching master notifications")

        # 1. Get vessel for this master
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT Vessel
                FROM Crew_Onboarding_History
                WHERE CrewID = %s AND is_active = 1;
            """, [crew_id])

            row = cursor.fetchone()
            logger.info("this is test")
            if not row or row[0] is None:
                return JsonResponse([], safe=False)

            coh_vessel = row[0]


        # 2. Get all msc_sr_no for this vessel
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT msc_sr_no_
                FROM msc_ship_notification
                WHERE vessel_id = %s;
            """, [coh_vessel])

            rows = cursor.fetchall()
            logger.info(f"Found rows: {len(rows)}")

        # Proper validation
        if not rows:
            return JsonResponse([], safe=False)

        # Convert list of tuples → flat list of sr_no
        msc_sr_no_list = [r[0] for r in rows]
        logger.info(f"msc_sr_no_list: {msc_sr_no_list}")


        msc_sr_no_placeholders = ','.join(['%s'] * len(msc_sr_no_list))
        logger.info(f"msc_sr_no_placeholders: {msc_sr_no_placeholders}")

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    md.id,
                    md.sr_no,
                    md.published_on,
                    md.title,
                    d.department_name AS dept,
                    md.hashtags,
                    md.attachment_path,
                    mt.name AS type,
                    mp.name AS priority
                FROM msc_data md
                LEFT JOIN msc_type mt ON md.msc_type = mt.id
                LEFT JOIN msc_priority mp ON md.priority = mp.id
                LEFT JOIN department d ON md.dept = d.id
                WHERE md.sr_no IN ({msc_sr_no_placeholders})
                    AND md.is_deleted = 0
            """, msc_sr_no_list)
            rows = cursor.fetchall()
            logger.info(f"Fetched msc_data rows: {len(rows)}")
        
        columns = [
            'id', 'sr_no', 'published_on', 'title', 'dept',
            'hashtags', 'attachment_path', 'type', 'priority'
        ]
        msc_data = [dict(zip(columns, row)) for row in rows]


        result = []

        for obj in msc_data:
            sr_no = obj.get('sr_no')   # <-- FIX HERE AGAIN
            logger.info("t")
            totalcrew,unreadCount = get_total_crew(crew_id, sr_no)

            status = check_reminder_notification(sr_no,crew_id)
            isReminder = 1
            
            logging.info(f"status:{status}")
            if status == 'Acknowledged':
                isReminder = 0
            
            logger.info(f"isReminder:{isReminder}")

            status_ack = check_notification_Acknowledge(sr_no, crew_id)
            logger.info(f"status_ack:{status_ack}")
            isAck = 0
            if status_ack == 'Acknowledged':
                isAck = 1
            hashtags = [h.strip() for h in (obj.get('hashtags') or '').split(',') if h.strip()]

            dept = obj.get('dept')
            scope = "SEQ" if dept == 'Deck' else "Technical" if dept == 'Engine' else "Other"

            publishedDate = (
                obj['published_on'].isoformat()
                if obj.get('published_on')
                else None
            )

            attachment_url = None
            if obj.get('attachment_path'):
                attachment_url = f"/media/attachments/{os.path.basename(obj['attachment_path'])}"

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT delivered_at, seen_at, reminder_sent_at
                    FROM msc_notification
                    WHERE msc_sr_no = %s AND crew_id = %s
                """,[sr_no,crew_id])
                temp = cursor.fetchall()
            # Safe handling
            if temp:
                delivered_at, seen_at, reminder_sent_at = temp[0]
            else:
                delivered_at = seen_at = reminder_sent_at = None    

            result.append({
                'id': obj.get('id'),
                'sr_no': obj.get('sr_no'),
                'title': obj.get('title') or 'No Title',
                'type': obj.get('type') or 'Alert',
                'criticality': obj.get('priority') or 'Medium',
                'scope': scope,
                'publishedDate': publishedDate,
                'hashtags': hashtags,
                'attachment_url': attachment_url,
                'isReminded': isReminder,
                'isAck': isAck,
                'unreadCount': unreadCount,
                'totalCrew': totalcrew,
                'delivered_at': delivered_at,
                'seen_at': seen_at,
                'reminder_sent_at': reminder_sent_at
            })
        logging.info("final result")
        logging.info(result)
        return JsonResponse(result, safe=False)

    except Exception as e:
        logger.error("get_master_notifications failed: %s", str(e), exc_info=True)
        return JsonResponse({'error': 'Failed to load notifications'}, status=500)
    
    

@api_view(['GET'])
@permission_classes([AllowAny])
def get_non_master_notifications(request):
    try:
        crew_id = request.GET.get('crew_id')
        logging.info(f"Received crew_id: {crew_id}")
        if not crew_id:
            return JsonResponse({'error': 'crew_id is required'}, status=400)
        logging.info("Fetching non-master notifications")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM HRM501
                WHERE CrewID = %s
            """, [crew_id])
            hr_row = cursor.fetchone()

        logger.info(f"rank_id: {hr_row[3]}")

        # Fetch msc_sr_no list
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT msc_sr_no
                FROM msc_rank_assigned
                WHERE rank_id = %s
            """, [hr_row[3]])
            rank_rows = cursor.fetchall()

        logger.info(f"msc_rank_assigned rows: {rank_rows}")

        # Check if no rows found
        if not rank_rows:
            return JsonResponse([], safe=False)

        # Convert from list of tuples to flat list
        msc_sr_no_list = [r[0] for r in rank_rows]
        logger.info(f"sr_no_list: {msc_sr_no_list}")


        msc_sr_no_placeholders = ','.join(['%s'] * len(msc_sr_no_list))

        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    md.id,
                    md.sr_no,
                    md.published_on,
                    md.title,
                    d.department_name AS dept,
                    md.hashtags,
                    md.attachment_path,
                    mt.name AS type,
                    mp.name AS priority
                FROM msc_data md
                LEFT JOIN msc_type mt ON md.msc_type = mt.id
                LEFT JOIN msc_priority mp ON md.priority = mp.id
                LEFT JOIN department d ON md.dept = d.id
                WHERE md.sr_no IN ({msc_sr_no_placeholders})
                    AND md.is_deleted = 0
            """, msc_sr_no_list)
            rows = cursor.fetchall()

        columns = [
            'id', 'sr_no', 'published_on', 'title', 'dept',
            'hashtags', 'attachment_path', 'type', 'priority'
        ]
        msc_data = [dict(zip(columns, row)) for row in rows]
        

        result = []
        for obj in msc_data:
            var = obj.get('sr_no')
            logging.info(f"crew_id and sr_no : {crew_id},{var}")
            status = check_reminder_notification(var,crew_id)
            isReminder = 1
            
            logging.info(f"status:{status}")
            if status == 'Acknowledged':
                isReminder = 0
            status_ack = check_notification_Acknowledge(var,crew_id)
            isAck = 0
            if status_ack == 'Acknowledged':
                isAck = 1
            hashtags = [h.strip() for h in (obj.get('hashtags') or '').split(',') if h.strip()]

            dept = obj.get('dept')
            scope = "SEQ" if dept == 'Deck' else "Technical" if dept == 'Engine' else "Other"

            publishedDate = (
                obj['published_on'].isoformat()
                if obj.get('published_on')
                else None
            )

            attachment_url = None
            if obj.get('attachment_path'):
                attachment_url = f"/media/attachments/{os.path.basename(obj['attachment_path'])}"
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT delivered_at, seen_at, reminder_sent_at
                    FROM msc_notification
                    WHERE msc_sr_no = %s AND crew_id = %s
                """,[var,crew_id])
                temp = cursor.fetchall()
            # Safe handling
            if temp:
                delivered_at, seen_at, reminder_sent_at = temp[0]
            else:
                delivered_at = seen_at = reminder_sent_at = None

            result.append({
                'id': obj.get('id'),
                'sr_no': obj.get('sr_no'),
                'title': obj.get('title') or 'No Title',
                'type': obj.get('type') or 'Alert',
                'criticality': obj.get('priority') or 'Medium',
                'scope': scope,
                'publishedDate': publishedDate,
                'hashtags': hashtags,
                'attachment_url': attachment_url,
                'isReminded': isReminder,
                'isAck': isAck,
                'delivered_at': delivered_at,
                'seen_at': seen_at,
                'reminder_sent_at': reminder_sent_at
            })


        return JsonResponse(result, safe=False)

    except Exception as e:
        print("API Error:", str(e))
        return JsonResponse({'error': 'Failed to load notifications'}, status=500)
    

def check_reminder_notification(sr_no, crew_id):
    status = 'Pending'

    # Fetch notification (assumes it exists, like your ORM version)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TOP 1 reminder_count FROM msc_notification WHERE msc_sr_no = %s AND crew_id = %s",
            [sr_no, crew_id]
        )
        obj1_row = cursor.fetchone()
        if not obj1_row:
            logging.info(f"[check_reminder_notification] No msc_notification row for {sr_no}, {crew_id}")
            return "Pending"

        # ⚠️ If no row, obj1_row is None → next line will crash, just like ORM version
        notification_count = obj1_row[0]  # equivalent to obj1.reminder_count


    # Fetch acknowledgment history
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TOP 1 reminder_count FROM msc_acknowledge_history WHERE msc_sr_no = %s AND read_by = %s",
            [sr_no, crew_id]
        )
        obj2_row = cursor.fetchone()

    temp = 0
    if not obj2_row or obj2_row[0] == 0:
        temp = 1    
        if notification_count == 1:
            status = "Acknowledged"
        else:
            status = "Pending"
        return status
    
    if temp == 0:
        ack_count = obj2_row[0]  # equivalent to obj2.reminder_count
        if notification_count == ack_count:
            status = "Acknowledged"
    return status






def check_notification_Acknowledge(sr_no, crew_id):
    status = "Pending"
    logging.info("i am in ack")
    logger.info(f"{sr_no},{crew_id}")

    # Fetch reminder_count from msc_notification (assumes record exists)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TOP 1 reminder_count FROM msc_notification WHERE msc_sr_no = %s AND crew_id = %s",
            [sr_no, crew_id]
        )
        obj1_row = cursor.fetchone()
        # ⚠️ This will crash if no row is found — matches your ORM behavior
        if not obj1_row:
            logging.info(f"[check_reminder_notification] No msc_notification row for {sr_no}, {crew_id}")
            return "Pending"
        notification_count = obj1_row[0]

    logging.info("check reminder_count error1")
    logging.info("check reminder_count error2")

    # Fetch reminder_count from msc_acknowledge_history
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TOP 1 reminder_count FROM msc_acknowledge_history WHERE msc_sr_no = %s AND read_by = %s",
            [sr_no, crew_id]
        )
        obj2_row = cursor.fetchone()

    temp = 0
    if not obj2_row or obj2_row[0] == 0:
        temp = 1
        status = "Pending"
        return status

    if temp == 0:
        ack_count = obj2_row[0]
        if notification_count == ack_count:
            status = "Acknowledged"
    logger.info(f"status:{status}")

    return status
    

def get_total_crew(master_crew_id, sr_no):
    """
    Returns (total_crew_count, unread_count) for a given notification (sr_no),
    for active crew on the same vessel as the master (excluding master).
    
    Unread logic:
      - Crew has no row in msc_acknowledge_history → unread
      - OR: mn.reminder_count > ah.reminder_count → unread (new reminder after ack)
    """
    try:
        # STEP 1: Get master's vessel
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT TOP 1 Vessel
                FROM Crew_Onboarding_History
                WHERE CrewID = %s AND is_active = 1
                ORDER BY id DESC;
            """, [master_crew_id])
            row = cursor.fetchone()
            if not row:
                return 0, 0
            vessel_id = row[0]

        # STEP 2: Count total crew and unread in one query
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) AS total,
                    SUM(
                        CASE 
                            WHEN ah.msc_sr_no IS NULL 
                                 OR mn.reminder_count > ah.reminder_count
                            THEN 1 
                            ELSE 0 
                        END
                    ) AS unread
                FROM Crew_Onboarding_History coh
                INNER JOIN msc_notification mn 
                    ON coh.CrewID = mn.crew_id
                LEFT JOIN msc_acknowledge_history ah
                    ON ah.read_by = coh.CrewID
                    AND ah.msc_sr_no = mn.msc_sr_no
                WHERE 
                    coh.Vessel = %s
                    AND coh.is_active = 1
                    AND coh.CrewID <> %s
                    AND mn.msc_sr_no = %s
            """, [vessel_id, master_crew_id, sr_no])
            
            result = cursor.fetchone()

        total_crew = result[0] if result else 0
        unread_count = result[1] if result and result[1] is not None else 0
        return total_crew, unread_count

    except Exception as e:
        # Optional: log error if you have logger set up
        # logger.error("Error in get_total_crew: %s", str(e))
        return 0, 0

@api_view(['GET'])
@permission_classes([AllowAny])
def get_crew_list(request):
    try:
        crew_id = request.GET.get('crew_id')
        sr_no = request.GET.get('notification_id')
        if not crew_id or not sr_no:    
            return JsonResponse({'error': 'crew_id and notification_id is required'}, status=400)
        logging.info(f"Fetching crew list for master crew_id and sr_no: {crew_id}, {sr_no}")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT TOP 1 id, CrewID, Vessel
                FROM Crew_Onboarding_History
                WHERE CrewID = %s AND is_active = 1
                ORDER BY id DESC;
            """, [crew_id])

            row = cursor.fetchone()

        if not row:
            return JsonResponse(
                {'error': 'No active vessel found for this crew_id'},
                status=404
            )

        # row = (id, CrewID, Vessel)
        coh_vessel = row[2]     # Vessel

        # ------------------------------------
        # 2. Fetch all CrewIDs on same vessel except current crew
        # ------------------------------------
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT CrewID
                FROM Crew_Onboarding_History
                WHERE Vessel = %s
                AND is_active = 1
                AND CrewID <> %s;
            """, [coh_vessel, crew_id])

            crew_list = [r[0] for r in cursor.fetchall()]
        logging.info(f"Crew list: {crew_list}")


        if crew_list:  # Only proceed if there are crew members
            # Convert the list to a format suitable for SQL IN clause
            placeholders = ','.join(['%s'] * len(crew_list))
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT crew_id
                    FROM msc_notification
                    WHERE crew_id IN ({placeholders}) AND msc_sr_no = %s
                """, crew_list + [sr_no])
                
                crew_final_list = [r[0] for r in cursor.fetchall()]
            logging.info(f"Crew list: {crew_final_list}")
        else:
            crew_final_list = []
        crew_status_list = get_crew_status(crew_final_list,sr_no)
        logger.info(f"new:{crew_status_list}")
        return JsonResponse(crew_status_list, safe=False)
    except Exception as e:
        logging.error(f"Error fetching crew list: {str(e)}")
        return JsonResponse({'error': 'Failed to load crew list'}, status=500)
    

def get_crew_status(crew_list,sr_no):
    crew_status_list = []
    for crew in crew_list:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT reminder_count
                FROM msc_notification
                WHERE msc_sr_no = %s AND crew_id = %s
            """,[sr_no,crew])
            row = cursor.fetchone()
        notification_count = row[0]
        logger.info(f"notification_count:{notification_count},{sr_no},{crew}")    
        obj1 = (
            MscNotification.objects
            .filter(msc_sr_no=sr_no, crew_id=crew)
            .first()
        )

        notification_count = obj1.reminder_count
        obj2 = (
            MscAcknowledgeHistory.objects
            .filter(msc_sr_no=sr_no, read_by=crew)
            .first()
        )
        temp = 0
        if not obj2:
            temp = 1
            crew_status_list.append({
                "crew_id": crew,
                "status": "pending",
            })
        if temp == 0:
            
            ack_count = obj2.reminder_count
            if notification_count == ack_count:
                logger.info(f"temp=0:{obj2.read_by}")
                crew_status_list.append({
                "crew_id": crew,
                "status": "Acknowledged",
                })
            else:
                logger.info(f"temp=0:{obj2.read_by},{notification_count},{ack_count}")
                crew_status_list.append({
                "crew_id": crew,
                "status": "pending",
                })

    return crew_status_list
    

@api_view(['POST'])
@permission_classes([AllowAny])
def send_reminder(request):
    try:
        data = json.loads(request.body)
        sr_no = data.get('msc_sr_no')
        crew_id = data.get('crew_id')
        logging.info('inside api')
        if not sr_no or not crew_id:
            return JsonResponse({'error': 'msc_sr_no and crew_id are required'}, status=400)
        logging.info(f"sr_no and crew_id: {sr_no}, {crew_id}")
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE msc_notification
                SET reminder_sent_at = %s,
                    reminder_count = reminder_count + 1
                WHERE msc_sr_no = %s
                AND crew_id = %s
                            """,[timezone.now(),sr_no,crew_id])
            rows_updated = cursor.rowcount
        if rows_updated == 0:
            return JsonResponse({'error': 'No matching record found to update'}, status=404)
        email_result = email_sent(sr_no, crew_id)
        return JsonResponse({'message': 'Reminder sent successfully'}, status=200)
    except Exception as e:
        logging.error(f"Error sending reminder for notification {sr_no} to crew {crew_id}: {str(e)}")
        return JsonResponse({'error': 'Failed to send reminder'}, status=500)
    


def email_sent(sr_no, crew_id):
    """
    Send reminder emails for unread notifications.
    :param sr_no: Notification serial number
    :param crew_id: Crew ID
    :param test_email: Optional test email to override actual emails
    :return: dict with 'success' and 'emails_sent'
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT  
                    n.id AS notif_id,
                    h.email_id,
                    d.title
                FROM msc_notification n
                INNER JOIN msc_data d ON n.msc_sr_no = d.sr_no
                INNER JOIN HRM501 h ON h.CrewID = n.crew_id 
                WHERE n.msc_sr_no = %s
                  AND n.crew_id = %s
                  AND h.email_id IS NOT NULL
                  AND TRIM(h.email_id) != ''
                  AND h.email_id LIKE '%%@%%.%%'
            """, [sr_no, crew_id])

            results = cursor.fetchall()
            logger.info(f"DB Results: {results}")

        if not results:
            logger.info("No matching crew found for reminder.")
            return {'success': True, 'emails_sent': 0}
        
        def is_valid_email(email):
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return re.match(pattern, email) is not None

        email_messages = []
        for notif_id, email_id, title in results:
            email_id = email_id.strip()
            if not is_valid_email(email_id):
                logger.warning(f"Skipping invalid email: {email_id}")
                continue
            subject = f"Reminder: Unread Notification - {title}".replace('\n','').replace('\r','')
            body = f"""
Dear Crew Member,

This is a reminder that you have an unread notification in the KSM Marine Portal:

Title: {title}
Reference ID: {sr_no}

Please log in at your earliest convenience to review and acknowledge it.

Best regards,
Kaizen Ship Management
            """.strip()

            email_messages.append(
                EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email_id]
                )
            )

        emails_sent = 0
        if email_messages:
            with get_connection() as email_conn:
                sent_count = email_conn.send_messages(email_messages)
                emails_sent = sent_count or 0

        logger.info(f"Remind crew completed: emails_sent={emails_sent}")
        return {'success': True, 'emails_sent': emails_sent}

    except Exception:
        logger.exception("Error in email_sent")
        return {'success': False, 'emails_sent': 0, 'error': 'Failed to send reminders'}




@api_view(['POST'])
@permission_classes([AllowAny])
def crew_acknowledge_notification(request):
    try:
        data = json.loads(request.body)
        sr_no = data.get('msc_sr_no')
        crew_id = data.get('crew_id')
        crew_role = data.get('crew_role')
        is_master_role = _is_circular_master_role(crew_role)
        logging.info(f"TYPE CHECK => sr_no={sr_no} ({type(sr_no)}), crew_id={crew_id} ({type(crew_id)}) , crew_role={crew_role} ({type(crew_role)})")


        logging.info(f"fetching crew_id and sr_no: {crew_id},{sr_no}")

        if not sr_no or not crew_id:
            return JsonResponse({'error': 'msc_sr_no and crew_id are required'}, status=400)

        # fetch crew notification
        notification_rows = list(MscNotification.objects.filter(msc_sr_no=sr_no, crew_id=crew_id))
        obj1 = _select_ack_notification_record(notification_rows)
        if obj1 is None:
            return JsonResponse({'error': 'Record not found in msc_notification'}, status=404)
        if len(notification_rows) > 1:
            logging.warning(
                "Multiple msc_notification rows found for acknowledge request: sr_no=%s crew_id=%s count=%s. "
                "Proceeding with the row carrying the highest reminder state.",
                sr_no,
                crew_id,
                len(notification_rows),
            )

        logging.info('line obj1')
        # fetch acknowledge history
        try:
            obj2 = MscAcknowledgeHistory.objects.get(msc_sr_no=sr_no, read_by=crew_id)
        except MscAcknowledgeHistory.DoesNotExist:
            # create if not exists
            logging.info('line before')
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE msc_notification
                    SET seen_at = GETDATE()
                    WHERE msc_sr_no = %s AND crew_id = %s
                """,[sr_no,crew_id])
            if is_master_role:
                master_acknowledge_ship_notification(crew_id,sr_no)     
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO msc_acknowledge_history 
                        (id, msc_sr_no, read_by, read_at, reminder_count)
                    VALUES (NEWID(), %s, %s, GETDATE(), %s)
                """, [sr_no, crew_id, obj1.reminder_count])
            logging.info('line after')
            return JsonResponse({'message': 'Notification acknowledged successfully'}, status=200)

        # update logic
        current_time = timezone.now()

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE msc_notification
                SET seen_at = %s
                WHERE msc_sr_no = %s AND crew_id = %s
            """,[current_time,sr_no,crew_id])

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE msc_acknowledge_history
                SET 
                    read_at = %s,
                    reminder_count = %s
                WHERE id = %s
            """, [
                current_time,
                obj1.reminder_count,
                obj2.id
            ])
        if is_master_role:
            logging.info("MASTER check")
            master_acknowledge_ship_notification(crew_id,sr_no)

        logging.info('successful acknowledge')
        return JsonResponse({'message': 'Notification acknowledged successfully'}, status=200)

    except Exception as e:
        logging.error(f"Error acknowledging notification {sr_no} for crew {crew_id}: {str(e)}")
        return JsonResponse({'error': 'Failed to acknowledge notification'}, status=500)



def master_acknowledge_ship_notification(crew_id,sr_no):
    logging.info("ack for master")
    vessel_id = CrewOnboardingHistory.objects.get(CrewID=crew_id, is_active=True).Vessel
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE msc_ship_notification
            SET seen_at = %s
            WHERE msc_sr_no_ = %s
                AND vessel_id = %s
        """,[timezone.now(),sr_no,vessel_id])
    return


@api_view(['GET'])
@permission_classes([AllowAny])
def get_notification_pdf_url(request):
    notification_id = request.GET.get('notificationId')
    crew_id = request.GET.get('crew_id')
    logging.info(f"Fetching PDF URL for notification_id: {notification_id}, crew_id: {crew_id}")

    if not notification_id or not crew_id:
        return JsonResponse({'error': 'Missing params'}, status=400)

    try:
        with connection.cursor() as cursor:
            
            cursor.execute("""
                SELECT attachment_path
                FROM msc_data
                WHERE sr_no = %s
            """, [notification_id])

            row = cursor.fetchone()
            if not row or not row[0]:
                return JsonResponse({'error': 'PDF not found'}, status=404)
            
            filename = os.path.basename(row[0])

            relative_path = os.path.join(
                "circular", "attachments", filename
            )

            attachment_url = request.build_absolute_uri(
                settings.MEDIA_URL + relative_path
            )
            print(f"PDF URL: {attachment_url}")
            return JsonResponse({'attachment_url': attachment_url})

    except Exception as e:
        print("PDF View Error:", str(e))
        return JsonResponse({'error': 'Server error'}, status=500)
        

def _build_pdf(title, rows, is_circular=False):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, rightMargin=0.5 * inch, leftMargin=0.5 * inch)
    elements = []

    # --- Logo + Title ---
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'ksm-logo.png')
    header_data = []

    # Styles
    title_style = ParagraphStyle(
        'Title',
        fontName='Times-Bold',
        fontSize=22,
        alignment=0,
        spaceAfter=20,
        spaceBefore=20,
        textColor=colors.HexColor("#1F3247"),
        leading=26
    )
    body_style = ParagraphStyle(
        'Body',
        fontName='Times-Roman',
        fontSize=10,
        leading=12,
        wordWrap='CJK',
    )
    header_cell_style = ParagraphStyle(
        'HeaderCell',
        fontName='Times-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.white,
    )

    if os.path.exists(logo_path):
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(logo_path)
        img_width, img_height = img_reader.getSize()
        aspect_ratio = img_width / img_height

        # Set logo height to match title's line height (26pt)
        logo_height = 26  # Convert points to ReportLab units
        logo_width = logo_height * aspect_ratio

        logo = Image(logo_path, width=logo_width, height=logo_height)
        title_para = Paragraph(title, title_style)
        header_data = [[logo, Spacer(25,0), title_para]]
        col_widths = [logo_width, 25, 5.5 * inch]
    else:
        header_data = [[Paragraph(title, title_style)]]
        col_widths = [None]

    header_table = Table(header_data, colWidths=col_widths)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 16))

    # --- Table ---
    table_data = [
        [
            Paragraph('SR No.', header_cell_style),
            Paragraph('Description', header_cell_style),
            Paragraph('Issued on', header_cell_style)
        ]
    ]

    for row in rows:
        if len(row) == 4:
            sr_no, title_txt, published_on, doc_type = row
        else:
            sr_no, title_txt, published_on = row
            doc_type = None

        if not sr_no:
            continue

        date_str = ''
        if published_on:
            date_str = published_on.strftime('%d %b %Y')

        table_data.append([
            Paragraph(sr_no or '', body_style),
            Paragraph(title_txt or '—', body_style),
            Paragraph(date_str, body_style),
        ])

    if len(table_data) == 1:
        table_data.append([
            Paragraph('No active records found.', body_style),
            Paragraph('', body_style),
            Paragraph('', body_style)
        ])

    table = Table(
        table_data,
        colWidths=[2.0 * inch, 4.4 * inch, 0.9 * inch],
        hAlign='LEFT',
        vAlign='TOP'
    )
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LEADING', (0, 0), (-1, -1), 11),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer






@api_view(['GET'])
@permission_classes([AllowAny])
def download_filtered_report(request):
    crew_id = request.GET.get('crew_id')
    if not crew_id:
        return HttpResponse("crew_id is required", status=400)

    # Parse filters (same as frontend)
    types = request.GET.get('types', '').split(',') if request.GET.get('types') else []
    criticalities = request.GET.get('criticalities', '').split(',') if request.GET.get('criticalities') else []
    scopes = request.GET.get('scope', '').split(',') if request.GET.get('scope') else []
    search = request.GET.get('search', '').strip().lower()
    only_unread = request.GET.get('only_unread', 'false').lower() == 'true'

    # STEP 1: Get vessel
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Vessel FROM Crew_Onboarding_History
            WHERE CrewID = %s AND is_active = 1;
        """, [crew_id])
        row = cursor.fetchone()
        if not row or row[0] is None:
            return HttpResponse("No vessel assigned", status=404)
        vessel = row[0]

    # STEP 2: Get msc_sr_no list for vessel
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT msc_sr_no_ FROM msc_ship_notification WHERE vessel_id = %s;
        """, [vessel])
        sr_no_list = [r[0] for r in cursor.fetchall() if r[0]]

    if not sr_no_list:
        return HttpResponse("No notifications assigned", status=404)

    # STEP 3: Fetch full data (same as get_master_notifications)
    placeholders = ','.join(['%s'] * len(sr_no_list))

    query = f"""
        SELECT 
            md.sr_no,
            md.title,
            md.published_on,
            mt.name AS msc_type,
            mp.name AS priority,
            d.department_name AS dept
        FROM msc_data md
        LEFT JOIN msc_type mt ON md.msc_type = mt.id
        LEFT JOIN msc_priority mp ON md.priority = mp.id
        LEFT JOIN department d ON md.dept = d.id
        WHERE md.sr_no IN ({placeholders})
        AND md.is_deleted = 0
    """

    with connection.cursor() as cursor:
        cursor.execute(query, sr_no_list)
        rows = cursor.fetchall()
        columns = ['sr_no', 'title', 'published_on', 'msc_type', 'priority', 'dept']
        msc_data = [dict(zip(columns, row)) for row in rows]

    logger.info(f"Fetched {len(msc_data)} records for vessel {vessel}")

    # STEP 4: Apply same filtering logic as frontend
    filtered_rows = []
    for item in msc_data:
        sr_no = item['sr_no']
        title = item['title'] or ''
        msc_type = item['msc_type'] or 'Alert'
        priority = item['priority'] or 'Medium'
        dept = item.get('dept')
        scope_label = "SEQ" if dept == "Deck" else "Technical" if dept == "Engine" else "Other"
        published_on = item['published_on']
        logger.info(f"Evaluating SR No: {sr_no}, Type: {msc_type}, Priority: {priority}, Scope: {scope_label}, dept: {dept}")

        # --- Apply frontend filters (NO revoked check needed) ---
        logger.info(f"types: {types}, {msc_type}, criticalities: {criticalities}, {priority}, scopes: {scopes}, {scope_label}, search: '{search}', only_unread: {only_unread}")
        if types and msc_type not in types:
            continue
        logger.info("1")
        if criticalities and priority not in criticalities:
            continue
        logging.info("2")
        if scopes and scope_label not in scopes:
            continue
        logging.info("3")
        if search and not (search in sr_no.lower() or search in title.lower()):
            continue
        logging.info("4")
        logger.info(f"only_unread: {only_unread}, type: {type(only_unread)}")
        if only_unread:
            # 1. Check assignmen
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT reminder_count FROM msc_notification
                    WHERE msc_sr_no = %s AND crew_id = %s
                """, [sr_no, crew_id])
                notif_row = cur.fetchone()
            
            if not notif_row:
                continue  # Not assigned → skip

            notification_count = notif_row[0]

            # 2. Check acknowledgment
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT reminder_count FROM msc_acknowledge_history
                    WHERE msc_sr_no = %s AND read_by = %s
                """, [sr_no, crew_id])
                ack_row = cur.fetchone()

            # 3. Determine if acknowledged
            is_acknowledged = False
            if ack_row:
                ack_count = ack_row[0]
                if ack_count >= notification_count:  # Use >= for safety
                    is_acknowledged = True

            # 4. Skip if acknowledged
            if is_acknowledged:
                continue

        # If we reach here, the item passes all filters → include it
        filtered_rows.append((sr_no, title, published_on, msc_type))
        logger.info(f"filtered row: {filtered_rows[-1]}")

    # Build title
    title = "KAIZEN SHIP MANAGEMENT"
    if search:
        title += f" (Search: {search})"
    if only_unread:
        title += " (Unread Only)"

    # Date format: use full date if ANY circular is in the result
    is_circular = any(row[3] == 'Circular' for row in filtered_rows)

    pdf_buffer = _build_pdf(title, filtered_rows, is_circular=is_circular)
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="KSM_Filtered_Report.pdf"'
    return response


