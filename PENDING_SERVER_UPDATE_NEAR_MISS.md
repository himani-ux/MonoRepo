# Pending Server Update: Near Miss

Do not deploy these near miss UI changes yet. Keep them pending and update together later.

## Latest Pending Changes

- Category dropdown no longer shows separate headings for `Category` and `Possible loss`.
- Category and possible loss options are shown together in one flat dropdown.
- Duplicate `Others` option was removed.
- Category dropdown keeps only `Other - Specify` at the bottom.
- Immediate cause custom option was moved into the dropdown as `Other - Specify`.
- Separate `Others - specify` button below Immediate cause was removed.

## Files To Update Later On Server

- `psc-frontend/src/components/safety/near-miss/near-miss-form.tsx`
- `psc-frontend/src/components/safety/shared/reference-pickers.tsx`

## Verification Done Locally

- `npm run type-check` passed in `psc-frontend`.
