-- =====================================================
-- CAR System Database Schema v4.0
-- Unified PSC / RightShip / Audit Close-out Module
-- =====================================================

-- =====================================================
-- MASTER TABLES
-- =====================================================

-- MOU Master (All Port State MOUs)
CREATE TABLE MOU_Master (
    MOU_Code VARCHAR(20) PRIMARY KEY,
    MOU_Name VARCHAR(100) NOT NULL,
    Region VARCHAR(50),
    Is_Active BIT DEFAULT 1,
    Sort_Order INT DEFAULT 0
);

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
('VINA', 'Viña del Mar Agreement', 'Latin America', 10);

-- PSC Action Taken Codes
CREATE TABLE PSC_Action_Codes (
    Action_Code INT PRIMARY KEY,
    Definition VARCHAR(100) NOT NULL,
    Description VARCHAR(500),
    Is_Detention BIT DEFAULT 0,
    Requires_Follow_Up BIT DEFAULT 0,
    Is_Active BIT DEFAULT 1
);

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

-- Audit Type Master (Extensible)
CREATE TABLE Audit_Type_Master (
    Audit_Type_Code VARCHAR(20) PRIMARY KEY,
    Audit_Type_Name VARCHAR(100) NOT NULL,
    Category VARCHAR(50), -- Internal, External, Vetting, Flag State, Other
    Is_Active BIT DEFAULT 1,
    Sort_Order INT DEFAULT 0,
    Created_Date DATETIME DEFAULT GETDATE(),
    Created_By VARCHAR(50)
);

INSERT INTO Audit_Type_Master (Audit_Type_Code, Audit_Type_Name, Category, Sort_Order) VALUES
('INT_ISM', 'Internal ISM Audit', 'Internal', 1),
('EXT_ISM', 'External ISM Audit', 'External', 2),
('INT_ISPS', 'Internal ISPS Audit', 'Internal', 3),
('EXT_ISPS', 'External ISPS Audit', 'External', 4),
('INT_MLC', 'Internal MLC Audit', 'Internal', 5),
('EXT_MLC', 'External MLC Audit', 'External', 6),
('FLAG', 'Flag State Audit', 'Flag State', 7),
('SIRE', 'SIRE Inspection', 'Vetting', 8),
('CDI', 'CDI Inspection', 'Vetting', 9),
('TMSA', 'TMSA Assessment', 'Vetting', 10),
('OTHER', 'Other (Specify)', 'Other', 99);

-- NC Grade Master
CREATE TABLE NC_Grade_Master (
    NC_Grade_Code VARCHAR(20) PRIMARY KEY,
    NC_Grade_Name VARCHAR(50) NOT NULL,
    Severity_Level INT, -- 1=Highest, 4=Lowest
    Description VARCHAR(200),
    Is_Active BIT DEFAULT 1
);

INSERT INTO NC_Grade_Master (NC_Grade_Code, NC_Grade_Name, Severity_Level, Description) VALUES
('MAJOR_NC', 'Major Non-Conformity', 1, 'Serious deficiency requiring immediate action'),
('MINOR_NC', 'Minor Non-Conformity', 2, 'Deficiency that does not pose immediate risk'),
('OBS', 'Observation', 3, 'Area noted for improvement'),
('OFI', 'Opportunity for Improvement', 4, 'Best practice suggestion');

-- PIC Master (Person In Charge)
CREATE TABLE PIC_Master (
    PIC_Code VARCHAR(10) PRIMARY KEY,
    PIC_Name VARCHAR(50) NOT NULL,
    Department VARCHAR(20), -- Deck, Engine
    Sort_Order INT DEFAULT 0
);

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

-- Evidence Type Master
CREATE TABLE Evidence_Type_Master (
    Evidence_Code VARCHAR(20) PRIMARY KEY,
    Evidence_Name VARCHAR(50) NOT NULL,
    Icon VARCHAR(10),
    Is_Active BIT DEFAULT 1
);

INSERT INTO Evidence_Type_Master (Evidence_Code, Evidence_Name, Icon) VALUES
('PHOTO', 'Photographs', '📷'),
('TEST', 'Test Record', '📋'),
('PMS', 'PMS Job', '🔧'),
('CERT', 'Certificate', '📜'),
('TRAIN', 'Training Record', '🎓'),
('OTHER', 'Other', '📁');

-- =====================================================
-- CLC (Comprehensive List of Causes) Library
-- =====================================================

-- CLC Category Master
CREATE TABLE CLC_Category (
    Category_ID INT PRIMARY KEY,
    Category_Code VARCHAR(50) NOT NULL,
    Category_Name VARCHAR(100) NOT NULL,
    Category_Type VARCHAR(50), -- Immediate_Action, Immediate_Condition, Root_Personal, Root_Job
    Parent_ID INT NULL,
    Sort_Order INT DEFAULT 0
);

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

