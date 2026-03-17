# BACKEND_STRUCTURE.md — Database Schema & API Contracts
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.0 | **Date:** 2026-02-04 | **Status:** APPROVED

---

## 1. Database Overview

| Property | Value |
|----------|-------|
| Database | `ksm_marine_live` |
| Server | SQL Server 2019 |
| Schema | `dbo` |
| Primary Key Type | `uniqueidentifier` (UUID) |
| Soft Delete | `is_deleted bit DEFAULT 0` |
| Audit Pattern | `created_by`, `created_date`, `updated_by`, `updated_date` |

### 1.1 Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Master Tables | `master_{name}` | `master_psc_def_code` |
| Transaction Tables | `psc_{name}` | `psc_inspection` |
| Stored Procedures | `usp_{action}_{entity}` | `usp_get_inspections` |
| Views | `vw_{name}` | `vw_inspection_summary` |
| Indexes | `IX_{table}_{columns}` | `IX_psc_inspection_vessel_id` |

---

## 2. Existing Tables (Reference Only — DO NOT MODIFY)

These tables exist in the shared database. The PSC module will **READ** from them.

### 2.1 VesselData
```sql
-- Existing table - DO NOT MODIFY
-- Key fields for PSC module:
SELECT 
    id,                    -- uniqueidentifier, PK
    vesselName,            -- varchar(max)
    vesselCode,            -- varchar(50), 3-char code
    flags,                 -- varchar(max), flag state
    imoNumber,             -- varchar(max)
    is_active,             -- bit
    is_deleted             -- bit
FROM VesselData
WHERE is_deleted = 0 AND is_active = 1;
```

### 2.2 HRM501 (Crew)
```sql
-- Existing table - DO NOT MODIFY
-- Key fields for PSC module:
SELECT 
    id,                    -- uniqueidentifier, PK
    CrewID,                -- varchar(7), display ID (KSM0001)
    first_name,            -- varchar(max)
    surname,               -- varchar(max)
    rank_name,             -- varchar(max)
    department_name,       -- varchar(max)
    user_id,               -- varchar(max)
    is_active,             -- bit
    is_deleted             -- bit
FROM HRM501
WHERE is_deleted = 0 AND is_active = 1;
```

### 2.3 users (Office Users)
```sql
-- Existing table - DO NOT MODIFY
-- Key fields for PSC module:
SELECT 
    employee_id,           -- varchar(20), PK
    employee_name,         -- varchar(100)
    display_name,          -- varchar(100)
    email_id,              -- varchar(100)
    username,              -- varchar(100)
    employee_role,         -- varchar(45)
    department,            -- varchar(max)
    is_active,             -- bit
    is_deleted             -- bit
FROM users
WHERE is_deleted = 0 AND is_active = 1;
```

### 2.4 master_RoleByVessel (Vessel Access)
```sql
-- Existing table - DO NOT MODIFY
-- Used for office user vessel filtering
SELECT 
    Id,                    -- uniqueidentifier, PK
    VesselId,              -- uniqueidentifier, FK to VesselData
    RoleId,                -- uniqueidentifier, FK to master_role
    UserId,                -- nvarchar(100), FK to users.employee_id
    IsActive,              -- bit
    is_deleted             -- bit
FROM master_RoleByVessel
WHERE is_deleted = 0 AND IsActive = 1;
```

### 2.5 master_applied_rank
```sql
-- Existing table - DO NOT MODIFY
SELECT 
    id,                    -- uniqueidentifier, PK
    rank_name,             -- varchar(max)
    rank_id,               -- varchar(max)
    department,            -- uniqueidentifier
    is_active,             -- bit
    is_deleted             -- bit
FROM master_applied_rank
WHERE is_deleted = 0 AND is_active = 1;
```

---

## 3. New Master Tables (PSC Module)

### 3.1 master_psc_def_code
**Purpose:** PSC deficiency codes (IMO standard codes)

```sql
CREATE TABLE [dbo].[master_psc_def_code] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [code] [varchar](10) NOT NULL,              -- e.g., "10101"
    [description] [nvarchar](500) NOT NULL,     -- e.g., "Certificates - International Tonnage"
    [category] [varchar](100) NULL,             -- e.g., "Certificates"
    [is_active] [bit] NOT NULL DEFAULT 1,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    
    CONSTRAINT [PK_master_psc_def_code] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [UQ_master_psc_def_code_code] UNIQUE ([code])
);

CREATE INDEX [IX_master_psc_def_code_code] ON [master_psc_def_code]([code]);
CREATE INDEX [IX_master_psc_def_code_category] ON [master_psc_def_code]([category]);
```

### 3.2 master_psc_action_code
**Purpose:** PSC action codes (what was done about deficiency)

```sql
CREATE TABLE [dbo].[master_psc_action_code] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [code] [varchar](10) NOT NULL,              -- e.g., "10", "17", "30"
    [description] [nvarchar](500) NOT NULL,     -- e.g., "Deficiency rectified"
    [is_clearing_code] [bit] NOT NULL DEFAULT 0, -- 1 if this code clears deficiency
    [is_active] [bit] NOT NULL DEFAULT 1,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    
    CONSTRAINT [PK_master_psc_action_code] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [UQ_master_psc_action_code_code] UNIQUE ([code])
);
```

### 3.3 master_mou
**Purpose:** Memorandum of Understanding regions

```sql
CREATE TABLE [dbo].[master_mou] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [code] [varchar](20) NOT NULL,              -- e.g., "TOKYO", "PARIS"
    [name] [nvarchar](200) NOT NULL,            -- e.g., "Tokyo MOU"
    [region] [varchar](100) NULL,               -- e.g., "Asia-Pacific"
    [is_active] [bit] NOT NULL DEFAULT 1,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    
    CONSTRAINT [PK_master_mou] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [UQ_master_mou_code] UNIQUE ([code])
);
```

### 3.4 master_clc_item
**Purpose:** Common Learning Codes for root cause analysis

```sql
CREATE TABLE [dbo].[master_clc_item] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [code] [varchar](20) NOT NULL,              -- e.g., "CLC001"
    [description] [nvarchar](500) NOT NULL,     -- e.g., "Lack of training"
    [category] [varchar](100) NULL,             -- e.g., "Human Factors"
    [is_active] [bit] NOT NULL DEFAULT 1,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    
    CONSTRAINT [PK_master_clc_item] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [UQ_master_clc_item_code] UNIQUE ([code])
);
```

### 3.5 master_psc_role
**Purpose:** PSC module-specific roles

```sql
CREATE TABLE [dbo].[master_psc_role] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [role_code] [varchar](50) NOT NULL,         -- e.g., "VESSEL_MASTER"
    [role_name] [nvarchar](100) NOT NULL,       -- e.g., "Vessel Master"
    [role_type] [varchar](20) NOT NULL,         -- "VESSEL" or "OFFICE"
    [is_active] [bit] NOT NULL DEFAULT 1,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    
    CONSTRAINT [PK_master_psc_role] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [UQ_master_psc_role_code] UNIQUE ([role_code])
);

-- Seed data
INSERT INTO master_psc_role (role_code, role_name, role_type) VALUES
('VESSEL_MASTER', 'Vessel Master', 'VESSEL'),
('VESSEL_CREW', 'Vessel Crew', 'VESSEL'),
('OFFICE_PIC', 'Person In Charge', 'OFFICE'),
('OFFICE_SSQE', 'SSQE Officer', 'OFFICE'),
('OFFICE_SUPT', 'Superintendent', 'OFFICE'),
('DPA', 'Designated Person Ashore', 'OFFICE'),
('PHYSICAL_VERIFIER', 'Physical Verifier', 'OFFICE');
```

