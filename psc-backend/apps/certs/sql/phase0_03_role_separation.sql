/*
Phase 0.3 - Certs database role separation.

Traceability:
- IMPLEMENTATION_PLAN.md step 0.3
- PRD FEAT-CERT-AUDIT-001
- BACKEND_STRUCTURE.md section 2
- FIELD_MAP.md sections 9 and 23
- SECURITY.md SEC-CERT-01 and SEC-CERT-16

This step provisions database roles only. The Certs tables are created in
Phase 0.4, so object-level GRANTs are intentionally not applied here.
Do not replace this with broad schema grants.
*/

USE [ksm_marine_live];
GO

SET NOCOUNT ON;
GO

IF DATABASE_PRINCIPAL_ID(N'vims_app') IS NULL
BEGIN
    CREATE ROLE [vims_app] AUTHORIZATION [dbo];
END;
GO

IF DATABASE_PRINCIPAL_ID(N'vims_admin') IS NULL
BEGIN
    CREATE ROLE [vims_admin] AUTHORIZATION [dbo];
END;
GO

IF DATABASE_PRINCIPAL_ID(N'vims_jobs') IS NULL
BEGIN
    CREATE ROLE [vims_jobs] AUTHORIZATION [dbo];
END;
GO

SELECT
    name,
    type_desc,
    create_date,
    modify_date
FROM sys.database_principals
WHERE name IN (N'vims_app', N'vims_admin', N'vims_jobs')
ORDER BY name;
GO

SELECT
    grantee.name AS grantee_name,
    permission.class_desc,
    OBJECT_SCHEMA_NAME(permission.major_id) AS object_schema,
    OBJECT_NAME(permission.major_id) AS object_name,
    permission.permission_name,
    permission.state_desc
FROM sys.database_permissions AS permission
JOIN sys.database_principals AS grantee
    ON permission.grantee_principal_id = grantee.principal_id
WHERE grantee.name IN (N'vims_app', N'vims_admin', N'vims_jobs')
ORDER BY
    grantee.name,
    object_schema,
    object_name,
    permission.permission_name;
GO
