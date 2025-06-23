// Service Worker per MasterWash PWA
const CACHE_NAME = 'masterwash-v1.0.0';
const DYNAMIC_CACHE = 'masterwash-dynamic-v1.0.0';

// File da cachare per funzionamento offline
const STATIC_FILES = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/manifest.json',
    '/static/icon-192.png',
    '/static/icon-512.png'
];

// API endpoints da cachare
const API_CACHE_PATTERNS = [
    '/api/stats-realtime',
    '/api/accessi-orari',
    '/api/abbonamenti-mensili'
];

// Pagine principali da cachare
const PAGE_CACHE_PATTERNS = [
    '/dashboard',
    '/accessi/',
    '/abbonamenti/',
    '/stampa/configurazione'
];

// ===== INSTALL EVENT =====
self.addEventListener('install', event => {
    console.log('🔧 Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 Caching static files...');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('✅ Static files cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('❌ Error caching static files:', error);
            })
    );
});

// ===== ACTIVATE EVENT =====
self.addEventListener('activate', event => {
    console.log('🚀 Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME && cacheName !== DYNAMIC_CACHE) {
                            console.log('🗑️ Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker activated');
                return self.clients.claim();
            })
    );
});

// ===== FETCH EVENT =====
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Skip non-GET requests and external requests
    if (request.method !== 'GET' || !url.origin.includes(self.location.origin)) {
        return;
    }
    
    // Handle different types of requests
    if (isStaticFile(request.url)) {
        event.respondWith(handleStaticFile(request));
    } else if (isAPIRequest(request.url)) {
        event.respondWith(handleAPIRequest(request));
    } else if (isPageRequest(request)) {
        event.respondWith(handlePageRequest(request));
    } else {
        event.respondWith(handleOtherRequest(request));
    }
});

// ===== REQUEST HANDLERS =====

// Cache First Strategy per file statici
function handleStaticFile(request) {
    return caches.match(request)
        .then(response => {
            if (response) {
                console.log('📁 Serving from cache:', request.url);
                return response;
            }
            
            return fetch(request)
                .then(response => {
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => cache.put(request, responseClone));
                    }
                    return response;
                })
                .catch(() => {
                    console.log('📁 Fallback for static file:', request.url);
                    return new Response('File non disponibile offline', {
                        status: 503,
                        statusText: 'Service Unavailable'
                    });
                });
        });
}

// Network First Strategy per API
function handleAPIRequest(request) {
    return fetch(request)
        .then(response => {
            if (response.status === 200) {
                const responseClone = response.clone();
                caches.open(DYNAMIC_CACHE)
                    .then(cache => cache.put(request, responseClone));
            }
            return response;
        })
        .catch(() => {
            console.log('🌐 API offline, serving from cache:', request.url);
            return caches.match(request)
                .then(response => {
                    if (response) {
                        // Aggiungi header per indicare che è cache
                        const headers = new Headers(response.headers);
                        headers.append('X-Served-By', 'ServiceWorker-Cache');
                        return new Response(response.body, {
                            status: response.status,
                            statusText: response.statusText,
                            headers: headers
                        });
                    }
                    
                    // Risposta offline di default per API
                    return new Response(JSON.stringify({
                        error: 'Dati non disponibili offline',
                        offline: true
                    }), {
                        status: 503,
                        headers: { 'Content-Type': 'application/json' }
                    });
                });
        });
}

// Network First Strategy per pagine
function handlePageRequest(request) {
    return fetch(request)
        .then(response => {
            if (response.status === 200) {
                const responseClone = response.clone();
                caches.open(DYNAMIC_CACHE)
                    .then(cache => cache.put(request, responseClone));
            }
            return response;
        })
        .catch(() => {
            console.log('📄 Page offline, serving from cache:', request.url);
            return caches.match(request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    
                    // Fallback alla pagina principale se disponibile
                    return caches.match('/')
                        .then(homeResponse => {
                            if (homeResponse) {
                                return homeResponse;
                            }
                            
                            // Pagina offline di emergenza
                            return new Response(`
                                <!DOCTYPE html>
                                <html>
                                <head>
                                    <title>MasterWash - Offline</title>
                                    <meta name="viewport" content="width=device-width, initial-scale=1">
                                    <style>
                                        body { 
                                            font-family: Arial, sans-serif; 
                                            text-align: center; 
                                            padding: 50px; 
                                            background: #f5f5f5;
                                        }
                                        .offline-container {
                                            background: white;
                                            padding: 30px;
                                            border-radius: 10px;
                                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                                            max-width: 400px;
                                            margin: 0 auto;
                                        }
                                        .offline-icon { font-size: 4rem; margin-bottom: 20px; }
                                        .offline-title { color: #333; margin-bottom: 15px; }
                                        .offline-message { color: #666; margin-bottom: 20px; }
                                        .retry-btn {
                                            background: #2563eb;
                                            color: white;
                                            border: none;
                                            padding: 10px 20px;
                                            border-radius: 5px;
                                            cursor: pointer;
                                        }
                                    </style>
                                </head>
                                <body>
                                    <div class="offline-container">
                                        <div class="offline-icon">📴</div>
                                        <h1 class="offline-title">MasterWash</h1>
                                        <p class="offline-message">
                                            Non sei connesso a Internet.<br>
                                            Verifica la connessione e riprova.
                                        </p>
                                        <button class="retry-btn" onclick="window.location.reload()">
                                            Riprova
                                        </button>
                                    </div>
                                </body>
                                </html>
                            `, {
                                status: 503,
                                headers: { 'Content-Type': 'text/html' }
                            });
                        });
                });
        });
}

