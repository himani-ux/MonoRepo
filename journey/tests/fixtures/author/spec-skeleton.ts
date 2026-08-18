import { test, expect } from '@playwright/test';

// JOURNEY: <JOURNEY-ID> — "<title>"
// Authored BLIND from the author bundle (journey intent + TEST_SURFACE only).

test('<JOURNEY-ID> — <title>', async ({ page }) => {
  // step <n>. <exact step text from the journey>
  //   ...one comment per journey step, in order, code beneath each...
  // ORACLE: <exact oracle text from the journey — verbatim>
  //   ...at least one `await expect(...)` directly under the ORACLE comment...
});
