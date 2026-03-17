-- =====================================================
-- VIMS Inspection - Seed Data Script
-- Creates missing unmanaged tables and inserts test data
-- Target DB: ksm_cms_dev (SQL Server)
-- =====================================================

-- Use transaction for safety
BEGIN TRANSACTION;

-- =====================================================
-- 1. USER & ROLE TABLES (unmanaged, referenced by Django models)
-- =====================================================

-- 1a. HRM501 — Vessel crew users
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'HRM501')
BEGIN
    CREATE TABLE HRM501 (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        CrewID VARCHAR(7) NOT NULL,
        first_name VARCHAR(255) NULL,
        surname VARCHAR(255) NULL,
        rank_name VARCHAR(255) NULL,
        department_name VARCHAR(255) NULL,
        user_id VARCHAR(255) NULL,
        password VARCHAR(255) NULL,
        vessel_id UNIQUEIDENTIFIER NULL,
        is_active BIT DEFAULT 1,
        is_deleted BIT DEFAULT 0
    );
    PRINT 'Created table: HRM501';
END
ELSE
    PRINT 'Table HRM501 already exists — skipping CREATE';

-- 1b. users — Office users
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'users')
BEGIN
    CREATE TABLE users (
        employee_id VARCHAR(20) PRIMARY KEY,
        employee_name VARCHAR(100) NULL,
        display_name VARCHAR(100) NULL,
        email_id VARCHAR(100) NULL,
        username VARCHAR(100) NULL,
        password VARCHAR(255) NULL,
        employee_role VARCHAR(45) NULL,
        department VARCHAR(255) NULL,
        is_active BIT DEFAULT 1,
        is_deleted BIT DEFAULT 0
    );
    PRINT 'Created table: users';
END
ELSE
    PRINT 'Table users already exists — skipping CREATE';

-- 1c. master_RoleByVessel — Office user vessel assignments
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'master_RoleByVessel')
BEGIN
    CREATE TABLE master_RoleByVessel (
        Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        VesselId UNIQUEIDENTIFIER NOT NULL,
        RoleId UNIQUEIDENTIFIER NULL,
        UserId VARCHAR(100) NOT NULL,
        IsActive BIT DEFAULT 1,
        is_deleted BIT DEFAULT 0
    );
    PRINT 'Created table: master_RoleByVessel';
END
ELSE
    PRINT 'Table master_RoleByVessel already exists — skipping CREATE';

-- 1d. master_applied_rank — Rank master
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'master_applied_rank')
BEGIN
    CREATE TABLE master_applied_rank (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        rank_name VARCHAR(255) NULL,
        rank_id VARCHAR(255) NULL,
        department UNIQUEIDENTIFIER NULL,
        is_active BIT DEFAULT 1,
        is_deleted BIT DEFAULT 0
    );
    PRINT 'Created table: master_applied_rank';
END
ELSE
    PRINT 'Table master_applied_rank already exists — skipping CREATE';

-- 1e. master_psc_role — PSC module roles
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'master_psc_role')
BEGIN
    CREATE TABLE master_psc_role (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        role_code VARCHAR(50) UNIQUE NOT NULL,
        role_name VARCHAR(100) NOT NULL,
        role_type VARCHAR(20) NOT NULL,
        is_active BIT DEFAULT 1,
        is_deleted BIT DEFAULT 0,
        created_by VARCHAR(100) NULL,
        created_date DATETIME DEFAULT GETDATE(),
        updated_by VARCHAR(100) NULL,
        updated_date DATETIME NULL
    );
    PRINT 'Created table: master_psc_role';
END
ELSE
    PRINT 'Table master_psc_role already exists — skipping CREATE';

-- 1f. master_role — Office role master
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'master_role')
BEGIN
    CREATE TABLE master_role (
        id UNIQUEIDENTIFIER PRIMARY KEY,
        role_name VARCHAR(100) NULL,
        is_active BIT NULL DEFAULT 1,
        is_deleted BIT NULL DEFAULT 0,
        created_by VARCHAR(100) NULL,
        created_date DATETIME NULL,
        updated_by VARCHAR(100) NULL,
        updated_date DATETIME NULL
    );
    PRINT 'Created table: master_role';
END
ELSE
    PRINT 'Table master_role already exists — skipping CREATE';

-- 1g. mapping_role_user — Office user to role mapping
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'mapping_role_user')
BEGIN
    CREATE TABLE mapping_role_user (
        id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
        userid VARCHAR(50) NULL,
        role_id UNIQUEIDENTIFIER NULL,
        is_active BIT NULL DEFAULT 1,
        is_deleted BIT NULL DEFAULT 0,
        created_by VARCHAR(100) NULL,
        created_date DATETIME NULL,
        updated_by VARCHAR(100) NULL,
        updated_date DATETIME NULL
    );
    PRINT 'Created table: mapping_role_user';
END
ELSE
    PRINT 'Table mapping_role_user already exists — skipping CREATE';

-- =====================================================
-- 2. MASTER DATA TABLES (from SQL schema files)
-- =====================================================

-- 2a. MOU_Master
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'MOU_Master')
BEGIN
    CREATE TABLE MOU_Master (
        MOU_Code VARCHAR(20) PRIMARY KEY,
        MOU_Name VARCHAR(100) NOT NULL,
        Region VARCHAR(50),
        Is_Active BIT DEFAULT 1,
        Sort_Order INT DEFAULT 0
    );
    PRINT 'Created table: MOU_Master';
END
ELSE
    PRINT 'Table MOU_Master already exists — skipping CREATE';

-- 2b. PSC_Action_Codes
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PSC_Action_Codes')
BEGIN
    CREATE TABLE PSC_Action_Codes (
        Action_Code INT PRIMARY KEY,
        Definition VARCHAR(100) NOT NULL,
        Description VARCHAR(500),
        Is_Detention BIT DEFAULT 0,
        Requires_Follow_Up BIT DEFAULT 0,
        Is_Active BIT DEFAULT 1
    );
    PRINT 'Created table: PSC_Action_Codes';
END
ELSE
    PRINT 'Table PSC_Action_Codes already exists — skipping CREATE';

-- 2c. PIC_Master
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PIC_Master')
BEGIN
    CREATE TABLE PIC_Master (
        PIC_Code VARCHAR(10) PRIMARY KEY,
        PIC_Name VARCHAR(50) NOT NULL,
        Department VARCHAR(20),
        Sort_Order INT DEFAULT 0
    );
    PRINT 'Created table: PIC_Master';
END
ELSE
    PRINT 'Table PIC_Master already exists — skipping CREATE';

-- 2d. CLC_Category
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'CLC_Category')
BEGIN
    CREATE TABLE CLC_Category (
        Category_ID INT PRIMARY KEY,
        Category_Code VARCHAR(50) NOT NULL,
        Category_Name VARCHAR(100) NOT NULL,
        Category_Type VARCHAR(50),
        Parent_ID INT NULL,
        Sort_Order INT DEFAULT 0
    );
    PRINT 'Created table: CLC_Category';
END
ELSE
    PRINT 'Table CLC_Category already exists — skipping CREATE';

-- 2e. CLC_Item
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'CLC_Item')
BEGIN
    CREATE TABLE CLC_Item (
        CLC_Code VARCHAR(10) PRIMARY KEY,
        Category_ID INT NOT NULL,
        Item_Name VARCHAR(200) NOT NULL,
        Item_Description VARCHAR(500),
        Sort_Order INT DEFAULT 0,
        Is_Active BIT DEFAULT 1
    );
    PRINT 'Created table: CLC_Item';
END
ELSE
    PRINT 'Table CLC_Item already exists — skipping CREATE';

-- 2f. PSC_Def_Category
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PSC_Def_Category')
BEGIN
    CREATE TABLE PSC_Def_Category (
        Category_Code VARCHAR(2) PRIMARY KEY,
        Category_Name VARCHAR(100) NOT NULL,
        Sort_Order INT DEFAULT 0,
        Is_Active BIT DEFAULT 1
    );
    PRINT 'Created table: PSC_Def_Category';
END
ELSE
    PRINT 'Table PSC_Def_Category already exists — skipping CREATE';

-- 2g. PSC_Def_Subcategory
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PSC_Def_Subcategory')
BEGIN
    CREATE TABLE PSC_Def_Subcategory (
        Subcategory_Code VARCHAR(3) PRIMARY KEY,
        Category_Code VARCHAR(2) NOT NULL,
        Subcategory_Name VARCHAR(100) NOT NULL,
        Sort_Order INT DEFAULT 0,
        Is_Active BIT DEFAULT 1
    );
    PRINT 'Created table: PSC_Def_Subcategory';
END
ELSE
    PRINT 'Table PSC_Def_Subcategory already exists — skipping CREATE';

-- 2h. PSC_Def_Code
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PSC_Def_Code')
BEGIN
    CREATE TABLE PSC_Def_Code (
        Def_Code VARCHAR(5) PRIMARY KEY,
        Category_Code VARCHAR(2) NOT NULL,
        Subcategory_Code VARCHAR(3),
        Def_Name VARCHAR(200) NOT NULL,
        Sort_Order INT DEFAULT 0,
        Is_Active BIT DEFAULT 1
    );
    PRINT 'Created table: PSC_Def_Code';
END
ELSE
    PRINT 'Table PSC_Def_Code already exists — skipping CREATE';

-- =====================================================
-- 3. SEED DATA — PSC Roles
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM master_psc_role WHERE role_code = 'VESSEL_MASTER')
BEGIN
    INSERT INTO master_psc_role (id, role_code, role_name, role_type, created_by) VALUES
    (NEWID(), 'VESSEL_MASTER', 'Vessel Master', 'VESSEL', 'SEED'),
    (NEWID(), 'VESSEL_CREW', 'Vessel Crew', 'VESSEL', 'SEED'),
    (NEWID(), 'OFFICE_PIC', 'Office PIC', 'OFFICE', 'SEED'),
    (NEWID(), 'OFFICE_SSQE', 'Office SSQE', 'OFFICE', 'SEED'),
    (NEWID(), 'OFFICE_SUPT', 'Office Superintendent', 'OFFICE', 'SEED'),
    (NEWID(), 'DPA', 'Designated Person Ashore', 'OFFICE', 'SEED'),
    (NEWID(), 'PHYSICAL_VERIFIER', 'Physical Verifier', 'OFFICE', 'SEED');
    PRINT 'Inserted 7 PSC roles';
