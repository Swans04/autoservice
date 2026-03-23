# АвтоСервис Онлайн — Веб-приложение для записи

Полная реализация курсовой работы:
**«Проектирование веб-приложения для онлайн-записи в автосервис»**

---

## 🗂 Структура проекта

```
autoservice/
├── backend/                     ← Django (Python) — сервер и API
│   ├── api/
│   │   ├── models.py            ← Таблицы базы данных
│   │   ├── serializers.py       ← JSON ↔ объекты Python
│   │   ├── views.py             ← Логика API-endpoint'ов
│   │   ├── urls.py              ← Маршруты API
│   │   ├── permissions.py       ← Права доступа
│   │   ├── signals.py           ← Email-уведомления
│   │   ├── admin.py             ← Встроенная админка Django
│   │   ├── apps.py              ← Конфигурация приложения
│   │   └── management/
│   │       └── commands/
│   │           └── populate_db.py  ← Тестовые данные
│   ├── backend/
│   │   ├── settings.py          ← Настройки Django
│   │   └── urls.py              ← Главные маршруты
│   ├── requirements.txt         ← Python-зависимости
│   └── Dockerfile
│
├── frontend/                    ← React — интерфейс
│   ├── src/
│   │   ├── App.jsx              ← Корневой компонент + роутинг
│   │   ├── index.js             ← Точка входа + PWA
│   │   ├── context/
│   │   │   └── AuthContext.jsx  ← Глобальное состояние авторизации
│   │   ├── pages/
│   │   │   └── Pages.jsx        ← Все страницы (Вход, Главная, Запись, Кабинет, Админка)
│   │   ├── services/
│   │   │   └── api.js           ← Все запросы к API
│   │   └── styles/
│   │       └── App.css          ← Все стили
│   ├── public/
│   │   ├── index.html           ← HTML-оболочка
│   │   ├── manifest.json        ← PWA манифест
│   │   └── service-worker.js    ← PWA кэш + push-уведомления
│   ├── package.json
│   └── Dockerfile
│
└── docker-compose.yml           ← Запуск всего одной командой
```

---

## 🚀 Быстрый старт (через Docker)

### Требования
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Шаги

**1. Откройте файл `docker-compose.yml` и замените заглушки:**

```yaml
POSTGRES_PASSWORD: ВАШ_ПАРОЛЬ        # Придумайте пароль для PostgreSQL
DB_PASSWORD:       ВАШ_ПАРОЛЬ        # Тот же пароль
DJANGO_SECRET_KEY: ВАШ_СЕКРЕТНЫЙ_КЛЮЧ
```

Сгенерировать `SECRET_KEY`:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**2. Запустите проект:**
```bash
docker-compose up --build
```

**3. Заполните базу тестовыми данными (в новом терминале):**
```bash
docker-compose exec backend python manage.py populate_db
```

**4. Откройте в браузере:**
- Приложение: http://localhost:3000
- API:         http://localhost:8000/api/
- Django-Adminка: http://localhost:8000/django-admin/

---

## 🛠 Ручная установка (без Docker)

### Backend

```bash
# 1. Переходим в папку backend
cd backend

# 2. Создаём виртуальное окружение
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows

# 3. Устанавливаем зависимости
pip install -r requirements.txt

# 4. Настраиваем базу данных
#    Откройте settings.py и вставьте данные вашего PostgreSQL
#    (имя БД, пользователь, пароль)

# 5. Применяем миграции (создаём таблицы)
python manage.py migrate

# 6. Создаём суперпользователя
python manage.py createsuperuser

# 7. Заполняем тестовыми данными
python manage.py populate_db

# 8. Запускаем сервер
python manage.py runserver
# Сервер доступен: http://localhost:8000
```

### Frontend

```bash
# 1. Переходим в папку frontend
cd frontend

# 2. Устанавливаем зависимости
npm install

# 3. Запускаем приложение
npm start
# Открывается: http://localhost:3000
```

---

## 🔑 Тестовые аккаунты (после populate_db)

| Роль          | Email                  | Пароль    |
|---------------|------------------------|-----------|
| Администратор | admin@autoservice.ru   | admin123  |
| Клиент        | client@test.ru         | client123 |

---

## 📡 API Endpoint'ы

| Метод | URL                                    | Описание                        | Доступ       |
|-------|----------------------------------------|---------------------------------|--------------|
| POST  | /api/auth/register/                    | Регистрация                     | Открытый     |
| POST  | /api/auth/login/                       | Вход (получить токены)          | Открытый     |
| POST  | /api/auth/refresh/                     | Обновить токен                  | Открытый     |
| GET   | /api/profile/                          | Мой профиль                     | Авторизован  |
| PATCH | /api/profile/                          | Обновить профиль                | Авторизован  |
| GET   | /api/services/                         | Список услуг                    | Открытый     |
| GET   | /api/employees/                        | Список сотрудников              | Открытый     |
| GET   | /api/employees/{id}/available-slots/   | Свободные слоты                 | Открытый     |
| GET   | /api/schedules/                        | Расписание                      | Открытый     |
| GET   | /api/appointments/                     | Мои записи                      | Авторизован  |
| POST  | /api/appointments/                     | Создать запись                  | Авторизован  |
| POST  | /api/appointments/{id}/cancel/         | Отменить запись                 | Авторизован  |
| PATCH | /api/appointments/{id}/                | Изменить статус                 | Администратор|
| GET   | /api/admin/stats/                      | Статистика дашборда             | Администратор|
| GET   | /api/reviews/                          | Отзывы                          | Открытый     |
| POST  | /api/reviews/                          | Оставить отзыв                  | Авторизован  |

---

## ✉️ Настройка email-уведомлений

Добавьте в `backend/settings.py`:

```python
# Для отправки через Gmail:
EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST         = 'smtp.gmail.com'
EMAIL_PORT         = 587
EMAIL_USE_TLS      = True
EMAIL_HOST_USER    = 'ВАШ_EMAIL@gmail.com'
EMAIL_HOST_PASSWORD = 'ПАРОЛЬ_ПРИЛОЖЕНИЯ_GMAIL'
DEFAULT_FROM_EMAIL = 'АвтоСервис <ВАШ_EMAIL@gmail.com>'

# Для тестирования (письма выводятся в консоль):
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

---

## 🛠 Используемые технологии

| Компонент       | Технология              | Версия  |
|-----------------|-------------------------|---------|
| Frontend        | React                   | 18.x    |
| Роутинг         | React Router DOM        | 6.x     |
| HTTP-клиент     | Axios                   | 1.x     |
| Backend         | Django                  | 4.2     |
| REST API        | Django REST Framework   | 3.14    |
| Аутентификация  | JWT (SimpleJWT)         | 5.3     |
| База данных     | PostgreSQL              | 15      |
| Контейнеры      | Docker + Compose        | 3.9     |
| PWA             | Service Worker API      | —       |