// Strategia generica per altre richieste
function handleOtherRequest(request) {
    return fetch(request)
        .catch(() => {
            return caches.match(request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    
                    return new Response('Risorsa non disponibile offline', {
                        status: 503,
                        statusText: 'Service Unavailable'
                    });
                });
        });
}

// ===== UTILITY FUNCTIONS =====

function isStaticFile(url) {
    return url.includes('/static/') || 
           url.endsWith('.css') || 
           url.endsWith('.js') || 
           url.endsWith('.png') || 
           url.endsWith('.jpg') || 
           url.endsWith('.ico') ||
           url.includes('manifest.json');
}

function isAPIRequest(url) {
    return url.includes('/api/') || 
           API_CACHE_PATTERNS.some(pattern => url.includes(pattern));
}

function isPageRequest(request) {
    return request.destination === 'document' ||
           PAGE_CACHE_PATTERNS.some(pattern => request.url.includes(pattern));
}

// ===== BACKGROUND SYNC =====
self.addEventListener('sync', event => {
    console.log('🔄 Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

function doBackgroundSync() {
    // Implementazione future per sincronizzazione dati offline
    console.log('🔄 Performing background sync...');
    return Promise.resolve();
}

// ===== PUSH NOTIFICATIONS =====
self.addEventListener('push', event => {
    console.log('🔔 Push message received');
    
    if (event.data) {
        const data = event.data.json();
        
        const options = {
            body: data.body || 'Nuovo aggiornamento disponibile',
            icon: '/static/icon-192.png',
            badge: '/static/icon-192.png',
            vibrate: [100, 50, 100],
            data: {
                url: data.url || '/'
            },
            actions: [
                {
                    action: 'open',
                    title: 'Apri App'
                },
                {
                    action: 'close',
                    title: 'Chiudi'
                }
            ]
        };
        
        event.waitUntil(
            self.registration.showNotification(data.title || 'MasterWash', options)
        );
    }
});

// ===== NOTIFICATION CLICK =====
self.addEventListener('notificationclick', event => {
    console.log('🔔 Notification clicked');
    
    event.notification.close();
    
    if (event.action === 'open' || !event.action) {
        const url = event.notification.data?.url || '/';
        
        event.waitUntil(
            clients.matchAll({ type: 'window' })
                .then(clientList => {
                    // Se c'è già una finestra aperta, focusla
                    for (const client of clientList) {
                        if (client.url === url && 'focus' in client) {
                            return client.focus();
                        }
                    }
                    
                    // Altrimenti apri una nuova finestra
                    if (clients.openWindow) {
                        return clients.openWindow(url);
                    }
                })
        );
    }
});

// ===== MESSAGE EVENT =====
self.addEventListener('message', event => {
    console.log('💬 Message received:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CACHE_UPDATE') {
        event.waitUntil(updateCache());
    }
});

function updateCache() {
    return caches.open(CACHE_NAME)
        .then(cache => {
            return cache.addAll(STATIC_FILES);
        })
        .then(() => {
            console.log('✅ Cache updated successfully');
        })
        .catch(error => {
            console.error('❌ Error updating cache:', error);
        });
}

// ===== CLEANUP =====
// Pulisci cache vecchie periodicamente
function cleanupOldCache() {
    const maxCacheAge = 7 * 24 * 60 * 60 * 1000; // 7 giorni
    const now = Date.now();
    
    return caches.open(DYNAMIC_CACHE)
        .then(cache => {
            return cache.keys()
                .then(requests => {
                    return Promise.all(
                        requests.map(request => {
                            return cache.match(request)
                                .then(response => {
                                    if (response) {
                                        const cachedTime = response.headers.get('sw-cache-time');
                                        if (cachedTime && (now - parseInt(cachedTime)) > maxCacheAge) {
                                            console.log('🗑️ Removing old cache entry:', request.url);
                                            return cache.delete(request);
                                        }
                                    }
                                });
                        })
                    );
                });
        });
}

// Esegui cleanup periodico
setInterval(cleanupOldCache, 24 * 60 * 60 * 1000); // Ogni 24 ore

console.log('🛠️ MasterWash Service Worker loaded successfully');