---

## 4. Transaction Tables (PSC Module)

### 4.1 psc_inspection
**Purpose:** Main inspection record

```sql
CREATE TABLE [dbo].[psc_inspection] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [vessel_id] [uniqueidentifier] NOT NULL,    -- FK to VesselData.id
    [inspection_type] [varchar](20) NOT NULL,   -- PSC, RS, AUDIT, INTERNAL
    [psc_subtype] [varchar](20) NULL,           -- INITIAL, EXPANDED, CIC, FOLLOW_UP
    [inspection_date] [date] NOT NULL,
    [port_place] [nvarchar](200) NOT NULL,
    [country] [nvarchar](100) NULL,
    [mou_id] [uniqueidentifier] NULL,           -- FK to master_mou.id
    [authority] [nvarchar](200) NULL,
    [inspector_name] [nvarchar](200) NULL,
    [report_reference] [varchar](100) NULL,
    [is_detention] [bit] NOT NULL DEFAULT 0,
    [status] [varchar](20) NOT NULL DEFAULT 'DRAFT',  -- DRAFT, SUBMITTED, PIC_REVIEWED, DPA_CLOSED
    [parent_inspection_id] [uniqueidentifier] NULL,   -- FK self-ref for follow-ups
    [revision_no] [int] NOT NULL DEFAULT 1,
    [pic_comment] [nvarchar](max) NULL,
    [pic_reviewed_by] [varchar](100) NULL,
    [pic_reviewed_at] [datetime] NULL,
    [dpa_comment] [nvarchar](max) NULL,
    [dpa_closed_by] [varchar](100) NULL,
    [dpa_closed_at] [datetime] NULL,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    [client_id] [uniqueidentifier] NULL,        -- For offline sync (client-generated ID)
    [sync_version] [int] NOT NULL DEFAULT 1,    -- For conflict detection
    
    CONSTRAINT [PK_psc_inspection] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_inspection_vessel] FOREIGN KEY ([vessel_id]) 
        REFERENCES [VesselData]([id]),
    CONSTRAINT [FK_psc_inspection_mou] FOREIGN KEY ([mou_id]) 
        REFERENCES [master_mou]([id]),
    CONSTRAINT [FK_psc_inspection_parent] FOREIGN KEY ([parent_inspection_id]) 
        REFERENCES [psc_inspection]([id]),
    CONSTRAINT [CK_psc_inspection_type] CHECK ([inspection_type] IN ('PSC', 'RS', 'AUDIT', 'INTERNAL')),
    CONSTRAINT [CK_psc_inspection_subtype] CHECK ([psc_subtype] IS NULL OR [psc_subtype] IN ('INITIAL', 'EXPANDED', 'CIC', 'FOLLOW_UP')),
    CONSTRAINT [CK_psc_inspection_status] CHECK ([status] IN ('DRAFT', 'SUBMITTED', 'PIC_REVIEWED', 'DPA_CLOSED'))
);

CREATE INDEX [IX_psc_inspection_vessel_id] ON [psc_inspection]([vessel_id]);
CREATE INDEX [IX_psc_inspection_status] ON [psc_inspection]([status]);
CREATE INDEX [IX_psc_inspection_date] ON [psc_inspection]([inspection_date] DESC);
CREATE INDEX [IX_psc_inspection_type] ON [psc_inspection]([inspection_type]);
```

### 4.2 psc_inspection_report
**Purpose:** Inspection report PDF attachments

```sql
CREATE TABLE [dbo].[psc_inspection_report] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [inspection_id] [uniqueidentifier] NOT NULL,  -- FK to psc_inspection.id
    [file_name] [nvarchar](255) NOT NULL,
    [file_path] [nvarchar](500) NOT NULL,
    [file_size] [int] NULL,                     -- bytes
    [mime_type] [varchar](100) NOT NULL DEFAULT 'application/pdf',
    [description] [nvarchar](500) NULL,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [uploaded_by] [varchar](100) NULL,
    [uploaded_at] [datetime] NULL DEFAULT GETDATE(),
    
    CONSTRAINT [PK_psc_inspection_report] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_inspection_report_inspection] FOREIGN KEY ([inspection_id]) 
        REFERENCES [psc_inspection]([id])
);

CREATE INDEX [IX_psc_inspection_report_inspection_id] ON [psc_inspection_report]([inspection_id]);
```

### 4.3 psc_deficiency
**Purpose:** Individual deficiency within an inspection

```sql
CREATE TABLE [dbo].[psc_deficiency] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [inspection_id] [uniqueidentifier] NOT NULL,  -- FK to psc_inspection.id
    [def_code_id] [uniqueidentifier] NOT NULL,    -- FK to master_psc_def_code.id
    [def_code] [varchar](10) NOT NULL,            -- Denormalized for display
    [description] [nvarchar](max) NOT NULL,
    [action_code_id] [uniqueidentifier] NULL,     -- FK to master_psc_action_code.id
    [action_code] [varchar](10) NULL,             -- Denormalized for display
    [target_date] [date] NULL,
    [is_cleared] [bit] NOT NULL DEFAULT 0,
    [cleared_date] [date] NULL,
    [cleared_by_follow_up_id] [uniqueidentifier] NULL,  -- FK to psc_inspection.id (follow-up)
    [sequence_no] [int] NOT NULL DEFAULT 1,       -- Order within inspection
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    [client_id] [uniqueidentifier] NULL,
    [sync_version] [int] NOT NULL DEFAULT 1,
    
    CONSTRAINT [PK_psc_deficiency] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_deficiency_inspection] FOREIGN KEY ([inspection_id]) 
        REFERENCES [psc_inspection]([id]),
    CONSTRAINT [FK_psc_deficiency_def_code] FOREIGN KEY ([def_code_id]) 
        REFERENCES [master_psc_def_code]([id]),
    CONSTRAINT [FK_psc_deficiency_action_code] FOREIGN KEY ([action_code_id]) 
        REFERENCES [master_psc_action_code]([id]),
    CONSTRAINT [FK_psc_deficiency_follow_up] FOREIGN KEY ([cleared_by_follow_up_id]) 
        REFERENCES [psc_inspection]([id])
);

CREATE INDEX [IX_psc_deficiency_inspection_id] ON [psc_deficiency]([inspection_id]);
CREATE INDEX [IX_psc_deficiency_def_code] ON [psc_deficiency]([def_code]);
CREATE INDEX [IX_psc_deficiency_is_cleared] ON [psc_deficiency]([is_cleared]);
```

### 4.4 psc_deficiency_action_history
**Purpose:** Track action code changes over time

```sql
CREATE TABLE [dbo].[psc_deficiency_action_history] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [deficiency_id] [uniqueidentifier] NOT NULL,
    [previous_action_code_id] [uniqueidentifier] NULL,
    [new_action_code_id] [uniqueidentifier] NOT NULL,
    [previous_action_code] [varchar](10) NULL,
    [new_action_code] [varchar](10) NOT NULL,
    [follow_up_inspection_id] [uniqueidentifier] NULL,
    [change_reason] [nvarchar](500) NULL,
    [changed_by] [varchar](100) NOT NULL,
    [changed_at] [datetime] NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT [PK_psc_deficiency_action_history] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_def_action_hist_deficiency] FOREIGN KEY ([deficiency_id]) 
        REFERENCES [psc_deficiency]([id])
);

CREATE INDEX [IX_psc_def_action_history_deficiency_id] ON [psc_deficiency_action_history]([deficiency_id]);
```

