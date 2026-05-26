
#Backend ---> views.py

import json
import uuid
import os
import io
import logging
import traceback
import hashlib
import requests
from types import SimpleNamespace
from datetime import datetime, timezone
from datetime import timezone as datetime_timezone
from django.http import JsonResponse
from django.db import transaction
from django.db import connection
from django.db import DatabaseError
from reportlab.lib.colors import navy, black, red, white
from django.conf import settings
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import DependencyError, PdfReadError
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
from django.core.exceptions import ValidationError
from apps.notifications.signals import (
    notify_circular_approved,
    notify_circular_created,
    notify_circular_distribution,
    notify_circular_pending_approval,
    notify_circular_rejected,
)
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


CIRCULAR_SR_LOCK_TIMEOUT_MS = 15000
MAX_CIRCULAR_ATTACHMENT_FILES = 3
ALLOWED_CIRCULAR_DELIVERY_CREW_STATUSES = ("Available", "On Board", "On Leave")
ALLOWED_CIRCULAR_DELIVERY_CREW_STATUS_LOOKUP = tuple(
    status_name.lower() for status_name in ALLOWED_CIRCULAR_DELIVERY_CREW_STATUSES
)
PDF_FONT_NAME = "bookos"
PDF_HEADER_FONT_SIZE = 12
PDF_TITLE_FONT_SIZE = 16
PDF_META_FONT_SIZE = 10
PDF_SUBJECT_FONT_SIZE = 12
PDF_SUBJECT_LINE_HEIGHT = 16
PDF_BODY_FONT_SIZE = 11
PDF_FOOTER_FONT_SIZE = 9
PDF_LINE_HEIGHT = 15
PDF_HEADER_GAP = 12
PDF_FIXED_FOOTER_Y = 42
PDF_FIXED_FOOTER_LINE_Y = PDF_FIXED_FOOTER_Y + 16
PDF_BODY_STOP_Y = PDF_FIXED_FOOTER_LINE_Y + 24
PDF_HEADER_TEXT = "KAIZEN SHIP MANAGEMENT CO. LTD"


class CircularAttachmentValidationError(ValueError):
    pass

# Keep existing SR prefixes stable for known departments while still
# falling back to the department master when new departments are added.
SR_NO_DEPARTMENT_DISPLAY_OVERRIDES = {
    '8949308c-aa8a-ee11-987c-7413ea3d6a70': 'SEQ',
    '8a49308c-aa8a-ee11-987c-7413ea3d6a70': 'Technical',
}

TECHNICAL_SUPERINTENDENT_PROFILE_IDS = {
    'd604980f-0f1c-ef11-a9f1-f348983bae6b',
}
TECHNICAL_CIRCULAR_DEPARTMENT_NAMES = {'engine', 'technical'}


def _get_department_display_name_for_sr_no(dept_id_string):
    if not dept_id_string:
        return 'Unknown Dept'

    override_display_name = SR_NO_DEPARTMENT_DISPLAY_OVERRIDES.get(str(dept_id_string).lower())
    if override_display_name:
        return override_display_name

    department_name = _lookup_department_name_by_identifier(dept_id_string)
    if department_name and department_name.strip():
        return department_name.strip()

    return 'Unknown Dept'


def _get_department_master_name(dept_id_string):
    if not dept_id_string:
        return None

    legacy_department_map = {
        '0': 'Deck',
        '1': 'Engine',
        'seq': 'Deck',
        'technical': 'Engine',
        'deck': 'Deck',
        'engine': 'Engine',
    }
    normalized_value = str(dept_id_string).strip()
    if normalized_value.lower() in legacy_department_map:
        return legacy_department_map[normalized_value.lower()]

    normalized_uuid = _clean_uuid_string(normalized_value)
    if not normalized_uuid:
        return normalized_value or None

    try:
        department_name = _lookup_department_name_by_identifier(normalized_uuid)
    except Exception as exc:
        print(f"_get_department_master_name: Failed to resolve department '{normalized_value}': {exc}")
        return normalized_value or None

    if department_name and department_name.strip():
        return department_name.strip()

    return normalized_value or None


def _clean_uuid_string(value):
    """Return a normalized UUID string or None when the value is empty/invalid."""
    if value is None:
        return None

    cleaned_value = str(value).strip().strip("'\"()[] ")
    if not cleaned_value:
        return None

    try:
        return str(uuid.UUID(cleaned_value))
    except (ValueError, AttributeError, TypeError):
        return None


def _normalize_uuid_list(values):
    normalized_values = []
    seen_values = set()

    for raw_value in values or []:
        cleaned_value = _clean_uuid_string(raw_value)
        if not cleaned_value or cleaned_value in seen_values:
            continue
        seen_values.add(cleaned_value)
        normalized_values.append(cleaned_value)

    return normalized_values


def _normalize_text_list(values):
    normalized_values = []
    seen_values = set()

    for raw_value in values or []:
        cleaned_value = str(raw_value or "").strip()
        if not cleaned_value or cleaned_value in seen_values:
            continue
        seen_values.add(cleaned_value)
        normalized_values.append(cleaned_value)

    return normalized_values


def _filter_crew_ids_by_allowed_status(crew_ids):
    normalized_crew_ids = _normalize_text_list(crew_ids)
    if not normalized_crew_ids:
        return []

    values_clause = ", ".join(["(%s)"] * len(normalized_crew_ids))
    status_placeholders = ", ".join(["%s"] * len(ALLOWED_CIRCULAR_DELIVERY_CREW_STATUS_LOOKUP))
    sql = f"""
        SET NOCOUNT ON;

        DECLARE @target_crews TABLE (
            crew_id NVARCHAR(255) PRIMARY KEY
        );

        INSERT INTO @target_crews (crew_id)
        VALUES {values_clause};

        WITH latest_final_crew AS (
            SELECT
                LTRIM(RTRIM(fcl.CrewID)) AS crew_id,
                LTRIM(RTRIM(COALESCE(cs.CrewStatusName, ''))) AS crew_status_name,
                ROW_NUMBER() OVER (
                    PARTITION BY LTRIM(RTRIM(fcl.CrewID))
                    ORDER BY
                        fcl.updated_date DESC,
                        fcl.created_date DESC,
                        fcl.id DESC
                ) AS rn
            FROM Final_crew_list fcl
            INNER JOIN @target_crews target
                ON target.crew_id = LTRIM(RTRIM(fcl.CrewID))
            LEFT JOIN ksm_marine_live.dbo.CrewStatus cs
                ON cs.id = fcl.Crew_Status
            WHERE ISNULL(fcl.is_active, 0) = 1
              AND ISNULL(fcl.is_delete, 0) = 0
              AND LTRIM(RTRIM(ISNULL(fcl.CrewID, ''))) <> ''
        )
        SELECT crew_id
        FROM latest_final_crew
        WHERE rn = 1
          AND LOWER(crew_status_name) IN ({status_placeholders});
    """

    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            normalized_crew_ids + list(ALLOWED_CIRCULAR_DELIVERY_CREW_STATUS_LOOKUP),
        )
        allowed_crew_ids = {
            str(row[0] or "").strip()
            for row in cursor.fetchall()
            if str(row[0] or "").strip()
        }

    return [crew_id for crew_id in normalized_crew_ids if crew_id in allowed_crew_ids]


def _format_pending_draft_doc_type_name(doc_type_display_name):
    normalized_name = str(doc_type_display_name or '').strip()
    if not normalized_name:
        return 'this document type'

    compact_name = normalized_name.replace(' ', '').lower()
    if compact_name == 'workinstruction':
        return 'Work Instruction'
    if compact_name == 'circular':
        return 'Circular'
    if compact_name == 'alert':
        return 'Alert'

    return normalized_name


def _build_pending_draft_conflict_message(doc_type_display_name):
    resolved_doc_type_name = _format_pending_draft_doc_type_name(doc_type_display_name)
    return (
        f"There is already a draft pending for {resolved_doc_type_name}. "
        "Please clear that first to avoid sequence disturbance."
    )


def _get_existing_active_draft_for_creator_and_type(created_by_id, msc_type_id, doc_type_display_name=None):
    normalized_created_by = str(created_by_id or '').strip()
    normalized_type_id = _clean_uuid_string(msc_type_id)
    normalized_doc_type_name = str(doc_type_display_name or '').strip()
    compact_doc_type_name = normalized_doc_type_name.replace(' ', '').lower()

    if not normalized_created_by or (not normalized_type_id and not compact_doc_type_name):
        return None

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT TOP 1
                id,
                sr_no
            FROM msc_data
            WHERE LTRIM(RTRIM(ISNULL(created_by, ''))) = %s
              AND publish_status = 0
              AND ISNULL(is_deleted, 0) = 0
              AND (
                    (
                        %s IS NOT NULL
                        AND LOWER(CONVERT(VARCHAR(36), TRY_CONVERT(uniqueidentifier, msc_type))) = %s
                    )
                    OR (
                        %s <> ''
                        AND REPLACE(LOWER(LTRIM(RTRIM(CONVERT(NVARCHAR(255), msc_type)))), ' ', '') = %s
                    )
              )
            ORDER BY created_at DESC
            """,
            [
                normalized_created_by,
                normalized_type_id,
                normalized_type_id,
                compact_doc_type_name,
                compact_doc_type_name,
            ],
        )
        row = cursor.fetchone()

    if not row:
        return None

    return SimpleNamespace(
        id=row[0],
        sr_no=row[1],
    )


def _lookup_department_name_by_identifier(dept_id_string):
    normalized_value = str(dept_id_string or "").strip().lower()
    if not normalized_value:
        return None

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT TOP 1 department_name
            FROM department
            WHERE LOWER(LTRIM(RTRIM(CONVERT(VARCHAR(36), id)))) = %s
            """,
            [normalized_value],
        )
        row = cursor.fetchone()

    return str(row[0]).strip() if row and row[0] else None


def _resolve_circular_actor_profile(actor_identifier):
    normalized_actor = str(actor_identifier or "").strip()
    if not normalized_actor:
        return None

    identifiers = {normalized_actor}
    employee_role = None

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT TOP 1 employee_id, username, employee_role
            FROM users
            WHERE LOWER(LTRIM(RTRIM(employee_id))) = LOWER(%s)
               OR LOWER(LTRIM(RTRIM(username))) = LOWER(%s)
            """,
            [normalized_actor, normalized_actor],
        )
        row = cursor.fetchone()

    if row:
        employee_id, username, employee_role = row
        if employee_id:
            identifiers.add(str(employee_id).strip())
        if username:
            identifiers.add(str(username).strip())

    profile_sql = """
        SELECT TOP 1
            CONVERT(VARCHAR(36), mr.id) AS profile_id,
            mr.role_name,
            p.form_ids,
            p.process_ids
        FROM mapping_role_user mru
        LEFT JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        LEFT JOIN msc_profiles p
            ON p.profile_id = mr.id
           AND p.work_side = 0
           AND p.is_active = 1
           AND p.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(LTRIM(RTRIM(mru.userid))) = LOWER(%s)
    """
    for identifier in identifiers:
        with connection.cursor() as cursor:
            cursor.execute(profile_sql, [identifier])
            row = cursor.fetchone()
        if row:
            return SimpleNamespace(
                profile_id=str(row[0]).strip() if row[0] else None,
                profile_name=str(row[1]).strip() if row[1] else None,
                form_ids=row[2],
                process_ids=row[3],
            )

    if employee_role:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    CONVERT(VARCHAR(36), profile_id) AS profile_id,
                    profile_name,
                    form_ids,
                    process_ids
                FROM msc_profiles
                WHERE work_side = 0
                  AND is_active = 1
                  AND is_deleted = 0
                  AND LOWER(LTRIM(RTRIM(profile_name))) = LOWER(%s)
                """,
                [str(employee_role).strip()],
            )
            row = cursor.fetchone()
        if row:
            return SimpleNamespace(
                profile_id=str(row[0]).strip() if row[0] else None,
                profile_name=str(row[1]).strip() if row[1] else None,
                form_ids=row[2],
                process_ids=row[3],
            )

    return None


def _is_technical_superintendent_profile(profile):
    if not profile:
        return False

    profile_id = str(getattr(profile, 'profile_id', '') or '').strip().lower()
    profile_name = str(getattr(profile, 'profile_name', '') or '').strip().lower()
    return (
        profile_id in TECHNICAL_SUPERINTENDENT_PROFILE_IDS
        or profile_name == 'technical superintendent'
    )


def _is_technical_circular_notification(notification):
    dept_name = _get_department_master_name(getattr(notification, 'dept', None))
    normalized_dept_name = str(dept_name or '').strip().lower()
    if normalized_dept_name in TECHNICAL_CIRCULAR_DEPARTMENT_NAMES:
        return True

    sr_no = str(getattr(notification, 'sr_no', '') or '').strip().lower()
    return '/technical/' in sr_no


def _validate_circular_approval_scope(notification, data):
    actor_identifier = (
        data.get('published_by')
        or data.get('acted_by')
        or data.get('actor_id')
        or data.get('updated_by')
    )
    if not actor_identifier:
        # Keep legacy callers working. Current UI sends published_by for approve
        # and acted_by for reject so this is only a compatibility fallback.
        return None

    actor_profile = _resolve_circular_actor_profile(actor_identifier)
    if _is_technical_superintendent_profile(actor_profile):
        return JsonResponse(
            {
                'error': (
                    'Technical Superintendent is not allowed to approve or '
                    'reject circulars, alerts, or work instructions.'
                )
            },
            status=403,
        )

    return None


def _fetch_all_rows_from_cursor(cursor):
    rows = []

    while True:
        if cursor.description is not None:
            rows = cursor.fetchall()

        try:
            has_next_result = cursor.nextset()
        except Exception as exc:
            if "No results" in str(exc):
                break
            raise

        if not has_next_result:
            break

    return rows


