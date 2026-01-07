// AirSpace Service Worker
self.addEventListener('install', (e) => {
  console.log('[Service Worker] Installed');
});

self.addEventListener('fetch', (e) => {
  // Filhal hum kuch cache nahi kar rahe taake Chat Real-time rahe
  e.respondWith(fetch(e.request));
});