import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { serviceAPI, employeeAPI, appointmentAPI, adminAPI } from '../services/api';

/*
========================================================
  LoginPage — страница входа
========================================================
*/
export function LoginPage() {
    const navigate = useNavigate();
    const { login, error: authError } = useAuth();
    const [formData, setFormData] = useState({ email: '', password: '' });
    const [formError, setFormError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        setFormError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.email || !formData.password) {
            setFormError('Заполните все поля.');
            return;
        }
        setIsLoading(true);
        try {
            const userData = await login(formData.email, formData.password);
            if (userData.role === 'admin' || userData.is_staff) {
                navigate('/admin');
            } else {
                navigate('/dashboard');
            }
        } catch {
            // ошибка уже в authError
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="page-center">
            <div className="auth-card">
                <h1 className="auth-title">Вход в систему</h1>
                <p className="auth-subtitle">Автосервис — онлайн-запись</p>
                <form onSubmit={handleSubmit} noValidate>
                    {(formError || authError) && (
                        <div className="error-block">{formError || authError}</div>
                    )}
                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input id="email" name="email" type="email"
                            value={formData.email} onChange={handleChange}
                            placeholder="your@email.com" disabled={isLoading}/>
                    </div>
                    <div className="form-group">
                        <label htmlFor="password">Пароль</label>
                        <input id="password" name="password" type="password"
                            value={formData.password} onChange={handleChange}
                            placeholder="••••••••" disabled={isLoading}/>
                    </div>
                    <button type="submit" className="btn btn-primary btn-full" disabled={isLoading}>
                        {isLoading ? 'Входим...' : 'Войти'}
                    </button>
                </form>
                <p className="auth-link">
                    Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
                </p>
            </div>
        </div>
    );
}


