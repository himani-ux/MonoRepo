# Notifications Module

## Path

- `psc-backend/apps/notifications/`

## Purpose

This module provides in-app notifications for PSC workflows and a scheduled overdue-action check. It is a cross-cutting module that turns workflow events into user-visible alerts for crew and office users.

## Owns

- Notification records and read state
- Notification list and mark-read APIs
- Helper functions for creating workflow notifications
- Daily overdue-action notification command

## Main Files

- `models.py`: notification table and type enums
- `views.py`: list, mark-read, mark-all-read
- `signals.py`: helper functions and CAR-created hook
- `management/commands/check_overdue_actions.py`: scheduled overdue scanner

## Workflow

1. Business modules call helper functions such as `notify_car_submitted` or `notify_def_assigned`.
2. Notifications are inserted with recipient type, recipient ID, vessel scope, and related entity.
3. Frontend polls notification APIs and lets users mark items read.
4. A scheduled command scans corrective actions for warning and overdue cases.

## Dependencies

- `apps.car`, `apps.inspection`, and `apps.sync` as event producers
- `apps.accounts` unmanaged tables for recipient resolution
- Frontend notification center and unread badge components

## Notes

- This module is intentionally data-driven; it does not own business state, only alert fan-out.
- Recipient resolution for vessel masters and office users is one of the more fragile parts because it crosses unmanaged legacy tables.