-- CLC Items (Causes)
CREATE TABLE CLC_Item (
    CLC_Code VARCHAR(10) PRIMARY KEY,
    Category_ID INT NOT NULL,
    Item_Name VARCHAR(200) NOT NULL,
    Item_Description VARCHAR(500),
    Sort_Order INT DEFAULT 0,
    Is_Active BIT DEFAULT 1,
    FOREIGN KEY (Category_ID) REFERENCES CLC_Category(Category_ID)
);

-- Sample CLC Items (Category 11 - Following Procedures)
INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
('1-1', 11, 'Violation by individual', 1),
('1-2', 11, 'Violation by group', 2),
('1-3', 11, 'Violation by supervisor', 3),
('1-4', 11, 'Operation equipment without authority', 4),
('1-5', 11, 'Improper position or posture for the task', 5),
('1-6', 11, 'Overexertion of physical capability', 6),
('1-7', 11, 'Work or motion at improper speed', 7),
('1-8', 11, 'Improper lifting', 8),
('1-9', 11, 'Improper loading', 9),
('1-10', 11, 'Shortcuts', 10);

-- (Additional CLC items would be inserted here - full library in clc_library.json)

-- =====================================================
-- CAR MAIN TABLE
-- =====================================================

CREATE TABLE CAR (
    CAR_ID INT IDENTITY(1,1) PRIMARY KEY,
    CAR_No VARCHAR(20) NOT NULL UNIQUE, -- Format: SOURCE-YYYY-NNN
    
    -- Source Identification
    Source VARCHAR(20) NOT NULL, -- PSC, RightShip, Audit
    
    -- Common Fields
    Vessel_ID INT NOT NULL, -- FK to Vessel Master
    Vessel_Name VARCHAR(100) NOT NULL,
    IMO_No VARCHAR(10) NOT NULL,
    Port_Place VARCHAR(100) NOT NULL,
    Inspection_Date DATE NOT NULL,
    Inspector_Auditor VARCHAR(100),
    Report_Ref VARCHAR(50),
    
    -- Finding Details
    Deficiency_Description NVARCHAR(MAX) NOT NULL,
    Root_Cause_Summary NVARCHAR(MAX),
    Corrective_Action NVARCHAR(MAX) NOT NULL,
    Preventive_Action NVARCHAR(MAX) NOT NULL,
    
    -- Target & PIC
    Target_Date DATE NOT NULL,
    PIC VARCHAR(10), -- FK to PIC_Master
    
    -- PSC Specific (NULL for non-PSC)
    PSC_MOU VARCHAR(20), -- FK to MOU_Master
    PSC_Deficiency_Code VARCHAR(10),
    PSC_Action_Code INT, -- FK to PSC_Action_Codes
    
    -- RightShip Specific (NULL for non-RightShip)
    RS_Question_No VARCHAR(20),
    RS_Rating_Impact VARCHAR(20), -- Yes, No, Pending
    
    -- Audit Specific (NULL for non-Audit)
    Audit_Type VARCHAR(20), -- FK to Audit_Type_Master
    Audit_Finding_Type VARCHAR(20), -- FK to NC_Grade_Master
    Audit_Def_No VARCHAR(30), -- Auto: TYPE-YYYY-NNN
    
    -- Office Section
    Office_Comments NVARCHAR(MAX),
    Revised_Target_Date DATE,
    
    -- DPA Section
    DPA_Comments NVARCHAR(MAX),
    DPA_Name VARCHAR(100),
    DPA_Closed_Date DATETIME,
    
    -- Status
    CAR_Status VARCHAR(20) DEFAULT 'Draft', -- Draft, Submitted, Closed_by_DPA, Reopened
    
    -- Verification Section
    Verification_Status VARCHAR(20) DEFAULT 'Pending', -- Pending, Verified, Follow-up
    Verified_By VARCHAR(100),
    Verification_Date DATETIME,
    Verification_Comments NVARCHAR(MAX),
    
    -- Audit Trail
    Created_Date DATETIME DEFAULT GETDATE(),
    Created_By VARCHAR(50),
    Modified_Date DATETIME,
    Modified_By VARCHAR(50),
    
    -- Indexes
    INDEX IX_CAR_Vessel (Vessel_ID),
    INDEX IX_CAR_Source (Source),
    INDEX IX_CAR_Status (CAR_Status),
    INDEX IX_CAR_Target_Date (Target_Date)
);

-- =====================================================
-- CAR RELATED TABLES
-- =====================================================

