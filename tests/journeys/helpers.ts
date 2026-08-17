import { expect, type Page, test } from '../../journey/surface-check/node_modules/@playwright/test';

const DEFAULT_TIMEOUT = 15000;

export function requireCredentials() {
  const missing = ['JOURNEY_USERNAME', 'JOURNEY_PASSWORD'].filter((name) => !process.env[name]);
  test.skip(
    missing.length > 0,
    `Set ${missing.join(', ')} before running audit journey tests.`
  );
}

export function requiredEnv(name: string): string {
  const value = process.env[name];
  test.skip(!value, `Set ${name} to run this record-specific journey.`);
  return value || '';
}

export async function loginAsJourneyUser(page: Page) {
  requireCredentials();

  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle').catch(() => undefined);

  const username = page.getByLabel(/username/i).or(page.getByPlaceholder(/username/i)).first();
  if (await username.isVisible().catch(() => false)) {
    await username.fill(process.env.JOURNEY_USERNAME || '');
    await page.getByLabel(/password/i).or(page.getByPlaceholder(/password/i)).first().fill(process.env.JOURNEY_PASSWORD || '');
    await page.getByRole('button', { name: /login|sign in/i }).click();
  }

  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: DEFAULT_TIMEOUT });
}

export async function openRoute(page: Page, route: string, expectedText: string | RegExp) {
  await page.goto(route, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle').catch(() => undefined);

  if (new URL(page.url()).pathname.includes('/login')) {
    throw new Error(`Route ${route} redirected to login. Check credentials/session.`);
  }

  await expectNoPermissionBlock(page, route);
  await expectTextVisible(page, expectedText);
}

export async function expectNoPermissionBlock(page: Page, context: string) {
  const denied = page.getByText(/access denied|you do not have permission|permission denied/i).first();
  if (await denied.isVisible().catch(() => false)) {
    throw new Error(`${context} is blocked by permissions for JOURNEY_USERNAME.`);
  }
}

export async function expectTextVisible(page: Page, text: string | RegExp) {
  await expect(page.getByText(text).first()).toBeVisible({ timeout: DEFAULT_TIMEOUT });
}

export async function expectAnyTextVisible(page: Page, texts: Array<string | RegExp>) {
  const failures: string[] = [];
  for (const text of texts) {
    const locator = page.getByText(text).first();
    try {
      await locator.waitFor({ state: 'visible', timeout: 2500 });
      return;
    } catch {
      failures.push(String(text));
    }
  }
  throw new Error(`None of the expected texts were visible: ${failures.join(', ')}`);
}

export async function expectAuditSidebar(page: Page, labels: string[]) {
  await expandSidebarButton(page, /inspection/i);
  await expandSidebarButton(page, /^audit$/i);

  for (const label of labels) {
    await expect(page.getByRole('link', { name: new RegExp(label, 'i') }).first()).toBeVisible({ timeout: DEFAULT_TIMEOUT });
  }
}

async function expandSidebarButton(page: Page, name: RegExp) {
  const button = page.getByRole('button', { name }).first();
  if (!(await button.isVisible().catch(() => false))) {
    return;
  }

  const expanded = await button.getAttribute('aria-expanded');
  if (expanded !== 'true') {
    await button.click().catch(() => undefined);
  }
}

export async function expectRouteAvailable(page: Page, route: string, title: string | RegExp) {
  await openRoute(page, route, title);
  await expect(page.locator('body')).not.toContainText(/not found|404/i);
}

export { test };
