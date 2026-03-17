-- =====================================================
-- PSC Deficiency Code Master Table
-- Based on Paris MOU THETIS Codes (Universal Standard)
-- =====================================================

-- Category Master (Top level: 01, 02, 03, etc.)
CREATE TABLE PSC_Def_Category (
    Category_Code VARCHAR(2) PRIMARY KEY,
    Category_Name VARCHAR(100) NOT NULL,
    Sort_Order INT DEFAULT 0,
    Is_Active BIT DEFAULT 1
);

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

-- Subcategory Master (Second level: 011, 012, 091, 141, etc.)
CREATE TABLE PSC_Def_Subcategory (
    Subcategory_Code VARCHAR(3) PRIMARY KEY,
    Category_Code VARCHAR(2) NOT NULL,
    Subcategory_Name VARCHAR(100) NOT NULL,
    Sort_Order INT DEFAULT 0,
    Is_Active BIT DEFAULT 1,
    FOREIGN KEY (Category_Code) REFERENCES PSC_Def_Category(Category_Code)
);

INSERT INTO PSC_Def_Subcategory (Subcategory_Code, Category_Code, Subcategory_Name, Sort_Order) VALUES
-- 01 Certificates & Documentation
('011', '01', 'Ship Certificate', 1),
('012', '01', 'Crew Certificate', 2),
('013', '01', 'Document', 3),
-- 09 Working and Living Conditions
('091', '09', 'Living conditions', 1),
('092', '09', 'Working Conditions', 2),
-- 14 Pollution Prevention
('141', '14', 'MARPOL Annex I', 1),
('142', '14', 'MARPOL Annex II', 2),
('143', '14', 'MARPOL Annex III', 3),
('144', '14', 'MARPOL Annex IV', 4),
('145', '14', 'MARPOL Annex V', 5),
('146', '14', 'MARPOL Annex VI', 6),
('147', '14', 'Anti Fouling', 7),
-- 18 MLC, 2006
('181', '18', 'Minimum requirements to work on a ship', 1),
('182', '18', 'Conditions of employment', 2),
('183', '18', 'Accommodation, recreational facilities, food and catering', 3),
('184', '18', 'Health protection, medical care, social security', 4);

-- Deficiency Code Master (Full list)
CREATE TABLE PSC_Def_Code (
    Def_Code VARCHAR(5) PRIMARY KEY,
    Category_Code VARCHAR(2) NOT NULL,
    Subcategory_Code VARCHAR(3),
    Def_Name VARCHAR(200) NOT NULL,
    Sort_Order INT DEFAULT 0,
    Is_Active BIT DEFAULT 1,
    FOREIGN KEY (Category_Code) REFERENCES PSC_Def_Category(Category_Code)
);

-- =====================================================
-- 01 - Certificates & Documentation
-- =====================================================

-- 011 - Ship Certificate
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('01101', '01', '011', 'Cargo ship safety equipment (including exemption)', 1),
('01102', '01', '011', 'Cargo ship safety construction (including exempt.)', 2),
('01103', '01', '011', 'Passenger ship safety (including exemption)', 3),
('01104', '01', '011', 'Cargo ship safety radio (including exemption)', 4),
('01105', '01', '011', 'Cargo ship safety (including exemption)', 5),
('01106', '01', '011', 'Document of compliance (DoC/ ISM)', 6),
('01107', '01', '011', 'Safety management certificate (SMC/ ISM)', 7),
('01108', '01', '011', 'Load lines (including Exemption)', 8),
('01109', '01', '011', 'Decision-support system for masters on pass. ships', 9),
('01110', '01', '011', 'Authorization for grain carriage', 10),
('01111', '01', '011', 'Liquefied gases in bulk (CoF/GC Code)', 11),
('01112', '01', '011', 'Liquefied gases in bulk (ICoF/IGC Code)', 12),
('01113', '01', '011', 'Minimum safe manning document', 13),
('01114', '01', '011', 'Dangerous chemicals in bulk (CoF/BCH Code)', 14),
('01115', '01', '011', 'Dangerous chemicals in bulk (ICoF/IBC Code)', 15),
('01116', '01', '011', 'Operational limitations for passenger ships', 16),
('01117', '01', '011', 'International Oil Pollution Prevention (IOPP)', 17),
('01118', '01', '011', 'Pollution prevention by noxious liquid sub in bulk', 18),
('01119', '01', '011', 'International Sewage Pollution Prevention Cert.', 19),
('01120', '01', '011', 'Statement of Compliance CAS', 20),
('01121', '01', '011', 'Interim Statement of Compliance CAS', 21),
('01122', '01', '011', 'International ship security certificate', 22),
('01123', '01', '011', 'Continuous synopsis record', 23),
('01124', '01', '011', 'International Air Pollution Prevention Cert', 24),
('01125', '01', '011', 'Engine International Air Pollution Prevention Cert', 25),
('01126', '01', '011', 'Document of compliance dangerous goods', 26),
('01127', '01', '011', 'Special purpose ship safety', 27),
('01128', '01', '011', 'High speed craft safety and permit to operate', 28),
('01129', '01', '011', 'Mobile offshore drilling unit safety', 29),
('01130', '01', '011', 'INF certificate of fitness', 30),
('01131', '01', '011', 'International AFS certificate', 31),
('01132', '01', '011', 'Tonnage certificate', 32),
('01133', '01', '011', 'Civil liability for oil pollution damage cert.', 33),
('01134', '01', '011', 'Polar ship certificate', 34),
('01135', '01', '011', 'Document for carriage of dangerous goods', 35),
('01136', '01', '011', 'Ballast Water Management Certificate', 36),
('01137', '01', '011', 'Civil liability for Bunker oil pollution damage cert', 37),
('01138', '01', '011', 'International Energy Efficiency Cert', 38),
('01139', '01', '011', 'Maritime Labour Certificate', 39),
('01140', '01', '011', 'Declaration of Maritime Labour Compliance (Part I and II)', 40),
('01199', '01', '011', 'Other (certificates)', 99);

