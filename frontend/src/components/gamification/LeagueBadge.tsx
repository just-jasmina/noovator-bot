import type { UserLeague } from '../../types'
import clsx from 'clsx'

const LEAGUE_CONFIG: Record<UserLeague, { emoji: string; labelUz: string; labelRu: string; class: string }> = {
  novice: { emoji: '🌱', labelUz: 'Yangi boshlovchi', labelRu: 'Новичок', class: 'badge-novice' },
  amateur: { emoji: '⚡', labelUz: 'Havaskor', labelRu: 'Любитель', class: 'badge-amateur' },
  professional: { emoji: '💎', labelUz: 'Professional', labelRu: 'Профессионал', class: 'badge-professional' },
  innovator: { emoji: '🏆', labelUz: 'Novator', labelRu: 'Новатор', class: 'badge-innovator' },
}

interface LeagueBadgeProps {
  league: UserLeague
  lang?: 'uz' | 'ru'
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export function LeagueBadge({ league, lang = 'uz', size = 'md', showLabel = true }: LeagueBadgeProps) {
  const cfg = LEAGUE_CONFIG[league]
  const sizes = {
    sm: 'text-xs px-2 py-0.5 gap-0.5',
    md: 'text-xs px-2.5 py-1 gap-1',
    lg: 'text-sm px-3 py-1.5 gap-1',
  }
  return (
    <span className={clsx('league-badge rounded-full font-bold', cfg.class, sizes[size])}>
      <span>{cfg.emoji}</span>
      {showLabel && <span>{lang === 'uz' ? cfg.labelUz : cfg.labelRu}</span>}
    </span>
  )
}

export function LeagueIcon({ league }: { league: UserLeague }) {
  return <span>{LEAGUE_CONFIG[league]?.emoji ?? '🌱'}</span>
}
