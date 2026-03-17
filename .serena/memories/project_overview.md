# VIMS Inspection - Project Overview

## Purpose
A comprehensive maritime inspection management system for vessels that handles:
- **Port State Control (PSC)** inspections
- **RightShip (RS)** inspections  
- **Audit** inspections

The system manages the complete lifecycle from inspection recording through deficiency tracking, Corrective Action Reports (CAR), and final DPA (Designated Person Ashore) closure.

## Target Users
| Role | Description |
|------|-------------|
| Vessel Master | Create inspections, submit CARs, register follow-ups |
| Crew (Action Owner) | View assigned actions, upload evidence |
| Office (PIC/SSQE/Supt) | Review, accept, edit-assist, request rework |
| DPA | Final closure authority |
| Physical Verifier | Record on-board verification visits |

## Key Business Rules (Non-Negotiable)
1. **DefCode Always Visible**: Every screen showing deficiencies must prominently display the DefCode
2. **1:1 CAR Relationship**: One deficiency creates exactly one CAR, automatically via trigger
3. **Evidence Requirements**: Submission requires ≥1 BEFORE + ≥1 AFTER evidence
4. **Root Cause Minimum**: root_cause_summary must be ≥50 characters
5. **Rework Reason Minimum**: rework reason must be ≥20 characters
6. **File Limits**: Max 3MB per file, PDF/JPG/JPEG only
7. **Storage Limit**: 150MB offline cache, warn at <10MB remaining
8. **Offline-First**: PWA with full offline support and conflict resolution

## State Machines
**Inspection States:** DRAFT → SUBMITTED → PIC_REVIEWED → DPA_CLOSED

**CAR States:** DRAFT → SUBMITTED → PIC_ACCEPTED → DPA_CLOSED
- REWORK_REQUESTED can occur from SUBMITTED or PIC_ACCEPTED
- REWORK_REQUESTED immediately transitions to DRAFT

## Documentation Structure
All canonical documentation is in `Docs/` folder:
- `PRD.md` - Feature requirements with IDs (FEAT-*)
- `APP_FLOW.md` - Screen layouts, navigation, user journeys
- `TECH_STACK.md` - Exact versions, dependencies (LOCKED)
- `DESIGN_SYSTEM.md` - Colors, spacing, typography tokens
- `FRONTEND_GUIDELINES.md` - Component architecture, patterns
- `BACKEND_STRUCTURE.md` - Database schema, API contracts
- `VALIDATION_RULES.md` - Field validation rules
- `IMPLEMENTATION_PLAN.md` - Build sequence (phases/steps)
- `CLAUDE.md` - AI agent operating instructions
- `LESSONS.md` - Captured mistakes to avoid
