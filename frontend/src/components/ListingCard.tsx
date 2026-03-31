import { Link } from 'react-router-dom'
import type { Listing } from '../types'

interface Props {
  listing: Listing
  isOwn?: boolean
}

const statusDot: Record<string, string> = {
  ACTIVE:  'bg-green-400',
  SOLD:    'bg-gray-300',
  BLOCKED: 'bg-amber-400',
}

const statusLabel: Record<string, string> = {
  ACTIVE:  'Доступен',
  SOLD:    'Продан',
  BLOCKED: 'Зарезервирован',
}

export default function ListingCard({ listing, isOwn = false }: Props) {
  const eventDate = listing.event?.event_date
    ? new Date(listing.event.event_date).toLocaleDateString('ru-RU', {
        day: 'numeric', month: 'short', year: 'numeric',
      })
    : null

  const eventTime = listing.event?.event_date
    ? new Date(listing.event.event_date).toLocaleTimeString('ru-RU', {
        hour: '2-digit', minute: '2-digit',
      })
    : null

  return (
    <Link to={`/listings/${listing.id}`} className="block group">
      <div className="bg-white rounded-2xl border border-gray-100 p-5 card-hover h-full flex flex-col">
        {/* Status + date */}
        <div className="flex items-center justify-between mb-3">
          <span className={`inline-flex items-center gap-1.5 text-xs font-medium text-gray-500`}>
            <span className={`w-1.5 h-1.5 rounded-full ${statusDot[listing.status] ?? 'bg-gray-300'}`} />
            {statusLabel[listing.status] ?? listing.status}
          </span>
          {eventDate && (
            <span className="text-xs text-gray-400">{eventDate}</span>
          )}
        </div>

        {/* Title */}
        <h3 className="font-bold text-gray-900 text-base leading-snug group-hover:text-brand-700 transition-colors line-clamp-2 mb-1.5">
          {listing.event?.title || 'Мероприятие'}
        </h3>

        {listing.event?.organizer_id && (
          <p className="text-[11px] text-gray-400 mb-2">
            Организатор: <span className="font-semibold text-gray-500">{listing.event.organizer_id}</span>
          </p>
        )}

        {/* Venue */}
        {listing.event?.venue && (
          <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
            <svg className="w-3 h-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {listing.event.venue}{listing.event.city ? `, ${listing.event.city}` : ''}
          </p>
        )}

        {/* Time */}
        {eventTime && (
          <p className="text-xs text-gray-400 mb-3 flex items-center gap-1">
            <svg className="w-3 h-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {eventTime}
          </p>
        )}

        {/* Seat */}
        {listing.ticket?.seat_info && (
          <div className="text-xs bg-gray-50 text-gray-600 px-2.5 py-1.5 rounded-lg mb-3 inline-block self-start">
            Место: <span className="font-semibold">{listing.ticket.seat_info}</span>
          </div>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Price row */}
        <div className="flex items-end justify-between pt-3 border-t border-gray-50 mt-3">
          <div>
            <p className="text-xl font-extrabold text-brand-600">
              {listing.price.toLocaleString('ru-RU')} ₽
            </p>
            {listing.ticket?.face_value && (
              <p className="text-xs text-gray-400 line-through leading-none">
                {listing.ticket.face_value.toLocaleString('ru-RU')} ₽
              </p>
            )}
          </div>

          {listing.status === 'ACTIVE' && !isOwn && (
            <span className="text-xs font-semibold text-brand-600 bg-brand-50 px-3 py-1.5 rounded-lg group-hover:bg-brand-600 group-hover:text-white transition-colors">
              Купить →
            </span>
          )}
          {listing.status === 'ACTIVE' && isOwn && (
            <span className="text-xs font-medium text-gray-400 bg-gray-50 px-3 py-1.5 rounded-lg">
              Моё объявление
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
