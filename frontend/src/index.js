/*
========================================================
  ФАЙЛ: frontend/src/index.js
  НАЗНАЧЕНИЕ: Точка входа React-приложения.
  Здесь:
  1. React монтируется в div#root из index.html
  2. Регистрируется Service Worker (PWA)
========================================================
*/

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// -----------------------------------------------------------
// Создаём корневой элемент React и рендерим приложение.
// createRoot — новый API React 18 (поддерживает Concurrent Mode)
// -----------------------------------------------------------
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
    // StrictMode — включает дополнительные предупреждения в режиме разработки.
    // В продакшене не влияет на поведение.
    <React.StrictMode>
        <App />
    </React.StrictMode>
);


// -----------------------------------------------------------
// РЕГИСТРАЦИЯ SERVICE WORKER (PWA)
// Раздел курсовой: 2.4 — "Progressive Web Application"
//
// Service Worker регистрируется только в продакшен-сборке
// (npm run build), а не в режиме разработки.
// Это сделано намеренно: в dev-режиме кэш мешает видеть изменения.
// -----------------------------------------------------------
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
    window.addEventListener('load', () => {
        navigator.serviceWorker
            .register('/service-worker.js')
            .then((registration) => {
                console.log('[PWA] Service Worker зарегистрирован:', registration.scope);

                // Проверяем обновления при каждой загрузке
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // Новая версия приложения готова
                            console.log('[PWA] Новая версия доступна. Обновите страницу.');
                        }
                    });
                });
            })
            .catch((err) => {
                console.error('[PWA] Ошибка регистрации Service Worker:', err);
            });
    });
}
