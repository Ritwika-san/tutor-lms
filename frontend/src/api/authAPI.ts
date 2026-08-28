import apiClient from './client';

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'student' | 'tutor' | 'admin';
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
  role: 'student' | 'tutor' | 'admin';
}

export interface LoginRequest {
  email: string;
  password: string;
}

const authAPI = {
  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    console.log('[register] sending request', {
      url: `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/register`,
      email: data.email,
      role: data.role,
    });
    const response = await apiClient.post<TokenResponse>('/auth/register', data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>('/auth/login', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
};

export default authAPI;
