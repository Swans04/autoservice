"""
========================================================
  ФАЙЛ: backend/api/signals.py
  НАЗНАЧЕНИЕ: Django-сигналы — автоматические действия
  при изменении данных в базе.
  
  Сигналы работают как «триггеры»:
  - post_save  → вызывается ПОСЛЕ сохранения объекта
  - pre_save   → вызывается ДО сохранения
  - post_delete → вызывается после удаления
  
  Здесь реализовано:
  1. Автоматическое создание лога при изменении статуса записи
  2. Отправка email-уведомлений клиенту
  
  Раздел курсовой:
  - 1.3 — "регистрация изменений в записях для аудита"
  - 2.4 — "уведомления"
  
  ⚠️ Не забудьте подключить сигналы в api/apps.py!
========================================================
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import Appointment, AppointmentLog

logger = logging.getLogger('api')


# ============================================================
#  СИГНАЛ: Логирование изменения статуса записи
#  Вызывается каждый раз когда объект Appointment сохраняется
# ============================================================
@receiver(pre_save, sender=Appointment)
def appointment_pre_save(sender, instance, **kwargs):
    """
    Сохраняем старый статус ДО сохранения объекта.
    Django не сохраняет историю изменений автоматически,
    поэтому мы делаем это вручную.
    
    Техника: сохраняем старое значение как атрибут объекта.
    В post_save мы его прочитаем.
    """
    if instance.pk:  # Объект уже существует в базе (не новый)
        try:
            # Читаем ТЕКУЩЕЕ значение из базы (до нашего изменения)
            old_instance = Appointment.objects.get(pk=instance.pk)
            # Сохраняем старый статус как временный атрибут
            instance._old_status = old_instance.status
        except Appointment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None  # Новый объект — нет старого статуса


@receiver(post_save, sender=Appointment)
def appointment_post_save(sender, instance, created, **kwargs):
    """
    Вызывается ПОСЛЕ сохранения объекта Appointment.
    
    created = True  → новая запись создана
    created = False → существующая запись обновлена
    """

    old_status = getattr(instance, '_old_status', None)  # Берём сохранённый старый статус

    if created:
        # --- Новая запись создана ---
        logger.info(f'Создана новая запись #{instance.id}')

        # Отправляем подтверждение клиенту
        send_appointment_email(instance, 'created')

    elif old_status and old_status != instance.status:
        # --- Статус изменился ---
        logger.info(
            f'Запись #{instance.id}: статус изменён '
            f'"{old_status}" → "{instance.status}"'
        )

        # Отправляем уведомление об изменении статуса
        send_appointment_email(instance, instance.status)


# ============================================================
#  ФУНКЦИЯ ОТПРАВКИ EMAIL
#  ⚠️ Для работы нужно настроить EMAIL в settings.py!
# ============================================================
def send_appointment_email(appointment, action):
    """
    Отправляет email-уведомление клиенту при изменении статуса записи.
    
    ⚠️ НАСТРОЙКА EMAIL:
    Добавьте в settings.py следующие строки:
    
    EMAIL_BACKEND   = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST      = 'smtp.gmail.com'   ← или ваш SMTP-сервер
    EMAIL_PORT      = 587
    EMAIL_USE_TLS   = True
    EMAIL_HOST_USER = 'ваш_email@gmail.com'    ← Ваш email отправителя
    EMAIL_HOST_PASSWORD = 'пароль_приложения'   ← Пароль приложения Gmail (не обычный пароль!)
    DEFAULT_FROM_EMAIL = 'АвтоСервис <ваш_email@gmail.com>'
    
    Как получить пароль приложения Gmail:
    1. Войдите в Google аккаунт
    2. Перейдите: Безопасность → Двухэтапная аутентификация → Пароли приложений
    3. Создайте пароль для "Другое приложение" → скопируйте в EMAIL_HOST_PASSWORD
    
    Для тестирования можно использовать консольный бэкенд:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    (письма будут выводиться в консоль, не отправляться реально)
    """

    # Проверяем: есть ли у клиента email
    if not appointment.client or not appointment.client.email:
        return  # Нет email — пропускаем

    client_email = appointment.client.email
    client_name  = appointment.client.get_full_name() or 'Клиент'
    service_name = appointment.service.name if appointment.service else 'Услуга'
    date_str     = appointment.appointment_date.strftime('%d.%m.%Y') if appointment.appointment_date else ''
    time_str     = appointment.appointment_time.strftime('%H:%M') if appointment.appointment_time else ''

    # Тексты писем для каждого типа действия
    email_templates = {
        'created': {
            'subject': f'Ваша запись принята — {service_name}',
            'body': (
                f'Здравствуйте, {client_name}!\n\n'
                f'Ваша запись успешно оформлена:\n'
                f'  Услуга: {service_name}\n'
                f'  Дата:   {date_str} в {time_str}\n'
                f'  Статус: Ожидает подтверждения\n\n'
                f'Мы свяжемся с вами для подтверждения.\n\n'
                f'С уважением,\nАвтоСервис Онлайн'
            ),
        },
        'confirmed': {
            'subject': f'Запись подтверждена — {date_str} в {time_str}',
            'body': (
                f'Здравствуйте, {client_name}!\n\n'
                f'Ваша запись ПОДТВЕРЖДЕНА:\n'
                f'  Услуга: {service_name}\n'
                f'  Дата:   {date_str} в {time_str}\n\n'
                f'Ждём вас! Пожалуйста, приезжайте вовремя.\n\n'
                f'С уважением,\nАвтоСервис Онлайн'
            ),
        },
        'completed': {
            'subject': f'Услуга выполнена — оцените нашу работу',
            'body': (
                f'Здравствуйте, {client_name}!\n\n'
                f'Спасибо за визит! Услуга "{service_name}" выполнена.\n\n'
                f'Оставьте отзыв о нашей работе в личном кабинете.\n'
                f'Ваше мнение помогает нам становиться лучше!\n\n'
                f'С уважением,\nАвтоСервис Онлайн'
            ),
        },
        'cancelled': {
            'subject': f'Запись отменена — {service_name}',
            'body': (
                f'Здравствуйте, {client_name}!\n\n'
                f'Ваша запись на {service_name} ({date_str}) была отменена.\n\n'
                f'Если это ошибка или вы хотите перенести запись,\n'
                f'свяжитесь с нами или создайте новую запись на сайте.\n\n'
                f'С уважением,\nАвтоСервис Онлайн'
            ),
        },
    }

    template = email_templates.get(action)
    if not template:
        return  # Неизвестное действие — пропускаем

    try:
        send_mail(
            subject=template['subject'],
            message=template['body'],
            from_email=settings.DEFAULT_FROM_EMAIL,  # Из settings.py
            recipient_list=[client_email],            # Кому отправить
            fail_silently=False,                      # False = исключение при ошибке
        )
        logger.info(f'Email отправлен: {client_email} ({action})')

    except Exception as e:
        # Логируем ошибку, но не прерываем работу системы
        logger.error(f'Не удалось отправить email ({client_email}): {e}')
