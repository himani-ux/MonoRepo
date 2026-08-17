import { expectAnyTextVisible, expectAuditSidebar, loginAsJourneyUser, openRoute, test } from './helpers';

test('JOURNEY-2: conductor can reach register-audit branch and checklist entry route', async ({ page }) => {
  await loginAsJourneyUser(page);
  await openRoute(page, '/inspections/new', /register audit|new inspection|audit/i);
  await expectAuditSidebar(page, ['Register Audit']);
  await expectAnyTextVisible(page, [/Audit Classification/i, /Audit Subtype/i, /Lead Auditor/i, /Register Audit/i]);
});
