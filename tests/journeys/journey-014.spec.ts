import { expectAnyTextVisible, loginAsJourneyUser, openRoute, requiredEnv, test } from './helpers';

test('JOURNEY-14: acting-HoD assignment route is reachable when implemented', async ({ page }) => {
  const route = requiredEnv('JOURNEY_ACTING_HOD_ROUTE');
  await loginAsJourneyUser(page);
  await openRoute(page, route, /Acting|HoD|Coverage/i);
  await expectAnyTextVisible(page, [/Acting/i, /HoD/i, /effective/i, /department/i]);
});