-- 012 - Crew Certificate
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('01201', '01', '012', 'Certificates for master and officers', 1),
('01202', '01', '012', 'Certificate for rating for watchkeeping', 2),
('01203', '01', '012', 'Certificates for radio personnel', 3),
('01204', '01', '012', 'Certificate for personnel on tankers', 4),
('01205', '01', '012', 'Certificate for personnel on fast rescue boats', 5),
('01206', '01', '012', 'Certificate for advanced fire-fighting', 6),
('01209', '01', '012', 'Manning specified by the minimum safe manning doc', 9),
('01210', '01', '012', 'Certificate for medical first aid', 10),
('01211', '01', '012', 'Cert for personnel on survival craft & rescue boat', 11),
('01212', '01', '012', 'Certificate for medical care', 12),
('01213', '01', '012', 'Evidence of basic training', 13),
('01214', '01', '012', 'Endorsement by flagstate', 14),
('01215', '01', '012', 'Application for Endorsement by flagstate', 15),
('01216', '01', '012', 'Certificate for personnel on ships subject to IGF Code', 16),
('01217', '01', '012', 'Ship Security Officer certificate', 17),
('01218', '01', '012', 'Medical certificate', 18),
('01219', '01', '012', 'Training and qualification MLC - Personnel safety training', 19),
('01220', '01', '012', 'Seafarer employment agreement SEA', 20),
('01221', '01', '012', 'Record of employment', 21),
('01222', '01', '012', 'Doc evidence for personnel on passenger ships', 22),
('01223', '01', '012', 'Security awareness training', 23),
('01224', '01', '012', 'Certificate for rating able seafarer deck/engine and electro-technical', 24);

-- 013 - Document
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('01302', '01', '013', 'SAR co-operation plan for pass.ships on fixed trade', 2),
('01303', '01', '013', 'Unattended machinery spaces (UMS) evidence', 3),
('01304', '01', '013', 'Declaration of AFS compliance', 4),
('01305', '01', '013', 'Log-books/compulsory entries', 5),
('01306', '01', '013', 'Shipboard working arrangements', 6),
('01307', '01', '013', 'Maximum hours of work or the minimum hours of rest', 7),
('01308', '01', '013', 'Records of seafarers daily hours of work or rest', 8),
('01309', '01', '013', 'Fire control plan – all', 9),
('01310', '01', '013', 'Signs, indications', 10),
('01311', '01', '013', 'Survey report file', 11),
('01312', '01', '013', 'Thickness measurement report', 12),
('01313', '01', '013', 'Booklet for bulk cargo loading/unloading/stowage', 13),
('01314', '01', '013', 'Shipboard oil pollution emergency plan (SOPEP)', 14),
('01315', '01', '013', 'Oil record book', 15),
('01316', '01', '013', 'Cargo information', 16),
('01317', '01', '013', 'Cargo record book', 17),
('01318', '01', '013', 'P & A manual', 18),
('01319', '01', '013', 'Shipboard mar. poll. Emergency plan (MPEP) for NLS', 19),
('01320', '01', '013', 'Garbage record book', 20),
('01322', '01', '013', 'Conformance Test Report', 22),
('01323', '01', '013', 'Fire safety operational booklet', 23),
('01324', '01', '013', 'Material safety data sheets', 24),
('01325', '01', '013', 'ACM statement of compliance (including exemption)', 25),
('01326', '01', '013', 'Stability Information Booklet', 26),
('01327', '01', '013', 'Energy Efficiency Design Index File', 27),
('01328', '01', '013', 'Ship Energy Efficiency Management plan', 28),
('01329', '01', '013', 'Report of inspection on MLC, 2006', 29),
('01330', '01', '013', 'Procedure for complaint under MLC, 2006', 30),
('01331', '01', '013', 'Collective bargaining agreement', 31),
('01332', '01', '013', 'AIS test report', 32),
('01333', '01', '013', 'Ship specific plans for the recovery of persons from the water', 33),
('01334', '01', '013', 'STS Operation Plan and Records of STS Operations', 34),
('01335', '01', '013', 'Polar Water Operational Manual', 35),
('01336', '01', '013', 'Certificate or documentary evidence of financial security for repatriation', 36),
('01337', '01', '013', 'Certificate or documentary evidence of financial security relating to shipowners liability', 37);