def _build_uuid_values_clause(uuid_values):
    if not uuid_values:
        return "", []

    return ", ".join(["(CAST(%s AS UNIQUEIDENTIFIER))"] * len(uuid_values)), list(uuid_values)


def _bulk_insert_ship_delivery_records(notification_sr_no, vessel_ids, delivered_at):
    normalized_vessel_ids = _normalize_uuid_list(vessel_ids)
    if not normalized_vessel_ids:
        return []

    values_clause, sql_params = _build_uuid_values_clause(normalized_vessel_ids)
    sql = f"""
        SET NOCOUNT ON;

        DECLARE @target_vessels TABLE (
            vessel_id UNIQUEIDENTIFIER PRIMARY KEY
        );

        INSERT INTO @target_vessels (vessel_id)
        VALUES {values_clause};

        DECLARE @inserted_vessels TABLE (
            vessel_id UNIQUEIDENTIFIER PRIMARY KEY
        );

        INSERT INTO msc_ship_notification (msc_sr_no_, vessel_id, delivered_at)
        OUTPUT INSERTED.vessel_id INTO @inserted_vessels (vessel_id)
        SELECT %s, target.vessel_id, %s
        FROM @target_vessels target
        WHERE NOT EXISTS (
            SELECT 1
            FROM msc_ship_notification existing WITH (UPDLOCK, HOLDLOCK)
            WHERE existing.msc_sr_no_ = %s
              AND existing.vessel_id = target.vessel_id
        );

        SELECT CAST(vessel_id AS VARCHAR(36)) AS vessel_id
        FROM @inserted_vessels;
    """

    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            sql_params + [notification_sr_no, delivered_at, notification_sr_no],
        )
        return _normalize_uuid_list([row[0] for row in _fetch_all_rows_from_cursor(cursor)])


def _bulk_insert_rank_assignments(notification_sr_no, rank_ids, assigned_at):
    normalized_rank_ids = _normalize_uuid_list(rank_ids)
    if not normalized_rank_ids:
        return []

    values_clause, sql_params = _build_uuid_values_clause(normalized_rank_ids)
    sql = f"""
        SET NOCOUNT ON;

        DECLARE @target_ranks TABLE (
            rank_id UNIQUEIDENTIFIER PRIMARY KEY
        );

        INSERT INTO @target_ranks (rank_id)
        VALUES {values_clause};

        DECLARE @inserted_ranks TABLE (
            rank_id UNIQUEIDENTIFIER PRIMARY KEY
        );

        INSERT INTO msc_rank_assigned (msc_sr_no, rank_id, assigned_date, is_active, is_deleted)
        OUTPUT INSERTED.rank_id INTO @inserted_ranks (rank_id)
        SELECT %s, target.rank_id, %s, 1, 0
        FROM @target_ranks target
        WHERE NOT EXISTS (
            SELECT 1
            FROM msc_rank_assigned existing WITH (UPDLOCK, HOLDLOCK)
            WHERE existing.msc_sr_no = %s
              AND existing.rank_id = target.rank_id
              AND ISNULL(existing.is_deleted, 0) = 0
        );

        SELECT CAST(rank_id AS VARCHAR(36)) AS rank_id
        FROM @inserted_ranks;
    """

    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            sql_params + [notification_sr_no, assigned_at, notification_sr_no],
        )
        return _normalize_uuid_list([row[0] for row in _fetch_all_rows_from_cursor(cursor)])


def _fetch_target_crew_ids_for_ranks(rank_ids):
    normalized_rank_ids = _normalize_uuid_list(rank_ids)
    if not normalized_rank_ids:
        return []

    placeholders = ", ".join(["%s"] * len(normalized_rank_ids))
    sql = f"""
        SELECT DISTINCT
            LTRIM(RTRIM(fcl.CrewID)) AS crew_id
        FROM final_crew_list fcl
        INNER JOIN HRM501 hrm
            ON hrm.id = TRY_CONVERT(UNIQUEIDENTIFIER, fcl.Crew_ref_id)
        WHERE hrm.rank_name IN ({placeholders})
          AND ISNULL(hrm.is_deleted, 0) = 0
          AND LTRIM(RTRIM(ISNULL(fcl.CrewID, ''))) <> ''
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, normalized_rank_ids)
        target_crew_ids = _normalize_text_list([row[0] for row in cursor.fetchall()])

    return _filter_crew_ids_by_allowed_status(target_crew_ids)


def _fetch_target_crew_ids_for_vessels(vessel_ids):
    normalized_vessel_ids = _normalize_uuid_list(vessel_ids)
    if not normalized_vessel_ids:
        return []

    values_clause, sql_params = _build_uuid_values_clause(normalized_vessel_ids)
    sql = f"""
        SET NOCOUNT ON;

        DECLARE @target_vessels TABLE (
            vessel_id UNIQUEIDENTIFIER PRIMARY KEY
        );

        INSERT INTO @target_vessels (vessel_id)
        VALUES {values_clause};

        WITH latest_onboarding AS (
            SELECT
                LTRIM(RTRIM(coh.CrewID)) AS crew_id,
                coh.Vessel,
                ROW_NUMBER() OVER (
                    PARTITION BY LTRIM(RTRIM(coh.CrewID))
                    ORDER BY
                        CASE WHEN ISNULL(coh.is_active, 0) = 1 THEN 0 ELSE 1 END,
                        coh.updated_date DESC,
                        coh.created_date DESC,
                        coh.SignOnDate DESC,
                        coh.id DESC
                ) AS rn
            FROM Crew_Onboarding_History coh
            INNER JOIN @target_vessels target
                ON target.vessel_id = TRY_CONVERT(UNIQUEIDENTIFIER, coh.Vessel)
            WHERE ISNULL(coh.is_deleted, 0) = 0
              AND LTRIM(RTRIM(ISNULL(coh.CrewID, ''))) <> ''
        )
        SELECT DISTINCT crew_id
        FROM latest_onboarding
        WHERE rn = 1;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, sql_params)
        target_crew_ids = _normalize_text_list([row[0] for row in _fetch_all_rows_from_cursor(cursor)])

    return _filter_crew_ids_by_allowed_status(target_crew_ids)


def _bulk_insert_crew_delivery_records(notification_sr_no, crew_ids, delivered_at, reminder_count=1):
    normalized_crew_ids = _normalize_text_list(crew_ids)
    if not normalized_crew_ids:
        return []

    values_clause = ", ".join(["(%s)"] * len(normalized_crew_ids))
    sql = f"""
        SET NOCOUNT ON;

        DECLARE @target_crews TABLE (
            crew_id NVARCHAR(255) PRIMARY KEY
        );

        INSERT INTO @target_crews (crew_id)
        VALUES {values_clause};

        DECLARE @inserted_crews TABLE (
            crew_id NVARCHAR(255) PRIMARY KEY
        );

        INSERT INTO msc_notification (msc_sr_no, crew_id, delivered_at, reminder_count)
        OUTPUT INSERTED.crew_id INTO @inserted_crews (crew_id)
        SELECT %s, target.crew_id, %s, %s
        FROM @target_crews target
        WHERE NOT EXISTS (
            SELECT 1
            FROM msc_notification existing WITH (UPDLOCK, HOLDLOCK)
            WHERE existing.msc_sr_no = %s
              AND LTRIM(RTRIM(existing.crew_id)) = target.crew_id
        );

        SELECT crew_id
        FROM @inserted_crews;
    """

    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            normalized_crew_ids + [notification_sr_no, delivered_at, reminder_count, notification_sr_no],
        )
        return _normalize_text_list([row[0] for row in _fetch_all_rows_from_cursor(cursor)])


def _fetch_vessel_rows_by_ids(vessel_ids):
    normalized_vessel_ids = _normalize_uuid_list(vessel_ids)
    if not normalized_vessel_ids:
        return {}

    values_clause = ", ".join(["(%s)"] * len(normalized_vessel_ids))
    sql = f"""
        SET NOCOUNT ON;

        DECLARE @target_vessels TABLE (
            vessel_id NVARCHAR(36) PRIMARY KEY
        );

        INSERT INTO @target_vessels (vessel_id)
        VALUES {values_clause};

        SELECT
            LOWER(LTRIM(RTRIM(CONVERT(VARCHAR(36), vessel.id)))) AS vessel_id,
            vessel.VesselName,
            vessel.vesselCode,
            vessel.email
        FROM VesselData vessel
        INNER JOIN @target_vessels target
            ON LOWER(LTRIM(RTRIM(CONVERT(VARCHAR(36), vessel.id)))) = target.vessel_id;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [value.lower() for value in normalized_vessel_ids])
        rows = _fetch_all_rows_from_cursor(cursor)

    return {
        str(row[0]).strip().lower(): {
            'id': str(row[0]).strip().lower(),
            'vesselName': row[1],
            'vesselCode': row[2],
            'email': row[3],
        }
        for row in rows
        if row and row[0]
    }


def _fetch_existing_ship_delivery_vessel_ids(notification_sr_no, vessel_ids):
    normalized_vessel_ids = _normalize_uuid_list(vessel_ids)
    if not normalized_vessel_ids:
        return set()

    values_clause = ", ".join(["(%s)"] * len(normalized_vessel_ids))
    sql = f"""
        SET NOCOUNT ON;

        DECLARE @target_vessels TABLE (
            vessel_id NVARCHAR(36) PRIMARY KEY
        );

        INSERT INTO @target_vessels (vessel_id)
        VALUES {values_clause};

        SELECT DISTINCT
            LOWER(LTRIM(RTRIM(CONVERT(VARCHAR(36), ship_notification.vessel_id)))) AS vessel_id
        FROM msc_ship_notification ship_notification
        INNER JOIN @target_vessels target
            ON LOWER(LTRIM(RTRIM(CONVERT(VARCHAR(36), ship_notification.vessel_id)))) = target.vessel_id
        WHERE ship_notification.msc_sr_no_ = %s;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [value.lower() for value in normalized_vessel_ids] + [notification_sr_no])
        rows = _fetch_all_rows_from_cursor(cursor)

    return set(_normalize_uuid_list([row[0] for row in rows]))


def _safe_get_lookup_name_by_id(model_class, raw_id, fallback_value=None):
    if raw_id is None:
        return fallback_value

    normalized_value = _clean_uuid_string(raw_id)
    if not normalized_value:
        stripped_value = str(raw_id).strip()
        if stripped_value:
            return stripped_value if fallback_value is None else fallback_value
        return fallback_value

    try:
        table_name = model_class._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT TOP 1 name FROM {table_name} WHERE id = CAST(%s AS UNIQUEIDENTIFIER)",
                [normalized_value]
            )
            row = cursor.fetchone()

        resolved_name = row[0] if row else None
        if resolved_name and str(resolved_name).strip():
            return str(resolved_name).strip()
    except Exception as exc:
        print(f"_safe_get_lookup_name_by_id: Failed to resolve {model_class.__name__} for value '{normalized_value}': {exc}")

    return normalized_value if fallback_value is None else fallback_value


def _infer_circular_type_name_from_sr_no(sr_no):
    sr_no_parts = str(sr_no or "").split('/')
    if len(sr_no_parts) >= 2:
        return sr_no_parts[1]
    return None


def _normalize_circular_type_name(doc_type_name):
    raw_value = str(doc_type_name or "").strip().lower()
    return "".join(ch for ch in raw_value if ch.isalnum())


def _resolve_circular_type_label(doc_type_name):
    normalized_type = _normalize_circular_type_name(doc_type_name)
    if not normalized_type or normalized_type == "all":
        return None
    if normalized_type.startswith("workinstruction"):
        return "Work Instruction"
    if normalized_type == "circular":
        return "Circular"
    if normalized_type == "alert":
        return "Alert"
    return str(doc_type_name or "").strip()


def _should_stack_footer_metadata(doc_type_name):
    return _normalize_circular_type_name(doc_type_name) == "workinstruction"


def _acquire_circular_sr_lock(cursor, prefix):
    lock_resource = f"circular-sr:{hashlib.sha256(prefix.encode('utf-8')).hexdigest()}"
    cursor.execute(
        """
        DECLARE @lock_result INT;
        EXEC @lock_result = sp_getapplock
            @Resource = %s,
            @LockMode = 'Exclusive',
            @LockOwner = 'Transaction',
            @LockTimeout = %s;
        SELECT @lock_result;
        """,
        [lock_resource, CIRCULAR_SR_LOCK_TIMEOUT_MS]
    )
    lock_row = cursor.fetchone()
    lock_result = lock_row[0] if lock_row else -999
    if lock_result < 0:
        raise RuntimeError(
            f"Unable to acquire circular SR lock for prefix '{prefix}'. SQL result: {lock_result}"
        )


