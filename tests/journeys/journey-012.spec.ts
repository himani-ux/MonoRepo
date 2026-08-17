import { expectAnyTextVisible, loginAsJourneyUser, openRoute, requiredEnv, test } from './helpers';

test('JOURNEY-12: external audit registration and optional close-out route are reachable', async ({ page }) => {
  await loginAsJourneyUser(page);
  await openRoute(page, '/audit/external/new', /External Audit/i);
  await expectAnyTextVisible(page, [/External Audit Definition/i, /External Audit Org UUID/i, /External Lead Auditor/i, /Register External Audit/i]);

  const externalAuditId = process.env.JOURNEY_EXTERNAL_AUDIT_ID;
  if (!externalAuditId) return;

  await openRoute(page, `/audit/external/${requiredEnv('JOURNEY_EXTERNAL_AUDIT_ID')}`, /External Audit/i);
  await expectAnyTextVisible(page, [/External Audit Close-out/i, /certificate impact/i, /Confirm External Closure/i]);
});
