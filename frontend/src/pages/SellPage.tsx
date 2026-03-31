import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { listingsApi } from '../api/listings'
import { useEffect, useState } from 'react'
import { organizersApi } from '../api/organizers'
import type { Organizer, OrganizerEvent } from '../types'

const schema = z.object({
  organizer_id:       z.string().min(1, 'Выберите организатора'),
  external_event_id:  z.string().min(1, 'Выберите мероприятие'),
  price:              z.coerce.number().positive('Цена должна быть положительной'),
  external_ticket_id: z.string().min(1, 'Укажите номер билета'),
  seat_info:          z.string().optional(),
  description:        z.string().optional(),
})

type FormData = z.infer<typeof schema>

const inputCls = (hasError?: boolean) =>
  `w-full border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 transition-all ${
    hasError
      ? 'border-red-300 bg-red-50 focus:ring-red-300'
      : 'border-gray-200 bg-gray-50 focus:bg-white focus:ring-brand-500'
  }`

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
      {children}
      {error && <p className="mt-1.5 text-xs text-red-500">{error}</p>}
    </div>
  )
}

export default function SellPage() {
  const navigate = useNavigate()
  const [serverError, setServerError] = useState('')
  const [ticketFile, setTicketFile] = useState<File | null>(null)
  const [organizers, setOrganizers] = useState<Organizer[]>([])
  const [organizerEvents, setOrganizerEvents] = useState<OrganizerEvent[]>([])
  const [loadingOrganizers, setLoadingOrganizers] = useState(true)
  const [loadingEvents, setLoadingEvents] = useState(false)

  const { register, watch, setValue, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const organizerId = watch('organizer_id')
  const externalEventId = watch('external_event_id')
  const selectedEvent = organizerEvents.find((event) => event.id === externalEventId)

  useEffect(() => {
    organizersApi.list()
      .then((resp) => setOrganizers(resp.data.items))
      .catch(() => setServerError('Не удалось загрузить список организаторов'))
      .finally(() => setLoadingOrganizers(false))
  }, [])

  useEffect(() => {
    if (!organizerId) {
      setOrganizerEvents([])
      setValue('external_event_id', '')
      return
    }

    setLoadingEvents(true)
    setOrganizerEvents([])
    setValue('external_event_id', '')
    organizersApi.listEvents(organizerId)
      .then((resp) => setOrganizerEvents(resp.data.items))
      .catch(() => setServerError('Не удалось загрузить мероприятия организатора'))
      .finally(() => setLoadingEvents(false))
  }, [organizerId, setValue])

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
      const err = e as { response?: { data?: { error?: string; code?: string } } }
      const code = err?.response?.data?.code
      const fallback = err?.response?.data?.error || 'Ошибка при создании объявления'
      const friendlyMessage = code === 'TICKET_NOT_FOUND'
        ? 'Такой номер билета не найден у выбранного организатора. Используйте один из demo-номеров ниже или проверьте ввод.'
        : code === 'EVENT_MISMATCH'
          ? 'Этот билет не относится к выбранному мероприятию. Проверьте выбор мероприятия и номер билета.'
          : code === 'EVENT_NOT_FOUND'
            ? 'Выбранное мероприятие не найдено у организатора. Попробуйте выбрать его заново.'
            : fallback
      setServerError(friendlyMessage)
    }
  }

  return (
    <div className="max-w-xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-7">
        <h1 className="text-3xl font-bold text-gray-900">Продать билет</h1>
        <p className="text-sm text-gray-500 mt-1">Заполните данные для публикации объявления</p>
      </div>

      <div className="mb-4 rounded-2xl border border-amber-100 bg-amber-50 px-4 py-4">
        <p className="text-sm font-semibold text-amber-900 mb-1">Демо-режим</p>
        <p className="text-sm text-amber-800 leading-relaxed">
          Выберите организатора и мероприятие, а затем используйте один из предложенных тестовых номеров билетов
          или свой demo-номер из mock organizer catalog.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="h-1.5 bg-gradient-to-r from-brand-500 via-brand-400 to-violet-400" />

        <div className="p-7">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <Field label="Организатор" error={errors.organizer_id?.message}>
              <select
                {...register('organizer_id')}
                className={inputCls(!!errors.organizer_id)}
                defaultValue=""
                disabled={loadingOrganizers}
              >
                <option value="">{loadingOrganizers ? 'Загружаем организаторов...' : 'Выберите организатора'}</option>
                {organizers.map((organizer) => (
                  <option key={organizer.id} value={organizer.id}>{organizer.name}</option>
                ))}
              </select>
            </Field>

            <Field label="Мероприятие" error={errors.external_event_id?.message}>
              <select
                {...register('external_event_id')}
                className={inputCls(!!errors.external_event_id)}
                defaultValue=""
                disabled={!organizerId || loadingEvents}
              >
                <option value="">
                  {!organizerId
                    ? 'Сначала выберите организатора'
                    : loadingEvents
                      ? 'Загружаем мероприятия...'
                      : 'Выберите мероприятие'}
                </option>
                {organizerEvents.map((event) => (
                  <option key={event.id} value={event.id}>
                    {event.title} · {event.city} · {new Date(event.event_date).toLocaleDateString('ru-RU')}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Номер билета" error={errors.external_ticket_id?.message}>
              <input
                {...register('external_ticket_id')}
                placeholder={selectedEvent?.sample_ticket_ids?.[0] ? `Например, ${selectedEvent.sample_ticket_ids[0]}` : 'Введите номер билета'}
                className={inputCls(!!errors.external_ticket_id)}
              />
            </Field>

            {selectedEvent && (
              <div className="rounded-xl border border-gray-100 bg-gray-50 px-4 py-4 space-y-2">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{selectedEvent.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {selectedEvent.city} · {selectedEvent.venue} · {new Date(selectedEvent.event_date).toLocaleString('ru-RU')}
                    </p>
                  </div>
                  {selectedEvent.category && (
                    <span className="text-[11px] uppercase tracking-wide text-brand-700 bg-brand-100 rounded-full px-2.5 py-1 font-semibold">
                      {selectedEvent.category}
                    </span>
                  )}
                </div>

                {selectedEvent.description && (
                  <p className="text-sm text-gray-600">{selectedEvent.description}</p>
                )}

                {!!selectedEvent.sample_ticket_ids?.length && (
                  <div className="pt-1">
                    <p className="text-xs font-medium text-gray-500 mb-2">Примеры тестовых номеров билетов для демо-режима:</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedEvent.sample_ticket_ids.map((ticketId) => (
                        <button
                          key={ticketId}
                          type="button"
                          onClick={() => setValue('external_ticket_id', ticketId, { shouldValidate: true })}
                          className="text-xs font-mono px-2.5 py-1.5 rounded-lg border border-brand-200 bg-white text-brand-700 hover:bg-brand-50 transition-colors"
                        >
                          {ticketId}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <Field label="Цена продажи (₽)" error={errors.price?.message}>
              <div className="relative">
                <input
                  {...register('price')}
                  type="number"
                  step="1"
                  placeholder="1500"
                  className={`${inputCls(!!errors.price)} pr-8`}
                />
                <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm font-medium">₽</span>
              </div>
            </Field>

            <Field label="Место (сектор, ряд, место)" error={errors.seat_info?.message}>
              <input
                {...register('seat_info')}
                placeholder="Сектор A, ряд 5, место 12"
                className={inputCls(!!errors.seat_info)}
              />
            </Field>

            <Field label="Описание (необязательно)" error={errors.description?.message}>
              <textarea
                {...register('description')}
                rows={3}
                placeholder="Дополнительная информация о билете..."
                className={`${inputCls()} resize-none`}
              />
            </Field>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Файл билета (PDF / PNG, необязательно)
              </label>
              <label className="flex items-center gap-3 w-full border-2 border-dashed border-gray-200 rounded-xl px-4 py-4 cursor-pointer hover:border-brand-300 hover:bg-brand-50 transition-colors group">
                <div className="w-9 h-9 bg-gray-100 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:bg-brand-100 transition-colors">
                  <svg className="w-4 h-4 text-gray-400 group-hover:text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-700 truncate">
                    {ticketFile ? ticketFile.name : 'Нажмите для выбора файла'}
                  </p>
                  <p className="text-xs text-gray-400">PDF, PNG, JPG до 10 МБ</p>
                </div>
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setTicketFile(e.target.files?.[0] ?? null)}
                  className="hidden"
                />
              </label>
            </div>

            {serverError && (
              <div className="bg-red-50 border border-red-100 text-red-700 px-4 py-3 rounded-xl text-sm flex items-start gap-2.5">
                <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>{serverError}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-brand-600 text-white py-3.5 rounded-xl font-bold text-base hover:bg-brand-700 disabled:opacity-50 transition-colors shadow-sm shadow-brand-200"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  Публикуем...
                </span>
              ) : 'Опубликовать объявление'}
            </button>
          </form>
        </div>
      </div>

      {/* Info note */}
      <div className="mt-4 flex items-start gap-3 bg-brand-50 border border-brand-100 rounded-xl px-4 py-4">
        <div className="w-8 h-8 bg-brand-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
          <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-sm text-brand-700 leading-relaxed">
          Сначала выберите организатора и мероприятие, а затем укажите номер билета с вашего исходного билета.
          Перед публикацией система верифицирует билет у организатора и проверит, что цена не превышает исходную
          <strong> более чем на 20%</strong>.
        </p>
      </div>
    </div>
  )
}
