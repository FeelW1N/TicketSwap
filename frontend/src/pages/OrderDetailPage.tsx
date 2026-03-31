import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ordersApi } from '../api/orders'
import type { Order } from '../types'
import StatusBadge from '../components/StatusBadge'
import { useAuthStore } from '../store/authStore'

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { fetchMe } = useAuthStore()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloadUrl, setDownloadUrl] = useState('')
  const [payError, setPayError] = useState('')
  const [paying, setPaying] = useState(false)

  const fetchOrder = useCallback(() => {
    if (!id) return
    ordersApi.get(id).then((r) => setOrder(r.data)).catch(console.error).finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    fetchOrder()
    const interval = setInterval(() => {
      if (order?.reissue?.status === 'PENDING') fetchOrder()
    }, 5000)
    return () => clearInterval(interval)
  }, [fetchOrder, order?.reissue?.status])

  const handleDownload = async () => {
    if (!order?.reissue?.ticket_id) return
    try {
      const resp = await ordersApi.downloadTicket(order.reissue.ticket_id)
      setDownloadUrl(resp.data.download_url)
      window.open(resp.data.download_url, '_blank')
    } catch (e) {
      console.error(e)
    }
  }

  const handlePay = async () => {
    if (!order) return
    setPayError('')
    setPaying(true)
    try {
      await ordersApi.createPayment(order.id)
      await fetchMe()
      fetchOrder()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      setPayError(err?.response?.data?.error || 'Не удалось оплатить заказ')
    } finally {
      setPaying(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-xl mx-auto">
        <div className="bg-white rounded-2xl border border-gray-100 p-8 animate-pulse space-y-6">
          <div className="h-6 bg-gray-100 rounded w-1/3" />
          <div className="space-y-2">
            <div className="h-4 bg-gray-100 rounded w-1/4" />
            <div className="h-6 bg-gray-100 rounded-full w-24" />
          </div>
        </div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="max-w-xl mx-auto text-center py-16">
        <p className="text-red-500">Заказ не найден</p>
        <Link to="/orders" className="mt-3 inline-block text-sm text-brand-600">← Мои покупки</Link>
      </div>
    )
  }

  const reissue = order.reissue
  const payment = order.payment

  return (
    <div className="max-w-xl mx-auto animate-fade-in">
      {/* Breadcrumb */}
      <Link
        to="/orders"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-5 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Мои покупки
      </Link>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="h-1.5 bg-gradient-to-r from-brand-500 via-brand-400 to-violet-400" />

        <div className="p-7 space-y-6">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Заказ #{order.id.slice(0, 8).toUpperCase()}
              </h1>
              <p className="text-sm text-gray-400 mt-0.5">
                {new Date(order.created_at).toLocaleString('ru-RU')}
              </p>
            </div>
            <StatusBadge status={order.status} />
          </div>

          {/* Payment */}
          {payment && (
            <Section title="Оплата" icon={
              <svg className="w-4 h-4 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
            }>
                <div className="flex items-center justify-between">
                  <div>
                    <StatusBadge status={payment.status} />
                    <p className="text-sm text-gray-600 mt-2">
                      Сумма: <strong className="text-gray-900">{payment.amount.toLocaleString('ru-RU')} ₽</strong>
                    </p>
                  </div>
                  {payment.status === 'CREATED' && (
                    <button
                      onClick={handlePay}
                      disabled={paying}
                      className="bg-brand-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors shadow-sm"
                    >
                      {paying ? 'Оплачиваем...' : 'Оплатить с кошелька'}
                    </button>
                  )}
                </div>
                {payError && (
                  <p className="text-sm text-red-600 mt-3">{payError}</p>
                )}
              </Section>
            )}

          {/* Reissue */}
          {reissue && (
            <Section title="Переоформление билета" icon={
              <svg className="w-4 h-4 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            }>
              <StatusBadge status={reissue.status} />

              {reissue.status === 'PENDING' && (
                <div className="mt-3 flex items-center gap-2.5 text-sm text-gray-500">
                  <svg className="animate-spin w-4 h-4 text-brand-500" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  Идёт переоформление у организатора...
                </div>
              )}

              {reissue.status === 'SUCCESS' && (
                <div className="mt-3 space-y-3">
                  <div className="bg-green-50 border border-green-100 rounded-xl px-4 py-3">
                    <p className="text-sm text-green-700 font-medium">Новый билет готов!</p>
                    {reissue.external_new_ticket_id && (
                      <p className="text-xs text-green-600 mt-0.5">
                        ID: <code className="font-mono">{reissue.external_new_ticket_id}</code>
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleDownload}
                      className="flex items-center gap-2 bg-green-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-green-700 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Скачать билет
                    </button>
                    {downloadUrl && (
                      <a href={downloadUrl} target="_blank" rel="noopener noreferrer"
                        className="text-sm text-brand-600 hover:text-brand-700 font-medium underline">
                        Открыть
                      </a>
                    )}
                  </div>
                </div>
              )}

              {reissue.status === 'FAILED' && (
                <div className="mt-3 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
                  <p className="text-sm text-red-700 font-medium">Ошибка переоформления</p>
                  {reissue.error_message && (
                    <p className="text-xs text-red-600 mt-0.5">{reissue.error_code} — {reissue.error_message}</p>
                  )}
                  <p className="text-xs text-red-600 mt-1">Деньги будут возвращены на ваш внутренний кошелёк.</p>
                </div>
              )}
            </Section>
          )}

          {order.status === 'PENDING_PAYMENT' && (
            <div className="pt-2 border-t border-gray-50">
              <button
                onClick={() => ordersApi.cancel(order.id).then(fetchOrder)}
                className="text-sm text-red-400 hover:text-red-600 transition-colors"
              >
                Отменить заказ
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({
  title,
  icon,
  children,
}: {
  title: string
  icon?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <div className="border-t border-gray-100 pt-5">
      <div className="flex items-center gap-2 mb-3">
        {icon && (
          <div className="w-6 h-6 bg-brand-50 rounded-md flex items-center justify-center">
            {icon}
          </div>
        )}
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">{title}</h3>
      </div>
      {children}
    </div>
  )
}