### 4.5 psc_car
**Purpose:** Corrective Action Report (1:1 with deficiency)

```sql
CREATE TABLE [dbo].[psc_car] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [deficiency_id] [uniqueidentifier] NOT NULL UNIQUE,  -- 1:1 relationship
    [car_number] [varchar](20) NOT NULL,          -- PSC-2026-001
    [status] [varchar](30) NOT NULL DEFAULT 'DRAFT',  -- DRAFT, SUBMITTED, PIC_ACCEPTED, REWORK_REQUESTED, DPA_CLOSED
    [root_cause_summary] [nvarchar](max) NULL,
    [target_date] [date] NULL,
    
    -- PIC Review
    [pic_comment] [nvarchar](max) NULL,
    [pic_accepted_by] [varchar](100) NULL,
    [pic_accepted_at] [datetime] NULL,
    
    -- Rework
    [rework_reason] [nvarchar](max) NULL,
    [rework_requested_by] [varchar](100) NULL,
    [rework_requested_at] [datetime] NULL,
    [rework_count] [int] NOT NULL DEFAULT 0,
    
    -- DPA Closure
    [dpa_comment] [nvarchar](max) NULL,
    [dpa_closed_by] [varchar](100) NULL,
    [dpa_closed_at] [datetime] NULL,
    
    [revision_no] [int] NOT NULL DEFAULT 1,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    [client_id] [uniqueidentifier] NULL,
    [sync_version] [int] NOT NULL DEFAULT 1,
    
    CONSTRAINT [PK_psc_car] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_car_deficiency] FOREIGN KEY ([deficiency_id]) 
        REFERENCES [psc_deficiency]([id]),
    CONSTRAINT [UQ_psc_car_number] UNIQUE ([car_number]),
    CONSTRAINT [CK_psc_car_status] CHECK ([status] IN ('DRAFT', 'SUBMITTED', 'PIC_ACCEPTED', 'REWORK_REQUESTED', 'DPA_CLOSED'))
);

CREATE INDEX [IX_psc_car_deficiency_id] ON [psc_car]([deficiency_id]);
CREATE INDEX [IX_psc_car_status] ON [psc_car]([status]);
CREATE INDEX [IX_psc_car_number] ON [psc_car]([car_number]);
```

### 4.6 psc_car_clc_mapping
**Purpose:** Multiple CLC codes per CAR (many-to-many)

```sql
CREATE TABLE [dbo].[psc_car_clc_mapping] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [car_id] [uniqueidentifier] NOT NULL,
    [clc_item_id] [uniqueidentifier] NOT NULL,
    [custom_cause_text] [nvarchar](500) NULL,     -- If CLC not sufficient
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    
    CONSTRAINT [PK_psc_car_clc_mapping] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_car_clc_car] FOREIGN KEY ([car_id]) 
        REFERENCES [psc_car]([id]),
    CONSTRAINT [FK_psc_car_clc_item] FOREIGN KEY ([clc_item_id]) 
        REFERENCES [master_clc_item]([id])
);

CREATE INDEX [IX_psc_car_clc_mapping_car_id] ON [psc_car_clc_mapping]([car_id]);
```

### 4.7 psc_corrective_action
**Purpose:** Individual corrective actions within a CAR

```sql
CREATE TABLE [dbo].[psc_corrective_action] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [car_id] [uniqueidentifier] NOT NULL,
    [action_type] [varchar](20) NOT NULL,         -- IMMEDIATE, LONG_TERM
    [description] [nvarchar](max) NOT NULL,
    [owner_crew_id] [uniqueidentifier] NULL,      -- FK to HRM501.id (vessel crew)
    [owner_user_id] [varchar](100) NULL,          -- FK to users.employee_id (office)
    [due_date] [date] NULL,
    [is_completed] [bit] NOT NULL DEFAULT 0,
    [completed_at] [datetime] NULL,
    [completion_remarks] [nvarchar](max) NULL,
    [sequence_no] [int] NOT NULL DEFAULT 1,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    [client_id] [uniqueidentifier] NULL,
    [sync_version] [int] NOT NULL DEFAULT 1,
    
    CONSTRAINT [PK_psc_corrective_action] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_corrective_action_car] FOREIGN KEY ([car_id]) 
        REFERENCES [psc_car]([id]),
    CONSTRAINT [CK_psc_corrective_action_type] CHECK ([action_type] IN ('IMMEDIATE', 'LONG_TERM'))
);

CREATE INDEX [IX_psc_corrective_action_car_id] ON [psc_corrective_action]([car_id]);
CREATE INDEX [IX_psc_corrective_action_owner_crew] ON [psc_corrective_action]([owner_crew_id]);
CREATE INDEX [IX_psc_corrective_action_is_completed] ON [psc_corrective_action]([is_completed]);
```

### 4.8 psc_evidence
**Purpose:** Evidence files (photos, documents) for CAR

```sql
CREATE TABLE [dbo].[psc_evidence] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [car_id] [uniqueidentifier] NOT NULL,
    [evidence_type] [varchar](20) NOT NULL,       -- BEFORE, AFTER, EVIDENCE, OTHER
    [file_name] [nvarchar](255) NOT NULL,
    [file_path] [nvarchar](500) NOT NULL,
    [file_size] [int] NULL,                       -- bytes
    [mime_type] [varchar](100) NOT NULL,
    [description] [nvarchar](500) NOT NULL,       -- Mandatory
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [uploaded_by] [varchar](100) NULL,
    [uploaded_at] [datetime] NULL DEFAULT GETDATE(),
    [client_id] [uniqueidentifier] NULL,
    [sync_status] [varchar](20) NOT NULL DEFAULT 'SYNCED',  -- PENDING, SYNCED, FAILED
    
    CONSTRAINT [PK_psc_evidence] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_evidence_car] FOREIGN KEY ([car_id]) 
        REFERENCES [psc_car]([id]),
    CONSTRAINT [CK_psc_evidence_type] CHECK ([evidence_type] IN ('BEFORE', 'AFTER', 'EVIDENCE', 'OTHER')),
    CONSTRAINT [CK_psc_evidence_mime] CHECK ([mime_type] IN ('application/pdf', 'image/jpeg', 'image/jpg'))
);

CREATE INDEX [IX_psc_evidence_car_id] ON [psc_evidence]([car_id]);
CREATE INDEX [IX_psc_evidence_type] ON [psc_evidence]([evidence_type]);
```

### 4.9 psc_physical_verification
**Purpose:** Physical verification visits for closed CARs

```sql
CREATE TABLE [dbo].[psc_physical_verification] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [car_id] [uniqueidentifier] NOT NULL,
    [status] [varchar](20) NOT NULL DEFAULT 'OPEN',  -- OPEN, CLOSED
    [scheduled_date] [date] NULL,
    [visit_date] [date] NULL,
    [visit_port] [nvarchar](200) NULL,
    [verifier_user_id] [varchar](100) NULL,       -- FK to users.employee_id
    [verifier_crew_id] [uniqueidentifier] NULL,   -- FK to HRM501.id (if crew verifies)
    [comments] [nvarchar](max) NULL,
    [is_deleted] [bit] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    [updated_by] [varchar](100) NULL,
    [updated_date] [datetime] NULL,
    [closed_by] [varchar](100) NULL,
    [closed_at] [datetime] NULL,
    
    CONSTRAINT [PK_psc_physical_verification] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_physical_verification_car] FOREIGN KEY ([car_id]) 
        REFERENCES [psc_car]([id]),
    CONSTRAINT [CK_psc_pv_status] CHECK ([status] IN ('OPEN', 'CLOSED'))
);

CREATE INDEX [IX_psc_physical_verification_car_id] ON [psc_physical_verification]([car_id]);
CREATE INDEX [IX_psc_physical_verification_status] ON [psc_physical_verification]([status]);
```

