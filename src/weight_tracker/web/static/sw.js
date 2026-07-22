// Minimal app-shell service worker (D-11/ADR-001): pre-cache the shell, serve
// network-first with cache fallback. GET only -- saves are never queued offline.
const SHELL_CACHE = "weight-tracker-shell-v1";
const APP_SHELL = ["/", "/static/uplot.iife.min.js", "/static/uplot.min.css"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((cache) => cache.addAll(APP_SHELL)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((name) => name !== SHELL_CACHE).map((name) => caches.delete(name)))
    )
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
