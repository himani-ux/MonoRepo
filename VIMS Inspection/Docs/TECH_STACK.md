# TECH_STACK.md â€” Locked Technology Versions
## Inspection Module â€” PSC/RS/Audit Close-out System
**Version:** 1.0 | **Date:** 2026-02-04 | **Status:** APPROVED

---

## âš ï¸ VERSION LOCK POLICY

**DO NOT** install any package not listed in this document without explicit approval.
**DO NOT** upgrade versions without testing and approval.
All versions are **pinned** to ensure reproducibility.

---

## 1. Frontend Stack

### 1.1 Runtime & Build

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| Node.js | 22.17.1 | JavaScript runtime | Via nvm or direct install |
| npm | 10.x | Package manager | Comes with Node.js |
| Vite | 5.4.0 | Build tool & dev server | `npm create vite@5.4.0` |

### 1.2 Core Framework

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| react | 18.3.1 | UI framework | `npm install react@18.3.1` |
| react-dom | 18.3.1 | React DOM renderer | `npm install react-dom@18.3.1` |
| typescript | 5.4.5 | Type safety | `npm install -D typescript@5.4.5` |
| @types/react | 18.3.3 | React type definitions | `npm install -D @types/react@18.3.3` |
| @types/react-dom | 18.3.0 | React DOM types | `npm install -D @types/react-dom@18.3.0` |

### 1.3 Routing

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| react-router-dom | 6.24.0 | Client-side routing | `npm install react-router-dom@6.24.0` |

### 1.4 Styling

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| tailwindcss | 3.4.7 | Utility-first CSS | `npm install -D tailwindcss@3.4.7` |
| postcss | 8.4.39 | CSS processing | `npm install -D postcss@8.4.39` |
| autoprefixer | 10.4.19 | Vendor prefixes | `npm install -D autoprefixer@10.4.19` |
| tailwind-merge | 2.4.0 | Merge Tailwind classes | `npm install tailwind-merge@2.4.0` |
| clsx | 2.1.1 | Conditional classes | `npm install clsx@2.1.1` |
| class-variance-authority | 0.7.0 | Component variants | `npm install class-variance-authority@0.7.0` |

### 1.5 UI Components

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| @radix-ui/react-dialog | 1.1.1 | Modal dialogs | `npm install @radix-ui/react-dialog@1.1.1` |
| @radix-ui/react-select | 2.1.1 | Select dropdowns | `npm install @radix-ui/react-select@2.1.1` |
| @radix-ui/react-checkbox | 1.1.1 | Checkboxes | `npm install @radix-ui/react-checkbox@1.1.1` |
| @radix-ui/react-label | 2.1.0 | Form labels | `npm install @radix-ui/react-label@2.1.0` |
| @radix-ui/react-slot | 1.1.0 | Slot pattern | `npm install @radix-ui/react-slot@1.1.0` |
| @radix-ui/react-toast | 1.2.1 | Toast notifications | `npm install @radix-ui/react-toast@1.2.1` |
| @radix-ui/react-tabs | 1.1.0 | Tab navigation | `npm install @radix-ui/react-tabs@1.1.0` |
| @radix-ui/react-dropdown-menu | 2.1.1 | Dropdown menus | `npm install @radix-ui/react-dropdown-menu@2.1.1` |
| lucide-react | 0.408.0 | Icons | `npm install lucide-react@0.408.0` |

### 1.6 State Management

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| @tanstack/react-query | 5.51.0 | Server state | `npm install @tanstack/react-query@5.51.0` |
| zustand | 4.5.4 | Client state | `npm install zustand@4.5.4` |

### 1.7 Forms & Validation

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| react-hook-form | 7.52.1 | Form handling | `npm install react-hook-form@7.52.1` |
| @hookform/resolvers | 3.9.0 | Validation resolvers | `npm install @hookform/resolvers@3.9.0` |
| zod | 3.23.8 | Schema validation | `npm install zod@3.23.8` |

### 1.8 HTTP Client

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| axios | 1.7.2 | HTTP requests | `npm install axios@1.7.2` |

### 1.9 Date Handling

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| date-fns | 3.6.0 | Date utilities | `npm install date-fns@3.6.0` |

### 1.10 Offline & PWA

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| workbox-core | 7.1.0 | Service worker core | `npm install workbox-core@7.1.0` |
| workbox-precaching | 7.1.0 | Precache assets | `npm install workbox-precaching@7.1.0` |
| workbox-routing | 7.1.0 | Request routing | `npm install workbox-routing@7.1.0` |
| workbox-strategies | 7.1.0 | Caching strategies | `npm install workbox-strategies@7.1.0` |
| workbox-background-sync | 7.1.0 | Background sync | `npm install workbox-background-sync@7.1.0` |
| workbox-window | 7.1.0 | SW registration | `npm install workbox-window@7.1.0` |
| vite-plugin-pwa | 0.20.0 | PWA Vite plugin | `npm install -D vite-plugin-pwa@0.20.0` |
| idb | 8.0.0 | IndexedDB wrapper | `npm install idb@8.0.0` |

