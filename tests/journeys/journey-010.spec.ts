import { expectAnyTextVisible, loginAsJourneyUser, openRoute, test } from './helpers';

test('JOURNEY-10: additional audit creation surface is present and separated from routine plan', async ({ page }) => {
  await loginAsJourneyUser(page);
  await openRoute(page, '/audit/plans', /Audit Plan Register/i);
  await expectAnyTextVisible(page, [/Create additional audit/i, /Additional reason/i, /Trigger type/i, /Additional/i]);
});
