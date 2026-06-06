import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Input, Textarea, Select } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { authApi } from '../../api/auth'
import { useAuthStore } from '../../store'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const STEPS = [
  { id: 1, title: 'Shaxsiy ma\'lumotlar', titleRu: 'Личные данные' },
  { id: 2, title: 'Manzil', titleRu: 'Адрес' },
  { id: 3, title: 'Kasbiy ma\'lumotlar', titleRu: 'Профессиональные данные' },
  { id: 4, title: 'Hujjatlar', titleRu: 'Документы' },
  { id: 5, title: 'Tasdiqlash', titleRu: 'Подтверждение' },
]

const REGIONS_UZ = [
  'Toshkent shahri', 'Toshkent viloyati', 'Andijon', 'Farg\'ona', 'Namangan',
  'Samarqand', 'Buxoro', 'Navoiy', 'Qashqadaryo', 'Surxondaryo',
  'Jizzax', 'Sirdaryo', 'Xorazm', "Qoraqalpog'iston",
]

export default function Registration() {
  const navigate = useNavigate()
  const { setUser } = useAuthStore()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)

  const [form, setForm] = useState({
    pnfl: '', first_name: '', last_name: '', middle_name: '',
    phone: '+998', email: '', birth_date: '', gender: 'male',
    region_type: 'uzbekistan', region: '', city: '', address: '',
    account_status: 'worker', diploma_specialty: '', current_specialty: '',
    workplace: '', study_place: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm(f => ({ ...f, [field]: e.target.value }))
    setErrors(e => ({ ...e, [field]: '' }))
  }

  const validateStep = (): boolean => {
    const errs: Record<string, string> = {}
    if (step === 1) {
      if (!/^\d{14}$/.test(form.pnfl)) errs.pnfl = 'PNFL 14 ta raqam bo\'lishi kerak'
      if (!form.first_name.trim()) errs.first_name = 'Ism kiritilishi shart'
      if (!form.last_name.trim()) errs.last_name = 'Familiya kiritilishi shart'
      if (!form.phone || form.phone.length < 10) errs.phone = 'Telefon raqam to\'g\'ri kiritilishi shart'
      if (!form.email.includes('@')) errs.email = 'Email to\'g\'ri formatda bo\'lishi kerak'
      if (!form.birth_date) errs.birth_date = 'Tug\'ilgan sana kiritilishi shart'
    }
    if (step === 2) {
      if (!form.region) errs.region = 'Hudud tanlanishi shart'
    }
    if (step === 3) {
      if (!form.diploma_specialty.trim()) errs.diploma_specialty = 'Diplom mutaxassisligi kiritilishi shart'
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleNext = () => {
    if (!validateStep()) return
    if (step < 5) setStep(s => s + 1)
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const user = await authApi.register({
        ...form,
        birth_date: form.birth_date,
      })
      setUser(user)
      toast.success('Ro\'yxatdan o\'tdingiz! Moderator tekshiruvi kutilmoqda.')
      navigate('/')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Xatolik yuz berdi')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-700 to-primary-900 flex flex-col">
      {/* Header */}
      <div className="px-6 pt-12 pb-6 text-white">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
            <span className="text-2xl">🏥</span>
          </div>
          <div>
            <h1 className="text-xl font-bold">Tibbiyot Novatorlari</h1>
            <p className="text-primary-200 text-sm">Ro'yxatdan o'tish</p>
          </div>
        </div>

        {/* Step progress */}
        <div className="flex gap-1.5">
          {STEPS.map(s => (
            <div
              key={s.id}
              className={clsx(
                'h-1 rounded-full flex-1 transition-all duration-300',
                s.id <= step ? 'bg-white' : 'bg-white/30'
              )}
            />
          ))}
        </div>
        <p className="text-primary-200 text-xs mt-2">
          {step}-qadam: {STEPS[step - 1]?.title}
        </p>
      </div>

      {/* Form */}
      <div className="flex-1 bg-white rounded-t-3xl overflow-y-auto">
        <div className="p-6 pb-32 flex flex-col gap-4">

          {step === 1 && (
            <>
              <h2 className="text-lg font-bold text-gray-900 mb-1">Shaxsiy ma'lumotlar</h2>
              <Input label="PNFL (14 raqam)" placeholder="00000000000000" maxLength={14}
                value={form.pnfl} onChange={update('pnfl')} error={errors.pnfl}
                inputMode="numeric" />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Familiya" placeholder="Karimov" value={form.last_name} onChange={update('last_name')} error={errors.last_name} />
                <Input label="Ism" placeholder="Alisher" value={form.first_name} onChange={update('first_name')} error={errors.first_name} />
              </div>
              <Input label="Otasining ismi" placeholder="Umarovich" value={form.middle_name} onChange={update('middle_name')} />
              <Input label="Tug'ilgan sana" type="date" value={form.birth_date} onChange={update('birth_date')} error={errors.birth_date} />
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700">Jins</label>
                <div className="flex gap-3">
                  {[{ v: 'male', l: 'Erkak' }, { v: 'female', l: 'Ayol' }].map(g => (
                    <label key={g.v} className={clsx('flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border-2 cursor-pointer transition-all',
                      form.gender === g.v ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-500')}>
                      <input type="radio" className="sr-only" value={g.v} checked={form.gender === g.v}
                        onChange={() => setForm(f => ({ ...f, gender: g.v }))} />
                      <span className="font-semibold text-sm">{g.l}</span>
                    </label>
                  ))}
                </div>
              </div>
              <Input label="Telefon" placeholder="+998 90 123-45-67" value={form.phone} onChange={update('phone')} error={errors.phone} inputMode="tel" />
              <Input label="Email" type="email" placeholder="email@example.com" value={form.email} onChange={update('email')} error={errors.email} />
            </>
          )}

          {step === 2 && (
            <>
              <h2 className="text-lg font-bold text-gray-900 mb-1">Manzil ma'lumotlari</h2>
              <Select label="Mintaqa turi" value={form.region_type} onChange={update('region_type')}
                options={[{ value: 'uzbekistan', label: 'O\'zbekiston' }, { value: 'abroad', label: 'Xorij davlati' }]} />
              {form.region_type === 'uzbekistan' && (
                <Select label="Viloyat/Shahar" value={form.region} onChange={update('region')} error={errors.region}
                  options={[{ value: '', label: 'Tanlang...' }, ...REGIONS_UZ.map(r => ({ value: r, label: r }))]} />
              )}
              {form.region_type === 'abroad' && (
                <Input label="Davlat" placeholder="Masalan: Rossiya" value={form.region} onChange={update('region')} error={errors.region} />
              )}
              <Input label="Shahar/Tuman" placeholder="Toshkent" value={form.city} onChange={update('city')} />
              <Input label="Ko'cha, uy" placeholder="Navruz ko'chasi, 5-uy" value={form.address} onChange={update('address')} />
            </>
          )}

          {step === 3 && (
            <>
              <h2 className="text-lg font-bold text-gray-900 mb-1">Kasbiy ma'lumotlar</h2>
              <Select label="Status" value={form.account_status} onChange={update('account_status')}
                options={[
                  { value: 'school', label: 'Maktab o\'quvchisi' },
                  { value: 'bachelor', label: 'Bakalavr talabasi' },
                  { value: 'master', label: 'Magistrant' },
                  { value: 'phd', label: 'Doktorant' },
                  { value: 'worker', label: 'Tibbiyot xodimi' },
                ]} />
              <Input label="Diplom mutaxassisligi" placeholder="Umumiy tibbiyot" value={form.diploma_specialty} onChange={update('diploma_specialty')} error={errors.diploma_specialty} />
              <Input label="Hozirgi mutaxassislik" placeholder="Kardiolog (ixtiyoriy)" value={form.current_specialty} onChange={update('current_specialty')} />
              {['school', 'bachelor', 'master', 'phd'].includes(form.account_status) ? (
                <Input label="O'quv muassasasi" placeholder="ToshTibbiyot universiteti" value={form.study_place} onChange={update('study_place')} />
              ) : (
                <Input label="Ish joyi" placeholder="1-sonli Respublika shifoxonasi" value={form.workplace} onChange={update('workplace')} />
              )}
            </>
          )}

          {step === 4 && (
            <div className="flex flex-col gap-4">
              <h2 className="text-lg font-bold text-gray-900 mb-1">Hujjatlar yuklash</h2>
              <div className="rounded-2xl border-2 border-dashed border-primary-200 bg-primary-50 p-6 text-center">
                <div className="text-4xl mb-2">📄</div>
                <p className="font-semibold text-gray-700 text-sm">Diplom / Attestat</p>
                <p className="text-xs text-gray-400 mt-1">PDF, JPG yoki PNG — max 10 MB</p>
                <Button variant="secondary" size="sm" className="mt-3">
                  Fayl tanlash
                </Button>
              </div>
              <div className="rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50 p-5 text-center">
                <p className="text-sm text-gray-500 font-medium">Qo'shimcha hujjatlar (ixtiyoriy)</p>
                <p className="text-xs text-gray-400 mt-1">Scopus, ORCID yoki boshqa guvohnomalar</p>
                <Button variant="secondary" size="sm" className="mt-3">
                  Qo'shish
                </Button>
              </div>
              <div className="bg-blue-50 rounded-2xl p-4">
                <p className="text-sm text-blue-800 font-medium">ℹ️ Muhim</p>
                <p className="text-xs text-blue-600 mt-1">
                  Hujjatlar yuklangandan so'ng hisobingiz "Tekshiruvda" holatiga o'tadi.
                  Moderator 48 soat ichida tekshiradi va Telegram orqali xabar yuboradi.
                </p>
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="flex flex-col gap-4">
              <h2 className="text-lg font-bold text-gray-900 mb-1">Ma'lumotlarni tasdiqlash</h2>
              <div className="card p-4 flex flex-col gap-3">
                {[
                  { l: 'Ism Familiya', v: `${form.last_name} ${form.first_name} ${form.middle_name}`.trim() },
                  { l: 'PNFL', v: form.pnfl },
                  { l: 'Telefon', v: form.phone },
                  { l: 'Email', v: form.email },
                  { l: 'Viloyat', v: form.region },
                  { l: 'Mutaxassislik', v: form.diploma_specialty },
                  { l: 'Status', v: form.account_status },
                ].map(item => (
                  <div key={item.l} className="flex justify-between text-sm">
                    <span className="text-gray-500">{item.l}</span>
                    <span className="font-medium text-gray-800 text-right max-w-[180px] truncate">{item.v || '—'}</span>
                  </div>
                ))}
              </div>
              <div className="bg-amber-50 rounded-2xl p-4 text-sm text-amber-800">
                ⚠️ Ma'lumotlaringiz to'g'riligini tasdiqlang. Noto'g'ri ma'lumotlar ro'yxatdan o'tish rad etilishiga olib keladi.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom action */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 p-4 safe-bottom">
        <div className="flex gap-3">
          {step > 1 && (
            <Button variant="secondary" onClick={() => setStep(s => s - 1)} className="flex-1">
              ← Orqaga
            </Button>
          )}
          {step < 5 ? (
            <Button onClick={handleNext} fullWidth={step === 1} className="flex-1">
              Keyingi →
            </Button>
          ) : (
            <Button onClick={handleSubmit} loading={loading} className="flex-1" variant="primary">
              ✅ Ro'yxatdan o'tish
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
