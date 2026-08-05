from __future__ import annotations

import uuid

from django.db import migrations, models


INCIDENT_TABLE = "vims_safety_incident"
WEATHER_OPTION_TABLE = "vims_safety_incident_weather_option"

WEATHER_OPTION_FIELDS = (
    "weather_visibility_id",
    "weather_precipitation_id",
    "weather_sea_state_id",
    "weather_wind_scale_id",
    "weather_wind_direction_id",
    "weather_lighting_source_id",
    "weather_current_direction_id",
    "weather_ice_condition_onboard_id",
    "weather_ice_condition_at_sea_id",
    "weather_light_condition_id",
)
WEATHER_TEXT_FIELDS = (
    "weather_current_strength_knots",
    "weather_ambient_temperature_c",
)


def _existing_tables(schema_editor) -> set[str]:
    return {table.lower() for table in schema_editor.connection.introspection.table_names()}


def _existing_columns(schema_editor, table_name: str) -> set[str]:
    with schema_editor.connection.cursor() as cursor:
        return {
            column.name.lower()
            for column in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }


def _ensure_weather_option_table(apps, schema_editor) -> None:
    if schema_editor.connection.vendor == "microsoft":
        with schema_editor.connection.cursor() as cursor:
            _ensure_sql_server_weather_option_table(cursor)
        return

    if WEATHER_OPTION_TABLE.lower() in _existing_tables(schema_editor):
        return

    IncidentWeatherOption = apps.get_model("safety", "IncidentWeatherOption")
    schema_editor.create_model(IncidentWeatherOption)


def _ensure_incident_weather_columns(apps, schema_editor) -> None:
    if schema_editor.connection.vendor == "microsoft":
        with schema_editor.connection.cursor() as cursor:
            _ensure_sql_server_incident_weather_columns(cursor)
        return

    existing_columns = _existing_columns(schema_editor, INCIDENT_TABLE)
    Incident = apps.get_model("safety", "Incident")
    for field_name in (*WEATHER_OPTION_FIELDS, *WEATHER_TEXT_FIELDS):
        if field_name.lower() not in existing_columns:
            schema_editor.add_field(Incident, Incident._meta.get_field(field_name))


def _ensure_sql_server_weather_option_table(cursor) -> None:
    cursor.execute(
        f"""
        IF OBJECT_ID(N'dbo.{WEATHER_OPTION_TABLE}', N'U') IS NULL
        BEGIN
            CREATE TABLE dbo.{WEATHER_OPTION_TABLE} (
                id CHAR(32) NOT NULL
                    CONSTRAINT df_{WEATHER_OPTION_TABLE}_id DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', ''))
                    CONSTRAINT pk_{WEATHER_OPTION_TABLE} PRIMARY KEY,
                field_key VARCHAR(32) NOT NULL,
                option_label NVARCHAR(128) NOT NULL,
                display_order SMALLINT NOT NULL
                    CONSTRAINT df_{WEATHER_OPTION_TABLE}_display_order DEFAULT 0,
                active BIT NOT NULL
                    CONSTRAINT df_{WEATHER_OPTION_TABLE}_active DEFAULT 1,
                created_by NVARCHAR(128) NOT NULL
                    CONSTRAINT df_{WEATHER_OPTION_TABLE}_created_by DEFAULT N'system',
                created_date DATETIME2 NOT NULL
                    CONSTRAINT df_{WEATHER_OPTION_TABLE}_created_date DEFAULT SYSUTCDATETIME(),
                updated_by NVARCHAR(128) NULL,
                updated_date DATETIME2 NULL
            );
        END

        IF OBJECT_ID(N'dbo.{WEATHER_OPTION_TABLE}', N'U') IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM sys.key_constraints
            WHERE name = N'uq_inc_weather_option_field_label'
              AND parent_object_id = OBJECT_ID(N'dbo.{WEATHER_OPTION_TABLE}')
        )
        BEGIN
            ALTER TABLE dbo.{WEATHER_OPTION_TABLE}
            ADD CONSTRAINT uq_inc_weather_option_field_label UNIQUE (field_key, option_label);
        END

        IF OBJECT_ID(N'dbo.{WEATHER_OPTION_TABLE}', N'U') IS NOT NULL
        AND NOT EXISTS (
            SELECT 1
            FROM sys.indexes
            WHERE name = N'ix_inc_weather_option_lookup'
              AND object_id = OBJECT_ID(N'dbo.{WEATHER_OPTION_TABLE}')
        )
        BEGIN
            CREATE INDEX ix_inc_weather_option_lookup
            ON dbo.{WEATHER_OPTION_TABLE} (active, field_key, display_order);
        END
        """
    )
    _ensure_sql_server_weather_option_table_id(cursor)