### 1.11 Dev Dependencies

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| eslint | 8.57.0 | Linting | `npm install -D eslint@8.57.0` |
| eslint-plugin-react | 7.34.3 | React linting | `npm install -D eslint-plugin-react@7.34.3` |
| eslint-plugin-react-hooks | 4.6.2 | Hooks linting | `npm install -D eslint-plugin-react-hooks@4.6.2` |
| @typescript-eslint/parser | 7.16.0 | TS parsing | `npm install -D @typescript-eslint/parser@7.16.0` |
| @typescript-eslint/eslint-plugin | 7.16.0 | TS linting | `npm install -D @typescript-eslint/eslint-plugin@7.16.0` |
| prettier | 3.3.3 | Code formatting | `npm install -D prettier@3.3.3` |
| prettier-plugin-tailwindcss | 0.6.5 | Tailwind sorting | `npm install -D prettier-plugin-tailwindcss@0.6.5` |

---

## 2. Backend Stack

### 2.1 Runtime

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| Python | 3.12.4 | Runtime | System install |
| pip | 24.x | Package manager | Comes with Python |

### 2.2 Framework

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| Django | 5.2.7 | Web framework | `pip install Django==5.2.7` |
| djangorestframework | 3.14.0 | REST API | `pip install djangorestframework==3.14.0` |
| django-cors-headers | 4.4.0 | CORS handling | `pip install django-cors-headers==4.4.0` |

### 2.3 Authentication

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| djangorestframework-simplejwt | 5.3.1 | JWT auth | `pip install djangorestframework-simplejwt==5.3.1` |
| PyJWT | 2.8.0 | JWT encoding | `pip install PyJWT==2.8.0` |

### 2.4 Database

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| pyodbc | 5.1.0 | ODBC connector | `pip install pyodbc==5.1.0` |
| mssql-django | 1.4 | SQL Server backend | `pip install mssql-django==1.4` |

### 2.5 File Generation

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| reportlab | 4.2.0 | PDF generation | `pip install reportlab==4.2.0` |
| PyPDF2 | 3.0.1 | PDF manipulation | `pip install PyPDF2==3.0.1` |
| openpyxl | 3.1.5 | Excel generation | `pip install openpyxl==3.1.5` |
| Pillow | 10.4.0 | Image processing | `pip install Pillow==10.4.0` |

### 2.6 Utilities

| Package | Version | Purpose | Install Command |
|---------|---------|---------|-----------------|
| python-dotenv | 1.0.1 | Environment vars | `pip install python-dotenv==1.0.1` |
| gunicorn | 22.0.0 | WSGI server | `pip install gunicorn==22.0.0` |

---

## 3. Database

| Component | Version | Notes |
|-----------|---------|-------|
| SQL Server | 2019 | Production database |
| Database Name | `ksm_marine_live` | Shared with CMS |
| ODBC Driver | 17 or 18 | Microsoft ODBC Driver for SQL Server |

### 3.1 Database Conventions

| Convention | Pattern | Example |
|------------|---------|---------|
| Primary Key | `id` (uniqueidentifier) | `id uniqueidentifier NOT NULL` |
| Foreign Key | `{entity}_id` | `vessel_id`, `car_id` |
| Master Tables | `master_{name}` | `master_psc_def_code` |
| Transaction Tables | `psc_{name}` | `psc_inspection` |
| Stored Procedures | `usp_{action}_{entity}` | `usp_get_inspection` |
| Soft Delete | `is_deleted` bit | `is_deleted bit DEFAULT 0` |
| Audit Columns | Standard set | `created_by`, `created_date`, `updated_by`, `updated_date` |

### 3.2 Connection String Pattern
```
Driver={ODBC Driver 17 for SQL Server};
Server=<server>;
Database=ksm_marine_live;
UID=<username>;
PWD=<password>;
```

---

## 4. Infrastructure

### 4.1 Web Server

| Component | Version | Purpose |
|-----------|---------|---------|
| Nginx | 1.24.x | Reverse proxy, static files |
| Gunicorn | 22.0.0 | WSGI application server |

### 4.2 File Storage

| Component | Path | Purpose |
|-----------|------|---------|
| Uploads Base | `/var/www/ksm_uploads/` | All module uploads |
| PSC Module | `/var/www/ksm_uploads/psc/` | PSC-specific files |
| Temp Uploads | `/var/www/ksm_uploads/psc/temp/` | Temporary files (daily cleanup) |

### 4.3 File Path Pattern
```
/var/www/ksm_uploads/psc/{vessel_id}/inspections/{inspection_id}/report_{timestamp}.pdf
/var/www/ksm_uploads/psc/{vessel_id}/cars/{car_id}/{type}_{timestamp}_{random4}.{ext}
```

**File naming:** `{type}_{YYYYMMDD}_{HHMMSS}_{random4}.{ext}`
- Example: `before_20260204_143052_a7f2.jpg`

---

## 5. Browser Support

