"""
========================================================
  ФАЙЛ: backend/api/permissions.py
  НАЗНАЧЕНИЕ: Кастомные разрешения для контроля доступа.
  Определяет кто и что может делать в API.
  Раздел курсовой: 2.1 — "разграничение прав доступа"
========================================================
"""

from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение: читать могут все, изменять — только администратор.
    Используется для услуг, сотрудников, расписаний.

    GET, HEAD, OPTIONS — разрешены всем (даже без авторизации)
    POST, PUT, PATCH, DELETE — только администратору
    """

    # SAFE_METHODS — методы только для чтения (не меняют данные)
    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

    def has_permission(self, request, view):
        # Запросы на чтение разрешены всем
        if request.method in self.SAFE_METHODS:
            return True

        # Запросы на изменение — только авторизованным администраторам
        return (
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Разрешение на уровне объекта:
    — Администратор видит и меняет всё
    — Пользователь видит и меняет только своё

    Используется для записей (Appointment).
    """

    def has_object_permission(self, request, view, obj):
        """
        obj — конкретный объект записи (Appointment).
        Проверяем: владелец записи == текущий пользователь?
        """
        # Администратор имеет доступ ко всему
        if request.user.is_admin:
            return True

        # Проверяем владельца объекта
        # Используем getattr для универсальности (obj.client или obj.user)
        owner = getattr(obj, 'client', None) or getattr(obj, 'user', None)
        return owner == request.user
