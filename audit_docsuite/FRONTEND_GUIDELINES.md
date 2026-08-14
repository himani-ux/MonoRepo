# FRONTEND_GUIDELINES.md — Engineering Rules & Component Architecture
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.1 | **Date:** 2026-02-04

---

## 1. Project Structure

```
psc-frontend/
├── index.html                    # Vite entry point
├── vite.config.ts                # Vite configuration
├── tailwind.config.js            # Tailwind configuration
├── tsconfig.json                 # TypeScript configuration
├── .env.example                  # Environment variables template
├── public/
│   ├── manifest.json             # PWA manifest
│   ├── sw.js                     # Service worker (generated)
│   └── icons/                    # PWA icons
│
├── src/
│   ├── main.tsx                  # React entry point
│   ├── App.tsx                   # Root component with router
│   ├── index.css                 # Global styles + Tailwind
│   ├── vite-env.d.ts             # Vite type definitions
│   │
│   ├── routes/                   # React Router pages
│   │   ├── index.tsx             # Route definitions
│   │   ├── login.tsx             # Login page
│   │   ├── dashboard.tsx         # Dashboard page
│   │   ├── inspections/
│   │   │   ├── index.tsx         # Inspection List
│   │   │   ├── new.tsx           # Create Inspection
│   │   │   ├── [id].tsx          # Inspection Detail
│   │   │   ├── [id].edit.tsx     # Edit Inspection
│   │   │   └── [id].follow-up.tsx # Register Follow-up
│   │   ├── cars/
│   │   │   ├── index.tsx         # CAR List
│   │   │   ├── [id].tsx          # CAR Detail
│   │   │   └── [id].edit.tsx     # Edit CAR
│   │   ├── notifications.tsx     # Notifications page
│   │   └── sync.tsx              # Sync Status page
│   │
│   ├── components/
│   │   ├── ui/                   # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── skeleton.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/               # Layout components
│   │   │   ├── root-layout.tsx   # Main app layout
│   │   │   ├── header.tsx
│   │   │   ├── sidebar.tsx
│   │   │   ├── bottom-nav.tsx
│   │   │   ├── page-header.tsx
│   │   │   └── container.tsx
│   │   │
│   │   ├── inspection/           # Inspection feature components
│   │   │   ├── inspection-card.tsx
│   │   │   ├── inspection-list.tsx
│   │   │   ├── inspection-detail.tsx
│   │   │   ├── inspection-form.tsx
│   │   │   ├── deficiency-card.tsx
│   │   │   ├── deficiency-list.tsx
│   │   │   ├── deficiency-modal.tsx
│   │   │   ├── follow-up-form.tsx
│   │   │   └── inspection-filters.tsx
│   │   │
│   │   ├── car/                  # CAR feature components
│   │   │   ├── car-card.tsx
│   │   │   ├── car-list.tsx
│   │   │   ├── car-detail.tsx
│   │   │   ├── car-form.tsx
│   │   │   ├── root-cause-section.tsx
│   │   │   ├── corrective-action-list.tsx
│   │   │   ├── corrective-action-item.tsx
│   │   │   ├── evidence-section.tsx
│   │   │   ├── evidence-upload-modal.tsx
│   │   │   ├── activity-history.tsx
│   │   │   ├── audit-log.tsx
│   │   │   ├── pic-accept-modal.tsx
│   │   │   ├── rework-modal.tsx
│   │   │   └── dpa-close-modal.tsx
│   │   │
│   │   ├── sync/                 # Sync feature components
│   │   │   ├── sync-status.tsx
│   │   │   ├── storage-indicator.tsx
│   │   │   ├── pending-changes.tsx
│   │   │   ├── conflict-list.tsx
│   │   │   └── offline-banner.tsx
│   │   │
│   │   ├── notification/         # Notification components
│   │   │   ├── notification-list.tsx
│   │   │   ├── notification-item.tsx
│   │   │   └── notification-badge.tsx
│   │   │
│   │   └── shared/               # Shared components
│   │       ├── status-badge.tsx
│   │       ├── date-picker.tsx
│       ├── file-upload.tsx
│       ├── search-input.tsx
│       ├── empty-state.tsx
│       ├── error-state.tsx
│       ├── loading-skeleton.tsx
│       ├── confirm-dialog.tsx
│       └── def-code-select.tsx
│
├── hooks/                        # Custom React hooks
│   ├── use-inspections.ts
│   ├── use-inspection.ts
│   ├── use-cars.ts
│   ├── use-car.ts
│   ├── use-deficiencies.ts
│   ├── use-sync.ts
│   ├── use-offline.ts
│   ├── use-auth.ts
│   ├── use-notifications.ts
│   ├── use-masters.ts
│   └── use-debounce.ts
│
├── lib/                          # Utilities and configurations
│   ├── api/
│   │   ├── client.ts             # Axios instance
│   │   ├── inspections.ts        # Inspection API calls
│   │   ├── cars.ts               # CAR API calls
│   │   ├── sync.ts               # Sync API calls
│   │   └── masters.ts            # Master data API calls
│   ├── db/
│   │   ├── index.ts              # IndexedDB setup (idb)
│   │   ├── inspections.ts        # Inspection offline store
│   │   ├── cars.ts               # CAR offline store
│   │   └── sync-queue.ts         # Offline sync queue
│   ├── utils/
│   │   ├── format-date.ts
│   │   ├── format-currency.ts
│   │   ├── validators.ts
│   │   ├── cn.ts                 # className utility
│   │   └── constants.ts
│   └── validations/
│       ├── inspection.ts         # Zod schemas
│       ├── car.ts
│       └── evidence.ts
│
├── stores/                       # Zustand stores
│   ├── auth-store.ts
│   ├── sync-store.ts
│   ├── notification-store.ts
│   └── ui-store.ts
│
├── types/                        # TypeScript types
│   ├── inspection.ts
│   ├── car.ts
│   ├── deficiency.ts
│   ├── user.ts
│   ├── masters.ts
│   ├── sync.ts
│   └── api.ts
│
└── styles/                       # Additional styles
    └── tailwind.css
```

