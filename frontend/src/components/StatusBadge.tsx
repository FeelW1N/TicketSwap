interface Props {
  status: string
}

const config: Record<string, { label: string; dot: string; className: string }> = {
  PENDING_PAYMENT: { label: 'Ожидает оплаты',    dot: 'bg-amber-400',   className: 'bg-amber-50 text-amber-700 border border-amber-200' },
  PAID:            { label: 'Оплачен',            dot: 'bg-blue-400',    className: 'bg-blue-50 text-blue-700 border border-blue-200' },
  CANCELLED:       { label: 'Отменён',            dot: 'bg-gray-300',    className: 'bg-gray-50 text-gray-500 border border-gray-200' },
  FAILED:          { label: 'Ошибка',             dot: 'bg-red-400',     className: 'bg-red-50 text-red-700 border border-red-200' },
  PENDING:         { label: 'Переоформление...',  dot: 'bg-violet-400',  className: 'bg-violet-50 text-violet-700 border border-violet-200' },
  SUCCESS:         { label: 'Готов',              dot: 'bg-green-400',   className: 'bg-green-50 text-green-700 border border-green-200' },
  CREATED:         { label: 'Создан',             dot: 'bg-gray-300',    className: 'bg-gray-50 text-gray-600 border border-gray-200' },
  CONFIRMED:       { label: 'Подтверждён',        dot: 'bg-green-400',   className: 'bg-green-50 text-green-700 border border-green-200' },
  REFUNDED:        { label: 'Возвращён',          dot: 'bg-violet-400',  className: 'bg-violet-50 text-violet-700 border border-violet-200' },
  ACTIVE:          { label: 'Доступен',           dot: 'bg-green-400',   className: 'bg-green-50 text-green-700 border border-green-200' },
  SOLD:            { label: 'Продан',             dot: 'bg-gray-300',    className: 'bg-gray-50 text-gray-500 border border-gray-200' },
  BLOCKED:         { label: 'Зарезервирован',     dot: 'bg-amber-400',   className: 'bg-amber-50 text-amber-700 border border-amber-200' },
}

export default function StatusBadge({ status }: Props) {
  const cfg = config[status] ?? { label: status, dot: 'bg-gray-300', className: 'bg-gray-50 text-gray-600 border border-gray-200' }
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${cfg.className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} flex-shrink-0`} />
      {cfg.label}
    </span>
  )
}
