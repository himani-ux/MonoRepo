/// <reference lib="webworker" />

/**
 * Custom service worker for PSC Inspection Module.
 *
 * Source: IMPLEMENTATION_PLAN.md Step 8.3
 * Implements: TECH_STACK.md §1.10 (Workbox 7.1.0)
 *
 * Caching strategy:
 * - App shell (HTML, CSS, JS): Precached by vite-plugin-pwa
 * - Navigation: NetworkFirst with offline fallback to cached shell
 * - Static assets (images, fonts): CacheFirst
 * - API requests: NetworkOnly (IndexedDB handles offline data per Phase 7)
 */

import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching';
import { registerRoute, NavigationRoute } from 'workbox-routing';
import { CacheFirst, NetworkFirst, NetworkOnly } from 'workbox-strategies';

declare let self: ServiceWorkerGlobalScope;

// Clean up old caches from previous versions
cleanupOutdatedCaches();

// Precache app shell — manifest injected by vite-plugin-pwa at build time
precacheAndRoute(self.__WB_MANIFEST);

// Navigation requests — serve cached app shell as SPA fallback
const navigationHandler = new NetworkFirst({
  cacheName: 'navigation-cache',
  networkTimeoutSeconds: 3,
});
registerRoute(
  new NavigationRoute(navigationHandler, {
    denylist: [/^\/api\//],
  })
);

// Static assets (images, fonts) — CacheFirst for performance
registerRoute(
  ({ request }) =>
    request.destination === 'image' || request.destination === 'font',
  new CacheFirst({
    cacheName: 'static-assets',
  })
);

// API requests — NetworkOnly (IndexedDB + sync service handles offline data)
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkOnly()
);

// Listen for SKIP_WAITING message from the app (prompt-for-update pattern)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
