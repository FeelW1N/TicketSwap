import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { listingsApi } from '../api/listings'
import { walletApi } from '../api/wallet'
import type { Listing } from '../types'

export default function ProfilePage() {
  const { user, fetchMe } = useAuthStore()
  const [listings, setListings] = useState<Listing[]>([])
  const [balance, setBalance] = useState<number>(0)
  const [topupAmount, setTopupAmount] = useState('')
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [topupError, setTopupError] = useState('')
  const [topupSuccess, setTopupSuccess] = useState('')
  const [withdrawError, setWithdrawError] = useState('')
  const [withdrawSuccess, setWithdrawSuccess] = useState('')
  const [toppingUp, setToppingUp] = useState(false)
  const [withdrawing, setWithdrawing] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [listingsResp, balanceResp] = await Promise.all([
          listingsApi.list({ per_page: 100 }),
          walletApi.getBalance(),
        ])
        // Фильтруем только свои листинги
        const myListings = listingsResp.data.items.filter(
          (l) => l.seller_user_id === user?.id
        )
        setListings(myListings)
        setBalance(balanceResp.data.balance)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [user?.id])

  const handleWithdraw = async () => {
    const amount = parseFloat(withdrawAmount)
    if (!amount || amount <= 0) {
      setWithdrawError('Введите сумму')
      return
    }
    setWithdrawError('')
    setWithdrawSuccess('')
    setWithdrawing(true)
    try {
      const resp = await walletApi.withdraw(amount)
      setBalance(resp.data.balance)
      setWithdrawAmount('')
      setWithdrawSuccess(`Выведено ₽${amount.toLocaleString('ru-RU')}. Новый баланс: ₽${resp.data.balance.toLocaleString('ru-RU', { minimumFractionDigits: 2 })}`)
      await fetchMe()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      setWithdrawError(err?.response?.data?.error || 'Ошибка вывода')
    } finally {
      setWithdrawing(false)
    }
  }

  const handleTopup = async () => {
    const amount = parseFloat(topupAmount)
    if (!amount || amount <= 0) {
      setTopupError('Введите сумму')
      return
    }
    setTopupError('')
    setTopupSuccess('')
    setToppingUp(true)
    try {
      const resp = await walletApi.topup(amount)
      setBalance(resp.data.balance)
      setTopupAmount('')
      setTopupSuccess(`Баланс пополнен на ₽${amount.toLocaleString('ru-RU')}. Текущий баланс: ₽${resp.data.balance.toLocaleString('ru-RU', { minimumFractionDigits: 2 })}`)
      await fetchMe()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      setTopupError(err?.response?.data?.error || 'Ошибка пополнения')
    } finally {
      setToppingUp(false)
    }
  }

  const statusLabel: Record<string, { label: string; cls: string }> = {
    ACTIVE: { label: 'Активно', cls: 'bg-green-50 text-green-700 border border-green-200' },
    SOLD:   { label: 'Продано', cls: 'bg-blue-50 text-blue-700 border border-blue-200' },
    BLOCKED:{ label: 'Снято', cls: 'bg-gray-100 text-gray-500 border border-gray-200' },
  }

  return (
    <div className="max-w-3xl mx-auto animate-fade-in space-y-8">

      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Личный кабинет</h1>
        <p className="text-sm text-gray-500 mt-1">{user?.email}</p>
      </div>

      {/* Карточка пользователя */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 flex items-center gap-5">
        <div className="w-16 h-16 rounded-full bg-brand-100 flex items-center justify-center text-2xl font-bold text-brand-700 shrink-0">
          {user?.full_name?.charAt(0).toUpperCase() ?? '?'}
        </div>
        <div>
          <p className="text-xl font-semibold text-gray-900">{user?.full_name}</p>
          <p className="text-sm text-gray-500">{user?.email}</p>
          {user?.phone && <p className="text-sm text-gray-400">{user.phone}</p>}
        </div>
      </div>

      {/* Кошелёк */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="h-1 bg-gradient-to-r from-brand-500 to-violet-400" />
        <div className="p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <svg className="w-5 h-5 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              Кошелёк
            </h2>
            <span className="text-2xl font-bold text-brand-600">
              ₽ {balance.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          <p className="text-xs text-gray-400 mb-4">
            Кошелёк используется и для покупки, и для вывода. Продавцу деньги зачисляются после успешного переоформления билета. Минимальная сумма вывода — 100 ₽.
          </p>

          <div className="grid gap-3 sm:grid-cols-[1fr_auto] mb-4">
            <input
              type="number"
              min="1"
              step="1"
              placeholder="Сумма пополнения"
              value={topupAmount}
              onChange={(e) => setTopupAmount(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 bg-gray-50 focus:bg-white"
            />
            <button
              onClick={handleTopup}
              disabled={toppingUp}
              className="px-5 py-2.5 bg-emerald-600 text-white text-sm font-semibold rounded-xl hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              {toppingUp ? 'Пополняем...' : 'Пополнить'}
            </button>
          </div>

          {topupError && (
            <p className="mb-2 text-xs text-red-500">{topupError}</p>
          )}
          {topupSuccess && (
            <p className="mb-3 text-xs text-green-600">{topupSuccess}</p>
          )}

          <div className="flex gap-3">
            <input
              type="number"
              min="100"
              step="1"
              placeholder="Сумма вывода"
              value={withdrawAmount}
              onChange={(e) => setWithdrawAmount(e.target.value)}
              className="flex-1 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 bg-gray-50 focus:bg-white"
            />
            <button
              onClick={handleWithdraw}
              disabled={withdrawing || balance < 100}
              className="px-5 py-2.5 bg-brand-600 text-white text-sm font-semibold rounded-xl hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {withdrawing ? 'Выводим...' : 'Вывести'}
            </button>
          </div>

          {withdrawError && (
            <p className="mt-2 text-xs text-red-500">{withdrawError}</p>
          )}
          {withdrawSuccess && (
            <p className="mt-2 text-xs text-green-600">{withdrawSuccess}</p>
          )}
          {balance < 100 && balance > 0 && (
            <p className="mt-2 text-xs text-gray-400">Недостаточно средств для вывода (мин. 100 ₽)</p>
          )}
        </div>
      </div>

      {/* Мои объявления */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Мои объявления</h2>
          <Link to="/sell" className="text-sm font-semibold text-brand-600 hover:text-brand-700">
            + Продать билет
          </Link>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : listings.length === 0 ? (
          <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-10 text-center">
            <p className="text-gray-400 text-sm">У вас пока нет объявлений</p>
            <Link to="/sell" className="mt-3 inline-block text-sm font-semibold text-brand-600 hover:text-brand-700">
              Разместить билет →
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {listings.map((listing) => {
              const badge = statusLabel[listing.status] ?? { label: listing.status, cls: 'bg-gray-100 text-gray-500' }
              return (
                <Link
                  key={listing.id}
                  to={`/listings/${listing.id}`}
                  className="flex items-center justify-between bg-white rounded-xl border border-gray-100 px-5 py-4 hover:border-brand-200 hover:shadow-sm transition-all group"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate group-hover:text-brand-700 transition-colors">
                      {listing.event?.title ?? 'Мероприятие'}
                    </p>
                    {listing.ticket?.seat_info && (
                      <p className="text-xs text-gray-400 mt-0.5">{listing.ticket.seat_info}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0 ml-4">
                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${badge.cls}`}>
                      {badge.label}
                    </span>
                    <span className="text-sm font-bold text-gray-900">
                      ₽ {listing.price.toLocaleString('ru-RU')}
                    </span>
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