---

## 5. Activity & Audit Tables

### 5.1 psc_activity_history
**Purpose:** User-visible activity timeline (synced to vessels)

```sql
CREATE TABLE [dbo].[psc_activity_history] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [entity_type] [varchar](30) NOT NULL,         -- INSPECTION, DEFICIENCY, CAR, EVIDENCE, ACTION
    [entity_id] [uniqueidentifier] NOT NULL,
    [vessel_id] [uniqueidentifier] NOT NULL,      -- For sync filtering
    [event_type] [varchar](50) NOT NULL,          -- See event types below
    [event_description] [nvarchar](500) NOT NULL,
    [performed_by] [varchar](100) NOT NULL,
    [performed_by_name] [nvarchar](200) NULL,
    [performed_at] [datetime] NOT NULL DEFAULT GETDATE(),
    [metadata] [nvarchar](max) NULL,              -- JSON for additional data
    
    CONSTRAINT [PK_psc_activity_history] PRIMARY KEY CLUSTERED ([id] ASC)
);

CREATE INDEX [IX_psc_activity_history_entity] ON [psc_activity_history]([entity_type], [entity_id]);
CREATE INDEX [IX_psc_activity_history_vessel] ON [psc_activity_history]([vessel_id]);
CREATE INDEX [IX_psc_activity_history_performed_at] ON [psc_activity_history]([performed_at] DESC);

-- Event Types:
-- INSPECTION_CREATED, INSPECTION_SUBMITTED, INSPECTION_PIC_REVIEWED, INSPECTION_DPA_CLOSED
-- DEFICIENCY_ADDED, DEFICIENCY_CLEARED, DEFICIENCY_ACTION_UPDATED
-- CAR_CREATED, CAR_SUBMITTED, CAR_PIC_ACCEPTED, CAR_REWORK_REQUESTED, CAR_DPA_CLOSED
-- EVIDENCE_UPLOADED, EVIDENCE_DELETED
-- ACTION_COMPLETED
```

### 5.2 psc_audit_log
**Purpose:** Detailed field-level audit trail (Office only, NOT synced to vessels)

```sql
CREATE TABLE [dbo].[psc_audit_log] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [entity_type] [varchar](30) NOT NULL,
    [entity_id] [uniqueidentifier] NOT NULL,
    [action] [varchar](20) NOT NULL,              -- CREATE, UPDATE, DELETE
    [field_name] [varchar](100) NULL,             -- NULL for CREATE/DELETE
    [old_value] [nvarchar](max) NULL,
    [new_value] [nvarchar](max) NULL,
    [performed_by] [varchar](100) NOT NULL,
    [performed_by_role] [varchar](50) NULL,
    [performed_at] [datetime] NOT NULL DEFAULT GETDATE(),
    [ip_address] [varchar](50) NULL,
    [user_agent] [nvarchar](500) NULL,
    [is_office_edit_assist] [bit] NOT NULL DEFAULT 0,  -- Office editing on behalf of vessel
    
    CONSTRAINT [PK_psc_audit_log] PRIMARY KEY CLUSTERED ([id] ASC)
);

CREATE INDEX [IX_psc_audit_log_entity] ON [psc_audit_log]([entity_type], [entity_id]);
CREATE INDEX [IX_psc_audit_log_performed_at] ON [psc_audit_log]([performed_at] DESC);
CREATE INDEX [IX_psc_audit_log_performed_by] ON [psc_audit_log]([performed_by]);
```

---

## 6. Sync Tables

### 6.1 psc_sync_log
**Purpose:** Track sync operations between vessel and server

```sql
CREATE TABLE [dbo].[psc_sync_log] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [vessel_id] [uniqueidentifier] NOT NULL,
    [sync_id] [uniqueidentifier] NOT NULL UNIQUE, -- Idempotency key
    [sync_type] [varchar](20) NOT NULL,           -- PUSH, PULL
    [sync_status] [varchar](20) NOT NULL,         -- PENDING, IN_PROGRESS, COMPLETED, FAILED
    [records_sent] [int] NULL,
    [records_received] [int] NULL,
    [payload_checksum] [varchar](64) NULL,        -- SHA-256
    [started_at] [datetime] NOT NULL,
    [completed_at] [datetime] NULL,
    [error_message] [nvarchar](max) NULL,
    [retry_count] [int] NOT NULL DEFAULT 0,
    [created_by] [varchar](100) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    
    CONSTRAINT [PK_psc_sync_log] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [CK_psc_sync_log_type] CHECK ([sync_type] IN ('PUSH', 'PULL')),
    CONSTRAINT [CK_psc_sync_log_status] CHECK ([sync_status] IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED'))
);

CREATE INDEX [IX_psc_sync_log_vessel_id] ON [psc_sync_log]([vessel_id]);
CREATE INDEX [IX_psc_sync_log_sync_id] ON [psc_sync_log]([sync_id]);
CREATE INDEX [IX_psc_sync_log_created_date] ON [psc_sync_log]([created_date] DESC);
```

### 6.2 psc_sync_log_detail
**Purpose:** Individual record sync status

```sql
CREATE TABLE [dbo].[psc_sync_log_detail] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [sync_log_id] [uniqueidentifier] NOT NULL,
    [entity_type] [varchar](30) NOT NULL,
    [entity_id] [uniqueidentifier] NOT NULL,
    [client_id] [uniqueidentifier] NULL,          -- Vessel-generated ID
    [operation] [varchar](20) NOT NULL,           -- CREATE, UPDATE, DELETE
    [sync_status] [varchar](20) NOT NULL,         -- SUCCESS, FAILED, CONFLICT
    [error_message] [nvarchar](max) NULL,
    [server_version] [int] NULL,
    [client_version] [int] NULL,
    
    CONSTRAINT [PK_psc_sync_log_detail] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_psc_sync_log_detail_log] FOREIGN KEY ([sync_log_id]) 
        REFERENCES [psc_sync_log]([id])
);

CREATE INDEX [IX_psc_sync_log_detail_sync_log_id] ON [psc_sync_log_detail]([sync_log_id]);
CREATE INDEX [IX_psc_sync_log_detail_entity] ON [psc_sync_log_detail]([entity_type], [entity_id]);
```

### 6.3 psc_sync_conflict
**Purpose:** Unresolved sync conflicts

