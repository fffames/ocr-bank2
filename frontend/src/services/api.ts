import axios from 'axios';
import { getToken, clearAuth } from '../utils/auth';

// Get API URL from environment or use localhost for development
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Direct API instance for uploads (bypass proxy for multipart data)
const directApi = axios.create({
  baseURL: `${API_URL}/api`,
});

// Helper function to add auth header
const addAuthHeader = (config: any) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

// Request interceptor for api
api.interceptors.request.use(
  (config) => {
    return addAuthHeader(config);
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Request interceptor for directApi
directApi.interceptors.request.use(
  (config) => {
    return addAuthHeader(config);
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors
const handleAuthError = (error: any) => {
  if (error.response?.status === 401) {
    // Clear auth data and redirect to login
    clearAuth();
    if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
      window.location.href = '/login';
    }
  }
  return Promise.reject(error);
};

// Response interceptor for api
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    return handleAuthError(error);
  }
);

directApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('Direct API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    return handleAuthError(error);
  }
);

export { directApi, API_URL };
export default api;