---

## 2. Naming Conventions

### 2.1 Files & Folders
| Type | Convention | Example |
|------|------------|---------|
| Components | kebab-case | `inspection-card.tsx` |
| Pages | kebab-case | `page.tsx` in folder |
| Hooks | camelCase with `use` prefix | `use-inspections.ts` |
| Utilities | kebab-case | `format-date.ts` |
| Types | kebab-case | `inspection.ts` |
| Stores | kebab-case with `-store` suffix | `auth-store.ts` |
| API modules | kebab-case | `inspections.ts` |

### 2.2 Components
| Type | Convention | Example |
|------|------------|---------|
| Component name | PascalCase | `InspectionCard` |
| Props interface | PascalCase with `Props` suffix | `InspectionCardProps` |
| Event handlers | camelCase with `on` prefix | `onSubmit`, `onClick` |
| Boolean props | camelCase with `is`/`has` prefix | `isLoading`, `hasError` |

### 2.3 Variables & Functions
| Type | Convention | Example |
|------|------------|---------|
| Variables | camelCase | `inspectionData` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_FILE_SIZE` |
| Functions | camelCase | `formatDate()` |
| Types/Interfaces | PascalCase | `Inspection`, `CarStatus` |
| Enums | PascalCase | `InspectionType` |

---

## 3. Component Patterns

### 3.1 Component Structure
```tsx
// inspection-card.tsx

import { type FC } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/status-badge';
import { formatDate } from '@/lib/utils/format-date';
import { cn } from '@/lib/utils/cn';
import type { Inspection } from '@/types/inspection';

// Props interface - always export
export interface InspectionCardProps {
  inspection: Inspection;
  onClick?: (id: number) => void;
  className?: string;
}

