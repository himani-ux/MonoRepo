# DESIGN_SYSTEM.md — Visual Language & Design Tokens
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.0 | **Date:** 2026-02-03

---

## 1. Color Palette

### 1.1 Primary Colors
| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `primary-50` | #EFF6FF | rgb(239, 246, 255) | Primary tint, hover backgrounds |
| `primary-100` | #DBEAFE | rgb(219, 234, 254) | Selected state backgrounds |
| `primary-200` | #BFDBFE | rgb(191, 219, 254) | Focus rings |
| `primary-300` | #93C5FD | rgb(147, 197, 253) | Borders on hover |
| `primary-400` | #60A5FA | rgb(96, 165, 250) | Icons, secondary actions |
| `primary-500` | #3B82F6 | rgb(59, 130, 246) | **Primary buttons, links, active states** |
| `primary-600` | #2563EB | rgb(37, 99, 235) | **Primary button hover** |
| `primary-700` | #1D4ED8 | rgb(29, 78, 216) | Primary button pressed |
| `primary-800` | #1E40AF | rgb(30, 64, 175) | Dark accents |
| `primary-900` | #1E3A8A | rgb(30, 58, 138) | Darkest primary |

### 1.2 Neutral Colors
| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `neutral-50` | #F9FAFB | rgb(249, 250, 251) | **Page background** |
| `neutral-100` | #F3F4F6 | rgb(243, 244, 246) | Card background alt, dividers |
| `neutral-200` | #E5E7EB | rgb(229, 231, 235) | **Borders, disabled backgrounds** |
| `neutral-300` | #D1D5DB | rgb(209, 213, 219) | Input borders |
| `neutral-400` | #9CA3AF | rgb(156, 163, 175) | Placeholder text, icons disabled |
| `neutral-500` | #6B7280 | rgb(107, 114, 128) | **Secondary text** |
| `neutral-600` | #4B5563 | rgb(75, 85, 99) | Icons |
| `neutral-700` | #374151 | rgb(55, 65, 81) | **Body text** |
| `neutral-800` | #1F2937 | rgb(31, 41, 55) | **Headings** |
| `neutral-900` | #111827 | rgb(17, 24, 39) | Darkest text |

### 1.3 Semantic Colors

#### Success
| Token | Hex | Usage |
|-------|-----|-------|
| `success-50` | #ECFDF5 | Success background |
| `success-100` | #D1FAE5 | Success badge background |
| `success-500` | #10B981 | **Success text, icons** |
| `success-600` | #059669 | Success button |
| `success-700` | #047857 | Success button hover |

#### Warning
| Token | Hex | Usage |
|-------|-----|-------|
| `warning-50` | #FFFBEB | Warning background |
| `warning-100` | #FEF3C7 | Warning badge background |
| `warning-500` | #F59E0B | **Warning text, icons** |
| `warning-600` | #D97706 | Warning button |
| `warning-700` | #B45309 | Warning button hover |

#### Error / Danger
| Token | Hex | Usage |
|-------|-----|-------|
| `error-50` | #FEF2F2 | Error background |
| `error-100` | #FEE2E2 | Error badge background, **detention row** |
| `error-500` | #EF4444 | **Error text, validation, overdue** |
| `error-600` | #DC2626 | Destructive button |
| `error-700` | #B91C1C | Destructive button hover |

#### Info
| Token | Hex | Usage |
|-------|-----|-------|
| `info-50` | #EFF6FF | Info background |
| `info-100` | #DBEAFE | Info badge background |
| `info-500` | #3B82F6 | Info text, icons |

### 1.4 Status Badge Colors
| Status | Background | Text | Border |
|--------|------------|------|--------|
| DRAFT | `neutral-100` | `neutral-700` | `neutral-300` |
| SUBMITTED | `primary-100` | `primary-700` | `primary-300` |
| PIC_REVIEWED | `info-100` | `info-700` | `info-300` |
| PIC_ACCEPTED | `info-100` | `info-700` | `info-300` |
| REWORK_REQUESTED | `warning-100` | `warning-700` | `warning-300` |
| DPA_CLOSED | `success-100` | `success-700` | `success-300` |
| OVERDUE | `error-100` | `error-700` | `error-300` |
| DETENTION | `error-100` | `error-700` | `error-500` (2px) |

### 1.5 Surface Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `surface-page` | #F9FAFB | Page background |
| `surface-card` | #FFFFFF | Card backgrounds |
| `surface-elevated` | #FFFFFF | Modal, dropdown backgrounds |
| `surface-overlay` | rgba(0,0,0,0.5) | Modal overlay |

