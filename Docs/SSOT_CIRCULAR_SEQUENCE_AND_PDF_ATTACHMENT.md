# Circular SSOT: Sequence Scope and PDF Attachments

Last updated: April 22, 2026

## Purpose

This document is the single source of truth (SSOT) for:

1. Circular SR number sequence rules
2. Circular PDF attachment rules

Code changes in backend or frontend must follow this document.

## Sequence Scope SSOT

### Rule

- Serial sequence is **global per document type only**.
- Sequence **must not depend on department**.
- Sequence **must not reset by year**.
- SR display format remains:
  - `KSM/{type}/{department}/{year}-{serial}`

### Example

- If latest `Alert` serial is `0129` in `2026`, next `Alert` in `2027` is `0130`.
- Department can change (`SEQ`, `Technical`, etc.), serial still continues for same type.

### Backend Enforcement

- File:
  - `psc-backend/modules/circular/circular_office/views.py`
- Function:
  - `_generate_unique_circular_sr_no(...)`
- Locking:
  - Type-level application lock (`type-seq:{type}`) is used to prevent concurrent duplicate serials.

## PDF Attachment SSOT

### Rule

- Allowed file type: **PDF only**.
- Maximum attachments per request: **3 files**.
- Applies to circular create and draft update flows.
- Backend is final authority; frontend is validation convenience.

### Behavior

- If user uploads non-PDF files:
  - Reject those files with validation message.
- If user selects more than 3 PDFs:
  - Accept only up to 3; extra files are rejected with message.
- Uploaded PDFs are merged into a single attachment stream after generated cover pages.

### Backend Enforcement

- File:
  - `psc-backend/modules/circular/circular_office/views.py`
- Constants/helpers:
  - `MAX_CIRCULAR_ATTACHMENT_FILES = 3`
  - `_extract_uploaded_pdf_attachments_from_request_files(...)`
  - `_store_circular_generated_pdf(...)`

### Frontend UX Requirement

- Both pages must expose the same user actions:
  - add files
  - remove single file
  - clear all selected files
- Files:
  - `psc-frontend/src/legacy/vims-basic/pages/circular/Officeuser.jsx`
  - `psc-frontend/src/legacy/vims-basic/pages/circular/Admin.jsx`

## Change Control

If rules change, update this document first, then update backend and frontend code in the same task.

