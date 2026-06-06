import { useNavigate } from 'react-router-dom'

interface HeaderProps {
  title: string
  subtitle?: string
  showBack?: boolean
  rightAction?: React.ReactNode
}

export function Header({ title, subtitle, showBack, rightAction }: HeaderProps) {
  const navigate = useNavigate()
  return (
    <div className="sticky top-0 z-40 bg-white border-b border-gray-100">
      <div className="flex items-center gap-3 px-4 py-3">
        {showBack && (
          <button
            className="p-2 -ml-2 text-gray-500 rounded-xl hover:bg-gray-100 transition-colors"
            onClick={() => navigate(-1)}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
        )}
        <div className="flex-1 min-w-0">
          <h1 className="font-bold text-gray-900 text-base truncate">{title}</h1>
          {subtitle && <p className="text-xs text-gray-400 truncate">{subtitle}</p>}
        </div>
        {rightAction}
      </div>
    </div>
  )
}

export function AppHeader() {
  const navigate = useNavigate()
  return (
    <div className="sticky top-0 z-40 bg-white border-b border-gray-100">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-600 to-teal-500 flex items-center justify-center shadow-sm">
            <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
            </svg>
          </div>
          <div>
            <p className="font-bold text-gray-900 text-sm leading-none">Tibbiyot Novatorlari</p>
            <p className="text-xs text-gray-400">Innovatsion platforma</p>
          </div>
        </div>
        <button
          className="p-2 text-gray-500 rounded-xl hover:bg-gray-100"
          onClick={() => navigate('/projects/new')}
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 5v14M5 12h14" strokeLinecap="round"/>
          </svg>
        </button>
      </div>
    </div>
  )
}