```sql
CREATE TABLE [dbo].[psc_sync_conflict] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [vessel_id] [uniqueidentifier] NOT NULL,
    [entity_type] [varchar](30) NOT NULL,
    [entity_id] [uniqueidentifier] NOT NULL,
    [server_data] [nvarchar](max) NOT NULL,       -- JSON snapshot
    [vessel_data] [nvarchar](max) NOT NULL,       -- JSON snapshot
    [conflicting_fields] [nvarchar](max) NOT NULL, -- JSON array of field names
    [status] [varchar](20) NOT NULL DEFAULT 'PENDING',  -- PENDING, RESOLVED
    [resolution] [varchar](30) NULL,              -- KEEP_SERVER, KEEP_VESSEL, REOPEN_FOR_MERGE
    [resolved_by] [varchar](100) NULL,
    [resolved_at] [datetime] NULL,
    [resolution_notes] [nvarchar](max) NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    
    CONSTRAINT [PK_psc_sync_conflict] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [CK_psc_sync_conflict_status] CHECK ([status] IN ('PENDING', 'RESOLVED')),
    CONSTRAINT [CK_psc_sync_conflict_resolution] CHECK ([resolution] IS NULL OR [resolution] IN ('KEEP_SERVER', 'KEEP_VESSEL', 'REOPEN_FOR_MERGE'))
);

CREATE INDEX [IX_psc_sync_conflict_vessel_id] ON [psc_sync_conflict]([vessel_id]);
CREATE INDEX [IX_psc_sync_conflict_status] ON [psc_sync_conflict]([status]);
CREATE INDEX [IX_psc_sync_conflict_entity] ON [psc_sync_conflict]([entity_type], [entity_id]);
```

### 6.4 psc_sync_token
**Purpose:** Track last sync point per vessel

```sql
CREATE TABLE [dbo].[psc_sync_token] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [vessel_id] [uniqueidentifier] NOT NULL UNIQUE,
    [last_sync_at] [datetime] NOT NULL,
    [last_sync_id] [uniqueidentifier] NULL,
    [last_server_version] [bigint] NOT NULL DEFAULT 0,
    [updated_at] [datetime] NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT [PK_psc_sync_token] PRIMARY KEY CLUSTERED ([id] ASC)
);

CREATE INDEX [IX_psc_sync_token_vessel_id] ON [psc_sync_token]([vessel_id]);
```

---

## 7. Notification Table

### 7.1 psc_notification
**Purpose:** In-app notifications

```sql
CREATE TABLE [dbo].[psc_notification] (
    [id] [uniqueidentifier] NOT NULL DEFAULT NEWID(),
    [recipient_type] [varchar](20) NOT NULL,      -- CREW, OFFICE
    [recipient_id] [varchar](100) NOT NULL,       -- CrewID or employee_id
    [vessel_id] [uniqueidentifier] NULL,          -- For vessel-specific notifications
    [notification_type] [varchar](50) NOT NULL,   -- See types below
    [title] [nvarchar](200) NOT NULL,
    [message] [nvarchar](500) NOT NULL,
    [entity_type] [varchar](30) NULL,
    [entity_id] [uniqueidentifier] NULL,
    [is_read] [bit] NOT NULL DEFAULT 0,
    [read_at] [datetime] NULL,
    [created_date] [datetime] NULL DEFAULT GETDATE(),
    
    CONSTRAINT [PK_psc_notification] PRIMARY KEY CLUSTERED ([id] ASC)
);

CREATE INDEX [IX_psc_notification_recipient] ON [psc_notification]([recipient_type], [recipient_id]);
CREATE INDEX [IX_psc_notification_vessel_id] ON [psc_notification]([vessel_id]);
CREATE INDEX [IX_psc_notification_is_read] ON [psc_notification]([is_read]);
CREATE INDEX [IX_psc_notification_created_date] ON [psc_notification]([created_date] DESC);

-- Notification Types:
-- CAR_CREATED, CAR_SUBMITTED, CAR_PIC_ACCEPTED, CAR_REWORK_REQUESTED, CAR_DPA_CLOSED
-- INSPECTION_DPA_CLOSED
-- ACTION_OVERDUE_WARNING (T-3 days), ACTION_OVERDUE
-- PSC_FOLLOW_UP_RECORDED
-- CONFLICT_DETECTED, CONFLICT_RESOLVED
-- PHYSICAL_VERIFICATION_CREATED
```

---

## 8. Triggers

### 8.1 Auto-Create CAR on Deficiency Insert

```sql
CREATE TRIGGER [trg_psc_deficiency_auto_create_car]
ON [dbo].[psc_deficiency]
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    INSERT INTO [psc_car] (
        [id],
        [deficiency_id],
        [car_number],
        [status],
        [target_date],
        [created_by],
        [created_date]
    )
    SELECT 
        NEWID(),
        i.[id],
        -- Generate CAR number: {TYPE}-{YEAR}-{SEQ}
        (
            SELECT TOP 1 
                insp.inspection_type + '-' + 
                CAST(YEAR(insp.inspection_date) AS VARCHAR) + '-' +
                RIGHT('000' + CAST(
                    ISNULL((
                        SELECT COUNT(*) + 1 
                        FROM psc_car c2 
                        INNER JOIN psc_deficiency d2 ON c2.deficiency_id = d2.id
                        INNER JOIN psc_inspection i2 ON d2.inspection_id = i2.id
                        WHERE i2.inspection_type = insp.inspection_type
                        AND YEAR(i2.inspection_date) = YEAR(insp.inspection_date)
                    ), 1) AS VARCHAR), 3)
            FROM psc_inspection insp 
            WHERE insp.id = i.inspection_id
        ),
        'DRAFT',
        ISNULL(i.target_date, DATEADD(day, 7, GETDATE())),
        i.created_by,
        GETDATE()
    FROM inserted i;
END;
GO
```

### 8.2 Auto-Clear Deficiency on Action Code 10

```sql
CREATE TRIGGER [trg_psc_deficiency_auto_clear]
ON [dbo].[psc_deficiency]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- If action_code changed to a clearing code (e.g., '10')
    UPDATE d
    SET 
        d.is_cleared = 1,
        d.cleared_date = GETDATE()
    FROM psc_deficiency d
    INNER JOIN inserted i ON d.id = i.id
    INNER JOIN deleted del ON d.id = del.id
    INNER JOIN master_psc_action_code ac ON i.action_code_id = ac.id
    WHERE ac.is_clearing_code = 1
    AND (del.action_code_id IS NULL OR del.action_code_id <> i.action_code_id);
END;
GO
```

---

## 9. Stored Procedures

### 9.1 usp_psc_get_inspections

```sql
CREATE PROCEDURE [dbo].[usp_psc_get_inspections]
    @vessel_id uniqueidentifier = NULL,
    @status varchar(20) = NULL,
    @inspection_type varchar(20) = NULL,
    @date_from date = NULL,
    @date_to date = NULL,
    @page int = 1,
    @page_size int = 20
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @offset int = (@page - 1) * @page_size;
    
    SELECT 
        i.id,
        i.vessel_id,
        v.vesselName as vessel_name,
        v.vesselCode as vessel_code,
        i.inspection_type,
        i.psc_subtype,
        i.inspection_date,
        i.port_place,
        i.country,
        i.mou_id,
        m.name as mou_name,
        i.authority,
        i.inspector_name,
        i.report_reference,
        i.is_detention,
        i.status,
        i.parent_inspection_id,
        i.revision_no,
        i.created_date,
        -- Counts
        (SELECT COUNT(*) FROM psc_deficiency d WHERE d.inspection_id = i.id AND d.is_deleted = 0) as deficiency_count,
        (SELECT COUNT(*) FROM psc_deficiency d WHERE d.inspection_id = i.id AND d.is_deleted = 0 AND d.is_cleared = 0) as open_deficiency_count,
        -- Report attached?
        CASE WHEN EXISTS (SELECT 1 FROM psc_inspection_report r WHERE r.inspection_id = i.id AND r.is_deleted = 0) THEN 1 ELSE 0 END as has_report
    FROM psc_inspection i
    INNER JOIN VesselData v ON i.vessel_id = v.id
    LEFT JOIN master_mou m ON i.mou_id = m.id
    WHERE i.is_deleted = 0
    AND (@vessel_id IS NULL OR i.vessel_id = @vessel_id)
    AND (@status IS NULL OR i.status = @status)
    AND (@inspection_type IS NULL OR i.inspection_type = @inspection_type)
    AND (@date_from IS NULL OR i.inspection_date >= @date_from)
    AND (@date_to IS NULL OR i.inspection_date <= @date_to)
    ORDER BY i.inspection_date DESC, i.created_date DESC
    OFFSET @offset ROWS FETCH NEXT @page_size ROWS ONLY;
    
    -- Return total count for pagination
    SELECT COUNT(*) as total_count
    FROM psc_inspection i
    WHERE i.is_deleted = 0
    AND (@vessel_id IS NULL OR i.vessel_id = @vessel_id)
    AND (@status IS NULL OR i.status = @status)
    AND (@inspection_type IS NULL OR i.inspection_type = @inspection_type)
    AND (@date_from IS NULL OR i.inspection_date >= @date_from)
    AND (@date_to IS NULL OR i.inspection_date <= @date_to);
END;
GO
```

