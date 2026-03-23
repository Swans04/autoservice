"""
========================================================
  ФАЙЛ: backend/api/management/commands/populate_db.py
  НАЗНАЧЕНИЕ: Команда для заполнения базы тестовыми данными.
  
  Запуск:
    python manage.py populate_db
  
  Создаёт:
  - Администратора системы
  - Тестового клиента
  - 5 типичных услуг автосервиса
  - 3 сотрудников с компетенциями
  - Расписание на ближайшие 7 дней
  - Несколько тестовых записей
========================================================
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными для разработки'

    def handle(self, *args, **options):
        # Импортируем модели здесь — они уже инициализированы к этому моменту
        from api.models import User, Service, Employee, EmployeeService, Schedule, Appointment

        self.stdout.write('Создаём тестовые данные...\n')

        # ============================================================
        #  СОЗДАЁМ ПОЛЬЗОВАТЕЛЕЙ
        # ============================================================

        # Администратор
        # ⚠️ После создания смените пароль в продакшене!
        admin, created = User.objects.get_or_create(
            email='admin@autoservice.ru',
            defaults={
                'username': 'admin',
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')  # ⚠️ Смените пароль!
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Администратор: admin@autoservice.ru / admin123'))
        else:
            self.stdout.write(f'  · Администратор уже существует')

        # Тестовый клиент
        client, created = User.objects.get_or_create(
            email='client@test.ru',
            defaults={
                'username': 'testclient',
                'first_name': 'Иван',
                'last_name': 'Тестов',
                'phone': '+7 (999) 123-45-67',
                'role': User.ROLE_CLIENT,
            }
        )
        if created:
            client.set_password('client123')  # ⚠️ Только для тестирования
            client.save()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Клиент: client@test.ru / client123'))

        # ============================================================
        #  СОЗДАЁМ УСЛУГИ
        # ============================================================
        services_data = [
            {'name': 'Замена масла и фильтров',  'duration_minutes': 60,  'price': 2500.00,  'description': 'Замена моторного масла, масляного и воздушного фильтров'},
            {'name': 'Шиномонтаж (4 колеса)',    'duration_minutes': 90,  'price': 1800.00,  'description': 'Снятие, монтаж и балансировка 4 колёс'},
            {'name': 'Диагностика двигателя',    'duration_minutes': 120, 'price': 3500.00,  'description': 'Компьютерная диагностика двигателя и систем автомобиля'},
            {'name': 'Замена тормозных колодок', 'duration_minutes': 90,  'price': 4200.00,  'description': 'Замена передних или задних тормозных колодок'},
            {'name': 'ТО (техническое обслуживание)', 'duration_minutes': 180, 'price': 6000.00, 'description': 'Комплексное техническое обслуживание по регламенту'},
        ]

        services = []
        for data in services_data:
            service, created = Service.objects.get_or_create(name=data['name'], defaults=data)
            services.append(service)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Услуга: {service.name}'))

        # ============================================================
        #  СОЗДАЁМ СОТРУДНИКОВ
        # ============================================================
        employees_data = [
            {
                'full_name': 'Петров Алексей Иванович',
                'position': 'Механик',
                'qualification': 'Опыт работы 10 лет. Специализация: двигатели, ходовая часть.',
                'phone': '+7 (999) 111-11-11',
            },
            {
                'full_name': 'Сидоров Михаил Петрович',
                'position': 'Шиномонтажник',
                'qualification': 'Опыт работы 7 лет. Специализация: шиномонтаж, балансировка.',
                'phone': '+7 (999) 222-22-22',
            },
            {
                'full_name': 'Козлов Дмитрий Сергеевич',
                'position': 'Мастер-диагност',
                'qualification': 'Опыт работы 12 лет. Специализация: диагностика, электрика.',
                'phone': '+7 (999) 333-33-33',
            },
        ]

        employees = []
        for data in employees_data:
            emp, created = Employee.objects.get_or_create(
                full_name=data['full_name'], defaults=data
            )
            employees.append(emp)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Сотрудник: {emp.full_name}'))

        # ============================================================
        #  НАЗНАЧАЕМ КОМПЕТЕНЦИИ
        # ============================================================
        # Петров умеет: замена масла, ТО, тормозные колодки
        for service in [services[0], services[4], services[3]]:
            EmployeeService.objects.get_or_create(
                employee=employees[0], service=service,
                defaults={'skill_level': 'senior'}
            )

        # Сидоров умеет: шиномонтаж
        EmployeeService.objects.get_or_create(
            employee=employees[1], service=services[1],
            defaults={'skill_level': 'senior'}
        )

        # Козлов умеет: диагностика, замена масла, ТО
        for service in [services[2], services[0], services[4]]:
            EmployeeService.objects.get_or_create(
                employee=employees[2], service=service,
                defaults={'skill_level': 'senior'}
            )

        self.stdout.write(self.style.SUCCESS('  ✓ Компетенции назначены'))

        # ============================================================
        #  СОЗДАЁМ РАСПИСАНИЕ НА БЛИЖАЙШИЕ 7 ДНЕЙ
        # ============================================================
        today = timezone.localdate()

        for i in range(7):  # 7 дней начиная с сегодня
            work_date = today + datetime.timedelta(days=i)

            # Пропускаем воскресенье (weekday() == 6)
            if work_date.weekday() == 6:
                continue

            for employee in employees:
                # В субботу (weekday() == 5) короткий день
                if work_date.weekday() == 5:
                    start = datetime.time(10, 0)
                    end   = datetime.time(16, 0)
                else:
                    start = datetime.time(9, 0)
                    end   = datetime.time(18, 0)

                Schedule.objects.get_or_create(
                    employee=employee,
                    work_date=work_date,
                    defaults={
                        'start_time': start,
                        'end_time': end,
                        'is_available': True,
                    }
                )

        self.stdout.write(self.style.SUCCESS('  ✓ Расписание создано на 7 дней'))

        # ============================================================
        #  СОЗДАЁМ ТЕСТОВЫЕ ЗАПИСИ
        # ============================================================
        tomorrow = today + datetime.timedelta(days=1)

        test_appointments = [
            {
                'client': client,
                'employee': employees[0],
                'service': services[0],
                'appointment_date': tomorrow,
                'appointment_time': datetime.time(10, 0),
                'status': 'confirmed',
                'client_comment': 'Последнее ТО было год назад.',
            },
            {
                'client': client,
                'employee': employees[1],
                'service': services[1],
                'appointment_date': tomorrow,
                'appointment_time': datetime.time(14, 0),
                'status': 'pending',
                'client_comment': '',
            },
        ]

        for data in test_appointments:
            appt, created = Appointment.objects.get_or_create(
                client=data['client'],
                employee=data['employee'],
                appointment_date=data['appointment_date'],
                appointment_time=data['appointment_time'],
                defaults=data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Запись: {appt.service.name} — {appt.appointment_date} {appt.appointment_time}'
                ))

        self.stdout.write('\n')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write('')
        self.stdout.write('Войдите как администратор:')
        self.stdout.write('  Email:  admin@autoservice.ru')
        self.stdout.write('  Пароль: admin123')
        self.stdout.write('')
        self.stdout.write('Войдите как клиент:')
        self.stdout.write('  Email:  client@test.ru')
        self.stdout.write('  Пароль: client123')
