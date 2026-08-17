import { expectAnyTextVisible, expectAuditSidebar, loginAsJourneyUser, openRoute, test } from './helpers';

test('JOURNEY-1: SEQ/DPA can open audit plan register and see planning controls', async ({ page }) => {
  await loginAsJourneyUser(page);
  await openRoute(page, '/audit/plans', /Audit Plan Register/i);
  await expectAuditSidebar(page, ['Audit Plans', 'Register Audit']);
  await expectAnyTextVisible(page, [/Create routine plan entry/i, /Register rows/i, /OPM F 713/i]);
});
