/*
========================================================
  ФАЙЛ: frontend/src/services/api.js
  НАЗНАЧЕНИЕ: Центральный модуль для всех HTTP-запросов к API.
  Все компоненты используют функции из этого файла,
  а не пишут fetch/axios напрямую.
  
  Структура:
  - Настройка axios (базовый URL, токены)
  - Интерцепторы (автоматическое добавление токена)
  - Функции для каждой группы endpoint'ов
========================================================
*/

import axios from 'axios';

// -----------------------------------------------------------
// BASE_URL — адрес нашего Django-сервера.
// ⚠️ КАК НАСТРОИТЬ:
//   При локальной разработке: http://localhost:8000
//   В продакшене: замените на реальный домен сервера,
//   например: https://api.autoservice.ru
//   Значение можно вынести в файл .env:
//     REACT_APP_API_URL=http://localhost:8000
//   Тогда здесь будет: process.env.REACT_APP_API_URL
// -----------------------------------------------------------
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// -----------------------------------------------------------
// Создаём экземпляр axios с базовыми настройками.
// Все запросы через apiClient автоматически имеют:
// - базовый URL
// - заголовок Content-Type: application/json
// - таймаут 10 секунд
// -----------------------------------------------------------
const apiClient = axios.create({
    baseURL: BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000,  // 10 секунд — если сервер не ответил, ошибка
});

