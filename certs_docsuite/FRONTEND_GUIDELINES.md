# VIMS Certificates Module — Frontend Guidelines

> **Version:** 1.0
> **Last Updated:** 2026-05-13
> **Status:** Locked
> **Source:** APP_FLOW.md + TECH_STACK.md + DESIGN_SYSTEM.md + Reporting/Safety frontend patterns.

---

## 1. File Layout

```
src/
├── routes/certs/
│   ├── index.tsx                          # /certs (FleetDashboard)
│   ├── catalog/
│   │   ├── index.tsx                      # /certs/catalog
│   │   └── $catalogId.tsx                 # /certs/catalog/<id>
│   ├── vessels/
│   │   ├── index.tsx                      # /certs/vessels list
│   │   └── $imo/
│   │       ├── index.tsx                  # /certs/vessels/<imo>
│   │       ├── profile.tsx                # /certs/vessels/<imo>/profile
│   │       └── cert/
│   │           └── $trackedItemId.tsx     # /certs/vessels/<imo>/cert/<id>
│   ├── onboarding/
│   │   ├── index.tsx                      # /certs/onboarding (hub)
│   │   ├── $imo/
│   │   │   ├── index.tsx                  # /certs/onboarding/<imo> (wizard)
│   │   │   └── batch/
│   │   │       └── $batchId/
│   │   │           └── gap-fill.tsx       # gap-fill UI
│   ├── reconciliation/
│   │   ├── index.tsx
│   │   └── $runId.tsx
│   ├── print/
│   │   ├── index.tsx                      # builder
│   │   └── history.tsx
│   ├── share-bundle.tsx
│   ├── auditor-access/
│   │   ├── index.tsx
│   │   └── $grantId.tsx
│   ├── audit-log.tsx
│   └── settings.tsx
├── components/certs/
│   ├── shared/                            # All cross-screen primitives per DESIGN_SYSTEM §9
│   ├── catalog/
│   ├── onboarding/
│   ├── tracked-item/
│   ├── reconciliation/
│   ├── print/
│   ├── notifications/
│   ├── auditor-access/
│   └── audit-log/
├── hooks/certs/
│   ├── useCatalog.ts                      # TanStack Query hooks per endpoint
│   ├── useTrackedItem.ts
│   ├── useReconciliation.ts
│   ├── useOnboarding.ts
│   ├── usePrint.ts
│   ├── useNotifications.ts
│   ├── useAuditorAccess.ts
│   └── useAuditLog.ts
├── stores/certs/
│   ├── useOnboardingWizardStore.ts        # Zustand: wizard step state, draft batch state
│   ├── useGapFillStore.ts                 # Zustand: in-progress field overrides
│   ├── useReconciliationFilterStore.ts
│   ├── usePrintBuilderStore.ts
│   └── useCertsUiStore.ts                 # Misc UI toggles
└── schemas/certs/
    ├── catalog.ts                         # Zod schemas matching API + form validation
    ├── trackedItem.ts
    ├── ocr.ts
    └── ... (per domain)
```

Routing convention: TanStack Router file-based (matches Reporting + Safety).

---

## 2. Component Naming

- All Certs components start with `Cert*` — e.g. `CertOnboardingWizard.tsx`, `CertReconciliationPanel.tsx`, `CertGapFillForm.tsx`.
- Shared sub-components per `DESIGN_SYSTEM.md §9` live in `src/components/certs/shared/`.
- Page-level route components named `<Domain><Action>Page` — e.g. `CertCatalogListPage`, `CertTrackedItemDetailPage`.

---

## 3. State Management

| Concern | Solution |
|---------|----------|
| Server data | TanStack Query (React Query) — one hook per endpoint, no direct `fetch` in components |
| Form state | React Hook Form + Zod resolver (schemas in `src/schemas/certs/`) |
| Cross-screen UI state | Zustand store per sub-domain |
| Local UI state | `useState` — only for genuinely component-local toggles |
| URL state | TanStack Router search params + path params |

**Rules:**
- NEVER fetch in `useEffect` — always use a TanStack hook.
- NEVER store server data in Zustand — it has its own cache (TanStack Query).
- Zustand stores hold WIP form state, wizard step indices, filter selections, NEVER cached server response.
- All forms use React Hook Form + Zod (no uncontrolled inputs except media file pickers).

---

## 4. Data Fetching Patterns

### 4.1 Query keys
Pattern: `['certs', '<domain>', '<entity>', ...params]`

