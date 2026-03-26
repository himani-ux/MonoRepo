# Legacy ORB Module

## Path

- `psc-backend/modules/orb/orb/`

## Purpose

This is a legacy Oil Record Book module that remains mounted inside the repository and frontend shell. It manages vessel operations, ORB code forms, entry approval/rejection, and PDF archive behavior.

## Owns

- Vessel and tank lookup APIs for ORB forms
- Operation entry CRUD
- Approval and rejection endpoints
- Deleted, rejected, approved, and active entry list endpoints
- PDF metadata persistence and PDF download/archive endpoints
- Current vessel selection helpers

## Main Files

- `models.py`: ORB-specific vessel, operation, and generated PDF tables
- `views.py`: large function-based and DRF viewset surface
- `serializers.py`: ORB data serializers
- `pdf_generator.py`, `validators.py`, `utils.py`
- `urls.py`: mounted under `/api/orb/`

## Workflow

1. Vessel user enters ORB operations through code-specific forms.
2. Entries are stored and later approved or rejected.
3. The module exposes filtered entry views for active, deleted, rejected, and approved sets.
4. Approved entries can be packaged into generated PDFs and later downloaded from the archive.

## Dependencies

- Frontend legacy ORB pages and Redux store
- Shared vessel and crew tables
- Report/PDF helper utilities inside the module

## Notes

- This code is separate from the modern PSC workflow and should be treated as a legacy bounded context.
- Security and maintainability expectations should be higher here because the module still exposes many unauthenticated endpoints.
