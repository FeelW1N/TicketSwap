import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listingsApi } from '../api/listings'
import type { Listing } from '../types'
import ListingCard from '../components/ListingCard'

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
    <div>
      {/* Hero */}
      <section className="text-center py-16 px-4">
        <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 mb-4">
          Безопасная перепродажа<br />
          <span className="text-brand-600">электронных билетов</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          Атомарное переоформление через API организатора — старый билет аннулируется,
          покупатель получает новый. Никаких дубликатов.
        </p>
        <div className="flex gap-4 justify-center">
          <Link to="/listings" className="bg-brand-600 text-white px-8 py-3 rounded-xl text-lg font-semibold hover:bg-brand-700 transition-colors">
            Найти билет
          </Link>
          <Link to="/sell" className="border-2 border-brand-600 text-brand-600 px-8 py-3 rounded-xl text-lg font-semibold hover:bg-brand-50 transition-colors">
            Продать билет
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {[
          { icon: '✅', title: 'Верификация билета', desc: 'Проверяем подлинность и принадлежность у организатора перед публикацией' },
          { icon: '🔄', title: 'Атомарное переоформление', desc: 'Старый билет аннулируется, новый выпускается на имя покупателя' },
          { icon: '🔒', title: 'Безопасная оплата', desc: 'Оплата через Stripe, средства переводятся только после получения нового билета' },
        ].map((f) => (
          <div key={f.title} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="font-bold text-gray-900 mb-2">{f.title}</h3>
            <p className="text-gray-600 text-sm">{f.desc}</p>
          </div>
        ))}
      </section>

      {/* Latest listings */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Свежие объявления</h2>
          <Link to="/listings" className="text-brand-600 hover:text-brand-700 text-sm font-medium">
            Все объявления →
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">Загрузка...</div>
        ) : listings.length === 0 ? (
          <div className="text-center py-12 text-gray-500">Пока нет объявлений</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {listings.map((l) => <ListingCard key={l.id} listing={l} />)}
          </div>
        )}
      </section>
    </div>
  )
}
