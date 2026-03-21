import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { listingsApi } from '../api/listings'
import { ordersApi } from '../api/orders'
import type { Listing } from '../types'
import { useAuthStore } from '../store/authStore'
import StatusBadge from '../components/StatusBadge'

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuthStore()
  const [listing, setListing] = useState<Listing | null>(null)
  const [loading, setLoading] = useState(true)
  const [buying, setBuying] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    listingsApi.get(id)
      .then((r) => setListing(r.data))
      .catch(() => setError('Объявление не найдено'))
      .finally(() => setLoading(false))
  }, [id])

  const handleBuy = async () => {
    if (!isAuthenticated) { navigate('/login'); return }
    if (!listing) return
    setBuying(true)
    setError('')
    try {
      const orderResp = await ordersApi.create(listing.id)
      const order = orderResp.data
      const paymentResp = await ordersApi.createPayment(order.id)
      const checkoutUrl = paymentResp.data.payment.checkout_url
      if (checkoutUrl) {
        window.location.href = checkoutUrl
      } else {
        navigate(`/orders/${order.id}`)
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      setError(err?.response?.data?.error || 'Ошибка при создании заказа')
    } finally {
      setBuying(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl border border-gray-100 p-8 animate-pulse">
          <div className="h-4 bg-gray-100 rounded w-1/4 mb-6" />
          <div className="h-7 bg-gray-100 rounded w-3/4 mb-3" />
          <div className="h-4 bg-gray-100 rounded w-1/2 mb-2" />
          <div className="h-4 bg-gray-100 rounded w-2/3 mb-8" />
          <div className="h-10 bg-gray-100 rounded-xl w-1/3" />
        </div>
      </div>
    )
  }

  if (error && !listing) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16">
        <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg className="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h2 className="font-bold text-gray-800 mb-2">{error}</h2>
        <Link to="/listings" className="text-sm text-brand-600 hover:text-brand-700 font-medium">
          ← Все объявления
        </Link>
      </div>
    )
  }
  if (!listing) return null

  const isOwn = user?.id === listing.seller_user_id
  const eventDate = listing.event?.event_date
    ? new Date(listing.event.event_date).toLocaleDateString('ru-RU', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
      })
    : null

  const discount = listing.ticket?.face_value
    ? Math.round((1 - listing.price / listing.ticket.face_value) * 100)
    : 0

  return (
    <div className="max-w-2xl mx-auto animate-fade-in">
      {/* Breadcrumb */}
      <Link
        to="/listings"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-5 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Все объявления
      </Link>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        {/* Top accent */}
        <div className="h-1.5 bg-gradient-to-r from-brand-500 via-brand-400 to-violet-400" />

        <div className="p-7 md:p-8">
          {/* Status row */}
          <div className="flex items-center justify-between mb-5">
            <StatusBadge status={listing.status} />
            <span className="text-xs text-gray-400">
              {new Date(listing.created_at).toLocaleDateString('ru-RU')}
            </span>
          </div>

          {/* Title */}
          <h1 className="text-2xl font-bold text-gray-900 mb-3 leading-tight">
            {listing.event?.title || 'Билет'}
          </h1>

          {/* Event info */}
          <div className="space-y-2 mb-5">
            {eventDate && (
              <div className="flex items-start gap-2 text-gray-600 text-sm">
                <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="capitalize">{eventDate}</span>
              </div>
            )}
            {listing.event?.venue && (
              <div className="flex items-start gap-2 text-gray-600 text-sm">
                <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>{listing.event.venue}{listing.event.city ? `, ${listing.event.city}` : ''}</span>
              </div>
            )}
          </div>

          {/* Seat info */}
          {listing.ticket?.seat_info && (
            <div className="bg-brand-50 border border-brand-100 rounded-xl px-4 py-3 mb-5 flex items-center gap-3">
              <div className="w-8 h-8 bg-brand-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-brand-500 font-medium">Место в зале</p>
                <p className="text-sm font-bold text-brand-800">{listing.ticket.seat_info}</p>
              </div>
            </div>
          )}

          {/* Description */}
          {listing.description && (
            <p className="text-gray-600 text-sm leading-relaxed mb-5">{listing.description}</p>
          )}

          {/* Price & Buy */}
          <div className="border-t border-gray-100 pt-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-extrabold text-brand-600">
                    {listing.price.toLocaleString('ru-RU')} ₽
                  </p>
                  {discount > 0 && (
                    <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                      -{discount}%
                    </span>
                  )}
                </div>
                {listing.ticket?.face_value && (
                  <p className="text-sm text-gray-400 mt-0.5">
                    Номинал: <span className="line-through">{listing.ticket.face_value.toLocaleString('ru-RU')} ₽</span>
                  </p>
                )}
              </div>

              {listing.status === 'ACTIVE' && !isOwn && (
                <button
                  onClick={handleBuy}
                  disabled={buying}
                  className="flex items-center gap-2 bg-brand-600 text-white px-8 py-3.5 rounded-xl font-bold hover:bg-brand-700 disabled:opacity-50 transition-colors shadow-md shadow-brand-200"
                >
                  {buying ? (
                    <>
                      <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                      </svg>
                      Оформляем...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                      Купить
                    </>
                  )}
                </button>
              )}

              {isOwn && listing.status === 'ACTIVE' && (
                <span className="text-sm text-gray-400 italic bg-gray-50 px-4 py-2 rounded-xl">
                  Ваше объявление
                </span>
              )}

              {listing.status === 'SOLD' && (
                <span className="text-sm text-gray-400 italic">Билет продан</span>
              )}
            </div>

            {error && (
              <div className="mt-4 bg-red-50 border border-red-100 text-red-700 px-4 py-3 rounded-xl text-sm">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Info footer */}
        <div className="bg-brand-50 border-t border-brand-100 px-7 md:px-8 py-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-brand-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
              <svg className="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <p className="text-sm text-brand-700 leading-relaxed">
              <strong>Атомарное переоформление:</strong> после оплаты ваш билет будет переоформлен через
              систему организатора. Старый билет аннулируется — вы получите новый с вашим именем.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
