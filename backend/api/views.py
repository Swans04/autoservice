"""
========================================================
  ФАЙЛ: backend/api/views.py
  НАЗНАЧЕНИЕ: API-обработчики (views) — принимают HTTP-запросы,
  выполняют бизнес-логику и возвращают JSON-ответы.
  Каждый ViewSet обрабатывает группу связанных endpoint'ов.
========================================================
"""

from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer
import datetime
import logging

from .models import User, Service, Employee, Schedule, Appointment, AppointmentLog, Review
from .serializers import (
    RegisterSerializer, UserProfileSerializer,
    ServiceSerializer, EmployeeSerializer, EmployeeBriefSerializer,
    ScheduleSerializer,
    AppointmentCreateSerializer, AppointmentDetailSerializer,
    AppointmentStatusUpdateSerializer, AppointmentLogSerializer,
    ReviewSerializer,
)
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin

# Логгер для этого модуля — все print() заменяем на logger
logger = logging.getLogger('api')
# ============================================================
#  КАСТОМНЫЙ VIEW ДЛЯ ВХОДА ЧЕРЕЗ EMAIL
#  POST /api/auth/login/
#  По умолчанию JWT ищет поле username — мы переопределяем на email
# ============================================================
class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer  # Используем наш сериализатор с email


# ============================================================
#  РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ
#  POST /api/register/
#  Открытый endpoint — аутентификация не требуется
# ============================================================
class RegisterView(generics.CreateAPIView):
    """
    Регистрация нового клиента.
    Тело запроса: { email, username, first_name, last_name, phone, password, password_confirm }
    Ответ: { id, email, username, first_name, last_name, phone }
    """

    permission_classes = [permissions.AllowAny]  # Регистрация — открытый endpoint
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        """
        Переопределяем create() чтобы вернуть красивый ответ
        с сообщением об успехе.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Если ошибка — вернёт 400

        user = serializer.save()

        logger.info(f'Новый пользователь зарегистрирован: {user.email}')

        return Response({
            'message': 'Регистрация прошла успешно. Теперь вы можете войти.',
            'user': {
                'id':    user.id,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)


# ============================================================
#  ПРОФИЛЬ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ
#  GET  /api/profile/  — получить профиль
#  PUT  /api/profile/  — обновить профиль (полностью)
#  PATCH /api/profile/ — обновить профиль (частично)
# ============================================================
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Профиль текущего авторизованного пользователя.
    Каждый видит только свой профиль.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Возвращаем текущего пользователя (из JWT-токена)."""
        return self.request.user  # request.user заполняется JWTAuthentication


# ============================================================
#  СМЕНА ПАРОЛЯ
#  POST /api/change-password/
# ============================================================
class ChangePasswordView(APIView):
    """
    Смена пароля текущего пользователя.
    Тело запроса: { old_password, new_password, new_password_confirm }
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password         = request.data.get('old_password', '')
        new_password         = request.data.get('new_password', '')
        new_password_confirm = request.data.get('new_password_confirm', '')

        # Проверяем старый пароль
        if not user.check_password(old_password):
            return Response(
                {'old_password': 'Неверный текущий пароль.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем совпадение новых паролей
        if new_password != new_password_confirm:
            return Response(
                {'new_password_confirm': 'Пароли не совпадают.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Устанавливаем новый пароль (метод set_password хэширует автоматически)
        user.set_password(new_password)
        user.save()

        logger.info(f'Пользователь {user.email} сменил пароль.')
        return Response({'message': 'Пароль успешно изменён.'})


# ============================================================
#  VIEWSET УСЛУГ
#  GET    /api/services/       — список всех активных услуг
#  GET    /api/services/{id}/  — детали услуги
#  POST   /api/services/       — создать услугу (только админ)
#  PUT    /api/services/{id}/  — обновить услугу (только админ)
#  DELETE /api/services/{id}/  — удалить услугу (только админ)
# ============================================================
class ServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD для услуг автосервиса.
    Клиенты могут только читать, администраторы — всё.
    """

    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrReadOnly]  # Читать могут все, писать — только админ

    def get_queryset(self):
        """
        Возвращаем список услуг.
        Клиенты видят только активные услуги.
        Администратор видит все (включая деактивированные).
        """
        queryset = Service.objects.all()

        # Если не администратор — показываем только активные
        if not (self.request.user.is_authenticated and self.request.user.is_admin):
            queryset = queryset.filter(is_active=True)

        return queryset


