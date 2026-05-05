/**
 * Authentication service for user registration, login, and management
 */

import axios from 'axios';
import { setToken, setUser, clearAuth, getToken } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Register a new user
 */
export const registerUser = async (email: string, password: string, name: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
      email,
      password,
      name,
    });

    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Registration failed');
  }
};

/**
 * Login user
 */
export const loginUser = async (email: string, password: string) => {
  try {
    // Use FormData for OAuth2PasswordRequestForm
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const response = await axios.post(`${API_BASE_URL}/api/auth/login`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    const { access_token, user } = response.data;

    // Store token and user info
    setToken(access_token);
    setUser(user);

    return { access_token, user };
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Login failed');
  }
};

/**
 * Get current user information
 */
export const getCurrentUser = async () => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token');
    }

    const response = await axios.get(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  } catch (error: any) {
    // If unauthorized, clear auth data
    if (error.response?.status === 401) {
      clearAuth();
    }
    throw new Error(error.response?.data?.detail || 'Failed to get user info');
  }
};

/**
 * Logout user
 */
export const logoutUser = () => {
  clearAuth();
};

/**
 * Change password
 */
export const changePassword = async (oldPassword: string, newPassword: string) => {
  try {
    const token = getToken();
    if (!token) {
      throw new Error('No authentication token');
    }

    const response = await axios.post(
      `${API_BASE_URL}/api/auth/change-password`,
      {
        old_password: oldPassword,
        new_password: newPassword,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Password change failed');
  }
};