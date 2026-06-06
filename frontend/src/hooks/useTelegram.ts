import { useEffect, useState } from 'react'

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp
    }
  }
}

interface TelegramWebApp {
  ready: () => void
  expand: () => void
  close: () => void
  initData: string
  initDataUnsafe: Record<string, unknown>
  colorScheme: 'light' | 'dark'
  themeParams: Record<string, string>
  isExpanded: boolean
  viewportHeight: number
  viewportStableHeight: number
  MainButton: {
    text: string
    color: string
    textColor: string
    isVisible: boolean
    isActive: boolean
    show: () => void
    hide: () => void
    enable: () => void
    disable: () => void
    setText: (text: string) => void
    onClick: (fn: () => void) => void
    offClick: (fn: () => void) => void
  }
  BackButton: {
    isVisible: boolean
    show: () => void
    hide: () => void
    onClick: (fn: () => void) => void
    offClick: (fn: () => void) => void
  }
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
    selectionChanged: () => void
  }
  showPopup: (params: { title?: string; message: string; buttons?: Array<{ type?: string; text?: string }> }, callback?: (id: string) => void) => void
  showConfirm: (message: string, callback: (confirmed: boolean) => void) => void
  showAlert: (message: string, callback?: () => void) => void
  sendData: (data: string) => void
  openLink: (url: string) => void
  openTelegramLink: (url: string) => void
  CloudStorage: {
    setItem: (key: string, value: string, callback?: (err: unknown, stored: boolean) => void) => void
    getItem: (key: string, callback: (err: unknown, value: string | null) => void) => void
    removeItem: (key: string, callback?: (err: unknown, removed: boolean) => void) => void
  }
}

export function useTelegram() {
  const tg = window.Telegram?.WebApp
  const [isDark, setIsDark] = useState(tg?.colorScheme === 'dark')

  useEffect(() => {
    if (!tg) return
    tg.ready()
    tg.expand()
    setIsDark(tg.colorScheme === 'dark')
  }, [tg])

  return {
    tg,
    initData: tg?.initData ?? '',
    isDark,
    haptic: tg?.HapticFeedback,
    mainButton: tg?.MainButton,
    backButton: tg?.BackButton,
    showPopup: tg?.showPopup.bind(tg),
    showConfirm: tg?.showConfirm.bind(tg),
    showAlert: tg?.showAlert.bind(tg),
  }
}