-- =====================================================
-- 02 - Structural condition
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('02101', '02', NULL, 'Closing devices/watertight doors', 1),
('02102', '02', NULL, 'Damage control plan', 2),
('02103', '02', NULL, 'Stability/strength/loading information and instruments', 3),
('02104', '02', NULL, 'Information on the A/A-max ratio (Roro/pass.only)', 4),
('02105', '02', NULL, 'Steering gear', 5),
('02106', '02', NULL, 'Hull damage impairing seaworthiness', 6),
('02107', '02', NULL, 'Ballast, fuel and other tanks', 7),
('02108', '02', NULL, 'Electric equipment in general', 8),
('02109', '02', NULL, 'Permanent means of access', 9),
('02110', '02', NULL, 'Beams, frames, floors-op.damage', 10),
('02111', '02', NULL, 'Beams, frames, floors-corrosion', 11),
('02112', '02', NULL, 'Hull - corrosion', 12),
('02113', '02', NULL, 'Hull - cracking', 13),
('02114', '02', NULL, 'Bulkhead – corrosion', 14),
('02115', '02', NULL, 'Bulkheads - operational damage', 15),
('02116', '02', NULL, 'Bulkheads – cracking', 16),
('02117', '02', NULL, 'Decks – corrosion', 17),
('02118', '02', NULL, 'Decks – cracking', 18),
('02119', '02', NULL, 'Enhanced survey programme (ESP)', 19),
('02120', '02', NULL, 'Marking of IMO number', 20),
('02121', '02', NULL, 'Cargo area segregation', 21),
('02122', '02', NULL, 'Openings to cargo area, doors, scuttles', 22),
('02123', '02', NULL, 'Wheelhouse door, -window', 23),
('02124', '02', NULL, 'Cargo pump room', 24),
('02125', '02', NULL, 'Spaces in cargo areas', 25),
('02126', '02', NULL, 'Cargo tank vent system', 26),
('02127', '02', NULL, 'Safe access to tanker bows', 27),
('02128', '02', NULL, 'Bulk carriers additional safety measures', 28),
('02129', '02', NULL, 'Bulkhead strength', 29),
('02130', '02', NULL, 'Triangle mark', 30),
('02132', '02', NULL, 'Water level detectors on single hold cargo ships', 32),
('02133', '02', NULL, 'Asbestos containing materials', 33),
('02134', '02', NULL, 'Loading/Ballast condition (Tanker)', 34),
('02199', '02', NULL, 'Other (Structural condition)', 99);

-- =====================================================
-- 03 - Water/Weathertight condition
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('03101', '03', NULL, 'Overloading', 1),
('03102', '03', NULL, 'Freeboard marks', 2),
('03103', '03', NULL, 'Railing, gangway, walkway and means for safe passage', 3),
('03104', '03', NULL, 'Cargo and other hatchways', 4),
('03105', '03', NULL, 'Covers (hatchway-, portable-, tarpaulins, etc.)', 5),
('03106', '03', NULL, 'Windows, side scuttles and deadlights', 6),
('03107', '03', NULL, 'Doors', 7),
('03108', '03', NULL, 'Ventilators, air pipes, casings', 8),
('03109', '03', NULL, 'Machinery space openings', 9),
('03110', '03', NULL, 'Manholes / flush scuttles', 10),
('03111', '03', NULL, 'Cargo ports and other similar openings', 11),
('03112', '03', NULL, 'Scuppers, inlets and discharges', 12),
('03113', '03', NULL, 'Bulwarks and freeing ports', 13),
('03114', '03', NULL, 'Stowage incl. uprights, lashing, etc (timber)', 14),
('03199', '03', NULL, 'Other (load lines)', 99);

-- =====================================================
-- 04 - Emergency Systems
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('04101', '04', NULL, 'Public address system', 1),
('04102', '04', NULL, 'Emergency fire pump and its pipes', 2),
('04103', '04', NULL, 'Emergency lighting, batteries and switches', 3),
('04104', '04', NULL, 'Low level lighting in corridors', 4),
('04105', '04', NULL, 'Location of emergency installations', 5),
('04106', '04', NULL, 'Emergency steering position communications/ compass reading', 6),
('04107', '04', NULL, 'Emergency towing arrangements and procedures', 7),
('04108', '04', NULL, 'Muster list', 8),
('04109', '04', NULL, 'Fire drills', 9),
('04110', '04', NULL, 'Abandon ship drills', 10),
('04111', '04', NULL, 'Damage control plan', 11),
('04112', '04', NULL, 'Shipboard Marine Pollution emergency operations', 12),
('04113', '04', NULL, 'Water level indicator', 13),
('04114', '04', NULL, 'Emergency source of power - Emergency generator', 14),
('04115', '04', NULL, 'Safe areas', 15),
('04116', '04', NULL, 'Means of communication between safety centre and other control stations', 16),
('04117', '04', NULL, 'Functionality of Safety Systems', 17),
('04118', '04', NULL, 'Enclosed space entry and rescue drills', 18);

-- =====================================================
-- 05 - Radio communication
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('05101', '05', NULL, 'Distress messages: obligations and procedures', 1),
('05102', '05', NULL, 'Functional requirements', 2),
('05103', '05', NULL, 'Main installation', 3),
('05104', '05', NULL, 'MF radio installation', 4),
('05105', '05', NULL, 'MF/HF radio installation', 5),
('05106', '05', NULL, 'INMARSAT ship earth station', 6),
('05107', '05', NULL, 'Maintenance / duplication of equipment', 7),
('05108', '05', NULL, 'Performance standards for radio equipment', 8),
('05109', '05', NULL, 'VHF radio installation', 9),
('05110', '05', NULL, 'Facilities for reception of marine safety information', 10),
('05111', '05', NULL, 'Satellite EPIRB 406MHz / 1.6 GHz', 11),
('05112', '05', NULL, 'VHF EPIRB', 12),
('05113', '05', NULL, 'SART/AIS-SART', 13),
('05114', '05', NULL, 'Reserve source of energy', 14),
('05115', '05', NULL, 'Radio log (diary)', 15),
('05116', '05', NULL, 'Operation/maintenance', 16),
('05118', '05', NULL, 'Operation of GMDSS equipment', 18),
('05199', '05', NULL, 'Other (radio communication)', 99);

