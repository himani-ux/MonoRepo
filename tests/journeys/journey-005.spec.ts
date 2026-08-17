import { expectAnyTextVisible, loginAsJourneyUser, openRoute, requiredEnv, test } from './helpers';

test('JOURNEY-5: master signature/backdate controls are visible on NC closure form', async ({ page }) => {
  const findingId = requiredEnv('JOURNEY_NC_FINDING_ID');
  await loginAsJourneyUser(page);
  await openRoute(page, `/audit/findings/${findingId}/nc`, /NC Closure|Corrective|Part/i);
  await expectAnyTextVisible(page, [/Master \/ HoD Signer/i, /signature/i, /signed/i, /backdate/i]);
});
