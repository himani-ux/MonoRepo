# System Design

## 1. Architecture Summary

VIMS is a hybrid monolith. The PSC inspection platform is the primary application, and the Circular and ORB modules are integrated as legacy-compatible sub-systems inside the same authenticated shell.

The design goals are:

- one login for all modules
- one role model for access control
- one server-side source of truth for workflows
- offline support for vessel users
- compatibility with legacy Circular and ORB behaviors

## 2. Major Layers

### 2.1 Presentation Layer

- React 18 application served by Vite
- TanStack Query for server state
- Zustand for client state
- legacy Redux bridge for Circular and ORB
- mobile-first shell with header, sidebar, and bottom navigation

### 2.2 API Layer

- Django REST Framework
- custom JWT authentication backend
- role-based and vessel-based permission classes
- module-specific view classes for inspections, CARs, sync, notifications, reports, and legacy modules

### 2.3 Data Layer

- Microsoft SQL Server
- shared unmanaged operational tables
- PSC-owned tables for inspections, CARs, sync, and notifications
- legacy Circular/ORB tables retained for compatibility

### 2.4 File Layer

- media uploads for reports and company logo
- structured upload paths for evidence and inspection reports
- generated PDFs and Excel exports returned as downloads

## 3. Module Interaction

```text
               +-------------------------------+
               |         Auth / JWT            |
               +---------------+---------------+
                               |
          +--------------------+--------------------+
          |                    |                    |
          v                    v                    v
   +--------------+     +--------------+     +--------------+
   | Inspection   |     | Circular     |     | ORB          |
   | Core module   |     | Legacy module|     | Legacy module|
   +------+-------+     +------+-------+     +------+-------+
          |                    |                    |
          v                    v                    v
   +---------------------------------------------------------+
   |                 Shared SQL Server Database              |
   |  masters, inspections, CAR, sync, notification, legacy  |
   +---------------------------------------------------------+
```

## 4. Inspection-Centric Data Flow

### 4.1 Inspection Creation Flow

1. User opens the inspection form.
2. Frontend loads master lookups and validates permissions.
3. Backend creates the inspection record in draft state.
4. User uploads the report if required.
5. User adds deficiencies.
6. Each deficiency auto-creates a linked CAR.

### 4.2 Inspection Review Flow

1. Vessel master or office user submits the inspection.
2. Backend verifies report presence and CAR completeness.
3. PIC reviewer adds a comment and moves the inspection to reviewed.
4. DPA closes the inspection after review.

### 4.3 CAR Workflow Flow

1. Deficiency creation produces a CAR in the allotted state.
2. Vessel users fill root cause, CLC selections, actions, evidence, and PV details.
3. The CAR is submitted into the office review flow.
4. PIC review and rework are handled through explicit transition endpoints.
5. DPA closes the CAR when work is complete.

### 4.4 Sync Flow

1. Vessel changes are recorded locally first.
2. Sync push sends batched events and attachment metadata.
3. Server validates versions and detects conflicts.
4. Sync pull returns server-side deltas and updates local stores.
5. Office/DPA users resolve conflicts when necessary.

## 5. Design Decisions

### 5.1 Custom Authentication Instead of Django Auth User

The system authenticates against existing vessel and office tables instead of the Django `auth_user` table. This matches the real enterprise data model and avoids duplicating identity records.

### 5.2 Explicit Workflow Endpoints

Workflow state changes are not hidden inside generic update calls. The code uses explicit endpoints such as:

- `submit`
- `pic-review`
- `dpa-close`
- `workflow`
- `allocate`

This makes approval logic auditable and easier to test.

### 5.3 Unmanaged Legacy Tables

Legacy tables are modeled as unmanaged Django models. That prevents accidental schema drift and keeps the repository aligned with the shared database.

### 5.4 Query-First Frontend

The frontend uses TanStack Query for all server interactions so cache invalidation is explicit and workflow transitions stay predictable.

### 5.5 Offline-First Vessel UX

Vessel workflows need to function with intermittent connectivity. The app therefore stores local state and sync queues before reconciling with the server.

### 5.6 Legacy Module Encapsulation

Circular and ORB are kept behind a legacy provider and route boundary. That isolates their older Redux-based assumptions from the modern PSC shell.

## 6. Scalability Considerations

### 6.1 Database

- Indexes are present on vessel, status, date, and entity identifiers.
- Query filters are scoped by vessel where possible.
- Audit and activity history are append-only patterns.

### 6.2 API

- Pagination is built into list endpoints.
- Large export endpoints stream generated files rather than returning raw JSON.
- Sync endpoints batch events and separate attachment payloads.

### 6.3 Frontend

- Page components are lazy-loaded.
- Query staleness is tuned by data volatility.
- Legacy modules are loaded only when the user navigates to them.

### 6.4 File Handling

- Upload paths are deterministic and grouped by vessel and entity type.
- Media files are stored outside code.
- Export files are regenerated on demand, not persisted permanently unless required by a legacy module.

## 7. Data Flow Diagram

```text
User Action
   |
   v
React Page / Component
   |
   +--> TanStack Query / Zustand / Local Queue
   |
   v
Axios Client with JWT
   |
   v
Django API View / Serializer / Permission
   |
   +--> SQL Server Read/Write
   |
   +--> File system upload/export
   |
   v
JSON / PDF / XLSX response
   |
   v
UI cache update and navigation
```

## 8. Boundary Rules

- PSC features must not depend on legacy Circular UI state.
- Legacy modules must not bypass the PSC JWT auth store.
- Office vessel visibility must always flow through the vessel-access helper.
- Reports and exports must honor role-based access and vessel scoping.

