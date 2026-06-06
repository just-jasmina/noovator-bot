import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useTelegram } from './hooks/useTelegram'
import { useAuthStore } from './store'
import { authApi } from './api/auth'
import { BottomNav } from './components/layout/BottomNav'
import { PageLoader } from './components/ui/Spinner'

// Pages
import Feed from './pages/Feed'
import MyProjects from './pages/MyProjects'
import Leaderboard from './pages/Leaderboard'
import Mentorship from './pages/Mentorship'
import Profile from './pages/Profile'
import Registration from './pages/Registration'
import NewProject from './pages/NewProject'
import ProjectDetail from './pages/ProjectDetail'
import ExpertQueue from './pages/ExpertReview'
import ExpertLogin from './pages/ExpertLogin'

const EXPERT_LOGIN_PATH = '/expert/login'

function isExpertRoute() {
  return window.location.pathname.startsWith('/expert')
}

export default function App() {
  const { initData, isDark } = useTelegram()
  const { user, token, setUser, setToken, isLoading } = useAuthStore()

  useEffect(() => {
    // Expert login page handles its own auth — skip Telegram init
    if (isExpertRoute()) return

    const init = async () => {
      try {
        if (token) {
          const me = await authApi.getMe()
          setUser(me)
          return
        }

        // Use real initData in production; fallback for dev
        const data = initData || (import.meta.env.DEV ? 'dev_mode' : '')
        if (!data) return

        const res = await authApi.loginTelegram(data)
        setToken(res.access_token)
        const me = await authApi.getMe()
        setUser(me)
      } catch {
        useAuthStore.getState().logout()
      }
    }
    init()
  }, [])

  // Apply Telegram dark theme
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
  }, [isDark])

  if (isLoading && !isExpertRoute() && !user) return <PageLoader />

  const isRegistered = user && user.pnfl
  const isActive = user && user.status === 'active'
  const isExpert = user && ['expert', 'moderator', 'admin'].includes(user.role)

  return (
    <BrowserRouter>
      <Toaster
        position="top-center"
        toastOptions={{
          className: 'font-sans text-sm rounded-2xl shadow-lg',
          duration: 3000,
        }}
      />

      <Routes>
        {/* Expert login — always accessible, no Telegram required */}
        <Route path="/expert/login" element={
          isExpert ? <Navigate to="/expert/queue" replace /> : <ExpertLogin />
        } />

        {/* Expert queue — requires expert auth */}
        <Route path="/expert/queue" element={
          isExpert ? <ExpertQueue /> : <Navigate to="/expert/login" replace />
        } />

        {/* Telegram Mini App routes */}
        <Route path="*" element={
          !isRegistered ? (
            <Registration />
          ) : !isActive ? (
            <QuarantineScreen />
          ) : (
            <>
              <Routes>
                <Route path="/" element={<Feed />} />
                <Route path="/my-projects" element={<MyProjects />} />
                <Route path="/projects/new" element={<NewProject />} />
                <Route path="/projects/:id" element={<ProjectDetail />} />
                <Route path="/leaderboard" element={<Leaderboard />} />
                <Route path="/mentorship" element={<Mentorship />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
              <BottomNav />
            </>
          )
        } />
      </Routes>
    </BrowserRouter>
  )
}

function QuarantineScreen() {
  const { user } = useAuthStore()
  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-700 to-primary-900 flex flex-col items-center justify-center p-6 text-white text-center">
      <div className="text-6xl mb-5">⏳</div>
      <h1 className="text-2xl font-black mb-2">Tekshiruvda</h1>
      <p className="text-primary-200 text-sm mb-6 leading-relaxed max-w-xs">
        Hujjatlaringiz moderator tomonidan ko'rib chiqilmoqda.
        Tekshiruv 48 soat ichida amalga oshiriladi.
        Natija Telegram orqali bildiriladi.
      </p>
      <div className="bg-white/10 rounded-3xl p-5 w-full max-w-xs">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center text-2xl">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" className="w-full h-full rounded-2xl object-cover" />
            ) : '👤'}
          </div>
          <div className="text-left">
            <p className="font-bold">{user?.first_name} {user?.last_name}</p>
            <p className="text-xs text-primary-200">{user?.email}</p>
          </div>
        </div>
        <div className="text-xs text-primary-200 space-y-1">
          <div className="flex justify-between">
            <span>Status</span>
            <span className="text-yellow-300 font-semibold">⏳ Kutilmoqda</span>
          </div>
          {user?.region && (
            <div className="flex justify-between">
              <span>Viloyat</span>
              <span>{user.region}</span>
            </div>
          )}
        </div>
      </div>
      <p className="mt-6 text-xs text-primary-300">
        Hujjatlar noto'g'ri bo'lsa, qayta yuborish imkoniyati beriladi.
      </p>
    </div>
  )
}
