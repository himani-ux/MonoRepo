import { expectAnyTextVisible, loginAsJourneyUser, openRoute, requiredEnv, test } from './helpers';

test('JOURNEY-8: observation closure reaches master-close flow', async ({ page }) => {
  const findingId = requiredEnv('JOURNEY_OBS_FINDING_ID');
  await loginAsJourneyUser(page);
  await openRoute(page, `/audit/findings/${findingId}/obs`, /Observation|Master Close|Action Plan/i);
  await expectAnyTextVisible(page, [/Master Close/i, /Action Plan/i, /Save and Continue/i]);
});
