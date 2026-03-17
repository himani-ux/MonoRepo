# VIMS Inspection - Task Completion Checklist

## Before Starting Any Task
- [ ] Read `Docs/CLAUDE.md` for operating rules
- [ ] Read `Docs/progress.txt` for current project state
- [ ] Identify current phase in `Docs/IMPLEMENTATION_PLAN.md`
- [ ] Check `Docs/LESSONS.md` for relevant patterns to avoid
- [ ] Write plan to `tasks/todo.md` with checkable items
- [ ] Get user approval before implementing

## During Implementation
- [ ] Check PRD.md for feature ID (FEAT-*)
- [ ] Check APP_FLOW.md for screen specifications
- [ ] Use only tokens from DESIGN_SYSTEM.md
- [ ] Follow patterns from FRONTEND_GUIDELINES.md
- [ ] Match API contracts in BACKEND_STRUCTURE.md
- [ ] Validate with VALIDATION_RULES.md schemas

## Code Quality Checks
- [ ] Run `npm run lint` - must pass with 0 warnings
- [ ] Run `npm run format` - format all changed files
- [ ] TypeScript compiles without errors
- [ ] All loading/empty/error states handled
- [ ] Mobile-first responsive design applied
- [ ] No hardcoded colors/spacing (use design tokens)

## After Task Completion
- [ ] Update `Docs/progress.txt` with what was completed
- [ ] Mark items complete in `tasks/todo.md`
- [ ] Add review section to todo.md with results
- [ ] If any corrections made, update `Docs/LESSONS.md`

## Forbidden Actions
❌ Do NOT install packages not in TECH_STACK.md
❌ Do NOT create colors/spacing/tokens not in DESIGN_SYSTEM.md
❌ Do NOT skip loading/empty/error states
❌ Do NOT implement features not in PRD.md
❌ Do NOT deviate from API contracts
❌ Do NOT overwrite canonical documentation files
❌ Do NOT mark tasks complete without verification
