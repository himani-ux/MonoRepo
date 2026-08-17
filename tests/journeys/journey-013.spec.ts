import { expectAnyTextVisible, loginAsJourneyUser, openRoute, test } from './helpers';

test('JOURNEY-13: office-department audit registration controls are visible', async ({ page }) => {
  await loginAsJourneyUser(page);
  await openRoute(page, '/inspections/new', /register audit|new inspection|audit/i);
  await page.locator('#auditee_type').click();
  await page.getByRole('option', { name: /Office Department/i }).click();
  await expectAnyTextVisible(page, [/Office Department/i, /OFFICE_DEPT/i, /Department/i, /Audit Scope/i]);
});