-- =====================================================
-- 06 - Cargo operations including equipment
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('06101', '06', NULL, 'Cargo securing manual', 1),
('06102', '06', NULL, 'Grain', 2),
('06103', '06', NULL, 'Other cargo - timber -deck/construction', 3),
('06104', '06', NULL, 'Lashing material', 4),
('06105', '06', NULL, 'Atmosphere testing instruments', 5),
('06106', '06', NULL, 'Cargo transfer - Tankers', 6),
('06107', '06', NULL, 'Cargo operation', 7),
('06108', '06', NULL, 'Cargo density declaration', 8),
('06199', '06', NULL, 'Other (cargo)', 99);

-- =====================================================
-- 07 - Fire safety
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('07101', '07', NULL, 'Fire prevention structural integrity', 1),
('07102', '07', NULL, 'Inert gas system', 2),
('07103', '07', NULL, 'Division – decks, bulkheads and penetrations', 3),
('07104', '07', NULL, 'Main vertical zone', 4),
('07105', '07', NULL, 'Fire doors/openings in fire-resisting divisions', 5),
('07106', '07', NULL, 'Fire detection', 6),
('07108', '07', NULL, 'Ready availability of fire fighting equipment', 8),
('07109', '07', NULL, 'Fixed fire extinguishing installation', 9),
('07110', '07', NULL, 'Fire fighting equipment and appliances', 10),
('07111', '07', NULL, 'Personal equipment', 11),
('07112', '07', NULL, 'Emergency escape breathing Device and disposition', 12),
('07113', '07', NULL, 'Fire pumps and its pipes', 13),
('07114', '07', NULL, 'Means of control (opening, pumps) Machinery spaces', 14),
('07115', '07', NULL, 'Fire-dampers', 15),
('07116', '07', NULL, 'Ventilation', 16),
('07117', '07', NULL, 'Jacketed high pressure lines and oil leakage alarm', 17),
('07118', '07', NULL, 'International shore-connection', 18),
('07120', '07', NULL, 'Means of escape', 20),
('07121', '07', NULL, 'Crew alarm', 21),
('07122', '07', NULL, 'Fire control plan', 22),
('07123', '07', NULL, 'Operation of Fire protection systems', 23),
('07124', '07', NULL, 'Maintenance of Fire protection systems', 24),
('07125', '07', NULL, 'Evaluation of crew performance (fire drills)', 25),
('07199', '07', NULL, 'Other (fire safety)', 99);

-- =====================================================
-- 08 - Alarms
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('08101', '08', NULL, 'General alarm', 1),
('08102', '08', NULL, 'Emergency signal', 2),
('08103', '08', NULL, 'Fire alarm', 3),
('08104', '08', NULL, 'Steering-gear alarm', 4),
('08105', '08', NULL, 'Engineers alarm', 5),
('08106', '08', NULL, 'Inert gas alarm', 6),
('08107', '08', NULL, 'Machinery controls alarm', 7),
('08108', '08', NULL, 'UMS-alarms', 8),
('08109', '08', NULL, 'Boiler-alarm', 9),
('08110', '08', NULL, 'Closing watertight doors alarm', 10),
('08199', '08', NULL, 'Other (alarms)', 99);

-- =====================================================
-- 09 - Working and Living Conditions
-- =====================================================

-- 091 - Living conditions
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('09101', '09', '091', 'Minimum age', 1),
('09102', '09', '091', 'Dirty, parasites', 2),
('09103', '09', '091', 'Ventilation (Accommodation)', 3),
('09104', '09', '091', 'Heating', 4),
('09105', '09', '091', 'Noise', 5),
('09106', '09', '091', 'Sanitary facilities', 6),
('09107', '09', '091', 'Drainage', 7),
('09108', '09', '091', 'Lighting (Accommodation)', 8),
('09109', '09', '091', 'Pipes, wires (insulation)', 9),
('09110', '09', '091', 'Electrical devices', 10),
('09111', '09', '091', 'Sickbay', 11),
('09112', '09', '091', 'Medical equipment', 12),
('09113', '09', '091', 'Access/structure', 13),
('09114', '09', '091', 'Sleeping room', 14),
('09115', '09', '091', 'No direct openings into sleeping rooms cargo/mach.', 15),
('09116', '09', '091', 'Furnishings', 16),
('09117', '09', '091', 'Berth dimensions, etc.', 17),
('09118', '09', '091', 'Clear head', 18),
('09119', '09', '091', 'Messroom (location)', 19),
('09120', '09', '091', 'Oil skin locker', 20),
('09121', '09', '091', 'Laundry', 21),
('09122', '09', '091', 'Record of inspection (Accommodation)', 22),
('09124', '09', '091', 'Galley, handlingroom (maintenance)', 24),
('09127', '09', '091', 'Cleanliness', 27),
('09128', '09', '091', 'Provisions quantity', 28),
('09129', '09', '091', 'Provisions quality', 29),
('09130', '09', '091', 'Water, pipes, tanks', 30),
('09131', '09', '091', 'Cold room', 31),
('09132', '09', '091', 'Cold room temperature', 32),
('09133', '09', '091', 'Cold room cleanliness', 33),
('09134', '09', '091', 'Food personal hygiene', 34),
('09135', '09', '091', 'Food temperature', 35),
('09136', '09', '091', 'Food segregation', 36),
('09137', '09', '091', 'Record of inspection', 37),
('09198', '09', '091', 'Other (crew and accommodation)', 98),
('09199', '09', '091', 'Other (food)', 99);

