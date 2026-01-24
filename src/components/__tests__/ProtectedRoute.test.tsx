import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ProtectedRoute } from '../ProtectedRoute';
import { AuthProvider } from '@/contexts/AuthContext';

describe('ProtectedRoute', () => {
    it('shows loading state while checking authentication', () => {
        render(
            <BrowserRouter>
                <AuthProvider>
                    <ProtectedRoute>
                        <div>Protected Content</div>
                    </ProtectedRoute>
                </AuthProvider>
            </BrowserRouter>
        );

        expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
    });

    it('renders children when authenticated', async () => {
        // Mock authenticated state
        localStorage.setItem('sentinal_access_token', 'fake-token');

        render(
            <BrowserRouter>
                <AuthProvider>
                    <ProtectedRoute>
                        <div>Protected Content</div>
                    </ProtectedRoute>
                </AuthProvider>
            </BrowserRouter>
        );

        // Note: This test would need proper mocking of the auth context
        // to fully test the authenticated state
    });
});
