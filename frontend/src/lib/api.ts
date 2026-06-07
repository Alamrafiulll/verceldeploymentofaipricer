import axios from 'axios';

import { createDemoApi, type ApiClient } from './demoApi';

const useRealApi = String(import.meta.env.VITE_USE_REAL_API ?? 'false') === 'true';

const realApi = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api',
});

realApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

realApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401 && !error.config?.url?.includes('/auth/')) {
      localStorage.removeItem('pricing_session');
      localStorage.removeItem('auth_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

const api: ApiClient = useRealApi ? (realApi as unknown as ApiClient) : createDemoApi();

export default api;