// -----------------------------------------------------------
// ИНТЕРЦЕПТОР ЗАПРОСОВ:
// Перед каждым запросом автоматически добавляем JWT-токен
// в заголовок Authorization.
// Это избавляет от необходимости вручную добавлять токен
// в каждый вызов API.
// -----------------------------------------------------------
apiClient.interceptors.request.use(
    (config) => {
        // Читаем токен из localStorage
        // localStorage — хранилище браузера, сохраняется между сессиями
        const token = localStorage.getItem('access_token');
        
        if (token) {
            // Формат: Authorization: Bearer eyJ0eXAiOiJKV1Q...
            config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;  // Возвращаем изменённый config запроса
    },
    (error) => {
        // Ошибка при формировании запроса (редко)
        return Promise.reject(error);
    }
);

// -----------------------------------------------------------
// ИНТЕРЦЕПТОР ОТВЕТОВ:
// Обрабатывает ответы от сервера.
// Главная задача: если получили 401 (токен истёк) —
// автоматически обновляем токен и повторяем запрос.
// -----------------------------------------------------------
apiClient.interceptors.response.use(
    (response) => response,  // Успешный ответ — возвращаем как есть

    async (error) => {
        const originalRequest = error.config;  // Сохраняем оригинальный запрос

        // Если ошибка 401 (Unauthorized) и это не повторный запрос
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;  // Помечаем: уже пробовали обновить токен

            try {
                // Пробуем обновить access-токен с помощью refresh-токена
                const refreshToken = localStorage.getItem('refresh_token');
                
                if (!refreshToken) {
                    // Нет refresh-токена — разлогиниваем пользователя
                    authService.logout();
                    return Promise.reject(error);
                }

                // Запрос на обновление токена (без интерцептора — чтобы не зациклиться)
                const response = await axios.post(`${BASE_URL}/auth/refresh/`, {
                    refresh: refreshToken
                });

                const newAccessToken = response.data.access;
                
                // Сохраняем новый токен
                localStorage.setItem('access_token', newAccessToken);

                // Повторяем исходный запрос с новым токеном
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                return apiClient(originalRequest);

            } catch (refreshError) {
                // Refresh-токен тоже истёк — разлогиниваем
                authService.logout();
                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);


// ============================================================
//  СЕРВИС АУТЕНТИФИКАЦИИ
//  Функции: регистрация, вход, выход, получение профиля
// ============================================================
export const authService = {
    /**
     * Регистрация нового пользователя.
     * @param {Object} data - { email, username, first_name, last_name, phone, password, password_confirm }
     * @returns {Promise} - Данные созданного пользователя
     */
    register: (data) => apiClient.post('/auth/register/', data),

    /**
     * Вход в систему.
     * @param {string} email
     * @param {string} password
     * @returns {Promise} - { access, refresh } — JWT-токены
     */
    login: async (email, password) => {
        const response = await apiClient.post('/auth/login/', { email, password });
        const { access, refresh } = response.data;
        
        // Сохраняем токены в localStorage (останутся даже после закрытия вкладки)
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        
        return response;
    },

    /**
     * Выход из системы.
     * Удаляем токены из localStorage и перенаправляем на страницу входа.
     */
    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');  // Очищаем кэш данных пользователя
        
        // Перенаправляем на страницу входа
        window.location.href = '/login';
    },

    /**
     * Получить профиль текущего пользователя.
     * @returns {Promise} - Данные пользователя
     */
    getProfile: () => apiClient.get('/profile/'),

    /**
     * Обновить профиль.
     * @param {Object} data - Изменённые поля профиля
     */
    updateProfile: (data) => apiClient.patch('/profile/', data),

    /**
     * Сменить пароль.
     * @param {Object} data - { old_password, new_password, new_password_confirm }
     */
    changePassword: (data) => apiClient.post('/change-password/', data),

    /**
     * Проверить, авторизован ли пользователь.
     * @returns {boolean}
     */
    isAuthenticated: () => !!localStorage.getItem('access_token'),

    /**
     * Получить текущего пользователя из localStorage.
     * Данные кэшируются при входе чтобы не делать лишние запросы.
     * @returns {Object|null}
     */
    getCurrentUser: () => {
        const userJson = localStorage.getItem('user');
        try {
            return userJson ? JSON.parse(userJson) : null;
        } catch {
            return null;
        }
    },

    /**
     * Кэшировать данные пользователя в localStorage.
     * @param {Object} user
     */
    setCurrentUser: (user) => {
        localStorage.setItem('user', JSON.stringify(user));
    },
};


// ============================================================
//  СЕРВИС УСЛУГ
// ============================================================
export const serviceAPI = {
    /**
     * Получить список всех активных услуг.
     * GET /api/services/
     */
    getAll: () => apiClient.get('/services/'),

    /**
     * Получить детали одной услуги.
     * GET /api/services/{id}/
     * @param {number} id
     */
    getById: (id) => apiClient.get(`/services/${id}/`),

    /**
     * Создать новую услугу (только администратор).
     * POST /api/services/
     * @param {Object} data - { name, description, duration_minutes, price }
     */
    create: (data) => apiClient.post('/services/', data),

    /**
     * Обновить услугу (только администратор).
     * @param {number} id
     * @param {Object} data
     */
    update: (id, data) => apiClient.patch(`/services/${id}/`, data),

    /**
     * Деактивировать услугу (только администратор).
     * @param {number} id
     */
    delete: (id) => apiClient.delete(`/services/${id}/`),
};


// ============================================================
//  СЕРВИС СОТРУДНИКОВ
// ============================================================
export const employeeAPI = {
    /**
     * Список сотрудников.
     * @param {Object} params - Фильтры, например: { service: 3 }
     */
    getAll: (params = {}) => apiClient.get('/employees/', { params }),

    /**
     * Детали сотрудника.
     * @param {number} id
     */
    getById: (id) => apiClient.get(`/employees/${id}/`),

    /**
     * Свободные слоты для записи.
     * GET /api/employees/{id}/available-slots/?date=2026-04-15&service=2
     * @param {number} employeeId
     * @param {string} date - Формат: YYYY-MM-DD
     * @param {number} serviceId
     */
    getAvailableSlots: (employeeId, date, serviceId) =>
        apiClient.get(`/employees/${employeeId}/available-slots/`, {
            params: { date, service: serviceId }
        }),
};


// ============================================================
//  СЕРВИС РАСПИСАНИЙ
// ============================================================
export const scheduleAPI = {
    /**
     * Расписание с фильтрацией.
     * @param {Object} params - { employee: 1, month: '2026-04' }
     */
    getAll: (params = {}) => apiClient.get('/schedules/', { params }),

    /**
     * Создать расписание (администратор).
     * @param {Object} data - { employee, work_date, start_time, end_time }
     */
    create: (data) => apiClient.post('/schedules/', data),

    /**
     * Обновить расписание.
     * @param {number} id
     * @param {Object} data
     */
    update: (id, data) => apiClient.patch(`/schedules/${id}/`, data),

    /**
     * Удалить день из расписания.
     * @param {number} id
     */
    delete: (id) => apiClient.delete(`/schedules/${id}/`),
};


// ============================================================
//  СЕРВИС ЗАПИСЕЙ НА ОБСЛУЖИВАНИЕ
// ============================================================
export const appointmentAPI = {
    /**
     * Список записей (клиент видит только свои, администратор — все).
     * @param {Object} params - Фильтры: { status, date, employee }
     */
    getAll: (params = {}) => apiClient.get('/appointments/', { params }),

    /**
     * Детали записи.
     * @param {number} id
     */
    getById: (id) => apiClient.get(`/appointments/${id}/`),

    /**
     * Создать запись на обслуживание.
     * POST /api/appointments/
     * @param {Object} data - { service, employee, appointment_date, appointment_time, client_comment }
     */
    create: (data) => apiClient.post('/appointments/', data),

    /**
     * Обновить запись (администратор меняет статус).
     * @param {number} id
     * @param {Object} data - { status, admin_note, final_price }
     */
    update: (id, data) => apiClient.patch(`/appointments/${id}/`, data),

    /**
     * Отменить запись.
     * POST /api/appointments/{id}/cancel/
     * @param {number} id
     * @param {string} reason - Причина отмены (необязательно)
     */
    cancel: (id, reason = '') => apiClient.post(`/appointments/${id}/cancel/`, { reason }),

    /**
     * История изменений записи (только администратор).
     * @param {number} id
     */
    getLogs: (id) => apiClient.get(`/appointments/${id}/logs/`),
};


// ============================================================
//  СЕРВИС ОТЗЫВОВ
// ============================================================
export const reviewAPI = {
    /**
     * Список отзывов (публичный).
     * @param {Object} params - Фильтры: { service }
     */
    getAll: (params = {}) => apiClient.get('/reviews/', { params }),

    /**
     * Оставить отзыв.
     * @param {Object} data - { appointment, rating, comment }
     */
    create: (data) => apiClient.post('/reviews/', data),
};


// ============================================================
//  СЕРВИС АДМИНИСТРАТОРА
// ============================================================
export const adminAPI = {
    /**
     * Общая статистика для дашборда.
     * GET /api/admin/stats/
     */
    getStats: () => apiClient.get('/admin/stats/'),
};

// Экспортируем по умолчанию для удобного импорта
export default apiClient;
