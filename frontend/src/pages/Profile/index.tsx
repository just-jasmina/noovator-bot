import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/layout/Header'
import { LeagueBadge } from '../../components/gamification/LeagueBadge'
import { XPBar, XPChip, StreakBadge } from '../../components/gamification/XPBar'
import { Button } from '../../components/ui/Button'
import { useAuthStore } from '../../store'
import { useTelegram } from '../../hooks/useTelegram'

const LEAGUE_KM: Record<string, number> = {
  novice: 500,
  amateur: 1500,
  professional: 3000,
  innovator: 9999,
}

const STATUS_LABELS: Record<string, string> = {
  pending: '⏳ Tekshiruvda',
  active: '✅ Faol',
  rejected: '❌ Rad etilgan',
  banned: '🚫 Ban',
}

export default function Profile() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { showConfirm } = useTelegram()

  if (!user) return null

  const fullName = [user.last_name, user.first_name, user.middle_name].filter(Boolean).join(' ')
  const km = LEAGUE_KM[user.league] ?? 0
  const progressToNext = user.league !== 'innovator'
    ? Math.min(100, Math.round((user.season_xp / km) * 100))
    : 100

  const handleLogout = () => {
    showConfirm?.('Hisobdan chiqishni istaysizmi?', (confirmed) => {
      if (confirmed) logout()
    })
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header
        title="Profil"
        rightAction={
          <button className="text-xs text-red-400 font-medium px-2 py-1" onClick={handleLogout}>
            Chiqish
          </button>
        }
      />

      <div className="page-container pb-24">
        {/* Profile hero card */}
        <div className="bg-gradient-to-br from-primary-700 to-teal-600 text-white m-4 rounded-3xl p-5 shadow-lg">
          <div className="flex items-center gap-4 mb-5">
            <div className="w-16 h-16 rounded-2xl bg-white/20 flex items-center justify-center text-3xl overflow-hidden border-2 border-white/30">
              {user.avatar_url ? (
                <img src={user.avatar_url} alt="" className="w-full h-full object-cover rounded-2xl" />
              ) : '👤'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-bold text-lg leading-tight truncate">
                {fullName || user.telegram_first_name || 'Foydalanuvchi'}
              </p>
              {user.current_specialty && (
                <p className="text-primary-100 text-sm truncate">{user.current_specialty}</p>
              )}
              {user.workplace && (
                <p className="text-primary-200 text-xs truncate">{user.workplace}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <LeagueBadge league={user.league} />
            <StreakBadge days={user.streak_days} />
            <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">
              {STATUS_LABELS[user.status] ?? user.status}
            </span>
          </div>

          {/* XP stats */}
          <div className="flex gap-4 mb-4">
            <div className="flex-1 bg-white/10 rounded-2xl p-3 text-center">
              <p className="text-2xl font-black">{user.season_xp.toLocaleString()}</p>
              <p className="text-xs text-primary-200">Mavsumiy XP</p>
            </div>
            <div className="flex-1 bg-white/10 rounded-2xl p-3 text-center">
              <p className="text-2xl font-black">{user.global_xp.toLocaleString()}</p>
              <p className="text-xs text-primary-200">Global XP</p>
            </div>
          </div>

          {/* League progress */}
          {user.league !== 'innovator' && (
            <div>
              <div className="flex justify-between text-xs text-primary-100 mb-1">
                <span>Keyingi ligaga: {progressToNext}%</span>
                <span>KM: {km.toLocaleString()} XP</span>
              </div>
              <div className="h-2 bg-white/20 rounded-full">
                <div
                  className="h-full bg-white rounded-full transition-all duration-700"
                  style={{ width: `${progressToNext}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Info sections */}
        <div className="mx-4 flex flex-col gap-3">
          {/* League info */}
          <div className="card p-4">
            <p className="font-bold text-gray-900 mb-3">Liga imtiyozlari</p>
            {[
              { league: 'novice',       icon: '🌱', text: 'Bazaviy status. 1 ta faol loyiha. Matn + 1 fayl.' },
              { league: 'amateur',      icon: '⚡', text: '3 ta faol loyiha. Video-pitch, Figma havola.' },
              { league: 'professional', icon: '💎', text: 'Cheksiz loyihalar. Minnatdorchilik xati. Izoh moderatsiyasi.' },
              { league: 'innovator',    icon: '🏆', text: 'Mentorlik birjasi. Zoom-himoya. Kadrlar zaxirasi.' },
            ].map(item => (
              <div key={item.league} className={`flex gap-3 p-2.5 rounded-xl mb-2 ${user.league === item.league ? 'bg-primary-50 ring-2 ring-primary-200' : 'bg-gray-50'}`}>
                <span className="text-xl">{item.icon}</span>
                <div>
                  <LeagueBadge league={item.league as any} size="sm" />
                  <p className="text-xs text-gray-500 mt-0.5">{item.text}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Personal info */}
          <div className="card p-4">
            <div className="flex justify-between items-center mb-3">
              <p className="font-bold text-gray-900">Shaxsiy ma'lumotlar</p>
              <button className="text-xs text-primary-600 font-semibold" onClick={() => navigate('/settings')}>
                Tahrirlash
              </button>
            </div>
            {[
              { label: 'Email', value: user.email },
              { label: 'Telefon', value: user.phone },
              { label: 'Hudud', value: user.region },
              { label: 'Mutaxassislik', value: user.current_specialty || user.diploma_specialty },
              { label: 'Til', value: user.language === 'uz' ? "O'zbek" : 'Русский' },
            ].map(item => item.value && (
              <div key={item.label} className="flex justify-between py-2 border-b border-gray-50 last:border-0 text-sm">
                <span className="text-gray-400">{item.label}</span>
                <span className="font-medium text-gray-700 max-w-[180px] text-right truncate">{item.value}</span>
              </div>
            ))}
          </div>

          {/* Expert tags (if expert) */}
          {user.role === 'expert' && user.expert_tags && (
            <div className="card p-4">
              <p className="font-bold text-gray-900 mb-2">Ekspert sohalari</p>
              <div className="flex flex-wrap gap-2">
                {user.expert_tags.split(',').map(tag => (
                  <span key={tag} className="tag bg-indigo-50 text-indigo-700 border border-indigo-100">
                    #{tag.trim().replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col gap-2">
            {user.role === 'expert' && (
              <Button variant="primary" fullWidth onClick={() => navigate('/expert/queue')}>
                📋 Ekspert navbati
              </Button>
            )}
            <Button variant="secondary" fullWidth onClick={() => navigate('/my-projects')}>
              📁 Mening loyihalarim
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