```ts
['certs', 'catalog', 'rows', { sectionId, isActive }]
['certs', 'tracked-items', 'list', { vesselId }]
['certs', 'tracked-items', 'detail', trackedItemId]
['certs', 'reconciliation', 'runs', { vesselId, classSociety }]
['certs', 'onboarding', vesselId]
['certs', 'auditor-access', 'list']
```

### 4.2 Mutations + invalidation
After any mutation, invalidate the affected query keys via `queryClient.invalidateQueries(['certs', '<domain>', ...])`. Keep invalidation scope minimal — don't invalidate `['certs']` wholesale.

### 4.3 Optimistic updates
Allowed for low-risk mutations (UI toggles, filter saves). Disallowed for write-paths to `vims_certs_tracked_item`, `vims_certs_audit_log`, `vims_certs_print_artifact`, `vims_certs_external_auditor_access` — these are compliance-critical; show pending state until server confirms.

### 4.4 Polling
- Default: stale-while-revalidate (TanStack Query default).
- Active batch OCR status: poll every 5s while status ∈ {queued, ocr_running}; stop polling on terminal states.
- Async print job: poll every 3s until status ∈ {success, failed}.
- Reconciliation run: do NOT poll — server-pushed via WebSocket if available, else stale-while-revalidate on focus.

---

## 5. The 4-State Contract

Every screen MUST implement four states (matches `APP_FLOW.md §5`):

```tsx
function MyPage() {
  const query = useMyData();
  if (query.isLoading) return <Skeleton variant="page" />;
  if (query.isError) return <ErrorBanner onRetry={query.refetch} />;
  if (query.data.length === 0) return <EmptyState ctaLabel="..." onCta={...} />;
  return <DataView data={query.data} />;
}
```

- **NEVER** blank screen.
- **NEVER** silent failure.
- Empty-filtered sub-state (results = 0 but filters applied): "No results — reset filters" CTA, not the true empty state.

---

## 6. Form Patterns

### 6.1 Standard form
```tsx
const schema = z.object({
  certificateNumber: z.string().min(1).max(128).nullable(),
  bypassCertNumber: z.boolean(),
  bypassReason: z.string().min(10).max(512).optional(),
  // ... per D-CERT-105
});

const form = useForm<z.infer<typeof schema>>({
  resolver: zodResolver(schema),
  defaultValues: ocrPayload ?? {},
});
```

### 6.2 Gap-fill form (OCR-driven)
- Pre-fill from `ocr_payload_json`.
- Per-field render highlights confidence band via `OcrConfidenceBadge`.
- "Save & next" within PDF carousel persists state to `useGapFillStore` between PDFs in a batch.
- "Commit batch" calls dry-run preview endpoint first (D-CERT-115), then commit.

### 6.3 Validation gates (D-CERT-116)
Validation runs in two places:
1. **Client-side** (React Hook Form + Zod) — instant feedback, blocks submit for required-field errors.
2. **Server-side** (DRF serializer) — authoritative; rejects with structured error → client surfaces in `ValidationBlocksDialog` or `ValidationWarnsDialog`.

Never rely on client-only validation for compliance gates — always re-validate server-side.

### 6.4 Confirmation dialogs (D-CERT-081)
For destructive actions: `ConfirmDialog` with named action + reversal path text:

```tsx
<ConfirmDialog
  title="Bulk soft-delete 12 catalog rows?"
  description="Rows will be marked inactive. Recoverable from audit log within 5y. Reason required."
  reasonRequired
  reasonMinLength={10}
  onConfirm={...}
/>
```

No 2FA / step-up reauth — just confirm + reason (per D-CERT-081).

---

## 7. RBAC Gating in UI

Use `useCertsPermission(form, process)` hook for visibility/disabled logic:

```tsx
const canCatalogEdit = useCertsPermission('CERT_F_001', 'CERT_P_008');
if (!canCatalogEdit) return <ReadOnlyView />;
```

Permissions are server-driven (`msc_profiles` per D-CERT-090); hook fetches once on session start, cached in TanStack Query.

**Never hide audit-log entries client-side based on role** — server returns only what the role is allowed to see.

---

## 8. Online-Required UX (D-CERT-156)

- Detect offline via `navigator.onLine` + ping `/api/health/`.
- Offline banner at top of viewport: "You're offline — Certs is online-required. Reconnect to continue."
- Active mutations queue locally for 30s then fail with retry suggestion.
- NO IndexedDB caching, NO service worker write-queue.
- Session re-auth (D-CERT-082): PMS-style modal overlay (NOT redirect); preserves form state in Zustand; 15-min + 5-min toast warnings before timeout.

---

## 9. Notification UX (per D-CERT-161)

