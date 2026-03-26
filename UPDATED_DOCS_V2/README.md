# VIMS Unified System

VIMS, the Vehicle Inspection Management System, is a unified full-stack application for managing three integrated business domains:

1. Inspection module, which is the core/base workflow for PSC, RightShip, and Audit inspections
2. Circular module, which preserves the legacy circular notification and approval workflows
3. ORB module, which preserves the legacy Online Reporting Bureau workflows

The current repository contains the PSC/VIMS inspection platform as the primary application, with Circular and ORB embedded as legacy-integrated modules through the same authenticated shell.

## What The System Does

- Authenticates vessel and office users through a custom JWT flow
- Manages inspection creation, submission, review, and close-out
- Auto-creates CARs when deficiencies are added
- Supports corrective action workflows, evidence uploads, and physical verification
- Provides dashboard analytics, notifications, offline sync, and PDF/Excel export
- Preserves the existing Circular and ORB workflows through the integrated legacy app shell

## Feature Summary

### Inspection

- Inspection list, create, detail, edit, delete
- Inspection report upload
- Inspection submit, PIC review, and DPA close
- Deficiency add/update/allocate/workflow transition
- Same-inspection follow-up wizard
- Excel export for deficiencies and bulk CAR PDF export

### Circular

- Legacy notification and circular delivery workflows
- Office-side draft, approved, and supersede flows
- Ship-side read/acknowledge and crew delivery tracking
- PDF viewing and circular report generation

### ORB

- Legacy operational record entry workflows
- Vessel, tank, and ORB code lookup APIs
- Approved/rejected/deleted entry views
- PDF metadata storage and report generation

## Technology Stack

### Backend

- Django 5.2.7
- Django REST Framework 3.14
- SimpleJWT 5.3.1
- mssql-django 1.6
- pyodbc 5.1.0
- ReportLab, PyPDF2, openpyxl, Pillow

### Frontend

- React 18
- TypeScript 5
- Vite 5
- TanStack Query 5
- Zustand
- Redux Toolkit and redux-persist for legacy module bridging
- Tailwind CSS 3
- Radix UI primitives
- Recharts
- Workbox PWA support

### Database

- Microsoft SQL Server
- Shared unmanaged legacy tables plus PSC-owned tables

## System Capabilities

- Role-based access for vessel, office, DPA, PIC, SSQE, SUPT, and physical verifier flows
- JWT-based authentication with token refresh and logout blacklisting
- Vessel-scoped and office-scoped data visibility
- Offline-first queueing for vessel workflows
- Conflict detection and resolution during sync
- PDF and Excel export pipelines
- Company logo upload for report branding
- Global reviewer resolution through mapped roles and profiles

## High-Level Architecture

```text
                         +-----------------------------+
                         |       React Frontend        |
                         |  Vite + TanStack Query +    |
                         |  Zustand + Legacy Modules   |
                         +--------------+--------------+
                                        |
                                        | HTTPS / JSON / multipart
                                        v
                         +--------------+--------------+
                         |        Django API            |
                         |  DRF + SimpleJWT + RBAC      |
                         |  PSC + Circular + ORB APIs   |
                         +--------------+--------------+
                                        |
                    +-------------------+-------------------+
                    |                                       |
                    v                                       v
       +--------------------------+          +------------------------------+
       | Microsoft SQL Server      |          | File Storage / Media         |
       | Shared tables + PSC tables|          | uploads, reports, companylogo|
       +--------------------------+          +------------------------------+
```

## Core Documentation

- [Implementation Plan](implementation_plan.md)
- [System Design](architecture/system_design.md)
- [Database Schema](architecture/database_schema.md)
- [Backend Overview](backend/overview.md)
- [API Documentation](backend/api_documentation.md)
- [Frontend Overview](frontend/overview.md)
- [Screen Inventory](frontend/screens.md)
- [Inspection Module](modules/inspection.md)
- [Circular Module](modules/circular.md)
- [ORB Module](modules/orb.md)
- [Shared Utilities](shared/utils_and_services.md)
- [Deployment Guide](deployment/deployment_guide.md)
- [Troubleshooting](troubleshooting.md)

