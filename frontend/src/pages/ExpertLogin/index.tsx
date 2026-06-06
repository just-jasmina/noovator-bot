import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store'
import toast from 'react-hot-toast'

export default function ExpertLogin() {
  const navigate = useNavigate()
  const { setToken, setUser } = useAuthStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return

    setLoading(true)
    try {
      const res = await authApi.loginExpert(username.trim(), password)
      setToken(res.access_token)
      setUser({
        id: res.user_id as unknown as number,
        role: 'expert',
        status: 'active',
        league: 'novice',
        season_xp: 0,
        global_xp: 0,
        streak_days: 0,
        language: 'uz',
      } as any)
      navigate('/expert/queue', { replace: true })
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Xatolik yuz berdi'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-700 to-primary-900 flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="text-5xl mb-3">🔬</div>
          <h1 className="text-2xl font-black text-white">Expert Panel</h1>
          <p className="text-primary-200 text-sm mt-1">Tibbiyot Novatorlari</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-3xl p-6 shadow-xl space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
              Login
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="expert_login"
              autoComplete="username"
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1 uppercase tracking-wide">
              Parol
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !username.trim() || !password.trim()}
            className="w-full bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-colors"
          >
            {loading ? 'Kirish...' : 'Kirish'}
          </button>
        </form>
      </div>
    </div>
  )
}
