import { Link } from 'react-router-dom'
import type { Listing } from '../types'

interface Props {
  listing: Listing
}

const statusLabel: Record<string, string> = {
  ACTIVE: 'Доступен',
  SOLD: 'Продан',
  BLOCKED: 'Зарезервирован',
}

const statusColor: Record<string, string> = {
  ACTIVE: 'bg-green-100 text-green-800',
  SOLD: 'bg-gray-100 text-gray-500',
  BLOCKED: 'bg-yellow-100 text-yellow-800',
}

export default function ListingCard({ listing }: Props) {
  const eventDate = listing.event?.event_date
    ? new Date(listing.event.event_date).toLocaleDateString('ru-RU', {
        day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
      })
    : null

  return (
    <Link to={`/listings/${listing.id}`} className="block">
      <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow p-5 border border-gray-100">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 text-lg truncate">
              {listing.event?.title || 'Мероприятие'}
            </h3>
            {eventDate && (
              <p className="text-sm text-gray-500 mt-1">{eventDate}</p>
            )}
            {listing.event?.venue && (
              <p className="text-sm text-gray-500">{listing.event.venue}, {listing.event.city}</p>
            )}
            {listing.ticket?.seat_info && (
              <p className="text-sm text-gray-600 mt-1">Место: {listing.ticket.seat_info}</p>
            )}
          </div>
          <div className="text-right shrink-0">
            <p className="text-2xl font-bold text-brand-600">
              {listing.price.toLocaleString('ru-RU')} ₽
            </p>
            {listing.ticket?.face_value && (
              <p className="text-xs text-gray-400 line-through">
                {listing.ticket.face_value.toLocaleString('ru-RU')} ₽
              </p>
            )}
          </div>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <span className={`inline-block text-xs font-medium px-2 py-1 rounded-full ${statusColor[listing.status]}`}>
            {statusLabel[listing.status]}
          </span>
          <span className="text-xs text-gray-400">
            {new Date(listing.created_at).toLocaleDateString('ru-RU')}
          </span>
        </div>
      </div>
    </Link>
  )
}
