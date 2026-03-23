/*
========================================================
  ФАЙЛ: frontend/src/context/AuthContext.jsx
  НАЗНАЧЕНИЕ: Глобальный контекст аутентификации.
  
  React Context — способ передавать данные через дерево
  компонентов без необходимости пробрасывать пропсы вручную.
  
  Здесь хранится: текущий пользователь, статус загрузки,
  функции login/logout доступны в любом компоненте через
  хук useAuth().
========================================================
*/

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/api';

// -----------------------------------------------------------
// Создаём контекст с null как начальным значением.
// null означает: провайдер ещё не обернул компонент.
// -----------------------------------------------------------
const AuthContext = createContext(null);

/**
 * AuthProvider — оборачивает всё приложение, делая
 * данные о пользователе доступными везде.
 * 
 * Использование в App.jsx:
 *   <AuthProvider>
 *     <App />
 *   </AuthProvider>
 */
export function AuthProvider({ children }) {
    // user — объект пользователя { id, email, role, first_name, ... } или null
    const [user, setUser] = useState(null);

    // loading — true пока идёт проверка авторизации при загрузке страницы
    const [loading, setLoading] = useState(true);

    // error — сообщение об ошибке при входе
    const [error, setError] = useState(null);

    // -----------------------------------------------------------
    // При первой загрузке приложения проверяем — есть ли
    // сохранённый токен и загружаем профиль пользователя.
    // Это позволяет "помнить" пользователя между сессиями.
    // -----------------------------------------------------------
    useEffect(() => {
        const initializeAuth = async () => {
            // Есть ли токен в localStorage?
            if (authService.isAuthenticated()) {
                try {
                    // Сначала пробуем взять кэшированные данные (быстро)
                    const cachedUser = authService.getCurrentUser();
                    if (cachedUser) {
                        setUser(cachedUser);
                    }

                    // Затем обновляем с сервера (актуальные данные)
                    const response = await authService.getProfile();
                    const freshUser = response.data;
                    setUser(freshUser);
                    authService.setCurrentUser(freshUser);  // Обновляем кэш

                } catch (err) {
                    // Токен недействителен — очищаем
                    authService.logout();
                    setUser(null);
                }
            }
            
            setLoading(false);  // Загрузка завершена
        };

        initializeAuth();
    }, []);  // [] — запускается только один раз при монтировании


    /**
     * Функция входа.
     * Вызывается из LoginPage при нажатии "Войти".
     * 
     * @param {string} email
     * @param {string} password
     * @returns {Object} Данные пользователя
     * @throws {Error} Если неверные данные
     */
    const login = useCallback(async (email, password) => {
        setError(null);  // Очищаем предыдущую ошибку
        
        try {
            // authService.login сохраняет токены в localStorage
            await authService.login(email, password);
            
            // Загружаем профиль пользователя
            const profileResponse = await authService.getProfile();
            const userData = profileResponse.data;
            
            // Сохраняем в состоянии и в кэш
            setUser(userData);
            authService.setCurrentUser(userData);
            
            return userData;
        } catch (err) {
            // Обрабатываем разные типы ошибок
            const message =
                err.response?.data?.detail ||           // Ошибка от Django
                err.response?.data?.non_field_errors?.[0] ||
                'Неверный email или пароль.';
            
            setError(message);
            throw new Error(message);
        }
    }, []);


    /**
     * Функция регистрации.
     * @param {Object} data - Данные нового пользователя
     */
    const register = useCallback(async (data) => {
        setError(null);
        
        try {
            const response = await authService.register(data);
            return response.data;
        } catch (err) {
            // Собираем все ошибки валидации в одно сообщение
            const errors = err.response?.data;
            if (errors) {
                const messages = Object.entries(errors)
                    .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
                    .join('\n');
                setError(messages);
                throw new Error(messages);
            }
            throw err;
        }
    }, []);


    /**
     * Функция выхода.
     * Очищает состояние и токены.
     */
    const logout = useCallback(() => {
        setUser(null);       // Очищаем состояние React
        authService.logout(); // Очищает localStorage и редиректит на /login
    }, []);


    /**
     * Обновить данные пользователя в контексте.
     * Используется после редактирования профиля.
     * @param {Object} updatedData
     */
    const updateUser = useCallback((updatedData) => {
        setUser(prev => {
            const newUser = { ...prev, ...updatedData };  // Мержим новые данные
            authService.setCurrentUser(newUser);           // Обновляем кэш
            return newUser;
        });
    }, []);


    // Значение, доступное через useAuth() в любом компоненте
    const contextValue = {
        user,          // Объект пользователя или null
        loading,       // true пока идёт инициализация
        error,         // Сообщение об ошибке
        login,         // Функция входа
        logout,        // Функция выхода
        register,      // Функция регистрации
        updateUser,    // Обновить данные пользователя
        isAuthenticated: !!user,              // Boolean: авторизован ли?
        isAdmin: user?.role === 'admin' || user?.is_staff,  // Boolean: администратор?
    };

    return (
        <AuthContext.Provider value={contextValue}>
            {/* Не рендерим приложение пока идёт проверка авторизации */}
            {/* Иначе будет мигание: сначала "Войти", потом "Профиль" */}
            {!loading && children}
        </AuthContext.Provider>
    );
}

/**
 * Хук для использования контекста аутентификации.
 * 
 * Пример использования в компоненте:
 *   const { user, login, logout, isAdmin } = useAuth();
 * 
 * @returns {Object} Контекст аутентификации
 * @throws {Error} Если используется вне AuthProvider
 */
export function useAuth() {
    const context = useContext(AuthContext);
    
    if (!context) {
        throw new Error('useAuth() должен использоваться внутри <AuthProvider>');
    }
    
    return context;
}

export default AuthContext;