def _ensure_sql_server_weather_option_table_id(cursor) -> None:
    cursor.execute(
        f"""
        IF OBJECT_ID(N'dbo.{WEATHER_OPTION_TABLE}', N'U') IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = N'dbo'
              AND TABLE_NAME = N'{WEATHER_OPTION_TABLE}'
              AND COLUMN_NAME = N'id'
              AND DATA_TYPE = N'uniqueidentifier'
        )
        BEGIN
            DECLARE @weather_pk_name SYSNAME;
            DECLARE @weather_default_name SYSNAME;
            DECLARE @weather_sql NVARCHAR(MAX);

            SELECT @weather_pk_name = kc.name
            FROM sys.key_constraints kc
            WHERE kc.parent_object_id = OBJECT_ID(N'dbo.{WEATHER_OPTION_TABLE}')
              AND kc.type = 'PK';

            IF @weather_pk_name IS NOT NULL
            BEGIN
                SET @weather_sql = N'ALTER TABLE dbo.{WEATHER_OPTION_TABLE} DROP CONSTRAINT ' + QUOTENAME(@weather_pk_name);
                EXEC sp_executesql @weather_sql;
            END

            SELECT @weather_default_name = dc.name
            FROM sys.default_constraints dc
            JOIN sys.columns c ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
            WHERE dc.parent_object_id = OBJECT_ID(N'dbo.{WEATHER_OPTION_TABLE}')
              AND c.name = N'id';

            IF @weather_default_name IS NOT NULL
            BEGIN
                SET @weather_sql = N'ALTER TABLE dbo.{WEATHER_OPTION_TABLE} DROP CONSTRAINT ' + QUOTENAME(@weather_default_name);
                EXEC sp_executesql @weather_sql;
            END

            ALTER TABLE dbo.{WEATHER_OPTION_TABLE} ADD id_char32 CHAR(32) NULL;
            EXEC(N'UPDATE dbo.{WEATHER_OPTION_TABLE}
                  SET id_char32 = LOWER(REPLACE(CONVERT(CHAR(36), id), ''-'', ''''))
                  WHERE id IS NOT NULL');
            ALTER TABLE dbo.{WEATHER_OPTION_TABLE} ALTER COLUMN id_char32 CHAR(32) NOT NULL;
            ALTER TABLE dbo.{WEATHER_OPTION_TABLE} DROP COLUMN id;
            EXEC sp_rename N'dbo.{WEATHER_OPTION_TABLE}.id_char32', N'id', N'COLUMN';
            ALTER TABLE dbo.{WEATHER_OPTION_TABLE}
                ADD CONSTRAINT pk_{WEATHER_OPTION_TABLE} PRIMARY KEY (id);
            ALTER TABLE dbo.{WEATHER_OPTION_TABLE}
                ADD CONSTRAINT df_{WEATHER_OPTION_TABLE}_id DEFAULT LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')) FOR id;
        END
        """
    )


