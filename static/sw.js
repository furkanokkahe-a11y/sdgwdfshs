self.addEventListener('push', function(event) {
  let veri = { title: '💌 Sana bir mesaj var', body: '...' };
  try { veri = event.data.json(); } catch(e) {}

  event.waitUntil(
    self.registration.showNotification(veri.title, {
      body: veri.body,
      icon: '/static/photos/' + (veri.icon || ''),
      badge: '',
      vibrate: [200, 100, 200],
      requireInteraction: true,
      data: { url: '/' }
    })
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(list) {
      for (const client of list) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow('/');
    })
  );
});
