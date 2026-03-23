"""
========================================================
  ФАЙЛ: backend/api/admin.py
  НАЗНАЧЕНИЕ: Регистрация моделей в административной панели Django.
  После регистрации модели появляются по адресу:
  http://localhost:8000/django-admin/
========================================================
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Service, Employee, EmployeeService, Schedule, Appointment, AppointmentLog, Review


# ============================================================
#  АДМИНИСТРИРОВАНИЕ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Кастомный admin для нашей расширенной модели User."""

    # Колонки в списке пользователей
    list_display = ('email', 'first_name', 'last_name', 'role', 'phone', 'is_active', 'created_at')

    # Фильтры в правой панели
    list_filter = ('role', 'is_active', 'is_staff')

    # Поля для поиска
    search_fields = ('email', 'first_name', 'last_name', 'phone')

    # Сортировка по умолчанию
    ordering = ('-created_at',)

    # Добавляем наши поля в форму редактирования
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('role', 'phone')}),
    )


# ============================================================
#  АДМИНИСТРИРОВАНИЕ УСЛУГ
# ============================================================
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display    = ('name', 'duration_minutes', 'price', 'is_active')
    list_filter     = ('is_active',)
    search_fields   = ('name',)
    list_editable   = ('is_active', 'price')  # Менять прямо в списке


# ============================================================
#  АДМИНИСТРИРОВАНИЕ СОТРУДНИКОВ
# ============================================================
class EmployeeServiceInline(admin.TabularInline):
    """Вложенная таблица компетенций внутри формы сотрудника."""
    model  = EmployeeService
    extra  = 1  # Одна пустая строка для добавления


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('full_name', 'position', 'is_active')
    list_filter   = ('is_active',)
    search_fields = ('full_name', 'position')
    inlines       = [EmployeeServiceInline]  # Показываем компетенции внутри сотрудника


# ============================================================
#  АДМИНИСТРИРОВАНИЕ РАСПИСАНИЙ
# ============================================================
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'work_date', 'start_time', 'end_time', 'is_available')
    list_filter   = ('is_available', 'employee')
    date_hierarchy = 'work_date'  # Навигация по датам


# ============================================================
#  АДМИНИСТРИРОВАНИЕ ЗАПИСЕЙ
# ============================================================
class AppointmentLogInline(admin.TabularInline):
    """Лог изменений прямо внутри формы записи."""
    model     = AppointmentLog
    extra     = 0       # Не добавлять пустые строки
    readonly_fields = ('action', 'old_status', 'new_status', 'changed_by', 'changed_at')
    can_delete = False  # Логи нельзя удалять из формы


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ('id', 'client', 'service', 'employee', 'appointment_date', 'appointment_time', 'status')
    list_filter   = ('status', 'appointment_date', 'employee')
    search_fields = ('client__email', 'client__first_name', 'service__name')
    date_hierarchy = 'appointment_date'
    inlines       = [AppointmentLogInline]
    readonly_fields = ('created_at', 'updated_at')


# ============================================================
#  АДМИНИСТРИРОВАНИЕ ОТЗЫВОВ
# ============================================================
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('appointment', 'rating', 'created_at')
    list_filter   = ('rating',)
