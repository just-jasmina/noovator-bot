import { create } from 'zustand'
import type { User } from '../types'

interface AuthStore {
  user: User | null
  token: string | null
  isLoading: boolean
  setUser: (user: User) => void
  setToken: (token: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isLoading: true,
  setUser: (user) => set({ user, isLoading: false }),
  setToken: (token) => {
    localStorage.setItem('access_token', token)
    set({ token })
  },
  logout: () => {
    localStorage.removeItem('access_token')
    set({ user: null, token: null })
  },
}))

interface UIStore {
  activeTab: string
  setActiveTab: (tab: string) => void
}

export const useUIStore = create<UIStore>((set) => ({
  activeTab: 'feed',
  setActiveTab: (activeTab) => set({ activeTab }),
}))