---

## 2. Typography

### 2.1 Font Stack
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, 'Courier New', monospace;
```

### 2.2 Type Scale
| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `text-xs` | 12px (0.75rem) | 16px (1rem) | 400 | Captions, timestamps |
| `text-sm` | 14px (0.875rem) | 20px (1.25rem) | 400 | Secondary text, labels |
| `text-base` | 16px (1rem) | 24px (1.5rem) | 400 | **Body text default** |
| `text-lg` | 18px (1.125rem) | 28px (1.75rem) | 500 | Card titles |
| `text-xl` | 20px (1.25rem) | 28px (1.75rem) | 600 | Section headers |
| `text-2xl` | 24px (1.5rem) | 32px (2rem) | 600 | Page titles |
| `text-3xl` | 30px (1.875rem) | 36px (2.25rem) | 700 | Hero text |

### 2.3 Font Weights
| Token | Value | Usage |
|-------|-------|-------|
| `font-normal` | 400 | Body text |
| `font-medium` | 500 | Emphasized text, labels |
| `font-semibold` | 600 | Headings, buttons |
| `font-bold` | 700 | Hero text, important headings |

### 2.4 Text Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `text-primary` | #1F2937 (neutral-800) | Headings |
| `text-secondary` | #6B7280 (neutral-500) | Secondary text |
| `text-tertiary` | #9CA3AF (neutral-400) | Placeholder, disabled |
| `text-inverse` | #FFFFFF | Text on dark backgrounds |
| `text-link` | #3B82F6 (primary-500) | Links |
| `text-link-hover` | #2563EB (primary-600) | Link hover |
| `text-error` | #EF4444 (error-500) | Error messages |
| `text-success` | #10B981 (success-500) | Success messages |

---

## 3. Spacing Scale

Base unit: **4px**

| Token | Value | Usage |
|-------|-------|-------|
| `space-0` | 0px | Reset |
| `space-0.5` | 2px | Micro spacing |
| `space-1` | 4px | Icon gaps, tight spacing |
| `space-1.5` | 6px | Small gaps |
| `space-2` | 8px | **Inline element gaps** |
| `space-2.5` | 10px | Compact padding |
| `space-3` | 12px | **Component internal padding** |
| `space-4` | 16px | **Default padding, gaps** |
| `space-5` | 20px | Medium spacing |
| `space-6` | 24px | **Section spacing** |
| `space-8` | 32px | Large section spacing |
| `space-10` | 40px | Extra large spacing |
| `space-12` | 48px | Page section spacing |
| `space-16` | 64px | Major section breaks |
| `space-20` | 80px | Hero spacing |
| `space-24` | 96px | Maximum spacing |

### 3.1 Component Spacing Patterns
| Component | Padding | Gap |
|-----------|---------|-----|
| Button (sm) | 8px 12px | 6px |
| Button (md) | 10px 16px | 8px |
| Button (lg) | 12px 20px | 10px |
| Input | 10px 12px | - |
| Card | 16px | 12px |
| Card (compact) | 12px | 8px |
| Modal | 24px | 16px |
| Section | 24px 0 | 16px |
| Page | 16px (mobile), 24px (desktop) | 24px |

---

## 4. Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-none` | 0px | Square corners |
| `radius-sm` | 4px | Small elements, badges |
| `radius-md` | 6px | **Buttons, inputs** |
| `radius-lg` | 8px | **Cards** |
| `radius-xl` | 12px | Modals, large cards |
| `radius-2xl` | 16px | Large containers |
| `radius-full` | 9999px | Pills, avatars |

---

## 5. Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-none` | none | No shadow |
| `shadow-sm` | 0 1px 2px rgba(0,0,0,0.05) | Subtle depth |
| `shadow-md` | 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1) | **Cards** |
| `shadow-lg` | 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1) | **Dropdowns, elevated cards** |
| `shadow-xl` | 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1) | **Modals** |
| `shadow-inner` | inset 0 2px 4px rgba(0,0,0,0.05) | Inset elements |

---

## 6. Borders

| Token | Value | Usage |
|-------|-------|-------|
| `border-width-0` | 0px | No border |
| `border-width-1` | 1px | **Default borders** |
| `border-width-2` | 2px | Focus rings, emphasis |
| `border-width-4` | 4px | Strong emphasis (detention) |

