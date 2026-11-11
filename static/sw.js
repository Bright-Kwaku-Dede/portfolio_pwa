const CACHE_NAME = "portfolio-v2";

// Every URL here must return 200, or the whole install fails.
const PRECACHE_URLS = [
  "/",
  "/static/css/style.css",
  "/static/weather_js/weather.js",
  "/manifest.json",
  "/static/icons/icon-192x192.png",
];

// Paths the service worker must never handle or cache:
// API calls, the password-protected admin area, and short-link redirects.
const NEVER_CACHE_PREFIXES = ["/api/", "/admin", "/s/"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k.startsWith("portfolio-") && k !== CACHE_NAME)
            .map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle same-origin GETs
  if (req.method !== "GET" || url.origin !== location.origin) return;

  // Leave API, admin and short-link requests entirely to the network
  if (NEVER_CACHE_PREFIXES.some((p) => url.pathname.startsWith(p))) return;

  // Pages: network first, fall back to cache, then to the home page
  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // Only cache successful responses (never 401/404/500 pages)
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => caches.match(req).then((r) => r || caches.match("/"))),
    );
    return;
  }

  // Static files: serve cached copy immediately, refresh it in the background
  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || network;
    }),
  );
});
