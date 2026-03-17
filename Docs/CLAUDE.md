# CLAUDE.md — AI Agent Instructions
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.0 | **Date:** 2026-02-03

---

## Project Overview

This is a maritime inspection management system handling Port State Control (PSC), RightShip (RS), and Audit inspections. The system manages the complete lifecycle from inspection recording through deficiency tracking, Corrective Action Reports (CAR), and final DPA closure.

**Primary Users:** Vessel Masters, Crew, Office (PIC/SSQE/Supt), DPA, Physical Verifiers

**Key Invariants:**
- DefCode (deficiency code) must be visible on ALL screens showing deficiencies
- 1 Deficiency = 1 CAR (auto-created, no manual CAR creation)
- Evidence requires at least 1 BEFORE + 1 AFTER photo for CAR submission
- Offline-first with conflict resolution

---

## Tech Stack Summary

**Backend:**
- Python 3.12.4
- Django 5.2.7
- Django REST Framework 3.14.0
- SQL Server 2019 (mssql-django 1.4)
- JWT Auth (djangorestframework-simplejwt 5.3.1)

**Frontend:**
- React 18.3.1
- TypeScript 5.4.5
- Vite 5.4.0
- Tailwind CSS 3.4.7
- TanStack Query 5.51.0
- Zustand 4.5.4
- shadcn/ui components
- Workbox 7.1.0 (PWA/offline)

> **Note:** This is a summary only. TECH_STACK.md is the canonical source for all versions. If any version here disagrees with TECH_STACK.md, TECH_STACK.md wins.

**Database Schema:** See BACKEND_STRUCTURE.md Part 2

---

## Canonical Documentation

These documents are LAW. Reference them for every decision.

| Document | Purpose | When to Reference |
|----------|---------|-------------------|
| PRD.md | Feature requirements with IDs (FEAT-*) | Before implementing any feature |
| APP_FLOW.md | Screen layouts, navigation, user journeys | Building any UI component |
| TECH_STACK.md | Exact versions, dependencies | Installing packages, choosing tools |
| DESIGN_SYSTEM.md | Colors, spacing, typography tokens | Any visual styling |
| FRONTEND_GUIDELINES.md | Component architecture, patterns | Creating components, hooks, stores |
| BACKEND_STRUCTURE.md | Database schema, API contracts | API implementation, data modeling |
| VALIDATION_RULES.md | Field validation rules, Zod schemas | Form validation, API validation |
| IMPLEMENTATION_PLAN.md | Build sequence (phases/steps) | Starting any task |

---

## Session Startup Sequence

**At the start of EVERY session, read these files in this order:**

1. **CLAUDE.md** (this file) — Your operating rules
2. **progress.txt** — Current project state, what's done, what's next
3. **IMPLEMENTATION_PLAN.md** — Find current phase/step
4. **LESSONS.md** — Mistakes to avoid this session
5. **Write tasks/todo.md** — Plan for this session
6. **Verify plan with user** — Before executing

```
STARTUP CHECKLIST:
[ ] Read CLAUDE.md
[ ] Read progress.txt
[ ] Identify current phase in IMPLEMENTATION_PLAN.md
[ ] Read LESSONS.md for relevant patterns
[ ] Create tasks/todo.md with checkable items
[ ] Get user approval on plan
```

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately — don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update LESSONS.md with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests — then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

## Protection Rules

### No Regressions
- Before modifying any existing file, diff what exists against what you're changing
- Never break working functionality to implement new functionality
- If a change touches more than one system, verify each system still works after
- When in doubt, ask before overwriting

### No File Overwrites
- Never overwrite existing documentation files
- Create new timestamped versions when documentation needs updating
- Canonical docs maintain history — the AI never destroys previous versions

### No Assumptions
- If you encounter anything not explicitly covered by documentation, STOP and ask
- Do not infer. Do not guess. Do not fill gaps with "reasonable defaults"
- Every undocumented decision gets escalated to the user before implementation
- Silence is not permission

### Design System Enforcement
- Before creating ANY component, check DESIGN_SYSTEM.md first
- Never invent colors, spacing values, border radii, shadows, or tokens not in the file
- If a design need arises that isn't covered, flag it and wait for the user to update DESIGN_SYSTEM.md
- Consistency is non-negotiable. Every pixel references the system.

### Mobile-First Mandate
- Every component starts as a mobile layout
- Desktop is the enhancement, not the default
- Breakpoint behavior is defined in DESIGN_SYSTEM.md — follow it exactly
- Test mental model: "Does this work on a phone first?"

---

## Task Management

