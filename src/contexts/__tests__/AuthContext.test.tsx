import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { AuthProvider, AuthContext } from '../AuthContext';
import { api } from '@/services/api';
import React from 'react';

// Real base64-encoded JWTs (exp set ~1 hour in the future from build time)
const FAKE_ACCESS_JWT =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcm5hbWUiOiJUZXN0IFVzZXIiLCJleHAiOjE3NzE5NDY1MDJ9.fakesignature';
const FAKE_NEW_ACCESS_JWT =
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwidXNlcm5hbWUiOiJUZXN0IFVzZXIiLCJleHAiOjE3NzE5NDY1MDJ9.fakesignature';

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
    default: {
        interceptors: {
            request: { use: vi.fn() },
            response: { use: vi.fn() },
        },
    },
}));

// Simple localStorage mock
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: (key: string) => store[key] ?? null,
        setItem: (key: string, value: string) => { store[key] = value.toString(); },
        removeItem: (key: string) => { delete store[key]; },
        clear: () => { store = {}; },
    };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock, writable: true });

describe('AuthContext', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorageMock.clear();
    });

    it('provides authentication context', () => {
        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <AuthProvider>{children}</AuthProvider>
        );

        const { result } = renderHook(() => React.useContext(AuthContext), { wrapper });

        expect(result.current).toBeDefined();
        expect(result.current?.isAuthenticated).toBe(false);
        expect(result.current?.user).toBeNull();
        expect(result.current?.token).toBeNull();
    });

    it('logs in user successfully', async () => {
        const mockUser = { id: '1', email: 'test@example.com', username: 'Test User' };

        vi.mocked(api.login).mockResolvedValueOnce({
            access_token: FAKE_ACCESS_JWT,
            refresh_token: 'fake-refresh-token',
            user: mockUser,
        });

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <AuthProvider>{children}</AuthProvider>
        );

        const { result } = renderHook(() => React.useContext(AuthContext), { wrapper });

        await waitFor(() => {
            expect(result.current?.isLoading).toBe(false);
        });

        await result.current!.login('test@example.com', 'password');

        await waitFor(() => {
            expect(result.current?.isAuthenticated).toBe(true);
            expect(result.current?.user?.email).toBe('test@example.com');
            expect(localStorageMock.getItem('sentinal_access_token')).toBe(FAKE_ACCESS_JWT);
        });
    });

    it('logs out user successfully', async () => {
        localStorageMock.setItem('sentinal_access_token', 'fake-token');
        localStorageMock.setItem('sentinal_refresh_token', 'fake-refresh');

        vi.mocked(api.logout).mockResolvedValueOnce({});

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <AuthProvider>{children}</AuthProvider>
        );

        const { result } = renderHook(() => React.useContext(AuthContext), { wrapper });

        await waitFor(() => {
            expect(result.current?.isLoading).toBe(false);
        });

        await result.current!.logout();

        await waitFor(() => {
            expect(result.current?.isAuthenticated).toBe(false);
            expect(result.current?.user).toBeNull();
            expect(localStorageMock.getItem('sentinal_access_token')).toBeNull();
        });
    });

    it('handles login failure', async () => {
        vi.mocked(api.login).mockRejectedValueOnce(
            Object.assign(new Error('Unauthorized'), {
                response: { data: { detail: 'Invalid credentials' } },
            })
        );

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <AuthProvider>{children}</AuthProvider>
        );

        const { result } = renderHook(() => React.useContext(AuthContext), { wrapper });

        await waitFor(() => {
            expect(result.current?.isLoading).toBe(false);
        });

        await expect(
            result.current!.login('test@example.com', 'wrong-password')
        ).rejects.toThrow();

        expect(result.current?.isAuthenticated).toBe(false);
    });

    it('refreshes token successfully', async () => {
        localStorageMock.setItem('sentinal_refresh_token', 'fake-refresh-token');

        vi.mocked(api.refreshToken).mockResolvedValueOnce({
            access_token: FAKE_NEW_ACCESS_JWT,
            refresh_token: 'new-refresh-token',
        });

        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <AuthProvider>{children}</AuthProvider>
        );

        const { result } = renderHook(() => React.useContext(AuthContext), { wrapper });

        await waitFor(() => {
            expect(result.current?.isLoading).toBe(false);
        });

        await result.current!.refreshToken();

        await waitFor(() => {
            expect(localStorageMock.getItem('sentinal_access_token')).toBe(FAKE_NEW_ACCESS_JWT);
        });
    });
});
