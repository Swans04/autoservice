/*
========================================================
  ФАЙЛ: frontend/src/App.jsx
  НАЗНАЧЕНИЕ: Корневой компонент приложения.
  Здесь настроены:
  - Роутинг (какая страница показывается по какому URL)
  - Защищённые маршруты (только для авторизованных)
  - Навигационная шапка
========================================================
*/

import { BrowserRouter, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import {
    LoginPage,
    RegisterPage,
    HomePage,
    BookingPage,
    DashboardPage,
    AdminPage
} from './pages/Pages';
import './styles/App.css';  // Подключаем глобальные стили


// ============================================================
//  КОМПОНЕНТ ЗАЩИЩЁННОГО МАРШРУТА
//  Если пользователь не авторизован — перенаправляет на вход.
//  Если нужна роль admin — проверяет роль.
// ============================================================
function ProtectedRoute({ children, adminOnly = false }) {
    const { isAuthenticated, isAdmin } = useAuth();
    const location = useLocation();  // Текущий URL — для сохранения после входа

    if (!isAuthenticated) {
        // Сохраняем текущий URL, чтобы после входа вернуть пользователя сюда
        return <Navigate to="/login" state={{ redirect: location.pathname }} replace />;
    }

    if (adminOnly && !isAdmin) {
        // Авторизован, но не администратор — на главную
        return <Navigate to="/" replace />;
    }

    return children;  // Всё в порядке — рендерим защищённую страницу
}


// ============================================================
//  НАВИГАЦИОННАЯ ШАПКА
// ============================================================
function Header() {
    const { user, isAuthenticated, isAdmin, logout } = useAuth();

    return (
        <header className="header">
            <div className="header-inner">
                {/* Логотип / ссылка на главную */}
                <Link to="/" className="logo">
                    🔧 АвтоСервис
                </Link>

                {/* Навигационные ссылки */}
                <nav className="nav">
                    <Link to="/" className="nav-link">Услуги</Link>

                    {isAuthenticated ? (
                        <>
                            <Link to="/booking" className="nav-link">Записаться</Link>

                            {isAdmin ? (
                                /* Администратор видит ссылку на панель управления */
                                <Link to="/admin" className="nav-link">Панель управления</Link>
                            ) : (
                                /* Клиент видит ссылку на личный кабинет */
                                <Link to="/dashboard" className="nav-link">Мои записи</Link>
                            )}

                            {/* Имя пользователя и кнопка выхода */}
                            <span className="nav-user">
                                {user?.first_name || user?.email}
                            </span>
                            <button className="btn btn-ghost" onClick={logout}>
                                Выйти
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="nav-link">Войти</Link>
                            <Link to="/register" className="btn btn-primary btn-small">
                                Регистрация
                            </Link>
                        </>
                    )}
                </nav>
            </div>
        </header>
    );
}


// ============================================================
//  ГЛАВНЫЙ КОМПОНЕНТ ПРИЛОЖЕНИЯ
// ============================================================
function AppContent() {
    return (
        <div className="app">
            <Header />

            <main className="main-content">
                <Routes>
                    {/* Публичные маршруты (доступны всем) */}
                    <Route path="/"         element={<HomePage />} />
                    <Route path="/login"    element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />

                    {/* Защищённые маршруты (только авторизованные) */}
                    <Route path="/booking" element={
                        <ProtectedRoute>
                            <BookingPage />
                        </ProtectedRoute>
                    } />

                    <Route path="/dashboard" element={
                        <ProtectedRoute>
                            <DashboardPage />
                        </ProtectedRoute>
                    } />

                    {/* Маршрут только для администратора */}
                    <Route path="/admin" element={
                        <ProtectedRoute adminOnly={true}>
                            <AdminPage />
                        </ProtectedRoute>
                    } />

                    {/* Любой другой URL → главная */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
            </main>

            <footer className="footer">
                <p>© 2026 АвтоСервис Онлайн. Все права защищены.</p>
            </footer>
        </div>
    );
}


// ============================================================
//  ЭКСПОРТИРУЕМЫЙ ROOT-КОМПОНЕНТ
//  Оборачивает всё в BrowserRouter (роутер) и AuthProvider
// ============================================================
export default function App() {
    return (
        <BrowserRouter>
            {/* AuthProvider должен быть ВНУТРИ BrowserRouter
                чтобы logout() мог использовать navigate */}
            <AuthProvider>
                <AppContent />
            </AuthProvider>
        </BrowserRouter>
    );
}