### 9.2 usp_psc_get_cars

```sql
CREATE PROCEDURE [dbo].[usp_psc_get_cars]
    @vessel_id uniqueidentifier = NULL,
    @status varchar(30) = NULL,
    @car_number varchar(20) = NULL,
    @page int = 1,
    @page_size int = 20
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @offset int = (@page - 1) * @page_size;
    
    SELECT 
        c.id,
        c.car_number,
        c.deficiency_id,
        c.status,
        c.root_cause_summary,
        c.target_date,
        c.rework_count,
        c.revision_no,
        c.created_date,
        -- Deficiency info
        d.def_code,
        d.description as deficiency_description,
        d.is_cleared as deficiency_is_cleared,
        -- Inspection info
        i.id as inspection_id,
        i.inspection_type,
        i.inspection_date,
        i.vessel_id,
        v.vesselName as vessel_name,
        v.vesselCode as vessel_code,
        -- Counts
        (SELECT COUNT(*) FROM psc_corrective_action a WHERE a.car_id = c.id AND a.is_deleted = 0) as action_count,
        (SELECT COUNT(*) FROM psc_corrective_action a WHERE a.car_id = c.id AND a.is_deleted = 0 AND a.is_completed = 1) as completed_action_count,
        (SELECT COUNT(*) FROM psc_evidence e WHERE e.car_id = c.id AND e.is_deleted = 0 AND e.evidence_type = 'BEFORE') as before_evidence_count,
        (SELECT COUNT(*) FROM psc_evidence e WHERE e.car_id = c.id AND e.is_deleted = 0 AND e.evidence_type = 'AFTER') as after_evidence_count
    FROM psc_car c
    INNER JOIN psc_deficiency d ON c.deficiency_id = d.id
    INNER JOIN psc_inspection i ON d.inspection_id = i.id
    INNER JOIN VesselData v ON i.vessel_id = v.id
    WHERE c.is_deleted = 0
    AND d.is_deleted = 0
    AND i.is_deleted = 0
    AND (@vessel_id IS NULL OR i.vessel_id = @vessel_id)
    AND (@status IS NULL OR c.status = @status)
    AND (@car_number IS NULL OR c.car_number LIKE '%' + @car_number + '%')
    ORDER BY c.created_date DESC
    OFFSET @offset ROWS FETCH NEXT @page_size ROWS ONLY;
    
    -- Return total count
    SELECT COUNT(*) as total_count
    FROM psc_car c
    INNER JOIN psc_deficiency d ON c.deficiency_id = d.id
    INNER JOIN psc_inspection i ON d.inspection_id = i.id
    WHERE c.is_deleted = 0
    AND d.is_deleted = 0
    AND i.is_deleted = 0
    AND (@vessel_id IS NULL OR i.vessel_id = @vessel_id)
    AND (@status IS NULL OR c.status = @status)
    AND (@car_number IS NULL OR c.car_number LIKE '%' + @car_number + '%');
END;
GO
```

### 9.3 usp_psc_generate_car_number

```sql
CREATE PROCEDURE [dbo].[usp_psc_generate_car_number]
    @inspection_type varchar(20),
    @year int,
    @car_number varchar(20) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @seq int;
    
    SELECT @seq = ISNULL(MAX(
        CAST(RIGHT(c.car_number, 3) AS INT)
    ), 0) + 1
    FROM psc_car c
    WHERE c.car_number LIKE @inspection_type + '-' + CAST(@year AS VARCHAR) + '-%';
    
    SET @car_number = @inspection_type + '-' + CAST(@year AS VARCHAR) + '-' + RIGHT('000' + CAST(@seq AS VARCHAR), 3);
END;
GO
```

---

## 10. API Contracts

### 10.1 Base URL & Authentication

```
Base URL: /api/psc/
Authentication: Bearer JWT token
Content-Type: application/json
```

### 10.2 Standard Response Format

**Success Response:**
```json
{
  "data": { ... },
  "message": "Success"
}
```

**List Response:**
```json
{
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 150,
    "total_pages": 8
  }
}
```

**Error Response:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Human readable message",
  "details": {
    "field_name": "Error for this field"
  }
}
```

### 10.3 Inspection Endpoints

#### GET /api/psc/inspections/
**Purpose:** List inspections with filters
**Roles:** All authenticated
**Query Params:**
- `vessel_id` (uuid, optional) — Filter by vessel
- `status` (string, optional) — DRAFT, SUBMITTED, PIC_REVIEWED, DPA_CLOSED
- `inspection_type` (string, optional) — PSC, RS, AUDIT, INTERNAL
- `date_from` (date, optional)
- `date_to` (date, optional)
- `page` (int, default 1)
- `page_size` (int, default 20, max 100)

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "vessel_id": "uuid",
      "vessel_name": "MV Example",
      "vessel_code": "EXM",
      "inspection_type": "PSC",
      "psc_subtype": "INITIAL",
      "inspection_date": "2026-01-15",
      "port_place": "Singapore",
      "country": "Singapore",
      "mou_id": "uuid",
      "mou_name": "Tokyo MOU",
      "authority": "MPA Singapore",
      "inspector_name": "John Inspector",
      "report_reference": "PSC-2026-001",
      "is_detention": false,
      "status": "SUBMITTED",
      "deficiency_count": 3,
      "open_deficiency_count": 2,
      "has_report": true,
      "created_date": "2026-01-15T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 45,
    "total_pages": 3
  }
}
```

#### POST /api/psc/inspections/
**Purpose:** Create new inspection
**Roles:** VESSEL_MASTER, OFFICE_*

**Request:**
```json
{
  "vessel_id": "uuid",
  "inspection_type": "PSC",
  "psc_subtype": "INITIAL",
  "inspection_date": "2026-01-15",
  "port_place": "Singapore",
  "country": "Singapore",
  "mou_id": "uuid",
  "authority": "MPA Singapore",
  "inspector_name": "John Inspector",
  "report_reference": "PSC-2026-001",
  "is_detention": false,
  "client_id": "uuid"
}
```

**Response:** 201 Created
```json
{
  "data": {
    "id": "uuid",
    "status": "DRAFT",
    ...
  },
  "message": "Inspection created successfully"
}
```

#### GET /api/psc/inspections/{id}/
**Purpose:** Get inspection detail
**Roles:** All authenticated