END
ELSE
    PRINT 'PSC roles already exist — skipping';

-- =====================================================
-- 4. SEED DATA — MOU Master
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM MOU_Master WHERE MOU_Code = 'PARIS')
BEGIN
    INSERT INTO MOU_Master (MOU_Code, MOU_Name, Region, Sort_Order) VALUES
    ('PARIS', 'Paris MOU', 'Europe', 1),
    ('TOKYO', 'Tokyo MOU', 'Asia-Pacific', 2),
    ('USCG', 'US Coast Guard', 'North America', 3),
    ('INDIAN', 'Indian Ocean MOU', 'Indian Ocean', 4),
    ('ABUJA', 'Abuja MOU', 'West & Central Africa', 5),
    ('BLACK_SEA', 'Black Sea MOU', 'Black Sea', 6),
    ('CARIBBEAN', 'Caribbean MOU', 'Caribbean', 7),
    ('MED', 'Mediterranean MOU', 'Mediterranean', 8),
    ('RIYADH', 'Riyadh MOU', 'Gulf States', 9),
    ('VINA', 'Vina del Mar Agreement', 'Latin America', 10);
    PRINT 'Inserted 10 MOU records';
END
ELSE
    PRINT 'MOU data already exists — skipping';

-- =====================================================
-- 5. SEED DATA — PSC Action Codes
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM PSC_Action_Codes WHERE Action_Code = 10)
BEGIN
    INSERT INTO PSC_Action_Codes (Action_Code, Definition, Description, Is_Detention, Requires_Follow_Up) VALUES
    (10, 'Deficiency rectified', 'PSCO checked and confirmed rectified', 0, 0),
    (12, 'All deficiencies rectified', 'ALL items on report checked and found rectified', 0, 0),
    (15, 'Rectify at next port', 'Cannot fix here; next port informed (combine with code 40)', 0, 1),
    (16, 'Rectify within 14 days', 'Minor deficiency; not hazardous; remains pending', 0, 1),
    (17, 'Master instructed to rectify before departure', 'PSCO may return to verify', 0, 1),
    (18, 'Rectify NC within 3 months', 'ISM non-conformity; remains pending', 0, 1),
    (19, 'Major NC before departure', 'ISM major NC; serious threat; immediate action required', 0, 1),
    (30, 'Ground for detention', 'Ship detained; follow with code 10 when fixed', 1, 1),
    (35, 'Allowed to sail after detention', 'Detention lifted', 0, 0),
    (36, 'Allowed to sail after follow-up detention', 'Second port lifts detention', 0, 0),
    (40, 'Next port informed', 'Next port to check deficiencies', 0, 1),
    (45, 'Next port to re-detain', 'Detention continues at second port', 1, 1),
    (50, 'Flag State/Consul informed', 'Required for every detention', 0, 0),
    (55, 'Flag State consulted', 'Relevant deficiencies discussed', 0, 0),
    (70, 'Classification Society informed', 'Class-related deficiency', 0, 0),
    (80, 'Temporary repair/exemption', 'Limit date for definitive repair required', 0, 1),
    (85, 'MARPOL discharge investigation', 'Self-explanatory', 0, 0),
    (95, 'Letter of warning issued', 'Self-explanatory', 0, 0),
    (96, 'Letter of warning withdrawn', 'Self-explanatory', 0, 0),
    (99, 'Others', 'When no other code applies', 0, 0);
    PRINT 'Inserted 20 PSC action codes';
END
ELSE
    PRINT 'PSC action codes already exist — skipping';

-- =====================================================
-- 6. SEED DATA — PIC Master
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM PIC_Master WHERE PIC_Code = 'MASTER')
BEGIN
    INSERT INTO PIC_Master (PIC_Code, PIC_Name, Department, Sort_Order) VALUES
    ('MASTER', 'Master', 'Deck', 1),
    ('CO', 'Chief Officer', 'Deck', 2),
    ('CE', 'Chief Engineer', 'Engine', 3),
    ('2O', 'Second Officer', 'Deck', 4),
    ('2E', 'Second Engineer', 'Engine', 5),
    ('3O', 'Third Officer', 'Deck', 6),
    ('3E', 'Third Engineer', 'Engine', 7),
    ('ETO', 'ETO', 'Engine', 8),
    ('BSN', 'Bosun', 'Deck', 9);
    PRINT 'Inserted 9 PIC records';
END
ELSE
    PRINT 'PIC data already exists — skipping';

-- =====================================================
-- 7. SEED DATA — CLC Categories
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM CLC_Category WHERE Category_ID = 1)
BEGIN
    -- Immediate Causes - Actions (1-4)
    INSERT INTO CLC_Category VALUES (1, 'IA', 'Immediate Causes - Actions', NULL, NULL, 1);
    INSERT INTO CLC_Category VALUES (11, '1', 'Following Procedures', 'Immediate_Action', 1, 1);
    INSERT INTO CLC_Category VALUES (12, '2', 'Use of Tools or Equipment', 'Immediate_Action', 1, 2);
    INSERT INTO CLC_Category VALUES (13, '3', 'Use of Protective Methods', 'Immediate_Action', 1, 3);
    INSERT INTO CLC_Category VALUES (14, '4', 'Inattention / Lack of Awareness', 'Immediate_Action', 1, 4);

    -- Immediate Causes - Conditions (5-8)
    INSERT INTO CLC_Category VALUES (2, 'IC', 'Immediate Causes - Conditions', NULL, NULL, 2);
    INSERT INTO CLC_Category VALUES (21, '5', 'Protective Systems', 'Immediate_Condition', 2, 5);
    INSERT INTO CLC_Category VALUES (22, '6', 'Tools, Equipment & Vehicles', 'Immediate_Condition', 2, 6);
    INSERT INTO CLC_Category VALUES (23, '7', 'Work Exposures', 'Immediate_Condition', 2, 7);
    INSERT INTO CLC_Category VALUES (24, '8', 'Work Place Environment / Layout', 'Immediate_Condition', 2, 8);

    -- Root Causes - Personal Factors (P1-P6)
    INSERT INTO CLC_Category VALUES (3, 'RP', 'Root Causes - Personal Factors', NULL, NULL, 3);
    INSERT INTO CLC_Category VALUES (31, 'P1', 'Physical Capability', 'Root_Personal', 3, 1);
    INSERT INTO CLC_Category VALUES (32, 'P2', 'Physical Condition', 'Root_Personal', 3, 2);
    INSERT INTO CLC_Category VALUES (33, 'P3', 'Mental State', 'Root_Personal', 3, 3);
    INSERT INTO CLC_Category VALUES (34, 'P4', 'Mental Stress', 'Root_Personal', 3, 4);
    INSERT INTO CLC_Category VALUES (35, 'P5', 'Behavior', 'Root_Personal', 3, 5);
    INSERT INTO CLC_Category VALUES (36, 'P6', 'Skill Level', 'Root_Personal', 3, 6);

    -- Root Causes - Job Factors (J7-J15)
    INSERT INTO CLC_Category VALUES (4, 'RJ', 'Root Causes - Job Factors', NULL, NULL, 4);
    INSERT INTO CLC_Category VALUES (41, 'J7', 'Training / Knowledge Transfer', 'Root_Job', 4, 7);
    INSERT INTO CLC_Category VALUES (42, 'J8', 'Management / Supervision / Leadership', 'Root_Job', 4, 8);
    INSERT INTO CLC_Category VALUES (43, 'J9', 'Contractor Selection & Oversight', 'Root_Job', 4, 9);
    INSERT INTO CLC_Category VALUES (44, 'J10', 'Engineering / Design', 'Root_Job', 4, 10);
    INSERT INTO CLC_Category VALUES (45, 'J11', 'Work Planning', 'Root_Job', 4, 11);
    INSERT INTO CLC_Category VALUES (46, 'J12', 'Purchasing, Material Handling & Control', 'Root_Job', 4, 12);
    INSERT INTO CLC_Category VALUES (47, 'J13', 'Tools & Equipment', 'Root_Job', 4, 13);
    INSERT INTO CLC_Category VALUES (48, 'J14', 'Work Rules / Policies / Standards / Procedures', 'Root_Job', 4, 14);
    INSERT INTO CLC_Category VALUES (49, 'J15', 'Communication', 'Root_Job', 4, 15);
    PRINT 'Inserted 27 CLC categories';
END
ELSE
    PRINT 'CLC categories already exist — skipping';

