import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';
import { AuthContext } from '@/contexts/AuthContext';

// Mock @/services/api so AuthProvider never makes real HTTP calls
vi.mock('@/services/api', () => ({
    api: {
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
        analyzeUser: vi.fn(),
        getGraphData: vi.fn(),
        getAdvancedExplanation: vi.fn(),
        healthCheck: vi.fn(),
    },
    default: { interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } } },
}));

/** Helper to inject a specific auth context value */
const renderWithAuth = (
    authValue: Partial<React.ContextType<typeof AuthContext>>,
    children: React.ReactNode
) => {
    const defaults = {
        isAuthenticated: false,
        isLoading: false,
        user: null,
        token: null,
        login: vi.fn(),
        logout: vi.fn(),
        refreshToken: vi.fn(),
    };
    return render(
        <BrowserRouter>
            <AuthContext.Provider value={{ ...defaults, ...authValue } as React.ContextType<typeof AuthContext>}>
                <ProtectedRoute>{children}</ProtectedRoute>
            </AuthContext.Provider>
        </BrowserRouter>
    );
};

describe('ProtectedRoute', () => {
    it('shows loading state while checking authentication', () => {
        renderWithAuth({ isLoading: true }, <div>Protected Content</div>);
        // ProtectedRoute renders <p>Loading...</p> when isLoading is true
        expect(screen.getByText(/Loading\.\.\./i)).toBeInTheDocument();
    });

    it('redirects to /login when not authenticated', () => {
        renderWithAuth({ isLoading: false, isAuthenticated: false }, <div>Protected Content</div>);
        // Should redirect — child content must NOT be visible
        expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('renders children when authenticated', () => {
        renderWithAuth({ isLoading: false, isAuthenticated: true }, <div>Protected Content</div>);
        expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
});
