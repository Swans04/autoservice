"""
========================================================
  ФАЙЛ: backend/api/serializers.py
  НАЗНАЧЕНИЕ: Сериализаторы — преобразуют объекты Python
  (модели Django) в JSON и обратно.
  Каждый API-запрос проходит через сериализатор:
    JSON → сериализатор → модель → база данных (запись)
    база данных → модель → сериализатор → JSON (чтение)
========================================================
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Service, Employee, EmployeeService, Schedule, Appointment, AppointmentLog, Review


# ============================================================
#  СЕРИАЛИЗАТОР РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЯ
# ============================================================
class RegisterSerializer(serializers.ModelSerializer):
    """
    Используется при регистрации нового клиента.
    Принимает: email, password, password_confirm, first_name, last_name, phone
    Возвращает: данные созданного пользователя (без пароля)
    """

    # Поле подтверждения пароля — только для записи, в базу не сохраняется
    password = serializers.CharField(
        write_only=True,        # Пароль не возвращается в ответе API
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Подтверждение пароля'
    )

    class Meta:
        model = User
        # Поля, которые принимает этот сериализатор
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'phone', 'password', 'password_confirm')
        extra_kwargs = {
            'first_name': {'required': True},   # Имя обязательно
            'last_name':  {'required': True},   # Фамилия обязательна
            'email':      {'required': True},
        }

    def validate(self, attrs):
        """
        Валидация данных перед сохранением.
        Проверяем: совпадают ли пароли, соответствует ли пароль
        требованиям безопасности Django.
        """
        # Проверяем совпадение паролей
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают.'})

        # Проверяем сложность пароля через стандартные валидаторы Django
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})

        return attrs

    def create(self, validated_data):
        """
        Создаём пользователя в базе данных.
        Убираем password_confirm (он не нужен для создания),
        хэшируем пароль методом create_user().
        """
        validated_data.pop('password_confirm')  # Удаляем лишнее поле

        # create_user() автоматически хэширует пароль (bcrypt)
        user = User.objects.create_user(
            username=validated_data.get('username', validated_data['email']),
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role=User.ROLE_CLIENT  # Новый пользователь всегда клиент
        )
        return user


# ============================================================
#  СЕРИАЛИЗАТОР ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ
# ============================================================
class UserProfileSerializer(serializers.ModelSerializer):
    """
    Используется для просмотра и редактирования профиля.
    Пароль через этот сериализатор не меняется (отдельный endpoint).
    """

    # Вычисляемое поле: полное имя (first_name + last_name)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'phone', 'role', 'full_name', 'created_at')
        # email и role нельзя менять через этот сериализатор
        read_only_fields = ('id', 'email', 'role', 'created_at')

    def get_full_name(self, obj):
        """Возвращает 'Иван Иванов' или email если имя не заполнено."""
        name = f'{obj.first_name} {obj.last_name}'.strip()
        return name if name else obj.email


# ============================================================
#  СЕРИАЛИЗАТОР УСЛУГИ
# ============================================================
class ServiceSerializer(serializers.ModelSerializer):
    # image_url — полный URL фото (например http://localhost:8000/media/services/foto.jpg)
    # SerializerMethodField позволяет вычислять поле динамически
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description',
            'duration_minutes', 'price',
            'is_active', 'image', 'image_url'
        ]

    def get_image_url(self, obj):
        # Если фото есть — возвращаем полный URL
        # Если нет — возвращаем None
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# ============================================================
#  СЕРИАЛИЗАТОР КОМПЕТЕНЦИИ СОТРУДНИКА
# ============================================================
class EmployeeServiceSerializer(serializers.ModelSerializer):
    """
    Вложенный сериализатор для отображения услуг сотрудника
    вместе с уровнем мастерства.
    """
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_duration = serializers.IntegerField(source='service.duration_minutes', read_only=True)
    service_price = serializers.DecimalField(source='service.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = EmployeeService
        fields = ('service', 'service_name', 'service_duration', 'service_price', 'skill_level')


# ============================================================
#  СЕРИАЛИЗАТОР СОТРУДНИКА (полный — для админки)
# ============================================================
class EmployeeSerializer(serializers.ModelSerializer):
    # Список услуг сотрудника
    services = ServiceSerializer(many=True, read_only=True)
    # Полный URL фото сотрудника
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'full_name', 'position',
            'qualification', 'phone',
            'photo', 'photo_url',
            'services', 'is_active'
        ]

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None


class EmployeeBriefSerializer(serializers.ModelSerializer):
    # Краткая версия для клиентов
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'full_name', 'position',
            'photo', 'photo_url'
        ]

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None

# ============================================================
#  СЕРИАЛИЗАТОР РАСПИСАНИЯ
# ============================================================
class ScheduleSerializer(serializers.ModelSerializer):
    """
    Расписание сотрудника. Клиент видит эти данные,
    чтобы выбрать доступное время для записи.
    """

    # Добавляем имя сотрудника (чтобы не делать отдельный запрос)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = Schedule
        fields = ('id', 'employee', 'employee_name', 'work_date',
                  'start_time', 'end_time', 'is_available', 'note')

    def validate(self, attrs):
        """
        Проверяем, что время начала раньше времени конца.
        Например: нельзя поставить start_time=18:00, end_time=09:00.
        """
        if attrs.get('start_time') and attrs.get('end_time'):
            if attrs['start_time'] >= attrs['end_time']:
                raise serializers.ValidationError(
                    'Время начала должно быть раньше времени окончания.'
                )
        return attrs


# ============================================================
#  СЕРИАЛИЗАТОР СОЗДАНИЯ ЗАПИСИ (для клиента)
# ============================================================
class AppointmentCreateSerializer(serializers.ModelSerializer):
    """
    Используется когда КЛИЕНТ создаёт запись.
    Клиент может указать только: услугу, сотрудника, дату, время, комментарий.
    Всё остальное (статус, клиент) устанавливается автоматически.
    """

    class Meta:
        model = Appointment
        fields = ('service', 'employee', 'appointment_date', 'appointment_time', 'client_comment')

    def validate_appointment_date(self, value):
        """
        Дата не может быть в прошлом.
        Нельзя записаться на вчера или раньше.
        """
        from django.utils import timezone
        import datetime

        today = timezone.localdate()  # Сегодняшняя дата по часовому поясу сервера
        if value < today:
            raise serializers.ValidationError('Нельзя записаться на прошедшую дату.')
        return value

    def validate(self, attrs):
        """
        Проверяем: нет ли уже записи к этому сотруднику на это время.
        Раздел курсовой 1.3: "исключить конфликты и пересечения в расписании"
        """
        employee         = attrs.get('employee')
        appointment_date = attrs.get('appointment_date')
        appointment_time = attrs.get('appointment_time')

        if employee and appointment_date and appointment_time:
            # Ищем записи к тому же мастеру, на ту же дату и время
            conflict = Appointment.objects.filter(
                employee=employee,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            ).exclude(status=Appointment.STATUS_CANCELLED)  # Отменённые не считаем

            # При обновлении — исключаем текущую запись из проверки
            if self.instance:
                conflict = conflict.exclude(pk=self.instance.pk)

            if conflict.exists():
                raise serializers.ValidationError(
                    'На это время уже есть запись к данному мастеру. '
                    'Пожалуйста, выберите другое время.'
                )

        return attrs

    def create(self, validated_data):
        """
        При создании автоматически привязываем клиента из запроса.
        Клиент не указывает себя сам — берём из JWT-токена.
        """
        # self.context['request'] — текущий HTTP-запрос, из него берём пользователя
        validated_data['client'] = self.context['request'].user
        return super().create(validated_data)


# ============================================================
#  СЕРИАЛИЗАТОР ЗАПИСИ (полный — для чтения)
# ============================================================
class AppointmentDetailSerializer(serializers.ModelSerializer):
    """
    Полная информация о записи с вложенными объектами.
    Используется при GET-запросах (чтение).
    """

    # Вместо просто ID — полные объекты (имя, должность и т.п.)
    client   = UserProfileSerializer(read_only=True)     # Полные данные клиента
    employee = EmployeeBriefSerializer(read_only=True)   # Краткие данные сотрудника
    service  = ServiceSerializer(read_only=True)         # Данные услуги

    # Человекочитаемый статус (например: 'Подтверждена' вместо 'confirmed')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = ('id', 'client', 'employee', 'service', 'appointment_date',
                  'appointment_time', 'status', 'status_display', 'client_comment',
                  'admin_note', 'final_price', 'created_at', 'updated_at')


# ============================================================
#  СЕРИАЛИЗАТОР ОБНОВЛЕНИЯ СТАТУСА ЗАПИСИ (для администратора)
# ============================================================
class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Используется администратором для изменения статуса записи.
    Доступные переходы:
      pending → confirmed (подтвердить)
      pending → cancelled (отменить)
      confirmed → completed (отметить выполненной)
      confirmed → cancelled (отменить подтверждённую)
    """

    class Meta:
        model = Appointment
        fields = ('status', 'admin_note', 'final_price')

    def validate_status(self, value):
        """
        Проверяем допустимость перехода статуса.
        Нельзя, например, перевести 'completed' обратно в 'pending'.
        """
        current = self.instance.status  # Текущий статус из базы

        # Матрица допустимых переходов: {текущий: [допустимые следующие]}
        allowed_transitions = {
            Appointment.STATUS_PENDING:   [Appointment.STATUS_CONFIRMED, Appointment.STATUS_CANCELLED],
            Appointment.STATUS_CONFIRMED: [Appointment.STATUS_COMPLETED, Appointment.STATUS_CANCELLED],
            Appointment.STATUS_COMPLETED: [],  # Выполненную запись нельзя менять
            Appointment.STATUS_CANCELLED: [],  # Отменённую запись нельзя менять
        }

        if value not in allowed_transitions.get(current, []):
            raise serializers.ValidationError(
                f'Нельзя перевести статус с "{current}" на "{value}". '
                f'Допустимые переходы: {allowed_transitions.get(current, [])}'
            )
        return value


