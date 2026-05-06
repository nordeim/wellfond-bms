/**
 * Wellfond BMS Service Worker
 * ============================
 * PWA support with offline caching and background sync.
 */

const CACHE_NAME = "wellfond-bms-v1";
const STATIC_ASSETS = [
  "/",
  "/ground",
  "/ground/heat",
  "/ground/mate",
  "/ground/whelp",
  "/ground/health",
  "/ground/weight",
  "/ground/nursing",
  "/ground/not-ready",
];

// Install - cache static assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate - clean up old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name !== CACHE_NAME)
            .map((name) => caches.delete(name))
        );
      })
      .then(() => self.clients.claim())
  );
});

// Fetch - network first, fallback to cache
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== "GET") {
    return;
  }

  // Skip API requests (let them fail properly)
  if (url.pathname.startsWith("/api/")) {
    return;
  }

  // Cache strategy: Network first, then cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Clone response before caching
        const responseClone = response.clone();

        // Cache successful responses
        if (response.status === 200) {
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
        }

        return response;
      })
      .catch(() => {
        // Fallback to cache
        return caches.match(request).then((cached) => {
          if (cached) {
            return cached;
          }

          // Return offline page for navigation requests
          if (request.mode === "navigate") {
            return caches.match("/ground");
          }

          // Return error for other requests
          return new Response("Offline", { status: 503 });
        });
      })
  );
});

// Push notifications (for alerts)
self.addEventListener("push", (event) => {
  const data = event.data?.json() || {};

  const options = {
    body: data.message || "New alert from Wellfond BMS",
    icon: "/icon-192x192.png",
    badge: "/badge-72x72.png",
    tag: data.tag || "alert",
    requireInteraction: data.severity === "serious",
    data: data,
  };

  event.waitUntil(
    self.registration.showNotification(
      data.title || "Wellfond BMS Alert",
      options
    )
  );
});

// Notification click
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const data = event.notification.data;
  let url = "/ground";

  if (data?.dog_id) {
    url = `/ground?dog=${data.dog_id}`;
  }

  event.waitUntil(
    clients.matchAll({ type: "window" }).then((clientList) => {
      // Focus existing client if open
      for (const client of clientList) {
        if (client.url === url && "focus" in client) {
          return client.focus();
        }
      }
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

