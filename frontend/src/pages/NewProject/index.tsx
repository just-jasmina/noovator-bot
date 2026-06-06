import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from '../../components/layout/Header'
import { Input, Textarea, Select } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { projectsApi } from '../../api/projects'
import { useTelegram } from '../../hooks/useTelegram'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const STEPS = [
  { id: 1, icon: '💡', title: 'Identifikatsiya' },
  { id: 2, icon: '🔍', title: 'Muammo & Yechim' },
  { id: 3, icon: '📊', title: 'Natija (KPI)' },
  { id: 4, icon: '💰', title: 'Resurslar' },
  { id: 5, icon: '📎', title: 'Hujjatlar' },
]

// Canonical tags — MUST match profiles.expert_tags so routing works
const AVAILABLE_TAGS = [
  'Organizatsiya_sogliqni_saqlash', 'IT_va_Raqamlashtirish',
  'Moliya_va_Iqtisodiyot', 'Jarrohlik_amaliyoti', 'Med_huquq',
  'Farmakologiya', 'Pediatriya', 'Medtexnika', 'Suniy_intellekt',
  'Sanitariya_Epidemiologiya', 'Tibbiyot_talimi', 'Laborator_diagnostika',
]

const AUDIENCE_OPTIONS = [
  'Shifokorlar', 'O\'rta tibbiyot xodimlari', 'Talabalar',
  'Bosh shifokorlar', 'IT mutaxassislar', 'Iqtisodchilar', 'Farmatsevtlar',
]

