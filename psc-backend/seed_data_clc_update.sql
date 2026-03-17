-- =====================================================
-- CLC Items Seed Data — All Categories
-- Based on ILCI Loss Causation Model
-- Run: sqlcmd -S .\SQLEXPRESS -d ksm_cms_dev -i seed_data_clc_update.sql
-- =====================================================

USE ksm_cms_dev;
GO

-- ─────────────────────────────────────────────────────
-- Immediate Causes - Actions
-- ─────────────────────────────────────────────────────

-- Category 12: Use of Tools or Equipment (code prefix "2-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = '2-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('2-1', 12, 'Use of defective equipment (aware)', 1),
    ('2-2', 12, 'Improper use of equipment', 2),
    ('2-3', 12, 'Use of equipment in unsafe manner', 3),
    ('2-4', 12, 'Using equipment beyond its capacity', 4),
    ('2-5', 12, 'Use of tools/equipment for wrong purpose', 5),
    ('2-6', 12, 'Failure to secure/lock out equipment', 6),
    ('2-7', 12, 'Operation of equipment at improper speed', 7),
    ('2-8', 12, 'Removal/bypass of safety devices', 8);
    PRINT 'Inserted CLC items for Category 12 (Use of Tools or Equipment)';
END

-- Category 13: Use of Protective Methods (code prefix "3-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = '3-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('3-1', 13, 'Lack of knowledge of hazards present', 1),
    ('3-2', 13, 'Failure to use available PPE', 2),
    ('3-3', 13, 'Improper use of PPE', 3),
    ('3-4', 13, 'Failure to warn co-workers of hazard', 4),
    ('3-5', 13, 'Failure to isolate/secure work area', 5),
    ('3-6', 13, 'Use of defective PPE', 6);
    PRINT 'Inserted CLC items for Category 13 (Use of Protective Methods)';
END

-- Category 14: Inattention / Lack of Awareness (code prefix "4-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = '4-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('4-1', 14, 'Failure to observe surroundings', 1),
    ('4-2', 14, 'Distracted by other concerns', 2),
    ('4-3', 14, 'Failure to identify changing conditions', 3),
    ('4-4', 14, 'Complacency due to routine task', 4),
    ('4-5', 14, 'Failure to communicate intentions', 5),
    ('4-6', 14, 'Working while fatigued', 6);
    PRINT 'Inserted CLC items for Category 14 (Inattention / Lack of Awareness)';
END

-- ─────────────────────────────────────────────────────
-- Immediate Causes - Conditions
-- ─────────────────────────────────────────────────────

-- Category 21: Protective Systems (code prefix "5-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = '5-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('5-1', 21, 'Missing or inadequate guards/barriers', 1),
    ('5-2', 21, 'Defective safety devices', 2),
    ('5-3', 21, 'Missing warning signs/alarms', 3),
    ('5-4', 21, 'Inadequate fire protection systems', 4),
    ('5-5', 21, 'Insufficient ventilation/exhaust systems', 5);
    PRINT 'Inserted CLC items for Category 21 (Protective Systems)';
END

-- Category 22: Tools, Equipment & Vehicles (code prefix "6-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = '6-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('6-1', 22, 'Defective tools or equipment', 1),
    ('6-2', 22, 'Equipment not fit for purpose', 2),
    ('6-3', 22, 'Poorly maintained machinery', 3),
    ('6-4', 22, 'Inadequate material handling equipment', 4),
    ('6-5', 22, 'Improper equipment configuration', 5);
    PRINT 'Inserted CLC items for Category 22 (Tools, Equipment & Vehicles)';
END

-- Category 23: Work Exposures (code prefix "7-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = '7-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('7-1', 23, 'Exposure to harmful substances', 1),
    ('7-2', 23, 'Exposure to extreme temperatures', 2),
    ('7-3', 23, 'Excessive noise levels', 3),
    ('7-4', 23, 'Exposure to radiation', 4),
    ('7-5', 23, 'Exposure to confined spaces without controls', 5);
    PRINT 'Inserted CLC items for Category 23 (Work Exposures)';
END

-- Category 24: Work Place Environment / Layout (code prefix "8-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = '8-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('8-1', 24, 'Poor housekeeping/cluttered work area', 1),
    ('8-2', 24, 'Inadequate lighting', 2),
    ('8-3', 24, 'Slippery/uneven walking surfaces', 3),
    ('8-4', 24, 'Congested work space', 4),
    ('8-5', 24, 'Inadequate access/egress routes', 5);
    PRINT 'Inserted CLC items for Category 24 (Work Place Environment / Layout)';
END

-- ─────────────────────────────────────────────────────
-- Root Causes - Personal Factors
-- ─────────────────────────────────────────────────────

-- Category 31: Physical Capability (code prefix "P1-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'P1-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('P1-1', 31, 'Physical limitations preventing safe task performance', 1),
    ('P1-2', 31, 'Insufficient strength or endurance', 2),
    ('P1-3', 31, 'Restricted range of movement', 3),
    ('P1-4', 31, 'Impaired vision or hearing', 4);
    PRINT 'Inserted CLC items for Category 31 (Physical Capability)';
END

-- Category 32: Physical Condition (code prefix "P2-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'P2-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('P2-1', 32, 'Illness or pre-existing medical condition', 1),
    ('P2-2', 32, 'Fatigue from overwork or insufficient rest', 2),
    ('P2-3', 32, 'Effects of medication or substances', 3),
    ('P2-4', 32, 'Impaired by injury', 4);
    PRINT 'Inserted CLC items for Category 32 (Physical Condition)';
END

-- Category 33: Mental State (code prefix "P3-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'P3-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('P3-1', 33, 'Fear or anxiety affecting performance', 1),
    ('P3-2', 33, 'Emotional distress', 2),
    ('P3-3', 33, 'Depression or low morale', 3),
    ('P3-4', 33, 'Overconfidence', 4);
    PRINT 'Inserted CLC items for Category 33 (Mental State)';
END

-- Category 34: Mental Stress (code prefix "P4-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'P4-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('P4-1', 34, 'Mental overload (task complexity)', 1),
    ('P4-2', 34, 'Conflicting demands or priorities', 2),
    ('P4-3', 34, 'Time pressure leading to errors', 3),
    ('P4-4', 34, 'Boredom or monotonous tasks', 4);
    PRINT 'Inserted CLC items for Category 34 (Mental Stress)';
END

-- Category 35: Behavior (code prefix "P5-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'P5-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('P5-1', 35, 'Risk-taking behavior', 1),
    ('P5-2', 35, 'Disregard for safety rules', 2),
    ('P5-3', 35, 'Attempting to save time/effort', 3),
    ('P5-4', 35, 'Peer pressure to take shortcuts', 4);
    PRINT 'Inserted CLC items for Category 35 (Behavior)';
END

-- Category 36: Skill Level (code prefix "P6-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'P6-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('P6-1', 36, 'Insufficient training for task', 1),
    ('P6-2', 36, 'Inadequate practice or experience', 2),
    ('P6-3', 36, 'New to the task or environment', 3),
    ('P6-4', 36, 'Skills not maintained through refresher training', 4);
    PRINT 'Inserted CLC items for Category 36 (Skill Level)';
END

-- ─────────────────────────────────────────────────────
-- Root Causes - Job Factors
-- ─────────────────────────────────────────────────────

-- Category 41: Training / Knowledge Transfer (code prefix "J7-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J7-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J7-1', 41, 'Inadequate training program', 1),
    ('J7-2', 41, 'Lack of familiarization training', 2),
    ('J7-3', 41, 'No competency verification after training', 3),
    ('J7-4', 41, 'Poor knowledge transfer during handover', 4);
    PRINT 'Inserted CLC items for Category 41 (Training / Knowledge Transfer)';
END

-- Category 42: Management / Supervision / Leadership (code prefix "J8-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J8-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J8-1', 42, 'Inadequate supervision of work', 1),
    ('J8-2', 42, 'Failure to enforce safety rules', 2),
    ('J8-3', 42, 'Poor safety leadership', 3),
    ('J8-4', 42, 'Lack of management commitment to safety', 4);
    PRINT 'Inserted CLC items for Category 42 (Management / Supervision / Leadership)';
END

-- Category 43: Contractor Selection & Oversight (code prefix "J9-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J9-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J9-1', 43, 'Inadequate contractor vetting process', 1),
    ('J9-2', 43, 'Insufficient oversight of contractor work', 2),
    ('J9-3', 43, 'Poor communication with contractor personnel', 3);
    PRINT 'Inserted CLC items for Category 43 (Contractor Selection & Oversight)';
END

-- Category 44: Engineering / Design (code prefix "J10-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J10-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J10-1', 44, 'Inadequate design for safe operation', 1),
    ('J10-2', 44, 'Failure to consider human factors in design', 2),
    ('J10-3', 44, 'Inadequate ergonomic design', 3);
    PRINT 'Inserted CLC items for Category 44 (Engineering / Design)';
END

-- Category 45: Work Planning (code prefix "J11-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J11-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J11-1', 45, 'Inadequate job/task planning', 1),
    ('J11-2', 45, 'Failure to identify hazards in planning', 2),
    ('J11-3', 45, 'Insufficient resource allocation', 3),
    ('J11-4', 45, 'Poor permit-to-work implementation', 4);
    PRINT 'Inserted CLC items for Category 45 (Work Planning)';
END

-- Category 46: Purchasing, Material Handling & Control (code prefix "J12-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J12-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J12-1', 46, 'Procurement of substandard materials/equipment', 1),
    ('J12-2', 46, 'Improper storage of materials', 2),
    ('J12-3', 46, 'Inadequate material handling procedures', 3);
    PRINT 'Inserted CLC items for Category 46 (Purchasing, Material Handling & Control)';
END

-- Category 47: Tools & Equipment (code prefix "J13-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J13-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J13-1', 47, 'Inadequate maintenance program', 1),
    ('J13-2', 47, 'Failure to replace worn/defective equipment', 2),
    ('J13-3', 47, 'Insufficient spare parts availability', 3);
    PRINT 'Inserted CLC items for Category 47 (Tools & Equipment)';
END

-- Category 48: Work Rules / Policies / Standards / Procedures (code prefix "J14-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J14-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J14-1', 48, 'Outdated or missing procedures', 1),
    ('J14-2', 48, 'Procedures not practical for actual conditions', 2),
    ('J14-3', 48, 'Conflicting procedures or standards', 3),
    ('J14-4', 48, 'Inadequate risk assessment procedures', 4);
    PRINT 'Inserted CLC items for Category 48 (Work Rules / Policies / Standards / Procedures)';
END

-- Category 49: Communication (code prefix "J15-")
IF NOT EXISTS (SELECT 1 FROM CLC_Item WHERE CLC_Code = 'J15-1')
BEGIN
    INSERT INTO CLC_Item (CLC_Code, Category_ID, Item_Name, Sort_Order) VALUES
    ('J15-1', 49, 'Inadequate communication of safety information', 1),
    ('J15-2', 49, 'Language barriers', 2),
    ('J15-3', 49, 'Poor shift handover communication', 3);
    PRINT 'Inserted CLC items for Category 49 (Communication)';
END

PRINT '';
PRINT 'CLC items seed update complete!';
PRINT 'Total new items: ~82 across 22 categories (10 existing in Category 11)';
GO