/*
========================================================
  RegisterPage — страница регистрации
========================================================
*/
export function RegisterPage() {
    const navigate = useNavigate();
    const { register } = useAuth();
    const [formData, setFormData] = useState({
        first_name: '', last_name: '', email: '',
        phone: '', username: '', password: '', password_confirm: ''
    });
    const [errors, setErrors] = useState({});
    const [isLoading, setIsLoading] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        if (name === 'email') {
            setFormData(prev => ({ ...prev, email: value, username: value.split('@')[0] }));
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
        setErrors(prev => ({ ...prev, [name]: '' }));
    };

    const validate = () => {
        const newErrors = {};
        if (!formData.first_name.trim()) newErrors.first_name = 'Введите имя.';
        if (!formData.last_name.trim())  newErrors.last_name  = 'Введите фамилию.';
        if (!formData.email.trim())      newErrors.email      = 'Введите email.';
        if (!formData.phone.trim())      newErrors.phone      = 'Введите телефон.';
        if (!formData.password)          newErrors.password   = 'Введите пароль.';
        if (formData.password && formData.password.length < 8)
            newErrors.password = 'Пароль минимум 8 символов.';
        if (formData.password !== formData.password_confirm)
            newErrors.password_confirm = 'Пароли не совпадают.';
        return newErrors;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const validationErrors = validate();
        if (Object.keys(validationErrors).length > 0) { setErrors(validationErrors); return; }
        setIsLoading(true);
        try {
            await register(formData);
            navigate('/login', { state: { message: 'Регистрация успешна! Войдите.' } });
        } catch (err) {
            setErrors({ general: err.message });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="page-center">
            <div className="auth-card">
                <h1 className="auth-title">Регистрация</h1>
                <form onSubmit={handleSubmit} noValidate>
                    {errors.general && <div className="error-block">{errors.general}</div>}
                    <div className="form-row">
                        <div className="form-group">
                            <label>Имя *</label>
                            <input name="first_name" type="text" value={formData.first_name}
                                onChange={handleChange} placeholder="Иван" disabled={isLoading}/>
                            {errors.first_name && <span className="field-error">{errors.first_name}</span>}
                        </div>
                        <div className="form-group">
                            <label>Фамилия *</label>
                            <input name="last_name" type="text" value={formData.last_name}
                                onChange={handleChange} placeholder="Иванов" disabled={isLoading}/>
                            {errors.last_name && <span className="field-error">{errors.last_name}</span>}
                        </div>
                    </div>
                    <div className="form-group">
                        <label>Email *</label>
                        <input name="email" type="email" value={formData.email}
                            onChange={handleChange} placeholder="ivan@example.com" disabled={isLoading}/>
                        {errors.email && <span className="field-error">{errors.email}</span>}
                    </div>
                    <div className="form-group">
                        <label>Телефон *</label>
                        <input name="phone" type="tel" value={formData.phone}
                            onChange={handleChange} placeholder="+7 (999) 123-45-67" disabled={isLoading}/>
                        {errors.phone && <span className="field-error">{errors.phone}</span>}
                    </div>
                    <div className="form-group">
                        <label>Пароль *</label>
                        <input name="password" type="password" value={formData.password}
                            onChange={handleChange} placeholder="Минимум 8 символов" disabled={isLoading}/>
                        {errors.password && <span className="field-error">{errors.password}</span>}
                    </div>
                    <div className="form-group">
                        <label>Подтвердите пароль *</label>
                        <input name="password_confirm" type="password" value={formData.password_confirm}
                            onChange={handleChange} placeholder="Повторите пароль" disabled={isLoading}/>
                        {errors.password_confirm && <span className="field-error">{errors.password_confirm}</span>}
                    </div>
                    <button type="submit" className="btn btn-primary btn-full" disabled={isLoading}>
                        {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
                    </button>
                </form>
                <p className="auth-link">Уже есть аккаунт? <Link to="/login">Войти</Link></p>
            </div>
        </div>
    );
}


/*
========================================================
  HomePage — главная страница со списком услуг + ФОТО
========================================================
*/
export function HomePage() {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [services, setServices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        serviceAPI.getAll()
            .then(r => setServices(r.data.results || r.data))
            .catch(() => setError('Не удалось загрузить услуги.'))
            .finally(() => setLoading(false));
    }, []);

    const handleBooking = (serviceId) => {
        if (!isAuthenticated) {
            navigate('/login');
        } else {
            navigate(`/booking?service=${serviceId}`);
        }
    };

    if (loading) return <div className="page-loading">Загрузка услуг...</div>;
    if (error)   return <div className="page-error">{error}</div>;

    return (
        <div className="page">
            <section className="hero">
                <h1>Онлайн-запись в автосервис</h1>
                <p>Выберите услугу, мастера и удобное время</p>
            </section>
            <section className="services-section">
                <h2>Наши услуги</h2>
                {services.length === 0 ? (
                    <p className="empty-message">Услуги временно недоступны.</p>
                ) : (
                    <div className="services-grid">
                        {services.map(service => (
                            <div key={service.id} className="service-card">
                                {/* Фото услуги — показываем если есть, иначе заглушка */}
                                <div className="service-image-wrap">
                                    {service.image_url ? (
                                        <img
                                            src={service.image_url}
                                            alt={service.name}
                                            className="service-image"
                                        />
                                    ) : (
                                        <div className="service-image-placeholder">
                                            🔧
                                        </div>
                                    )}
                                </div>
                                <div className="service-card-body">
                                    <h3 className="service-name">{service.name}</h3>
                                    {service.description && (
                                        <p className="service-desc">{service.description}</p>
                                    )}
                                    <div className="service-meta">
                                        <span className="service-duration">⏱ {service.duration_minutes} мин</span>
                                        <span className="service-price">{service.price} ₽</span>
                                    </div>
                                    <button className="btn btn-primary" onClick={() => handleBooking(service.id)}>
                                        Записаться
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
}


/*
========================================================
  BookingPage — страница оформления записи (3 шага) + ФОТО МАСТЕРОВ
========================================================
*/
export function BookingPage() {
    const navigate = useNavigate();
    const { isAuthenticated } = useAuth();
    const [step, setStep] = useState(1);
    const [selectedService,  setSelectedService]  = useState(null);
    const [selectedEmployee, setSelectedEmployee] = useState(null);
    const [selectedDate,     setSelectedDate]     = useState('');
    const [selectedTime,     setSelectedTime]     = useState('');
    const [comment,          setComment]          = useState('');
    const [services,  setServices]  = useState([]);
    const [employees, setEmployees] = useState([]);
    const [slots,     setSlots]     = useState([]);
    const [loading,   setLoading]   = useState(false);
    const [error,     setError]     = useState('');
    const [success,   setSuccess]   = useState(false);

    useEffect(() => {
        if (!isAuthenticated) { navigate('/login'); return; }
        serviceAPI.getAll().then(r => setServices(r.data.results || r.data));
        const params = new URLSearchParams(window.location.search);
        const serviceId = params.get('service');
        if (serviceId) {
            serviceAPI.getById(serviceId).then(r => setSelectedService(r.data));
        }
    }, [isAuthenticated, navigate]);

    useEffect(() => {
        if (selectedService) {
            setLoading(true);
            employeeAPI.getAll({ service: selectedService.id })
                .then(r => setEmployees(r.data.results || r.data))
                .finally(() => setLoading(false));
        }
    }, [selectedService]);

    useEffect(() => {
        if (selectedEmployee && selectedDate && selectedService) {
            setLoading(true);
            setSlots([]);
            setSelectedTime('');
            employeeAPI.getAvailableSlots(selectedEmployee.id, selectedDate, selectedService.id)
                .then(r => setSlots(r.data.available_slots || []))
                .catch(() => setSlots([]))
                .finally(() => setLoading(false));
        }
    }, [selectedEmployee, selectedDate, selectedService]);

    const handleSubmit = async () => {
        if (!selectedService || !selectedEmployee || !selectedDate || !selectedTime) {
            setError('Заполните все поля.');
            return;
        }
        setLoading(true);
        setError('');
        try {
            await appointmentAPI.create({
                service: selectedService.id,
                employee: selectedEmployee.id,
                appointment_date: selectedDate,
                appointment_time: selectedTime,
                client_comment: comment,
            });
            setSuccess(true);
        } catch (err) {
            const errorData = err.response?.data;
            const message = typeof errorData === 'string'
                ? errorData
                : Object.values(errorData || {}).flat().join(' ');
            setError(message || 'Ошибка при создании записи.');
        } finally {
            setLoading(false);
        }
    };

    const today = new Date().toISOString().split('T')[0];

    if (success) {
        return (
            <div className="page page-center">
                <div className="success-card">
                    <div className="success-icon">✓</div>
                    <h2>Запись оформлена!</h2>
                    <p>Ожидайте подтверждения.</p>
                    <div className="success-details">
                        <p><strong>Услуга:</strong> {selectedService?.name}</p>
                        <p><strong>Мастер:</strong> {selectedEmployee?.full_name}</p>
                        <p><strong>Дата:</strong> {selectedDate} в {selectedTime}</p>
                    </div>
                    <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
                        Мои записи
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="page">
            <h1>Запись на обслуживание</h1>
            <div className="steps-indicator">
                {['Услуга', 'Мастер и время', 'Подтверждение'].map((label, idx) => (
                    <div key={idx} className={`step ${step > idx+1 ? 'done' : ''} ${step === idx+1 ? 'active' : ''}`}>
                        <span className="step-num">{idx + 1}</span>
                        <span className="step-label">{label}</span>
                    </div>
                ))}
            </div>
            {error && <div className="error-block">{error}</div>}

            {step === 1 && (
                <div className="step-content">
                    <h2>Шаг 1: Выберите услугу</h2>
                    <div className="services-grid">
                        {services.map(svc => (
                            <div key={svc.id}
                                className={`service-card selectable ${selectedService?.id === svc.id ? 'selected' : ''}`}
                                onClick={() => setSelectedService(svc)}>
                                {/* Фото услуги в форме записи */}
                                <div className="service-image-wrap">
                                    {svc.image_url ? (
                                        <img
                                            src={svc.image_url}
                                            alt={svc.name}
                                            className="service-image"
                                        />
                                    ) : (
                                        <div className="service-image-placeholder">🔧</div>
                                    )}
                                </div>
                                <div className="service-card-body">
                                    <h3>{svc.name}</h3>
                                    <p>{svc.duration_minutes} мин — {svc.price} ₽</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="step-actions">
                        <button className="btn btn-primary" disabled={!selectedService} onClick={() => setStep(2)}>
                            Далее →
                        </button>
                    </div>
                </div>
            )}

            {step === 2 && (
                <div className="step-content">
                    <h2>Шаг 2: Мастер и время</h2>
                    <div className="form-group">
                        <label>Выберите мастера</label>
                        {loading && <p>Загрузка мастеров...</p>}
                        <div className="employees-grid">
                            {employees.map(emp => (
                                <div key={emp.id}
                                    className={`employee-card selectable ${selectedEmployee?.id === emp.id ? 'selected' : ''}`}
                                    onClick={() => setSelectedEmployee(emp)}>
                                    {/* Фото мастера */}
                                    <div className="employee-photo-wrap">
                                        {emp.photo_url ? (
                                            <img
                                                src={emp.photo_url}
                                                alt={emp.full_name}
                                                className="employee-photo"
                                            />
                                        ) : (
                                            <div className="employee-photo-placeholder">
                                                👤
                                            </div>
                                        )}
                                    </div>
                                    <p className="employee-name">{emp.full_name}</p>
                                    <p className="employee-position">{emp.position}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="form-group">
                        <label>Дата</label>
                        <input type="date" value={selectedDate} min={today}
                            onChange={e => setSelectedDate(e.target.value)}/>
                    </div>
                    {selectedEmployee && selectedDate && (
                        <div className="form-group">
                            <label>Доступное время</label>
                            {loading ? <p>Загрузка слотов...</p> : slots.length === 0 ? (
                                <p className="empty-message">Нет свободного времени в этот день.</p>
                            ) : (
                                <div className="time-slots">
                                    {slots.map(slot => (
                                        <button key={slot}
                                            className={`time-slot ${selectedTime === slot ? 'selected' : ''}`}
                                            onClick={() => setSelectedTime(slot)}>
                                            {slot}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                    <div className="step-actions">
                        <button className="btn btn-secondary" onClick={() => setStep(1)}>← Назад</button>
                        <button className="btn btn-primary"
                            disabled={!selectedEmployee || !selectedDate || !selectedTime}
                            onClick={() => setStep(3)}>
                            Далее →
                        </button>
                    </div>
                </div>
            )}

            {step === 3 && (
                <div className="step-content">
                    <h2>Шаг 3: Подтверждение</h2>
                    <div className="booking-summary">
                        <div className="summary-row"><span>Услуга:</span>    <strong>{selectedService?.name}</strong></div>
                        <div className="summary-row"><span>Стоимость:</span> <strong>{selectedService?.price} ₽</strong></div>
                        <div className="summary-row"><span>Мастер:</span>    <strong>{selectedEmployee?.full_name}</strong></div>
                        <div className="summary-row"><span>Дата:</span>      <strong>{selectedDate}</strong></div>
                        <div className="summary-row"><span>Время:</span>     <strong>{selectedTime}</strong></div>
                    </div>
                    <div className="form-group">
                        <label>Комментарий (необязательно)</label>
                        <textarea value={comment} onChange={e => setComment(e.target.value)}
                            placeholder="Опишите проблему..." rows={3}/>
                    </div>
                    <div className="step-actions">
                        <button className="btn btn-secondary" onClick={() => setStep(2)}>← Назад</button>
                        <button className="btn btn-primary" disabled={loading} onClick={handleSubmit}>
                            {loading ? 'Оформление...' : 'Подтвердить запись'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}


/*
========================================================
  DashboardPage — личный кабинет клиента
========================================================
*/
export function DashboardPage() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [appointments, setAppointments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('active');

    useEffect(() => {
        appointmentAPI.getAll()
            .then(r => setAppointments(r.data.results || r.data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    const handleCancel = async (id) => {
        if (!window.confirm('Отменить запись?')) return;
        try {
            await appointmentAPI.cancel(id);
            setAppointments(prev =>
                prev.map(a => a.id === id ? { ...a, status: 'cancelled', status_display: 'Отменена' } : a)
            );
        } catch (err) {
            alert('Не удалось отменить: ' + (err.response?.data?.error || 'Ошибка'));
        }
    };

    const active  = appointments.filter(a => ['pending', 'confirmed'].includes(a.status));
    const history = appointments.filter(a => ['completed', 'cancelled'].includes(a.status));
    const list    = activeTab === 'active' ? active : history;

    const statusColors = {
        pending: 'status-pending', confirmed: 'status-confirmed',
        completed: 'status-completed', cancelled: 'status-cancelled',
    };

    if (loading) return <div className="page-loading">Загрузка...</div>;

    return (
        <div className="page">
            <h1>Личный кабинет</h1>
            <p className="welcome-text">Добро пожаловать, {user?.first_name || user?.email}!</p>
            <div className="dashboard-actions">
                <button className="btn btn-primary" onClick={() => navigate('/booking')}>
                    + Новая запись
                </button>
            </div>
            <div className="tabs">
                <button className={`tab ${activeTab === 'active' ? 'active' : ''}`} onClick={() => setActiveTab('active')}>
                    Активные ({active.length})
                </button>
                <button className={`tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
                    История ({history.length})
                </button>
            </div>
            {list.length === 0 ? (
                <div className="empty-state">
                    <p>{activeTab === 'active' ? 'Нет активных записей.' : 'История пуста.'}</p>
                </div>
            ) : (
                <div className="appointments-list">
                    {list.map(a => (
                        <div key={a.id} className="appointment-card">
                            <div className="appointment-header">
                                <h3>{a.service?.name || 'Услуга'}</h3>
                                <span className={`status-badge ${statusColors[a.status]}`}>
                                    {a.status_display}
                                </span>
                            </div>
                            <div className="appointment-details">
                                {/* Фото мастера в карточке записи */}
                                {a.employee?.photo_url && (
                                    <img
                                        src={a.employee.photo_url}
                                        alt={a.employee.full_name}
                                        className="employee-photo-small"
                                    />
                                )}
                                <p>📅 {a.appointment_date} в {a.appointment_time}</p>
                                <p>👨‍🔧 {a.employee?.full_name}</p>
                                <p>💰 {a.final_price} ₽</p>
                                {a.client_comment && <p>💬 {a.client_comment}</p>}
                            </div>
                            {['pending', 'confirmed'].includes(a.status) && (
                                <button className="btn btn-danger btn-small" onClick={() => handleCancel(a.id)}>
                                    Отменить
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}


/*
========================================================
  AdminPage — панель администратора
========================================================
*/
export function AdminPage() {
    const navigate = useNavigate();
    const { isAdmin } = useAuth();
    const [stats,        setStats]        = useState(null);
    const [appointments, setAppointments] = useState([]);
    const [loading,      setLoading]      = useState(true);
    const [activeTab,    setActiveTab]    = useState('dashboard');
    const [statusFilter, setStatusFilter] = useState('');

    useEffect(() => {
        if (!isAdmin) { navigate('/'); }
    }, [isAdmin, navigate]);

    useEffect(() => {
        setLoading(true);
        Promise.all([
            adminAPI.getStats(),
            appointmentAPI.getAll(statusFilter ? { status: statusFilter } : {}),
        ]).then(([statsRes, appRes]) => {
            setStats(statsRes.data);
            setAppointments(appRes.data.results || appRes.data);
        }).catch(err => console.error(err))
          .finally(() => setLoading(false));
    }, [statusFilter]);

    const handleStatusChange = async (id, newStatus) => {
        try {
            await appointmentAPI.update(id, { status: newStatus });
            setAppointments(prev => prev.map(a => a.id === id ? { ...a, status: newStatus } : a));
        } catch (err) {
            alert('Ошибка: ' + (err.response?.data?.status?.[0] || 'Не удалось изменить'));
        }
    };

    if (loading && !stats) return <div className="page-loading">Загрузка...</div>;

    return (
        <div className="page admin-page">
            <h1>Панель администратора</h1>
            <div className="admin-tabs">
                {[{ key: 'dashboard', label: 'Дашборд' }, { key: 'appointments', label: 'Записи' }].map(tab => (
                    <button key={tab.key}
                        className={`admin-tab ${activeTab === tab.key ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.key)}>
                        {tab.label}
                    </button>
                ))}
            </div>

            {activeTab === 'dashboard' && stats && (
                <div className="stats-grid">
                    {[
                        { title: 'Всего записей',   value: stats.appointments.total,     color: 'blue' },
                        { title: 'Ожидают',         value: stats.appointments.pending,   color: 'orange' },
                        { title: 'Сегодня',         value: stats.appointments.today,     color: 'green' },
                        { title: 'Выполнено',       value: stats.appointments.completed, color: 'teal' },
                        { title: 'Клиентов',        value: stats.clients.total,          color: 'purple' },
                        { title: 'Средний рейтинг', value: stats.rating.average ? `${stats.rating.average} ★` : 'Нет', color: 'yellow' },
                    ].map(s => (
                        <div key={s.title} className={`stat-card stat-${s.color}`}>
                            <p className="stat-value">{s.value}</p>
                            <p className="stat-title">{s.title}</p>
                        </div>
                    ))}
                </div>
            )}

            {activeTab === 'appointments' && (
                <div>
                    <div className="filter-bar">
                        <label>Статус:</label>
                        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                            <option value="">Все</option>
                            <option value="pending">Ожидают</option>
                            <option value="confirmed">Подтверждены</option>
                            <option value="completed">Выполнены</option>
                            <option value="cancelled">Отменены</option>
                        </select>
                    </div>
                    {loading ? <p>Загрузка...</p> : (
                        <div className="admin-table-wrap">
                            <table className="admin-table">
                                <thead>
                                    <tr>
                                        <th>#</th><th>Клиент</th><th>Услуга</th>
                                        <th>Мастер</th><th>Дата и время</th>
                                        <th>Статус</th><th>Действия</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {appointments.map(ap => (
                                        <tr key={ap.id}>
                                            <td>{ap.id}</td>
                                            <td>{ap.client?.full_name || ap.client?.email || '—'}</td>
                                            <td>
                                                {/* Миниатюра фото услуги в таблице */}
                                                {ap.service?.image_url && (
                                                    <img
                                                        src={ap.service.image_url}
                                                        alt={ap.service.name}
                                                        className="table-image"
                                                    />
                                                )}
                                                {ap.service?.name || '—'}
                                            </td>
                                            <td>
                                                {/* Миниатюра фото мастера в таблице */}
                                                {ap.employee?.photo_url && (
                                                    <img
                                                        src={ap.employee.photo_url}
                                                        alt={ap.employee.full_name}
                                                        className="table-image"
                                                    />
                                                )}
                                                {ap.employee?.full_name || '—'}
                                            </td>
                                            <td>{ap.appointment_date} {ap.appointment_time}</td>
                                            <td><span className={`status-badge status-${ap.status}`}>{ap.status_display || ap.status}</span></td>
                                            <td className="action-buttons">
                                                {ap.status === 'pending' && (
                                                    <button className="btn btn-small btn-success"
                                                        onClick={() => handleStatusChange(ap.id, 'confirmed')}>
                                                        Подтвердить
                                                    </button>
                                                )}
                                                {ap.status === 'confirmed' && (
                                                    <button className="btn btn-small btn-primary"
                                                        onClick={() => handleStatusChange(ap.id, 'completed')}>
                                                        Выполнено
                                                    </button>
                                                )}
                                                {['pending', 'confirmed'].includes(ap.status) && (
                                                    <button className="btn btn-small btn-danger"
                                                        onClick={() => handleStatusChange(ap.id, 'cancelled')}>
                                                        Отменить
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}