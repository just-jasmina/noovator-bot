import { useState, useEffect } from 'react'
import { Header } from '../../components/layout/Header'
import { LeagueBadge } from '../../components/gamification/LeagueBadge'
import { Spinner } from '../../components/ui/Spinner'
import { apiClient } from '../../api/client'
import { useAuthStore } from '../../store'
import type { LeaderboardEntry, UserLeague } from '../../types'
import clsx from 'clsx'

const LEAGUES: Array<{ key: UserLeague | 'all'; labelUz: string; emoji: string }> = [
  { key: 'all', labelUz: 'Umumiy', emoji: '🌐' },
  { key: 'innovator', labelUz: 'Novator', emoji: '🏆' },
  { key: 'professional', labelUz: 'Professional', emoji: '💎' },
  { key: 'amateur', labelUz: 'Havaskor', emoji: '⚡' },
  { key: 'novice', labelUz: 'Yangi', emoji: '🌱' },
]

export default function Leaderboard() {
  const { user } = useAuthStore()
  const [league, setLeague] = useState<string>('all')
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [myRank, setMyRank] = useState<number | null>(null)

  useEffect(() => {
    const fetch = async () => {
      setLoading(true)
      try {
        const res = await apiClient.get(`/leaderboard?league=${league}`)
        setEntries(res.data.entries)
        if (user) {
          const rankRes = await apiClient.get(`/leaderboard/my-rank?league=${league}&user_id=${user.id}`)
          setMyRank(rankRes.data.rank)
        }
      } finally {
        setLoading(false)
      }
    }
    fetch()
  }, [league, user])

  const topThree = entries.slice(0, 3)
  const rest = entries.slice(3)

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header title="🏆 Reyting" subtitle="Mavsumiy reyting" />

      {/* League tabs */}
      <div className="bg-white border-b border-gray-100 px-4 py-3 sticky top-[61px] z-30">
        <div className="flex gap-2 overflow-x-auto scrollbar-hide">
          {LEAGUES.map(l => (
            <button
              key={l.key}
              className={clsx(
                'whitespace-nowrap flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all',
                league === l.key ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600'
              )}
              onClick={() => setLeague(l.key)}
            >
              <span>{l.emoji}</span>
              <span>{l.labelUz}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 page-container pb-24">
        {/* My rank bar */}
        {myRank && user && (
          <div className="bg-gradient-to-r from-primary-600 to-teal-500 text-white mx-4 mt-4 rounded-2xl p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-xs opacity-80">Sizning o'rningiz</p>
                <p className="text-3xl font-black">#{myRank}</p>
              </div>
              <div className="text-right">
                <p className="text-xs opacity-80">Mavsumiy XP</p>
                <p className="text-2xl font-bold">{user.season_xp?.toLocaleString()}</p>
              </div>
              <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center text-2xl">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt="" className="w-full h-full rounded-2xl object-cover" />
                ) : '👤'}
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : (
          <div className="px-4 mt-4 flex flex-col gap-2">
            {/* Podium — top 3 */}
            {topThree.length >= 3 && (
              <div className="flex items-end justify-center gap-2 mb-4">
                {/* 2nd */}
                <PodiumItem entry={topThree[1]} place={2} />
                {/* 1st */}
                <PodiumItem entry={topThree[0]} place={1} />
                {/* 3rd */}
                <PodiumItem entry={topThree[2]} place={3} />
              </div>
            )}

            {/* Rest */}
            {entries.map((entry, idx) => {
              const isMe = user && entry.user_id === user.id
              const isTopThree = idx < 3
              const isBottomThree = idx >= entries.length - 3 && entries.length > 5

              return (
                <div
                  key={entry.user_id}
                  className={clsx(
                    'card flex items-center gap-3 p-3 transition-all',
                    isMe && 'ring-2 ring-primary-500 bg-primary-50',
                    isBottomThree && !isTopThree && 'border-red-100 bg-red-50'
                  )}
                >
                  <div className={clsx(
                    'w-8 h-8 rounded-full flex items-center justify-center text-sm font-black',
                    isTopThree ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'
                  )}>
                    {isTopThree ? ['🥇','🥈','🥉'][idx] : entry.rank}
                  </div>

                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-100 to-teal-100 flex items-center justify-center text-lg overflow-hidden flex-shrink-0">
                    {entry.avatar_url ? (
                      <img src={entry.avatar_url} alt="" className="w-full h-full object-cover" />
                    ) : '👤'}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <p className="text-sm font-semibold text-gray-900 truncate">
                        {entry.first_name} {entry.last_name}
                        {isMe && ' (Siz)'}
                      </p>
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <LeagueBadge league={entry.league} size="sm" />
                      {entry.streak_days > 6 && (
                        <span className="text-xs text-orange-500">🔥{entry.streak_days}</span>
                      )}
                    </div>
                  </div>

                  <div className="text-right">
                    <p className="text-sm font-bold text-primary-600">{entry.season_xp.toLocaleString()}</p>
                    <p className="text-xs text-gray-400">XP</p>
                  </div>
                </div>
              )
            })}

            {entries.length === 0 && (
              <div className="text-center py-16">
                <p className="text-4xl mb-3">🏆</p>
                <p className="text-gray-500">Hozircha reyting ma'lumotlari yo'q</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function PodiumItem({ entry, place }: { entry: LeaderboardEntry; place: 1 | 2 | 3 }) {
  const heights = { 1: 'h-24', 2: 'h-16', 3: 'h-12' }
  const medals = { 1: '🥇', 2: '🥈', 3: '🥉' }
  return (
    <div className="flex flex-col items-center gap-1.5 flex-1">
      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-100 to-teal-100 flex items-center justify-center text-xl overflow-hidden border-2 border-white shadow">
        {entry.avatar_url ? (
          <img src={entry.avatar_url} alt="" className="w-full h-full object-cover" />
        ) : '👤'}
      </div>
      <p className="text-xs font-bold text-gray-700 text-center leading-tight max-w-[70px] truncate">
        {entry.first_name}
      </p>
      <p className="text-xs text-primary-600 font-bold">{entry.season_xp.toLocaleString()}</p>
      <div className={clsx(
        'w-full rounded-t-xl flex items-center justify-center text-xl',
        heights[place],
        place === 1 ? 'bg-amber-400' : place === 2 ? 'bg-gray-300' : 'bg-amber-600/60'
      )}>
        {medals[place]}
      </div>
    </div>
  )
}
