# logbook/validators.py
from django.core.exceptions import ValidationError
from decimal import Decimal
import re

def validate_orb_entry(entry):
    """
    Validates ORB entry per MARPOL Annex I, AMSA 228, and INTERTANKO Guide.
    """
    errors = []

    # Required fields
    if not entry.date:
        errors.append("Date is required.")
    if not entry.code:
        errors.append("Operation code is required.")
    if not entry.details.strip():
        errors.append("Details are required.")
    if not entry.officer_in_charge:
        errors.append("Officer in charge is required.")

    # GPS for Code D/E
    if entry.code in ['D', 'E'] and (entry.item_no in ['15.1', '16.1']):
        if not entry.latitude or not entry.longitude:
            errors.append("GPS position is required for bilge discharge (Code D/E).")
        if abs(entry.latitude) > 90 or abs(entry.longitude) > 180:
            errors.append("Invalid GPS coordinates.")

    # Validate item_no based on code
    if entry.code == 'C':
        if entry.item_no not in ['11.1', '11.2', '11.3', '11.4', '12.1', '12.2', '12.3', '12.4']:
            errors.append(f"Invalid item number '{entry.item_no}' for Code C.")
        if entry.item_no == '11.4' and 'COLLECTED' not in entry.details.upper():
            errors.append("C11.4 must describe manual sludge collection.")
        if entry.item_no == '11.1':
            sludge_tanks = entry.vessel.tanks.filter(type='sludge').values_list('identifier', flat=True)
            if not any(tank in entry.details for tank in sludge_tanks):
                errors.append("C11.1: Tank must be listed in IOPP Section 3.1.")

    elif entry.code == 'D':
        if entry.item_no not in ['13', '14', '15.1', '15.2', '15.3']:
            errors.append(f"Invalid item number '{entry.item_no}' for Code D.")
        if entry.item_no == '15.1' and 'POSITION AT START' not in entry.details:
            errors.append("D15.1: Position at start and end required.")
        if entry.item_no == '15.3':
            bilge_tanks = entry.vessel.tanks.filter(type='bilge').values_list('identifier', flat=True)
            if not any(tank in entry.details for tank in bilge_tanks):
                errors.append("D15.3: Must transfer to IOPP Section 3.3 bilge tank.")

    elif entry.code == 'H':
        if entry.item_no not in ['26.1', '26.2', '26.3', '26.4']:
            errors.append(f"Invalid item number '{entry.item_no}' for Code H.")
        if 'MT' not in entry.details and 'TONNES' not in entry.details:
            errors.append("H26.3/H26.4: Quantity must be in metric tonnes.")

    elif entry.code == 'F':
        if entry.item_no not in ['19', '20', '21']:
            errors.append(f"Invalid item number '{entry.item_no}' for Code F.")
        if entry.item_no == '19' and not re.search(r'\d{2}:\d{2}', entry.details):
            errors.append("F19: Failure time must include HH:MM.")

    elif entry.code == 'G':
        if entry.item_no not in ['22', '23', '24', '25']:
            errors.append(f"Invalid item number '{entry.item_no}' for Code G.")
        if 'APPROXIMATE' not in entry.details.upper():
            errors.append("G24: Quantity must be approximate.")

    elif entry.code == 'I':
        if entry.item_no != '27.1':
            errors.append("Code I must use item number 27.1 for remarks.")
        if 'CORRECTION' in entry.details.upper() and 'Date(1)' not in entry.details:
            errors.append("Code I correction must include Date(1) and Date(2) per INTERTANKO 4.18b.")

    # Missed entry correction format
    if 'MISSED OPERATION' in entry.details.upper() and entry.code != 'I':
        errors.append("Missed entries must be corrected under Code I with Date(1)/Date(2).")

    # Manual sludge collection format
    if entry.code == 'C' and entry.item_no == '11.4':
        if not re.search(r'\d+(\.\d+)?\s*M\s*COLLECTED', entry.details, re.IGNORECASE):
            errors.append("C11.4: Must state quantity collected in m³.")

    if errors:
        raise ValidationError(errors)