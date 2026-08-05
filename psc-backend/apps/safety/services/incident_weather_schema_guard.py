from __future__ import annotations

from django.db import connection


INCIDENT_TABLE = "vims_safety_incident"
WEATHER_OPTION_TABLE = "vims_safety_incident_weather_option"
WEATHER_OPTION_SEEDS = [
    ("VISIBILITY", "Good: More than 5 nautical miles"),
    ("VISIBILITY", "Moderate: Between 2 and 5 nautical miles"),
    ("VISIBILITY", "Poor: Between 1000 meters and 2 nautical miles"),
    ("VISIBILITY", "Very Poor: Less than 1000 meters"),
    ("PRECIPITATION", "No Rain / Hail / Snow"),
    ("PRECIPITATION", "Rain Showers"),
    ("PRECIPITATION", "Light Rain"),
    ("PRECIPITATION", "Heavy Rain"),
    ("PRECIPITATION", "Rain Storm"),
    ("PRECIPITATION", "Light Hail"),
    ("PRECIPITATION", "Heavy Hail"),
    ("PRECIPITATION", "Hail Storm"),
    ("PRECIPITATION", "Light Snow"),
    ("PRECIPITATION", "Heavy Snow"),
    ("PRECIPITATION", "Snow Storm"),
    ("SEA_STATE", "0: Calm (Glassy)"),
    ("SEA_STATE", "1: Calm (Rippled)"),
    ("SEA_STATE", "2: Smooth"),
    ("SEA_STATE", "3: Slight"),
    ("SEA_STATE", "4: Moderate"),
    ("SEA_STATE", "5: Rough"),
    ("SEA_STATE", "6: Very Rough"),
    ("SEA_STATE", "7: High"),
    ("SEA_STATE", "8: Very High"),
    ("SEA_STATE", "9: Phenomenal"),
    ("WIND_SCALE", "0: Calm"),
    ("WIND_SCALE", "1: Light Air"),
    ("WIND_SCALE", "2: Light Breeze"),
    ("WIND_SCALE", "3: Gentle Breeze"),
    ("WIND_SCALE", "4: Moderate Breeze"),
    ("WIND_SCALE", "5: Fresh Breeze"),
    ("WIND_SCALE", "6: Strong Breeze"),
    ("WIND_SCALE", "7: High Wind / Moderate Gale / Near Gale"),
    ("WIND_SCALE", "8: Gale / Fresh Gale"),
    ("WIND_SCALE", "9: Strong Gale"),
    ("WIND_SCALE", "10: Storm / Whole Gale"),
    ("WIND_SCALE", "11: Violent Storm"),
    ("WIND_SCALE", "12: Hurricane Force"),
    ("WIND_DIRECTION", "N"),
    ("WIND_DIRECTION", "NE"),
    ("WIND_DIRECTION", "E"),
    ("WIND_DIRECTION", "SE"),
    ("WIND_DIRECTION", "S"),
    ("WIND_DIRECTION", "SW"),
    ("WIND_DIRECTION", "W"),
    ("WIND_DIRECTION", "NW"),
    ("CURRENT_DIRECTION", "N"),
    ("CURRENT_DIRECTION", "NE"),
    ("CURRENT_DIRECTION", "E"),
    ("CURRENT_DIRECTION", "SE"),
    ("CURRENT_DIRECTION", "S"),
    ("CURRENT_DIRECTION", "SW"),
    ("CURRENT_DIRECTION", "W"),
    ("CURRENT_DIRECTION", "NW"),
    ("LIGHTING_SOURCE", "Artificial"),
    ("LIGHTING_SOURCE", "Natural"),
    ("LIGHTING_SOURCE", "Darkness"),
    ("ICE_CONDITION_ONBOARD", "No ice"),
    ("ICE_CONDITION_ONBOARD", "Light"),
    ("ICE_CONDITION_ONBOARD", "Moderate"),
    ("ICE_CONDITION_ONBOARD", "Heavy"),
    ("ICE_CONDITION_AT_SEA", "Open Water"),
    ("ICE_CONDITION_AT_SEA", "Bergy Water"),
    ("ICE_CONDITION_AT_SEA", "Brash (ice fragments < 2 m)"),
    ("ICE_CONDITION_AT_SEA", "New Ice (N)"),
    ("ICE_CONDITION_AT_SEA", "Nilas, Ice Rind"),
    ("ICE_CONDITION_AT_SEA", "Grey Ice (G)"),
    ("ICE_CONDITION_AT_SEA", "Grey-White Ice (GW)"),
    ("ICE_CONDITION_AT_SEA", "Thin First-Year Ice - 1st Stage"),
    ("ICE_CONDITION_AT_SEA", "Thin First-Year Ice - 2nd Stage"),
    ("ICE_CONDITION_AT_SEA", "Thin First-Year Ice (FY)"),
    ("ICE_CONDITION_AT_SEA", "Medium First-Year Ice (MFY)"),
    ("ICE_CONDITION_AT_SEA", "Thick First-Year Ice (TFY)"),
    ("ICE_CONDITION_AT_SEA", "Second-Year Ice (SY)"),
    ("ICE_CONDITION_AT_SEA", "Old / Multi-Year Ice (MY)"),
    ("LIGHT_CONDITION", "Full light"),
    ("LIGHT_CONDITION", "Full dark"),
    ("LIGHT_CONDITION", "Dusk"),
    ("LIGHT_CONDITION", "Dawn"),
]

WEATHER_INCIDENT_OPTION_COLUMNS = (
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


def ensure_incident_weather_runtime_schema() -> None:
    """Keep incident weather fields usable on DBs not yet migrated."""
    if connection.vendor == "microsoft":
        _ensure_sql_server_weather_schema()


def _ensure_sql_server_weather_schema() -> None:
    with connection.cursor() as cursor:
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

            IF COL_LENGTH(N'dbo.{INCIDENT_TABLE}', N'weather_current_strength_knots') IS NULL
                ALTER TABLE dbo.{INCIDENT_TABLE} ADD weather_current_strength_knots NVARCHAR(MAX) NULL;
            IF COL_LENGTH(N'dbo.{INCIDENT_TABLE}', N'weather_ambient_temperature_c') IS NULL
                ALTER TABLE dbo.{INCIDENT_TABLE} ADD weather_ambient_temperature_c NVARCHAR(MAX) NULL;
            """
        )
        _ensure_sql_server_weather_option_table_id(cursor)
        _ensure_sql_server_incident_weather_columns(cursor)
        cursor.executemany(
            f"""
            IF NOT EXISTS (
                SELECT 1
                FROM dbo.{WEATHER_OPTION_TABLE}
                WHERE field_key = %s
                  AND option_label = %s
            )
            BEGIN
                INSERT INTO dbo.{WEATHER_OPTION_TABLE}
                    (id, field_key, option_label, display_order, active, created_by, created_date)
                VALUES
                    (LOWER(REPLACE(CONVERT(CHAR(36), NEWID()), '-', '')), %s, %s, %s, 1, N'runtime_guard', SYSUTCDATETIME());
            END
            """,
            [
                (field_key, option_label, field_key, option_label, display_order)
                for display_order, (field_key, option_label) in enumerate(WEATHER_OPTION_SEEDS, start=1)
            ],
        )


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
    for column_name in WEATHER_INCIDENT_OPTION_COLUMNS:
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
