import { useEffect, useState, useCallback } from 'react'
import { listingsApi } from '../api/listings'
import { useAuthStore } from '../store/authStore'
import type { Listing } from '../types'
import ListingCard from '../components/ListingCard'

type SortOption = 'newest' | 'price_asc' | 'price_desc' | 'date_asc' | 'date_desc'

const SORT_LABELS: Record<SortOption, string> = {
  newest:     'Новые сначала',
  price_asc:  'Цена: по возрастанию',
  price_desc: 'Цена: по убыванию',
  date_asc:   'Дата: ближайшие',
  date_desc:  'Дата: поздние',
}

const CATEGORIES = [
  { value: '', label: 'Все категории' },
  { value: 'concert', label: 'Концерты' },
  { value: 'sport', label: 'Спорт' },
  { value: 'theatre', label: 'Театр' },
  { value: 'festival', label: 'Фестивали' },
  { value: 'other', label: 'Другое' },
]

export default function ListingsPage() {
  const { user } = useAuthStore()
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)

  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState<SortOption>('newest')

  const load = useCallback((p: number) => {
    setLoading(true)
    listingsApi.list({
      page: p, per_page: 12,
      q: search || undefined,
      category: category || undefined,
      sort,
    })
      .then((r) => {
        setListings(r.data.items)
        setTotalPages(r.data.pages)
        setTotal(r.data.total ?? r.data.items.length)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [search, category, sort])

  useEffect(() => { setPage(1) }, [search, category, sort])
  useEffect(() => { load(page) }, [page, load])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSearch(searchInput)
  }

  const clearFilters = () => {
    setSearchInput(''); setSearch(''); setCategory(''); setSort('newest')
  }

  const hasFilters = !!(search || category || sort !== 'newest')

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Все объявления</h1>
        {!loading && (
          <p className="text-sm text-gray-500 mt-1">
            {total > 0 ? `Найдено: ${total} билетов` : 'Нет доступных билетов'}
          </p>
        )}
      </div>

      {/* Search + filters */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 mb-6 space-y-3">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Поиск по названию, городу, площадке..."
              className="w-full pl-9 pr-9 py-2.5 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-400 transition-all"
            />
            {searchInput && (
              <button type="button" onClick={() => { setSearchInput(''); setSearch('') }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-300 hover:text-gray-500">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
          <button type="submit" className="px-4 py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 transition-colors">
            Найти
          </button>
        </form>

        <div className="flex flex-wrap gap-2 items-center">
          <select value={category} onChange={(e) => setCategory(e.target.value)}
            className="text-sm border border-gray-200 rounded-xl px-3 py-2 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-400 transition-all cursor-pointer">
            {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>

          <select value={sort} onChange={(e) => setSort(e.target.value as SortOption)}
            className="text-sm border border-gray-200 rounded-xl px-3 py-2 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-400 transition-all cursor-pointer">
            {Object.entries(SORT_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>

          {hasFilters && (
            <button onClick={clearFilters} className="text-sm text-gray-400 hover:text-red-500 flex items-center gap-1 transition-colors ml-auto">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Сбросить
            </button>
          )}
        </div>

        {search && (
          <div className="flex items-center gap-1.5 text-xs text-brand-700">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Поиск: <span className="font-semibold">«{search}»</span>
          </div>
        )}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
              <div className="h-4 bg-gray-100 rounded-lg w-1/4 mb-4" />
              <div className="h-5 bg-gray-100 rounded-lg w-3/4 mb-2" />
              <div className="h-3 bg-gray-100 rounded w-1/2 mb-1" />
              <div className="h-3 bg-gray-100 rounded w-2/3 mb-5" />
              <div className="h-6 bg-gray-100 rounded-lg w-1/3" />
            </div>
          ))}
        </div>
      ) : listings.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl border border-gray-100">
          <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-700 mb-1">
            {hasFilters ? 'Ничего не найдено' : 'Нет доступных объявлений'}
          </h3>
          <p className="text-sm text-gray-400">
            {hasFilters ? 'Попробуйте изменить параметры поиска' : 'Пока никто не выставил билеты на продажу'}
          </p>
          {hasFilters && (
            <button onClick={clearFilters} className="mt-3 text-sm font-semibold text-brand-600 hover:text-brand-700">
              Сбросить фильтры
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {listings.map((l) => (
              <ListingCard key={l.id} listing={l} isOwn={l.seller_user_id === user?.id} />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-10">
              <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
                className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium border border-gray-200 rounded-xl disabled:opacity-40 hover:bg-gray-50 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
                Назад
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter(p => Math.abs(p - page) <= 2 || p === 1 || p === totalPages)
                  .reduce<(number | '...')[]>((acc, p, idx, arr) => {
                    if (idx > 0 && (p as number) - (arr[idx - 1] as number) > 1) acc.push('...')
                    acc.push(p); return acc
                  }, [])
                  .map((p, i) => p === '...' ? (
                    <span key={`dots-${i}`} className="px-2 text-gray-400 text-sm">…</span>
                  ) : (
                    <button key={p} onClick={() => setPage(p as number)}
                      className={`w-9 h-9 rounded-xl text-sm font-medium transition-colors ${p === page ? 'bg-brand-600 text-white shadow-sm' : 'hover:bg-gray-100 text-gray-600'}`}>
                      {p}
                    </button>
                  ))
                }
              </div>
              <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}
                className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium border border-gray-200 rounded-xl disabled:opacity-40 hover:bg-gray-50 transition-colors">
                Вперёд
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
