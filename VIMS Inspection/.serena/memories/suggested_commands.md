# VIMS Inspection - Development Commands

## Frontend Commands (run from `psc-frontend/` directory)

### Development
```bash
npm run dev          # Start Vite dev server (localhost:5173)
npm run build        # TypeScript check + Vite build
npm run preview      # Preview production build
```

### Code Quality
```bash
npm run lint         # Run ESLint (ts,tsx files, max 0 warnings)
npm run format       # Run Prettier on src/**/*.{ts,tsx,css,json}
```

### Package Management
```bash
npm install          # Install dependencies
npm ci               # Clean install (for CI/reproducible builds)
```

## Windows-Specific Utilities
```powershell
# List directory contents
dir                  # or ls (PowerShell alias)
Get-ChildItem -Recurse  # Recursive listing

# Find files
Get-ChildItem -Recurse -Filter "*.tsx"

# Search in files
Select-String -Path "src\**\*.ts" -Pattern "pattern"

# Git commands (same as unix)
git status
git diff
git log --oneline
```

## Project Navigation
- Frontend code: `psc-frontend/src/`
- Documentation: `Docs/`
- Tasks: `tasks/todo.md`

## Environment Setup
1. Copy `psc-frontend/.env.example` to `psc-frontend/.env`
2. Configure `VITE_API_BASE_URL` for API endpoint

## Pre-Task Checklist
Before starting any task:
1. Read `Docs/CLAUDE.md` (AI instructions)
2. Read `Docs/progress.txt` (current state)
3. Check `Docs/IMPLEMENTATION_PLAN.md` (current phase)
4. Read `Docs/LESSONS.md` (mistakes to avoid)
5. Update `tasks/todo.md` with plan
