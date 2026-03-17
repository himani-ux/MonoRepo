# VIMS Inspection - Tech Stack Summary

> **Note**: TECH_STACK.md in Docs/ is the canonical source. All versions are LOCKED.

## Frontend Stack
| Package | Version | Purpose |
|---------|---------|---------|
| React | 18.3.1 | UI framework |
| TypeScript | 5.4.5 | Type safety |
| Vite | 5.4.0 | Build tool & dev server |
| Tailwind CSS | 3.4.7 | Utility-first styling |
| TanStack Query | 5.51.1 | Server state management |
| Zustand | 4.5.4 | Client state management |
| React Hook Form | 7.52.1 | Form handling |
| Zod | 3.23.8 | Schema validation |
| Radix UI | Various | Accessible primitives (shadcn/ui) |
| Axios | 1.7.2 | HTTP client |
| date-fns | 3.6.0 | Date utilities |
| Workbox | 7.1.0 | PWA/offline support |
| idb | 8.0.0 | IndexedDB wrapper |
| Lucide React | 0.408.0 | Icons |

## Backend Stack
| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.12.4 | Runtime |
| Django | 5.2.7 | Web framework |
| Django REST Framework | 3.14.0 | REST API |
| mssql-django | 1.4 | SQL Server backend |
| djangorestframework-simplejwt | 5.3.1 | JWT authentication |
| reportlab | 4.2.0 | PDF generation |
| openpyxl | 3.1.5 | Excel generation |

## Database
- SQL Server 2019
- Database: `ksm_marine_live` (shared with CMS)
- ODBC Driver 17 or 18

## Forbidden Packages
Do NOT use: moment.js, redux, styled-components, material-ui, localforage, swr, formik, yup

## Runtime Requirements
- Node.js 22.17.1
- npm 10.x
- Browsers: Chrome 90+, Safari 14+, Edge 90+, Firefox 90+
