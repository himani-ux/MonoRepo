# Notifications Module

## Path

- `psc-backend/apps/notifications/`

## Purpose

This module provides in-app notifications for PSC workflows and a scheduled overdue-action check. It is a cross-cutting module that turns workflow events into user-visible alerts for crew and office users, including the newer circular workflow events now shown in the same notification tab as inspection/CAR alerts.

## Owns

- Notification records and read state
- Notification list and mark-read APIs
- Helper functions for creating workflow notifications
- Daily overdue-action notification command
- Circular workflow notifications without introducing circular-specific notification tables

## Main Files

- `models.py`: notification table and type enums
- `views.py`: list, mark-read, mark-all-read
- `signals.py`: helper functions and CAR-created hook
- `management/commands/check_overdue_actions.py`: scheduled overdue scanner
- `tests.py`: notification trigger and recipient-resolution coverage, including circular events

## Workflow

1. Business modules call helper functions such as `notify_car_submitted`, `notify_def_assigned`, or the circular helpers in `signals.py`.
2. Notifications are inserted with recipient type, recipient ID, vessel scope, and related entity.
3. Frontend polls notification APIs and lets users mark items read.
4. A scheduled command scans corrective actions for warning and overdue cases.

## Circular Workflow Coverage

Circular workflow notifications are implemented on top of the existing `psc_notification` table. No new notification table was created for circulars.

Current circular notification types in `models.py`:

- `CIRCULAR_CREATED`
- `CIRCULAR_PENDING_APPROVAL`
- `CIRCULAR_APPROVED`
- `CIRCULAR_REJECTED`

Current circular helper functions in `signals.py`:

- `notify_circular_created`
- `notify_circular_pending_approval`
- `notify_circular_approved`
- `notify_circular_rejected`
- `notify_circular_distribution`

Current trigger sources:

- `modules/circular/circular_office/views.py`
  - `create_notification`
  - `update_notification_status`
  - `link_notification_to_ranks`

Current recipient rules:

- draft save -> creator
- submit for approval -> creator and office reviewer roles
- approve/reject -> creator
- final crew distribution -> unique crew recipients

## Dependencies

- `apps.car`, `apps.inspection`, and `apps.sync` as event producers
- `modules/circular/circular_office` as the circular event producer
- `apps.accounts` unmanaged tables for recipient resolution
- Frontend notification center and unread badge components

## Notes

- This module is intentionally data-driven; it does not own business state, only alert fan-out.
- Recipient resolution for vessel masters and office users is one of the more fragile parts because it crosses unmanaged legacy tables.
- Circular notifications intentionally reuse the shared notification center, so the frontend click behavior for circular items is implemented in the generic notification components rather than in a circular-only notification page.
