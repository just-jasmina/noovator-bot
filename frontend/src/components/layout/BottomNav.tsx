import { useNavigate, useLocation } from 'react-router-dom'
import clsx from 'clsx'

const TABS = [
  {
    key: 'feed',
    path: '/',
    icon: (active: boolean) => (
      <svg className={clsx('w-6 h-6', active && 'fill-current')} viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
        <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
      </svg>
    ),
    labelUz: 'Lenta',
    labelRu: 'Лента',
  },
  {
    key: 'my-projects',
    path: '/my-projects',
    icon: (active: boolean) => (
      <svg className={clsx('w-6 h-6', active && 'fill-current')} viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
        <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
      </svg>
    ),
    labelUz: 'Loyihalar',
    labelRu: 'Проекты',
  },
  {
    key: 'leaderboard',
    path: '/leaderboard',
    icon: (active: boolean) => (
      <svg className={clsx('w-6 h-6', active && 'fill-current')} viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
        <path d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
      </svg>
    ),
    labelUz: 'Reyting',
    labelRu: 'Рейтинг',
  },
  {
    key: 'mentorship',
    path: '/mentorship',
    icon: (active: boolean) => (
      <svg className={clsx('w-6 h-6', active && 'fill-current')} viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
        <path d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
      </svg>
    ),
    labelUz: 'Mentorlik',
    labelRu: 'Менторство',
  },
  {
    key: 'profile',
    path: '/profile',
    icon: (active: boolean) => (
      <svg className={clsx('w-6 h-6', active && 'fill-current')} viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
        <path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
      </svg>
    ),
    labelUz: 'Profil',
    labelRu: 'Профиль',
  },
]

export function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 safe-bottom z-50">
      <div className="flex items-center justify-around px-2">
        {TABS.map(tab => {
          const active = tab.path === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(tab.path)
          return (
            <button
              key={tab.key}
              className={clsx('bottom-nav-item', active && 'active')}
              onClick={() => navigate(tab.path)}
            >
              {tab.icon(active)}
              <span className="text-[10px] font-medium">{tab.labelUz}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}
