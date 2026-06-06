import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/layout/Header'
import { LeagueBadge } from '../../components/gamification/LeagueBadge'
import { Button } from '../../components/ui/Button'
import { Spinner } from '../../components/ui/Spinner'
import { apiClient } from '../../api/client'
import { useAuthStore } from '../../store'
import toast from 'react-hot-toast'
import clsx from 'clsx'

interface MentorEntry {
  user_id: number
  first_name?: string
  last_name?: string
  avatar_url?: string
  tags: string[]
  global_xp: number
  active_mentorships: number
  slots_available: number
}

export default function Mentorship() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [mentors, setMentors] = useState<MentorEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [requesting, setRequesting] = useState<number | null>(null)
  const [tab, setTab] = useState<'exchange' | 'my'>('exchange')

  useEffect(() => {
    apiClient.get('/mentorship/exchange').then(r => setMentors(r.data)).finally(() => setLoading(false))
  }, [])

  const handleRequest = async (mentorId: number) => {
    setRequesting(mentorId)
    try {
      // In production: show project selector modal
      toast.success('Mentorlik so\'rovi yuborildi!')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Xatolik')
    } finally {
      setRequesting(null)
    }
  }

  const isMentor = user?.league === 'innovator'

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header title="🤝 Mentorlik" />

      {/* Tabs */}
      <div className="bg-white border-b border-gray-100 flex sticky top-[61px] z-30">
        {[
          { key: 'exchange', label: 'Mentor birjasi' },
          { key: 'my', label: 'Mening mentorligim' },
        ].map(t => (
          <button
            key={t.key}
            className={clsx('flex-1 py-3 text-sm font-semibold border-b-2 transition-all',
              tab === t.key ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-400')}
            onClick={() => setTab(t.key as 'exchange' | 'my')}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 page-container pb-24">
        {tab === 'exchange' && (
          <div className="px-4 pt-4 flex flex-col gap-3">
            {/* Info banner */}
            <div className="bg-gradient-to-br from-purple-600 to-indigo-700 rounded-3xl p-5 text-white">
              <p className="font-bold text-lg mb-1">Mentor Birjasi</p>
              <p className="text-purple-200 text-sm">
                Novator ligasidagi mutaxassislar loyihangizga mentorlik qila oladi.
                Muvaffaqiyatda mentor +500 XP, muallif ham bonus oladi.
              </p>
              <div className="flex gap-3 mt-4">
                <div className="bg-white/20 rounded-2xl p-3 flex-1 text-center">
                  <p className="text-2xl font-black">{mentors.length}</p>
                  <p className="text-xs text-purple-200">Bo'sh mentor</p>
                </div>
                <div className="bg-white/20 rounded-2xl p-3 flex-1 text-center">
                  <p className="text-2xl font-black">2</p>
                  <p className="text-xs text-purple-200">Max loyiha/mentor</p>
                </div>
                <div className="bg-white/20 rounded-2xl p-3 flex-1 text-center">
                  <p className="text-2xl font-black">+500</p>
                  <p className="text-xs text-purple-200">XP bonusi</p>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="flex justify-center py-10"><Spinner size="lg" /></div>
            ) : mentors.length === 0 ? (
              <div className="text-center py-10">
                <p className="text-4xl mb-2">🏆</p>
                <p className="text-gray-500">Hozircha bo'sh mentorlar yo'q</p>
              </div>
            ) : (
              mentors.map(mentor => (
                <div key={mentor.user_id} className="card p-4">
                  <div className="flex items-start gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-100 to-indigo-100 flex items-center justify-center text-xl overflow-hidden flex-shrink-0">
                      {mentor.avatar_url ? (
                        <img src={mentor.avatar_url} alt="" className="w-full h-full object-cover" />
                      ) : '🏆'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-bold text-gray-900 text-sm truncate">
                          {mentor.first_name} {mentor.last_name}
                        </p>
                        <LeagueBadge league="innovator" size="sm" />
                      </div>
                      <p className="text-xs text-gray-400">{mentor.global_xp.toLocaleString()} Global XP</p>
                      {mentor.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {mentor.tags.map(t => (
                            <span key={t} className="tag bg-purple-50 text-purple-700 text-[10px]">
                              #{t.replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-50">
                    <div className="flex gap-2">
                      {[0, 1].map(i => (
                        <div key={i} className={clsx(
                          'w-6 h-6 rounded-full border-2 flex items-center justify-center text-xs',
                          i < mentor.active_mentorships ? 'bg-purple-100 border-purple-400' : 'bg-gray-50 border-dashed border-gray-300'
                        )}>
                          {i < mentor.active_mentorships ? '👤' : ''}
                        </div>
                      ))}
                      <span className="text-xs text-gray-400 ml-1">
                        {mentor.slots_available} bo'sh slot
                      </span>
                    </div>
                    <Button
                      size="sm"
                      disabled={mentor.slots_available === 0}
                      loading={requesting === mentor.user_id}
                      onClick={() => handleRequest(mentor.user_id)}
                    >
                      {mentor.slots_available === 0 ? 'To\'liq' : 'So\'rov yuborish'}
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {tab === 'my' && (
          <div className="px-4 pt-4 flex flex-col gap-4">
            {isMentor ? (
              <div className="bg-purple-50 rounded-2xl p-4 border border-purple-100">
                <p className="font-bold text-purple-800 mb-1">🏆 Siz Novatorsiz!</p>
                <p className="text-sm text-purple-600">
                  Loyihalarga mentorlik qila olasiz. Shogirdingiz loyihasi
                  "Joriy etilgan" holatga o'tsa +1500 XP olasiz.
                </p>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-2xl p-4 text-center">
                <p className="text-3xl mb-2">🌱</p>
                <p className="text-sm text-gray-600">Mentorlik uchun Novator ligasiga o'ting</p>
                <p className="text-xs text-gray-400 mt-1">3000 XP kerak</p>
              </div>
            )}

            <div className="text-center py-8 text-gray-400">
              <p className="text-2xl mb-2">📭</p>
              <p className="text-sm">Faol mentorlik yo'q</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
