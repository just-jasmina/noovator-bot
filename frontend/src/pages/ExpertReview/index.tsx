import { useState, useEffect } from 'react'
import { Button } from '../../components/ui/Button'
import { Textarea } from '../../components/ui/Input'
import { Spinner } from '../../components/ui/Spinner'
import { apiClient } from '../../api/client'
import { useAuthStore } from '../../store'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const DECISIONS = [
  { key: 'approve', emoji: '✅', labelUz: 'Tasdiqlash', labelRu: 'Одобрить', color: 'border-green-400 bg-green-50 text-green-700' },
  { key: 'reject', emoji: '❌', labelUz: 'Rad etish', labelRu: 'Отклонить', color: 'border-red-400 bg-red-50 text-red-700' },
  { key: 'revision', emoji: '🔄', labelUz: 'Qayta ishlash', labelRu: 'На доработку', color: 'border-yellow-400 bg-yellow-50 text-yellow-700' },
]

interface ReviewItem {
  review_id: string
  project_id: string
  title: string
  pitch?: string
  tags: string[]
  tag_labels: string[]
  sla_deadline: string | null
  is_overdue: boolean
}

interface ReviewDetail extends ReviewItem {
  problem?: string
  solution?: string
  audience?: string[]
  kpis?: string[]
  effect?: string
  cost_range?: string
  budget_use?: string
  timeline?: string
}

const TIMELINE_LABELS: Record<string, string> = {
  '1_month': '1 oy', '3_months': '3 oy', '6_months': '6 oy',
  '1_year': '1 yil', '2_years': '2 yil', 'over_2_years': "2 yildan ortiq",
}

