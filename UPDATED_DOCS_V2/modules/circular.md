# Circular Module

## 1. Scope

Circular is a legacy integrated module for circular-style notifications, approvals, reminders, acknowledgments, and PDF handling. The frontend keeps the legacy screens inside the modern authenticated shell, and the backend exposes legacy route families under `/api/circular/`.

## 2. Key Concepts

- office-side creation and publishing
- ship-side viewing and acknowledgment
- draft versus approved versus superseded states
- crew delivery tracking
- PDF generation and viewing
- form/process-based permissions from `form_ids` and `process_ids`

## 3. KSM Library

The module uses a KSM-style library pattern for circular content grouping.

Typical legacy constructs:

- circular master data
- categories and subcategories
- priority and department mapping
- crew delivery records
- reminders and acknowledgment history

## 4. Circular Lifecycle

1. Office creates a draft circular.
2. Draft is linked to vessel, department, and rank/crew recipients.
3. Circular is published or superseded.
4. Vessel-side users receive the item.
5. Crew acknowledge or read the notification.
6. Office can resend reminders and inspect delivery/ack state.

## 5. Frontend Integration

The frontend wraps the module with:

- `CircularModulePage`
- `LegacyBasicProvider`
- `CircularRoutes`

This keeps the old Redux-based screen stack working while sharing the modern auth state.

## 6. Backend API Families

### 6.1 Office-side

Document and lookup endpoints include:

- role and mapping lookups
- users
- document types
- departments
- priorities
- subcategories
- second subcategories
- vessels
- ranks

Notification workflow endpoints include:

- create notification
- list submitted items
- item detail
- single notification lookup
- delete
- supersede
- status update
- email dispatch
- link ranks
- crew delivery status
- send reminder

Draft endpoints include:

- list drafts
- user drafts
- update by SR number
- delete by SR number or ID
- get draft by SR number

Approval and user view endpoints include:

- approved notifications
- approved CSV export
- user notifications

Crew endpoints include:

- crews by department
- crews by department and vessel

### 6.2 Ship-side

Ship-side endpoints include:

- master notifications for a crew member
- non-master notifications by rank
- PDF URL lookup
- acknowledgment/read ack
- crew reminders
- crew list
- crew status
- PDF download

## 7. UI Layout

Circular screens generally follow the legacy layout:

- header
- sidebar
- content cards or tables
- PDF viewer panel
- footer actions

The module preserves the older workflow vocabulary and navigation patterns, so it should not be redesigned to look like PSC screens.

## 8. Integration With Inspection

Circular and Inspection share a common auth and vessel context, but their business logic is separate.

Important integration points:

- both need the same JWT identity
- both rely on vessel and crew resolution data
- both use shared master data such as vessels and ranks
- both may surface notifications in the global header

## 9. Common Pitfalls

- confusing Circular acknowledgement state with PSC inspection status
- bypassing the legacy provider and breaking the Redux bridge
- mixing legacy `ship` user type with modern `vessel` user type without normalization
- assuming Circular permissions are process-based only; some screens are also rank-based

