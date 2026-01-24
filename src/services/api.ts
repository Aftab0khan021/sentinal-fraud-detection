import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('sentinal_access_token');

        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // If error is 401 and we haven't retried yet
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                // Try to refresh the token
                const refreshToken = localStorage.getItem('sentinal_refresh_token');

                if (!refreshToken) {
                    throw new Error('No refresh token available');
                }

                const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
                    refresh_token: refreshToken,
                });

                const { access_token, refresh_token: newRefreshToken } = response.data;

                // Store new tokens
                localStorage.setItem('sentinal_access_token', access_token);
                if (newRefreshToken) {
                    localStorage.setItem('sentinal_refresh_token', newRefreshToken);
                }

                // Retry original request with new token
                if (originalRequest.headers) {
                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                }

                return apiClient(originalRequest);
            } catch (refreshError) {
                // Refresh failed, clear tokens and redirect to login
                localStorage.removeItem('sentinal_access_token');
                localStorage.removeItem('sentinal_refresh_token');

                // Redirect to login page
                window.location.href = '/login';

                return Promise.reject(refreshError);
            }
        }

        return Promise.reject(error);
    }
);

// API service functions
export const api = {
    // Authentication
    login: async (email: string, password: string) => {
        const response = await apiClient.post('/api/auth/login', { email, password });
        return response.data;
    },

    logout: async () => {
        const response = await apiClient.post('/api/auth/logout');
        return response.data;
    },

    refreshToken: async (refreshToken: string) => {
        const response = await apiClient.post('/api/auth/refresh', { refresh_token: refreshToken });
        return response.data;
    },

    // Fraud detection
    analyzeUser: async (userId: number) => {
        const response = await apiClient.get(`/api/analyze/${userId}`);
        return response.data;
    },

    getGraphData: async () => {
        const response = await apiClient.get('/api/graph');
        return response.data;
    },

    getAdvancedExplanation: async (userId: number) => {
        const response = await apiClient.get(`/api/explain/advanced/${userId}`);
        return response.data;
    },

    // Health check
    healthCheck: async () => {
        const response = await apiClient.get('/health');
        return response.data;
    },
};

export default apiClient;