-- 092 - Working Conditions
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('09201', '09', '092', 'Ventilation (Working spaces)', 1),
('09202', '09', '092', 'Heating', 2),
('09203', '09', '092', 'Lighting (Working spaces)', 3),
('09204', '09', '092', 'Safe means of access', 4),
('09205', '09', '092', 'Safe means of access shore – ship', 5),
('09206', '09', '092', 'Safe means of access deck - hold/tank, etc.', 6),
('09207', '09', '092', 'Obstruction/slipping, etc.', 7),
('09208', '09', '092', 'Protection machinery', 8),
('09209', '09', '092', 'Electrical', 9),
('09210', '09', '092', 'Machinery', 10),
('09211', '09', '092', 'Steam pipes and pressure pipes', 11),
('09212', '09', '092', 'Danger areas', 12),
('09213', '09', '092', 'Gas instruments', 13),
('09214', '09', '092', 'Emergency cleaning devices', 14),
('09216', '09', '092', 'Personal equipment', 16),
('09217', '09', '092', 'Warning notices', 17),
('09218', '09', '092', 'Protection machines/parts', 18),
('09219', '09', '092', 'Pipes, wires (insulation)', 19),
('09220', '09', '092', 'Structural features (ship)', 20),
('09221', '09', '092', 'Entry dangerous spaces', 21),
('09223', '09', '092', 'Gangway, accommodation-ladder', 23),
('09224', '09', '092', 'Stowage of cargo', 24),
('09225', '09', '092', 'Loading and unloading equipment', 25),
('09226', '09', '092', 'Holds and tanks safety', 26),
('09227', '09', '092', 'Ropes and wires', 27),
('09228', '09', '092', 'Anchoring devices', 28),
('09229', '09', '092', 'Winches and capstans', 29),
('09230', '09', '092', 'Adequate lighting - mooring arrangements', 30),
('09232', '09', '092', 'Cleanliness of engine room', 32),
('09233', '09', '092', 'Guards / fencing around dangerous machinery parts', 33),
('09234', '09', '092', 'Night working for seafarer under the age of 18', 34),
('09235', '09', '092', 'Fitness for duty – work and rest hours', 35),
('09236', '09', '092', 'Legal documentation on work and rest hours', 36),
('09237', '09', '092', 'Fitness for duty – intoxication', 37),
('09297', '09', '092', 'Other (working space ILO)', 97),
('09298', '09', '092', 'Other (accident prevention)', 98),
('09299', '09', '092', 'Other (mooring)', 99);

-- =====================================================
-- 10 - Safety of Navigation
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('10101', '10', NULL, 'Pilot ladders and hoist/pilot transfer arrangements', 1),
('10102', '10', NULL, 'Type approval equipment', 2),
('10103', '10', NULL, 'Radar', 3),
('10104', '10', NULL, 'Gyro compass', 4),
('10105', '10', NULL, 'Magnetic compass', 5),
('10106', '10', NULL, 'Compass correction log', 6),
('10107', '10', NULL, 'Automatic radar plotting aid (ARPA)', 7),
('10109', '10', NULL, 'Lights, shapes, sound-signals', 9),
('10110', '10', NULL, 'Signalling lamp', 10),
('10111', '10', NULL, 'Charts', 11),
('10112', '10', NULL, 'Electronic charts (ECDIS)', 12),
('10113', '10', NULL, 'Automatic Identification System (AIS)', 13),
('10114', '10', NULL, 'Voyage Data Recorder (VDR) / Simplified VDR (SVDR)', 14),
('10115', '10', NULL, 'GNSS receiver/terrestrial radio navigation system', 15),
('10116', '10', NULL, 'Nautical publications', 16),
('10117', '10', NULL, 'Echo sounder', 17),
('10118', '10', NULL, 'Speed and distance indicator', 18),
('10119', '10', NULL, 'Rudder angle indicator', 19),
('10120', '10', NULL, 'Revolution counter', 20),
('10121', '10', NULL, 'Variable pitch indicator', 21),
('10122', '10', NULL, 'Rate-of-turn indicator', 22),
('10123', '10', NULL, 'International code of signals- SOLAS', 23),
('10124', '10', NULL, 'Life-saving signals', 24),
('10125', '10', NULL, 'Use of the automatic pilot', 25),
('10126', '10', NULL, 'Records of drills and steering gear tests', 26),
('10127', '10', NULL, 'Voyage or passage plan', 27),
('10128', '10', NULL, 'Navigation bridge visibility', 28),
('10129', '10', NULL, 'Navigation records', 29),
('10132', '10', NULL, 'Communication - SOLAS Chapter V', 32),
('10133', '10', NULL, 'Bridge operation', 33),
('10134', '10', NULL, 'HSC operation', 34),
('10135', '10', NULL, 'Monitoring of voyage or passage plan', 35),
('10136', '10', NULL, 'Establishment of working language on board', 36),
('10137', '10', NULL, 'Long-Range Identification and Tracking system (LRIT)', 37),
('10138', '10', NULL, 'Bridge Navigational Watch Alarm System (BNWAS)', 38),
('10199', '10', NULL, 'Other (navigation)', 99);

