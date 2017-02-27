
var CACHE = 'app-cache';

self.addEventListener('install', function(evt) {
  evt.waitUntil(precache());
});

self.addEventListener('fetch', function(evt) {
  evt.respondWith(fetch(evt.request).catch(function () {
    return caches.open(CACHE).then(function(cache) {
      return cache.match('/media/offline.html');
    });
  }));
});

function precache() {
  return caches.open(CACHE).then(function (cache) {
    return cache.addAll([
      '/',
      '/media/offline.html',
      '/static/css/oneplus.css',
      '/media/img/appicons/dig-it_icon_96.png',
      '/media/img/appicons/dig-it_icon_144.png',
      '/media/img/appicons/dig-it_icon_192.png'
    ]);
  });
}