// Component - use named export
export const InspectionCard: FC<InspectionCardProps> = ({
  inspection,
  onClick,
  className,
}) => {
  const handleClick = () => {
    onClick?.(inspection.inspection_id);
  };

  return (
    <Card 
      className={cn(
        'cursor-pointer transition-shadow hover:shadow-lg',
        inspection.is_detention && 'border-l-4 border-l-error-500 bg-error-50',
        className
      )}
      onClick={handleClick}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-2">
          <Ship className="h-5 w-5 text-neutral-500" />
          <span className="font-semibold text-neutral-800">
            {inspection.vessel_name}
          </span>
        </div>
        <StatusBadge status={inspection.status} />
      </CardHeader>
      <CardContent>
        <div className="text-sm text-neutral-500">
          {inspection.inspection_type}
          {inspection.psc_subtype && ` - ${inspection.psc_subtype}`}
        </div>
        <div className="text-sm text-neutral-500">
          {inspection.port_place} | {formatDate(inspection.inspection_date)}
        </div>
        <div className="mt-2 text-sm">
          Deficiencies: {inspection.deficiency_count} 
          ({inspection.open_deficiency_count} open)
        </div>
        {inspection.is_detention && (
          <Badge variant="destructive" className="mt-2">
            DETENTION
          </Badge>
        )}
      </CardContent>
    </Card>
  );
};
```

### 3.2 Form Component Pattern
```tsx
// inspection-form.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { inspectionSchema, type InspectionFormData } from '@/lib/validations/inspection';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { DatePicker } from '@/components/shared/date-picker';
import { INSPECTION_TYPES, PSC_SUBTYPES } from '@/lib/utils/constants';

export interface InspectionFormProps {
  defaultValues?: Partial<InspectionFormData>;
  onSubmit: (data: InspectionFormData) => Promise<void>;
  isLoading?: boolean;
}

export const InspectionForm: FC<InspectionFormProps> = ({
  defaultValues,
  onSubmit,
  isLoading,
}) => {
  const form = useForm<InspectionFormData>({
    resolver: zodResolver(inspectionSchema),
    defaultValues: {
      inspection_type: 'PSC',
      ...defaultValues,
    },
  });

  const inspectionType = form.watch('inspection_type');

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {/* Inspection Type */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-neutral-700">
          Inspection Type *
        </label>
        <Select
          {...form.register('inspection_type')}
          options={INSPECTION_TYPES}
          error={form.formState.errors.inspection_type?.message}
        />
      </div>

      {/* PSC Subtype - Conditional */}
      {inspectionType === 'PSC' && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-neutral-700">
            PSC Subtype *
          </label>
          <Select
            {...form.register('psc_subtype')}
            options={PSC_SUBTYPES}
            error={form.formState.errors.psc_subtype?.message}
          />
        </div>
      )}

      {/* ... more fields ... */}

      <div className="flex gap-4">
        <Button type="button" variant="outline">
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Create Inspection'}
        </Button>
      </div>
    </form>
  );
};
```

### 3.3 List Component with Loading/Empty States
```tsx
// inspection-list.tsx

import { InspectionCard } from './inspection-card';
import { LoadingSkeleton } from '@/components/shared/loading-skeleton';
import { EmptyState } from '@/components/shared/empty-state';
import type { Inspection } from '@/types/inspection';

export interface InspectionListProps {
  inspections: Inspection[];
  isLoading: boolean;
  onInspectionClick: (id: number) => void;
  emptyMessage?: string;
  emptyAction?: () => void;
  emptyActionLabel?: string;
}

export const InspectionList: FC<InspectionListProps> = ({
  inspections,
  isLoading,
  onInspectionClick,
  emptyMessage = 'No inspections found',
  emptyAction,
  emptyActionLabel,
}) => {
  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <LoadingSkeleton key={i} className="h-32" />
        ))}
      </div>
    );
  }

  // Empty state
  if (inspections.length === 0) {
    return (
      <EmptyState
        icon={<Ship className="h-12 w-12" />}
        title={emptyMessage}
        description="Previous inspection records will appear here once uploaded."
        action={emptyAction}
        actionLabel={emptyActionLabel}
      />
    );
  }

  // Data state
  return (
    <div className="space-y-4">
      {inspections.map((inspection) => (
        <InspectionCard
          key={inspection.inspection_id}
          inspection={inspection}
          onClick={onInspectionClick}
        />
      ))}
    </div>
  );
};
```

---

## 4. State Management

### 4.1 Server State (TanStack Query)
```tsx
// hooks/use-inspections.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inspectionsApi } from '@/lib/api/inspections';
import type { InspectionFilters, CreateInspectionData } from '@/types/inspection';