def _ensure_sql_server_incident_weather_columns(cursor) -> None:
    for column_name in WEATHER_TEXT_FIELDS:
        cursor.execute(
            f"""
            IF COL_LENGTH(N'dbo.{INCIDENT_TABLE}', N'{column_name}') IS NULL
                ALTER TABLE dbo.{INCIDENT_TABLE} ADD {column_name} NVARCHAR(MAX) NULL;
            """
        )
    for column_name in WEATHER_OPTION_FIELDS:
        cursor.execute(
            f"""
            IF COL_LENGTH(N'dbo.{INCIDENT_TABLE}', N'{column_name}') IS NULL
            BEGIN
                ALTER TABLE dbo.{INCIDENT_TABLE} ADD {column_name} CHAR(32) NULL;
            END
            ELSE IF EXISTS (
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = N'dbo'
                  AND TABLE_NAME = N'{INCIDENT_TABLE}'
                  AND COLUMN_NAME = N'{column_name}'
                  AND DATA_TYPE = N'uniqueidentifier'
            )
            BEGIN
                ALTER TABLE dbo.{INCIDENT_TABLE} ADD {column_name}_char32 CHAR(32) NULL;
                EXEC(N'UPDATE dbo.{INCIDENT_TABLE}
                      SET {column_name}_char32 = LOWER(REPLACE(CONVERT(CHAR(36), {column_name}), ''-'', ''''))
                      WHERE {column_name} IS NOT NULL');
                ALTER TABLE dbo.{INCIDENT_TABLE} DROP COLUMN {column_name};
                EXEC sp_rename N'dbo.{INCIDENT_TABLE}.{column_name}_char32', N'{column_name}', N'COLUMN';
            END
            """
        )


def _incident_weather_option_state_operation() -> migrations.CreateModel:
    return migrations.CreateModel(
        name="IncidentWeatherOption",
        fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            (
                "field_key",
                models.CharField(
                    choices=[
                        ("VISIBILITY", "Visibility"),
                        ("PRECIPITATION", "Precipitation"),
                        ("SEA_STATE", "Sea State"),
                        ("WIND_SCALE", "Wind Scale"),
                        ("WIND_DIRECTION", "Wind Direction"),
                        ("LIGHTING_SOURCE", "Source of Lighting"),
                        ("CURRENT_DIRECTION", "Current Direction"),
                        ("ICE_CONDITION_ONBOARD", "Ice condition on-board"),
                        ("ICE_CONDITION_AT_SEA", "Ice condition at sea"),
                        ("LIGHT_CONDITION", "Light condition"),
                    ],
                    db_index=True,
                    max_length=32,
                ),
            ),
            ("option_label", models.CharField(max_length=128)),
            ("display_order", models.PositiveSmallIntegerField(default=0)),
            ("active", models.BooleanField(default=True)),
            ("created_by", models.CharField(default="system", max_length=128)),
            ("created_date", models.DateTimeField(auto_now_add=True)),
            ("updated_by", models.CharField(blank=True, max_length=128, null=True)),
            ("updated_date", models.DateTimeField(blank=True, null=True)),
        ],
        options={
            "db_table": WEATHER_OPTION_TABLE,
            "ordering": ("field_key", "display_order", "option_label"),
            "constraints": [
                models.UniqueConstraint(
                    fields=("field_key", "option_label"),
                    name="uq_inc_weather_option_field_label",
                ),
            ],
            "indexes": [
                models.Index(
                    fields=("active", "field_key", "display_order"),
                    name="ix_inc_weather_option_lookup",
                ),
            ],
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0042_near_miss_rejected_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[_incident_weather_option_state_operation()],
        ),
        migrations.RunPython(_ensure_weather_option_table, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="incident",
                    name="weather_visibility_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_precipitation_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_sea_state_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_wind_scale_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_wind_direction_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_lighting_source_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_current_direction_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_current_strength_knots",
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_ambient_temperature_c",
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_ice_condition_onboard_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_ice_condition_at_sea_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="incident",
                    name="weather_light_condition_id",
                    field=models.UUIDField(blank=True, null=True),
                ),
            ],
        ),
        migrations.RunPython(_ensure_incident_weather_columns, migrations.RunPython.noop),
    ]