### 6.1 Border Colors
| Token | Hex | Usage |
|-------|-----|-------|
| `border-default` | #E5E7EB (neutral-200) | **Default borders** |
| `border-strong` | #D1D5DB (neutral-300) | Input borders |
| `border-focus` | #3B82F6 (primary-500) | Focus state |
| `border-error` | #EF4444 (error-500) | Error state |
| `border-success` | #10B981 (success-500) | Success state |

---

## 7. Breakpoints

| Token | Value | Description |
|-------|-------|-------------|
| `screen-sm` | 640px | Small devices (landscape phones) |
| `screen-md` | 768px | **Tablets** |
| `screen-lg` | 1024px | **Desktops** |
| `screen-xl` | 1280px | Large desktops |
| `screen-2xl` | 1536px | Extra large screens |

### 7.1 Container Widths
| Breakpoint | Max Width | Padding |
|------------|-----------|---------|
| Default (mobile) | 100% | 16px |
| sm (640px+) | 100% | 24px |
| md (768px+) | 100% | 32px |
| lg (1024px+) | 1024px | 32px |
| xl (1280px+) | 1152px | 32px |

### 7.2 Responsive Patterns
```
Mobile First Approach:
- Start with mobile layout (< 768px)
- Enhance for tablet (768px+)
- Enhance for desktop (1024px+)

Layout Shifts:
- Navigation: Bottom tabs (mobile) → Sidebar (desktop)
- Card grid: 1 column (mobile) → 2 columns (tablet) → 3 columns (desktop)
- Form layout: Single column (mobile) → Two column (desktop)
```

---

## 8. Animation & Transitions

### 8.1 Duration
| Token | Value | Usage |
|-------|-------|-------|
| `duration-75` | 75ms | Micro interactions |
| `duration-100` | 100ms | Hover states |
| `duration-150` | 150ms | **Button hover, focus** |
| `duration-200` | 200ms | **Default transitions** |
| `duration-300` | 300ms | **Modal open/close** |
| `duration-500` | 500ms | Page transitions |

### 8.2 Easing
| Token | Value | Usage |
|-------|-------|-------|
| `ease-linear` | linear | Progress bars |
| `ease-in` | cubic-bezier(0.4, 0, 1, 1) | Exit animations |
| `ease-out` | cubic-bezier(0, 0, 0.2, 1) | **Enter animations** |
| `ease-in-out` | cubic-bezier(0.4, 0, 0.2, 1) | **Default** |

### 8.3 Common Transitions
```css
/* Button hover */
transition: background-color 150ms ease-in-out, 
            border-color 150ms ease-in-out,
            box-shadow 150ms ease-in-out;

/* Input focus */
transition: border-color 200ms ease-out, 
            box-shadow 200ms ease-out;

/* Card hover */
transition: box-shadow 200ms ease-out,
            transform 200ms ease-out;

/* Modal */
transition: opacity 300ms ease-out, 
            transform 300ms ease-out;
```

---

## 9. Z-Index Scale

| Token | Value | Usage |
|-------|-------|-------|
| `z-0` | 0 | Default |
| `z-10` | 10 | Raised elements |
| `z-20` | 20 | Dropdowns |
| `z-30` | 30 | Sticky headers |
| `z-40` | 40 | Fixed navigation |
| `z-50` | 50 | **Modals, overlays** |
| `z-60` | 60 | Toasts, notifications |
| `z-max` | 9999 | Critical overlays |

---

## 10. Icons

### 10.1 Icon Library
**Primary:** Lucide React (lucide-react@0.408.0)

### 10.2 Icon Sizes
| Token | Size | Usage |
|-------|------|-------|
| `icon-xs` | 12px | Inline with small text |
| `icon-sm` | 16px | Inline with body text |
| `icon-md` | 20px | **Buttons, inputs** |
| `icon-lg` | 24px | **Card icons, navigation** |
| `icon-xl` | 32px | Empty states |
| `icon-2xl` | 48px | Hero illustrations |

### 10.3 Common Icons
| Usage | Icon | Lucide Name |
|-------|------|-------------|
| Add/Create | ➕ | `Plus` |
| Edit | ✏️ | `Pencil` |
| Delete | 🗑️ | `Trash2` |
| View | 👁️ | `Eye` |
| Download | 📥 | `Download` |
| Upload | 📤 | `Upload` |
| Search | 🔍 | `Search` |
| Filter | 🔽 | `Filter` |
| Close | ✕ | `X` |
| Check | ✓ | `Check` |
| Warning | ⚠️ | `AlertTriangle` |
| Error | ❌ | `AlertCircle` |
| Info | ℹ️ | `Info` |
| Success | ✅ | `CheckCircle` |
| Vessel | 🚢 | `Ship` |
| Document | 📄 | `FileText` |
| Image | 🖼️ | `Image` |
| Calendar | 📅 | `Calendar` |
| User | 👤 | `User` |
| Settings | ⚙️ | `Settings` |
| Notification | 🔔 | `Bell` |
| Sync | 🔄 | `RefreshCw` |
| Offline | 📴 | `WifiOff` |
| Online | 🟢 | `Wifi` |

