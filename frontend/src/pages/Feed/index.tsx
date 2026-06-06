import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppHeader } from '../../components/layout/Header'
import { ProjectCard } from '../../components/project/ProjectCard'
import { Spinner } from '../../components/ui/Spinner'
import { projectsApi } from '../../api/projects'
import type { Project } from '../../types'
import clsx from 'clsx'

const TAGS = [
  '#Barcha', '#IT_va_Raqamlashtirish', '#Tibbiyot_amaliyoti',
  '#Moliya', '#Sun\'iy_intellekt', '#Pediatriya', '#Farmakologiya',
]

const SORTS = [
  { key: 'newest', label: 'Yangi' },
  { key: 'popular', label: 'Mashhur' },
  { key: 'discussed', label: 'Ko\'p muhokama' },
]

export default function Feed() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedTag, setSelectedTag] = useState('')
  const [sort, setSort] = useState('newest')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)

  const fetchProjects = async (reset = false) => {
    try {
      setLoading(true)
      const currentPage = reset ? 1 : page
      const data = await projectsApi.list({
        tag: selectedTag || undefined,
        sort,
        page: currentPage,
      })
      if (reset) {
        setProjects(data)
        setPage(2)
      } else {
        setProjects(prev => [...prev, ...data])
        setPage(p => p + 1)
      }
      setHasMore(data.length === 20)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchProjects(true) }, [selectedTag, sort])

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <AppHeader />

      {/* Filters */}
      <div className="bg-white border-b border-gray-100 sticky top-[61px] z-30">
        {/* Tags */}
        <div className="flex gap-2 px-4 py-3 overflow-x-auto scrollbar-hide">
          {TAGS.map(tag => {
            const tagKey = tag === '#Barcha' ? '' : tag.replace('#', '')
            const isActive = tagKey === selectedTag
            return (
              <button
                key={tag}
                className={clsx(
                  'whitespace-nowrap px-3 py-1.5 rounded-full text-xs font-semibold transition-all',
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-600'
                )}
                onClick={() => setSelectedTag(tagKey)}
              >
                {tag}
              </button>
            )
          })}
        </div>
        {/* Sort */}
        <div className="flex gap-3 px-4 pb-3">
          {SORTS.map(s => (
            <button
              key={s.key}
              className={clsx(
                'text-xs font-semibold px-3 py-1 rounded-lg transition-all',
                sort === s.key ? 'bg-primary-50 text-primary-600' : 'text-gray-400'
              )}
              onClick={() => setSort(s.key)}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Project list */}
      <div className="flex-1 page-container px-4 pt-4 pb-28">
        {loading && projects.length === 0 ? (
          <div className="flex justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="text-5xl mb-4">🔬</div>
            <p className="font-semibold text-gray-600">Hozircha loyihalar yo'q</p>
            <p className="text-sm text-gray-400 mt-1">Birinchi bo'lib g'oyangizni yuboring!</p>
            <button
              className="mt-6 btn-primary"
              onClick={() => navigate('/projects/new')}
            >
              + Loyiha yuborish
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {projects.map(p => <ProjectCard key={p.id} project={p} />)}
            {hasMore && (
              <button
                className="w-full py-3 text-sm text-primary-600 font-medium"
                onClick={() => fetchProjects()}
                disabled={loading}
              >
                {loading ? <Spinner size="sm" className="mx-auto" /> : 'Ko\'proq ko\'rish'}
              </button>
            )}
          </div>
        )}
      </div>

      {/* FAB */}
      <button
        className="fixed bottom-20 right-4 w-14 h-14 bg-primary-600 text-white rounded-2xl shadow-lg flex items-center justify-center text-2xl active:scale-95 transition-transform z-40"
        onClick={() => navigate('/projects/new')}
      >
        +
      </button>
    </div>
  )
}
