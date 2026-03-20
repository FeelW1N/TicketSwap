import { useEffect, useState } from 'react'
import { listingsApi } from '../api/listings'
import type { Listing } from '../types'
import ListingCard from '../components/ListingCard'

export default function ListingsPage() {
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const load = (p: number) => {
    setLoading(true)
    listingsApi.list({ page: p, per_page: 12 })
      .then((r) => {
        setListings(r.data.items)
        setTotalPages(r.data.pages)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(page) }, [page])

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Все объявления</h1>

      {loading ? (
        <div className="text-center py-16 text-gray-500">Загрузка...</div>
      ) : listings.length === 0 ? (
        <div className="text-center py-16 text-gray-500">Нет доступных объявлений</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {listings.map((l) => <ListingCard key={l.id} listing={l} />)}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-4 py-2 rounded-lg border disabled:opacity-40 hover:bg-gray-50"
              >
                ← Назад
              </button>
              <span className="px-4 py-2 text-gray-600">{page} / {totalPages}</span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-4 py-2 rounded-lg border disabled:opacity-40 hover:bg-gray-50"
              >
                Вперёд →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