**Response:**
```json
{
  "data": {
    "id": "uuid",
    "vessel_id": "uuid",
    "vessel_name": "MV Example",
    ...
    "deficiencies": [
      {
        "id": "uuid",
        "def_code": "10101",
        "def_code_description": "Certificates - International Tonnage",
        "description": "Certificate expired",
        "action_code": "30",
        "action_code_description": "Deficiency to be rectified",
        "target_date": "2026-01-22",
        "is_cleared": false,
        "car": {
          "id": "uuid",
          "car_number": "PSC-2026-001",
          "status": "DRAFT"
        }
      }
    ],
    "reports": [
      {
        "id": "uuid",
        "file_name": "inspection_report.pdf",
        "file_path": "/psc/...",
        "uploaded_at": "2026-01-15T14:30:00Z"
      }
    ],
    "activity_history": [ ... ]
  }
}
```

#### PUT /api/psc/inspections/{id}/
**Purpose:** Update inspection
**Roles:** VESSEL_MASTER (DRAFT only), OFFICE_* (any status)

#### POST /api/psc/inspections/{id}/submit/
**Purpose:** Submit inspection for review
**Roles:** VESSEL_MASTER, OFFICE_*
**Preconditions:** Has report attached, status = DRAFT

**Response:** 200 OK
```json
{
  "data": { "id": "uuid", "status": "SUBMITTED" },
  "message": "Inspection submitted successfully"
}
```

#### POST /api/psc/inspections/{id}/pic-review/
**Purpose:** PIC reviews inspection
**Roles:** OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT
**Preconditions:** status = SUBMITTED

**Request:**
```json
{
  "comment": "Reviewed and acknowledged. (mandatory, min 10 chars)"
}
```

#### POST /api/psc/inspections/{id}/dpa-close/
**Purpose:** DPA closes inspection
**Roles:** DPA
**Preconditions:** status = PIC_REVIEWED

**Request:**
```json
{
  "comment": "Closed by DPA. (mandatory, min 10 chars)"
}
```

#### DELETE /api/psc/inspections/{id}/
**Purpose:** Soft delete draft inspection
**Roles:** VESSEL_MASTER
**Preconditions:** status = DRAFT

---

### 10.4 Deficiency Endpoints

#### POST /api/psc/inspections/{inspection_id}/deficiencies/
**Purpose:** Add deficiency to inspection (auto-creates CAR)
**Roles:** VESSEL_MASTER, OFFICE_*

**Request:**
```json
{
  "def_code_id": "uuid",
  "description": "Certificate found expired during inspection",
  "action_code_id": "uuid",
  "target_date": "2026-01-22",
  "client_id": "uuid"
}
```

**Response:** 201 Created
```json
{
  "data": {
    "id": "uuid",
    "def_code": "10101",
    ...
    "car": {
      "id": "uuid",
      "car_number": "PSC-2026-001",
      "status": "DRAFT"
    }
  },
  "message": "Deficiency added and CAR created"
}
```

#### PUT /api/psc/deficiencies/{id}/action-code/
**Purpose:** Update deficiency action code
**Roles:** VESSEL_MASTER

**Request:**
```json
{
  "action_code_id": "uuid",
  "follow_up_inspection_id": "uuid",
  "change_reason": "Rectified during follow-up inspection"
}
```

---

### 10.5 CAR Endpoints

#### GET /api/psc/cars/
**Purpose:** List CARs with filters
**Query Params:** vessel_id, status, car_number, page, page_size

#### GET /api/psc/cars/{id}/
**Purpose:** Get CAR detail with all related data

**Response:**
```json
{
  "data": {
    "id": "uuid",
    "car_number": "PSC-2026-001",
    "status": "DRAFT",
    "deficiency": {
      "id": "uuid",
      "def_code": "10101",
      "description": "..."
    },
    "inspection": {
      "id": "uuid",
      "inspection_type": "PSC",
      "vessel_name": "MV Example"
    },
    "root_cause_summary": "...",
    "clc_items": [
      { "id": "uuid", "code": "CLC001", "description": "..." }
    ],
    "corrective_actions": [
      {
        "id": "uuid",
        "action_type": "IMMEDIATE",
        "description": "...",
        "owner_name": "John Doe",
        "due_date": "2026-01-20",
        "is_completed": false
      }
    ],
    "evidence": [
      {
        "id": "uuid",
        "evidence_type": "BEFORE",
        "file_name": "before_photo.jpg",
        "file_path": "/psc/...",
        "description": "Photo before correction"
      }
    ],
    "physical_verification": null,
    "activity_history": [ ... ]
  }
}
```

#### PUT /api/psc/cars/{id}/
**Purpose:** Update CAR (root cause, etc.)
**Roles:** VESSEL_MASTER (DRAFT/REWORK), OFFICE_* (any)

**Request:**
```json
{
  "root_cause_summary": "Lack of proper document management... (min 50 chars)",
  "target_date": "2026-01-22",
  "clc_item_ids": ["uuid1", "uuid2"],
  "custom_cause_text": "Optional additional cause"
}
```

#### POST /api/psc/cars/{id}/submit/
**Purpose:** Submit CAR for PIC review
**Roles:** VESSEL_MASTER, OFFICE_*
**Preconditions:**
- root_cause_summary >= 50 chars
- At least 1 IMMEDIATE action
- At least 1 LONG_TERM action
- At least 1 BEFORE evidence
- At least 1 AFTER evidence

#### POST /api/psc/cars/{id}/pic-accept/
**Purpose:** PIC accepts CAR
**Roles:** OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT
**Preconditions:** status = SUBMITTED

**Request:**
```json
{
  "comment": "Accepted. Root cause analysis adequate. (mandatory)"
}
```

#### POST /api/psc/cars/{id}/rework/
**Purpose:** Request rework on CAR
**Roles:** OFFICE_PIC, OFFICE_SSQE, OFFICE_SUPT, DPA
**Preconditions:** status = SUBMITTED or PIC_ACCEPTED

**Request:**
```json
{
  "reason": "Root cause analysis insufficient. Please elaborate on... (min 20 chars)"
}
```

#### POST /api/psc/cars/{id}/dpa-close/
**Purpose:** DPA closes CAR
**Roles:** DPA
**Preconditions:** status = PIC_ACCEPTED

**Request:**
```json
{
  "comment": "Closed. Corrective actions verified. (mandatory)"
}
```

---

### 10.6 Corrective Action Endpoints

#### POST /api/psc/cars/{car_id}/actions/
**Purpose:** Add corrective action to CAR

**Request:**
```json
{
  "action_type": "IMMEDIATE",
  "description": "Replace expired certificate immediately",
  "owner_crew_id": "uuid",
  "due_date": "2026-01-20",
  "client_id": "uuid"
}
```

#### PUT /api/psc/actions/{id}/
**Purpose:** Update corrective action

#### POST /api/psc/actions/{id}/complete/
**Purpose:** Mark action as completed
**Roles:** Owner (VESSEL_CREW) or VESSEL_MASTER

**Request:**
```json
{
  "completion_remarks": "Certificate renewed and verified"
}
```

---

### 10.7 Evidence Endpoints

#### POST /api/psc/cars/{car_id}/evidence/
**Purpose:** Upload evidence file
**Content-Type:** multipart/form-data

**Request:**
```
file: (binary, max 3MB, PDF/JPG/JPEG only)
evidence_type: BEFORE | AFTER | EVIDENCE | OTHER
description: "Photo showing deficiency before correction" (mandatory)
client_id: uuid (optional, for offline)
```

