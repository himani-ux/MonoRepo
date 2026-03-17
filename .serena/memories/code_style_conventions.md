# VIMS Inspection - Code Style & Conventions

## File Naming
| Type | Convention | Example |
|------|------------|---------|
| Components | kebab-case.tsx | `inspection-card.tsx` |
| Pages | kebab-case.tsx | `[id].edit.tsx` |
| Hooks | use-*.ts | `use-inspections.ts` |
| Stores | *-store.ts | `auth-store.ts` |
| Types | kebab-case.ts | `inspection.ts` |
| Utilities | kebab-case.ts | `format-date.ts` |
| API modules | kebab-case.ts | `inspections.ts` |

## Component Naming
| Type | Convention | Example |
|------|------------|---------|
| Component name | PascalCase | `InspectionCard` |
| Props interface | PascalCase + Props | `InspectionCardProps` |
| Event handlers | on + Action | `onSubmit`, `onClick` |
| Boolean props | is/has prefix | `isLoading`, `hasError` |

## Variables & Functions
| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `inspectionData` |
| Constants | SCREAMING_SNAKE | `MAX_FILE_SIZE` |
| Functions | camelCase | `formatDate()` |
| Types/Interfaces | PascalCase | `Inspection` |
| Enums | PascalCase | `InspectionType` |

## Prettier Config
```json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "tabWidth": 2,
  "useTabs": false,
  "printWidth": 80,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

## ESLint Rules
- No unused vars (except prefixed with `_`)
- `@typescript-eslint/no-explicit-any`: warn
- `react-hooks/rules-of-hooks`: error
- `react-hooks/exhaustive-deps`: warn

## Component Structure Pattern
```tsx
import { type FC } from 'react';
// ...imports

// Props - always export
export interface ComponentNameProps {
  // ...
}

// Component - named export
export const ComponentName: FC<ComponentNameProps> = ({
  // destructured props
}) => {
  // hooks first
  // handlers
  // derived state
  // render
};
```

## Required Patterns
1. Always handle loading, empty, and error states in lists
2. Use TanStack Query for server state, Zustand for client state
3. Use react-hook-form + zod for forms
4. Mobile-first responsive design
5. Follow DESIGN_SYSTEM.md tokens (never invent colors/spacing)