export const inspectionKeys = {
  all: ['inspections'] as const,
  lists: () => [...inspectionKeys.all, 'list'] as const,
  list: (filters: InspectionFilters) => [...inspectionKeys.lists(), filters] as const,
  details: () => [...inspectionKeys.all, 'detail'] as const,
  detail: (id: number) => [...inspectionKeys.details(), id] as const,
};

export function useInspections(filters: InspectionFilters) {
  return useQuery({
    queryKey: inspectionKeys.list(filters),
    queryFn: () => inspectionsApi.getList(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useInspection(id: number) {
  return useQuery({
    queryKey: inspectionKeys.detail(id),
    queryFn: () => inspectionsApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateInspection() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CreateInspectionData) => inspectionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: inspectionKeys.lists() });
    },
  });
}
```

### 4.2 Client State (Zustand)
```tsx
// stores/sync-store.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SyncState {
  isOnline: boolean;
  lastSyncTime: Date | null;
  pendingChanges: number;
  conflicts: number;
  setOnline: (isOnline: boolean) => void;
  setLastSyncTime: (time: Date) => void;
  incrementPendingChanges: () => void;
  decrementPendingChanges: () => void;
  setConflicts: (count: number) => void;
}

export const useSyncStore = create<SyncState>()(
  persist(
    (set) => ({
      isOnline: true,
      lastSyncTime: null,
      pendingChanges: 0,
      conflicts: 0,
      setOnline: (isOnline) => set({ isOnline }),
      setLastSyncTime: (time) => set({ lastSyncTime: time }),
      incrementPendingChanges: () => 
        set((state) => ({ pendingChanges: state.pendingChanges + 1 })),
      decrementPendingChanges: () => 
        set((state) => ({ pendingChanges: Math.max(0, state.pendingChanges - 1) })),
      setConflicts: (conflicts) => set({ conflicts }),
    }),
    {
      name: 'sync-storage',
    }
  )
);
```

---

## 5. API Integration

### 5.1 API Client Setup
```tsx
// lib/api/client.ts

import axios, { type AxiosError } from 'axios';
import { useAuthStore } from '@/stores/auth-store';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/psc';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 5.2 API Module Pattern
```tsx
// lib/api/inspections.ts

import { apiClient } from './client';
import type { 
  Inspection, 
  InspectionFilters, 
  CreateInspectionData,
  PaginatedResponse 
} from '@/types/inspection';

export const inspectionsApi = {
  getList: async (filters: InspectionFilters): Promise<PaginatedResponse<Inspection>> => {
    const { data } = await apiClient.get('/inspection/inspections/', { params: filters });
    return data;
  },

  getById: async (id: number): Promise<Inspection> => {
    const { data } = await apiClient.get(`/inspection/inspections/${id}/`);
    return data;
  },

  create: async (payload: CreateInspectionData): Promise<Inspection> => {
    const { data } = await apiClient.post('/inspection/inspections/', payload);
    return data;
  },

  update: async (id: number, payload: Partial<Inspection>): Promise<Inspection> => {
    const { data } = await apiClient.patch(`/inspection/inspections/${id}/`, payload);
    return data;
  },

  submit: async (id: number): Promise<Inspection> => {
    const { data } = await apiClient.post(`/inspection/inspections/${id}/submit/`);
    return data;
  },

  uploadReport: async (id: number, file: File, description: string): Promise<void> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('description', description);
    await apiClient.post(`/inspection/inspections/${id}/upload-report/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
```

---

## 6. Validation

### 6.1 Zod Schemas
```tsx
// lib/validations/inspection.ts

import { z } from 'zod';
import { INSPECTION_TYPES, PSC_SUBTYPES } from '@/lib/utils/constants';

export const inspectionSchema = z.object({
  vessel_id: z.string().uuid('Vessel is required'),
  inspection_type: z.enum(INSPECTION_TYPES, {
    required_error: 'Inspection type is required',
  }),
  psc_subtype: z.enum(PSC_SUBTYPES).optional().nullable(),
  inspection_date: z.coerce.date()
    .max(new Date(), 'Inspection date cannot be in the future'),
  port_place: z.string().min(1, 'Port/Place is required'),
  country: z.string().optional(),
  authority: z.string().optional(),
  mou_code: z.string().optional(),
  inspector_name: z.string().optional(),
  report_reference: z.string().optional(),
  is_detention: z.boolean().default(false),
}).refine(
  (data) => {
    if (data.inspection_type === 'PSC' && !data.psc_subtype) {
      return false;
    }
    return true;
  },
  {
    message: 'PSC subtype is required for PSC inspections',
    path: ['psc_subtype'],
  }
);

