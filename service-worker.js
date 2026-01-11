const CACHE_NAME = "phone-prices-v1";
const CORE_ASSETS = [
  "./",
  "./index.html",
  "./phones.json",
  "./stores.json",
  "./manifest.json"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(CORE_ASSETS).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => k !== CACHE_NAME && caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;

  event.respondWith(
    caches.match(req).then(cached => {
      const fetchPromise = fetch(req)
        .then(res => {
          if (!res || res.status !== 200) return cached;
          const copy = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, copy).catch(() => {}));
          return res;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
