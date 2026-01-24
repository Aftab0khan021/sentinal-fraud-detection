import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { AuthProvider, AuthContext } from '../AuthContext';
import React from 'react';

// Mock fetch
global.fetch = vi.fn();

// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => {
            store[key] = value.toString();
        },
        removeItem: (key: string) => {
            delete store[key];
        },
        clear: () => {
            store = {};
        },
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
});

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
        const mockUser = {
            id: '1',
            email: 'test@example.com',
            username: 'Test User',
        };

        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                access_token: 'fake-access-token',
                refresh_token: 'fake-refresh-token',
                user: mockUser,
            }),
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
            expect(localStorageMock.getItem('sentinal_access_token')).toBe('fake-access-token');
        });
    });

    it('logs out user successfully', async () => {
        localStorageMock.setItem('sentinal_access_token', 'fake-token');
        localStorageMock.setItem('sentinal_refresh_token', 'fake-refresh');

        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => ({}),
        });

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
        (global.fetch as any).mockResolvedValueOnce({
            ok: false,
            json: async () => ({ detail: 'Invalid credentials' }),
        });

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

        (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                access_token: 'new-access-token',
                refresh_token: 'new-refresh-token',
            }),
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
            expect(localStorageMock.getItem('sentinal_access_token')).toBe('new-access-token');
        });
    });
});