def _generate_unique_circular_sr_no(cursor, doc_type_display_name, dept_display_name, created_at):
    doc_type_segment = (doc_type_display_name or 'Unknown').strip() or 'Unknown'
    dept_segment = (dept_display_name or 'Unknown Dept').strip() or 'Unknown Dept'
    display_prefix = f"KSM/{doc_type_segment}/{dept_segment}/{created_at.year}-"
    type_prefix = f"KSM/{doc_type_segment}/"
    type_sequence_lock_key = _normalize_circular_type_name(doc_type_segment) or doc_type_segment.lower()

    # The visible SR format includes department/year for readability, but the
    # numeric serial is global per document type and must continue across years.
    _acquire_circular_sr_lock(cursor, f"type-seq:{type_sequence_lock_key}")

    cursor.execute(
        """
        SELECT MAX(
            CASE
                WHEN CHARINDEX('-', sr_no) > 0
                THEN TRY_CAST(RIGHT(sr_no, CHARINDEX('-', REVERSE(sr_no)) - 1) AS INT)
                ELSE NULL
            END
        )
        FROM msc_data WITH (UPDLOCK, HOLDLOCK)
        WHERE sr_no IS NOT NULL
          AND LEFT(sr_no, LEN(%s)) = %s
          AND NOT (
              (
                  publish_status = 0
                  AND ISNULL(is_deleted, 0) = 1
              )
              OR publish_status = 3
          )
        """,
        [type_prefix, type_prefix]
    )
    max_row = cursor.fetchone()
    next_serial = (max_row[0] or 0) + 1

    while True:
        candidate_sr_no = f"{display_prefix}{next_serial:04d}"
        cursor.execute(
            """
            SELECT COUNT(1)
            FROM msc_data WITH (UPDLOCK, HOLDLOCK)
            WHERE sr_no IS NOT NULL
              AND LEFT(sr_no, LEN(%s)) = %s
              AND (
                    CASE
                        WHEN CHARINDEX('-', sr_no) > 0
                        THEN TRY_CAST(RIGHT(sr_no, CHARINDEX('-', REVERSE(sr_no)) - 1) AS INT)
                        ELSE NULL
                    END
                  ) = %s
              AND NOT (
                  (
                      publish_status = 0
                      AND ISNULL(is_deleted, 0) = 1
                  )
                  OR publish_status = 3
              )
            """,
            [type_prefix, type_prefix, next_serial]
        )
        existing_row = cursor.fetchone()
        if not existing_row or existing_row[0] == 0:
            return candidate_sr_no
        next_serial += 1


def _draw_pdf_supersede_notice(canvas_obj, margin, ref_date_y, supersede_reference):
    if not supersede_reference:
        return ref_date_y - 35

    supersede_y = ref_date_y - 18
    canvas_obj.setFillColor(red)
    canvas_obj.setFont(PDF_FONT_NAME, PDF_META_FONT_SIZE)
    canvas_obj.drawString(
        margin,
        supersede_y,
        f"Supersedes {supersede_reference}"
    )
    canvas_obj.setFillColor(black)
    return supersede_y - 28


def _draw_pdf_subject_block(canvas_obj, width, margin, subject_y, subject_text):
    subject_value = subject_text or ""
    subject_lines = _wrap_text_simple(
        canvas_obj,
        f"SUBJECT: {subject_value}",
        width - (2 * margin),
        PDF_FONT_NAME,
        PDF_SUBJECT_FONT_SIZE
    )

    canvas_obj.setFont(PDF_FONT_NAME, PDF_SUBJECT_FONT_SIZE)
    current_y = subject_y
    for line in subject_lines:
        canvas_obj.drawString(margin, current_y, line)
        current_y -= PDF_SUBJECT_LINE_HEIGHT

    return current_y


def _draw_fixed_footer(
    canvas_obj,
    width,
    margin,
    left_text,
    center_text,
    right_text,
    stack_metadata_below_left=False,
):
    canvas_obj.setStrokeColor(navy)
    canvas_obj.line(margin, PDF_FIXED_FOOTER_LINE_Y, width - margin, PDF_FIXED_FOOTER_LINE_Y)
    canvas_obj.setStrokeColor(black)
    canvas_obj.setFillColor(black)
    canvas_obj.setFont(PDF_FONT_NAME, PDF_FOOTER_FONT_SIZE)

    metadata_lines = []
    if center_text:
        if isinstance(center_text, (list, tuple)):
            metadata_lines = [line for line in center_text if line]
        else:
            metadata_lines = [center_text]

    left_text_y = PDF_FIXED_FOOTER_Y + 8 if stack_metadata_below_left and metadata_lines else PDF_FIXED_FOOTER_Y
    canvas_obj.drawString(margin, left_text_y, left_text)

    if metadata_lines:
        if stack_metadata_below_left:
            for index, line in enumerate(metadata_lines):
                canvas_obj.drawString(margin, left_text_y - ((index + 1) * 10), line)
        elif len(metadata_lines) == 1:
            canvas_obj.drawCentredString(width / 2, PDF_FIXED_FOOTER_Y, metadata_lines[0])
        else:
            first_line_y = PDF_FIXED_FOOTER_Y + 2
            for index, line in enumerate(metadata_lines):
                canvas_obj.drawCentredString(width / 2, first_line_y - (index * 10), line)

    if right_text:
        canvas_obj.drawRightString(width - margin, left_text_y, right_text)


def _merge_footer_onto_pdf_page(page_obj, margin, left_text, center_text, right_text):
    overlay_buffer = io.BytesIO()
    page_width = float(page_obj.mediabox.width)
    page_height = float(page_obj.mediabox.height)
    overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
    _draw_fixed_footer(overlay_canvas, page_width, margin, left_text, center_text, right_text)
    overlay_canvas.save()
    overlay_buffer.seek(0)
    page_obj.merge_page(PdfReader(overlay_buffer).pages[0])
    return page_obj


def _get_circular_attachment_paths(formatted_id):
    media_path = os.path.join(settings.MEDIA_ROOT, 'circular', 'attachments')
    safe_formatted_id = formatted_id.replace('/', '_')
    merged_path = os.path.join(media_path, f"merged_{safe_formatted_id}.pdf")
    original_path = os.path.join(media_path, f"original_{safe_formatted_id}.pdf")
    return media_path, merged_path, original_path


def _get_original_attachment_copy_path(merged_attachment_path):
    if not merged_attachment_path:
        return None

    directory, filename = os.path.split(merged_attachment_path)
    if filename.startswith("merged_"):
        return os.path.join(directory, f"original_{filename[len('merged_'):]}")

    return None


def _is_pdf_attachment_upload(uploaded_file):
    file_name = str(getattr(uploaded_file, "name", "") or "").strip().lower()
    content_type = str(getattr(uploaded_file, "content_type", "") or "").strip().lower()
    return file_name.endswith(".pdf") or content_type in {"application/pdf", "application/x-pdf"}


def _extract_uploaded_pdf_attachments_from_request_files(request_files):
    if request_files is None:
        return []

    uploaded_files = list(request_files.getlist("attachment") or [])
    alternate_field_files = list(request_files.getlist("attachments") or [])
    if alternate_field_files:
        uploaded_files.extend(alternate_field_files)

    deduped_uploaded_files = []
    seen_markers = set()
    for uploaded_file in uploaded_files:
        marker = id(uploaded_file)
        if marker in seen_markers:
            continue
        seen_markers.add(marker)
        deduped_uploaded_files.append(uploaded_file)

    if len(deduped_uploaded_files) > MAX_CIRCULAR_ATTACHMENT_FILES:
        raise CircularAttachmentValidationError(
            f"You can upload a maximum of {MAX_CIRCULAR_ATTACHMENT_FILES} PDF files."
        )

    invalid_file_names = [
        str(getattr(uploaded_file, "name", "Unknown file"))
        for uploaded_file in deduped_uploaded_files
        if not _is_pdf_attachment_upload(uploaded_file)
    ]
    if invalid_file_names:
        raise CircularAttachmentValidationError(
            "Only PDF attachments are allowed. Invalid files: "
            + ", ".join(invalid_file_names)
        )

    return deduped_uploaded_files


def _merge_uploaded_pdf_bytes(uploaded_file_bytes_list):
    normalized_bytes_list = [file_bytes for file_bytes in (uploaded_file_bytes_list or []) if file_bytes is not None]
    if not normalized_bytes_list:
        return None

    merged_writer = PdfWriter()
    for file_bytes in normalized_bytes_list:
        uploaded_pdf_reader = _open_uploaded_pdf_reader(io.BytesIO(file_bytes))
        for page in uploaded_pdf_reader.pages:
            merged_writer.add_page(page)

    merged_buffer = io.BytesIO()
    merged_writer.write(merged_buffer)
    merged_buffer.seek(0)
    return merged_buffer.getvalue()


def _store_circular_generated_pdf(formatted_id, pdf_data, uploaded_file_bytes_list=None):
    uploaded_file_streams = [
        io.BytesIO(file_bytes)
        for file_bytes in (uploaded_file_bytes_list or [])
        if file_bytes is not None
    ]
    merged_pdf_buffer = generate_pdf_with_cover_and_original(
        uploaded_file_streams,
        pdf_data,
    )

    media_path, merged_filepath, original_filepath = _get_circular_attachment_paths(formatted_id)
    os.makedirs(media_path, exist_ok=True)

    with open(merged_filepath, 'wb') as merged_file:
        merged_file.write(merged_pdf_buffer.getvalue())

    original_attachments_pdf_bytes = _merge_uploaded_pdf_bytes(uploaded_file_bytes_list)
    if original_attachments_pdf_bytes is not None:
        with open(original_filepath, 'wb') as original_file:
            original_file.write(original_attachments_pdf_bytes)

    return os.path.basename(merged_filepath), merged_filepath


def _open_uploaded_pdf_reader(uploaded_file):
    if uploaded_file is None:
        return None

    try:
        pdf_reader = PdfReader(uploaded_file)
    except DependencyError as exc:
        raise CircularAttachmentValidationError(
            "The uploaded PDF uses encryption that cannot be processed by the current server. "
            "Please save or print it as an unlocked PDF and upload it again."
        ) from exc
    except PdfReadError as exc:
        raise CircularAttachmentValidationError(
            "The uploaded PDF could not be read. Please upload a valid, unlocked PDF file."
        ) from exc

    if getattr(pdf_reader, "is_encrypted", False):
        try:
            decrypt_result = pdf_reader.decrypt("")
        except DependencyError as exc:
            raise CircularAttachmentValidationError(
                "The uploaded PDF is encrypted and cannot be processed by the current server. "
                "Please save or print it as an unlocked PDF and upload it again."
            ) from exc
        except Exception:
            decrypt_result = 0

        if not decrypt_result:
            raise CircularAttachmentValidationError(
                "The uploaded PDF is password-protected. Please save or print it as an unlocked PDF and upload it again."
            )

    return pdf_reader


def _is_system_generated_circular_page(page_obj, sr_no):
    try:
        page_text = " ".join((page_obj.extract_text() or "").split())
    except Exception as exc:
        print(f"_is_system_generated_circular_page: text extraction failed for {sr_no}: {exc}")
        return False

    if not page_text:
        return False

    return (
        PDF_HEADER_TEXT in page_text and
        f"Sr. No: {sr_no}" in page_text and
        any(marker in page_text for marker in ("Created By:", "Approved By:", "Created At:", "Approved At:", "Edited At:"))
    )


def _count_leading_system_generated_pages(pdf_reader, sr_no):
    generated_page_count = 0

    for page in pdf_reader.pages:
        if _is_system_generated_circular_page(page, sr_no):
            generated_page_count += 1
        else:
            break

    return generated_page_count


def _resolve_attachment_reader_for_merge(merged_attachment_path, sr_no):
    original_attachment_copy_path = _get_original_attachment_copy_path(merged_attachment_path)
    if original_attachment_copy_path and os.path.exists(original_attachment_copy_path):
        try:
            print(f"_resolve_attachment_reader_for_merge: Using preserved original attachment {original_attachment_copy_path}")
            return PdfReader(original_attachment_copy_path), 0
        except Exception as exc:
            print(f"_resolve_attachment_reader_for_merge: Failed to read preserved original attachment {original_attachment_copy_path}: {exc}")

    merged_reader = PdfReader(merged_attachment_path)
    attachment_start_index = _count_leading_system_generated_pages(merged_reader, sr_no)
    print(
        f"_resolve_attachment_reader_for_merge: Falling back to merged PDF split for {sr_no}. "
        f"Attachment pages start at index {attachment_start_index}."
    )
    return merged_reader, attachment_start_index