**Response:** 201 Created
```json
{
  "data": {
    "id": "uuid",
    "evidence_type": "BEFORE",
    "file_name": "before_20260115_143052_a7f2.jpg",
    "file_path": "/psc/{vessel_id}/cars/{car_id}/before_20260115_143052_a7f2.jpg",
    "file_size": 1524000,
    "mime_type": "image/jpeg",
    "description": "Photo showing deficiency before correction"
  }
}
```

#### DELETE /api/psc/evidence/{id}/
**Purpose:** Soft delete evidence
**Roles:** VESSEL_MASTER, OFFICE_*

---

### 10.8 Physical Verification Endpoints

#### POST /api/psc/cars/{car_id}/physical-verification/
**Purpose:** Create physical verification
**Roles:** OFFICE_*, DPA
**Preconditions:** CAR status = DPA_CLOSED

**Request:**
```json
{
  "scheduled_date": "2026-02-15",
  "visit_port": "Singapore",
  "verifier_user_id": "EMP001"
}
```

#### PUT /api/psc/physical-verifications/{id}/
**Purpose:** Update physical verification details

#### POST /api/psc/physical-verifications/{id}/close/
**Purpose:** Close physical verification
**Roles:** Assigned verifier, DPA

**Request:**
```json
{
  "visit_date": "2026-02-15",
  "comments": "Verified on board. All corrections confirmed. (mandatory)"
}
```

---

### 10.9 Sync Endpoints

#### POST /api/psc/sync/pull/
**Purpose:** Pull changes from server to vessel
**Roles:** VESSEL_MASTER, VESSEL_CREW

**Request:**
```json
{
  "vessel_id": "uuid",
  "last_sync_token": "uuid",
  "last_server_version": 12345
}
```

**Response:**
```json
{
  "data": {
    "inspections": [ ... ],
    "deficiencies": [ ... ],
    "cars": [ ... ],
    "corrective_actions": [ ... ],
    "evidence_metadata": [ ... ],
    "activity_history": [ ... ],
    "masters": {
      "def_codes": [ ... ],
      "action_codes": [ ... ],
      "mou": [ ... ],
      "clc_items": [ ... ]
    }
  },
  "sync_token": "uuid",
  "server_version": 12350
}
```

#### POST /api/psc/sync/push/
**Purpose:** Push changes from vessel to server
**Roles:** VESSEL_MASTER, VESSEL_CREW

**Request:**
```json
{
  "sync_id": "uuid",
  "vessel_id": "uuid",
  "checksum": "sha256-hash",
  "events": [
    {
      "event_id": "uuid",
      "entity_type": "INSPECTION",
      "entity_id": "uuid",
      "client_id": "uuid",
      "operation": "CREATE",
      "client_version": 1,
      "data": { ... },
      "timestamp": "2026-01-15T14:30:00Z"
    }
  ],
  "attachments": [
    {
      "client_id": "uuid",
      "car_id": "uuid",
      "evidence_type": "BEFORE",
      "file_name": "photo.jpg",
      "file_size": 1524000
    }
  ]
}
```

**Response:**
```json
{
  "data": {
    "sync_id": "uuid",
    "processed": 5,
    "failed": 0,
    "conflicts": [],
    "id_mappings": {
      "client_id_1": "server_id_1",
      "client_id_2": "server_id_2"
    },
    "attachment_upload_urls": [
      {
        "client_id": "uuid",
        "upload_url": "/api/psc/sync/upload/{token}",
        "expires_at": "2026-01-15T15:00:00Z"
      }
    ]
  }
}
```

#### POST /api/psc/sync/resolve-conflict/
**Purpose:** Resolve sync conflict
**Roles:** OFFICE_*

**Request:**
```json
{
  "conflict_id": "uuid",
  "resolution": "KEEP_SERVER",
  "notes": "Office version is correct, vessel was working with stale data"
}
```

---

### 10.10 Master Data Endpoints

#### GET /api/psc/masters/psc-def-codes/
**Query:** ?search=certificate&category=Certificates

#### GET /api/psc/masters/psc-action-codes/

#### GET /api/psc/masters/mou/

#### GET /api/psc/masters/clc/
**Query:** ?search=training&category=Human+Factors

#### GET /api/psc/masters/pic/

---

### 10.11 Notification Endpoints

#### GET /api/psc/notifications/
**Query:** ?is_read=false&page=1&page_size=20

#### POST /api/psc/notifications/mark-read/
**Request:**
```json
{
  "notification_ids": ["uuid1", "uuid2"]
}
```

#### POST /api/psc/notifications/mark-all-read/

---

## 11. Role-Based Access Control (RBAC)

### 11.1 Permission Matrix

| Action | VESSEL_MASTER | VESSEL_CREW | OFFICE_PIC | OFFICE_SSQE | OFFICE_SUPT | DPA |
|--------|---------------|-------------|------------|-------------|-------------|-----|
| Create Inspection | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Edit Inspection (DRAFT) | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Edit Inspection (Post-Submit) | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Submit Inspection | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| PIC Review Inspection | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| DPA Close Inspection | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Delete Inspection (DRAFT) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Add Deficiency | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Edit CAR (DRAFT/REWORK) | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Submit CAR | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| PIC Accept CAR | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| Request Rework | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| DPA Close CAR | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Upload Evidence | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Complete Action | ✅ (any) | ✅ (own) | ✅ | ✅ | ✅ | ✅ |
| Create Physical Verification | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Close Physical Verification | ❌ | ❌ | ✅* | ✅* | ✅* | ✅ |
| Resolve Sync Conflict | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| View Audit Log | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |

*Only if assigned as verifier

### 11.2 Data Visibility

| Role | Vessels Visible |
|------|-----------------|
| VESSEL_MASTER | Own vessel only |
| VESSEL_CREW | Own vessel only |
| OFFICE_* | Vessels assigned via `master_RoleByVessel` |
| DPA | All vessels |

---

## 12. Django Project Structure

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── core/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── __init__.py
│   ├── authentication/
│   │   ├── __init__.py
│   │   ├── models.py          # Unmanaged models for existing tables
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── permissions.py
│   ├── psc/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── inspection.py
│   │   │   ├── deficiency.py
│   │   │   ├── car.py
│   │   │   ├── evidence.py
│   │   │   ├── sync.py
│   │   │   └── notification.py
│   │   ├── serializers/
│   │   │   ├── __init__.py
│   │   │   ├── inspection.py
│   │   │   ├── deficiency.py
│   │   │   ├── car.py
│   │   │   └── sync.py
│   │   ├── views/
│   │   │   ├── __init__.py
│   │   │   ├── inspection.py
│   │   │   ├── deficiency.py
│   │   │   ├── car.py
│   │   │   ├── evidence.py
│   │   │   ├── sync.py
│   │   │   └── notification.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── car_service.py
│   │   │   ├── sync_service.py
│   │   │   └── notification_service.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── pdf_generator.py
│   │   │   ├── excel_generator.py
│   │   │   └── file_utils.py
│   │   ├── urls.py
│   │   └── admin.py
│   └── masters/
│       ├── __init__.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
└── tests/
    ├── __init__.py
    ├── test_inspection.py
    ├── test_car.py
    └── test_sync.py
```

---

## Document References

| Document | Reference |
|----------|-----------|
| PRD.md | Feature IDs (FEAT-*) |
| TECH_STACK.md | Package versions |
| FRONTEND_GUIDELINES.md | API consumption patterns |
| VALIDATION_RULES.md | Field validation rules |
| IMPLEMENTATION_PLAN.md | Build sequence |

---

**Document Control:**
- Created: 2026-02-04
- Author: System Generated
- Database Version: 1.0
