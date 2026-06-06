export type UserRole = 'user' | 'expert' | 'mentor' | 'moderator' | 'admin'
export type UserLeague = 'novice' | 'amateur' | 'professional' | 'innovator'
export type UserStatus = 'pending' | 'active' | 'rejected' | 'banned'

export type ProjectStatus =
  | 'draft' | 'review' | 'revision' | 'crowdsource'
  | 'incubation' | 'ministry' | 'pilot' | 'scaled' | 'rejected' | 'archived'

export interface User {
  id: number
  telegram_id?: number
  telegram_username?: string
  first_name?: string
  last_name?: string
  middle_name?: string
  telegram_first_name?: string
  diploma_specialty?: string
  avatar_url?: string
  league: UserLeague
  role: UserRole
  status: UserStatus
  season_xp: number
  global_xp: number
  region?: string
  region_type?: string
  current_specialty?: string
  workplace?: string
  streak_days: number
  language: string
  pnfl?: string
  email?: string
  phone?: string
  created_at: string
  expert_tags?: string
}

export interface Project {
  id: number
  title: string
  elevator_pitch?: string
  tags: string[]
  status: ProjectStatus
  author_id: number
  author_name?: string
  author_league?: UserLeague
  comment_count: number
  view_count: number
  has_mentor: boolean
  created_at: string
  // Detail fields
  problem?: string
  solution?: string
  audience?: string[]
  kpi?: Array<{ label: string; value: string }>
  social_economic_effect?: string
  budget_min?: number
  budget_max?: number
  budget_purpose?: string
  timeline?: string
  documents?: Array<{ name: string; url: string }>
  updated_at?: string
  submitted_at?: string
}

export interface Comment {
  id: number
  content: string
  author_id: number
  author_name?: string
  author_league?: UserLeague
  author_avatar?: string
  created_at: string
  replies: Comment[]
}

export interface Review {
  review_id: number
  project_id: number
  title: string
  tags: string[]
  sla_deadline: string
  is_overdue: boolean
}

export interface Mentorship {
  id: number
  mentor_id: number
  mentee_id: number
  project_id: number
  status: 'pending' | 'active' | 'completed' | 'cancelled'
  mentor_ready: boolean
}

export interface LeaderboardEntry {
  rank: number
  user_id: number
  first_name?: string
  last_name?: string
  avatar_url?: string
  league: UserLeague
  season_xp: number
  global_xp: number
  streak_days: number
  region?: string
}

export interface XPTransaction {
  id: number
  amount: number
  action: string
  description?: string
  created_at: string
}
