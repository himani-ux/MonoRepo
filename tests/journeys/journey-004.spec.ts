import { expectAnyTextVisible, loginAsJourneyUser, openRoute, requiredEnv, test } from './helpers';

test('JOURNEY-4: crew action owner can open NC wizard draft workflow', async ({ page }) => {
  const findingId = requiredEnv('JOURNEY_NC_FINDING_ID');
  await loginAsJourneyUser(page);
  await openRoute(page, `/audit/findings/${findingId}/nc/wizard`, /wizard|root cause|corrective/i);
  await expectAnyTextVisible(page, [/Root Cause/i, /Save and Continue/i, /RCA/i, /wizard/i]);
});
