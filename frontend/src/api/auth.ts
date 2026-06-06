import { apiClient } from './client'
import type { User } from '../types'

export const authApi = {
  loginTelegram: async (initData: string) => {
    const res = await apiClient.post<{ access_token: string; user_id: number; is_registered: boolean }>(
      '/auth/telegram',
      { init_data: initData }
    )
    return res.data
  },

  loginExpert: async (username: string, password: string) => {
    const res = await apiClient.post<{ access_token: string; user_id: number; is_registered: boolean }>(
      '/auth/expert/login',
      { username, password }
    )
    return res.data
  },

  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/users/me')
    return res.data
  },

  register: async (data: Record<string, unknown>): Promise<User> => {
    const res = await apiClient.post<User>('/users/register', data)
    return res.data
  },

  updateProfile: async (data: Record<string, unknown>): Promise<User> => {
    const res = await apiClient.put<User>('/users/me', data)
    return res.data
  },
}
