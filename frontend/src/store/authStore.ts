import { create } from 'zustand'
import type { User } from '../types'
import { authApi } from '../api/auth'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; password: string; full_name: string; phone?: string }) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  loading: false,

  login: async (email, password) => {
    set({ loading: true })
    try {
      const resp = await authApi.login({ email, password })
      localStorage.setItem('access_token', resp.data.access_token)
      localStorage.setItem('refresh_token', resp.data.refresh_token)
      set({ user: resp.data.user, isAuthenticated: true })
    } finally {
      set({ loading: false })
    }
  },

  register: async (data) => {
    set({ loading: true })
    try {
      const resp = await authApi.register(data)
      localStorage.setItem('access_token', resp.data.access_token)
      localStorage.setItem('refresh_token', resp.data.refresh_token)
      set({ user: resp.data.user, isAuthenticated: true })
    } finally {
      set({ loading: false })
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  fetchMe: async () => {
    try {
      const resp = await authApi.me()
      set({ user: resp.data, isAuthenticated: true })
    } catch {
      set({ user: null, isAuthenticated: false })
    }
  },
}))