def _draw_pdf_continuation_header(c, width, height, margin, logo_path, logo_width, logo_height, document_id, page_number):
    divider_y = draw_pdf_header(
        c, width, height, margin,
        logo_path, logo_width, logo_height
    )

    c.setFont(PDF_FONT_NAME, PDF_META_FONT_SIZE)
    c.drawString(margin, divider_y - 20, f"Document: {document_id}")
    c.drawRightString(width - margin, divider_y - 20, f"Page {page_number}")

    c.setStrokeColor(navy)
    c.line(margin, divider_y - 40, width - margin, divider_y - 40)
    c.setStrokeColor(black)

    return divider_y - 55








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
        dept_id_string = clean_uuid_string(request.POST.get('department'), 'department')
        print(f"create_notification: Received department ID string from frontend: {dept_id_string}")

        if not doc_type_uuid_verified or not dept_id_string: # Check for the string, not an integer
            print("create_notification: Missing type or department, returning 400")
            return JsonResponse({'error': 'type and department are required'}, status=400)

        # Resolve the department label that becomes part of the SR prefix.
        dept_display_name = _get_department_display_name_for_sr_no(dept_id_string)
        print(f"create_notification: Mapped department ID {dept_id_string} to display name: {dept_display_name}")

        now = django_timezone.now()
        current_year = now.year
        print(f"create_notification: dept_display_name: {dept_display_name}, current_year: {current_year}")

        # --- Get created_by ---
        created_by_employee_id = request.POST.get('created_by')
        print(f"create_notification: created_by: {created_by_employee_id}")

        # --- Get Initial Publish Status ---
        initial_publish_status = int(request.POST.get('publish_status', 0))
        print(f"create_notification: publish_status: {initial_publish_status}")

        existing_pending_draft = _get_existing_active_draft_for_creator_and_type(
            created_by_employee_id,
            doc_type_uuid_verified,
            doc_type_display_name,
        )
        if existing_pending_draft:
            conflict_message = _build_pending_draft_conflict_message(doc_type_display_name)
            print(
                "create_notification: Blocking new notification because an active draft already exists "
                f"for created_by={created_by_employee_id}, msc_type={doc_type_uuid_verified}, "
                f"draft_sr_no={existing_pending_draft.sr_no}"
            )
            return JsonResponse(
                {
                    'error': conflict_message,
                    'draft_id': str(existing_pending_draft.id),
                    'draft_sr_no': existing_pending_draft.sr_no,
                },
                status=409,
            )
        
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

        # --- Get and clean Vessel IDs ---
        received_vessel_ids = request.POST.getlist('vessel_ids')
        cleaned_vessel_ids = []
        for v_id in received_vessel_ids:
            cleaned = clean_uuid_string(v_id, 'vessel_id')
            if cleaned:
                cleaned_vessel_ids.append(cleaned)
        
        vessel_id_str = ', '.join(cleaned_vessel_ids) if cleaned_vessel_ids else None
        print(f"create_notification: vessel_ids: {vessel_id_str}")

        received_title = request.POST.get('title', '')   
        created_at_str = now.strftime('%Y-%m-%d %H:%M:%S')
        published_on_str = published_on_datetime.strftime('%Y-%m-%d %H:%M:%S') if published_on_datetime else None
        notification_id = 'unknown'
        formatted_id = None

        with transaction.atomic():
            print("create_notification: Generating SR No under transaction lock...")
            with connection.cursor() as cursor:
                formatted_id = _generate_unique_circular_sr_no(
                    cursor,
                    doc_type_display_name,
                    dept_display_name,
                    now
                )
            print(f"create_notification: Generated SR No: {formatted_id}")

            try:
                uploaded_files = _extract_uploaded_pdf_attachments_from_request_files(request.FILES)
            except CircularAttachmentValidationError as exc:
                print(f"create_notification: Attachment validation failed - {exc}")
                return JsonResponse({'error': str(exc)}, status=400)

            uploaded_file_bytes_list = []
            if uploaded_files:
                print(f"create_notification: Processing {len(uploaded_files)} file attachment(s)...")
                uploaded_file_bytes_list = [uploaded_file.read() for uploaded_file in uploaded_files]
            else:
                print("create_notification: No attachment uploaded. Generating circular PDF from form content only.")

            pdf_data = {
                'title': request.POST.get('title', ''),
                'body': request.POST.get('body', ''),
                'doc_type_name': doc_type_display_name,
                'formatted_id': formatted_id,
                'current_date': now.strftime('%d-%m-%Y'),
                'superseding_old_notification_sr_no': superseding_old_notification_sr_no,
                'created_by_employee_id': created_by_employee_id,
            }

            try:
                attachment_name, attachment_path = _store_circular_generated_pdf(
                    formatted_id,
                    pdf_data,
                    uploaded_file_bytes_list=uploaded_file_bytes_list,
                )
            except CircularAttachmentValidationError as exc:
                print(f"create_notification: Attachment validation failed - {exc}")
                return JsonResponse({'error': str(exc)}, status=400)
            print(f"create_notification: Generated circular PDF saved at {attachment_path}")

            print("create_notification: Creating MscData record using raw SQL...")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO msc_data (
                        sr_no, msc_type, dept, category, sub_category, second_sub_category,
                        title, office_instructions, hashtags, created_by, created_at,
                        publish_status, published_by, published_on, is_active, is_deleted,
                        priority, attachment_name, attachment_path, vessel_id
                    )
                    OUTPUT INSERTED.id
                    VALUES (
                        %s,
                        CAST(%s AS UNIQUEIDENTIFIER),
                        %s, %s,
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
                        doc_type_uuid_verified,
                        dept_id_string,
                        request.POST.get('category'),
                        sub_cat_uuid_verified,
                        second_sub_cat_uuid_verified,
                        received_title,
                        body,
                        request.POST.get('hashtags'),
                        created_by_employee_id,
                        created_at_str,
                        initial_publish_status,
                        published_by_id,
                        published_on_str,
                        True,
                        False,
                        priority_uuid_verified,
                        attachment_name,
                        attachment_path,
                        vessel_id_str
                    ]
                )
                inserted_row = cursor.fetchone()
                notification_id = inserted_row[0] if inserted_row else 'unknown'
            print(f"create_notification: Record inserted - SR No: {formatted_id}")

            if initial_publish_status == 0:
                transaction.on_commit(
                    lambda sr_no=formatted_id, circular_title=received_title, creator_id=created_by_employee_id, circular_id=notification_id, type_name=doc_type_display_name: notify_circular_created(
                        sr_no=sr_no,
                        title=circular_title,
                        creator_employee_id=creator_id,
                        notification_id=str(circular_id) if circular_id else None,
                        doc_type_name=type_name,
                    )
                )
            elif initial_publish_status == 1:
                transaction.on_commit(
                    lambda sr_no=formatted_id, circular_title=received_title, creator_id=created_by_employee_id, circular_id=notification_id, type_name=doc_type_display_name: notify_circular_pending_approval(
                        sr_no=sr_no,
                        title=circular_title,
                        creator_employee_id=creator_id,
                        notification_id=str(circular_id) if circular_id else None,
                        doc_type_name=type_name,
                    )
                )
            elif initial_publish_status == 2:
                transaction.on_commit(
                    lambda sr_no=formatted_id, circular_title=received_title, creator_id=created_by_employee_id, circular_id=notification_id, type_name=doc_type_display_name: notify_circular_approved(
                        sr_no=sr_no,
                        title=circular_title,
                        creator_employee_id=creator_id,
                        notification_id=str(circular_id) if circular_id else None,
                        doc_type_name=type_name,
                    )
                )

            if superseding_old_notification_sr_no:
                print("create_notification: Finalizing supersede...")
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            UPDATE msc_data
                            SET is_superseeded = 1, superseeded_by = %s
                            WHERE sr_no = %s AND is_deleted = 0
                            """,
                            [formatted_id, superseding_old_notification_sr_no]
                        )
                        rows_updated = cursor.rowcount
                    if rows_updated == 0:
                        raise ValueError(
                            f"Superseded circular '{superseding_old_notification_sr_no}' was not found."
                        )
                    print("create_notification: Supersede updated")
                except Exception as e:
                    print(f"create_notification: Supersede error: {e}")
                    raise

            if initial_publish_status == 2:
                print("create_notification: Creating delivery records...")
                try:
                    hrm_records_for_dept = HRM501.objects.filter(department_name=dept_id_string)
                    hrm_ids_for_dept = [rec.id for rec in hrm_records_for_dept]

                    if hrm_ids_for_dept:
                        final_crew_list_for_dept = FinalCrewList.objects.filter(Crew_ref_id__in=hrm_ids_for_dept)
                        final_crew_ids_for_dept = [crew.CrewID for crew in final_crew_list_for_dept]

                        relevant_final_crew_ids = _filter_crew_ids_by_allowed_status(final_crew_ids_for_dept)
                        if cleaned_vessel_ids:
                            try:
                                uuid_vessel_ids = [uuid.UUID(v_id) for v_id in cleaned_vessel_ids]
                                onboardings_for_vessels = CrewOnboardingHistory.objects.filter(
                                    CrewID__in=relevant_final_crew_ids,
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


def generate_pdf_with_cover_and_original(uploaded_files, notification_data):
    """
    Generate PDF with cover page + multi-page content, then merge with uploaded PDF(s).
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
    c.setFont(PDF_FONT_NAME, PDF_TITLE_FONT_SIZE)
    title_y = divider_y - 45
    dynamic_title_text = _get_dynamic_title(notification_data['doc_type_name'])
    c.drawCentredString(width / 2, title_y, dynamic_title_text)

    # -------------------------------
    # Serial + Date
    # -------------------------------
    c.setFont(PDF_FONT_NAME, PDF_META_FONT_SIZE)
    ref_date_y = title_y - 30
    c.drawString(margin, ref_date_y, f"Serial_no. : {notification_data['formatted_id']}")
    c.drawRightString(width - margin, ref_date_y, f"Date: {notification_data['current_date']}")

    # Subject
    subject_y = _draw_pdf_supersede_notice(
        c,
        margin,
        ref_date_y,
        notification_data.get('superseding_old_notification_sr_no')
    )
    subject_bottom_y = _draw_pdf_subject_block(
        c,
        width,
        margin,
        subject_y,
        notification_data['title']
    )

    # ===============================
    # BODY CONTENT
    # ===============================
    c.setFont(PDF_FONT_NAME, PDF_BODY_FONT_SIZE)
    body_start_y = subject_bottom_y - 20
    y_position = body_start_y

    body_lines = _wrap_text_simple(
        c, notification_data['body'],
        width - 2 * margin, PDF_FONT_NAME, PDF_BODY_FONT_SIZE
    )

    page_number = 1
    last_body_y_position = y_position

    for line in body_lines:
        if y_position > PDF_BODY_STOP_Y:
            c.drawString(margin, y_position, line)
            y_position -= PDF_LINE_HEIGHT
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
            y_position = _draw_pdf_continuation_header(
                c, width, height, margin,
                logo_path, logo_width, logo_height,
                notification_data['formatted_id'],
                page_number
            )
            c.setFont(PDF_FONT_NAME, PDF_BODY_FONT_SIZE)
            c.drawString(margin, y_position, line)
            y_position -= PDF_LINE_HEIGHT
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

    normalized_uploaded_files = []
    if uploaded_files is None:
        normalized_uploaded_files = []
    elif isinstance(uploaded_files, (list, tuple)):
        normalized_uploaded_files = list(uploaded_files)
    else:
        normalized_uploaded_files = [uploaded_files]

    for uploaded_file in normalized_uploaded_files:
        original_pdf = _open_uploaded_pdf_reader(uploaded_file)
        if original_pdf is None:
            continue
        for page in original_pdf.pages:
            writer.add_page(page)

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
    c.setFont(PDF_FONT_NAME, PDF_HEADER_FONT_SIZE)
    c.setFillColor(navy)
    text_baseline_y = height - margin
    text_center_y = text_baseline_y - (PDF_HEADER_FONT_SIZE / 2)
    logo_y = text_center_y - (logo_height / 2)
    text_width = c.stringWidth(PDF_HEADER_TEXT, PDF_FONT_NAME, PDF_HEADER_FONT_SIZE)
    text_start_x = max(margin + logo_width + PDF_HEADER_GAP, (width - text_width) / 2)

    try:
        c.drawImage(logo_path, margin, logo_y,
                    width=logo_width, height=logo_height, mask='auto')
        company_x = text_start_x
    except:
        company_x = max(margin, (width - text_width) / 2)

    c.drawString(company_x, text_baseline_y, PDF_HEADER_TEXT)
    c.setFillColor(black)

    divider_y = text_baseline_y - 40
    c.setStrokeColor(navy)
    c.line(margin, divider_y, width - margin, divider_y)
    c.setStrokeColor(black)

    return divider_y

