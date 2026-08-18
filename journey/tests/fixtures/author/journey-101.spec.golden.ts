import { test, expect } from '@playwright/test';

// JOURNEY: JOURNEY-101 — "Corrected invoice upload accepted"
// Authored BLIND from the author bundle (journey intent + TEST_SURFACE only).

test('JOURNEY-101 — Corrected invoice upload accepted', async ({ page }) => {
  // step 1. land on /invoices (state: EMPTY)
  await page.goto('/invoices');
  // step 2. upload malformed.csv -> schema_error displayed inline
  await page.getByTestId('upload-input').setInputFiles({
    name: 'malformed.csv', mimeType: 'text/csv', buffer: Buffer.from('bad,data'),
  });
  await expect(page.getByTestId('upload-error')).toBeVisible();
  // step 3. fix the CSV locally, re-upload corrected.csv
  await page.getByTestId('upload-input').setInputFiles({
    name: 'corrected.csv', mimeType: 'text/csv', buffer: Buffer.from('file,amount\ncorrected.csv,100'),
  });
  // step 4. observe status=ACCEPTED in the invoice list
  // ORACLE: the row shows status=ACCEPTED AND the file appears in the invoice list immediately after upload
  await expect(page.getByTestId('invoice-list')).toContainText('corrected.csv');
  await expect(page.getByTestId('invoice-status').filter({ hasText: 'ACCEPTED' }).first()).toBeVisible();
});