export type InspectionFormData = z.infer<typeof inspectionSchema>;
```

### 6.2 CAR Submission Validation
```tsx
// lib/validations/car.ts

import { z } from 'zod';

export const carSubmissionSchema = z.object({
  root_cause_summary: z.string()
    .min(50, 'Root cause summary is required (minimum 50 characters)'),
  clc_codes: z.array(z.string()).optional(),
  custom_cause: z.string().optional(),
  corrective_actions: z.array(z.object({
    action_type: z.enum(['IMMEDIATE', 'LONGTERM']),
    description: z.string().min(1, 'Description is required'),
    assigned_to: z.string().min(1, 'Owner is required'),
    due_date: z.coerce.date({ required_error: 'Due date is required' }),
  })),
  before_evidence: z.array(z.any()).min(1, 'At least one BEFORE evidence is required'),
  after_evidence: z.array(z.any()).min(1, 'At least one AFTER evidence is required'),
}).refine(
  (data) => (data.clc_codes?.length ?? 0) > 0 || (data.custom_cause?.length ?? 0) > 0,
  {
    message: 'At least one root cause is required',
    path: ['clc_codes'],
  }
).refine(
  (data) => data.corrective_actions.some(a => a.action_type === 'IMMEDIATE'),
  {
    message: 'At least one immediate action is required',
    path: ['corrective_actions'],
  }
).refine(
  (data) => data.corrective_actions.some(a => a.action_type === 'LONGTERM'),
  {
    message: 'At least one long-term action is required',
    path: ['corrective_actions'],
  }
);
```

---

## 7. Offline Support

### 7.1 IndexedDB Setup
```tsx
// lib/db/index.ts

import { openDB, type DBSchema, type IDBPDatabase } from 'idb';

interface InspectionDB extends DBSchema {
  inspections: {
    key: number;
    value: Inspection;
    indexes: { 'by-vessel': string; 'by-status': string };
  };
  deficiencies: {
    key: number;
    value: Deficiency;
    indexes: { 'by-inspection': number };
  };
  cars: {
    key: number;
    value: Car;
    indexes: { 'by-deficiency': number; 'by-status': string };
  };
  syncQueue: {
    key: number;
    value: SyncEvent;
    indexes: { 'by-timestamp': number };
  };
  masters: {
    key: string;
    value: any;
  };
}

let dbPromise: Promise<IDBPDatabase<InspectionDB>>;

export async function getDB() {
  if (!dbPromise) {
    dbPromise = openDB<InspectionDB>('inspection-module', 1, {
      upgrade(db) {
        // Inspections store
        const inspectionStore = db.createObjectStore('inspections', { 
          keyPath: 'inspection_id' 
        });
        inspectionStore.createIndex('by-vessel', 'vessel_id');
        inspectionStore.createIndex('by-status', 'status');

        // Deficiencies store
        const deficiencyStore = db.createObjectStore('deficiencies', { 
          keyPath: 'deficiency_id' 
        });
        deficiencyStore.createIndex('by-inspection', 'inspection_id');

        // CARs store
        const carStore = db.createObjectStore('cars', { 
          keyPath: 'car_id' 
        });
        carStore.createIndex('by-deficiency', 'deficiency_id');
        carStore.createIndex('by-status', 'status');

        // Sync queue
        const syncStore = db.createObjectStore('syncQueue', { 
          keyPath: 'id', 
          autoIncrement: true 
        });
        syncStore.createIndex('by-timestamp', 'timestamp');

        // Masters
        db.createObjectStore('masters', { keyPath: 'key' });
      },
    });
  }
  return dbPromise;
}
```

### 7.2 Offline Hook
```tsx
// hooks/use-offline.ts

import { useState, useEffect } from 'react';
import { useSyncStore } from '@/stores/sync-store';