def _add_footer_to_page(canvas_obj, width, margin, notification_data, page_number, last_body_y):
    created_by_part = f"Created By: {notification_data.get('created_by_employee_id', 'Unknown User')}"
    _draw_fixed_footer(
        canvas_obj,
        width,
        margin,
        f"Sr. No: {notification_data['formatted_id']}",
        created_by_part,
        f"Created At: {notification_data['current_date']} | Page {page_number}",
        stack_metadata_below_left=_should_stack_footer_metadata(notification_data.get('doc_type_name')),
    )



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
            'dept_name': _get_department_master_name(n.dept),
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
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TOP 1
                    id, sr_no, msc_type, dept, category, sub_category, second_sub_category,
                    office_instructions, hashtags, created_by, created_at, publish_status,
                    publish_comment, published_by, published_on, is_superseeded,
                    superseeded_by, is_active, is_deleted, priority,
                    attachment_name, attachment_path
                FROM msc_data
                WHERE sr_no = %s AND is_deleted = 0
                ORDER BY created_at DESC, id DESC
                """,
                [sr_no]
            )
            row = cursor.fetchone()
            columns = [column[0] for column in cursor.description] if cursor.description else []

        if not row:
            print(f"get_notification_details: Notification with SR No {sr_no} not found or is deleted.")
            return JsonResponse({'error': f'Notification with SR No {sr_no} not found or is deleted.'}, status=404)

        notification = dict(zip(columns, row))
        print(f"get_notification_details: Found notification. ID: {notification.get('id')}, SR No: {notification.get('sr_no')}")

        inferred_type_name = _infer_circular_type_name_from_sr_no(notification.get('sr_no'))
        resolved_type_name = _safe_get_lookup_name_by_id(
            MscType,
            notification.get('msc_type'),
            inferred_type_name
        ) or inferred_type_name

        notification_data = {
            'id': str(notification.get('id')) if notification.get('id') is not None else None,
            'sr_no': notification.get('sr_no'),
            'msc_type': resolved_type_name,
            'dept': str(notification.get('dept')) if notification.get('dept') is not None else None,
            'dept_name': _get_department_master_name(notification.get('dept')),
            'category': notification.get('category'),
            'sub_category': _safe_get_lookup_name_by_id(MscSubCat, notification.get('sub_category')),
            'second_sub_category': _safe_get_lookup_name_by_id(Msc2ndSubCat, notification.get('second_sub_category')),
            'office_instructions': notification.get('office_instructions'),
            'hashtags': notification.get('hashtags'),
            'created_by': notification.get('created_by'),
            'created_at': notification.get('created_at').isoformat() if notification.get('created_at') else None,
            'publish_status': notification.get('publish_status'),
            'publish_comment': notification.get('publish_comment'),
            'published_by': notification.get('published_by'),
            'published_on': notification.get('published_on').isoformat() if notification.get('published_on') else None,
            'is_superseeded': notification.get('is_superseeded'),
            'superseeded_by': notification.get('superseeded_by'),
            'is_active': notification.get('is_active'),
            'is_deleted': notification.get('is_deleted'),
            'priority': _safe_get_lookup_name_by_id(MscPriority, notification.get('priority')),
            'attachment_name': notification.get('attachment_name'),
            'attachment_path': notification.get('attachment_path'),
            'attachment_url': f"{settings.MEDIA_URL}circular/attachments/{notification.get('attachment_name')}" if notification.get('attachment_name') else None,
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
            'sub_category', 'second_sub_category', 'title', 'office_instructions',
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
        allow_repeat_approval = bool(
            data.get('allow_repeat_approval') or data.get('resend_approval')
        )

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
                        published_on_datetime = django_timezone.make_aware(published_on_datetime, datetime_timezone.utc)
                except ValueError as e:
                    print(f"⚠️ Warning: Invalid published_on format '{published_on_iso_string}': {e}")
                    published_on_datetime = django_timezone.now()
            else:
                published_on_datetime = django_timezone.now()

            print(f"   Setting published_by to: {published_by_id}")
            print(f"   Setting published_on to: {published_on_datetime}")

        # === Fetch Notification for Department Info (for PDF update) ===
        # This is still needed for the PDF cover generation logic below
        notification_for_dept = _get_latest_notification_record_by_sr_no(notification_sr_no)
        if not notification_for_dept:
            print(f"update_notification_status: Notification with SR No {notification_sr_no} not found.")
            return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)

        scope_error = _validate_circular_approval_scope(notification_for_dept, data)
        if scope_error is not None:
            return scope_error

        is_repeat_approval = (
            allow_repeat_approval
            and new_status == 2
            and notification_for_dept.publish_status == 2
        )

        if notification_for_dept.publish_status == new_status and not is_repeat_approval:
            already_message = 'Notification already approved.' if new_status == 2 else 'Notification already rejected.'
            print(f"update_notification_status: {already_message} Skipping duplicate status update for {notification_sr_no}.")
            return JsonResponse({'success': True, 'message': already_message, 'already_processed': True})

        if is_repeat_approval:
            print(
                f"update_notification_status: Re-running approval flow for already approved notification "
                f"{notification_sr_no}."
            )

        dept_name_for_crews = _get_department_master_name(notification_for_dept.dept) or 'Unknown'
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
                notification_to_update = notification_for_dept
                if not notification_to_update.attachment_path:
                    print(f"update_notification_status: Notification {notification_sr_no} has no attachment path, skipping PDF cover update.")
                    # Continue with the status update even if PDF update fails
                else:
                    print(f"update_notification_status: Found notification with attachment path: {notification_to_update.attachment_path}")
                    print("update_notification_status: Resolving attachment PDF for cover replacement...")

                    attachment_pdf_reader, attachment_start_index = _resolve_attachment_reader_for_merge(
                        notification_to_update.attachment_path,
                        notification_to_update.sr_no
                    )

                    # 2. Generate the UPDATED COVER PAGE (with approval info and body) - NOW GENERATE ALL PAGES
                    print("update_notification_status: Generating updated cover page with approval info and body...")

                    # Create a new PDF buffer for the NEWLY GENERATED PAGES (cover + body text + footer)
                    cover_buffer = io.BytesIO()
                    c = canvas.Canvas(cover_buffer, pagesize=letter)
                    width, height = letter
                    margin = 50
                    
                    page_number = 1  # Track page number for headers
                    logo_path = os.path.join(settings.BASE_DIR, "static", "ksm-logo.png")
                    logo_width = 30
                    logo_height = 50

                    # --- Page 1: Header and Title ---
                    # Company Header (with Logo)
                    divider_y = draw_pdf_header(
                        c, width, height, margin,
                        logo_path, logo_width, logo_height
                    )



                    # Document Title
                    c.setFont(PDF_FONT_NAME, PDF_TITLE_FONT_SIZE)
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
                    c.setFont(PDF_FONT_NAME, PDF_META_FONT_SIZE)
                    ref_date_y = title_y - 30
                    c.drawString(margin, ref_date_y, f"Serial_no. : {notification_to_update.sr_no}")
                    c.drawRightString(width - margin, ref_date_y,
                                    f"Date: {notification_to_update.created_at.strftime('%d-%m-%Y') if notification_to_update.created_at else 'N/A'}")


                    # Subject
                    subject_y = _draw_pdf_supersede_notice(
                        c,
                        margin,
                        ref_date_y,
                        notification_to_update.superseeded_by
                    )
                    subject_bottom_y = _draw_pdf_subject_block(
                        c,
                        width,
                        margin,
                        subject_y,
                        notification_to_update.title or notification_to_update.sr_no
                    )

                    # Office Instructions (Main Body Content)
                    print("--- START: Office Instructions Generation (Update/Approval) ---")
                    c.setFont(PDF_FONT_NAME, PDF_BODY_FONT_SIZE)
                    body_start_y = subject_bottom_y - 20
                    y_position = body_start_y

                    body_text = notification_to_update.office_instructions or ""
                    print(f"update_notification_status: Adding body content: {body_text[:50]}...") # Log first 50 chars

                    if body_text:
                        # Prepare the body text for multi-page handling
                        body_lines = _wrap_text_simple(c, body_text, width - 2 * margin, PDF_FONT_NAME, PDF_BODY_FONT_SIZE)
                        
                        # Variable to track the last Y position of body text on each page
                        last_body_y_position = y_position

                        for line in body_lines:
                            if y_position > PDF_BODY_STOP_Y:
                                c.drawString(margin, y_position, line)
                                y_position -= PDF_LINE_HEIGHT
                                last_body_y_position = y_position
                            else:
                                _add_footer_to_page_update(c, width, margin, notification_to_update, page_number, last_body_y_position, published_by_id, published_on_datetime)

                                c.showPage()
                                page_number += 1

                                y_position = _draw_pdf_continuation_header(
                                    c, width, height, margin,
                                    logo_path, logo_width, logo_height,
                                    notification_to_update.sr_no,
                                    page_number
                                )
                                c.setFont(PDF_FONT_NAME, PDF_BODY_FONT_SIZE)
                                c.drawString(margin, y_position, line)
                                y_position -= PDF_LINE_HEIGHT
                                last_body_y_position = y_position

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

                    print(
                        f"update_notification_status: Appending attachment pages from index "
                        f"{attachment_start_index} without modifying the attachment PDF..."
                    )
                    for i in range(attachment_start_index, len(attachment_pdf_reader.pages)):
                        merger.add_page(attachment_pdf_reader.pages[i])

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

        resolved_doc_type_name = (
            _infer_circular_type_name_from_sr_no(notification_for_dept.sr_no)
            or _safe_get_lookup_name_by_id(MscType, notification_for_dept.msc_type_id, 'Circular')
            or 'Circular'
        )

        if new_status == 2 and not is_repeat_approval:
            notify_circular_approved(
                sr_no=notification_for_dept.sr_no,
                title=notification_for_dept.title,
                creator_employee_id=notification_for_dept.created_by,
                notification_id=str(notification_for_dept.id) if notification_for_dept.id else None,
                doc_type_name=resolved_doc_type_name,
            )
        else:
            notify_circular_rejected(
                sr_no=notification_for_dept.sr_no,
                title=notification_for_dept.title,
                creator_employee_id=notification_for_dept.created_by,
                notification_id=str(notification_for_dept.id) if notification_for_dept.id else None,
                doc_type_name=resolved_doc_type_name,
                comment=comment,
            )

        message = 'Notification approval rerun successfully.' if is_repeat_approval else f'Notification status updated to {new_status}'
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
    created_by_part = f"Created By: {notification_obj.created_by}" if notification_obj.created_by else "Created By: Unknown User"
    approved_by_part = f"Approved By: {published_by_id}" if published_by_id else "Approved By: Pending"
    approved_at_part = f"Approved At: {published_on_datetime.strftime('%d-%m-%Y %H:%M:%S') if published_on_datetime else django_timezone.now().strftime('%d-%m-%Y %H:%M:%S')}"
    _draw_fixed_footer(
        canvas_obj,
        width,
        margin,
        f"Sr. No: {notification_obj.sr_no}",
        [created_by_part, approved_by_part],
        f"{approved_at_part} | Page {page_number}",
        stack_metadata_below_left=_should_stack_footer_metadata(
            _infer_circular_type_name_from_sr_no(notification_obj.sr_no)
        ),
    )


def _build_delivery_status_records(notification_records):
    records = list(notification_records)
    if not records:
        return []

    crew_ids = []
    for record in records:
        crew_id = str(record.crew_id or "").strip()
        if crew_id and crew_id not in crew_ids:
            crew_ids.append(crew_id)

    crew_lookup = {}
    if crew_ids:
        placeholders = ", ".join(["%s"] * len(crew_ids))
        delivery_lookup_sql = f"""
            WITH latest_onboarding AS (
                SELECT
                    coh.CrewID,
                    coh.Vessel,
                    ROW_NUMBER() OVER (
                        PARTITION BY coh.CrewID
                        ORDER BY
                            CASE WHEN ISNULL(coh.is_active, 0) = 1 THEN 0 ELSE 1 END,
                            coh.updated_date DESC,
                            coh.created_date DESC,
                            coh.SignOnDate DESC,
                            coh.id DESC
                    ) AS rn
                FROM Crew_Onboarding_History coh
                WHERE coh.CrewID IN ({placeholders})
                  AND ISNULL(coh.is_deleted, 0) = 0
            ),
            latest_final_crew AS (
                SELECT
                    LTRIM(RTRIM(fcl.CrewID)) AS crew_id,
                    fcl.Crew_Status,
                    ROW_NUMBER() OVER (
                        PARTITION BY LTRIM(RTRIM(fcl.CrewID))
                        ORDER BY
                            CASE WHEN ISNULL(fcl.is_active, 0) = 1 THEN 0 ELSE 1 END,
                            fcl.updated_date DESC,
                            fcl.created_date DESC,
                            fcl.id DESC
                    ) AS rn
                FROM Final_crew_list fcl
                WHERE LTRIM(RTRIM(ISNULL(fcl.CrewID, ''))) IN ({placeholders})
                  AND ISNULL(fcl.is_delete, 0) = 0
            ),
            latest_hrm AS (
                SELECT
                    LTRIM(RTRIM(h.CrewID)) AS crew_id,
                    LTRIM(RTRIM(COALESCE(h.first_name, ''))) AS first_name,
                    LTRIM(RTRIM(COALESCE(h.surname, ''))) AS surname,
                    LTRIM(RTRIM(COALESCE(h.rank_name, ''))) AS raw_rank_name,
                    ROW_NUMBER() OVER (
                        PARTITION BY LTRIM(RTRIM(h.CrewID))
                        ORDER BY
                            CASE WHEN ISNULL(h.is_active, 0) = 1 THEN 0 ELSE 1 END,
                            h.updated_date DESC,
                            h.created_date DESC,
                            h.id DESC
                    ) AS rn
                FROM HRM501 h
                WHERE LTRIM(RTRIM(ISNULL(h.CrewID, ''))) IN ({placeholders})
                  AND ISNULL(h.is_deleted, 0) = 0
            )
            SELECT
                lh.crew_id,
                lh.first_name,
                lh.surname,
                LTRIM(RTRIM(COALESCE(mar.rank_name, lh.raw_rank_name, ''))) AS rank_name,
                mar.rank_level,
                LTRIM(RTRIM(COALESCE(v.VesselName, v.vesselCode, ''))) AS vessel_name,
                LTRIM(RTRIM(COALESCE(cs.CrewStatusName, ''))) AS crew_status_name
            FROM latest_hrm lh
            LEFT JOIN master_applied_rank mar
                ON mar.id = TRY_CONVERT(uniqueidentifier, lh.raw_rank_name)
            LEFT JOIN latest_onboarding lo
                ON lo.CrewID = lh.crew_id
               AND lo.rn = 1
            LEFT JOIN latest_final_crew lfc
                ON lfc.crew_id = lh.crew_id
               AND lfc.rn = 1
            LEFT JOIN VesselData v
                ON v.id = TRY_CONVERT(uniqueidentifier, lo.Vessel)
            LEFT JOIN ksm_marine_live.dbo.CrewStatus cs
                ON cs.id = lfc.Crew_Status
            WHERE lh.rn = 1
        """

        with connection.cursor() as cursor:
            cursor.execute(delivery_lookup_sql, crew_ids + crew_ids + crew_ids)
            for row in cursor.fetchall():
                crew_id, first_name, surname, rank_name, rank_level, vessel_name, crew_status_name = row
                normalized_crew_id = str(crew_id or "").strip()
                if not normalized_crew_id:
                    continue
                full_name = " ".join(
                    part for part in [str(first_name or "").strip(), str(surname or "").strip()] if part
                ) or None
                crew_lookup[normalized_crew_id] = {
                    "resolved_crew_id": normalized_crew_id,
                    "crew_name": full_name,
                    "rank_name": str(rank_name or "").strip() or None,
                    "rank_level": rank_level if rank_level is not None else None,
                    "vessel_name": str(vessel_name or "").strip() or None,
                    "crew_status_name": str(crew_status_name or "").strip() or None,
                }

    delivery_records_by_crew = {}
    for record in records:
        raw_crew_id = str(record.crew_id or "").strip()
        lookup_row = crew_lookup.get(raw_crew_id, {})
        dedupe_key = lookup_row.get("resolved_crew_id") or raw_crew_id or str(uuid.uuid4())
        normalized_record = {
            "crew_id": raw_crew_id,
            "resolved_crew_id": lookup_row.get("resolved_crew_id") or raw_crew_id or None,
            "crew_name": lookup_row.get("crew_name"),
            "rank_name": lookup_row.get("rank_name"),
            "rank_level": lookup_row.get("rank_level"),
            "vessel_name": lookup_row.get("vessel_name"),
            "crew_status_name": lookup_row.get("crew_status_name"),
            "seen_at_raw": record.seen_at,
            "reminder_sent_at_raw": record.reminder_sent_at,
        }

        existing_record = delivery_records_by_crew.get(dedupe_key)
        if existing_record is None:
            delivery_records_by_crew[dedupe_key] = normalized_record
            continue

        if normalized_record["seen_at_raw"] and (
            existing_record["seen_at_raw"] is None
            or normalized_record["seen_at_raw"] > existing_record["seen_at_raw"]
        ):
            existing_record["seen_at_raw"] = normalized_record["seen_at_raw"]

        if normalized_record["reminder_sent_at_raw"] and (
            existing_record["reminder_sent_at_raw"] is None
            or normalized_record["reminder_sent_at_raw"] > existing_record["reminder_sent_at_raw"]
        ):
            existing_record["reminder_sent_at_raw"] = normalized_record["reminder_sent_at_raw"]

        if not existing_record.get("crew_name") and normalized_record.get("crew_name"):
            existing_record["crew_name"] = normalized_record["crew_name"]
        if not existing_record.get("rank_name") and normalized_record.get("rank_name"):
            existing_record["rank_name"] = normalized_record["rank_name"]
        if existing_record.get("rank_level") is None and normalized_record.get("rank_level") is not None:
            existing_record["rank_level"] = normalized_record["rank_level"]
        if not existing_record.get("vessel_name") and normalized_record.get("vessel_name"):
            existing_record["vessel_name"] = normalized_record["vessel_name"]
        if not existing_record.get("crew_status_name") and normalized_record.get("crew_status_name"):
            existing_record["crew_status_name"] = normalized_record["crew_status_name"]

    delivery_records = list(delivery_records_by_crew.values())
    delivery_records.sort(
        key=lambda row: (
            row["rank_level"] if row["rank_level"] is not None else 9999,
            str(row.get("rank_name") or "").lower(),
            str(row.get("crew_name") or "").lower(),
            str(row.get("vessel_name") or "").lower(),
            str(row.get("resolved_crew_id") or "").lower(),
        )
    )

    return [
        {
            "crew_id": row["crew_id"],
            "resolved_crew_id": row["resolved_crew_id"],
            "crew_name": row["crew_name"],
            "rank_name": row["rank_name"],
            "vessel_name": row["vessel_name"],
            "crew_status_name": row["crew_status_name"],
            "seen_at": row["seen_at_raw"].isoformat() if row["seen_at_raw"] else None,
            "reminder_sent_at": row["reminder_sent_at_raw"].isoformat() if row["reminder_sent_at_raw"] else None,
        }
        for row in delivery_records
    ]
    
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
        can.setFont(PDF_FONT_NAME, 14)
        can.drawString(COMPANY_X, COMPANY_Y, company_name)

        can.setFont(PDF_FONT_NAME, 10)
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
    return draw_pdf_header(c, width, height, margin, logo_path, logo_w, logo_h)


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
    c.setFont(PDF_FONT_NAME, 16)
    c.drawString(50, height - 100, "Circular / Alert / Work Instruction")

    # SR No
    c.setFont(PDF_FONT_NAME, 12)
    c.drawString(50, height - 140, f"SR. No: {sr_no}")

    # Title
    c.setFont(PDF_FONT_NAME, 14)
    c.drawString(50, height - 180, f"Title: {title}")

    # Body/Instruction
    c.setFont(PDF_FONT_NAME, 11)
    text = c.beginText(50, height - 220)
    text.setFont(PDF_FONT_NAME, 11)
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
        eligible_crew_ids = set(_filter_crew_ids_by_allowed_status([crew.CrewID for crew in crews]))
        print(
            f"get_crews_by_department: Found {len(eligible_crew_ids)} eligible crew records "
            f"with status in {ALLOWED_CIRCULAR_DELIVERY_CREW_STATUSES}"
        )

        # --- Format response ---
        result = []
        for crew in crews:
            if str(crew.CrewID or "").strip() not in eligible_crew_ids:
                continue
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

        eligible_crew_ids = set(
            _filter_crew_ids_by_allowed_status([crew.CrewID for crew in final_crew_list_for_dept])
        )
        eligible_final_crew_records = [
            crew
            for crew in final_crew_list_for_dept
            if str(crew.CrewID or "").strip() in eligible_crew_ids
        ]

        if not eligible_final_crew_records:
            print(
                "get_crews_by_department_and_vessel: No crew found with allowed statuses "
                f"{ALLOWED_CIRCULAR_DELIVERY_CREW_STATUSES} for department '{dept_name}'."
            )
            return JsonResponse([], safe=False)

        # 3. Get the HRM501 details for the crews found in FinalCrewList to get their rank_name
        print("get_crews_by_department_and_vessel: Fetching HRM501 details for crews to get rank_name...")
        # Use select_related for efficiency if HRM501 is linked via ForeignKey (unlikely here, as FinalCrewList links via Crew_ref_id string)
        # Use prefetch_related if HRM501 has a reverse FK from FinalCrewList (also unlikely based on field names)
        # Since FinalCrewList.Crew_ref_id seems to be a string matching HRM501.id,
        # we'll fetch the HRM records separately based on the Crew_ref_id values from FinalCrewList.
        eligible_final_crew_by_ref = {}
        for crew in eligible_final_crew_records:
            eligible_final_crew_by_ref.setdefault(str(crew.Crew_ref_id), crew)
        crew_ref_ids_from_final = list(eligible_final_crew_by_ref.keys())
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
            final_crew_record = eligible_final_crew_by_ref.get(str(hrm_record.id))

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
            'title': notification.title,
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
            'sub_category', 'second_sub_category', 'title', 'office_instructions',
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
def _get_active_draft_record_by_sr_no(sr_no):
    normalized_sr_no = str(sr_no or '').strip()
    if not normalized_sr_no:
        return None

    return (
        MscData.objects
        .filter(
            sr_no=normalized_sr_no,
            publish_status=0,
            is_deleted=False,
        )
        .first()
    )


def _get_latest_notification_record_by_sr_no(sr_no):
    normalized_sr_no = str(sr_no or '').strip()
    if not normalized_sr_no:
        return None

    notification_queryset = (
        MscData.objects
        .filter(
            sr_no=normalized_sr_no,
            is_deleted=False,
        )
        .order_by('-created_at', '-id')
    )

    notification_record = notification_queryset.first()
    if not notification_record:
        return None

    duplicate_count = notification_queryset.count()
    if duplicate_count > 1:
        print(
            "_get_latest_notification_record_by_sr_no: Multiple rows found for "
            f"sr_no={normalized_sr_no}. Using the latest row and ignoring {duplicate_count - 1} duplicates."
        )

    return notification_record


def _serialize_draft_record(draft):
    draft_data = {
        'id': str(draft.id),
        'sr_no': draft.sr_no,
        'title': draft.title,
        'msc_type': str(draft.msc_type_id) if draft.msc_type_id else None,
        'dept': str(draft.dept) if draft.dept else None,
        'category': draft.category,
        'sub_category': str(draft.sub_category_id) if draft.sub_category_id else None,
        'second_sub_category': str(draft.second_sub_category_id) if draft.second_sub_category_id else None,
        'office_instructions': draft.office_instructions,
        'hashtags': draft.hashtags,
        'priority': str(draft.priority_id) if draft.priority_id else None,
        'attachment_name': draft.attachment_name,
        'attachment_path': draft.attachment_path,
        'publish_comment': draft.publish_comment,
        'publish_status': draft.publish_status,
        'created_by': draft.created_by,
    }

    if draft.attachment_name:
        draft_data['attachment_url'] = f"{settings.MEDIA_URL}circular/attachments/{draft.attachment_name}"
    else:
        draft_data['attachment_url'] = None

    return draft_data


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
        draft = _get_active_draft_record_by_sr_no(sr_no)
        if not draft:
            print(f"get_draft_by_sr_no: Draft with SR No {sr_no} not found")
            return JsonResponse({'error': 'Draft not found'}, status=404)
        
        print(f"get_draft_by_sr_no: Found draft with SR No {draft.sr_no}, created_by: {draft.created_by}")
        draft_data = _serialize_draft_record(draft)

        if draft_data['attachment_url']:
            print(f"get_draft_by_sr_no: Generated attachment URL: {draft_data['attachment_url']}")
        else:
            print(f"get_draft_by_sr_no: No attachment for draft SR No {draft.sr_no}")

        print(f"get_draft_by_sr_no: Returning draft data for SR No {draft.sr_no}")
        return JsonResponse(draft_data, safe=False)
        
        draft_data = {
            'id': str(draft.id),  # Convert UUID back to string for JSON serialization
            'sr_no': draft.sr_no,
            'title': draft.title,
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


@api_view(['POST'])
@permission_classes([AllowAny])
def delete_draft_by_id(request, draft_id):
    """Soft delete a draft by its database ID."""
    print(f"=== delete_draft_by_id: Starting function for draft_id = {draft_id} ===")

    if request.method != 'POST':
        print(f"delete_draft_by_id: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        normalized_draft_id = str(uuid.UUID(str(draft_id).strip()))
        print(f"delete_draft_by_id: Looking for draft with ID {normalized_draft_id} to soft-delete")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE msc_data
                SET is_deleted = 1
                WHERE id = TRY_CONVERT(uniqueidentifier, %s)
                  AND publish_status = 0
                  AND ISNULL(is_deleted, 0) = 0
                """,
                [normalized_draft_id],
            )
            updated_count = cursor.rowcount

        if updated_count > 0:
            print(f"delete_draft_by_id: Successfully soft-deleted draft {normalized_draft_id}")
            return JsonResponse({'success': True, 'message': 'Draft deleted successfully'})

        print(f"delete_draft_by_id: Draft with ID {normalized_draft_id} not found or not editable")
        return JsonResponse({'error': 'Draft not found'}, status=404)

    except (ValueError, TypeError, AttributeError) as exc:
        print(f"delete_draft_by_id: Invalid draft ID '{draft_id}' - {exc}")
        return JsonResponse({'error': 'Invalid draft ID format'}, status=400)
    except Exception as e:
        print(f"delete_draft_by_id: Error occurred during deletion - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)

def _update_draft_record_from_request(request, draft_record, log_label):
    print(f"{log_label}: Found draft SR No {draft_record.sr_no}, current status: {draft_record.publish_status}")

    if draft_record.publish_status != 0:
        print(f"{log_label}: Record {draft_record.sr_no} is not a draft (status {draft_record.publish_status}), cannot update via this method.")
        return JsonResponse({'error': 'Only draft records (status 0) can be updated via this method.'}, status=400)

    title = request.POST.get('title', draft_record.title)
    body = request.POST.get('body', draft_record.office_instructions)
    hashtags = request.POST.get('hashtags', draft_record.hashtags)
    category = request.POST.get('category', draft_record.category)
    sub_cat_list = request.POST.getlist('sub_cat')
    second_sub_cat_list = request.POST.getlist('second_sub_cat')

    incoming_msc_type_raw = request.POST.get('type')
    incoming_dept_raw = request.POST.get('department')
    incoming_priority_raw = request.POST.get('priority')

    msc_type_id = (
        _clean_uuid_string(incoming_msc_type_raw)
        if incoming_msc_type_raw is not None
        else _clean_uuid_string(draft_record.msc_type_id)
    )
    dept_id = (
        _clean_uuid_string(incoming_dept_raw)
        if incoming_dept_raw is not None
        else (str(draft_record.dept).strip() if draft_record.dept is not None else None)
    )
    priority_id = (
        _clean_uuid_string(incoming_priority_raw)
        if incoming_priority_raw is not None
        else _clean_uuid_string(draft_record.priority_id)
    )
    sub_category_id = (
        _clean_uuid_string(sub_cat_list[0])
        if sub_cat_list
        else _clean_uuid_string(draft_record.sub_category_id)
    )
    second_sub_category_id = (
        _clean_uuid_string(second_sub_cat_list[0])
        if second_sub_cat_list
        else _clean_uuid_string(draft_record.second_sub_category_id)
    )

    if incoming_msc_type_raw is not None and not msc_type_id:
        print(f"{log_label}: Invalid document type UUID received: {incoming_msc_type_raw}")
        return JsonResponse({'error': 'Invalid document type value'}, status=400)

    if incoming_priority_raw is not None and not priority_id:
        print(f"{log_label}: Invalid priority UUID received: {incoming_priority_raw}")
        return JsonResponse({'error': 'Invalid priority value'}, status=400)

    if incoming_dept_raw is not None and not dept_id:
        print(f"{log_label}: Invalid department UUID received: {incoming_dept_raw}")
        return JsonResponse({'error': 'Invalid department value'}, status=400)

    if sub_cat_list and not sub_category_id:
        print(f"{log_label}: Invalid sub-category UUID received: {sub_cat_list[0]}")
        return JsonResponse({'error': 'Invalid sub-category value'}, status=400)

    if second_sub_cat_list and not second_sub_category_id:
        print(f"{log_label}: Invalid second sub-category UUID received: {second_sub_cat_list[0]}")
        return JsonResponse({'error': 'Invalid second sub-category value'}, status=400)

    publish_status_raw = request.POST.get('publish_status', '1')
    try:
        requested_publish_status = int(publish_status_raw)
    except (TypeError, ValueError):
        requested_publish_status = 1

    if requested_publish_status not in [0, 1]:
        requested_publish_status = 1

    print(f"{log_label}: Updated publish_status to {requested_publish_status} for draft {draft_record.sr_no}")

    attachment_name_to_store = draft_record.attachment_name
    attachment_path_to_store = draft_record.attachment_path

    pdf_data = {
        'title': title or '',
        'body': body or '',
        'doc_type_name': (
            _safe_get_lookup_name_by_id(
                MscType,
                msc_type_id,
                _infer_circular_type_name_from_sr_no(draft_record.sr_no) or 'Unknown'
            ) or 'Unknown'
        ),
        'formatted_id': draft_record.sr_no,
        'current_date': django_timezone.now().strftime('%d-%m-%Y'),
        'superseding_old_notification_sr_no': None,
        'created_by_employee_id': draft_record.created_by,
    }

    try:
        uploaded_files = _extract_uploaded_pdf_attachments_from_request_files(request.FILES)
    except CircularAttachmentValidationError as exc:
        print(f"{log_label}: Attachment validation failed - {exc}")
        return JsonResponse({'error': str(exc)}, status=400)

    if uploaded_files:
        uploaded_file_bytes_list = [uploaded_file.read() for uploaded_file in uploaded_files]
        try:
            attachment_name_to_store, attachment_path_to_store = _store_circular_generated_pdf(
                draft_record.sr_no,
                pdf_data,
                uploaded_file_bytes_list=uploaded_file_bytes_list,
            )
        except CircularAttachmentValidationError as exc:
            print(f"{log_label}: Attachment validation failed - {exc}")
            return JsonResponse({'error': str(exc)}, status=400)
        print(f"{log_label}: Updated attachment for {draft_record.sr_no} at {attachment_path_to_store}")
    elif not attachment_path_to_store:
        try:
            attachment_name_to_store, attachment_path_to_store = _store_circular_generated_pdf(
                draft_record.sr_no,
                pdf_data,
            )
        except CircularAttachmentValidationError as exc:
            print(f"{log_label}: Attachment validation failed - {exc}")
            return JsonResponse({'error': str(exc)}, status=400)
        print(f"{log_label}: Created generated circular PDF for draft {draft_record.sr_no} at {attachment_path_to_store}")

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE msc_data
                SET
                    msc_type = CAST(%s AS UNIQUEIDENTIFIER),
                    dept = %s,
                    category = %s,
                    sub_category = CAST(%s AS UNIQUEIDENTIFIER),
                    second_sub_category = CAST(%s AS UNIQUEIDENTIFIER),
                    title = %s,
                    office_instructions = %s,
                    hashtags = %s,
                    publish_status = %s,
                    priority = CAST(%s AS UNIQUEIDENTIFIER),
                    attachment_name = %s,
                    attachment_path = %s
                WHERE sr_no = %s
                  AND publish_status = 0
                  AND is_deleted = 0
                """,
                [
                    msc_type_id,
                    dept_id,
                    category,
                    sub_category_id,
                    second_sub_category_id,
                    title,
                    body,
                    hashtags,
                    requested_publish_status,
                    priority_id,
                    attachment_name_to_store,
                    attachment_path_to_store,
                    draft_record.sr_no,
                ]
            )
            rows_updated = cursor.rowcount

    if rows_updated <= 0:
        print(f"{log_label}: No draft rows were updated for SR No {draft_record.sr_no}")
        return JsonResponse({'error': 'Draft not found or not editable'}, status=404)

    print(f"{log_label}: Successfully updated draft record ID {draft_record.id} (SR No: {draft_record.sr_no})")

    response_message = (
        'Draft updated successfully'
        if requested_publish_status == 0
        else 'Draft record updated and submitted successfully'
    )

    if requested_publish_status == 1:
        notify_circular_pending_approval(
            sr_no=draft_record.sr_no,
            title=title,
            creator_employee_id=draft_record.created_by,
            notification_id=str(draft_record.id) if draft_record.id else None,
            doc_type_name=pdf_data.get('doc_type_name'),
        )

    return JsonResponse({
        'success': True,
        'message': response_message,
        'updated_sr_no': draft_record.sr_no,
        'publish_status': requested_publish_status,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def update_draft_by_sr_no(request, sr_no):
    """Update an existing draft by its SR No."""
    print(f"=== update_draft_by_sr_no: Starting function for sr_no = {sr_no} ===")
    
    if request.method != 'POST':
        print(f"update_draft_by_sr_no: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        print(f"update_draft_by_sr_no: Looking for draft with SR No {sr_no} to update")
        draft = _get_active_draft_record_by_sr_no(sr_no)
        if not draft:
            print(f"update_draft_by_sr_no: Draft with SR No {sr_no} not found or not a draft (status != 0)")
            return JsonResponse({'error': 'Draft not found or not editable'}, status=404)
        
        print(f"update_draft_by_sr_no: Found draft ID {draft.id} (SR No: {draft.sr_no})")
        return _update_draft_record_from_request(request, draft, 'update_draft_by_sr_no')

    except Exception as e:
        print(f"update_draft_by_sr_no: Error occurred during update - {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_draft_by_id(request, draft_id):
    """
    Updates an existing draft record identified by its database ID.
    Respects the requested publish_status so a saved draft can remain status 0,
    while a resubmitted draft can move to status 1.
    """
    print(f"=== update_draft_by_id: Starting for draft_id = {draft_id} ===")

    if request.method != 'POST':
        print(f"update_draft_by_id: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        normalized_draft_id = str(uuid.UUID(str(draft_id).strip()))
        print(f"update_draft_by_id: Looking for draft with database ID {normalized_draft_id}")
        try:
            draft_record = MscData.objects.get(id=normalized_draft_id, is_deleted=False)
        except DatabaseError as db_exc:
            print(f"update_draft_by_id: Direct id lookup failed for {normalized_draft_id}, falling back to string comparison. Error: {db_exc}")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TOP 1 sr_no
                    FROM msc_data
                    WHERE CAST(id AS NVARCHAR(255)) = %s
                      AND is_deleted = 0
                    """,
                    [normalized_draft_id]
                )
                fallback_row = cursor.fetchone()

            if not fallback_row or not fallback_row[0]:
                raise MscData.DoesNotExist()

            draft_record = _get_latest_notification_record_by_sr_no(fallback_row[0])
            if not draft_record:
                raise MscData.DoesNotExist()

        return _update_draft_record_from_request(request, draft_record, 'update_draft_by_id')

    except MscData.DoesNotExist:
        print(f"update_draft_by_id: Draft with ID {draft_id} not found")
        return JsonResponse({'error': 'Draft record not found'}, status=404)
    except (ValueError, TypeError, AttributeError) as exc:
        print(f"update_draft_by_id: Invalid draft ID '{draft_id}' - {exc}")
        return JsonResponse({'error': 'Invalid draft ID format'}, status=400)
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
            'sub_category', 'second_sub_category', 'title', 'office_instructions',
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
    The new circular SR No is stored in superseeded_by.
    """
    print(f"=== supersede_notification: Starting for SR No {sr_no} ===")
    try:
        # --- 1. Get the SR No of the NEW notification from the request body ---
        # This comes from the frontend after creating the new one
        try:
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)
            superseding_sr_no = body_data.get('superseding_sr_no')
            print(f"supersede_notification: Superseding SR No from request body: {superseding_sr_no}")
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
            print("supersede_notification: Could not get required data from request body.")
            return JsonResponse({'error': 'Invalid request data.'}, status=400)

        if not superseding_sr_no:
            return JsonResponse({'error': 'superseding_sr_no is required.'}, status=400)

        # --- 2. Perform a direct database update based on the old SR No ---
        # Use filter(sr_no=sr_no) to target the correct row(s) and update() to change fields directly in the DB.
        # This bypasses loading the potentially corrupted object instance into Python.
        # It returns the number of rows affected.
        
        print(f"supersede_notification: Attempting direct database update for old SR No='{sr_no}'")
        # Update the is_superseeded and superseeded_by fields
        # Set is_superseeded to True and superseeded_by to the new circular SR No.
        update_data = {
            'is_superseeded': True,
            'superseeded_by': superseding_sr_no
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
    resolved_msc_type = _resolve_circular_type_label(msc_type)

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

        if resolved_msc_type:
            notifications_queryset = notifications_queryset.filter(msc_type__name__icontains=resolved_msc_type)

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

        if resolved_msc_type and priority:
            note_text = f"This is the list of {priority.lower()} {resolved_msc_type.lower()} published by KSM."
        elif resolved_msc_type:
            note_text = f"This is the list of {resolved_msc_type.lower()} published by KSM."
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
            notification = _get_latest_notification_record_by_sr_no(notification_sr_no)
            if not notification:
                raise MscData.DoesNotExist()
            print(f"create_delivery_records: Found notification {notification.sr_no} (ID: {notification.id}) to link delivery records to.")
        except MscData.DoesNotExist:
            print(f"create_delivery_records: Notification with SR No {notification_sr_no} not found.")
            return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)

        eligible_crew_ids = _filter_crew_ids_by_allowed_status(crew_ids)
        print(
            "create_delivery_records: "
            f"{len(eligible_crew_ids)} of {len(_normalize_text_list(crew_ids))} crew IDs are eligible "
            f"with status in {ALLOWED_CIRCULAR_DELIVERY_CREW_STATUSES}."
        )

        created_crew_ids = _bulk_insert_crew_delivery_records(
            notification.sr_no,
            eligible_crew_ids,
            django_timezone.now(),
            reminder_count=1,
        )
        created_records_count = len(created_crew_ids)

        print(f"create_delivery_records: Successfully created {created_records_count} delivery records for notification {notification_sr_no}")

        return JsonResponse({
            'success': True,
            'message': f'Created {created_records_count} delivery records for notification {notification_sr_no}.',
            'notification_sr_no': notification_sr_no,
            'crew_ids_processed': len(_normalize_text_list(crew_ids)),
            'crew_ids_eligible': len(eligible_crew_ids),
            'records_created': created_records_count,
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
        notification = _get_latest_notification_record_by_sr_no(notification_sr_no)
        if not notification:
            raise MscData.DoesNotExist()

        print(f"get_notification_details_by_sr_no: Found notification. ID (DB): {notification.id}, SR No: {notification.sr_no}") # ✅ Updated log message

        # Prepare the response data (include fields needed for crew list logic, like 'dept')
        notification_data = {
            'id': str(notification.id), # Keep the database ID for internal use if needed (convert UUID to string)
            'sr_no': notification.sr_no, # ✅ Include the SR No
            'title': notification.title,
            'msc_type': notification.msc_type,
            'dept': notification.dept, # This is the crucial field for fetching crews
            'dept_name': _get_department_master_name(notification.dept),
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
            notification_details = _get_latest_notification_record_by_sr_no(notification_sr_no)
            if not notification_details:
                raise MscData.DoesNotExist()
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


@api_view(['POST'])
@permission_classes([AllowAny])
def send_emails_to_vessels(request):
    """
    Optimized/idempotent delivery for vessel notifications.
    Keeps email sending best-effort while preventing duplicate delivery rows on repeat clicks.
    """
    print("=== send_emails_to_vessels[v2]: Starting function ===")
    print(f"send_emails_to_vessels[v2]: Request body: {request.body.decode('utf-8', errors='ignore')}")

    if request.method != 'POST':
        print(f"send_emails_to_vessels[v2]: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        notification_sr_no = data.get('notification_sr_no')
        vessel_ids_list = _normalize_uuid_list(data.get('vessel_ids', []))

        if not notification_sr_no or not vessel_ids_list:
            print(
                f"send_emails_to_vessels[v2]: Missing required data - "
                f"notification_sr_no: {notification_sr_no}, vessel_ids: {vessel_ids_list}"
            )
            return JsonResponse({'error': 'notification_sr_no and vessel_ids list are required'}, status=400)

        notification_details = _get_latest_notification_record_by_sr_no(notification_sr_no)
        if not notification_details:
            print(f"send_emails_to_vessels[v2]: Notification with SR No {notification_sr_no} not found.")
            return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)

        sr_no_parts = notification_sr_no.split('/')
        extracted_type_name = sr_no_parts[1] if len(sr_no_parts) >= 2 else "Unknown Type"

        vessel_lookup = _fetch_vessel_rows_by_ids(vessel_ids_list)

        if not vessel_lookup:
            return JsonResponse({
                'success': True,
                'message': 'No valid vessel records found to notify.',
                'emails_sent': 0,
                'delivery_records_created': 0,
                'already_processed': 0,
                'total_requested': len(vessel_ids_list),
            })

        existing_delivery_vessels = _fetch_existing_ship_delivery_vessel_ids(
            notification_sr_no,
            vessel_ids_list,
        )
        valid_vessel_ids = [
            vessel_id for vessel_id in vessel_ids_list
            if vessel_id in vessel_lookup
        ]
        pending_vessel_ids = [
            vessel_id for vessel_id in vessel_ids_list
            if vessel_id in vessel_lookup and vessel_id not in existing_delivery_vessels
        ]

        print(
            f"send_emails_to_vessels[v2]: {len(existing_delivery_vessels)} vessels already processed, "
            f"{len(pending_vessel_ids)} remaining for notification {notification_sr_no}."
        )

        created_vessel_ids = _bulk_insert_ship_delivery_records(
            notification_sr_no,
            valid_vessel_ids,
            django_timezone.now(),
        )
        delivery_records_created_count = len(created_vessel_ids)
        vessel_crew_ids = _fetch_target_crew_ids_for_vessels(valid_vessel_ids)
        created_vessel_crew_ids = _bulk_insert_crew_delivery_records(
            notification_sr_no,
            vessel_crew_ids,
            django_timezone.now(),
            reminder_count=1,
        )

        emails_sent_count = 0
        vessels_without_email_count = 0
        email_failed_count = 0
        for vessel_id_str in pending_vessel_ids:
            vessel_details = vessel_lookup.get(vessel_id_str)
            if not vessel_details:
                continue

            vessel_name = vessel_details.get('vesselName')
            vessel_email = vessel_details.get('email')
            if not vessel_email:
                print(f"send_emails_to_vessels[v2]: Vessel {vessel_name} has no email. Skipping.")
                vessels_without_email_count += 1
                continue

            subject = f"New {extracted_type_name} Notification: {notification_details.sr_no}"
            body_text = f"""
