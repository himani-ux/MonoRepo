# ORB Module

## 1. Scope

ORB is the legacy Online Reporting Bureau module. It remains available through the modern app shell and handles vessel-side operational entry workflows and office review/approved-entry workflows.

## 2. Features

- vessel data and tank lookup
- operation entry creation and editing
- approved, rejected, deleted, and non-deleted entry views
- PDF metadata and PDF archive support
- print status updates
- latest entry date validation
- current vessel selection

## 3. ORB Workflows

### 3.1 Vessel Workflow

1. Select vessel context.
2. Retrieve vessel tanks and ORB code mappings.
3. Enter operation records.
4. Save draft or submit according to the legacy flow.
5. Generate or view PDFs.

### 3.2 Office Workflow

1. Review submitted ORB entries.
2. Approve or reject entries.
3. Maintain archive and print status metadata.
4. Access approved entry screens and reports.

## 4. Frontend Integration

The modern frontend uses:

- `ORBModulePage`
- `LegacyBasicProvider` for vessel users
- `OfficeORBApprovedEntriesPage` for office users

This dual behavior is important:

- vessel users get the legacy ORB app shell
- office users get the approved-entry review screen

## 5. Backend API Families

ORB routes are exposed through the legacy `/api/orb/` and `/api/orb/api/` families.

Core route groups:

- vessel data lookup
- tank lookup
- ORB code lookup
- operation CRUD
- soft delete
- approve/reject actions
- entry retrieval
- page number lookup
- non-deleted / deleted / rejected / approved entry listings
- print status update
- internal IP lookup
- PDF metadata save and listing
- PDF download
- current vessel lookup
- latest entry date lookup

## 6. Data Model Highlights

- `VesselData` is the vessel master record
- `VesselTankDetails` stores tank metadata
- `ORBCodes` stores code/part/description rows
- `OperationEntry` stores the operational log entries
- `CurrentVessel` stores selected vessel context
- `GeneratedPDF` stores generated PDF metadata

## 7. Validation Rules

Important rules in the ORB flow include:

- vessel UUID must be valid
- ORB code must exist
- item number must be numeric when present
- entry date cannot be earlier than the latest existing entry for that vessel

## 8. Integration Points

ORB depends on the same shared vessel data and auth context as PSC and Circular.

Do not treat ORB as an isolated application. It is a legacy module embedded in the same authentication and navigation shell.