-- =====================================================
-- 8. SEED DATA — CLC Items (sample)
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = '1-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    -- Category 11: Following Procedures (1-x)
    ('1-1', 11, 'Violation by individual', 1),
    ('1-2', 11, 'Violation by group', 2),
    ('1-3', 11, 'Violation by supervisor', 3),
    ('1-4', 11, 'Operation equipment without authority', 4),
    ('1-5', 11, 'Improper position or posture for the task', 5),
    ('1-6', 11, 'Overexertion of physical capability', 6),
    ('1-7', 11, 'Work or motion at improper speed', 7),
    ('1-8', 11, 'Improper lifting', 8),
    ('1-9', 11, 'Improper loading', 9),
    ('1-10', 11, 'Shortcuts', 10),
    -- Category 12: Use of Tools or Equipment (2-x)
    ('2-1', 12, 'Use of defective equipment (aware)', 1),
    ('2-2', 12, 'Improper use of equipment', 2),
    ('2-3', 12, 'Use of equipment in unsafe manner', 3),
    ('2-4', 12, 'Using equipment beyond its capacity', 4),
    ('2-5', 12, 'Use of tools/equipment for wrong purpose', 5),
    ('2-6', 12, 'Failure to secure/lock out equipment', 6),
    ('2-7', 12, 'Operation of equipment at improper speed', 7),
    ('2-8', 12, 'Removal/bypass of safety devices', 8),
    -- Category 13: Use of Protective Methods (3-x)
    ('3-1', 13, 'Lack of knowledge of hazards present', 1),
    ('3-2', 13, 'Failure to use available PPE', 2),
    ('3-3', 13, 'Improper use of PPE', 3),
    ('3-4', 13, 'Failure to warn co-workers of hazard', 4),
    ('3-5', 13, 'Failure to isolate/secure work area', 5),
    ('3-6', 13, 'Use of defective PPE', 6),
    -- Category 14: Inattention / Lack of Awareness (4-x)
    ('4-1', 14, 'Failure to observe surroundings', 1),
    ('4-2', 14, 'Distracted by other concerns', 2),
    ('4-3', 14, 'Failure to identify changing conditions', 3),
    ('4-4', 14, 'Complacency due to routine task', 4),
    ('4-5', 14, 'Failure to communicate intentions', 5),
    ('4-6', 14, 'Working while fatigued', 6),
    -- Category 21: Protective Systems (5-x)
    ('5-1', 21, 'Missing or inadequate guards/barriers', 1),
    ('5-2', 21, 'Defective safety devices', 2),
    ('5-3', 21, 'Missing warning signs/alarms', 3),
    ('5-4', 21, 'Inadequate fire protection systems', 4),
    ('5-5', 21, 'Insufficient ventilation/exhaust systems', 5),
    -- Category 22: Tools, Equipment & Vehicles (6-x)
    ('6-1', 22, 'Defective tools or equipment', 1),
    ('6-2', 22, 'Equipment not fit for purpose', 2),
    ('6-3', 22, 'Poorly maintained machinery', 3),
    ('6-4', 22, 'Inadequate material handling equipment', 4),
    ('6-5', 22, 'Improper equipment configuration', 5),
    -- Category 23: Work Exposures (7-x)
    ('7-1', 23, 'Exposure to harmful substances', 1),
    ('7-2', 23, 'Exposure to extreme temperatures', 2),
    ('7-3', 23, 'Excessive noise levels', 3),
    ('7-4', 23, 'Exposure to radiation', 4),
    ('7-5', 23, 'Exposure to confined spaces without controls', 5),
    -- Category 24: Work Place Environment / Layout (8-x)
    ('8-1', 24, 'Poor housekeeping/cluttered work area', 1),
    ('8-2', 24, 'Inadequate lighting', 2),
    ('8-3', 24, 'Slippery/uneven walking surfaces', 3),
    ('8-4', 24, 'Congested work space', 4),
    ('8-5', 24, 'Inadequate access/egress routes', 5),
    -- Category 31: Physical Capability (P1-x)
    ('P1-1', 31, 'Physical limitations preventing safe task performance', 1),
    ('P1-2', 31, 'Insufficient strength or endurance', 2),
    ('P1-3', 31, 'Restricted range of movement', 3),
    ('P1-4', 31, 'Impaired vision or hearing', 4),
    -- Category 32: Physical Condition (P2-x)
    ('P2-1', 32, 'Illness or pre-existing medical condition', 1),
    ('P2-2', 32, 'Fatigue from overwork or insufficient rest', 2),
    ('P2-3', 32, 'Effects of medication or substances', 3),
    ('P2-4', 32, 'Impaired by injury', 4),
    -- Category 33: Mental State (P3-x)
    ('P3-1', 33, 'Fear or anxiety affecting performance', 1),
    ('P3-2', 33, 'Emotional distress', 2),
    ('P3-3', 33, 'Depression or low morale', 3),
    ('P3-4', 33, 'Overconfidence', 4),
    -- Category 34: Mental Stress (P4-x)
    ('P4-1', 34, 'Mental overload (task complexity)', 1),
    ('P4-2', 34, 'Conflicting demands or priorities', 2),
    ('P4-3', 34, 'Time pressure leading to errors', 3),
    ('P4-4', 34, 'Boredom or monotonous tasks', 4),
    -- Category 35: Behavior (P5-x)
    ('P5-1', 35, 'Risk-taking behavior', 1),
    ('P5-2', 35, 'Disregard for safety rules', 2),
    ('P5-3', 35, 'Attempting to save time/effort', 3),
    ('P5-4', 35, 'Peer pressure to take shortcuts', 4),
    -- Category 36: Skill Level (P6-x)
    ('P6-1', 36, 'Insufficient training for task', 1),
    ('P6-2', 36, 'Inadequate practice or experience', 2),
    ('P6-3', 36, 'New to the task or environment', 3),
    ('P6-4', 36, 'Skills not maintained through refresher training', 4),
    -- Category 41: Training / Knowledge Transfer (J7-x)
    ('J7-1', 41, 'Inadequate training program', 1),
    ('J7-2', 41, 'Lack of familiarization training', 2),
    ('J7-3', 41, 'No competency verification after training', 3),
    ('J7-4', 41, 'Poor knowledge transfer during handover', 4),
    -- Category 42: Management / Supervision / Leadership (J8-x)
    ('J8-1', 42, 'Inadequate supervision of work', 1),
    ('J8-2', 42, 'Failure to enforce safety rules', 2),
    ('J8-3', 42, 'Poor safety leadership', 3),
    ('J8-4', 42, 'Lack of management commitment to safety', 4),
    -- Category 43: Contractor Selection & Oversight (J9-x)
    ('J9-1', 43, 'Inadequate contractor vetting process', 1),
    ('J9-2', 43, 'Insufficient oversight of contractor work', 2),
    ('J9-3', 43, 'Poor communication with contractor personnel', 3),
    -- Category 44: Engineering / Design (J10-x)
    ('J10-1', 44, 'Inadequate design for safe operation', 1),
    ('J10-2', 44, 'Failure to consider human factors in design', 2),
    ('J10-3', 44, 'Inadequate ergonomic design', 3),
    -- Category 45: Work Planning (J11-x)
    ('J11-1', 45, 'Inadequate job/task planning', 1),
    ('J11-2', 45, 'Failure to identify hazards in planning', 2),
    ('J11-3', 45, 'Insufficient resource allocation', 3),
    ('J11-4', 45, 'Poor permit-to-work implementation', 4),
    -- Category 46: Purchasing, Material Handling & Control (J12-x)
    ('J12-1', 46, 'Procurement of substandard materials/equipment', 1),
    ('J12-2', 46, 'Improper storage of materials', 2),
    ('J12-3', 46, 'Inadequate material handling procedures', 3),
    -- Category 47: Tools & Equipment (J13-x)
    ('J13-1', 47, 'Inadequate maintenance program', 1),
    ('J13-2', 47, 'Failure to replace worn/defective equipment', 2),
    ('J13-3', 47, 'Insufficient spare parts availability', 3),
    -- Category 48: Work Rules / Policies / Standards / Procedures (J14-x)
    ('J14-1', 48, 'Outdated or missing procedures', 1),
    ('J14-2', 48, 'Procedures not practical for actual conditions', 2),
    ('J14-3', 48, 'Conflicting procedures or standards', 3),
    ('J14-4', 48, 'Inadequate risk assessment procedures', 4),
    -- Category 49: Communication (J15-x)
    ('J15-1', 49, 'Inadequate communication of safety information', 1),
    ('J15-2', 49, 'Language barriers', 2),
    ('J15-3', 49, 'Poor shift handover communication', 3);
    PRINT 'Inserted 92 CLC items across all 23 categories';
END
ELSE
    PRINT 'CLC items already exist — skipping';

-- =====================================================
-- 9. SEED DATA — PSC Deficiency Categories
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM PSC_Def_Category WHERE Category_Code = '01')
BEGIN
    INSERT INTO PSC_Def_Category (Category_Code, Category_Name, Sort_Order) VALUES
    ('01', 'Certificates & Documentation', 1),
    ('02', 'Structural condition', 2),
    ('03', 'Water/Weathertight condition', 3),
    ('04', 'Emergency Systems', 4),
    ('05', 'Radio communication', 5),
    ('06', 'Cargo operations including equipment', 6),
    ('07', 'Fire safety', 7),
    ('08', 'Alarms', 8),
    ('09', 'Working and Living Conditions', 9),
    ('10', 'Safety of Navigation', 10),
    ('11', 'Life saving appliances', 11),
    ('12', 'Dangerous Goods', 12),
    ('13', 'Propulsion and auxiliary machinery', 13),
    ('14', 'Pollution Prevention', 14),
    ('15', 'ISM', 15),
    ('16', 'ISPS', 16),
    ('18', 'MLC, 2006', 18),
    ('99', 'Other', 99);
    PRINT 'Inserted 18 deficiency categories';
END
ELSE
    PRINT 'Deficiency categories already exist — skipping';

-- =====================================================
-- 10. SEED DATA — PSC Deficiency Subcategories
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM PSC_Def_Subcategory WHERE Subcategory_Code = '011')
BEGIN
    INSERT INTO PSC_Def_Subcategory (Subcategory_Code, Category_Code, Subcategory_Name, Sort_Order) VALUES
    ('011', '01', 'Ship Certificate', 1),
    ('012', '01', 'Crew Certificate', 2),
    ('013', '01', 'Document', 3),
    ('091', '09', 'Living conditions', 1),
    ('092', '09', 'Working Conditions', 2),
    ('141', '14', 'MARPOL Annex I', 1),
    ('142', '14', 'MARPOL Annex II', 2),
    ('143', '14', 'MARPOL Annex III', 3),
    ('144', '14', 'MARPOL Annex IV', 4),
    ('145', '14', 'MARPOL Annex V', 5),
    ('146', '14', 'MARPOL Annex VI', 6),
    ('147', '14', 'Anti Fouling', 7),
    ('181', '18', 'Minimum requirements to work on a ship', 1),
    ('182', '18', 'Conditions of employment', 2),
    ('183', '18', 'Accommodation, recreational facilities, food and catering', 3),
    ('184', '18', 'Health protection, medical care, social security', 4);
    PRINT 'Inserted 16 deficiency subcategories';
