import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/layout/Header'
import { ProjectCard } from '../../components/project/ProjectCard'
import { Button } from '../../components/ui/Button'
import { Spinner } from '../../components/ui/Spinner'
import { projectsApi } from '../../api/projects'
import type { Project, ProjectStatus } from '../../types'
import clsx from 'clsx'

const STATUS_FILTERS: Array<{ key: string; label: string }> = [
  { key: 'all', label: 'Barchasi' },
  { key: 'review', label: 'Ekspertizda' },
  { key: 'crowdsource', label: 'Muhokamada' },
  { key: 'incubation', label: 'Inkubatorda' },
  { key: 'pilot', label: 'Pilot' },
  { key: 'scaled', label: 'Joriy etilgan' },
  { key: 'rejected', label: 'Rad etilgan' },
]

export default function MyProjects() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    projectsApi.myProjects().then(setProjects).finally(() => setLoading(false))
  }, [])

  const filtered = filter === 'all' ? projects : projects.filter(p => p.status === filter)

  const stats = {
    total: projects.length,
    pilot: projects.filter(p => p.status === 'pilot').length,
    scaled: projects.filter(p => p.status === 'scaled').length,
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header
        title="Mening loyihalarim"
        rightAction={
          <button
            className="p-2 bg-primary-600 text-white rounded-xl"
            onClick={() => navigate('/projects/new')}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 5v14M5 12h14" strokeLinecap="round" />
            </svg>
          </button>
        }
      />

      <div className="page-container pb-24">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 p-4 pb-0">
          {[
            { label: 'Jami', value: stats.total, color: 'text-primary-600' },
            { label: 'Pilot', value: stats.pilot, color: 'text-orange-500' },
            { label: 'Joriy etilgan', value: stats.scaled, color: 'text-emerald-600' },
          ].map(s => (
            <div key={s.label} className="card p-3 text-center">
              <p className={`text-2xl font-black ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Filter */}
        <div className="flex gap-2 px-4 py-3 overflow-x-auto scrollbar-hide">
          {STATUS_FILTERS.map(f => (
            <button
              key={f.key}
              className={clsx(
                'whitespace-nowrap px-3 py-1.5 rounded-full text-xs font-semibold transition-all',
                filter === f.key ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600'
              )}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* List */}
        <div className="px-4 flex flex-col gap-3">
          {loading ? (
            <div className="flex justify-center py-16"><Spinner size="lg" /></div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16">
              <div className="text-5xl mb-3">📝</div>
              <p className="font-semibold text-gray-600">Loyihalar topilmadi</p>
              <p className="text-sm text-gray-400 mt-1 mb-6">Hali loyiha yubormadingiz</p>
              <Button onClick={() => navigate('/projects/new')}>
                + Yangi loyiha
              </Button>
            </div>
          ) : (
            filtered.map(p => <ProjectCard key={p.id} project={p} />)
          )}
        </div>
      </div>
    </div>
  )
}
