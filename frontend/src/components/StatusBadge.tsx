interface Props {
  status: string
}

const config: Record<string, { label: string; className: string }> = {
  PENDING_PAYMENT: { label: 'Ожидает оплаты', className: 'bg-yellow-100 text-yellow-800' },
  PAID: { label: 'Оплачен', className: 'bg-blue-100 text-blue-800' },
  CANCELLED: { label: 'Отменён', className: 'bg-gray-100 text-gray-500' },
  FAILED: { label: 'Ошибка', className: 'bg-red-100 text-red-800' },
  PENDING: { label: 'Переоформление...', className: 'bg-yellow-100 text-yellow-800' },
  SUCCESS: { label: 'Готов', className: 'bg-green-100 text-green-800' },
  CREATED: { label: 'Создан', className: 'bg-gray-100 text-gray-600' },
  CONFIRMED: { label: 'Подтверждён', className: 'bg-green-100 text-green-800' },
  ACTIVE: { label: 'Активен', className: 'bg-green-100 text-green-800' },
  SOLD: { label: 'Продан', className: 'bg-gray-100 text-gray-500' },
  BLOCKED: { label: 'Зарезервирован', className: 'bg-yellow-100 text-yellow-800' },
}

export default function StatusBadge({ status }: Props) {
  const cfg = config[status] ?? { label: status, className: 'bg-gray-100 text-gray-600' }
  return (
    <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}