Hello,

You have a new {extracted_type_name.lower()} notification:

SR No: {notification_details.sr_no}
Title: {notification_details.title}


Best regards,
Kaizen Ship Management
            """.strip()

            try:
                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=body_text,
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    to=[vessel_email],
                )
                email_message.send()
                emails_sent_count += 1
                print(f"send_emails_to_vessels[v2]: Email sent successfully to {vessel_email} for {vessel_name}.")
            except Exception as single_vessel_error:
                email_failed_count += 1
                print(
                    f"send_emails_to_vessels[v2]: Error sending to vessel {vessel_id_str}: "
                    f"{single_vessel_error}"
                )
                traceback.print_exc()

        return JsonResponse({
            'success': True,
            'message': (
                f'KSM Library delivery created for {delivery_records_created_count} vessels. '
                f'Crew delivery created for {len(created_vessel_crew_ids)} crew members. '
                f'Emails sent successfully to {emails_sent_count} vessels.'
            ),
            'emails_sent': emails_sent_count,
            'email_failed': email_failed_count,
            'vessels_without_email': vessels_without_email_count,
            'delivery_records_created': delivery_records_created_count,
            'crew_delivery_records_created': len(created_vessel_crew_ids),
            'crew_delivery_records_eligible': len(vessel_crew_ids),
            'already_processed': len(existing_delivery_vessels),
            'total_requested': len(vessel_ids_list),
        })
    except json.JSONDecodeError as je:
        print(f"send_emails_to_vessels[v2]: JSON Decode Error: {je}")
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except Exception as e:
        print(f"send_emails_to_vessels[v2]: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
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
            notification = _get_latest_notification_record_by_sr_no(notification_sr_no)
            if not notification:
                raise MscData.DoesNotExist()
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

        if created_notification_records_count > 0:
            notify_circular_distribution(
                sr_no=notification.sr_no,
                title=notification.title,
                crew_ids=[record.CrewID for record in final_crew_records],
                notification_id=str(notification.id) if notification.id else None,
                doc_type_name=(
                    _infer_circular_type_name_from_sr_no(notification.sr_no)
                    or _safe_get_lookup_name_by_id(MscType, notification.msc_type_id, 'Circular')
                    or 'Circular'
                ),
            )



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




@api_view(['POST'])
@permission_classes([AllowAny])
def link_notification_to_ranks(request, notification_sr_no):
    """
    Optimized/idempotent rank linking for approved circulars.
    """
    print(f"=== link_notification_to_ranks[v2]: Starting for notification SR No {notification_sr_no} ===")
    print(f"link_notification_to_ranks[v2]: Request body: {request.body.decode('utf-8', errors='ignore')}")

    if request.method != 'POST':
        print(f"link_notification_to_ranks[v2]: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        data = json.loads(request.body)
        selected_rank_uuids = _normalize_uuid_list(data.get('selected_rank_ids', []))

        if not selected_rank_uuids:
            print("link_notification_to_ranks[v2]: No selected_rank_ids provided in request body.")
            return JsonResponse({'error': 'selected_rank_ids list is required'}, status=400)

        notification = _get_latest_notification_record_by_sr_no(notification_sr_no)
        if not notification:
            print(f"link_notification_to_ranks[v2]: Notification with SR No {notification_sr_no} not found.")
            return JsonResponse({'error': f'Notification with SR No {notification_sr_no} not found.'}, status=404)

        target_crew_ids = _fetch_target_crew_ids_for_ranks(selected_rank_uuids)
        created_crew_ids = _bulk_insert_crew_delivery_records(
            notification.sr_no,
            target_crew_ids,
            django_timezone.now(),
            reminder_count=1,
        )
        inserted_rank_ids = _bulk_insert_rank_assignments(
            notification.sr_no,
            selected_rank_uuids,
            django_timezone.now(),
        )

        if created_crew_ids:
            notify_circular_distribution(
                sr_no=notification.sr_no,
                title=notification.title,
                crew_ids=created_crew_ids,
                notification_id=str(notification.id) if notification.id else None,
                doc_type_name=(
                    _infer_circular_type_name_from_sr_no(notification.sr_no)
                    or _safe_get_lookup_name_by_id(MscType, notification.msc_type_id, 'Circular')
                    or 'Circular'
                ),
            )

        print(
            f"link_notification_to_ranks[v2]: crews_found={len(target_crew_ids)}, "
            f"records_created={len(created_crew_ids)}, rank_assignments_created={len(inserted_rank_ids)}"
        )

        return JsonResponse({
            'success': True,
            'message': (
                f'Notifications sent to {len(created_crew_ids)} crew members based on selected rank UUIDs. '
                f'{len(inserted_rank_ids)} rank assignments recorded.'
            ),
            'crews_found': len(target_crew_ids),
            'records_created': len(created_crew_ids),
            'rank_assignments_created': len(inserted_rank_ids),
            'notification_sr_no': notification.sr_no,
        })
    except json.JSONDecodeError as je:
        print(f"link_notification_to_ranks[v2]: JSON Decode Error: {je}")
        return JsonResponse({'error': 'Invalid JSON data in request body.'}, status=400)
    except Exception as e:
        print(f"link_notification_to_ranks[v2]: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_crew_ids_and_status_by_notification_sr_no(request, notification_sr_no):
    """
    Fetches delivery status rows for a notification, enriched with crew, rank,
    and vessel display data for office users.
    Expects the notification SR No in the URL path.
    Returns a JSON array of objects containing crew_id, resolved_crew_id,
    crew_name, rank_name, vessel_name, seen_at, and reminder_sent_at.
    """
    print(f"=== get_crew_ids_and_status_by_notification_sr_no: Starting for notification SR No {notification_sr_no} ===")

    if request.method != 'GET':
        print(f"get_crew_ids_and_status_by_notification_sr_no: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only GET allowed'}, status=405)

    try:
        # Find all MscNotification records matching the specific msc_sr_no
        print(f"get_crew_ids_and_status_by_notification_sr_no: Fetching crew delivery records for notification SR No '{notification_sr_no}' from msc_notification table...")
        notification_records = MscNotification.objects.filter(msc_sr_no=notification_sr_no)

        result = _build_delivery_status_records(notification_records)

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
def send_notification_reminder(request, notification_sr_no):
    """
    Updates reminder metadata for every unread crew delivery record associated
    with a notification SR No so the office can resend a circular reminder.
    """
    print(f"=== send_notification_reminder: Starting for notification SR No {notification_sr_no} ===")

    if request.method != 'POST':
        print(f"send_notification_reminder: Invalid method {request.method}, returning 405")
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    try:
        current_time = django_timezone.now()
        print(
            "send_notification_reminder: Updating unread delivery records "
            f"for notification {notification_sr_no} at {current_time}"
        )

        update_sql = """
            UPDATE msc_notification
            SET reminder_sent_at = %s,
                reminder_count = ISNULL(reminder_count, 0) + 1
            WHERE msc_sr_no = %s
              AND seen_at IS NULL
        """

        with connection.cursor() as cursor:
            cursor.execute(update_sql, [current_time, notification_sr_no])
            rows_affected = cursor.rowcount

        print(f"send_notification_reminder: Raw SQL update affected {rows_affected} rows.")

        if rows_affected == 0:
            print(
                "send_notification_reminder: No unread delivery records found "
                f"for notification {notification_sr_no}."
            )
            return JsonResponse({
                'success': True,
                'message': f'No unread delivery records found for notification {notification_sr_no}.',
                'notification_sr_no': notification_sr_no,
                'rows_affected': 0,
                'reminder_sent_at': current_time.isoformat(),
            }, status=200)

        print(
            "send_notification_reminder: Successfully updated unread reminder metadata "
            f"for notification {notification_sr_no}."
        )
        return JsonResponse({
            'success': True,
            'message': f'Reminder sent successfully for notification {notification_sr_no}.',
            'notification_sr_no': notification_sr_no,
            'rows_affected': rows_affected,
            'reminder_sent_at': current_time.isoformat(),
        })
    except Exception as e:
        print(f"send_notification_reminder: UNEXPECTED ERROR - {type(e).__name__}: {str(e)}")
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
        notification = _get_latest_notification_record_by_sr_no(notification_id)
        if not notification:
            raise MscData.DoesNotExist()
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
            attachment_pdf_reader = None
            attachment_start_index = 0
            if notification.attachment_path and os.path.exists(notification.attachment_path):
                 print("edit_pending_notification: Original attachment found, starting PDF cover regeneration...")
                 attachment_pdf_reader, attachment_start_index = _resolve_attachment_reader_for_merge(
                     notification.attachment_path,
                     notification.sr_no
                 )

                 # 2. Generate the UPDATED COVER PAGE (with new details)
                 cover_buffer = io.BytesIO()
                 c = canvas.Canvas(cover_buffer, pagesize=letter)
                 width, height = letter
                 margin = 50
                 top_section_y_start = height - 50
                 logo_path = os.path.join(settings.BASE_DIR, "static", "ksm-logo.png")
                 logo_width = 30
                 logo_height = 50

                 # --- 1. Company Header (with Logo - Conditional) ---
                 divider_y = draw_pdf_header(
                     c, width, height, margin,
                     logo_path, logo_width, logo_height
                 )





                 # --- 3. Document Title (Dynamic) ---
                 c.setFont(PDF_FONT_NAME, PDF_TITLE_FONT_SIZE)
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
                 c.setFont(PDF_FONT_NAME, PDF_META_FONT_SIZE)
                 ref_date_y = title_y - 30
                 c.drawString(margin, ref_date_y, f"serial_no. : {notification.sr_no}")
                 c.drawRightString(width - margin, ref_date_y,
                                 f"Date: {notification.created_at.strftime('%d-%m-%Y') if notification.created_at else 'N/A'}")


                 subject_y = _draw_pdf_supersede_notice(
                     c,
                     margin,
                     ref_date_y,
                     notification.superseeded_by
                 )

                 # --- 5. Subject ---
                 subject_bottom_y = _draw_pdf_subject_block(
                     c,
                     width,
                     margin,
                     subject_y,
                     notification.title or notification.sr_no
                 )

                 # --- 6. Office Instructions (Main Body Content) ---
                 print("--- START: Office Instructions Generation (Update/Edit) ---")
                 c.setFont(PDF_FONT_NAME, PDF_BODY_FONT_SIZE)
                 body_start_y = subject_bottom_y - 20
                 y_position = body_start_y
                 page_number = 1
                 body_text = notification.office_instructions or ""
                 print(f"edit_pending_notification: Adding body content: {body_text[:50]}...")

                 created_by_part = f"Created By: {notification.created_by}" if notification.created_by else "Created By: Unknown User"
                 approved_by_part = f"Approved By: {notification.published_by}" if notification.published_by else "Approved By: Pending"
                 edited_at_part = f"Edited At: {django_timezone.now().strftime('%d-%m-%Y %H:%M:%S')}"
                 footer_middle_text = [created_by_part, approved_by_part]
                 should_stack_footer_metadata = _should_stack_footer_metadata(
                     _infer_circular_type_name_from_sr_no(notification.sr_no)
                 )

                 if body_text:
                     body_lines = _wrap_text_simple(c, body_text, width - 2 * margin, PDF_FONT_NAME, PDF_BODY_FONT_SIZE)
                     last_body_y_position = y_position

                     for line in body_lines:
                         if y_position > PDF_BODY_STOP_Y:
                             c.drawString(margin, y_position, line)
                             y_position -= PDF_LINE_HEIGHT
                             last_body_y_position = y_position
                         else:
                             _draw_fixed_footer(
                                 c,
                                 width,
                                 margin,
                                 f"Sr. No: {notification.sr_no}",
                                 footer_middle_text,
                                 f"{edited_at_part} | Page {page_number}",
                                 stack_metadata_below_left=should_stack_footer_metadata,
                             )
                             c.showPage()
                             page_number += 1
                             y_position = _draw_pdf_continuation_header(
                                 c, width, height, margin,
                                 logo_path, logo_width, logo_height,
                                 notification.sr_no,
                                 page_number
                             )
                             c.setFont(PDF_FONT_NAME, PDF_BODY_FONT_SIZE)
                             c.drawString(margin, y_position, line)
                             y_position -= PDF_LINE_HEIGHT
                             last_body_y_position = y_position

                     _draw_fixed_footer(
                         c,
                         width,
                         margin,
                         f"Sr. No: {notification.sr_no}",
                         footer_middle_text,
                         f"{edited_at_part} | Page {page_number}",
                         stack_metadata_below_left=should_stack_footer_metadata,
                     )
                 else:
                     print("--- END: Office Instructions Generation (Update/Edit) ---")
                     _draw_fixed_footer(
                         c,
                         width,
                         margin,
                         f"Sr. No: {notification.sr_no}",
                         footer_middle_text,
                         f"{edited_at_part} | Page {page_number}",
                         stack_metadata_below_left=should_stack_footer_metadata,
                     )

                 c.save()
                 cover_buffer.seek(0)
                 # ===== END: EMBEDDED COVER PAGE GENERATION =====


            
                 print("edit_pending_notification: Merging updated cover with original content...")
                 new_cover_reader = PdfReader(cover_buffer)
                 merger = PdfWriter()

                 for page in new_cover_reader.pages:
                     merger.add_page(page)

                 for i in range(attachment_start_index, len(attachment_pdf_reader.pages)):
                     merger.add_page(attachment_pdf_reader.pages[i])

            
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


