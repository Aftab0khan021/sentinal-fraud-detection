import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Login } from '../Login';
import { AuthProvider } from '@/contexts/AuthContext';
import { api } from '@/services/api';

// Real base64-encoded JWT for demo@sentinal.ai (exp set far in the future)
const FAKE_DEMO_JWT =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJkZW1vQHNlbnRpbmFsLmFpIiwidXNlcm5hbWUiOiJEZW1vIFVzZXIiLCJleHAiOjE3NzE5NDY1MDJ9.fakesignature';

// Mock the shared api service — factory uses only vi.fn() (no hoisted vars)
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
    // default export is the axios instance — stub minimal interceptors to avoid module errors
    default: {
        interceptors: {
            request: { use: vi.fn() },
            response: { use: vi.fn() },
        },
    },
}));

// Mock the useNavigate hook
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return { ...actual, useNavigate: () => mockNavigate };
});

describe('Login Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorage.clear();
    });

    it('renders login form', () => {
        render(
            <BrowserRouter>
                <AuthProvider>
                    <Login />
                </AuthProvider>
            </BrowserRouter>
        );

        expect(screen.getByText(/SentinAL Login/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
    });

    it('displays demo credentials hint in dev mode', () => {
        render(
            <BrowserRouter>
                <AuthProvider>
                    <Login />
                </AuthProvider>
            </BrowserRouter>
        );

        // Bug #14 fix: hint now shows email only (no raw password exposed)
        expect(
            screen.getByText(/dev mode.*demo@sentinal\.ai/i)
        ).toBeInTheDocument();
    });

    it('shows error alert on failed login', async () => {
        vi.mocked(api.login).mockRejectedValueOnce(
            Object.assign(new Error('Incorrect email or password'), {
                response: { data: { detail: 'Incorrect email or password' } },
            })
        );

        render(
            <BrowserRouter>
                <AuthProvider>
                    <Login />
                </AuthProvider>
            </BrowserRouter>
        );

        fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'test@example.com' } });
        fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'wrongpassword' } });
        fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

        await waitFor(() => {
            expect(screen.getByRole('alert')).toBeInTheDocument();
        });
    });

    it('navigates to home on successful login', async () => {
        vi.mocked(api.login).mockResolvedValueOnce({
            access_token: FAKE_DEMO_JWT,
            refresh_token: 'fake-refresh-token',
            user: { id: '1', email: 'demo@sentinal.ai', username: 'Demo User' },
        });

        render(
            <BrowserRouter>
                <AuthProvider>
                    <Login />
                </AuthProvider>
            </BrowserRouter>
        );

        fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: 'demo@sentinal.ai' } });
        fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: 'demo123' } });
        fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

        await waitFor(() => {
            expect(mockNavigate).toHaveBeenCalledWith('/');
        });
    });

    it('disables form during submission', async () => {
        vi.mocked(api.login).mockImplementation(
            () =>
                new Promise((resolve) =>
                    setTimeout(
                        () =>
                            resolve({
                                access_token: FAKE_DEMO_JWT,
                                refresh_token: 'ref',
                                user: { id: '1', email: 'demo@sentinal.ai', username: 'Demo User' },
                            }),
                        100
                    )
                )
        );

        render(
            <BrowserRouter>
                <AuthProvider>
                    <Login />
                </AuthProvider>
            </BrowserRouter>
        );

        const emailInput = screen.getByLabelText(/Email/i) as HTMLInputElement;
        const passwordInput = screen.getByLabelText(/Password/i) as HTMLInputElement;

        fireEvent.change(emailInput, { target: { value: 'demo@sentinal.ai' } });
        fireEvent.change(passwordInput, { target: { value: 'demo123' } });
        fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

        await waitFor(() => {
            expect(emailInput.disabled).toBe(true);
            expect(passwordInput.disabled).toBe(true);
        });
    });
});
