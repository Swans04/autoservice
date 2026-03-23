"""
========================================================
  ФАЙЛ: backend/backend/urls.py
  НАЗНАЧЕНИЕ: Главный файл маршрутов всего проекта Django.
  Подключает маршруты из приложения api/ и встроенной админки.
========================================================
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Встроенная административная панель Django
    # Доступна по адресу: http://localhost:8000/django-admin/
    # ⚠️ Это НЕ наша кастомная панель — это технический интерфейс Django
    path('django-admin/', admin.site.urls),

    # Все наши API-маршруты подключаем с префиксом /api/
    # Пример: /api/services/, /api/appointments/, /api/auth/login/
    path('api/', include('api.urls')),
]

# --- Отдача медиафайлов в режиме разработки ---
# В продакшене медиафайлы должен отдавать nginx, не Django!
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,           # URL-префикс: /media/
        document_root=settings.MEDIA_ROOT  # Физический путь к файлам
    )
