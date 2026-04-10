import React, { createContext, useState, useEffect, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
import { api } from '@/services/api'; // Bug #3: use shared api service instead of hardcoded localhost

interface User {
    id: string;
    email: string;
    username: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;

    refreshToken: () => Promise<void>;
}

interface JWTPayload {
    sub: string;
    email: string;
    username: string;
    exp: number;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'sentinal_access_token';
const REFRESH_TOKEN_KEY = 'sentinal_refresh_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();

    // Decode and validate token
    const decodeToken = useCallback((accessToken: string): User | null => {
        try {
            const decoded = jwtDecode<JWTPayload>(accessToken);
            if (decoded.exp * 1000 < Date.now()) {
                return null;
            }
            return {
                id: decoded.sub,
                email: decoded.email,
                username: decoded.username,
            };
        } catch (error) {
            console.error('Failed to decode token:', error);
            return null;
        }
    }, []);

    // Bug #13: login wrapped in useCallback for referential stability
    const login = useCallback(async (email: string, password: string) => {
        try {
            // Bug #3: uses api service (reads VITE_API_URL) instead of hardcoded localhost
            const data = await api.login(email, password);

            localStorage.setItem(TOKEN_KEY, data.access_token);
            if (data.refresh_token) {
                localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
            }

            const decodedUser = decodeToken(data.access_token);
            if (decodedUser) {
                setToken(data.access_token);
                setUser(decodedUser);
            } else {
                throw new Error('Invalid token received');
            }
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }, [decodeToken]);

    // Logout function
    const logout = useCallback(async () => {
        try {
            if (token) {
                // Bug #3: uses api service instead of hardcoded localhost
                await api.logout();
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            setToken(null);
            setUser(null);
        }
    }, [token]);

    // Bug #12: refreshToken defined BEFORE useEffect so it's initialized when the effect runs
    // Bug #13: wrapped in useCallback for referential stability
    const refreshToken = useCallback(async () => {
        const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

        if (!storedRefreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            // Bug #3: uses api service instead of hardcoded localhost
            const data = await api.refreshToken(storedRefreshToken);

            localStorage.setItem(TOKEN_KEY, data.access_token);
            if (data.refresh_token) {
                localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
            }

            const decodedUser = decodeToken(data.access_token);
            if (decodedUser) {
                setToken(data.access_token);
                setUser(decodedUser);
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            // B11: await logout so async state cleanup completes before re-throw
            await logout();
            throw error;
        }
    }, [decodeToken, logout]);

    // Initialize auth state from localStorage
    // Bug #12: refreshToken is now defined above, so it's safely in scope here
    useEffect(() => {
        const initAuth = async () => {
            const storedToken = localStorage.getItem(TOKEN_KEY);

            if (storedToken) {
                const decodedUser = decodeToken(storedToken);

                if (decodedUser) {
                    setToken(storedToken);
                    setUser(decodedUser);
                } else {
                    // Token expired, try to refresh
                    try {
                        await refreshToken();
                    } catch {
                        localStorage.removeItem(TOKEN_KEY);
                        localStorage.removeItem(REFRESH_TOKEN_KEY);
                    }
                }
            }

            setIsLoading(false);
        };

        initAuth();
    }, [decodeToken, refreshToken]);

    // Listen for the global logout event fired by the Axios interceptor when
    // token refresh fails. This provides a clean React-state-aware logout without
    // a hard window.location.href reload (which would conflict with React Router).
    useEffect(() => {
        const handleForcedLogout = async () => {
            await logout();
            navigate('/login', { replace: true });
        };
        window.addEventListener('sentinal:logout', handleForcedLogout as EventListener);
        return () => window.removeEventListener('sentinal:logout', handleForcedLogout as EventListener);
    }, [logout, navigate]);


    const value: AuthContextType = {
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        logout,
        refreshToken,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// B17: useAuth guard — throws a descriptive error if used outside <AuthProvider>
export const useAuth = (): AuthContextType => {
    const ctx = useContext(AuthContext);
    if (!ctx) {
        throw new Error('useAuth must be used inside <AuthProvider>. Wrap your component tree with <AuthProvider>.');
    }
    return ctx;
};