1. **Plan First:** Write plan to tasks/todo.md with checkable items
2. **Verify Plan:** Check in with user before starting implementation
3. **Track Progress:** Mark items complete as you go
4. **Explain Changes:** High-level summary at each step
5. **Document Results:** Add review section to tasks/todo.md
6. **Capture Lessons:** Update LESSONS.md after corrections

---

## Core Principles

- **Simplicity First:** Make every change as simple as possible. Impact minimal code.
- **No Laziness:** Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact:** Changes should only touch what's necessary. Avoid introducing bugs.

---

## File Naming Conventions

**Frontend (per FRONTEND_GUIDELINES.md):**
| Type | Convention | Example |
|------|------------|---------|
| Components | kebab-case.tsx | `inspection-card.tsx` |
| Hooks | use-*.ts | `use-inspections.ts` |
| Stores | *-store.ts | `auth-store.ts` |
| Types | kebab-case.ts | `inspection.ts` |
| Utils | kebab-case.ts | `format-date.ts` |

**Backend:**
| Type | Convention | Example |
|------|------------|---------|
| Models | models.py, *_models.py | `deficiency_models.py` |
| Views | views.py, *_views.py | `followup_views.py` |
| Serializers | serializers.py | `serializers.py` |
| URLs | urls.py | `urls.py` |

---

## Component Patterns

**Always follow FRONTEND_GUIDELINES.md Section 3 for:**
- Component structure (imports, props, implementation)
- Form components (react-hook-form + zod)
- List components (loading/empty/error states)
- State management (TanStack Query for server, Zustand for client)

**Required patterns:**
```typescript
// Props interface - always export
export interface ComponentNameProps { ... }

// Component - named export
export const ComponentName: FC<ComponentNameProps> = ({ ... }) => { ... }
```

---

## API Contract Compliance

All API implementations MUST match BACKEND_STRUCTURE.md exactly:
- Request/response shapes must match documented contracts
- Error responses must use standard format
- RBAC must match permission matrix
- Status codes must be as documented

---

## State Machine Enforcement

**Inspection States:** DRAFT → SUBMITTED → PIC_REVIEWED → DPA_CLOSED

**CAR States:** DRAFT → SUBMITTED → PIC_ACCEPTED → DPA_CLOSED
- REWORK_REQUESTED can occur from SUBMITTED or PIC_ACCEPTED
- REWORK_REQUESTED immediately transitions to DRAFT

Never allow invalid state transitions. Validate on both frontend and backend.

---

## Business Rules (Non-Negotiable)

1. **DefCode Always Visible:** Every screen showing deficiencies must prominently display the DefCode
2. **1:1 CAR Relationship:** One deficiency creates exactly one CAR, automatically via trigger
3. **Evidence Requirements:** Submission requires ≥1 BEFORE + ≥1 AFTER evidence
4. **Root Cause Minimum:** root_cause_summary must be ≥50 characters
5. **Rework Reason Minimum:** rework reason must be ≥20 characters
6. **File Limits:** Max 3MB per file, PDF/JPG/JPEG only
7. **Storage Limit:** 150MB offline cache, warn at <10MB remaining
8. **Retry Logic:** 3 attempts with exponential backoff (1s, 2s, 4s)

---

## Forbidden Actions

❌ Do NOT install packages not in TECH_STACK.md without asking
❌ Do NOT create colors/spacing/tokens not in DESIGN_SYSTEM.md
❌ Do NOT skip loading/empty/error states
❌ Do NOT implement features not in PRD.md
❌ Do NOT deviate from API contracts in BACKEND_STRUCTURE.md
❌ Do NOT skip the session startup sequence
❌ Do NOT mark tasks complete without verification
❌ Do NOT overwrite canonical documentation files

---

## Questions to Ask Yourself

Before implementing anything:
1. Is this feature in PRD.md? What's the feature ID?
2. What does APP_FLOW.md say about this screen?
3. Am I using tokens from DESIGN_SYSTEM.md?
4. Am I following patterns from FRONTEND_GUIDELINES.md?
5. Does my API match BACKEND_STRUCTURE.md contracts?
6. What step is this in IMPLEMENTATION_PLAN.md?
7. Did I update progress.txt after completing?
8. Did I capture any corrections in LESSONS.md?

---

## Emergency Protocols

**If stuck:**
1. Stop and re-read relevant canonical doc
2. Check LESSONS.md for similar issues
3. Ask user for clarification
4. Do NOT guess or assume

**If something broke:**
1. Git diff to identify changes
2. Revert if necessary
3. Re-plan from stable state
4. Document what went wrong in LESSONS.md

**If requirements unclear:**
1. Check PRD.md for feature definition
2. Check APP_FLOW.md for screen spec
3. If still unclear, STOP and ask user
4. Never fill gaps with assumptions

---

**Remember:** These documents exist so you can build correctly without hallucinating. Use them.
