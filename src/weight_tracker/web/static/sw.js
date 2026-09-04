// Minimal app-shell service worker (D-11/ADR-001): pre-cache the shell, serve
// network-first with cache fallback. GET only -- saves are never queued offline.
// v4 (US-013): no new asset ships, but APP_SHELL pre-caches "/" itself and that
// page grew a date row -- without a new name an offline open keeps being served
// the pre-date-row entry screen out of v3.
// v5 (US-015, D-32): no new asset either, but the pre-cached graph.js changed --
// it now applies the served axis. Fetch is network-first, so an online morning
// is unaffected; an OFFLINE open would otherwise keep the pre-axis engine out
// of v4 until the worker reinstalls.
const SHELL_CACHE = "weight-tracker-shell-v5";
const APP_SHELL = [
  "/",
  "/static/uplot.iife.min.js",
  "/static/uplot.min.css",
  "/static/graph.js",
  "/static/theme.css",
];

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