| Browser | Minimum Version | Notes |
|---------|-----------------|-------|
| Chrome | 90+ | Primary target |
| Safari | 14+ | iOS devices on vessels |
| Edge | 90+ | Windows fallback |
| Firefox | 90+ | Secondary support |

**PWA Requirements:**
- Service Worker support
- IndexedDB support
- Background Sync API support

---

## 6. Complete Installation Commands

### 6.1 Frontend (package.json dependencies)
```json
{
  "dependencies": {
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "react-router-dom": "6.24.0",
    "@tanstack/react-query": "5.51.0",
    "zustand": "4.5.4",
    "react-hook-form": "7.52.1",
    "@hookform/resolvers": "3.9.0",
    "zod": "3.23.8",
    "axios": "1.7.2",
    "date-fns": "3.6.0",
    "tailwind-merge": "2.4.0",
    "clsx": "2.1.1",
    "class-variance-authority": "0.7.0",
    "@radix-ui/react-dialog": "1.1.1",
    "@radix-ui/react-select": "2.1.1",
    "@radix-ui/react-checkbox": "1.1.1",
    "@radix-ui/react-label": "2.1.0",
    "@radix-ui/react-slot": "1.1.0",
    "@radix-ui/react-toast": "1.2.1",
    "@radix-ui/react-tabs": "1.1.0",
    "@radix-ui/react-dropdown-menu": "2.1.1",
    "lucide-react": "0.408.0",
    "workbox-core": "7.1.0",
    "workbox-precaching": "7.1.0",
    "workbox-routing": "7.1.0",
    "workbox-strategies": "7.1.0",
    "workbox-background-sync": "7.1.0",
    "workbox-window": "7.1.0",
    "idb": "8.0.0"
  },
  "devDependencies": {
    "typescript": "5.4.5",
    "@types/react": "18.3.3",
    "@types/react-dom": "18.3.0",
    "vite": "5.4.0",
    "tailwindcss": "3.4.7",
    "postcss": "8.4.39",
    "autoprefixer": "10.4.19",
    "vite-plugin-pwa": "0.20.0",
    "eslint": "8.57.0",
    "eslint-plugin-react": "7.34.3",
    "eslint-plugin-react-hooks": "4.6.2",
    "@typescript-eslint/parser": "7.16.0",
    "@typescript-eslint/eslint-plugin": "7.16.0",
    "prettier": "3.3.3",
    "prettier-plugin-tailwindcss": "0.6.5"
  }
}
```

### 6.2 Backend (requirements.txt)
```txt
Django==5.2.7
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.1
django-cors-headers==4.4.0
PyJWT==2.8.0
pyodbc==5.1.0
mssql-django==1.4
reportlab==4.2.0
PyPDF2==3.0.1
openpyxl==3.1.5
Pillow==10.4.0
python-dotenv==1.0.1
gunicorn==22.0.0
```

Install command:
```bash
pip install -r requirements.txt
```

---

## 7. Environment Configuration

### 7.1 Frontend (.env)
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8001/api/psc

# PWA Configuration
VITE_APP_NAME=PSC Inspection Module
VITE_APP_SHORT_NAME=PSC
```

### 7.2 Backend (.env)
```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQL Server)
DB_HOST=localhost
DB_NAME=ksm_marine_live
DB_USER=sa
DB_PASSWORD=your-password-here
DB_PORT=1433

# JWT Authentication (units: MINUTES)
JWT_ACCESS_TOKEN_LIFETIME=60          # 60 minutes = 1 hour
JWT_REFRESH_TOKEN_LIFETIME=43200      # 43200 minutes = 30 days

# File Upload
UPLOAD_BASE_PATH=/var/www/ksm_uploads
MAX_FILE_SIZE_MB=3

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 7.3 Django settings.py JWT Configuration
```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 60))),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 43200))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

---

## 8. Version Compatibility Matrix

| Frontend | Backend | Database | Status |
|----------|---------|----------|--------|
| React 18.3.1 + Vite 5.4.0 | Django 5.2.7 + DRF 3.14.0 | SQL Server 2019 | âœ… Tested |

---

## 9. Forbidden Packages

**DO NOT USE** these packages (common alternatives that conflict with our stack):

| Package | Reason | Use Instead |
|---------|--------|-------------|
| moment.js | Large bundle, deprecated | date-fns |
| redux | Over-engineered for this project | zustand + react-query |
| styled-components | Conflicts with Tailwind | Tailwind CSS |
| material-ui | Conflicts with shadcn/ui | shadcn/ui + Radix |
| localforage | Less control than idb | idb |
| swr | Already using react-query | @tanstack/react-query |
| formik | Already using react-hook-form | react-hook-form |
| yup | Already using zod | zod |
| WeasyPrint | Requires system deps | reportlab |
| xlsxwriter | Less features | openpyxl |

---

## Document References

| Document | Reference |
|----------|-----------|
| FRONTEND_GUIDELINES.md | How to use these packages |
| BACKEND_STRUCTURE.md | Django project structure |
| IMPLEMENTATION_PLAN.md | Installation steps |

---

**Document Control:**
- Created: 2026-02-04
- Author: System Generated
- Approved By: [Pending]