# ============================================================
#  СЕРИАЛИЗАТОР ЛОГА ЗАПИСИ
# ============================================================
class AppointmentLogSerializer(serializers.ModelSerializer):
    """
    История изменений записи (только для чтения).
    Показывается в деталях записи в административной панели.
    """

    # Имя пользователя, который внёс изменение
    changed_by_name = serializers.SerializerMethodField()
    action_display  = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = AppointmentLog
        fields = ('id', 'action', 'action_display', 'old_status', 'new_status',
                  'note', 'changed_by_name', 'changed_at')

    def get_changed_by_name(self, obj):
        """Возвращает имя пользователя или 'Система' если изменение автоматическое."""
        if obj.changed_by:
            return obj.changed_by.get_full_name() or obj.changed_by.email
        return 'Система'


# ============================================================
#  СЕРИАЛИЗАТОР ОТЗЫВА
# ============================================================
class ReviewSerializer(serializers.ModelSerializer):
    """
    Отзыв клиента после выполнения услуги.
    """

    # Имя клиента для отображения (берём из привязанной записи)
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ('id', 'appointment', 'rating', 'comment', 'client_name', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_client_name(self, obj):
        """Возвращает имя клиента из связанной записи."""
        if obj.appointment.client:
            return obj.appointment.client.get_full_name() or obj.appointment.client.email
        return 'Аноним'

    def validate_appointment(self, value):
        """
        Проверяем: можно оставить отзыв только на выполненную запись,
        и только если пользователь — владелец этой записи.
        """
        user = self.context['request'].user

        # Отзыв только на свою запись
        if value.client != user:
            raise serializers.ValidationError('Вы можете оставить отзыв только на свою запись.')

        # Только на выполненную запись
        if value.status != Appointment.STATUS_COMPLETED:
            raise serializers.ValidationError('Отзыв можно оставить только после выполнения услуги.')

        # Нельзя оставить два отзыва
        if hasattr(value, 'review'):
            raise serializers.ValidationError('На эту запись уже оставлен отзыв.')

        return value
# ========================================================
# Кастомный сериализатор для входа через email (не username)
# По умолчанию JWT ищет поле username — мы переопределяем это
# ========================================================
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'  # Говорим JWT искать поле email вместо username

    def validate(self, attrs):
        # Берём email и пароль из запроса
        email = attrs.get('email')
        password = attrs.get('password')

        # Ищем пользователя по email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'email': 'Пользователь с таким email не найден'}
            )

        # Проверяем пароль
        if not user.check_password(password):
            raise serializers.ValidationError(
                {'password': 'Неверный пароль'}
            )

        # Проверяем что аккаунт активен
        if not user.is_active:
            raise serializers.ValidationError(
                {'email': 'Аккаунт заблокирован'}
            )

        # Генерируем токены
        refresh = self.get_token(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }
        return data