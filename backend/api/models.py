from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    ROLE_CLIENT = 'client'
    ROLE_ADMIN  = 'admin'
    ROLE_CHOICES = [
        (ROLE_CLIENT, 'Клиент'),
        (ROLE_ADMIN,  'Администратор'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_CLIENT)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(unique=True)

    groups = models.ManyToManyField(
        'auth.Group', blank=True, related_name='api_user_set'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', blank=True, related_name='api_user_set'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_staff


class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.IntegerField(validators=[MinValueValidator(5)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    # Фото услуги — сохраняется в папку media/services/
    image = models.ImageField(
        upload_to='services/',
        blank=True,
        null=True,
        verbose_name='Фото услуги'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'

    def __str__(self):
        return self.name


class Employee(models.Model):
    full_name = models.CharField(max_length=150)
    position = models.CharField(max_length=100)
    qualification = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    # Фото сотрудника — сохраняется в папку media/employees/
    photo = models.ImageField(
        upload_to='employees/',
        blank=True,
        null=True,
        verbose_name='Фото сотрудника'
    )
    services = models.ManyToManyField(Service, through='EmployeeService', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'employees'

    def __str__(self):
        return self.full_name


class EmployeeService(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    LEVEL_CHOICES = [
        ('junior', 'Начинающий'),
        ('middle', 'Опытный'),
        ('senior', 'Эксперт'),
    ]
    skill_level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='middle')

    class Meta:
        db_table = 'employee_services'
        unique_together = ('employee', 'service')


class Schedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    work_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'schedules'
        unique_together = ('employee', 'work_date')


class Appointment(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        ('pending',   'Ожидает'),
        ('confirmed', 'Подтверждена'),
        ('completed', 'Выполнена'),
        ('cancelled', 'Отменена'),
    ]
    client = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='appointments')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING)
    client_comment = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointments'

    def __str__(self):
        return f'{self.client} — {self.appointment_date}'

    def save(self, *args, **kwargs):
        if self.service and not self.final_price:
            self.final_price = self.service.price
        super().save(*args, **kwargs)


class AppointmentLog(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='logs')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ACTION_CHOICES = [
        ('created',     'Создана'),
        ('confirmed',   'Подтверждена'),
        ('cancelled',   'Отменена'),
        ('completed',   'Выполнена'),
        ('updated',     'Изменена'),
        ('rescheduled', 'Перенесена'),
    ]
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_status = models.CharField(max_length=15, blank=True)
    new_status = models.CharField(max_length=15, blank=True)
    note = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointment_logs'


class Review(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
