/**
 * Service worker registration for PWA support.
 *
 * Source: IMPLEMENTATION_PLAN.md Step 8.3
 * Implements: TECH_STACK.md §1.10 (vite-plugin-pwa 0.20.0)
 *
 * Uses virtual:pwa-register module provided by vite-plugin-pwa.
 * Handles:
 * - SW registration in production only
 * - Update detection with user prompt
 * - Periodic update checks (every hour)
 * - Offline readiness detection
 */

import { registerSW } from 'virtual:pwa-register';

let updateSW: ((reloadPage?: boolean) => Promise<void>) | undefined;

/**
 * Register the service worker and set up update handling.
 * Only active in production — vite-plugin-pwa skips in dev mode.
 */
export function registerServiceWorker(): void {
  if (!('serviceWorker' in navigator)) {
    return;
  }

  updateSW = registerSW({
    onNeedRefresh() {
      // New version available — prompt user to reload
      const shouldUpdate = window.confirm(
        'A new version of PSC Inspection is available. Reload to update?'
      );
      if (shouldUpdate) {
        updateSW?.(true);
      }
    },
    onOfflineReady() {
      console.info('PSC Inspection is ready to work offline.');
    },
    onRegisteredSW(swUrl, registration) {
      // Check for updates periodically (every hour)
      if (registration) {
        setInterval(async () => {
          if (registration.installing || !navigator) return;
          if ('connection' in navigator && !navigator.onLine) return;

          try {
            const resp = await fetch(swUrl, {
              cache: 'no-store',
              headers: {
                'cache': 'no-store',
                'cache-control': 'no-cache',
              },
            });
            if (resp?.status === 200) {
              await registration.update();
            }
          } catch {
            // Network error — skip this update check
          }
        }, 60 * 60 * 1000); // Every hour
      }
    },
    onRegisterError(error) {
      console.error('Service worker registration failed:', error);
    },
  });
}

/**
 * Manually trigger a service worker update check.
 */
export function checkForUpdates(): void {
  updateSW?.();
}
