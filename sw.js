const CACHE_VERSION = "life-wallet-shell-v2";
const APP_SHELL = [
  "./",
  "./index.html",
  "./runtime-config.js",
  "./manifest.webmanifest",
  "./assets/tailwindcss.js",
  "./assets/crypto-js.min.js",
  "./assets/password-worker.js",
  "./assets/app-icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/api/") || url.pathname === "/health" || url.pathname === "/ready") {
    return;
  }

  const isRuntimeConfig = url.pathname.endsWith("/runtime-config.js");
  if (request.mode === "navigate" || isRuntimeConfig) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || caches.match("./index.html")))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const networkUpdate = fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => cached);

      if (cached) {
        event.waitUntil(networkUpdate.catch(() => cached));
        return cached;
      }
      return networkUpdate;
    })
  );
});