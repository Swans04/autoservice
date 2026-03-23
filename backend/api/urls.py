"""
========================================================
  ФАЙЛ: backend/api/urls.py
  НАЗНАЧЕНИЕ: Таблица маршрутов API.
  Связывает URL-адреса с соответствующими View-функциями.
========================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,      # Обновление: принимает refresh-токен, возвращает новый access-токен
    TokenVerifyView,       # Проверка: принимает access-токен, подтверждает что он валиден
)
from . import views

# -----------------------------------------------------------
# DefaultRouter автоматически создаёт стандартные маршруты
# для каждого зарегистрированного ViewSet:
#
#   /api/services/        GET  → list()     Список услуг
#   /api/services/        POST → create()   Создать услугу
#   /api/services/{id}/   GET  → retrieve() Детали услуги
#   /api/services/{id}/   PUT  → update()   Обновить услугу
#   /api/services/{id}/   DEL  → destroy()  Удалить услугу
# -----------------------------------------------------------
router = DefaultRouter()

# Регистрируем ViewSet'ы:
# первый аргумент — часть URL (/api/services/, /api/employees/ и т.п.)
# второй — ViewSet
# basename — используется для именования URL (для reverse('api:service-list'))
router.register(r'services',     views.ServiceViewSet,     basename='service')
router.register(r'employees',    views.EmployeeViewSet,    basename='employee')
router.register(r'schedules',    views.ScheduleViewSet,    basename='schedule')
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'reviews',      views.ReviewViewSet,      basename='review')


urlpatterns = [
    # -----------------------------------------------------------
    # АУТЕНТИФИКАЦИЯ (JWT-токены)
    # -----------------------------------------------------------

    # Вход в систему: POST { email, password } → { access, refresh }
    path('auth/login/', views.EmailTokenObtainPairView.as_view(), name='token_obtain'),

    # Обновление токена: POST { refresh } → { access }
    # Используется фронтендом автоматически когда access-токен истёк
    path('auth/refresh/',  TokenRefreshView.as_view(),   name='token_refresh'),

    # Проверка токена: POST { token } → 200 OK или 401
    path('auth/verify/',   TokenVerifyView.as_view(),    name='token_verify'),

    # Регистрация нового пользователя: POST { email, password, ... }
    path('auth/register/', views.RegisterView.as_view(), name='register'),

    # -----------------------------------------------------------
    # ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
    # -----------------------------------------------------------
    # GET /api/profile/   — получить свой профиль
    # PATCH /api/profile/ — обновить профиль
    path('profile/',          views.UserProfileView.as_view(),   name='profile'),
    path('change-password/',  views.ChangePasswordView.as_view(), name='change-password'),

    # -----------------------------------------------------------
    # СТАТИСТИКА (только для администратора)
    # -----------------------------------------------------------
    path('admin/stats/', views.AdminStatsView.as_view(), name='admin-stats'),

    # -----------------------------------------------------------
    # ViewSet маршруты (автоматически от DefaultRouter)
    # Включает: /services/, /employees/, /schedules/, /appointments/, /reviews/
    # -----------------------------------------------------------
    path('', include(router.urls)),
]
