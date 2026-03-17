"""
Database utility functions for handling cross-table UUID type mismatches.

mssql-django stores UUIDs as char(32) in managed tables, while existing
unmanaged tables (like VesselData) use native uniqueidentifier columns.
These functions provide proper conversion for cross-table subqueries.

The char(32) format is e.g. 'e2e7ff0dab6d4485afb8aa45aa537d73' (no hyphens),
while uniqueidentifier expects 'E2E7FF0D-AB6D-4485-AFB8-AA45AA537D73'.
We use CONVERT with style 2 which handles hex-string-to-uniqueidentifier.
"""

from django.db.models.expressions import RawSQL


def _char32_to_uuid(column_ref):
    """
    SQL expression to convert a char(32) column to uniqueidentifier.
    Uses CONVERT with STUFF to insert hyphens before casting.
    """
    return (
        f"CAST("
        f"STUFF(STUFF(STUFF(STUFF({column_ref}, 9, 0, '-'), 14, 0, '-'), 19, 0, '-'), 24, 0, '-')"
        f" AS uniqueidentifier)"
    )


def vessel_name_annotation():
    """
    RawSQL subquery to get vessel_name from VesselData.
    Handles char(32) -> uniqueidentifier conversion for the join.
    Use with .annotate(vessel_name=vessel_name_annotation())
    """
    cast_expr = _char32_to_uuid('psc_inspection.vessel_id')
    return RawSQL(
        f"(SELECT v.vesselName FROM VesselData v "
        f"WHERE v.id = {cast_expr} "
        f"AND v.is_active = 1 AND v.is_deleted = 0)",
        [],
    )


def vessel_code_annotation():
    """
    RawSQL subquery to get vessel_code from VesselData.
    Handles char(32) -> uniqueidentifier conversion for the join.
    """
    cast_expr = _char32_to_uuid('psc_inspection.vessel_id')
    return RawSQL(
        f"(SELECT v.vesselCode FROM VesselData v "
        f"WHERE v.id = {cast_expr} "
        f"AND v.is_active = 1 AND v.is_deleted = 0)",
        [],
    )


def imo_number_annotation():
    """
    RawSQL subquery to get imo_number from VesselData.
    Handles char(32) -> uniqueidentifier conversion for the join.
    """
    cast_expr = _char32_to_uuid('psc_inspection.vessel_id')
    return RawSQL(
        f"(SELECT v.imoNumber FROM VesselData v "
        f"WHERE v.id = {cast_expr} "
        f"AND v.is_active = 1 AND v.is_deleted = 0)",
        [],
    )


def vessel_name_for_table(table_name, fk_column='vessel_id'):
    """
    Generic RawSQL subquery to get vessel_name from VesselData
    for any table with a vessel_id FK stored as char(32).
    """
    cast_expr = _char32_to_uuid(f'{table_name}.{fk_column}')
    return RawSQL(
        f"(SELECT v.vesselName FROM VesselData v "
        f"WHERE v.id = {cast_expr} "
        f"AND v.is_active = 1 AND v.is_deleted = 0)",
        [],
    )


def vessel_code_for_table(table_name, fk_column='vessel_id'):
    """
    Generic RawSQL subquery to get vessel_code from VesselData
    for any table with a vessel_id FK stored as char(32).
    """
    cast_expr = _char32_to_uuid(f'{table_name}.{fk_column}')
    return RawSQL(
        f"(SELECT v.vesselCode FROM VesselData v "
        f"WHERE v.id = {cast_expr} "
        f"AND v.is_active = 1 AND v.is_deleted = 0)",
        [],
    )


def car_vessel_name_annotation():
    """
    RawSQL subquery to get vessel_name for a CAR record.
    Joins through psc_deficiency -> psc_inspection -> VesselData.
    """
    cast_expr = _char32_to_uuid('i.vessel_id')
    return RawSQL(
        f"(SELECT v.vesselName FROM VesselData v "
        f"INNER JOIN psc_inspection i ON v.id = {cast_expr} "
        f"INNER JOIN psc_deficiency d ON d.inspection_id = i.id "
        f"WHERE d.car_id = psc_car.id "
        f"AND v.is_active = 1 AND v.is_deleted = 0 "
        f"AND d.is_deleted = 0 AND i.is_deleted = 0)",
        [],
    )


def car_vessel_code_annotation():
    """
    RawSQL subquery to get vessel_code for a CAR record.
    Joins through psc_deficiency -> psc_inspection -> VesselData.
    """
    cast_expr = _char32_to_uuid('i.vessel_id')
    return RawSQL(
        f"(SELECT v.vesselCode FROM VesselData v "
        f"INNER JOIN psc_inspection i ON v.id = {cast_expr} "
        f"INNER JOIN psc_deficiency d ON d.inspection_id = i.id "
        f"WHERE d.car_id = psc_car.id "
        f"AND v.is_active = 1 AND v.is_deleted = 0 "
        f"AND d.is_deleted = 0 AND i.is_deleted = 0)",
        [],
    )
