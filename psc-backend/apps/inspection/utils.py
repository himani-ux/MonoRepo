"""
Utility functions for the inspection app.
"""

from django.db import connection


def generate_report_reference(vessel_id, inspection_date):
    """
    Generate report reference in format: {VesselCode}-{YYYY}-{SEQ:02d}
    SEQ is zero-padded 2 digits, resets yearly per vessel.
    Example: KSMP-2026-01

    Args:
        vessel_id: UUID of the vessel (Python UUID object or hyphenated string)
        inspection_date: date object for the inspection

    Returns:
        Formatted report reference string, or None if vessel not found
    """
    from .models import Inspection

    vessel_id_str = str(vessel_id)

    # Get vessel_code from VesselData (raw SQL for UUID type conversion)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT vesselCode FROM VesselData "
            "WHERE id = CAST(%s AS uniqueidentifier) "
            "AND is_active = 1 AND is_deleted = 0",
            [vessel_id_str]
        )
        row = cursor.fetchone()
        if not row:
            return None

    vessel_code = row[0]
    year = inspection_date.year

    # Count existing inspections for this vessel in the same year
    existing_count = Inspection.objects.filter(
        vessel_id=vessel_id,
        is_deleted=False,
        inspection_date__year=year,
    ).exclude(
        report_reference__isnull=True,
    ).exclude(
        report_reference='',
    ).count()

    seq = existing_count + 1
    return f"{vessel_code}-{year}-{seq:02d}"
