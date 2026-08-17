import { expectAnyTextVisible, loginAsJourneyUser, openRoute, test } from './helpers';

test('JOURNEY-9: OPM F 713 extension/cancellation controls are present in plan register', async ({ page }) => {
  await loginAsJourneyUser(page);
  await openRoute(page, '/audit/plans', /Audit Plan Register/i);
  await expectAnyTextVisible(page, [/OPM F 713/i, /Request extension/i, /Cancel/i, /Extension/i]);
});
