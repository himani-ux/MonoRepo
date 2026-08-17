import { expectAnyTextVisible, loginAsJourneyUser, openRoute, test } from './helpers';

test('JOURNEY-11: DPA failed-notification and scan-validation queues are reachable', async ({ page }) => {
  await loginAsJourneyUser(page);
  await openRoute(page, '/dpa/notifications/failed', /Failed Notifications/i);
  await expectAnyTextVisible(page, [/Failed notifications/i, /Retry/i, /notified offline/i, /No failed notifications/i]);

  await openRoute(page, '/dpa/scan-validation-queue', /Scan Validation Queue/i);
  await expectAnyTextVisible(page, [/Scan-validation queue/i, /Accept/i, /rescan/i, /No scan mismatches/i]);
});
