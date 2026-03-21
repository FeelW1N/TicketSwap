import client from './client'
import type { User } from '../types'

interface AuthResponse {
  access_token: string
  refresh_token: string
  user: User
}

export const authApi = {
  register: (data: { email: string; password: string; full_name: string; phone?: string }) =>
    client.post<AuthResponse>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    client.post<AuthResponse>('/auth/login', data),

  me: () => client.get<User>('/auth/me'),

  forgotPassword: (email: string) =>
    client.post<{ message: string; debug_token?: string }>('/auth/forgot-password', { email }),

  resetPassword: (token: string, password: string) =>
    client.post<{ message: string }>('/auth/reset-password', { token, password }),
}
