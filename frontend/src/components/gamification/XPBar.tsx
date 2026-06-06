import type { UserLeague } from '../../types'

const LEAGUE_THRESHOLDS: Record<UserLeague, { min: number; next: number; label: string }> = {
  novice:       { min: 0,    next: 500,  label: 'Havaskor' },
  amateur:      { min: 500,  next: 1500, label: 'Professional' },
  professional: { min: 1500, next: 3000, label: 'Novator' },
  innovator:    { min: 3000, next: 3000, label: '🏆' },
}

interface XPBarProps {
  seasonXp: number
  league: UserLeague
  showNumbers?: boolean
}

export function XPBar({ seasonXp, league, showNumbers = true }: XPBarProps) {
  const { min, next, label } = LEAGUE_THRESHOLDS[league]
  const isMax = league === 'innovator'
  const progress = isMax ? 100 : Math.min(100, ((seasonXp - min) / (next - min)) * 100)

  return (
    <div className="flex flex-col gap-1.5">
      {showNumbers && (
        <div className="flex justify-between text-xs text-gray-500">
          <span className="font-semibold text-primary-600">{seasonXp.toLocaleString()} XP</span>
          {!isMax && <span>→ {label}: {next.toLocaleString()} XP</span>}
          {isMax && <span className="text-amber-600 font-bold">MAX LIGA 🏆</span>}
        </div>
      )}
      <div className="xp-bar">
        <div className="xp-bar-fill" style={{ width: `${progress}%` }} />
      </div>
    </div>
  )
}

export function XPChip({ amount, className = '' }: { amount: number; className?: string }) {
  const isPositive = amount >= 0
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-bold px-2 py-0.5 rounded-full
      ${isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} ${className}`}>
      {isPositive ? '+' : ''}{amount} XP
    </span>
  )
}

export function StreakBadge({ days }: { days: number }) {
  if (days < 2) return null
  return (
    <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-orange-100 text-orange-700">
      🔥 {days} kun / дней
    </span>
  )
}
