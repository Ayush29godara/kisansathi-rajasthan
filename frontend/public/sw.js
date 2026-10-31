// Self-healing Service Worker cleanup for KisanSathi Rajasthan
// Purges stale cached index.html from v1, unregisters itself, and reloads open tabs.

const CACHE_NAME = 'kisansathi-cleanup-v4';

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    (async () => {
      try {
        const keys = await caches.keys();
        await Promise.all(keys.map((key) => caches.delete(key)));
      } catch (e) {
        // Ignore cache deletion errors
      }
      try {
        await self.clients.claim();
        await self.registration.unregister();
        const clients = await self.clients.matchAll({ type: 'window' });
        for (const client of clients) {
          client.navigate(client.url);
        }
      } catch (e) {
        // Ignore navigation errors
      }
    })()
  );
});
