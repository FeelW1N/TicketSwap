import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { listingsApi } from '../api/listings'
import { useState } from 'react'

const schema = z.object({
  event_id: z.string().uuid('Введите корректный ID события'),
  price: z.coerce.number().positive('Цена должна быть положительной'),
  external_ticket_id: z.string().min(1, 'Укажите номер билета'),
  organizer_id: z.string().min(1, 'Укажите ID организатора'),
  seat_info: z.string().optional(),
  description: z.string().optional(),
})

type FormData = z.infer<typeof schema>

export default function SellPage() {
  const navigate = useNavigate()
  const [serverError, setServerError] = useState('')
  const [ticketFile, setTicketFile] = useState<File | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = async (data: FormData) => {
    setServerError('')
    const formData = new FormData()
    Object.entries(data).forEach(([k, v]) => {
      if (v !== undefined && v !== '') formData.append(k, String(v))
    })
    if (ticketFile) formData.append('ticket_file', ticketFile)

    try {
      const resp = await listingsApi.create(formData)
      navigate(`/listings/${resp.data.id}`)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      setServerError(err?.response?.data?.error || 'Ошибка при создании объявления')
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Продать билет</h1>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <Field label="ID события" error={errors.event_id?.message}>
            <input {...register('event_id')} placeholder="uuid события" className={inputCls} />
          </Field>

          <Field label="ID организатора" error={errors.organizer_id?.message}>
            <input {...register('organizer_id')} placeholder="org-1" className={inputCls} />
          </Field>

          <Field label="Номер / ID билета (у организатора)" error={errors.external_ticket_id?.message}>
            <input {...register('external_ticket_id')} placeholder="TKT-12345" className={inputCls} />
          </Field>

          <Field label="Цена продажи (₽)" error={errors.price?.message}>
            <input
              {...register('price')}
              type="number"
              step="1"
              placeholder="1500"
              className={inputCls}
            />
          </Field>

          <Field label="Место (сектор, ряд, место)" error={errors.seat_info?.message}>
            <input {...register('seat_info')} placeholder="Сектор A, ряд 5, место 12" className={inputCls} />
          </Field>

          <Field label="Описание (необязательно)" error={errors.description?.message}>
            <textarea {...register('description')} rows={3} className={inputCls} placeholder="Доп. информация о билете" />
          </Field>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Файл билета (PDF / PNG, необязательно)
            </label>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => setTicketFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
            />
          </div>

          {serverError && (
            <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">{serverError}</div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-brand-600 text-white py-3 rounded-xl font-semibold text-lg hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? 'Публикация...' : 'Опубликовать объявление'}
          </button>
        </form>
      </div>

      <div className="mt-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-700">
        Перед публикацией система верифицирует билет у организатора и проверит, что цена не превышает исходную более чем на 20%.
      </div>
    </div>
  )
}

const inputCls = 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent'

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  )
}