-- CAR Root Causes (Many-to-Many with CLC)
CREATE TABLE CAR_Root_Causes (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    CAR_ID INT NOT NULL,
    CLC_Code VARCHAR(10), -- FK to CLC_Item (NULL for custom)
    Custom_Cause NVARCHAR(500), -- Free text if not from CLC
    Sort_Order INT DEFAULT 0,
    Created_Date DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (CAR_ID) REFERENCES CAR(CAR_ID),
    FOREIGN KEY (CLC_Code) REFERENCES CLC_Item(CLC_Code)
);

-- CAR Evidence (Many-to-Many with Evidence Types + File Links)
CREATE TABLE CAR_Evidence (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    CAR_ID INT NOT NULL,
    Evidence_Code VARCHAR(20) NOT NULL, -- FK to Evidence_Type_Master
    File_Name VARCHAR(255),
    File_Path VARCHAR(500),
    Description NVARCHAR(500),
    Uploaded_Date DATETIME DEFAULT GETDATE(),
    Uploaded_By VARCHAR(50),
    FOREIGN KEY (CAR_ID) REFERENCES CAR(CAR_ID),
    FOREIGN KEY (Evidence_Code) REFERENCES Evidence_Type_Master(Evidence_Code)
);

-- CAR Status History (Audit Trail)
CREATE TABLE CAR_Status_History (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    CAR_ID INT NOT NULL,
    From_Status VARCHAR(20),
    To_Status VARCHAR(20) NOT NULL,
    Changed_Date DATETIME DEFAULT GETDATE(),
    Changed_By VARCHAR(50),
    Comments NVARCHAR(500),
    FOREIGN KEY (CAR_ID) REFERENCES CAR(CAR_ID)
);

-- =====================================================
-- CAR NUMBER SEQUENCE (For Auto-generation)
-- =====================================================

CREATE TABLE CAR_Sequence (
    Source VARCHAR(20) NOT NULL,
    Year INT NOT NULL,
    Last_Number INT DEFAULT 0,
    PRIMARY KEY (Source, Year)
);

-- =====================================================
-- STORED PROCEDURES
-- =====================================================

-- Generate next CAR number
CREATE OR ALTER PROCEDURE sp_GetNextCARNumber
    @Source VARCHAR(20),
    @CARNo VARCHAR(20) OUTPUT
AS
BEGIN
    DECLARE @Year INT = YEAR(GETDATE());
    DECLARE @NextNum INT;
    
    -- Get or create sequence
    IF NOT EXISTS (SELECT 1 FROM CAR_Sequence WHERE Source = @Source AND Year = @Year)
    BEGIN
        INSERT INTO CAR_Sequence (Source, Year, Last_Number) VALUES (@Source, @Year, 0);
    END
    
    -- Increment and get number
    UPDATE CAR_Sequence 
    SET Last_Number = Last_Number + 1
    WHERE Source = @Source AND Year = @Year;
    
    SELECT @NextNum = Last_Number 
    FROM CAR_Sequence 
    WHERE Source = @Source AND Year = @Year;
    
    -- Format: SOURCE-YYYY-NNN
    SET @CARNo = @Source + '-' + CAST(@Year AS VARCHAR) + '-' + RIGHT('000' + CAST(@NextNum AS VARCHAR), 3);
END;
GO

-- Calculate Target Date based on source
CREATE OR ALTER FUNCTION fn_CalculateTargetDate
(
    @Source VARCHAR(20),
    @InspectionDate DATE,
    @AuditTargetDate DATE = NULL -- Only used for Audit source
)
RETURNS DATE
AS
BEGIN
    DECLARE @TargetDate DATE;
    
    IF @Source = 'Audit' AND @AuditTargetDate IS NOT NULL
        SET @TargetDate = @AuditTargetDate; -- Auditor sets target
    ELSE IF @Source IN ('PSC', 'RightShip')
        SET @TargetDate = DATEADD(DAY, 7, @InspectionDate); -- Default 7 days
    ELSE
        SET @TargetDate = DATEADD(DAY, 14, @InspectionDate); -- Fallback 14 days
    
    RETURN @TargetDate;
END;
GO

-- =====================================================
-- VIEWS
-- =====================================================

