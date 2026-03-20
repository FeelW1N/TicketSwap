import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ordersApi } from '../api/orders'
import type { Order } from '../types'
import StatusBadge from '../components/StatusBadge'

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    ordersApi.list()
      .then((r) => setOrders(r.data.items))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-16 text-gray-500">Загрузка...</div>

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Мои покупки</h1>

      {orders.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p>У вас пока нет заказов</p>
          <Link to="/listings" className="mt-4 inline-block text-brand-600 hover:text-brand-700">
            Найти билеты →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {orders.map((order) => (
            <Link key={order.id} to={`/orders/${order.id}`} className="block">
              <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 hover:shadow-md transition-shadow flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Заказ #{order.id.slice(0, 8)}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleDateString('ru-RU')}
                  </p>
                </div>
                <div className="text-right flex items-center gap-4">
                  <span className="font-semibold text-gray-900">
                    {order.amount.toLocaleString('ru-RU')} ₽
                  </span>
                  <StatusBadge status={order.status} />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