export default function ExpertQueue() {
  const { logout } = useAuthStore()
  const [reviews, setReviews] = useState<ReviewItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<ReviewDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [decision, setDecision] = useState('')
  const [reviewText, setReviewText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const loadQueue = () => {
    setLoading(true)
    apiClient.get('/reviews/my')
      .then(r => setReviews(r.data))
      .catch(() => setReviews([]))
      .finally(() => setLoading(false))
  }

  useEffect(loadQueue, [])

  const openReview = async (item: ReviewItem) => {
    setDecision('')
    setReviewText('')
    setDetailLoading(true)
    setSelected(item as ReviewDetail)
    try {
      const r = await apiClient.get(`/reviews/${item.review_id}`)
      setSelected(r.data)
    } catch {
      toast.error('Loyiha ma\'lumotlarini yuklab bo\'lmadi')
    } finally {
      setDetailLoading(false)
    }
  }

  const wordCount = reviewText.trim().split(/\s+/).filter(Boolean).length
  const isValid = decision && wordCount >= 150

  const handleSubmit = async () => {
    if (!selected || !isValid) return
    setSubmitting(true)
    try {
      await apiClient.post(`/reviews/${selected.review_id}`, {
        decision,
        review_text: reviewText,
      })
      toast.success('Retsenziya yuborildi! +30 XP 🎉')
      setReviews(prev => prev.filter(r => r.review_id !== selected.review_id))
      setSelected(null)
      setDecision('')
      setReviewText('')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Xatolik')
    } finally {
      setSubmitting(false)
    }
  }

  const fmtDate = (s: string | null) =>
    s ? new Date(s).toLocaleDateString('uz-UZ', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '—'

  // ---------- DETAIL VIEW ----------
  if (selected) {
    return (
      <div className="flex flex-col min-h-screen bg-gray-50">
        <div className="bg-primary-700 text-white px-4 pt-5 pb-4 sticky top-0 z-10">
          <button onClick={() => setSelected(null)} className="text-primary-200 text-sm mb-2 flex items-center gap-1">
            ← Orqaga
          </button>
          <h1 className="text-lg font-black leading-tight">{selected.title}</h1>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {(selected.tag_labels?.length ? selected.tag_labels : selected.tags).map((t, i) => (
              <span key={i} className="text-[11px] px-2 py-0.5 rounded-full bg-white/15 text-white">{t}</span>
            ))}
          </div>
        </div>

        <div className="flex-1 pb-32 px-4 pt-4 flex flex-col gap-4">
          {detailLoading ? (
            <div className="flex justify-center py-10"><Spinner size="lg" /></div>
          ) : (
            <>
              {selected.pitch && (
                <Section icon="💡" title="Elevator Pitch"><p className="text-sm text-gray-700 leading-relaxed">{selected.pitch}</p></Section>
              )}
              {selected.problem && (
                <Section icon="🔍" title="Muammo"><p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{selected.problem}</p></Section>
              )}
              {selected.solution && (
                <Section icon="🎯" title="Yechim"><p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{selected.solution}</p></Section>
              )}
              {selected.audience && selected.audience.length > 0 && (
                <Section icon="👥" title="Maqsadli auditoriya">
                  <div className="flex flex-wrap gap-1.5">
                    {selected.audience.map((a, i) => (
                      <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-teal-50 text-teal-700 border border-teal-100">{a}</span>
                    ))}
                  </div>
                </Section>
              )}
              {selected.kpis && selected.kpis.length > 0 && (
                <Section icon="📊" title="KPI">
                  <ul className="flex flex-col gap-1.5">
                    {selected.kpis.map((k, i) => (
                      <li key={i} className="text-sm text-gray-700 flex gap-2"><span className="text-primary-500">▸</span>{k}</li>
                    ))}
                  </ul>
                </Section>
              )}
              {selected.effect && (
                <Section icon="📈" title="Ijtimoiy-iqtisodiy ta'sir"><p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{selected.effect}</p></Section>
              )}
              {(selected.cost_range || selected.budget_use || selected.timeline) && (
                <Section icon="💰" title="Resurslar">
                  <div className="flex flex-col gap-2 text-sm">
                    {selected.cost_range && <Row label="Byudjet" value={`${selected.cost_range} so'm`} />}
                    {selected.timeline && <Row label="Muddat" value={TIMELINE_LABELS[selected.timeline] || selected.timeline} />}
                    {selected.budget_use && <div className="text-gray-600 mt-1">{selected.budget_use}</div>}
                  </div>
                </Section>
              )}

              {/* SLA */}
              <div className={clsx('rounded-2xl p-3 text-xs font-medium', selected.is_overdue ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-700')}>
                ⏰ SLA muddati: {fmtDate(selected.sla_deadline)} {selected.is_overdue && '— ⚠️ Muddat o\'tgan!'}
              </div>

              {/* Decision */}
              <div className="flex flex-col gap-2">
                <p className="text-sm font-bold text-gray-800">Qaror *</p>
                {DECISIONS.map(d => (
                  <button key={d.key}
                    className={clsx('flex items-center gap-3 p-3 rounded-2xl border-2 transition-all text-left',
                      decision === d.key ? d.color : 'border-gray-200 bg-white')}
                    onClick={() => setDecision(d.key)}>
                    <span className="text-2xl">{d.emoji}</span>
                    <div>
                      <p className="font-semibold text-sm">{d.labelUz}</p>
                      <p className="text-xs text-gray-400">{d.labelRu}</p>
                    </div>
                  </button>
                ))}
              </div>

              {/* Review text */}
              <Textarea
                label="Retsenziya * (kamida 150 so'z)"
                placeholder="Loyihani batafsil baholang: afzalliklari, kamchiliklari, tavsiyalar..."
                value={reviewText}
                onChange={e => setReviewText(e.target.value)}
                rows={8}
              />
              <div className={clsx('text-sm font-semibold text-center -mt-2', wordCount >= 150 ? 'text-green-600' : 'text-gray-400')}>
                {wordCount} / 150+ so'z {wordCount >= 150 ? '✅' : `(yana ${150 - wordCount} ta)`}
              </div>

              <div className="bg-amber-50 rounded-2xl p-3 text-xs text-amber-700">
                ⚠️ Blind Review: muallif ma'lumotlari ko'rsatilmaydi.
              </div>
            </>
          )}
        </div>

        <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 safe-bottom">
          <Button fullWidth onClick={handleSubmit} loading={submitting} disabled={!isValid}>
            {!decision ? 'Avval qaror tanlang' : wordCount < 150 ? `Yana ${150 - wordCount} so'z kerak` : '📤 Yuborish (+30 XP)'}
          </Button>
        </div>
      </div>
    )
  }

  // ---------- QUEUE VIEW ----------
  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <div className="bg-primary-700 text-white px-4 pt-5 pb-5 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-black">📋 Ekspert navbati</h1>
            <p className="text-primary-200 text-xs mt-0.5">Blind Review · SLA 7 kun</p>
          </div>
          <button onClick={logout} className="text-xs bg-white/15 px-3 py-1.5 rounded-lg font-medium">
            Chiqish
          </button>
        </div>
      </div>

      <div className="flex-1 pb-10 px-4 pt-4">
        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : reviews.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-5xl mb-3">✅</div>
            <p className="font-semibold text-gray-600">Barcha loyihalar ko'rib chiqildi!</p>
            <p className="text-sm text-gray-400 mt-1">Yangi loyiha kelganda shu yerda ko'rinadi</p>
            <button onClick={loadQueue} className="mt-4 text-sm text-primary-600 font-semibold">↻ Yangilash</button>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="bg-blue-50 rounded-2xl p-3 text-xs text-blue-700">
              📌 {reviews.length} ta loyiha retsenziya kutmoqda
            </div>
            {reviews.map(r => (
              <button key={r.review_id}
                onClick={() => openReview(r)}
                className={clsx('bg-white rounded-2xl p-4 text-left shadow-sm active:scale-[0.98] transition-all border',
                  r.is_overdue ? 'border-red-200' : 'border-gray-100')}>
                <div className="flex items-start justify-between gap-2">
                  <p className="font-bold text-gray-900 text-sm leading-snug">{r.title}</p>
                  {r.is_overdue && <span className="text-[10px] bg-red-100 text-red-600 px-2 py-0.5 rounded-full whitespace-nowrap">muddat o'tgan</span>}
                </div>
                {r.pitch && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{r.pitch}</p>}
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {(r.tag_labels?.length ? r.tag_labels : r.tags).map((t, i) => (
                    <span key={i} className="text-[11px] px-2 py-0.5 rounded-full bg-primary-50 text-primary-700">{t}</span>
                  ))}
                </div>
                <p className="text-[11px] text-gray-400 mt-2">⏰ SLA: {fmtDate(r.sla_deadline)}</p>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Section({ icon, title, children }: { icon: string; title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
      <p className="font-bold text-gray-900 text-sm mb-2">{icon} {title}</p>
      {children}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-800 text-right">{value}</span>
    </div>
  )
}
