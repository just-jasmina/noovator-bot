import { useNavigate } from 'react-router-dom'
import type { Project, ProjectStatus } from '../../types'
import { LeagueBadge } from '../gamification/LeagueBadge'
import clsx from 'clsx'

const STATUS_CONFIG: Record<ProjectStatus, { labelUz: string; labelRu: string; colorClass: string }> = {
  draft:       { labelUz: 'Qoralama', labelRu: 'Черновик', colorClass: 'bg-gray-100 text-gray-500' },
  review:      { labelUz: 'Ekspertizda', labelRu: 'На экспертизе', colorClass: 'bg-blue-100 text-blue-700' },
  revision:    { labelUz: 'Qayta ishlashda', labelRu: 'На доработке', colorClass: 'bg-yellow-100 text-yellow-700' },
  crowdsource: { labelUz: 'Muhokamada', labelRu: 'В обсуждении', colorClass: 'bg-green-100 text-green-700' },
  incubation:  { labelUz: 'Inkubatorda', labelRu: 'В инкубаторе', colorClass: 'bg-purple-100 text-purple-700' },
  ministry:    { labelUz: 'Vazirlikda', labelRu: 'В Минздраве', colorClass: 'bg-indigo-100 text-indigo-700' },
  pilot:       { labelUz: 'Pilot', labelRu: 'Пилот', colorClass: 'bg-orange-100 text-orange-700' },
  scaled:      { labelUz: 'Joriy etilgan', labelRu: 'Масштабирован', colorClass: 'bg-emerald-100 text-emerald-700' },
  rejected:    { labelUz: 'Rad etilgan', labelRu: 'Отклонён', colorClass: 'bg-red-100 text-red-700' },
  archived:    { labelUz: 'Arxiv', labelRu: 'Архив', colorClass: 'bg-gray-100 text-gray-400' },
}

const TAG_COLORS = [
  'bg-blue-50 text-blue-700 border-blue-100',
  'bg-teal-50 text-teal-700 border-teal-100',
  'bg-violet-50 text-violet-700 border-violet-100',
  'bg-pink-50 text-pink-700 border-pink-100',
]

interface ProjectCardProps {
  project: Project
  compact?: boolean
}

export function ProjectCard({ project, compact = false }: ProjectCardProps) {
  const navigate = useNavigate()
  const statusCfg = STATUS_CONFIG[project.status] ?? STATUS_CONFIG.draft
  const isIncubating = project.has_mentor && project.status === 'incubation'

  return (
    <div
      className={clsx(
        'card cursor-pointer transition-all duration-200 active:scale-[0.98]',
        isIncubating && 'opacity-70'
      )}
      onClick={() => navigate(`/projects/${project.id}`)}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 text-sm leading-tight line-clamp-2">
              {project.title}
            </h3>
          </div>
          <span className={clsx('tag text-xs shrink-0', statusCfg.colorClass)}>
            {statusCfg.labelUz}
          </span>
        </div>

        {/* Elevator pitch */}
        {project.elevator_pitch && !compact && (
          <p className="text-xs text-gray-500 line-clamp-2 mb-3">
            {project.elevator_pitch}
          </p>
        )}

        {/* Tags */}
        {project.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {project.tags.map((tag, i) => (
              <span key={tag} className={clsx('tag border', TAG_COLORS[i % TAG_COLORS.length])}>
                #{tag.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {project.author_league && (
              <LeagueBadge league={project.author_league} showLabel={false} size="sm" />
            )}
            <span className="text-xs text-gray-400 truncate max-w-[120px]">
              {project.author_name || 'Anonymous'}
            </span>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400">
            {isIncubating && <span className="text-purple-600 font-medium">🧪 Inkubator</span>}
            <span className="flex items-center gap-1">
              💬 {project.comment_count}
            </span>
            <span className="flex items-center gap-1">
              👁 {project.view_count}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