END
ELSE
    PRINT 'Deficiency subcategories already exist — skipping';

-- =====================================================
-- 11. SEED DATA — PSC Deficiency Codes (essential subset)
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM PSC_Def_Code WHERE Def_Code = '01101')
BEGIN
    -- 01 - Certificates & Documentation (Ship Certificates)
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('01101', '01', '011', 'Cargo ship safety equipment (including exemption)', 1),
    ('01102', '01', '011', 'Cargo ship safety construction (including exempt.)', 2),
    ('01106', '01', '011', 'Document of compliance (DoC/ ISM)', 6),
    ('01107', '01', '011', 'Safety management certificate (SMC/ ISM)', 7),
    ('01113', '01', '011', 'Minimum safe manning document', 13),
    ('01122', '01', '011', 'International ship security certificate', 22),
    ('01139', '01', '011', 'Maritime Labour Certificate', 39);

    -- 01 - Crew Certificates
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('01201', '01', '012', 'Certificates for master and officers', 1),
    ('01202', '01', '012', 'Certificate for rating for watchkeeping', 2),
    ('01209', '01', '012', 'Manning specified by the minimum safe manning doc', 9);

    -- 01 - Documents
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('01309', '01', '013', 'Fire control plan - all', 9),
    ('01314', '01', '013', 'Shipboard oil pollution emergency plan (SOPEP)', 14),
    ('01315', '01', '013', 'Oil record book', 15);

    -- 02 - Structural condition
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('02105', '02', NULL, 'Steering gear', 5),
    ('02106', '02', NULL, 'Hull damage impairing seaworthiness', 6),
    ('02108', '02', NULL, 'Electric equipment in general', 8);

    -- 04 - Emergency Systems
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('04102', '04', NULL, 'Emergency fire pump and its pipes', 2),
    ('04103', '04', NULL, 'Emergency lighting, batteries and switches', 3),
    ('04108', '04', NULL, 'Muster list', 8),
    ('04109', '04', NULL, 'Fire drills', 9);

    -- 07 - Fire safety
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('07106', '07', NULL, 'Fire detection', 6),
    ('07108', '07', NULL, 'Ready availability of fire fighting equipment', 8),
    ('07109', '07', NULL, 'Fixed fire extinguishing installation', 9),
    ('07110', '07', NULL, 'Fire fighting equipment and appliances', 10),
    ('07120', '07', NULL, 'Means of escape', 20);

    -- 10 - Safety of Navigation
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('10103', '10', NULL, 'Radar', 3),
    ('10111', '10', NULL, 'Charts', 11),
    ('10112', '10', NULL, 'Electronic charts (ECDIS)', 12),
    ('10113', '10', NULL, 'Automatic Identification System (AIS)', 13),
    ('10127', '10', NULL, 'Voyage or passage plan', 27);

    -- 11 - Life saving appliances
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('11101', '11', NULL, 'Lifeboats', 1),
    ('11108', '11', NULL, 'Inflatable liferafts', 8),
    ('11117', '11', NULL, 'Lifebuoys incl. provision and disposition', 17),
    ('11118', '11', NULL, 'Lifejackets incl. provision and disposition', 18);

    -- 13 - Propulsion and auxiliary machinery
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('13101', '13', NULL, 'Propulsion main engine', 1),
    ('13102', '13', NULL, 'Auxiliary engine', 2),
    ('13104', '13', NULL, 'Bilge pumping arrangements', 4);

    -- 14 - Pollution Prevention
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('14101', '14', '141', 'Control of discharge of oil', 1),
    ('14104', '14', '141', 'Oil filtering equipment', 4),
    ('14501', '14', '145', 'Garbage', 1);

    -- 15 - ISM
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('15150', '15', NULL, 'ISM', 1);

    -- 16 - ISPS
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('16103', '16', NULL, 'Ship security plan', 3),
    ('16105', '16', NULL, 'Access control to ship', 5);

    -- 99 - Other
    INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
    ('99101', '99', NULL, 'Other safety in general', 1);

    PRINT 'Inserted 42 deficiency codes (essential subset)';
END
ELSE
    PRINT 'Deficiency codes already exist — skipping';

-- =====================================================
-- 12. SEED DATA — Rank Master
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM master_applied_rank WHERE rank_name = 'Master')
BEGIN
    INSERT INTO master_applied_rank (id, rank_name, rank_id) VALUES
    (NEWID(), 'Master', 'MST'),
    (NEWID(), 'Chief Officer', 'CO'),
    (NEWID(), 'Chief Engineer', 'CE'),
    (NEWID(), 'Second Officer', '2O'),
    (NEWID(), 'Second Engineer', '2E'),
    (NEWID(), 'Third Officer', '3O'),
    (NEWID(), 'Third Engineer', '3E'),
    (NEWID(), 'Bosun', 'BSN'),
    (NEWID(), 'ETO', 'ETO'),
    (NEWID(), 'Able Seaman', 'AB'),
    (NEWID(), 'Oiler', 'OLR');
    PRINT 'Inserted 11 ranks';
END
ELSE
    PRINT 'Ranks already exist — skipping';

-- =====================================================
-- 13. SEED DATA — Test Users
-- =====================================================

-- Vessel IDs from existing VesselData:
-- KSM Pioneer  = 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73'
-- KSM Voyager  = '40234651-e087-44cd-a90e-a5fd2798e6d2'
-- KSM Explorer = 'fb0e9c4b-5bff-4242-94f2-0ef5973d94a7'

