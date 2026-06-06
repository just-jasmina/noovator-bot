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

function loadInitialUser() {
  try {
    const raw = localStorage.getItem('auth_user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: loadInitialUser(),
  token: localStorage.getItem('access_token'),
  isLoading: true,
  setUser: (user) => {
    localStorage.setItem('auth_user', JSON.stringify(user))
    set({ user, isLoading: false })
  },
  setToken: (token) => {
    localStorage.setItem('access_token', token)
    set({ token })
  },
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('auth_user')
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
