// Service Worker fuer japanese-learning.ch
// Phase 3: Web Push Notifications fuer Streak-Reminder

const CACHE_VERSION = 'jpl-sw-v1';

self.addEventListener('install', (event) => {
    // sofort aktivieren, kein Wait
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
    let data = {};
    try { data = event.data ? event.data.json() : {}; } catch (e) { data = {}; }

    const title = data.title || 'Japanisch lernen';
    const body  = data.body  || 'Heute schon geübt? Dein Streak wartet.';
    const tag   = data.tag   || 'streak-reminder';
    const url   = data.url   || '/practice/kana';

    const options = {
        body,
        tag,
        icon: '/static/favicon-32.png',
        badge: '/static/favicon-16.png',
        data: { url },
        requireInteraction: false,
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = event.notification.data?.url || '/practice/kana';
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then((wins) => {
            // Bestehenden Tab fokussieren wenn vorhanden
            for (const w of wins) {
                if (w.url.includes(self.location.origin)) {
                    w.focus();
                    w.navigate(url);
                    return;
                }
            }
            return clients.openWindow(url);
        })
    );
});