- Shared bell icon in platform top-bar (existing component) — Certs entries merged via `module=certs` filter.
- Magic-link landing (`/api/certs/notifications/ack/<token>/`) renders a server-side HTML page → redirects to the cert detail with success toast.
- Per-side routing is enforced server-side; UI just renders whatever the inbox query returns.

---

## 10. Print / Share-Bundle UX

- Sync per-vessel: progress bar with "Generating PDF (page X of Y)..." (D-CERT-144). Hard cap 60s; on timeout, surface "Generation timed out — try a narrower scope or contact support" + auto-create support ticket via D-CERT-150 mechanism.
- Async fleet-wide: queue, ETA, in-app notification on complete.
- Auto-archive every print artifact (D-CERT-149) — visible in `/certs/print/history`.
- Normal Print certs status uses the current vessel context and one single-select Certificate sections dropdown. `All sections` prints the full vessel status; selecting one section prints every certificate in that section. Do not show individual certificate choices, Buckets/Add Vessel filters, Scope, Status, Sections, Watermark, or Recipient fields in the normal print screen (D-CERT-208, D-CERT-209, D-CERT-210, D-CERT-211).
- Share Bundle remains separate: certificate-section multi-select with Select all / Clear all, recipient name, recipient email validation, ZIP download, and optional email delivery. Do not list individual certificates in the normal share screen.

---

## 11. PDF Preview

Use `<embed>` or `<object>` for inline PDF preview. Fallback to native viewer link on iOS Safari (some versions block embed). Download button always present alongside preview.

---

## 12. Slack Routing UX (D-CERT-160)

- DPA central config on `/certs/settings` (Slack tab) + per-vessel on `/certs/vessels/<imo>/profile`.
- UI shows current channel mappings; "Test message to this channel" button writes a server-side test event.
- Vessel users never see Slack config (their notifications never route to Slack per D-CERT-161).

---

## 13. Performance

- Code-split per route via TanStack Router lazy imports.
- Reconciliation review tabs: virtualize long flag lists (>50 rows) with `react-window` or equivalent.
- Catalog Admin: fetch catalog rows with `page/pageSize`; render the first page before loading later pages in the background.
- Audit log table: server-side pagination 25 rows; never load full table client-side.
- Print artifact list: server-side pagination 25 rows.
- PDF preview: lazy-load (`loading="lazy"` on embed) until row expanded.

---

## 14. Error Handling

- Network errors: TanStack `onError` → `toast.error('Connection issue — retrying...')` with retry indicator.
- 401/403: redirect to login (re-auth modal handles in-session).
- 422 (validation): surface field-level errors in form; map to React Hook Form `setError`.
- 5xx: full-screen error boundary with "Something broke. Please retry. If it persists, contact support." + auto-report to support endpoint.

---

## 15. Testing

- Unit: vitest for hooks + utilities.
- Component: vitest + @testing-library/react.
- E2E: Playwright (per platform convention).
- **Mandatory E2E coverage:**
  - 7-step onboarding wizard end-to-end on a fresh vessel.
  - OCR confidence-band gap-fill UX (mocked OCR engine returning specific confidence payloads).
  - Approval state machine (draft → submit → approve / reject).
  - Per-side notification routing (vessel mock + office mock; assert correct channels appear).
  - Print artifact generation + audit log entry presence.
  - External auditor portal token flow + redaction enforcement.
- Snapshot tests for `CertStatusBadge` × 13 variants (per DESIGN_SYSTEM §2/§3).

---

## 16. Accessibility

- Mandatory keyboard nav for every interactive element.
- ARIA labels for all icon-only buttons.
- Focus trap inside modals and re-auth overlay.
- `aria-live="polite"` for OCR completion + reconciliation status changes.
- Color-blind verified via Storybook a11y addon.

---

*End of FRONTEND_GUIDELINES v1.0.*

---

## Appendix — Decisions Index Backfill

> **Audit traceability (2026-05-13):** the following D-CERT-\* IDs are referenced by `COVERAGE.md` as in-scope for `FRONTEND_GUIDELINES.md` but were not literally cited inline in earlier prose. They are listed here as an audit-grade citation index so every `COVERAGE.md` ✓ resolves to a literal grep match against this doc. Decision text remains binding from `../VIMS-CERTIFICATES-MODULE-SSOT.md` §16; this index points back to the SSOT row.

| Decision ID | SSOT topic (terse) | Status |
|-------------|--------------------|--------|
| D-CERT-106 | OCR confidence handling — three-mode fallback. | LOCKED |
| D-CERT-123 | OCR processing = async per batch. | LOCKED |
| D-CERT-154 | Email-to-action = magic-link one-click ack. | LOCKED |
