import React, { createContext, useState, useEffect, useCallback } from 'react';
import { jwtDecode } from 'jwt-decode';

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
    logout: () => void;
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

    // Decode and validate token
    const decodeToken = useCallback((accessToken: string): User | null => {
        try {
            const decoded = jwtDecode<JWTPayload>(accessToken);

            // Check if token is expired
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

    // Initialize auth state from localStorage
    useEffect(() => {
        const initAuth = () => {
            const storedToken = localStorage.getItem(TOKEN_KEY);

            if (storedToken) {
                const decodedUser = decodeToken(storedToken);

                if (decodedUser) {
                    setToken(storedToken);
                    setUser(decodedUser);
                } else {
                    // Token expired, try to refresh
                    refreshToken().catch(() => {
                        // Refresh failed, clear everything
                        localStorage.removeItem(TOKEN_KEY);
                        localStorage.removeItem(REFRESH_TOKEN_KEY);
                    });
                }
            }

            setIsLoading(false);
        };

        initAuth();
    }, [decodeToken]);

    // Login function
    const login = async (email: string, password: string) => {
        try {
            const response = await fetch('http://localhost:8000/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();

            // Store tokens
            localStorage.setItem(TOKEN_KEY, data.access_token);
            if (data.refresh_token) {
                localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
            }

            // Decode and set user
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
    };

    // Logout function
    const logout = useCallback(async () => {
        try {
            // Call logout endpoint to invalidate token on server
            if (token) {
                await fetch('http://localhost:8000/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                });
            }
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            // Clear local state regardless of API call success
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(REFRESH_TOKEN_KEY);
            setToken(null);
            setUser(null);
        }
    }, [token]);

    // Refresh token function
    const refreshToken = async () => {
        const storedRefreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

        if (!storedRefreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await fetch('http://localhost:8000/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: storedRefreshToken }),
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();

            // Store new tokens
            localStorage.setItem(TOKEN_KEY, data.access_token);
            if (data.refresh_token) {
                localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
            }

            // Update state
            const decodedUser = decodeToken(data.access_token);
            if (decodedUser) {
                setToken(data.access_token);
                setUser(decodedUser);
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            // Clear everything on refresh failure
            logout();
            throw error;
        }
    };

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
