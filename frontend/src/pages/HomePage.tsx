import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listingsApi } from '../api/listings'
import type { Listing } from '../types'
import ListingCard from '../components/ListingCard'

const features = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    title: 'Верификация билета',
    desc: 'Проверяем подлинность и принадлежность у организатора перед публикацией',
    color: 'text-brand-500 bg-brand-50',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    title: 'Атомарное переоформление',
    desc: 'Старый билет аннулируется, новый выпускается на имя покупателя через API организатора',
    color: 'text-violet-500 bg-violet-50',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
    title: 'Безопасная оплата',
    desc: 'Покупатель оплачивает заказ из внутреннего кошелька, а деньги продавцу зачисляются после успешного переоформления',
    color: 'text-emerald-500 bg-emerald-50',
  },
]

export default function HomePage() {
  const [listings, setListings] = useState<Listing[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listingsApi.list({ per_page: 8 })
      .then((r) => setListings(r.data.items))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <section className="relative -mx-4 sm:-mx-6 lg:-mx-8 -mt-8 mb-12 overflow-hidden">
        <div className="bg-hero-gradient px-4 sm:px-6 lg:px-8 py-20 md:py-28">
          {/* Decorative orbs */}
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-500 opacity-10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-violet-400 opacity-10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative max-w-7xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20 text-white/80 text-xs font-medium px-3 py-1.5 rounded-full mb-6 backdrop-blur-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse-slow"></span>
              Безопасная перепродажа · НИУ ВШЭ
            </div>

            <h1 className="text-4xl md:text-6xl font-extrabold text-white mb-5 leading-tight tracking-tight">
              Перепродажа билетов<br />
              <span className="gradient-text">без риска обмана</span>
            </h1>

            <p className="text-lg md:text-xl text-white/70 max-w-2xl mx-auto mb-10 font-light">
              Атомарное переоформление через API организатора —
              старый билет аннулируется, покупатель получает новый. Никаких дубликатов.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                to="/listings"
                className="inline-flex items-center justify-center gap-2 bg-white text-brand-700 px-8 py-3.5 rounded-xl text-base font-bold hover:bg-brand-50 transition-colors shadow-lg shadow-black/20"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Найти билет
              </Link>
              <Link
                to="/sell"
                className="inline-flex items-center justify-center gap-2 bg-white/10 border border-white/25 text-white px-8 py-3.5 rounded-xl text-base font-bold hover:bg-white/20 transition-colors backdrop-blur-sm"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                Продать билет
              </Link>
            </div>

            {/* Stats */}
            <div className="flex flex-col sm:flex-row gap-6 justify-center mt-12 text-center">
              {[
                { value: '100%', label: 'Верифицированные билеты' },
                { value: '5%', label: 'Комиссия платформы' },
                { value: 'Кошелёк', label: 'Простая оплата' },
              ].map((stat) => (
                <div key={stat.label} className="text-white/80">
                  <p className="text-2xl font-bold text-white">{stat.value}</p>
                  <p className="text-xs text-white/50 mt-0.5">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* Bottom wave */}
        <div className="absolute bottom-0 left-0 right-0 h-8 bg-gray-50" style={{
          clipPath: 'ellipse(55% 100% at 50% 100%)'
        }} />
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-14 animate-slide-up">
        {features.map((f) => (
          <div
            key={f.title}
            className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm card-hover"
          >
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${f.color}`}>
              {f.icon}
            </div>
            <h3 className="font-bold text-gray-900 mb-2">{f.title}</h3>
            <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Latest listings */}
      <section>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Свежие объявления</h2>
            <p className="text-sm text-gray-500 mt-0.5">Последние добавленные билеты</p>
          </div>
          <Link
            to="/listings"
            className="flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700 transition-colors"
          >
            Все объявления
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-white rounded-2xl border border-gray-100 p-5 animate-pulse">
                <div className="h-5 bg-gray-100 rounded-lg w-3/4 mb-3" />
                <div className="h-3 bg-gray-100 rounded w-1/2 mb-2" />
                <div className="h-3 bg-gray-100 rounded w-2/3 mb-4" />
                <div className="h-7 bg-gray-100 rounded-lg w-1/3" />
              </div>
            ))}
          </div>
        ) : listings.length === 0 ? (
          <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
            <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
              </svg>
            </div>
            <p className="text-gray-500 text-sm">Пока нет объявлений</p>
            <Link to="/sell" className="mt-3 inline-block text-sm font-medium text-brand-600 hover:text-brand-700">
              Добавить первый →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {listings.map((l) => <ListingCard key={l.id} listing={l} />)}
          </div>
        )}
      </section>
    </div>
  )
}