-- =====================================================
-- 11 - Life saving appliances
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('11101', '11', NULL, 'Lifeboats', 1),
('11102', '11', NULL, 'Lifeboat inventory', 2),
('11103', '11', NULL, 'Stowage and provision of lifeboats', 3),
('11104', '11', NULL, 'Rescue boats', 4),
('11105', '11', NULL, 'Rescue boat inventory', 5),
('11106', '11', NULL, 'Fast rescue boats', 6),
('11107', '11', NULL, 'Stowage of rescue boats', 7),
('11108', '11', NULL, 'Inflatable liferafts', 8),
('11109', '11', NULL, 'Rigid liferafts', 9),
('11110', '11', NULL, 'Stowage of liferafts', 10),
('11111', '11', NULL, 'Marine evacuation system', 11),
('11112', '11', NULL, 'Launching arrangements for survival craft', 12),
('11113', '11', NULL, 'Launching arrangements for rescue boats', 13),
('11114', '11', NULL, 'Helicopter landing and pick-up area', 14),
('11115', '11', NULL, 'Means of rescue', 15),
('11116', '11', NULL, 'Distress flares', 16),
('11117', '11', NULL, 'Lifebuoys incl. provision and disposition', 17),
('11118', '11', NULL, 'Lifejackets incl. provision and disposition', 18),
('11119', '11', NULL, 'Immersion suits', 19),
('11120', '11', NULL, 'Anti-exposure suits', 20),
('11121', '11', NULL, 'Thermal Protective Aids', 21),
('11122', '11', NULL, 'Radio life-saving appliances', 22),
('11123', '11', NULL, 'Emergency equipment for 2-way comm.', 23),
('11124', '11', NULL, 'Embarkation arrangement survival craft', 24),
('11125', '11', NULL, 'Embarkation arrangements rescue boats', 25),
('11126', '11', NULL, 'Means of recovery of life saving appliances', 26),
('11127', '11', NULL, 'Buoyant apparatus', 27),
('11128', '11', NULL, 'Line-throwing appliance', 28),
('11129', '11', NULL, 'Operational readiness of lifesaving appliances', 29),
('11130', '11', NULL, 'Evaluation, testing and approval', 30),
('11131', '11', NULL, 'On board training and instructions', 31),
('11132', '11', NULL, 'Maintenance and inspections', 32),
('11134', '11', NULL, 'Operation of Life Saving Appliances', 34),
('11135', '11', NULL, 'Maintenance of Life Saving Appliances', 35),
('11199', '11', NULL, 'Other (life saving)', 99);

-- =====================================================
-- 12 - Dangerous Goods
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('12101', '12', NULL, 'Stowage/segregation/packaging of dangerous goods', 1),
('12102', '12', NULL, 'Dangerous liquid chemicals in bulk', 2),
('12103', '12', NULL, 'Liquefied gases in bulk', 3),
('12104', '12', NULL, 'Dangerous goods code', 4),
('12105', '12', NULL, 'Temperature control', 5),
('12106', '12', NULL, 'Instrumentation', 6),
('12107', '12', NULL, 'Fire protection cargo deck area', 7),
('12108', '12', NULL, 'Personal protection', 8),
('12109', '12', NULL, 'Special requirements', 9),
('12110', '12', NULL, 'Tank entry', 10),
('12112', '12', NULL, 'Dangerous goods or harmful substances in pack. Form', 12),
('12199', '12', NULL, 'Other (tankers)', 99);

-- =====================================================
-- 13 - Propulsion and auxiliary machinery
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('13101', '13', NULL, 'Propulsion main engine', 1),
('13102', '13', NULL, 'Auxiliary engine', 2),
('13103', '13', NULL, 'Gauges, thermometers etc.', 3),
('13104', '13', NULL, 'Bilge pumping arrangements', 4),
('13105', '13', NULL, 'UMS-ship', 5),
('13106', '13', NULL, 'Insulation wetted through (oil)', 6),
('13108', '13', NULL, 'Operation of machinery', 8),
('13199', '13', NULL, 'Other (machinery)', 99);

-- =====================================================
-- 14 - Pollution Prevention
-- =====================================================

-- 141 - MARPOL Annex I
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('14101', '14', '141', 'Control of discharge of oil', 1),
('14102', '14', '141', 'Retention of oil on board', 2),
('14103', '14', '141', 'Segregation of oil and water ballast', 3),
('14104', '14', '141', 'Oil filtering equipment', 4),
('14105', '14', '141', 'Pumping, piping and discharge arrangements', 5),
('14106', '14', '141', 'Pump room bottom protection', 6),
('14107', '14', '141', 'Oil discharge monitoring and control system', 7),
('14108', '14', '141', '15 PPM alarm arrangements', 8),
('14109', '14', '141', 'Oil / water interface detector', 9),
('14110', '14', '141', 'Standard discharge connection', 10),
('14111', '14', '141', 'SBT, CBT, COW', 11),
('14112', '14', '141', 'COW operations and equipment manual', 12),
('14113', '14', '141', 'Double hull construction', 13),
('14114', '14', '141', 'Hydrostatically balanced loading', 14),
('14115', '14', '141', 'Condition Assessment Scheme', 15),
('14116', '14', '141', 'Pollution report - MARPOL Annex I', 16),
('14117', '14', '141', 'Ship type designation', 17),
('14119', '14', '141', 'Oil and oily mixtures from machinery spaces', 19),
('14120', '14', '141', 'Loading, unloading & cleaning procedures cargo spaces of tankers', 20),
('14121', '14', '141', 'Suspected of discharge violation', 21),
('14199', '14', '141', 'Other (MARPOL Annex I)', 99);

-- 142 - MARPOL Annex II
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('14201', '14', '142', 'Efficient stripping', 1),
('14202', '14', '142', 'Residue discharge systems', 2),
('14203', '14', '142', 'Tank washing equipment', 3),
('14204', '14', '142', 'Prohibited discharge of NLS slops', 4),
('14205', '14', '142', 'Cargo heating systems - cat. Y substances', 5),
('14206', '14', '142', 'Ventilation procedures / equipment', 6),
('14207', '14', '142', 'Pollution report - MARPOL Annex II', 7),
('14208', '14', '142', 'Ship type designation', 8),
('14299', '14', '142', 'Other (MARPOL Annex II)', 99);

