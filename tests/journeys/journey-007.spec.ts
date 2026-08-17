import { expectAnyTextVisible, loginAsJourneyUser, openRoute, requiredEnv, test } from './helpers';

test('JOURNEY-7: lead-auditor verification and effectiveness review surface is reachable', async ({ page }) => {
  const findingId = requiredEnv('JOURNEY_NC_FINDING_ID');
  await loginAsJourneyUser(page);
  await openRoute(page, `/audit/findings/${findingId}/nc`, /NC Closure|Corrective|Part/i);
  await expectAnyTextVisible(page, [/Effectiveness/i, /Verification/i, /Lead Auditor/i, /Review Method/i]);
});
