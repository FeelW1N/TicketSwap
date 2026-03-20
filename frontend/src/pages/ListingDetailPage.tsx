import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
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
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
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

  if (loading) return <div className="text-center py-16 text-gray-500">Загрузка...</div>
  if (error && !listing) return <div className="text-center py-16 text-red-500">{error}</div>
  if (!listing) return null

  const isOwn = user?.id === listing.seller_user_id
  const eventDate = listing.event?.event_date
    ? new Date(listing.event.event_date).toLocaleDateString('ru-RU', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
      })
    : null

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <div className="mb-4">
          <StatusBadge status={listing.status} />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {listing.event?.title || 'Билет'}
        </h1>

        {eventDate && <p className="text-gray-600 mb-1">{eventDate}</p>}
        {listing.event?.venue && (
          <p className="text-gray-600 mb-4">{listing.event.venue}{listing.event.city ? `, ${listing.event.city}` : ''}</p>
        )}

        {listing.ticket?.seat_info && (
          <div className="bg-gray-50 rounded-lg p-3 mb-4">
            <span className="text-sm text-gray-500">Место: </span>
            <span className="font-medium">{listing.ticket.seat_info}</span>
          </div>
        )}

        {listing.description && (
          <p className="text-gray-700 mb-4">{listing.description}</p>
        )}

        <div className="border-t pt-4 flex items-center justify-between">
          <div>
            <p className="text-3xl font-bold text-brand-600">
              {listing.price.toLocaleString('ru-RU')} ₽
            </p>
            {listing.ticket?.face_value && (
              <p className="text-sm text-gray-400">
                Исходная цена: {listing.ticket.face_value.toLocaleString('ru-RU')} ₽
              </p>
            )}
          </div>

          {listing.status === 'ACTIVE' && !isOwn && (
            <button
              onClick={handleBuy}
              disabled={buying}
              className="bg-brand-600 text-white px-8 py-3 rounded-xl text-lg font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
            >
              {buying ? 'Оформляем...' : 'Купить'}
            </button>
          )}

          {isOwn && listing.status === 'ACTIVE' && (
            <span className="text-sm text-gray-500 italic">Это ваше объявление</span>
          )}
        </div>

        {error && <p className="mt-3 text-red-500 text-sm">{error}</p>}

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-700">
            🔒 После оплаты ваш билет будет переоформлен через систему организатора.
            Старый билет аннулируется, вы получите новый с вашим именем.
          </p>
        </div>
      </div>
    </div>
  )
}