-- 13a. Vessel Users (HRM501)
IF NOT EXISTS (SELECT 1 FROM HRM501 WHERE user_id = 'master001')
BEGIN
    INSERT INTO HRM501 (id, CrewID, first_name, surname, rank_name, department_name, user_id, password, vessel_id) VALUES
    (NEWID(), 'CRW0001', 'John', 'Smith', 'Master', 'Deck', 'master001', 'test123', 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73'),
    (NEWID(), 'CRW0002', 'James', 'Wilson', 'Able Seaman', 'Deck', 'crew001', 'test123', 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73'),
    (NEWID(), 'CRW0003', 'Robert', 'Brown', 'Chief Officer', 'Deck', 'co001', 'test123', 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73'),
    (NEWID(), 'CRW0004', 'David', 'Lee', 'Chief Engineer', 'Engine', 'ce001', 'test123', 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73'),
    (NEWID(), 'CRW0005', 'Michael', 'Taylor', 'Master', 'Deck', 'master002', 'test123', '40234651-e087-44cd-a90e-a5fd2798e6d2'),
    (NEWID(), 'CRW0006', 'Kevin', 'Park', 'Second Engineer', 'Engine', '2e001', 'test123', 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73');
    PRINT 'Inserted 6 vessel users';
END
ELSE
    PRINT 'Vessel users already exist — skipping';

-- 13b. Office Users
IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'pic001')
BEGIN
    INSERT INTO users (employee_id, employee_name, display_name, email_id, username, password, employee_role, department) VALUES
    ('EMP001', 'Alice Johnson', 'Alice J.', 'alice@ksm.com', 'pic001', 'test123', 'PIC', 'Marine'),
    ('EMP002', 'Bob Martinez', 'Bob M.', 'bob@ksm.com', 'ssqe001', 'test123', 'SSQE', 'Safety'),
    ('EMP003', 'Carol White', 'Carol W.', 'carol@ksm.com', 'dpa001', 'test123', 'DPA', 'Management'),
    ('EMP004', 'Dan Green', 'Dan G.', 'dan@ksm.com', 'supt001', 'test123', 'Superintendent', 'Marine'),
    ('EMP005', 'Eve Black', 'Eve B.', 'eve@ksm.com', 'pv001', 'test123', 'Physical Verifier', 'Marine');
    PRINT 'Inserted 5 office users';
END
ELSE
    PRINT 'Office users already exist — skipping';

-- 13c. Role-by-Vessel assignments (office users to vessels)
IF NOT EXISTS (SELECT 1 FROM master_RoleByVessel WHERE UserId = 'EMP001')
BEGIN
    -- PIC assigned to all 3 vessels
    INSERT INTO master_RoleByVessel (Id, VesselId, UserId) VALUES
    (NEWID(), 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73', 'EMP001'),
    (NEWID(), '40234651-e087-44cd-a90e-a5fd2798e6d2', 'EMP001'),
    (NEWID(), 'fb0e9c4b-5bff-4242-94f2-0ef5973d94a7', 'EMP001');

    -- SSQE assigned to KSM Pioneer and KSM Voyager
    INSERT INTO master_RoleByVessel (Id, VesselId, UserId) VALUES
    (NEWID(), 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73', 'EMP002'),
    (NEWID(), '40234651-e087-44cd-a90e-a5fd2798e6d2', 'EMP002');

    -- DPA assigned to all 3 vessels
    INSERT INTO master_RoleByVessel (Id, VesselId, UserId) VALUES
    (NEWID(), 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73', 'EMP003'),
    (NEWID(), '40234651-e087-44cd-a90e-a5fd2798e6d2', 'EMP003'),
    (NEWID(), 'fb0e9c4b-5bff-4242-94f2-0ef5973d94a7', 'EMP003');

    -- Superintendent assigned to KSM Pioneer
    INSERT INTO master_RoleByVessel (Id, VesselId, UserId) VALUES
    (NEWID(), 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73', 'EMP004');

    -- Physical Verifier assigned to KSM Pioneer
    INSERT INTO master_RoleByVessel (Id, VesselId, UserId) VALUES
    (NEWID(), 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73', 'EMP005');

    PRINT 'Inserted 10 vessel-role assignments';
END
ELSE
    PRINT 'Vessel-role assignments already exist — skipping';

-- 13d. master_role
-- (24 rows)
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'f415d39c-4037-ee11-b023-782b4610c006')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f415d39c-4037-ee11-b023-782b4610c006', 'Operation Team', 1, 1, NULL, '2023-08-10T11:11:55.357', NULL, '2024-05-27T16:12:33.89');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '9ec9fb38-95cd-ef11-aa02-9aca9a39e86d')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9ec9fb38-95cd-ef11-aa02-9aca9a39e86d', 'Observer', 1, 0, NULL, '2025-01-08T13:20:27.16', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '841c6054-a5d1-ef11-aa02-9aca9a39e86d')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('841c6054-a5d1-ef11-aa02-9aca9a39e86d', 'Purchase Executive', 1, 0, NULL, '2025-01-13T17:26:45.343', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'a103b023-a6d1-ef11-aa02-9aca9a39e86d')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a103b023-a6d1-ef11-aa02-9aca9a39e86d', 'Purchase Manager', 1, 0, NULL, '2025-01-13T17:31:37.527', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '4bb2b3f3-d1b8-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4bb2b3f3-d1b8-ed11-99ad-9da677dd1a69', 'Test_New', 1, 1, NULL, '2023-03-02T08:12:20.463', NULL, '2024-05-27T16:12:28.233');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '7195f6af-87c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7195f6af-87c4-ed11-99ad-9da677dd1a69', 'Operational Section', 1, 1, NULL, '2023-07-29T12:44:09.84', NULL, '2024-05-27T16:12:38.443');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'c9840f10-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c9840f10-88c4-ed11-99ad-9da677dd1a69', 'Change Request', 1, 1, NULL, '2023-03-17T05:53:39.24', NULL, '2024-05-27T16:12:43.583');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'b4dd2c54-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('b4dd2c54-88c4-ed11-99ad-9da677dd1a69', 'View_Only', 1, 1, NULL, '2023-03-17T05:55:33.517', NULL, '2024-05-27T16:12:48.323');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '53718017-e8a2-ed11-b6bb-a864f15c6e2f')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('53718017-e8a2-ed11-b6bb-a864f15c6e2f', 'admin', 1, 0, NULL, '2024-05-27T15:29:16.77', NULL, '2025-02-10T15:39:48.887');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 'Fleet Manager', 1, 0, NULL, '2024-05-27T16:04:17.67', NULL, '2024-05-27T15:25:58.82');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '09f8d8f5-1fa6-ed11-b6bc-a864f15c6e2f')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('09f8d8f5-1fa6-ed11-b6bc-a864f15c6e2f', 'New Request', 1, 1, NULL, '2023-02-06T18:42:52.717', NULL, '2024-05-27T16:12:52.68');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '26d5ad8f-83e3-ef11-aa04-cd8db15ac468')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('26d5ad8f-83e3-ef11-aa04-cd8db15ac468', 'Accounts', 1, 0, NULL, '2025-02-05T11:09:27.25', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'c9ca60a5-9c20-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c9ca60a5-9c20-ee11-99ae-da75f524456d', 'SupportTeam', 1, 1, NULL, '2023-07-12T15:42:46.66', NULL, '2024-05-27T16:12:57.42');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 'Developer', 1, 1, NULL, '2023-06-15T12:31:45.997', NULL, '2024-05-27T16:13:15.117');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '2abce8a3-4a0b-ee11-b6ad-dc1ba160dafa')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('2abce8a3-4a0b-ee11-b6ad-dc1ba160dafa', 'Tester', 1, 1, NULL, '2023-06-15T12:32:51.047', NULL, '2024-05-27T16:13:20.23');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '1baaa9b0-0c1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('1baaa9b0-0c1c-ef11-a9f1-f348983bae6b', 'Super Admin', 1, 0, NULL, '2024-05-27T15:07:11.093', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '30723f07-0f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('30723f07-0f1c-ef11-a9f1-f348983bae6b', 'Fleet_Manager', 1, 1, NULL, '2024-05-27T16:01:17.57', NULL, '2024-05-27T16:13:26.733');
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'd604980f-0f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('d604980f-0f1c-ef11-a9f1-f348983bae6b', 'Technical Superintendent', 1, 0, NULL, '2024-05-27T15:26:38.467', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '407ef017-0f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('407ef017-0f1c-ef11-a9f1-f348983bae6b', 'Marine Superintendent', 1, 0, NULL, '2024-05-27T15:26:49.567', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '809c3c1e-0f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('809c3c1e-0f1c-ef11-a9f1-f348983bae6b', 'SEQ Manager', 1, 0, NULL, '2024-05-27T15:24:33.92', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'a446e624-0f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a446e624-0f1c-ef11-a9f1-f348983bae6b', 'Crewing Manager', 1, 0, NULL, '2024-05-27T15:24:45.087', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '0c3ad72b-0f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0c3ad72b-0f1c-ef11-a9f1-f348983bae6b', 'Crewing Executive', 1, 0, NULL, '2024-05-27T15:24:56.73', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = 'ad92a33d-191c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ad92a33d-191c-ef11-a9f1-f348983bae6b', 'Energy Efficiency and Operations Officer', 1, 0, NULL, '2024-05-27T16:37:01.557', NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM master_role WHERE id = '28d37c55-191c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO master_role (id, role_name, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('28d37c55-191c-ef11-a9f1-f348983bae6b', 'Senior Technical Superintendent', 1, 0, NULL, '2024-05-27T16:37:41.587', NULL, NULL);
END

-- 13e. mapping_role_user
-- (256 rows)
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '232dc207-5db4-ee11-988b-7413ea3d6a70')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('232dc207-5db4-ee11-988b-7413ea3d6a70', '20230072', 'f415d39c-4037-ee11-b023-782b4610c006', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'db742829-cb18-ef11-98a8-7413ea3d6a70')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('db742829-cb18-ef11-98a8-7413ea3d6a70', 'roop@123', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0e62d53b-cf18-ef11-98a8-7413ea3d6a70')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0e62d53b-cf18-ef11-98a8-7413ea3d6a70', 'dcdscs', 'f415d39c-4037-ee11-b023-782b4610c006', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f43dc9c6-d118-ef11-98a8-7413ea3d6a70')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f43dc9c6-d118-ef11-98a8-7413ea3d6a70', 'sXSx', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a1d0f90f-d518-ef11-98a8-7413ea3d6a70')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a1d0f90f-d518-ef11-98a8-7413ea3d6a70', '1021771655', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e6844489-d518-ef11-98a8-7413ea3d6a70')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e6844489-d518-ef11-98a8-7413ea3d6a70', 'dscsdc', '4bb2b3f3-d1b8-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4697aa7f-c319-ef11-98a8-7413ea3d6a70')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4697aa7f-c319-ef11-98a8-7413ea3d6a70', 'roopam.198604', 'b4dd2c54-88c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '38b8cecf-8078-ee11-986d-745d223e029b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('38b8cecf-8078-ee11-986d-745d223e029b', '20230001', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '9149cc93-1b7e-ee11-9872-745d223e029b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9149cc93-1b7e-ee11-9872-745d223e029b', '20230003', '4bb2b3f3-d1b8-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3b3064f8-fa81-ee11-9873-745d223e029b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3b3064f8-fa81-ee11-9873-745d223e029b', '20230002', '4bb2b3f3-d1b8-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'dabed9f1-6187-ee11-987b-745d223e029b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('dabed9f1-6187-ee11-987b-745d223e029b', '200231004', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f0dadb92-f32d-ee11-b020-782b4610c006')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f0dadb92-f32d-ee11-b020-782b4610c006', '10217715', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '18e01f42-f72d-ee11-b020-782b4610c006')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('18e01f42-f72d-ee11-b020-782b4610c006', '10217716', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '8254919f-f72d-ee11-b020-782b4610c006')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('8254919f-f72d-ee11-b020-782b4610c006', '10217717', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ce70afb6-1235-ee11-b020-782b4610c006')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ce70afb6-1235-ee11-b020-782b4610c006', '10217720', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4763794c-95cd-ef11-aa02-9aca9a39e86d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4763794c-95cd-ef11-aa02-9aca9a39e86d', 'SFYC_Araya', '9ec9fb38-95cd-ef11-aa02-9aca9a39e86d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a01d3bcb-a5d1-ef11-aa02-9aca9a39e86d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a01d3bcb-a5d1-ef11-aa02-9aca9a39e86d', 'Gauri2025', '841c6054-a5d1-ef11-aa02-9aca9a39e86d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '9ff170ca-a6d1-ef11-aa02-9aca9a39e86d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9ff170ca-a6d1-ef11-aa02-9aca9a39e86d', 'Sunita', 'a103b023-a6d1-ef11-aa02-9aca9a39e86d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '9322f72e-9ea7-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9322f72e-9ea7-ed11-99ad-9da677dd1a69', '62266451', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7ec9c1b3-2ea8-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7ec9c1b3-2ea8-ed11-99ad-9da677dd1a69', '61455645', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '66c3e6f4-01bc-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('66c3e6f4-01bc-ed11-99ad-9da677dd1a69', '10217714', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '2b6cec33-0ebc-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('2b6cec33-0ebc-ed11-99ad-9da677dd1a69', '61377055', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'bd08f840-10bc-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('bd08f840-10bc-ed11-99ad-9da677dd1a69', '61345646', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'be08f840-10bc-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('be08f840-10bc-ed11-99ad-9da677dd1a69', '61382598', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '559de9e4-45bf-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('559de9e4-45bf-ed11-99ad-9da677dd1a69', '61395258', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '43e38178-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('43e38178-88c4-ed11-99ad-9da677dd1a69', '61235196', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'b7678c7f-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('b7678c7f-88c4-ed11-99ad-9da677dd1a69', '10251061', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '989caf85-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('989caf85-88c4-ed11-99ad-9da677dd1a69', '61314968', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6d13748d-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6d13748d-88c4-ed11-99ad-9da677dd1a69', '61317489', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '073db498-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('073db498-88c4-ed11-99ad-9da677dd1a69', '61346740', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '8fae02ba-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('8fae02ba-88c4-ed11-99ad-9da677dd1a69', '61317801', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ee9270ca-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ee9270ca-88c4-ed11-99ad-9da677dd1a69', '61348601', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '64332cdc-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('64332cdc-88c4-ed11-99ad-9da677dd1a69', '61350239', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '43c3e4e3-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('43c3e4e3-88c4-ed11-99ad-9da677dd1a69', '61351666', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e0e8e0ea-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e0e8e0ea-88c4-ed11-99ad-9da677dd1a69', '61362499', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'dff0d7ff-88c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('dff0d7ff-88c4-ed11-99ad-9da677dd1a69', '61370627', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '87ae3512-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('87ae3512-89c4-ed11-99ad-9da677dd1a69', '61371424', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f2766b1e-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f2766b1e-89c4-ed11-99ad-9da677dd1a69', '61373607', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '66b86626-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('66b86626-89c4-ed11-99ad-9da677dd1a69', '61378431', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '01c3d72d-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('01c3d72d-89c4-ed11-99ad-9da677dd1a69', '61406477', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f43a9f37-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f43a9f37-89c4-ed11-99ad-9da677dd1a69', '61424591', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '948b5864-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('948b5864-89c4-ed11-99ad-9da677dd1a69', '61432903', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '59a8feb3-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('59a8feb3-89c4-ed11-99ad-9da677dd1a69', '62409712', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '802ac3c3-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('802ac3c3-89c4-ed11-99ad-9da677dd1a69', '61437069', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '8ef38aca-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('8ef38aca-89c4-ed11-99ad-9da677dd1a69', '61443094', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '8ff38aca-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('8ff38aca-89c4-ed11-99ad-9da677dd1a69', '61443859', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '329dd5d4-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('329dd5d4-89c4-ed11-99ad-9da677dd1a69', '62017491', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '339dd5d4-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('339dd5d4-89c4-ed11-99ad-9da677dd1a69', '62043570', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3cf0c4dc-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3cf0c4dc-89c4-ed11-99ad-9da677dd1a69', '62102203', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c52408e5-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c52408e5-89c4-ed11-99ad-9da677dd1a69', '62111295', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c54d2beb-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c54d2beb-89c4-ed11-99ad-9da677dd1a69', '62231932', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c64d2beb-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c64d2beb-89c4-ed11-99ad-9da677dd1a69', '62246133', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '69935cf4-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('69935cf4-89c4-ed11-99ad-9da677dd1a69', '62312627', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6a935cf4-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6a935cf4-89c4-ed11-99ad-9da677dd1a69', '62325607', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '79c991fe-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('79c991fe-89c4-ed11-99ad-9da677dd1a69', '69105638', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7ac991fe-89c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7ac991fe-89c4-ed11-99ad-9da677dd1a69', '69130758', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0cfd1407-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0cfd1407-8ac4-ed11-99ad-9da677dd1a69', '69139287', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0dfd1407-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0dfd1407-8ac4-ed11-99ad-9da677dd1a69', '69139844', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '31d7ab11-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('31d7ab11-8ac4-ed11-99ad-9da677dd1a69', '69141569', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '64427f1b-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('64427f1b-8ac4-ed11-99ad-9da677dd1a69', '69212601', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '01c62875-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('01c62875-8ac4-ed11-99ad-9da677dd1a69', '69150889', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '132d9c7c-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('132d9c7c-8ac4-ed11-99ad-9da677dd1a69', '69156854', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '142d9c7c-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('142d9c7c-8ac4-ed11-99ad-9da677dd1a69', '69160409', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '26afd084-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('26afd084-8ac4-ed11-99ad-9da677dd1a69', '69161246', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '465ee39a-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('465ee39a-8ac4-ed11-99ad-9da677dd1a69', '69162827', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '35799aa1-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('35799aa1-8ac4-ed11-99ad-9da677dd1a69', '69181871', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '36799aa1-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('36799aa1-8ac4-ed11-99ad-9da677dd1a69', '69182946', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '79bd57a9-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('79bd57a9-8ac4-ed11-99ad-9da677dd1a69', '69186326', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7abd57a9-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7abd57a9-8ac4-ed11-99ad-9da677dd1a69', '69194889', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'cf961eb1-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('cf961eb1-8ac4-ed11-99ad-9da677dd1a69', '69202299', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '9e8855b9-8ac4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9e8855b9-8ac4-ed11-99ad-9da677dd1a69', '69208104', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a84b8221-90c4-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a84b8221-90c4-ed11-99ad-9da677dd1a69', '61446683', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'd5de4ba4-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('d5de4ba4-dac6-ed11-99ad-9da677dd1a69', '61434210', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0b283fad-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0b283fad-dac6-ed11-99ad-9da677dd1a69', '61457001', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0963e9b4-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0963e9b4-dac6-ed11-99ad-9da677dd1a69', '62020065', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3fc69abc-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3fc69abc-dac6-ed11-99ad-9da677dd1a69', '62185187', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '40c69abc-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('40c69abc-dac6-ed11-99ad-9da677dd1a69', '62217346', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7a0672c7-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7a0672c7-dac6-ed11-99ad-9da677dd1a69', '62231930', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6a7118ce-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6a7118ce-dac6-ed11-99ad-9da677dd1a69', '62327871', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6b7118ce-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6b7118ce-dac6-ed11-99ad-9da677dd1a69', '62336472', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '24b687d7-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('24b687d7-dac6-ed11-99ad-9da677dd1a69', '62352973', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '25b687d7-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('25b687d7-dac6-ed11-99ad-9da677dd1a69', '62368109', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e01ec0e0-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e01ec0e0-dac6-ed11-99ad-9da677dd1a69', '62375425', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e11ec0e0-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e11ec0e0-dac6-ed11-99ad-9da677dd1a69', '69139507', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '8b8a7feb-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('8b8a7feb-dac6-ed11-99ad-9da677dd1a69', '69141419', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e97f3df5-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e97f3df5-dac6-ed11-99ad-9da677dd1a69', '69162743', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a16069fc-dac6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a16069fc-dac6-ed11-99ad-9da677dd1a69', '69164344', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'eb94e103-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('eb94e103-dbc6-ed11-99ad-9da677dd1a69', '69172877', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '11e9ef0b-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('11e9ef0b-dbc6-ed11-99ad-9da677dd1a69', '62309605', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '84fb1a14-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('84fb1a14-dbc6-ed11-99ad-9da677dd1a69', '69180383', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a64e0d1e-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a64e0d1e-dbc6-ed11-99ad-9da677dd1a69', '69191550', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '67d47927-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('67d47927-dbc6-ed11-99ad-9da677dd1a69', '69194801', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3f5def31-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3f5def31-dbc6-ed11-99ad-9da677dd1a69', '69195796', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'eb51be40-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('eb51be40-dbc6-ed11-99ad-9da677dd1a69', '69206450', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7cf36249-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7cf36249-dbc6-ed11-99ad-9da677dd1a69', '69196115', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7df36249-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7df36249-dbc6-ed11-99ad-9da677dd1a69', '69203378', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '331b6057-dbc6-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('331b6057-dbc6-ed11-99ad-9da677dd1a69', '69196621', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '59165eb2-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('59165eb2-49c9-ed11-99ad-9da677dd1a69', '61279925', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'dcef63bf-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('dcef63bf-49c9-ed11-99ad-9da677dd1a69', '69203380', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '73c06dc6-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('73c06dc6-49c9-ed11-99ad-9da677dd1a69', '69213311', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '429987cd-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('429987cd-49c9-ed11-99ad-9da677dd1a69', '69209679', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6b05c6d3-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6b05c6d3-49c9-ed11-99ad-9da677dd1a69', '61409623', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a60d48da-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a60d48da-49c9-ed11-99ad-9da677dd1a69', '61410512', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a70d48da-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a70d48da-49c9-ed11-99ad-9da677dd1a69', '62111253', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3c298de7-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3c298de7-49c9-ed11-99ad-9da677dd1a69', '62380923', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '5ad166ee-49c9-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('5ad166ee-49c9-ed11-99ad-9da677dd1a69', '62385437', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ff759a9f-2bcd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ff759a9f-2bcd-ed11-99ad-9da677dd1a69', '62379321', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '1793f8a9-2bcd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('1793f8a9-2bcd-ed11-99ad-9da677dd1a69', '61347204', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4fc5c639-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4fc5c639-2ecd-ed11-99ad-9da677dd1a69', '61454638', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3756cf43-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3756cf43-2ecd-ed11-99ad-9da677dd1a69', '62287548', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3856cf43-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3856cf43-2ecd-ed11-99ad-9da677dd1a69', '62148116', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e4126650-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e4126650-2ecd-ed11-99ad-9da677dd1a69', '62295704', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c7b06159-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c7b06159-2ecd-ed11-99ad-9da677dd1a69', '62310167', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '1d95ce61-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('1d95ce61-2ecd-ed11-99ad-9da677dd1a69', '62388490', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0a8ecb6a-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0a8ecb6a-2ecd-ed11-99ad-9da677dd1a69', '69154261', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '164ca073-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('164ca073-2ecd-ed11-99ad-9da677dd1a69', '61438895', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'da8ccb7d-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('da8ccb7d-2ecd-ed11-99ad-9da677dd1a69', '69174229', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '304b1586-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('304b1586-2ecd-ed11-99ad-9da677dd1a69', '62368561', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f1d8b7cc-2ecd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f1d8b7cc-2ecd-ed11-99ad-9da677dd1a69', '62365035', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'db061711-30cd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('db061711-30cd-ed11-99ad-9da677dd1a69', '62272842', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6349d918-30cd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6349d918-30cd-ed11-99ad-9da677dd1a69', '69090467', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4665d357-35cd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4665d357-35cd-ed11-99ad-9da677dd1a69', '61369203', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '1b729f31-02d2-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('1b729f31-02d2-ed11-99ad-9da677dd1a69', '61476332', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e9845430-08dd-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e9845430-08dd-ed11-99ad-9da677dd1a69', '62382067', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '026d6f3b-43e3-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('026d6f3b-43e3-ed11-99ad-9da677dd1a69', '61388424', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '51d09526-46e3-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('51d09526-46e3-ed11-99ad-9da677dd1a69', '62416674', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '152df717-b3e8-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('152df717-b3e8-ed11-99ad-9da677dd1a69', '62235680', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f132db2c-b3e8-ed11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f132db2c-b3e8-ed11-99ad-9da677dd1a69', '62348303', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'fd553580-050c-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('fd553580-050c-ee11-99ad-9da677dd1a69', '62038599', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ae9176c5-9e11-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ae9176c5-9e11-ee11-99ad-9da677dd1a69', '69189404', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e14d1dd1-9e11-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e14d1dd1-9e11-ee11-99ad-9da677dd1a69', '69194675', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7cfdc0da-9e11-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7cfdc0da-9e11-ee11-99ad-9da677dd1a69', '61347534', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6d98fde1-9e11-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6d98fde1-9e11-ee11-99ad-9da677dd1a69', '61416507', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '8b2de0ea-9e11-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('8b2de0ea-9e11-ee11-99ad-9da677dd1a69', '69203900', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f54e53f5-9e11-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f54e53f5-9e11-ee11-99ad-9da677dd1a69', '69149658', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4de395c4-f313-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4de395c4-f313-ee11-99ad-9da677dd1a69', '69212905', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '2849a4cc-f313-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('2849a4cc-f313-ee11-99ad-9da677dd1a69', '69195126', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '25fc63d4-f313-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('25fc63d4-f313-ee11-99ad-9da677dd1a69', '61452639', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '393690e0-f313-ee11-99ad-9da677dd1a69')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('393690e0-f313-ee11-99ad-9da677dd1a69', '69209576', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '042671d2-01a3-ed11-b6bb-a864f15c6e2f')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('042671d2-01a3-ed11-b6bb-a864f15c6e2f', '69206036', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, '69206036', NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '2482d62e-8ca3-ed11-b6bb-a864f15c6e2f')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('2482d62e-8ca3-ed11-b6bb-a864f15c6e2f', '10241089', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'd94859fc-1e25-ee11-99af-b9474d69e51e')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('d94859fc-1e25-ee11-99af-b9474d69e51e', '69140478', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6a8426b8-3225-ee11-99af-b9474d69e51e')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6a8426b8-3225-ee11-99af-b9474d69e51e', '62388679', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a19f1e01-f825-ee11-99af-b9474d69e51e')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a19f1e01-f825-ee11-99af-b9474d69e51e', '62391235', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '90a3bc0b-f825-ee11-99af-b9474d69e51e')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('90a3bc0b-f825-ee11-99af-b9474d69e51e', '62280530', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'b4a98acb-cb26-ee11-99af-b9474d69e51e')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('b4a98acb-cb26-ee11-99af-b9474d69e51e', '62000217', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '86b495e7-cb26-ee11-99af-b9474d69e51e')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('86b495e7-cb26-ee11-99af-b9474d69e51e', '62280526', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ddbb8f74-612c-ee11-99af-b9474d69e51e')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ddbb8f74-612c-ee11-99af-b9474d69e51e', '62233206', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c5c452da-612c-ee11-99af-b9474d69e51e')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c5c452da-612c-ee11-99af-b9474d69e51e', '69208829', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e09c63e7-2e9d-f011-9dda-c3ff60c955a8')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e09c63e7-2e9d-f011-9dda-c3ff60c955a8', 'Aman.Oberoi', '407ef017-0f1c-ef11-a9f1-f348983bae6b', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '1dd09a9e-83e3-ef11-aa04-cd8db15ac468')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('1dd09a9e-83e3-ef11-aa04-cd8db15ac468', 'Suparanee', '26d5ad8f-83e3-ef11-aa04-cd8db15ac468', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'fa38d633-97e7-ef11-aa04-cd8db15ac468')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('fa38d633-97e7-ef11-aa04-cd8db15ac468', 'KD.Singh', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '314c130a-45e8-ef11-aa04-cd8db15ac468')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('314c130a-45e8-ef11-aa04-cd8db15ac468', 'Don', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '45958f6e-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('45958f6e-b615-ee11-99ae-da75f524456d', '61449841', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'cda02377-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('cda02377-b615-ee11-99ae-da75f524456d', '61299151', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f59e7880-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f59e7880-b615-ee11-99ae-da75f524456d', '61383242', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '031fdb8a-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('031fdb8a-b615-ee11-99ae-da75f524456d', '61409143', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '44c7939a-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('44c7939a-b615-ee11-99ae-da75f524456d', '61463507', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '01c546a3-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('01c546a3-b615-ee11-99ae-da75f524456d', '62002068', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3de2ffac-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3de2ffac-b615-ee11-99ae-da75f524456d', '62217050', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '422e07b5-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('422e07b5-b615-ee11-99ae-da75f524456d', '62021186', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e83c3dbe-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e83c3dbe-b615-ee11-99ae-da75f524456d', '62280479', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '153bd1ce-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('153bd1ce-b615-ee11-99ae-da75f524456d', '62384018', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4580cbe2-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4580cbe2-b615-ee11-99ae-da75f524456d', '62385210', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4680cbe2-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4680cbe2-b615-ee11-99ae-da75f524456d', '62388697', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '208fd2f5-b615-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('208fd2f5-b615-ee11-99ae-da75f524456d', '62421258', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c9fe2509-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c9fe2509-b715-ee11-99ae-da75f524456d', '69158725', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'cafe2509-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('cafe2509-b715-ee11-99ae-da75f524456d', '69161256', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '9e9cf12b-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9e9cf12b-b715-ee11-99ae-da75f524456d', '69141472', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '063bbb38-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('063bbb38-b715-ee11-99ae-da75f524456d', '69173043', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4c37f248-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4c37f248-b715-ee11-99ae-da75f524456d', '69194769', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f0746454-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f0746454-b715-ee11-99ae-da75f524456d', '69201168', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '79c78cb0-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('79c78cb0-b715-ee11-99ae-da75f524456d', '69203515', 'c9ca60a5-9c20-ee11-99ae-da75f524456d', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6e6596b8-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6e6596b8-b715-ee11-99ae-da75f524456d', '69203624', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '941656c0-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('941656c0-b715-ee11-99ae-da75f524456d', '69205051', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0437ddc9-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0437ddc9-b715-ee11-99ae-da75f524456d', '69205735', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a3a0b8d2-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a3a0b8d2-b715-ee11-99ae-da75f524456d', '69212646', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '69dffdda-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('69dffdda-b715-ee11-99ae-da75f524456d', '69213437', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f268b6e2-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f268b6e2-b715-ee11-99ae-da75f524456d', '69214583', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '973c6aea-b715-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('973c6aea-b715-ee11-99ae-da75f524456d', '69215346', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'd9a14367-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('d9a14367-5116-ee11-99ae-da75f524456d', '69206708', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'da9f0278-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('da9f0278-5116-ee11-99ae-da75f524456d', '61455803', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '127f7283-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('127f7283-5116-ee11-99ae-da75f524456d', '62289077', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'e708a28e-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('e708a28e-5116-ee11-99ae-da75f524456d', '62296761', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '02374a9b-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('02374a9b-5116-ee11-99ae-da75f524456d', '62372196', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'bc9d99a5-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('bc9d99a5-5116-ee11-99ae-da75f524456d', '62375798', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'dddcf2ac-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('dddcf2ac-5116-ee11-99ae-da75f524456d', '62380767', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '2a02cbb6-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('2a02cbb6-5116-ee11-99ae-da75f524456d', '69144213', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6d790ec1-5116-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6d790ec1-5116-ee11-99ae-da75f524456d', '69193400', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '83856704-fd16-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('83856704-fd16-ee11-99ae-da75f524456d', '61351089', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '84856704-fd16-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('84856704-fd16-ee11-99ae-da75f524456d', '61365196', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '28b32719-fd16-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('28b32719-fd16-ee11-99ae-da75f524456d', '62018687', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7b41522f-fd16-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7b41522f-fd16-ee11-99ae-da75f524456d', '62388135', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0f598645-fd16-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0f598645-fd16-ee11-99ae-da75f524456d', '62413619', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '97338f5e-fd16-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('97338f5e-fd16-ee11-99ae-da75f524456d', '69178460', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ee1610b4-0b18-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ee1610b4-0b18-ee11-99ae-da75f524456d', '62312967', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ffe664c8-0b18-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ffe664c8-0b18-ee11-99ae-da75f524456d', '62384019', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '06ea71db-0b18-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('06ea71db-0b18-ee11-99ae-da75f524456d', '69148456', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '4e840625-211a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('4e840625-211a-ee11-99ae-da75f524456d', '10227816', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c4b62b39-211a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c4b62b39-211a-ee11-99ae-da75f524456d', '61365990', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c5b62b39-211a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c5b62b39-211a-ee11-99ae-da75f524456d', '61381955', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ad90df48-211a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ad90df48-211a-ee11-99ae-da75f524456d', '61462212', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '88581750-211a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('88581750-211a-ee11-99ae-da75f524456d', '61467279', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7dca475a-211a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7dca475a-211a-ee11-99ae-da75f524456d', '62418487', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '98172a66-211a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('98172a66-211a-ee11-99ae-da75f524456d', '69156321', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'd607f5ae-701a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('d607f5ae-701a-ee11-99ae-da75f524456d', '61315682', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f98dc7bf-701a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f98dc7bf-701a-ee11-99ae-da75f524456d', '61408229', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '9db807d6-701a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9db807d6-701a-ee11-99ae-da75f524456d', '69195790', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '2b2428e1-701a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('2b2428e1-701a-ee11-99ae-da75f524456d', '69153974', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '86fe3ff6-701a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('86fe3ff6-701a-ee11-99ae-da75f524456d', '69130865', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '527aa521-711a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('527aa521-711a-ee11-99ae-da75f524456d', '69023399', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a506307a-f31a-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a506307a-f31a-ee11-99ae-da75f524456d', '62366222', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '30c4d68c-031b-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('30c4d68c-031b-ee11-99ae-da75f524456d', '69162688', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '74619a9d-031b-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('74619a9d-031b-ee11-99ae-da75f524456d', '61322724', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '9b23fdff-1c1b-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9b23fdff-1c1b-ee11-99ae-da75f524456d', '61389170', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'b0053059-c41b-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('b0053059-c41b-ee11-99ae-da75f524456d', '69093973', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '1db56fa2-c81b-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('1db56fa2-c81b-ee11-99ae-da75f524456d', '69150436', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '7e9968ce-c81b-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('7e9968ce-c81b-ee11-99ae-da75f524456d', '62078434', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '87a2f106-7a1c-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('87a2f106-7a1c-ee11-99ae-da75f524456d', '61355351', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'b42f0816-7a1c-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('b42f0816-7a1c-ee11-99ae-da75f524456d', '69098844', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '54629a34-7a1c-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('54629a34-7a1c-ee11-99ae-da75f524456d', '69207273', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ebd47efc-b91c-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ebd47efc-b91c-ee11-99ae-da75f524456d', '69186466', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '9b5dddc3-351e-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('9b5dddc3-351e-ee11-99ae-da75f524456d', '62341683', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'd97557d8-1e1f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('d97557d8-1e1f-ee11-99ae-da75f524456d', '69216852', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3c00d2fe-1e1f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3c00d2fe-1e1f-ee11-99ae-da75f524456d', '69213241', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '34a1f74d-1f1f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('34a1f74d-1f1f-ee11-99ae-da75f524456d', '69087962', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '5d66a058-1f1f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('5d66a058-1f1f-ee11-99ae-da75f524456d', '69215208', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '1dffd264-1f1f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('1dffd264-1f1f-ee11-99ae-da75f524456d', '69035907', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '1de53670-1f1f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('1de53670-1f1f-ee11-99ae-da75f524456d', '69216566', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '3ba09391-b71f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('3ba09391-b71f-ee11-99ae-da75f524456d', '61380556', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '28badcc6-b71f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('28badcc6-b71f-ee11-99ae-da75f524456d', '62024933', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'dd5a69d1-b71f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('dd5a69d1-b71f-ee11-99ae-da75f524456d', '61378816', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'c99df12c-d21f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('c99df12c-d21f-ee11-99ae-da75f524456d', '69159792', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6e4555b4-d21f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6e4555b4-d21f-ee11-99ae-da75f524456d', '69201413', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0d9855c1-d21f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0d9855c1-d21f-ee11-99ae-da75f524456d', '69212552', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'a196371a-e51f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('a196371a-e51f-ee11-99ae-da75f524456d', '62374963', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '65cd5625-e51f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('65cd5625-e51f-ee11-99ae-da75f524456d', '62385224', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '71eae130-e51f-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('71eae130-e51f-ee11-99ae-da75f524456d', '62391574', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '5fcd1e01-6920-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('5fcd1e01-6920-ee11-99ae-da75f524456d', '69092470', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '23a85269-4a21-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('23a85269-4a21-ee11-99ae-da75f524456d', '61392482', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '34ea5d94-2a22-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('34ea5d94-2a22-ee11-99ae-da75f524456d', '62386369', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'd179f39b-2a22-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('d179f39b-2a22-ee11-99ae-da75f524456d', '69190620', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'b77960a8-2a22-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('b77960a8-2a22-ee11-99ae-da75f524456d', '69189559', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '0176554b-c722-ee11-99ae-da75f524456d')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('0176554b-c722-ee11-99ae-da75f524456d', '61448241', '7195f6af-87c4-ed11-99ad-9da677dd1a69', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'ebaf6891-b8ae-ee11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('ebaf6891-b8ae-ee11-a9f1-f348983bae6b', '20240001', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '94ae1108-240d-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('94ae1108-240d-ef11-a9f1-f348983bae6b', '12345678', 'a446e624-0f1c-ef11-a9f1-f348983bae6b', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '938f9651-de0d-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('938f9651-de0d-ef11-a9f1-f348983bae6b', '1357924680', '0c3ad72b-0f1c-ef11-a9f1-f348983bae6b', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '57f76bc3-0a1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('57f76bc3-0a1c-ef11-a9f1-f348983bae6b', 'xyzabc', '37cd227d-4a0b-ee11-b6ad-dc1ba160dafa', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '58ef752a-0e1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('58ef752a-0e1c-ef11-a9f1-f348983bae6b', 'KSM001', '53718017-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '6d8195df-191c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('6d8195df-191c-ef11-a9f1-f348983bae6b', 'Karan.Tikare', 'ad92a33d-191c-ef11-a9f1-f348983bae6b', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '99d41305-1b1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('99d41305-1b1c-ef11-a9f1-f348983bae6b', 'Prince. S', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'b586eae4-1b1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('b586eae4-1b1c-ef11-a9f1-f348983bae6b', 'Gaurav.M', '28d37c55-191c-ef11-a9f1-f348983bae6b', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = '61ecf26b-1c1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('61ecf26b-1c1c-ef11-a9f1-f348983bae6b', 'Prince.S', 'aea9911e-e8a2-ed11-b6bb-a864f15c6e2f', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'f82c77dd-1f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('f82c77dd-1f1c-ef11-a9f1-f348983bae6b', 'Harman.S', '809c3c1e-0f1c-ef11-a9f1-f348983bae6b', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'edf9d6e6-1f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('edf9d6e6-1f1c-ef11-a9f1-f348983bae6b', 'Pradeep.V', 'd604980f-0f1c-ef11-a9f1-f348983bae6b', 1, 1, NULL, NULL, NULL, NULL);
END
IF NOT EXISTS (SELECT 1 FROM mapping_role_user WHERE id = 'b44229f4-1f1c-ef11-a9f1-f348983bae6b')
BEGIN
    INSERT INTO mapping_role_user (id, userid, role_id, is_active, is_deleted, created_by, created_date, updated_by, updated_date) VALUES ('b44229f4-1f1c-ef11-a9f1-f348983bae6b', 'Tarun.S', '407ef017-0f1c-ef11-a9f1-f348983bae6b', 1, 1, NULL, NULL, NULL, NULL);
END

-- =====================================================
-- GAP-FILLING: Idempotent inserts for users that may
-- have been missed on earlier seed runs
-- =====================================================

-- crew001 (CRW0002) gap-fill
IF NOT EXISTS (SELECT 1 FROM HRM501 WHERE user_id = 'crew001')
BEGIN
    INSERT INTO HRM501 (id, CrewID, first_name, surname, rank_name, department_name, user_id, password, vessel_id)
    VALUES (NEWID(), 'CRW0002', 'James', 'Wilson', 'Able Seaman', 'Deck', 'crew001', 'test123', 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73');
    PRINT 'Gap-filled crew001';
END

-- 2e001 (CRW0006) gap-fill
IF NOT EXISTS (SELECT 1 FROM HRM501 WHERE user_id = '2e001')
BEGIN
    INSERT INTO HRM501 (id, CrewID, first_name, surname, rank_name, department_name, user_id, password, vessel_id)
    VALUES (NEWID(), 'CRW0006', 'Kevin', 'Park', 'Second Engineer', 'Engine', '2e001', 'test123', 'e2e7ff0d-ab6d-4485-afb8-aa45aa537d73');
    PRINT 'Gap-filled 2e001';
END

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

PRINT '';
PRINT '=== SEED DATA VERIFICATION ===';

SELECT 'master_psc_role' AS [Table], COUNT(*) AS [Count] FROM master_psc_role
UNION ALL
SELECT 'MOU_Master', COUNT(*) FROM MOU_Master
UNION ALL
SELECT 'PSC_Action_Codes', COUNT(*) FROM PSC_Action_Codes
UNION ALL
SELECT 'PIC_Master', COUNT(*) FROM PIC_Master
UNION ALL
SELECT 'CLC_Category', COUNT(*) FROM CLC_Category
UNION ALL
SELECT 'CLC_Item', COUNT(*) FROM CLC_Item
UNION ALL
SELECT 'PSC_Def_Category', COUNT(*) FROM PSC_Def_Category
UNION ALL
SELECT 'PSC_Def_Subcategory', COUNT(*) FROM PSC_Def_Subcategory
UNION ALL
SELECT 'PSC_Def_Code', COUNT(*) FROM PSC_Def_Code
UNION ALL
SELECT 'mapping_role_user', COUNT(*) FROM mapping_role_user
UNION ALL
SELECT 'master_role', COUNT(*) FROM master_role
UNION ALL
SELECT 'master_applied_rank', COUNT(*) FROM master_applied_rank
UNION ALL
SELECT 'HRM501', COUNT(*) FROM HRM501
UNION ALL
SELECT 'users (office)', COUNT(*) FROM users
UNION ALL
SELECT 'master_RoleByVessel', COUNT(*) FROM master_RoleByVessel;

PRINT '';
PRINT '=== TEST USER CREDENTIALS ===';
PRINT 'Vessel Master (KSM Pioneer): master001 / test123';
PRINT 'Vessel Crew   (KSM Pioneer): crew001  / test123';
PRINT 'Office PIC:                   pic001   / test123';
PRINT 'Office SSQE:                  ssqe001  / test123';
PRINT 'Office DPA:                   dpa001   / test123';
PRINT 'Office Supt:                  supt001  / test123';
PRINT 'Office PV:                    pv001    / test123';

COMMIT TRANSACTION;
PRINT '';
PRINT 'Seed data script completed successfully!';
