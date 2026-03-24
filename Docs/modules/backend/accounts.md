# Accounts Module

## Path

- `psc-backend/apps/accounts/`

## Purpose

This module is the identity and authorization layer for the PSC application. It does not use Django's built-in user model as the system of record. Instead it reconstructs authenticated users from existing SQL Server tables and emits JWT tokens with the claims the frontend and backend need.

## Owns

- Login, token refresh, logout, `me`
- Vessel and office user lookup
- Role normalization (`VESSEL_MASTER`, `OFFICE_PIC`, `DPA`, etc.)
- Form/process permission lists from `msc_profiles`
- Crew list lookup by vessel
- Company logo upload status for PDF generation

## Main Files

- `backends.py`: vessel and office authentication, JWT user reconstruction
- `models.py`: unmanaged mappings to external identity tables plus PSC role constants
- `permissions.py`: reusable role/process permission classes
- `views.py`: auth endpoints and crew/logo APIs
- `serializers.py`: token and user payload contract

## Workflow

1. `POST /api/psc/auth/login/` accepts username and password.
2. `PSCAuthenticationBackend` tries vessel auth first, then office auth.
3. The backend enriches the user with vessel, rank, role, and process metadata.
4. `PSCRefreshToken` writes those values into JWT claims.
5. Frontend auth store persists tokens and later calls `GET /api/psc/auth/me/` to rebuild session state.
6. Other modules use `request.user.role`, `request.user.user_type`, and `request.user.process_ids` for authorization.

## Dependencies

- External SQL Server tables: `Ship_UsersLogin`, `HRM501`, `users`, role mapping tables
- `rest_framework_simplejwt`
- Downstream consumers: every backend app and the frontend auth bootstrap

## Notes

- This module is the seam between modern PSC code and existing enterprise identity tables.
- It carries legacy compatibility fields such as `legacy_user_type`, `UserName`, and `work_side` because the embedded legacy frontend still expects them.
