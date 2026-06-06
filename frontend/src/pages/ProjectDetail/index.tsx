import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Header } from '../../components/layout/Header'
import { LeagueBadge } from '../../components/gamification/LeagueBadge'
import { Button } from '../../components/ui/Button'
import { Spinner } from '../../components/ui/Spinner'
import { Input } from '../../components/ui/Input'
import { projectsApi } from '../../api/projects'
import { useAuthStore } from '../../store'
import type { Project, Comment } from '../../types'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [project, setProject] = useState<Project | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [commentText, setCommentText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [tab, setTab] = useState<'details' | 'comments'>('details')

  useEffect(() => {
    if (!id) return
    Promise.all([
      projectsApi.get(parseInt(id)).then(setProject),
      projectsApi.getComments(parseInt(id)).then(setComments),
    ]).finally(() => setLoading(false))
  }, [id])

  const handleComment = async () => {
    if (!commentText.trim() || !id) return
    setSubmitting(true)
    try {
      const c = await projectsApi.addComment(parseInt(id), commentText)
      setComments(prev => [{ ...c, replies: [], author_name: user?.first_name } as Comment, ...prev])
      setCommentText('')
      if (commentText.length >= 50) toast.success('+5 XP! Konstruktiv izoh 🎉')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Xatolik')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return (
    <div className="flex justify-center items-center min-h-screen">
      <Spinner size="lg" />
    </div>
  )

  if (!project) return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <p className="text-gray-500">Loyiha topilmadi</p>
      <Button variant="ghost" onClick={() => navigate(-1)} className="mt-3">← Orqaga</Button>
    </div>
  )

  const isAuthor = user?.id === project.author_id

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header
        title={project.title}
        showBack
        subtitle={`${project.view_count} ko'rilgan · ${project.comment_count} izoh`}
        rightAction={isAuthor && ['draft','revision'].includes(project.status) ? (
          <button className="p-2 text-primary-600" onClick={() => navigate(`/projects/${project.id}/edit`)}>
            ✏️
          </button>
        ) : undefined}
      />

      {/* Tabs */}
      <div className="bg-white border-b border-gray-100 flex">
        {[
          { key: 'details', label: 'Tafsilotlar' },
          { key: 'comments', label: `Izohlar (${project.comment_count})` },
        ].map(t => (
          <button
            key={t.key}
            className={clsx(
              'flex-1 py-3 text-sm font-semibold border-b-2 transition-all',
              tab === t.key ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-400'
            )}
            onClick={() => setTab(t.key as 'details' | 'comments')}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 page-container pb-28">
        {tab === 'details' && (
          <div className="px-4 pt-4 flex flex-col gap-4">
            {/* Tags & status */}
            <div className="flex flex-wrap gap-2">
              {project.tags.map(tag => (
                <span key={tag} className="tag bg-blue-50 text-blue-700 border border-blue-100">#{tag.replace(/_/g, ' ')}</span>
              ))}
              <span className={clsx('tag', {
                'bg-green-100 text-green-700': project.status === 'crowdsource',
                'bg-purple-100 text-purple-700': project.status === 'incubation',
                'bg-orange-100 text-orange-700': project.status === 'pilot',
                'bg-emerald-100 text-emerald-700': project.status === 'scaled',
                'bg-blue-100 text-blue-700': project.status === 'review',
              })}>
                {project.status}
              </span>
            </div>

            {/* Author */}
            <div className="flex items-center gap-2 text-sm">
              <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center">👤</div>
              <span className="font-medium text-gray-700">{project.author_name || 'Anonymous'}</span>
              {project.author_league && <LeagueBadge league={project.author_league} size="sm" />}
            </div>

            {/* Elevator pitch */}
            {project.elevator_pitch && (
              <div className="bg-primary-50 rounded-2xl p-4 border border-primary-100">
                <p className="text-xs font-semibold text-primary-700 mb-1">Elevator Pitch</p>
                <p className="text-sm text-gray-700 leading-relaxed">{project.elevator_pitch}</p>
              </div>
            )}

            {/* Problem */}
            {project.problem && (
              <Section icon="🔴" title="Muammo" content={project.problem} />
            )}

            {/* Solution */}
            {project.solution && (
              <Section icon="🟢" title="Yechim" content={project.solution} />
            )}

            {/* KPI */}
            {project.kpi && project.kpi.length > 0 && (
              <div className="card p-4">
                <p className="font-bold text-gray-900 mb-3 flex items-center gap-2">📊 KPI</p>
                {project.kpi.map((k, i) => (
                  <div key={i} className="flex justify-between py-2 border-b border-gray-50 last:border-0">
                    <span className="text-sm text-gray-600">{k.label}</span>
                    <span className="text-sm font-bold text-primary-600">{k.value}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Budget */}
            {(project.budget_min || project.budget_max) && (
              <div className="card p-4">
                <p className="font-bold text-gray-900 mb-2">💰 Byudjet</p>
                <p className="text-sm text-gray-700">
                  {project.budget_min?.toLocaleString()} — {project.budget_max?.toLocaleString()} so'm
                </p>
                {project.timeline && (
                  <p className="text-xs text-gray-400 mt-1">⏱ Muddat: {project.timeline}</p>
                )}
                {project.budget_purpose && (
                  <p className="text-sm text-gray-600 mt-2">{project.budget_purpose}</p>
                )}
              </div>
            )}

            {/* Mentor CTA */}
            {project.status === 'crowdsource' && !project.has_mentor && !isAuthor && user?.league === 'innovator' && (
              <div className="bg-purple-50 rounded-2xl p-4 border border-purple-100">
                <p className="font-semibold text-purple-800 text-sm mb-2">🤝 Mentorlik taklifi</p>
                <p className="text-xs text-purple-600 mb-3">Siz Novator sifatida bu loyihaga mentorlik qilishingiz mumkin</p>
                <Button variant="primary" size="sm" onClick={() => navigate('/mentorship')}>
                  Mentorlik birjasi
                </Button>
              </div>
            )}
          </div>
        )}

        {tab === 'comments' && (
          <div className="px-4 pt-4 flex flex-col gap-3">
            {/* Add comment */}
            {['crowdsource', 'incubation', 'ministry', 'pilot', 'scaled'].includes(project.status) && (
              <div className="card p-3 flex flex-col gap-2">
                <Input
                  placeholder="Izoh yozing (50+ belgi = +5 XP)..."
                  value={commentText}
                  onChange={e => setCommentText(e.target.value)}
                />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">{commentText.length} belgi</span>
                  <Button size="sm" onClick={handleComment} loading={submitting} disabled={!commentText.trim()}>
                    Yuborish
                  </Button>
                </div>
              </div>
            )}

            {comments.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-3xl mb-2">💬</p>
                <p className="text-gray-500 text-sm">Hali izohlar yo'q. Birinchi bo'ling!</p>
              </div>
            ) : (
              comments.map(c => (
                <CommentItem key={c.id} comment={c} />
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function Section({ icon, title, content }: { icon: string; title: string; content: string }) {
  const [expanded, setExpanded] = useState(false)
  const isLong = content.length > 200
  return (
    <div className="card p-4">
      <p className="font-bold text-gray-900 mb-2 flex items-center gap-2">{icon} {title}</p>
      <p className={clsx('text-sm text-gray-700 leading-relaxed', !expanded && isLong && 'line-clamp-4')}>
        {content}
      </p>
      {isLong && (
        <button className="text-xs text-primary-600 font-semibold mt-2" onClick={() => setExpanded(!expanded)}>
          {expanded ? 'Yig\'ish' : 'Ko\'proq o\'qish'}
        </button>
      )}
    </div>
  )
}

function CommentItem({ comment }: { comment: Comment }) {
  const [showReplies, setShowReplies] = useState(false)
  return (
    <div className="card p-3">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-7 h-7 rounded-xl bg-gray-100 flex items-center justify-center text-xs">
          {comment.author_avatar ? (
            <img src={comment.author_avatar} alt="" className="w-full h-full rounded-xl object-cover" />
          ) : '👤'}
        </div>
        <span className="text-xs font-semibold text-gray-700">{comment.author_name || 'Anonymous'}</span>
        {comment.author_league && <LeagueBadge league={comment.author_league} size="sm" showLabel={false} />}
        <span className="text-xs text-gray-400 ml-auto">
          {new Date(comment.created_at).toLocaleDateString('uz-UZ')}
        </span>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed">{comment.content}</p>
      {comment.replies.length > 0 && (
        <button className="text-xs text-primary-600 mt-2" onClick={() => setShowReplies(!showReplies)}>
          {showReplies ? '↑ Javoblarni yashirish' : `↓ ${comment.replies.length} ta javob`}
        </button>
      )}
      {showReplies && comment.replies.map(r => (
        <div key={r.id} className="mt-2 pl-3 border-l-2 border-gray-100">
          <p className="text-xs font-semibold text-gray-500 mb-1">{r.author_name}</p>
          <p className="text-xs text-gray-600">{r.content}</p>
        </div>
      ))}
    </div>
  )
}