export default function NewProject() {
  const navigate = useNavigate()
  const { mainButton, haptic } = useTelegram()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedAudience, setSelectedAudience] = useState<string[]>([])
  const [kpis, setKpis] = useState([{ label: '', value: '' }])

  const [form, setForm] = useState({
    title: '',
    elevator_pitch: '',
    problem: '',
    solution: '',
    social_economic_effect: '',
    budget_min: '',
    budget_max: '',
    budget_purpose: '',
    timeline: '6_months',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const wordCount = (text: string) => text.trim().split(/\s+/).filter(Boolean).length

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm(f => ({ ...f, [field]: e.target.value }))
    setErrors(er => ({ ...er, [field]: '' }))
  }

  const toggleTag = (tag: string) => {
    haptic?.selectionChanged()
    setSelectedTags(prev => {
      if (prev.includes(tag)) return prev.filter(t => t !== tag)
      if (prev.length >= 3) {
        toast('Maksimal 3 ta teg tanlash mumkin', { icon: '⚠️' })
        return prev
      }
      return [...prev, tag]
    })
  }

  const toggleAudience = (a: string) => {
    setSelectedAudience(prev =>
      prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a]
    )
  }

  const validateStep = (): boolean => {
    const errs: Record<string, string> = {}
    if (step === 1) {
      if (!form.title.trim()) errs.title = 'Nomi kiritilishi shart'
      if (form.title.length > 100) errs.title = 'Maksimal 100 belgi'
      if (selectedTags.length === 0) errs.tags = 'Kamida 1 ta teg tanlang'
      if (form.elevator_pitch && wordCount(form.elevator_pitch) > 150)
        errs.elevator_pitch = 'Maksimal 150 so\'z'
    }
    if (step === 2) {
      if (!form.problem.trim()) errs.problem = 'Muammo tavsifi kiritilishi shart'
      if (!form.solution.trim()) errs.solution = 'Yechim tavsifi kiritilishi shart'
    }
    if (step === 3) {
      if (kpis.every(k => !k.label.trim())) errs.kpi = 'Kamida 1 ta KPI qo\'shing'
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleNext = () => {
    if (!validateStep()) return
    haptic?.impactOccurred('light')
    setStep(s => s + 1)
  }

  const handleSubmit = async () => {
    setLoading(true)
    haptic?.impactOccurred('medium')
    try {
      await projectsApi.create({
        title: form.title,
        elevator_pitch: form.elevator_pitch,
        tags: selectedTags,
        problem: form.problem,
        solution: form.solution,
        audience: selectedAudience,
        kpi: kpis.filter(k => k.label.trim()),
        social_economic_effect: form.social_economic_effect,
        budget_min: form.budget_min ? parseInt(form.budget_min) : undefined,
        budget_max: form.budget_max ? parseInt(form.budget_max) : undefined,
        budget_purpose: form.budget_purpose,
        timeline: form.timeline,
      })
      haptic?.notificationOccurred('success')
      toast.success('Loyiha muvaffaqiyatli yuborildi! +50 XP 🎉')
      navigate('/my-projects')
    } catch (e: any) {
      haptic?.notificationOccurred('error')
      toast.error(e.response?.data?.detail || 'Xatolik yuz berdi')
    } finally {
      setLoading(false)
    }
  }

  const progress = ((step - 1) / (STEPS.length - 1)) * 100

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header title="Yangi loyiha" subtitle={`${step}/${STEPS.length} — ${STEPS[step-1].title}`} showBack />

      {/* Step indicator */}
      <div className="bg-white px-4 pt-3 pb-4 border-b border-gray-100">
        <div className="flex items-center gap-1.5 mb-3">
          {STEPS.map(s => (
            <div key={s.id} className="flex-1 flex flex-col items-center gap-1">
              <div className={clsx(
                'w-8 h-8 rounded-xl flex items-center justify-center text-sm transition-all',
                s.id < step ? 'bg-green-500 text-white' : s.id === step ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-400'
              )}>
                {s.id < step ? '✓' : s.icon}
              </div>
            </div>
          ))}
        </div>
        <div className="xp-bar">
          <div className="xp-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto pb-28 px-4 pt-5">
        <div className="flex flex-col gap-4">

          {step === 1 && (
            <>
              <Input
                label="Loyiha nomi *"
                placeholder="Masalan: AI-yordamchi vrach uchun diagnoz qo'yishda"
                value={form.title}
                onChange={update('title')}
                error={errors.title}
                hint={`${form.title.length}/100 belgi`}
                maxLength={100}
              />

              <div className="flex flex-col gap-2">
                <div className="flex justify-between">
                  <label className="text-sm font-medium text-gray-700">Teglar * (1-3 ta)</label>
                  <span className="text-xs text-gray-400">{selectedTags.length}/3</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {AVAILABLE_TAGS.map(tag => (
                    <button
                      key={tag}
                      type="button"
                      className={clsx(
                        'text-xs px-3 py-1.5 rounded-full border font-medium transition-all',
                        selectedTags.includes(tag)
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'bg-white text-gray-600 border-gray-200'
                      )}
                      onClick={() => toggleTag(tag)}
                    >
                      #{tag.replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>
                {errors.tags && <p className="text-xs text-red-500">{errors.tags}</p>}
              </div>

              <Textarea
                label="Elevator Pitch (ixtiyoriy, ≤150 so'z)"
                placeholder="Loyihangizni 150 so'z ichida qisqacha tushuntiring..."
                value={form.elevator_pitch}
                onChange={update('elevator_pitch')}
                error={errors.elevator_pitch}
                showWordCount maxWords={150}
                rows={4}
              />
            </>
          )}

          {step === 2 && (
            <>
              <Textarea
                label="Muammo tavsifi * (≤1500 belgi)"
                placeholder="Sog'liqni saqlash sohasidagi qanday muammoni hal qilasiz?..."
                value={form.problem}
                onChange={update('problem')}
                error={errors.problem}
                maxLength={1500}
                rows={5}
                hint={`${form.problem.length}/1500`}
              />
              <Textarea
                label="Yechim tavsifi * (≤1500 belgi)"
                placeholder="Muammoni hal qilish usulini batafsil yozing..."
                value={form.solution}
                onChange={update('solution')}
                error={errors.solution}
                maxLength={1500}
                rows={5}
                hint={`${form.solution.length}/1500`}
              />

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-700">Maqsadli auditoriya</label>
                <div className="flex flex-wrap gap-2">
                  {AUDIENCE_OPTIONS.map(a => (
                    <button key={a} type="button"
                      className={clsx('text-xs px-3 py-1.5 rounded-full border font-medium transition-all',
                        selectedAudience.includes(a) ? 'bg-teal-500 text-white border-teal-500' : 'bg-white text-gray-600 border-gray-200')}
                      onClick={() => toggleAudience(a)}>
                      {a}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {step === 3 && (
            <>
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-gray-700">O'lchanadigan KPI *</label>
                  <button type="button" className="text-xs text-primary-600 font-semibold"
                    onClick={() => setKpis(k => [...k, { label: '', value: '' }])}>
                    + Qo'shish
                  </button>
                </div>
                {kpis.map((kpi, i) => (
                  <div key={i} className="flex gap-2 items-center">
                    <Input placeholder="KPI nomi (masalan: Xarajat qisqarishi)" value={kpi.label}
                      onChange={e => setKpis(k => k.map((x, j) => j === i ? { ...x, label: e.target.value } : x))}
                      className="flex-1" />
                    <Input placeholder="Qiymat (masalan: 30%)" value={kpi.value}
                      onChange={e => setKpis(k => k.map((x, j) => j === i ? { ...x, value: e.target.value } : x))}
                      className="w-28" />
                    {kpis.length > 1 && (
                      <button type="button" className="text-red-400 p-1"
                        onClick={() => setKpis(k => k.filter((_, j) => j !== i))}>✕</button>
                    )}
                  </div>
                ))}
                {errors.kpi && <p className="text-xs text-red-500">{errors.kpi}</p>}
              </div>

              <Textarea
                label="Kutilayotgan ijtimoiy-iqtisodiy ta'sir"
                placeholder="Loyiha amalga oshirilganda qanday natija kutiladi?..."
                value={form.social_economic_effect}
                onChange={update('social_economic_effect')}
                rows={4}
              />
            </>
          )}

          {step === 4 && (
            <>
              <div className="flex gap-3">
                <Input label="Minimal byudjet (so'm)" type="number" placeholder="1000000"
                  value={form.budget_min} onChange={update('budget_min')} className="flex-1" />
                <Input label="Maksimal byudjet (so'm)" type="number" placeholder="5000000"
                  value={form.budget_max} onChange={update('budget_max')} className="flex-1" />
              </div>
              <Textarea
                label="Mablag' nima uchun kerak"
                placeholder="Uskunalar, xodimlar, dasturiy ta'minot..."
                value={form.budget_purpose}
                onChange={update('budget_purpose')}
                rows={3}
              />
              <Select label="Amalga oshirish muddati" value={form.timeline} onChange={update('timeline')}
                options={[
                  { value: '1_month', label: '1 oy' },
                  { value: '3_months', label: '3 oy' },
                  { value: '6_months', label: '6 oy' },
                  { value: '1_year', label: '1 yil' },
                  { value: '2_years', label: '2 yil' },
                  { value: 'over_2_years', label: '2 yildan ortiq' },
                ]} />
            </>
          )}

          {step === 5 && (
            <div className="flex flex-col gap-4">
              <div className="rounded-2xl border-2 border-dashed border-primary-200 bg-primary-50 p-6 text-center">
                <div className="text-4xl mb-2">📎</div>
                <p className="font-semibold text-gray-700 text-sm">Tegishli hujjatlar</p>
                <p className="text-xs text-gray-400 mt-1">PDF, DOCX, JPG — max 10 MB</p>
                <Button variant="secondary" size="sm" className="mt-3">
                  Fayllar qo'shish
                </Button>
              </div>

              {/* Summary */}
              <div className="card p-4">
                <p className="font-bold text-gray-900 mb-3">Xulosa</p>
                <div className="flex flex-col gap-2 text-sm">
                  <div className="flex justify-between"><span className="text-gray-500">Nomi</span><span className="font-medium max-w-[180px] text-right truncate">{form.title}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">Teglar</span><span className="font-medium">{selectedTags.map(t => `#${t}`).join(', ')}</span></div>
                  <div className="flex justify-between"><span className="text-gray-500">KPI</span><span className="font-medium">{kpis.filter(k => k.label).length} ta</span></div>
                </div>
              </div>

              <div className="bg-green-50 rounded-2xl p-4 text-sm text-green-800">
                ✅ Yuborilgandan so'ng <b>+50 XP</b> beriladi va 3 ta ekspertga
                avtomatik yo'naltiriladi (7 kun SLA).
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 p-4 safe-bottom">
        <div className="flex gap-3">
          {step > 1 && (
            <Button variant="secondary" onClick={() => setStep(s => s - 1)}>
              ←
            </Button>
          )}
          {step < 5 ? (
            <Button onClick={handleNext} fullWidth={step === 1} className="flex-1">
              Keyingi →
            </Button>
          ) : (
            <Button onClick={handleSubmit} loading={loading} className="flex-1">
              🚀 Yuborish (+50 XP)
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