# ============================================================
#  VIEWSET СОТРУДНИКОВ
#  GET    /api/employees/              — список сотрудников
#  GET    /api/employees/{id}/         — детали сотрудника
#  GET    /api/employees/{id}/schedule/ — расписание сотрудника
#  GET    /api/employees/{id}/available-slots/ — свободные слоты
# ============================================================
class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Управление сотрудниками.
    Клиенты видят краткую информацию, администраторы — полную.
    """

    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        """
        Выбираем сериализатор в зависимости от роли:
        — Администратор → полный EmployeeSerializer
        — Клиент → краткий EmployeeBriefSerializer
        """
        if self.request.user.is_authenticated and self.request.user.is_admin:
            return EmployeeSerializer
        return EmployeeBriefSerializer

    def get_queryset(self):
        """
        Список сотрудников.
        Фильтрация по услуге: GET /api/employees/?service=3
        """
        queryset = Employee.objects.filter(is_active=True)

        # Фильтрация по услуге (клиент ищет мастера для конкретной услуги)
        service_id = self.request.query_params.get('service')
        if service_id:
            # Используем many-to-many: employees, которые умеют делать эту услугу
            queryset = queryset.filter(services__id=service_id)

        return queryset

    @action(detail=True, methods=['get'], url_path='available-slots')
    def available_slots(self, request, pk=None):
        """
        Дополнительный endpoint: свободные слоты для записи.
        GET /api/employees/{id}/available-slots/?date=2026-04-15&service=2

        Логика:
        1. Берём расписание сотрудника на запрошенный день
        2. Делим рабочий день на слоты (по длительности услуги)
        3. Убираем уже занятые слоты
        4. Возвращаем свободные
        """
        employee = self.get_object()  # Получаем сотрудника по {id} из URL

        # Читаем параметры из строки запроса
        date_str   = request.query_params.get('date')
        service_id = request.query_params.get('service')

        # Дата обязательна
        if not date_str:
            return Response(
                {'error': 'Укажите параметр date (формат: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Парсим дату
        try:
            requested_date = datetime.date.fromisoformat(date_str)  # '2026-04-15' → date объект
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты. Используйте YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем расписание сотрудника на этот день
        try:
            schedule = Schedule.objects.get(
                employee=employee,
                work_date=requested_date,
                is_available=True
            )
        except Schedule.DoesNotExist:
            # Сотрудник не работает в этот день
            return Response({'available_slots': [], 'message': 'Мастер не работает в этот день.'})

        # Определяем длительность слота
        slot_duration = 60  # По умолчанию 60 минут
        if service_id:
            try:
                service = Service.objects.get(id=service_id, is_active=True)
                slot_duration = service.duration_minutes
            except Service.DoesNotExist:
                pass

        # Получаем занятые слоты на этот день
        booked_times = set(
            Appointment.objects.filter(
                employee=employee,
                appointment_date=requested_date,
            ).exclude(status=Appointment.STATUS_CANCELLED)  # Отменённые — не занятые
            .values_list('appointment_time', flat=True)      # Только время, без лишних данных
        )

        # Генерируем все возможные слоты
        available_slots = []
        current_time = datetime.datetime.combine(requested_date, schedule.start_time)
        end_time      = datetime.datetime.combine(requested_date, schedule.end_time)
        slot_delta    = datetime.timedelta(minutes=slot_duration)

        while current_time + slot_delta <= end_time:
            slot_time = current_time.time()

            # Этот слот свободен если:
            # 1. Он не в списке забронированных
            # 2. Он не в прошлом (сегодня нельзя записаться на уже прошедшее время)
            is_booked = slot_time in booked_times
            is_past   = (requested_date == timezone.localdate() and
                         slot_time <= timezone.localtime().time())

            if not is_booked and not is_past:
                available_slots.append(slot_time.strftime('%H:%M'))

            current_time += slot_delta  # Переходим к следующему слоту

        return Response({
            'employee_id':      employee.id,
            'employee_name':    employee.full_name,
            'date':             date_str,
            'slot_duration':    slot_duration,
            'available_slots':  available_slots,
            'total_available':  len(available_slots),
        })


# ============================================================
#  VIEWSET РАСПИСАНИЯ СОТРУДНИКОВ
#  GET    /api/schedules/        — список расписаний
#  GET    /api/schedules/?employee=1&date=2026-04  — фильтрация
# ============================================================
class ScheduleViewSet(viewsets.ModelViewSet):
    """
    Управление расписанием сотрудников.
    Клиенты могут только просматривать.
    """

    serializer_class = ScheduleSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        """
        Возвращаем расписания с поддержкой фильтрации:
        - ?employee=1       — только для сотрудника с id=1
        - ?date=2026-04-15  — только на конкретный день
        - ?month=2026-04    — только на конкретный месяц
        """
        queryset = Schedule.objects.select_related('employee').all()

        # Фильтр по сотруднику
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        # Фильтр по конкретной дате
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(work_date=date)

        # Фильтр по месяцу (формат: 2026-04)
        month = self.request.query_params.get('month')
        if month:
            try:
                year, mon = month.split('-')
                queryset = queryset.filter(work_date__year=year, work_date__month=mon)
            except ValueError:
                pass  # Неверный формат — игнорируем

        return queryset


# ============================================================
#  VIEWSET ЗАПИСЕЙ НА ОБСЛУЖИВАНИЕ
#  GET    /api/appointments/        — список записей
#  POST   /api/appointments/        — создать запись
#  GET    /api/appointments/{id}/   — детали записи
#  PATCH  /api/appointments/{id}/   — обновить запись
#  DELETE /api/appointments/{id}/   — отменить запись
# ============================================================
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    Главный ViewSet — записи на обслуживание.

    Права доступа:
    - Клиент: видит только свои записи, может создавать и отменять
    - Администратор: видит все записи, может менять статусы
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        """
        Разные сериализаторы для разных действий:
        - create → AppointmentCreateSerializer (принимает от клиента)
        - update статуса администратором → AppointmentStatusUpdateSerializer
        - чтение → AppointmentDetailSerializer (возвращает полные данные)
        """
        if self.action == 'create':
            return AppointmentCreateSerializer

        if self.action in ('update', 'partial_update'):
            # Администратор меняет статус — особый сериализатор
            if self.request.user.is_admin:
                return AppointmentStatusUpdateSerializer

        return AppointmentDetailSerializer  # Для GET — полные данные

    def get_queryset(self):
        """
        Список записей в зависимости от роли:
        - Администратор → все записи
        - Клиент → только свои

        Поддерживаемые фильтры:
        - ?status=pending        — по статусу
        - ?date=2026-04-15       — по дате
        - ?employee=1            — по сотруднику (только для админа)
        """
        user = self.request.user

        # Базовый queryset с предварительной загрузкой связанных объектов
        # select_related() — уменьшает количество SQL-запросов (JOIN вместо N запросов)
        queryset = Appointment.objects.select_related(
            'client', 'employee', 'service'
        ).prefetch_related('logs')

        # Фильтруем по роли
        if not user.is_admin:
            queryset = queryset.filter(client=user)  # Клиент видит только свои

        # Фильтр по статусу: ?status=pending
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтр по дате: ?date=2026-04-15
        date_filter = self.request.query_params.get('date')
        if date_filter:
            queryset = queryset.filter(appointment_date=date_filter)

        # Фильтр по сотруднику (только для администратора): ?employee=2
        employee_filter = self.request.query_params.get('employee')
        if employee_filter and user.is_admin:
            queryset = queryset.filter(employee_id=employee_filter)

        return queryset

    def perform_create(self, serializer):
        """
        Вызывается после успешной валидации при создании.
        Создаём запись и тут же пишем в лог.
        """
        appointment = serializer.save()

        # Создаём запись в логе об открытии записи
        AppointmentLog.objects.create(
            appointment=appointment,
            action='created',
            new_status=appointment.status,
            changed_by=self.request.user,
            note='Запись создана клиентом.'
        )

        logger.info(f'Создана запись #{appointment.id} от пользователя {self.request.user.email}')

    def perform_update(self, serializer):
        """
        Вызывается при обновлении записи.
        Сохраняем старый статус для лога.
        """
        old_status = self.get_object().status  # Запоминаем статус ДО изменения
        appointment = serializer.save()

        # Если статус изменился — пишем в лог
        if old_status != appointment.status:
            action_map = {
                Appointment.STATUS_CONFIRMED: 'confirmed',
                Appointment.STATUS_CANCELLED: 'cancelled',
                Appointment.STATUS_COMPLETED: 'completed',
            }
            AppointmentLog.objects.create(
                appointment=appointment,
                action=action_map.get(appointment.status, 'updated'),
                old_status=old_status,
                new_status=appointment.status,
                changed_by=self.request.user,
            )

            logger.info(
                f'Запись #{appointment.id}: статус изменён '
                f'{old_status} → {appointment.status} '
                f'пользователем {self.request.user.email}'
            )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Отмена записи.
        POST /api/appointments/{id}/cancel/

        Клиент может отменить свою запись.
        Администратор — любую.
        Нельзя отменить выполненную запись.
        """
        appointment = self.get_object()

        if appointment.status == Appointment.STATUS_COMPLETED:
            return Response(
                {'error': 'Нельзя отменить уже выполненную запись.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if appointment.status == Appointment.STATUS_CANCELLED:
            return Response(
                {'error': 'Запись уже отменена.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = appointment.status
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.save()

        # Записываем отмену в лог
        AppointmentLog.objects.create(
            appointment=appointment,
            action='cancelled',
            old_status=old_status,
            new_status=Appointment.STATUS_CANCELLED,
            changed_by=request.user,
            note=request.data.get('reason', ''),  # Причина отмены (опционально)
        )

        return Response({'message': 'Запись отменена.', 'status': 'cancelled'})

    @action(detail=True, methods=['get'], url_path='logs')
    def logs(self, request, pk=None):
        """
        История изменений записи.
        GET /api/appointments/{id}/logs/
        Доступно только администратору.
        """
        if not request.user.is_admin:
            return Response(status=status.HTTP_403_FORBIDDEN)

        appointment = self.get_object()
        logs = appointment.logs.all()
        serializer = AppointmentLogSerializer(logs, many=True)
        return Response(serializer.data)


# ============================================================
#  СТАТИСТИКА ДЛЯ АДМИНИСТРАТИВНОЙ ПАНЕЛИ
#  GET /api/admin/stats/
#  Раздел курсовой: 2.4 — "Обсуждение результатов проекта"
# ============================================================
class AdminStatsView(APIView):
    """
    Сводная статистика для дашборда администратора.
    Только для администраторов.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Проверяем права
        if not request.user.is_admin:
            return Response(status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()

        # --- Записи ---
        total_appointments     = Appointment.objects.count()
        pending_appointments   = Appointment.objects.filter(status=Appointment.STATUS_PENDING).count()
        today_appointments     = Appointment.objects.filter(appointment_date=today).count()
        completed_appointments = Appointment.objects.filter(status=Appointment.STATUS_COMPLETED).count()

        # --- Клиенты ---
        total_clients = User.objects.filter(role=User.ROLE_CLIENT).count()

        # --- Средний рейтинг ---
        avg_rating = Review.objects.aggregate(avg=Avg('rating'))['avg']

        # --- Популярные услуги (топ-5) ---
        popular_services = (
            Service.objects
            .annotate(bookings_count=Count('appointments'))  # Считаем записей на каждую услугу
            .order_by('-bookings_count')
            .values('id', 'name', 'bookings_count')[:5]     # Топ-5
        )

        return Response({
            'appointments': {
                'total':     total_appointments,
                'pending':   pending_appointments,
                'today':     today_appointments,
                'completed': completed_appointments,
            },
            'clients': {
                'total': total_clients,
            },
            'rating': {
                'average': round(avg_rating, 2) if avg_rating else None,
                'total_reviews': Review.objects.count(),
            },
            'popular_services': list(popular_services),
        })


# ============================================================
#  VIEWSET ОТЗЫВОВ
#  GET  /api/reviews/               — список отзывов
#  POST /api/reviews/               — оставить отзыв
# ============================================================
class ReviewViewSet(viewsets.ModelViewSet):
    """
    Отзывы клиентов.
    """

    serializer_class = ReviewSerializer

    def get_permissions(self):
        """
        Читать отзывы могут все (даже незарегистрированные).
        Создавать — только авторизованные клиенты.
        """
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Review.objects.select_related(
            'appointment', 'appointment__client', 'appointment__service'
        ).order_by('-created_at')

        # Фильтр по услуге: ?service=2
        service_id = self.request.query_params.get('service')
        if service_id:
            queryset = queryset.filter(appointment__service_id=service_id)

        return queryset

    def perform_create(self, serializer):
        """Сохраняем отзыв."""
        serializer.save()
