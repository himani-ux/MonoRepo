# ORB UI Alignment Handoff

Date: 2026-03-18

## Objective

Align the ORB frontend UI with the VIMS Inspection design system while keeping all business logic unchanged.

Constraints followed:
- UI-only changes
- No backend/API/database changes
- No business-logic refactors
- Reuse-oriented approach

## Reference Design Source

The active VIMS reference is the modern `psc-frontend` app, not the separate `VIMS Inspection` folder.

Key reference files:
- `psc-frontend/src/index.css`
- `psc-frontend/src/components/layout/root-layout.tsx`
- `psc-frontend/src/components/layout/header.tsx`
- `psc-frontend/src/components/layout/orb-header-actions.tsx`
- `psc-frontend/src/components/ui/button.tsx`
- `psc-frontend/src/components/ui/input.tsx`
- `psc-frontend/src/components/ui/select.tsx`
- `psc-frontend/src/components/ui/label.tsx`
- `psc-frontend/src/components/ui/card.tsx`

## What Was Changed

### 1. ORB compatibility wrapper updated

The legacy ORB UI wrapper was changed to render with VIMS-style shared primitives instead of the older ORB-specific visual layer.

Updated file:
- `psc-frontend/src/legacy/vims-basic/components/orb/OrbUI.jsx`

What changed:
- `Card` now wraps the shared VIMS card component structure
- `Button` now maps ORB variants onto shared VIMS button variants
- `Panel` kept as a compatibility structure, but styled to match VIMS
- Existing ORB pages can keep using the same component API with updated visuals

### 2. ORB theme rewritten to VIMS-aligned styling

Updated files:
- `psc-frontend/src/legacy/vims-basic/styles/orb/orb-theme.css`
- `psc-frontend/src/legacy/vims-basic/styles/orb/CrewDashboard.css`
- `psc-frontend/src/legacy/vims-basic/styles/orb/GuidelinesPage.css`

What changed:
- Removed the old ORB glass/gradient/purple-heavy theme
- Replaced it with VIMS-aligned neutral surfaces, blue accents, VIMS-like borders, spacing, shadows, radius, and table styling
- Added compatibility classes for routed ORB pages:
  - `orb-page`
  - `orb-page-status`
  - `orb-toolbar`
  - `orb-meta`
  - `orb-table-shell`
  - `orb-empty`
  - `orb-link-list`
  - `orb-link-card`
- Kept styling scoped to ORB theme usage where possible

### 3. ORB reusable components aligned

Updated files:
- `psc-frontend/src/legacy/vims-basic/components/orb/ORBEntryForm.jsx`
- `psc-frontend/src/legacy/vims-basic/components/orb/ORBTable.jsx`

What changed:
- Replaced the draft save button usage with the compatibility `Button`
- Updated table action buttons to use shared-style variants
- Replaced some inline layout wrappers with class-based layout hooks
- Preserved all submit/edit/delete/approve/reject handlers exactly as-is

### 4. Routed ORB pages visually aligned

Updated files:
- `psc-frontend/src/legacy/vims-basic/pages/orb/AllEntriesView.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/ApprovedEntriesView.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/RejectedEntriesView.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/DeletedEntriesView.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/PDFArchive.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/GuidelinesPage.jsx`

What changed:
- Converted page shells to use the new ORB compatibility styling
- Replaced older ad hoc title/content blocks with `Card title=...`
- Added VIMS-like toolbar/meta sections for vessel info and refresh actions
- Wrapped tables in a consistent scroll shell
- Replaced some ad hoc button styling with compatibility buttons
- Simplified guidelines page links into VIMS-aligned card/link presentation

## What Was Not Changed

- No API endpoints
- No fetch/mutation logic
- No form validation logic
- No permission logic
- No routing logic
- No backend or database code

## Build Verification

Executed:

```bash
cd psc-frontend
npm run build
```

Result:
- Build passed successfully
- Only existing Vite chunk-size warnings were reported

## Current Modified Files

- `psc-frontend/src/legacy/vims-basic/components/orb/ORBEntryForm.jsx`
- `psc-frontend/src/legacy/vims-basic/components/orb/ORBTable.jsx`
- `psc-frontend/src/legacy/vims-basic/components/orb/OrbUI.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/AllEntriesView.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/ApprovedEntriesView.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/DeletedEntriesView.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/GuidelinesPage.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/PDFArchive.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/RejectedEntriesView.jsx`
- `psc-frontend/src/legacy/vims-basic/styles/orb/CrewDashboard.css`
- `psc-frontend/src/legacy/vims-basic/styles/orb/GuidelinesPage.css`
- `psc-frontend/src/legacy/vims-basic/styles/orb/orb-theme.css`

## Likely Next Steps

If continuing later, focus only on remaining UI cleanup:

1. Review the current ORB pages in the browser for any visual regressions on narrow screens.
2. Reduce remaining inline table cell styling in ORB list pages if needed.
3. Decide whether unused legacy ORB shell files should remain untouched or be cleaned up later:
   - `psc-frontend/src/legacy/vims-basic/components/orb/AppHeader.jsx`
   - `psc-frontend/src/legacy/vims-basic/components/orb/AppFooter.jsx`
   - `psc-frontend/src/legacy/vims-basic/pages/orb/MainDashboard.jsx`
   - `psc-frontend/src/legacy/vims-basic/pages/orb/CrewDashboard.jsx`
   - `psc-frontend/src/legacy/vims-basic/pages/orb/ChiefDashboard.jsx`
4. Keep all future changes UI-only unless requirements explicitly change.

## Suggested Resume Prompt

Use this in the next session:

“Continue the ORB UI alignment work in `psc-frontend`. Start by reading `tasks/orb_ui_alignment_handoff_2026-03-18.md`. The branch contains uncommitted UI-only changes in legacy ORB components/pages/styles to align ORB with the VIMS design system. `npm run build` already passed. Continue from the current state without changing business logic, backend code, or APIs.”
