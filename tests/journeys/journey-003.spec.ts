import { expectAnyTextVisible, loginAsJourneyUser, openRoute, requiredEnv, test } from './helpers';

test('JOURNEY-3: audit detail exposes submit gates and acknowledgement surface', async ({ page }) => {
  const auditId = requiredEnv('JOURNEY_AUDIT_ID');
  await loginAsJourneyUser(page);
  await openRoute(page, `/audit/audits/${auditId}`, /audit/i);
  await expectAnyTextVisible(page, [/Submit/i, /Scorecard/i, /Vessel Acknowledge/i, /findings/i]);
});
