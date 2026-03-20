import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { ordersApi } from '../api/orders'
import type { Order } from '../types'
import StatusBadge from '../components/StatusBadge'

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [order, setOrder] = useState<Order | null>(null)
  const [loading, setLoading] = useState(true)
  const [downloadUrl, setDownloadUrl] = useState('')

  const fetchOrder = useCallback(() => {
    if (!id) return
    ordersApi.get(id).then((r) => setOrder(r.data)).catch(console.error).finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    fetchOrder()
    // Polling: если переоформление PENDING — проверяем каждые 5 сек
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

  if (loading) return <div className="text-center py-16 text-gray-500">Загрузка...</div>
  if (!order) return <div className="text-center py-16 text-red-500">Заказ не найден</div>

  const reissue = order.reissue
  const payment = order.payment

  return (
    <div className="max-w-xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Заказ #{order.id.slice(0, 8)}</h1>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 space-y-6">
        {/* Статус заказа */}
        <Section title="Статус заказа">
          <StatusBadge status={order.status} />
          <p className="text-sm text-gray-500 mt-1">
            Создан: {new Date(order.created_at).toLocaleString('ru-RU')}
          </p>
        </Section>

        {/* Оплата */}
        {payment && (
          <Section title="Оплата">
            <StatusBadge status={payment.status} />
            <p className="text-sm text-gray-600 mt-1">
              Сумма: <strong>{payment.amount.toLocaleString('ru-RU')} ₽</strong>
            </p>
            {payment.checkout_url && payment.status === 'CREATED' && (
              <a
                href={payment.checkout_url}
                className="mt-3 inline-block bg-brand-600 text-white px-6 py-2 rounded-lg text-sm font-semibold hover:bg-brand-700 transition-colors"
              >
                Оплатить
              </a>
            )}
          </Section>
        )}

        {/* Переоформление */}
        {reissue && (
          <Section title="Переоформление билета">
            <StatusBadge status={reissue.status} />
            {reissue.status === 'PENDING' && (
              <p className="text-sm text-gray-500 mt-2 flex items-center gap-2">
                <span className="inline-block w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                Идёт переоформление у организатора...
              </p>
            )}
            {reissue.status === 'SUCCESS' && (
              <div className="mt-3">
                <p className="text-sm text-green-700 mb-2">
                  Новый билет готов! ID: <code>{reissue.external_new_ticket_id}</code>
                </p>
                <button
                  onClick={handleDownload}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg text-sm font-semibold hover:bg-green-700 transition-colors"
                >
                  Скачать билет
                </button>
                {downloadUrl && (
                  <a href={downloadUrl} target="_blank" rel="noopener noreferrer"
                    className="ml-3 text-sm text-brand-600 underline">
                    Открыть ссылку
                  </a>
                )}
              </div>
            )}
            {reissue.status === 'FAILED' && (
              <p className="text-sm text-red-600 mt-2">
                Ошибка переоформления: {reissue.error_code} — {reissue.error_message}
              </p>
            )}
          </Section>
        )}

        {order.status === 'PENDING_PAYMENT' && (
          <button
            onClick={() => ordersApi.cancel(order.id).then(fetchOrder)}
            className="text-sm text-red-500 hover:text-red-600"
          >
            Отменить заказ
          </button>
        )}
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">{title}</h3>
      {children}
    </div>
  )
}