-- 143 - MARPOL Annex III
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('14301', '14', '143', 'Packaging', 1),
('14302', '14', '143', 'Marking and labelling', 2),
('14303', '14', '143', 'Documentation (MARPOL Annex III)', 3),
('14304', '14', '143', 'Stowage', 4),
('14399', '14', '143', 'Other (MARPOL - Annex III)', 99);

-- 144 - MARPOL Annex IV
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('14402', '14', '144', 'Sewage treatment plan', 2),
('14403', '14', '144', 'Sewage comminuting and disinfecting system', 3),
('14404', '14', '144', 'Sewage discharge connection', 4),
('14499', '14', '144', 'Other (MARPOL Annex IV)', 99);

-- 145 - MARPOL Annex V
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('14501', '14', '145', 'Garbage', 1),
('14502', '14', '145', 'Placards', 2),
('14503', '14', '145', 'Garbage management plan', 3),
('14599', '14', '145', 'Other (MARPOL Annex V)', 99);

-- 146 - MARPOL Annex VI
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('14601', '14', '146', 'Technical Files and if applicable, monitoring manual', 1),
('14602', '14', '146', 'Record book engine parameters', 2),
('14603', '14', '146', 'Approved doc exhaust gas cleaning system', 3),
('14604', '14', '146', 'Bunker delivery notes', 4),
('14605', '14', '146', 'Type approval certificate of incinerator', 5),
('14606', '14', '146', 'Diesel engine air pollution control', 6),
('14607', '14', '146', 'Quality of fuel oil', 7),
('14608', '14', '146', 'Incinerator incl. operations and operating manual', 8),
('14609', '14', '146', 'Volatile Organic compounds in tankers', 9),
('14610', '14', '146', 'Operational proc. for engines or equipment', 10),
('14611', '14', '146', 'Ozone depleting substances', 11),
('14613', '14', '146', 'Approved method', 13),
('14614', '14', '146', 'Sulphur oxides', 14),
('14699', '14', '146', 'Other (MARPOL ANNEX VI)', 99);

-- 147 - Anti Fouling
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('14701', '14', '147', 'AFS supporting documentation', 1),
('14702', '14', '147', 'Logbook entries referring AFS', 2),
('14703', '14', '147', 'Paint condition', 3),
('14799', '14', '147', 'Other (AFS)', 99);

-- =====================================================
-- 15 - ISM
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('15150', '15', NULL, 'ISM', 1);

-- Additional ISM codes (commonly used)
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('15109', '15', NULL, 'ISM - SMS implementation', 2),
('15199', '15', NULL, 'Other (ISM)', 99);

-- =====================================================
-- 16 - ISPS
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('16101', '16', NULL, 'Security related defects', 1),
('16102', '16', NULL, 'Ship security alert system', 2),
('16103', '16', NULL, 'Ship security plan', 3),
('16104', '16', NULL, 'Ship security officer', 4),
('16105', '16', NULL, 'Access control to ship', 5),
('16106', '16', NULL, 'Security drills', 6),
('16199', '16', NULL, 'Other (maritime security)', 99);

-- =====================================================
-- 18 - MLC, 2006
-- =====================================================

-- 181 - Minimum requirements to work on a ship
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('18101', '18', '181', 'Minimum age', 1),
('18102', '18', '181', 'Night working', 2),
('18103', '18', '181', 'Medical fitness', 3),
('18104', '18', '181', 'Recruitment and placement service', 4),
('18199', '18', '181', 'Other (Minimum requirements)', 99);

-- 182 - Conditions of employment
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('18201', '18', '182', 'Fitness for duty - work and rest hours', 1),
('18202', '18', '182', 'Legal documentation on work and rest hours', 2),
('18203', '18', '182', 'Wages', 3),
('18204', '18', '182', 'Calculation and payment', 4),
('18205', '18', '182', 'Measures to ensure transmission to seafarers family', 5),
('18299', '18', '182', 'Other (Conditions of employment)', 99);

-- 183 - Accommodation, recreational facilities, food and catering
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('18301', '18', '183', 'Noise, vibration and other ambient factors', 1),
('18302', '18', '183', 'Sanitary Facilities', 2),
('18303', '18', '183', 'Drainage', 3),
('18304', '18', '183', 'Lighting (Accommodation)', 4),
('18305', '18', '183', 'Hospital accommodation (Sickbay)', 5),
('18306', '18', '183', 'Sleeping room, additional spaces', 6),
('18307', '18', '183', 'Direct openings into sleeping rooms cargo/mach.', 7),
('18308', '18', '183', 'Furnishings', 8),
('18309', '18', '183', 'Berth dimensions, etc.', 9),
('18310', '18', '183', 'Minimum headroom', 10),
('18311', '18', '183', 'Mess room and recreational facilities', 11),
('18312', '18', '183', 'Galley, handlingroom (maintenance)', 12),
('18313', '18', '183', 'Cleanliness', 13),
('18314', '18', '183', 'Provisions quantity', 14),
('18315', '18', '183', 'Provisions quality and nutritional value', 15),
('18316', '18', '183', 'Water, pipes, tanks', 16),
('18317', '18', '183', 'Food personal hygiene', 17),
('18318', '18', '183', 'Food temperature', 18),
('18319', '18', '183', 'Food segregation', 19),
('18320', '18', '183', 'Record of inspection (food and catering)', 20),
('18321', '18', '183', 'Heating, air conditioning and ventilation', 21),
('18322', '18', '183', 'Insulation', 22),
('18323', '18', '183', 'Office', 23),
('18324', '18', '183', 'Cold room, cold room cleanliness, cold room temperature', 24),
('18325', '18', '183', 'Training and qualification of ships cook', 25),
('18326', '18', '183', 'Laundry, Adequate Locker', 26),
('18327', '18', '183', 'Ventilation (Working spaces)', 27),
('18328', '18', '183', 'Record of inspection', 28),
('18399', '18', '183', 'Other (Accommodation, recreational facilities)', 99);

