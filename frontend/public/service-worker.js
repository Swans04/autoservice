/*
========================================================
  ФАЙЛ: frontend/public/service-worker.js
  НАЗНАЧЕНИЕ: Service Worker — основа PWA (Progressive Web App).
  
  Что делает:
  1. Кэширует файлы приложения для работы офлайн
  2. Перехватывает сетевые запросы (стратегия Cache-First)
  3. Получает и отображает Push-уведомления
  
  Раздел курсовой: 2.4 — "интеграция с современными
  инструментами, включая PWA и push-уведомления"
  
  ⚠️ Этот файл должен лежать в папке public/ (корень сайта).
  Service Worker регистрируется в index.js.
========================================================
*/

// -----------------------------------------------------------
// Версия кэша — при обновлении приложения меняйте CACHE_VERSION
// чтобы сбросить старый кэш у пользователей
// -----------------------------------------------------------
const CACHE_VERSION   = 'v1.0.0';
const CACHE_STATIC    = `autoservice-static-${CACHE_VERSION}`;   // Статические файлы
const CACHE_DYNAMIC   = `autoservice-dynamic-${CACHE_VERSION}`;  // API-ответы и динамика

// -----------------------------------------------------------
// Список файлов для предварительного кэширования.
// Эти файлы загружаются и сохраняются сразу при установке SW.
// Это позволяет открыть приложение без интернета.
// -----------------------------------------------------------
const STATIC_ASSETS = [
    '/',                          // Главная страница
    '/index.html',                // HTML-оболочка React
    '/manifest.json',             // Манифест PWA
    '/static/js/main.chunk.js',   // Основной JS React (имя может отличаться после сборки)
    '/static/css/main.chunk.css', // Основной CSS
    // ⚠️ Точные имена файлов появятся после npm run build.
    // Запустите сборку и добавьте сюда реальные имена из папки build/static/
];


// ============================================================
//  СОБЫТИЕ INSTALL — установка Service Worker
//  Вызывается один раз при первой загрузке
// ============================================================
self.addEventListener('install', (event) => {
    console.log(`[SW] Установка: ${CACHE_STATIC}`);

    event.waitUntil(
        caches.open(CACHE_STATIC)
            .then((cache) => {
                console.log('[SW] Кэшируем статические файлы...');
                // addAll() загружает и кэширует все файлы из списка
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                // skipWaiting() — активируем новый SW немедленно,
                // не ждём закрытия всех вкладок
                return self.skipWaiting();
            })
            .catch((err) => {
                console.error('[SW] Ошибка кэширования статики:', err);
            })
    );
});


// ============================================================
//  СОБЫТИЕ ACTIVATE — активация Service Worker
//  Удаляем устаревший кэш от предыдущих версий
// ============================================================
self.addEventListener('activate', (event) => {
    console.log(`[SW] Активация: ${CACHE_STATIC}`);

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    // Оставляем только актуальные кэши текущей версии
                    .filter(name => name !== CACHE_STATIC && name !== CACHE_DYNAMIC)
                    .map(name => {
                        console.log(`[SW] Удаляем устаревший кэш: ${name}`);
                        return caches.delete(name);  // Удаляем старый кэш
                    })
            );
        })
        .then(() => self.clients.claim())  // Берём управление над всеми вкладками
    );
});


// ============================================================
//  СОБЫТИЕ FETCH — перехват всех сетевых запросов
//  Стратегии кэширования:
//  - Статические файлы: Cache First (кэш → сеть)
//  - API-запросы: Network First (сеть → кэш)
// ============================================================
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Пропускаем запросы не к нашему серверу (CDN, сторонние сервисы)
    if (!url.origin.includes(self.location.origin) &&
        !url.hostname.includes('localhost')) {
        return;  // Не перехватываем — пускаем напрямую
    }

    // --- API-запросы: Network First ---
    // Сначала пробуем сеть (актуальные данные),
    // при ошибке — берём из кэша (офлайн-режим)
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // --- Статика и страницы: Cache First ---
    // Сначала кэш (быстро), при отсутствии — сеть
    event.respondWith(cacheFirst(request));
});


