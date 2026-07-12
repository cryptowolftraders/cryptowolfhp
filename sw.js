/* CryptoWolf HP — Service Worker */
const VER = 'wolf-v1';
const SHELL = ['/', '/index.html', '/manifest.json',
  '/icons/icon-192.png', '/icons/icon-512.png', '/icons/apple-touch-icon.png'];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(VER).then((c) => c.addAll(SHELL).catch(() => {})));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== VER).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Sadece kendi origin'imiz — Railway proxy / Binance / API asla cache'lenmez
  if (url.origin !== self.location.origin) return;

  const isHTML = req.mode === 'navigate' ||
    (req.headers.get('accept') || '').includes('text/html');

  if (isHTML) {
    // HTML: önce ağ (güncel kalsın), offline'da cache'ten
    e.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(VER).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => caches.match(req).then((r) => r || caches.match('/index.html')))
    );
    return;
  }

  // Statik (ikon/görsel/font): cache-first + arkada güncelle
  e.respondWith(
    caches.match(req).then((cached) => {
      const net = fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(VER).then((c) => c.put(req, copy)).catch(() => {});
        return res;
      }).catch(() => cached);
      return cached || net;
    })
  );
});
