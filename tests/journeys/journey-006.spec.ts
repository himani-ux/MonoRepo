import { expectAnyTextVisible, loginAsJourneyUser, openRoute, requiredEnv, test } from './helpers';

test('JOURNEY-6: office/PIC NC closure form exposes office drafting and PIC review surface', async ({ page }) => {
  const findingId = requiredEnv('JOURNEY_NC_FINDING_ID');
  await loginAsJourneyUser(page);
  await openRoute(page, `/audit/findings/${findingId}/nc`, /NC Closure|Corrective|Part/i);
  await expectAnyTextVisible(page, [/PIC/i, /Office/i, /Review/i, /Draft/i]);
});