/**
 * Стратегия Cache First:
 * Ищем в кэше → если нашли, отдаём.
 * Если нет → запрашиваем сеть, кэшируем ответ.
 */
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;  // Нашли в кэше — отдаём немедленно
    }

    try {
        const networkResponse = await fetch(request);

        // Кэшируем ответ для будущего использования
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_STATIC);
            // Клонируем: Response можно прочитать только один раз
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch {
        // Нет ни кэша, ни сети — возвращаем офлайн-страницу
        const offlinePage = await caches.match('/index.html');
        return offlinePage || new Response('Нет подключения к интернету', { status: 503 });
    }
}


/**
 * Стратегия Network First:
 * Запрашиваем сеть → при успехе кэшируем и отдаём.
 * При ошибке → берём из кэша.
 */
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok && request.method === 'GET') {
            // Кэшируем GET-запросы к API (POST/PUT не кэшируем — они изменяют данные)
            const cache = await caches.open(CACHE_DYNAMIC);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch {
        // Нет сети — ищем в кэше
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Нет ни сети, ни кэша — возвращаем ошибку в формате JSON
        return new Response(
            JSON.stringify({ error: 'Нет подключения к интернету. Данные могут быть устаревшими.' }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}


// ============================================================
//  PUSH-УВЕДОМЛЕНИЯ
//  Раздел курсовой: 2.4 — "push-уведомления"
//
//  ⚠️ Чтобы push-уведомления работали, нужно:
//  1. Настроить VAPID-ключи на сервере:
//     pip install pywebpush
//     python -c "from pywebpush import webpush; print(webpush.generate_keys())"
//  2. Вставить публичный VAPID-ключ в serviceWorkerRegistration.js
//  3. Подписать пользователя на пуш через pushManager.subscribe()
// ============================================================
self.addEventListener('push', (event) => {
    if (!event.data) return;

    // Читаем данные уведомления из push-события
    let notificationData;
    try {
        notificationData = event.data.json();
    } catch {
        // Если данные не JSON — берём как текст
        notificationData = {
            title: 'АвтоСервис',
            body: event.data.text(),
        };
    }

    const title   = notificationData.title   || 'АвтоСервис Онлайн';
    const options = {
        body:    notificationData.body    || 'Новое уведомление',
        icon:    notificationData.icon    || '/icons/icon-192x192.png',
        badge:   '/icons/icon-72x72.png',  // Маленькая иконка в статусбаре Android
        tag:     notificationData.tag     || 'autoservice',  // Группировка уведомлений
        data:    notificationData.data    || { url: '/' },   // Данные для обработчика клика
        actions: notificationData.actions || [               // Кнопки в уведомлении
            { action: 'view', title: 'Посмотреть' },
            { action: 'dismiss', title: 'Закрыть' },
        ],
        vibrate:          [200, 100, 200],     // Паттерн вибрации (Android)
        requireInteraction: false,              // Не требовать взаимодействия
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});


// ============================================================
//  КЛИК ПО PUSH-УВЕДОМЛЕНИЮ
// ============================================================
self.addEventListener('notificationclick', (event) => {
    event.notification.close();  // Закрываем уведомление

    const action = event.action;
    const url    = event.notification.data?.url || '/';

    if (action === 'dismiss') return;  // Нажали "Закрыть" — ничего не делаем

    // Открываем вкладку с нужным URL или фокусируемся на уже открытой
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Ищем уже открытую вкладку нашего приложения
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.focus();
                        client.navigate(url);  // Переходим на нужную страницу
                        return;
                    }
                }
                // Открытой вкладки нет — открываем новую
                clients.openWindow(url);
            })
    );
});