export function useOffline() {
  const { isOnline, setOnline } = useSyncStore();
  const [wasOffline, setWasOffline] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setOnline(true);
      if (wasOffline) {
        // Trigger sync when coming back online
        triggerSync();
      }
    };

    const handleOffline = () => {
      setOnline(false);
      setWasOffline(true);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Set initial state
    setOnline(navigator.onLine);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [wasOffline, setOnline]);

  return { isOnline, wasOffline };
}
```

---

## 8. Responsive Patterns

### 8.1 Mobile-First Classes
```tsx
// Always start with mobile styles, then enhance for larger screens

// Grid layout
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

// Visibility
<div className="block md:hidden">Mobile only</div>
<div className="hidden md:block">Tablet and up</div>

// Navigation
<nav className="fixed bottom-0 md:fixed md:left-0 md:top-0 md:h-screen md:w-64">

// Padding
<div className="p-4 md:p-6 lg:p-8">

// Typography
<h1 className="text-xl md:text-2xl lg:text-3xl">
```

### 8.2 Container Pattern
```tsx
// components/layout/container.tsx

export const Container: FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => (
  <div className={cn(
    'mx-auto w-full px-4 md:px-6 lg:px-8',
    'max-w-full lg:max-w-5xl xl:max-w-6xl',
    className
  )}>
    {children}
  </div>
);
```

---

## 9. Error Handling

### 9.1 Error Boundary
```tsx
// components/shared/error-boundary.tsx

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { ErrorState } from './error-state';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Send to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <ErrorState
          title="Something went wrong"
          description="Please try refreshing the page."
          onRetry={() => this.setState({ hasError: false, error: null })}
        />
      );
    }

    return this.props.children;
  }
}
```

### 9.2 API Error Handling
```tsx
// lib/utils/handle-api-error.ts

import { AxiosError } from 'axios';
import { toast } from '@/components/ui/toast';

interface ApiError {
  error: string;
  message: string;
  details?: Record<string, string>;
}

export function handleApiError(error: unknown) {
  if (error instanceof AxiosError) {
    const apiError = error.response?.data as ApiError;
    
    if (apiError?.details) {
      // Show field-level errors
      Object.entries(apiError.details).forEach(([field, message]) => {
        toast.error(`${field}: ${message}`);
      });
    } else if (apiError?.message) {
      toast.error(apiError.message);
    } else {
      toast.error('An unexpected error occurred');
    }
  } else {
    toast.error('An unexpected error occurred');
  }
}
```

---

## 10. Testing Patterns

### 10.1 Component Testing
```tsx
// __tests__/components/inspection-card.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { InspectionCard } from '@/components/inspection/inspection-card';
import { mockInspection } from '@/__mocks__/inspection';

describe('InspectionCard', () => {
  it('renders inspection details', () => {
    render(<InspectionCard inspection={mockInspection} />);
    
    expect(screen.getByText(mockInspection.vessel_name)).toBeInTheDocument();
    expect(screen.getByText(/PSC - INITIAL/)).toBeInTheDocument();
    expect(screen.getByText(mockInspection.port_place)).toBeInTheDocument();
  });

  it('shows detention badge when is_detention is true', () => {
    render(<InspectionCard inspection={{ ...mockInspection, is_detention: true }} />);
    
    expect(screen.getByText('DETENTION')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<InspectionCard inspection={mockInspection} onClick={handleClick} />);
    
    fireEvent.click(screen.getByRole('article'));
    
    expect(handleClick).toHaveBeenCalledWith(mockInspection.inspection_id);
  });
});
```

---

## 11. Document References

| Document | Reference |
|----------|-----------|
| DESIGN_SYSTEM.md | All color, spacing, typography tokens |
| APP_FLOW.md | Screen layouts and navigation |
| PRD.md | Feature requirements (FEAT-*) |
| BACKEND_STRUCTURE.md | API endpoint contracts |
| VALIDATION_RULES.md | Zod validation schemas |
| TECH_STACK.md | Package versions |

---

**Document Control:**
- Created: 2026-02-03
- Updated: 2026-02-04
- Author: System Generated
- Framework: React 18.3.1 + TypeScript 5.4.5 + Tailwind CSS 3.4.7