---

## 11. Component Tokens

### 11.1 Button
```
Primary Button:
  - Background: primary-500
  - Background Hover: primary-600
  - Background Active: primary-700
  - Text: white
  - Border Radius: radius-md (6px)
  - Padding: 10px 16px
  - Font: text-sm, font-semibold
  - Shadow: none
  - Transition: 150ms ease-in-out

Secondary Button:
  - Background: white
  - Background Hover: neutral-50
  - Border: 1px solid neutral-300
  - Text: neutral-700
  
Destructive Button:
  - Background: error-600
  - Background Hover: error-700
  - Text: white

Ghost Button:
  - Background: transparent
  - Background Hover: neutral-100
  - Text: neutral-700

Disabled Button:
  - Background: neutral-100
  - Text: neutral-400
  - Cursor: not-allowed
```

### 11.2 Input
```
Default Input:
  - Background: white
  - Border: 1px solid neutral-300
  - Border Radius: radius-md (6px)
  - Padding: 10px 12px
  - Font: text-base
  - Text: neutral-800
  - Placeholder: neutral-400

Focus State:
  - Border: 1px solid primary-500
  - Ring: 0 0 0 3px primary-100

Error State:
  - Border: 1px solid error-500
  - Ring: 0 0 0 3px error-100

Disabled State:
  - Background: neutral-100
  - Text: neutral-400
```

### 11.3 Card
```
Default Card:
  - Background: surface-card (white)
  - Border: 1px solid neutral-200
  - Border Radius: radius-lg (8px)
  - Padding: 16px
  - Shadow: shadow-md

Clickable Card (Hover):
  - Shadow: shadow-lg
  - Transform: translateY(-2px)
  
Detention Card:
  - Border Left: 4px solid error-500
  - Background: error-50
```

### 11.4 Badge
```
Default Badge:
  - Padding: 2px 8px
  - Border Radius: radius-full (pill)
  - Font: text-xs, font-medium
  - Text Transform: uppercase

Status-specific colors per section 1.4
```

### 11.5 Modal
```
Overlay:
  - Background: surface-overlay (rgba(0,0,0,0.5))
  - Z-Index: z-50

Dialog:
  - Background: surface-elevated (white)
  - Border Radius: radius-xl (12px)
  - Shadow: shadow-xl
  - Padding: 24px
  - Max Width: 500px (sm), 640px (md), 800px (lg)
  - Animation: fade in + scale up, 300ms ease-out
```

---

## 12. PDF Report Styling

Per KLOSS_REMEDIATION_PACK_v3.md Part 8:

```
Page Setup:
  - Size: A4 (210mm × 297mm)
  - Orientation: Portrait
  - Margins: Top 20mm, Bottom 15mm, Left 15mm, Right 15mm

Fonts:
  - Primary: Arial
  - Body: 10pt
  - Headings: 12pt bold
  - Title: 14pt bold

Header:
  - Logo: 30mm × 15mm, top left
  - Title: Centered
  - CAR No: Top right, 12pt bold

Table Styling:
  - Header Row: Bold, #D6EAF8 background
  - Alternating Rows: White / #F8F9FA
  - Detention Rows: #FADBD8 background
  - Borders: 0.5pt solid #D1D5DB
```

---

## 13. Dark Mode (Future)

Reserved tokens for future dark mode implementation:

```
Dark Mode Colors:
  - surface-page: #111827
  - surface-card: #1F2937
  - text-primary: #F9FAFB
  - text-secondary: #9CA3AF
  - border-default: #374151
```

---

## 14. Document References

| Document | Reference |
|----------|-----------|
| FRONTEND_GUIDELINES.md | Component implementation using these tokens |
| APP_FLOW.md | Screen layouts using these patterns |
| TECH_STACK.md | Tailwind CSS version (3.4.7) |
| Tailwind Config | Map tokens to Tailwind classes |

---

**Document Control:**
- Created: 2026-02-03
- Updated: 2026-02-04
- Author: System Generated
- Design System Version: 1.0
