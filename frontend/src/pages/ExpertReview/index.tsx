import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/layout/Header'
import { Button } from '../../components/ui/Button'
import { Textarea } from '../../components/ui/Input'
import { Spinner } from '../../components/ui/Spinner'
import { apiClient } from '../../api/client'
import type { Review } from '../../types'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const DECISIONS = [
  { key: 'approve', emoji: '✅', labelUz: 'Tasdiqlash', labelRu: 'Одобрить', color: 'border-green-400 bg-green-50 text-green-700' },
  { key: 'reject', emoji: '❌', labelUz: 'Rad etish', labelRu: 'Отклонить', color: 'border-red-400 bg-red-50 text-red-700' },
  { key: 'revision', emoji: '🔄', labelUz: 'Qayta ishlash', labelRu: 'На доработку', color: 'border-yellow-400 bg-yellow-50 text-yellow-700' },
]

export default function ExpertQueue() {
  const navigate = useNavigate()
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Review | null>(null)
  const [decision, setDecision] = useState('')
  const [reviewText, setReviewText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    apiClient.get('/reviews/my').then(r => setReviews(r.data)).finally(() => setLoading(false))
  }, [])

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
      toast.success('Retsenziya yuborildi!')
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

  if (selected) {
    return (
      <div className="flex flex-col min-h-screen bg-gray-50">
        <Header title="Ekspertiza" subtitle={selected.title} showBack />
        <div className="flex-1 page-container pb-28 px-4 pt-4 flex flex-col gap-4">

          {/* Project info */}
          <div className="card p-4">
            <p className="font-bold text-gray-900 text-sm mb-2">📋 {selected.title}</p>
            <div className="flex flex-wrap gap-1.5">
              {selected.tags.map(t => (
                <span key={t} className="tag bg-blue-50 text-blue-700 border border-blue-100">#{t.replace(/_/g, ' ')}</span>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
              <span className={clsx('font-medium', selected.is_overdue ? 'text-red-500' : 'text-gray-500')}>
                ⏰ SLA: {new Date(selected.sla_deadline).toLocaleDateString('uz-UZ')}
                {selected.is_overdue && ' — ⚠️ Muddat o\'tgan!'}
              </span>
            </div>
          </div>

          {/* Decision picker */}
          <div className="flex flex-col gap-2">
            <p className="text-sm font-semibold text-gray-700">Qaror *</p>
            {DECISIONS.map(d => (
              <button
                key={d.key}
                className={clsx(
                  'flex items-center gap-3 p-3 rounded-2xl border-2 transition-all text-left',
                  decision === d.key ? d.color : 'border-gray-200 bg-white'
                )}
                onClick={() => setDecision(d.key)}
              >
                <span className="text-2xl">{d.emoji}</span>
                <div>
                  <p className="font-semibold text-sm">{d.labelUz}</p>
                  <p className="text-xs text-gray-400">{d.labelRu}</p>
                </div>
                {decision === d.key && (
                  <svg className="w-5 h-5 ml-auto flex-shrink-0" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                )}
              </button>
            ))}
          </div>

          {/* Review text */}
          <Textarea
            label={`Retsenziya * (kamida 150 so'z)`}
            placeholder="Loyihani batafsil ko'rib chiqing: afzalliklari, kamchiliklari, tavsiyalar..."
            value={reviewText}
            onChange={e => setReviewText(e.target.value)}
            rows={8}
            showWordCount
            maxWords={9999}
          />
          <div className={clsx('text-sm font-semibold text-center', wordCount >= 150 ? 'text-green-600' : 'text-gray-400')}>
            {wordCount} / 150+ so'z {wordCount >= 150 ? '✅' : `(${150 - wordCount} ta so'z qoldi)`}
          </div>

          <div className="bg-amber-50 rounded-2xl p-3 text-xs text-amber-700">
            ⚠️ Blind Review: Muallifning ismi va ma'lumotlari sizga ko'rsatilmaydi.
            Retsenziyangiz ham anonim saqlanadi.
          </div>
        </div>

        <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 safe-bottom">
          <Button
            fullWidth
            onClick={handleSubmit}
            loading={submitting}
            disabled={!isValid}
          >
            {!decision ? 'Avval qaror tanlang' : wordCount < 150 ? `${150 - wordCount} so'z yetishmaydi` : '📤 Retsenziyani yuborish'}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <Header title="📋 Ekspert navbati" subtitle="Blind Review" />

      <div className="flex-1 page-container pb-24 px-4 pt-4">
        {loading ? (
          <div className="flex justify-center py-16"><Spinner size="lg" /></div>
        ) : reviews.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-5xl mb-3">✅</div>
            <p className="font-semibold text-gray-600">Barcha loyihalar ko'rib chiqildi!</p>
            <p className="text-sm text-gray-400 mt-1">Yangi loyihalar tushganda xabar olasiz</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="bg-blue-50 rounded-2xl p-3 text-xs text-blue-700">
              📌 {reviews.length} ta loyiha retsenziya kutmoqda. SLA: 7 kalendar kun.
            </div>
            {reviews.map(r => (
              <div
                key={r.review_id}
                className={clsx('card p-4 cursor-pointer active:scale-[0.98] transition-all', r.is_overdue && 'border-red-200')}
                onClick={() => setSelected(r)}
              >
                <div className="flex justify-between items-start mb-2">
                  <p className="font-semibold text-sm text-gray-900 flex-1 pr-2">{r.title}</p>
                  {r.is_overdue && (
                    <span className="tag bg-red-100 text-red-600 shrink-0">⚠️ Kechikkan</span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {r.tags.map(t => (
                    <span key={t} className="tag bg-gray-100 text-gray-600">#{t.replace(/_/g, ' ')}</span>
                  ))}
                </div>
                <div className="flex justify-between text-xs text-gray-400">
                  <span>SLA: {new Date(r.sla_deadline).toLocaleDateString('uz-UZ')}</span>
                  <span className="text-primary-600 font-semibold">Ko'rish →</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
