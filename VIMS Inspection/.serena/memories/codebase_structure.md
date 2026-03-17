# VIMS Inspection - Codebase Structure

## Project Layout
```
D:\Projects\VIMS Inspection\
├── .claude/           # Claude Code configuration
├── .serena/           # Serena MCP server data
├── Docs/              # Canonical documentation (DO NOT OVERWRITE)
│   ├── CLAUDE.md           # AI agent instructions
│   ├── PRD.md              # Product requirements (FEAT-*)
│   ├── APP_FLOW.md         # Screen layouts & navigation
│   ├── TECH_STACK.md       # Locked package versions
│   ├── DESIGN_SYSTEM.md    # Visual tokens
│   ├── FRONTEND_GUIDELINES.md  # Component patterns
│   ├── BACKEND_STRUCTURE.md    # API & database schema
│   ├── VALIDATION_RULES.md     # Zod schemas
│   ├── IMPLEMENTATION_PLAN.md  # Build phases
│   ├── LESSONS.md          # Mistakes to avoid
│   └── progress.txt        # Current state tracker
├── psc-frontend/      # React frontend application
│   ├── src/
│   │   ├── main.tsx        # Entry point
│   │   ├── App.tsx         # Root component
│   │   ├── index.css       # Global styles + Tailwind
│   │   └── lib/utils/cn.ts # className utility
│   ├── public/             # Static assets
│   ├── package.json        # Dependencies
│   ├── vite.config.ts      # Vite config
│   ├── tsconfig.json       # TypeScript config
│   ├── tailwind.config.js  # Tailwind config
│   ├── .eslintrc.cjs       # ESLint config
│   └── .prettierrc         # Prettier config
└── tasks/             # Task tracking
    └── todo.md             # Current session tasks
```

## Target Frontend Structure (per FRONTEND_GUIDELINES.md)
```
src/
├── routes/            # React Router pages
├── components/
│   ├── ui/           # shadcn/ui primitives
│   ├── layout/       # Layout components
│   ├── inspection/   # Inspection feature
│   ├── car/          # CAR feature
│   ├── sync/         # Sync feature
│   ├── notification/ # Notification feature
│   └── shared/       # Shared components
├── hooks/            # Custom React hooks
├── lib/
│   ├── api/          # API modules
│   ├── db/           # IndexedDB stores
│   ├── utils/        # Utilities
│   └── validations/  # Zod schemas
├── stores/           # Zustand stores
├── types/            # TypeScript types
└── styles/           # Additional styles
```

## Current State
The project is in active development. Phases 1-4 are complete. Phase 5 (CAR Module) is 4/6 steps done.
Frontend has: auth, layout, masters, inspection CRUD, CAR list/detail/edit pages.
Backend has: accounts, masters, inspection, car Django apps with full API endpoints.
Step 5.4 added: car-form.tsx (complex edit form with CLC multi-select, corrective action inline CRUD,
evidence display, submission validation), validations/car.ts, [id].edit.tsx route.

## Key Configuration Files
- `vite.config.ts` - Build configuration
- `tsconfig.json` - TypeScript paths (@/ alias)
- `tailwind.config.js` - Design system tokens
- `.env` - Environment variables (copy from .env.example)