-- Active CARs with status
CREATE OR ALTER VIEW vw_CAR_Active AS
SELECT 
    c.CAR_ID,
    c.CAR_No,
    c.Source,
    c.Vessel_Name,
    c.IMO_No,
    c.Port_Place,
    c.Inspection_Date,
    c.Deficiency_Description,
    c.Target_Date,
    c.Revised_Target_Date,
    COALESCE(c.Revised_Target_Date, c.Target_Date) AS Effective_Target_Date,
    c.CAR_Status,
    c.Verification_Status,
    DATEDIFF(DAY, GETDATE(), COALESCE(c.Revised_Target_Date, c.Target_Date)) AS Days_Remaining,
    CASE 
        WHEN DATEDIFF(DAY, GETDATE(), COALESCE(c.Revised_Target_Date, c.Target_Date)) < 0 THEN 'Overdue'
        WHEN DATEDIFF(DAY, GETDATE(), COALESCE(c.Revised_Target_Date, c.Target_Date)) <= 3 THEN 'Critical'
        WHEN DATEDIFF(DAY, GETDATE(), COALESCE(c.Revised_Target_Date, c.Target_Date)) <= 7 THEN 'Warning'
        ELSE 'Normal'
    END AS Urgency_Status,
    -- Root cause count
    (SELECT COUNT(*) FROM CAR_Root_Causes rc WHERE rc.CAR_ID = c.CAR_ID) AS Root_Cause_Count,
    -- Evidence count
    (SELECT COUNT(*) FROM CAR_Evidence ce WHERE ce.CAR_ID = c.CAR_ID) AS Evidence_Count
FROM CAR c
WHERE c.CAR_Status NOT IN ('Closed_by_DPA')
   OR (c.CAR_Status = 'Closed_by_DPA' AND c.Verification_Status = 'Pending');
GO

-- CAR Summary by Vessel
CREATE OR ALTER VIEW vw_CAR_Summary_By_Vessel AS
SELECT 
    Vessel_ID,
    Vessel_Name,
    IMO_No,
    COUNT(*) AS Total_CARs,
    SUM(CASE WHEN Source = 'PSC' THEN 1 ELSE 0 END) AS PSC_CARs,
    SUM(CASE WHEN Source = 'RightShip' THEN 1 ELSE 0 END) AS RightShip_CARs,
    SUM(CASE WHEN Source = 'Audit' THEN 1 ELSE 0 END) AS Audit_CARs,
    SUM(CASE WHEN CAR_Status = 'Draft' THEN 1 ELSE 0 END) AS Draft_Count,
    SUM(CASE WHEN CAR_Status = 'Submitted' THEN 1 ELSE 0 END) AS Submitted_Count,
    SUM(CASE WHEN CAR_Status = 'Closed_by_DPA' THEN 1 ELSE 0 END) AS Closed_Count,
    SUM(CASE WHEN Verification_Status = 'Verified' THEN 1 ELSE 0 END) AS Verified_Count
FROM CAR
GROUP BY Vessel_ID, Vessel_Name, IMO_No;
GO

-- =====================================================
-- PHASE 2: RISQ Question Master (Placeholder)
-- =====================================================

CREATE TABLE RISQ_Section (
    Section_No VARCHAR(10) PRIMARY KEY,
    Section_Name VARCHAR(100) NOT NULL,
    Sort_Order INT DEFAULT 0
);

CREATE TABLE RISQ_Question (
    Question_No VARCHAR(20) PRIMARY KEY,
    Section_No VARCHAR(10) NOT NULL,
    Question_Text NVARCHAR(1000) NOT NULL,
    Question_Type VARCHAR(20), -- (M)andatory, (V)erify, etc.
    Is_Active BIT DEFAULT 1,
    FOREIGN KEY (Section_No) REFERENCES RISQ_Section(Section_No)
);

-- Sample RISQ sections (Phase 2)
INSERT INTO RISQ_Section VALUES
('1', 'General Information', 1),
('2', 'Certification and Personnel Management', 2),
('3', 'Navigation', 3),
('4', 'ISM System', 4),
('5', 'Pollution Prevention and Control', 5),
('6', 'Ship''s Structure', 6),
('7A', 'Fuel Management (Oil Fuel)', 7),
('7B', 'Fuel Management (LNG Fuels)', 8),
('8A', 'Cargo Operation - Solid Bulk Cargo', 9),
('8B', 'Cargo Operation - Bulk Grain', 10),
('8C', 'Cargo Operation - General Cargo', 11),
('8D', 'Cargo Operation - Container Ships', 12),
('8E', 'Cargo Operation - Self-Unloading', 13),
('9A', 'Hatch Cover and Lifting Appliances', 14),
('9B', 'Gantry Cranes', 15),
('10', 'Mooring Operations', 16),
('11', 'Radio and Communication', 17),
('12', 'Security', 18),
('13', 'Machinery Space', 19),
('14', 'General Appearance', 20),
('15', 'Health and Welfare of Seafarers', 21),
('16', 'Ice or Polar Water Operations', 22);

PRINT 'CAR System Database Schema v4.0 created successfully.';
GO