-- 184 - Health protection, medical care, social security
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('18401', '18', '184', 'Medical Equipment, medical chest, medical guide', 1),
('18402', '18', '184', 'Access to on shore medical doctor or dentist', 2),
('18403', '18', '184', 'Standard medical report form', 3),
('18404', '18', '184', 'Medical doctor or person in charge of medical care', 4),
('18405', '18', '184', 'Medical advice by radio or satellite', 5),
('18406', '18', '184', 'Medical care onboard or ashore free of charge', 6),
('18407', '18', '184', 'Lighting (Working spaces)', 7),
('18408', '18', '184', 'Electrical', 8),
('18409', '18', '184', 'Dangerous areas', 9),
('18410', '18', '184', 'Gas instruments', 10),
('18411', '18', '184', 'Emergency cleaning devices', 11),
('18412', '18', '184', 'Personal equipment', 12),
('18413', '18', '184', 'Warning notices', 13),
('18414', '18', '184', 'Protection machines/parts', 14),
('18415', '18', '184', 'Entry dangerous spaces', 15),
('18416', '18', '184', 'Ropes and wires', 16),
('18417', '18', '184', 'Anchoring devices', 17),
('18418', '18', '184', 'Winches & capstans', 18),
('18419', '18', '184', 'Adequate lighting - mooring arrangements', 19),
('18420', '18', '184', 'Cleanliness of engine room', 20),
('18421', '18', '184', 'Guards - fencing around dangerous machinery parts', 21),
('18422', '18', '184', 'Asbestos fibres', 22),
('18423', '18', '184', 'Preventative information', 23),
('18424', '18', '184', 'Steam pipes, pressure pipes, wires (insulation)', 24),
('18425', '18', '184', 'Access / structural features (ship)', 25),
('18426', '18', '184', 'Exposure to harmful levels of ambient factors', 26),
('18427', '18', '184', 'Ships occupational safety and health policies and programmes', 27),
('18428', '18', '184', 'On board programme for prevention of occupational injuries and diseases', 28),
('18429', '18', '184', 'Procedure for inspection, reporting and correcting unsafe conditions', 29),
('18430', '18', '184', 'Ships safety committee', 30),
('18431', '18', '184', 'Investigation after accident', 31),
('18432', '18', '184', 'Risk evaluation, training and instruction to seafarers', 32),
('18499', '18', '184', 'Other (Health protection, medical care)', 99);

-- =====================================================
-- 99 - Other
-- =====================================================
INSERT INTO PSC_Def_Code (Def_Code, Category_Code, Subcategory_Code, Def_Name, Sort_Order) VALUES
('99101', '99', NULL, 'Other safety in general', 1),
('99102', '99', NULL, 'Other (SOLAS operational)', 2),
('99103', '99', NULL, 'Other (MARPOL operational)', 3);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================
CREATE INDEX IX_PSC_Def_Code_Category ON PSC_Def_Code(Category_Code);
CREATE INDEX IX_PSC_Def_Code_Subcategory ON PSC_Def_Code(Subcategory_Code);

-- =====================================================
-- VIEW: Deficiency Code with full hierarchy
-- =====================================================
CREATE OR ALTER VIEW vw_PSC_Def_Code_Full AS
SELECT 
    d.Def_Code,
    d.Def_Name,
    c.Category_Code,
    c.Category_Name,
    s.Subcategory_Code,
    s.Subcategory_Name,
    -- Display format: "07115 - Fire-dampers (Fire safety)"
    d.Def_Code + ' - ' + d.Def_Name + ' (' + c.Category_Name + ')' AS Display_Text,
    -- Short format: "07115 - Fire-dampers"
    d.Def_Code + ' - ' + d.Def_Name AS Short_Text
FROM PSC_Def_Code d
JOIN PSC_Def_Category c ON d.Category_Code = c.Category_Code
LEFT JOIN PSC_Def_Subcategory s ON d.Subcategory_Code = s.Subcategory_Code
WHERE d.Is_Active = 1
ORDER BY d.Def_Code;
GO

-- =====================================================
-- STORED PROCEDURE: Search deficiency codes
-- =====================================================
CREATE OR ALTER PROCEDURE sp_Search_PSC_Def_Code
    @SearchTerm VARCHAR(100) = NULL,
    @CategoryCode VARCHAR(2) = NULL
AS
BEGIN
    SELECT 
        d.Def_Code,
        d.Def_Name,
        c.Category_Name,
        s.Subcategory_Name,
        d.Def_Code + ' - ' + d.Def_Name AS Display_Text
    FROM PSC_Def_Code d
    JOIN PSC_Def_Category c ON d.Category_Code = c.Category_Code
    LEFT JOIN PSC_Def_Subcategory s ON d.Subcategory_Code = s.Subcategory_Code
    WHERE d.Is_Active = 1
      AND (@CategoryCode IS NULL OR d.Category_Code = @CategoryCode)
      AND (@SearchTerm IS NULL 
           OR d.Def_Code LIKE '%' + @SearchTerm + '%'
           OR d.Def_Name LIKE '%' + @SearchTerm + '%')
    ORDER BY d.Def_Code;
END;
GO

PRINT 'PSC Deficiency Code Master Table created with ' + 
      CAST((SELECT COUNT(*) FROM PSC_Def_Code) AS VARCHAR) + ' codes.';
GO
