import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useState } from 'react'

const schema = z.object({
  full_name: z.string()
    .min(2, 'Имя слишком короткое (минимум 2 символа)'),
  email: z.string()
    .min(1, 'Введите email')
    .email('Некорректный формат email — например: ivan@mail.ru'),
  password: z.string()
    .min(8, 'Пароль слишком короткий (минимум 8 символов)'),
  phone: z.string().optional(),
})

type FormData = z.infer<typeof schema>

const SERVER_ERRORS: Record<string, string> = {
  email_already_exists:  'Этот email уже зарегистрирован',
  invalid_email_format:  'Некорректный формат email',
  email_required:        'Введите email',
  password_required:     'Введите пароль',
  password_too_short:    'Пароль слишком короткий (минимум 8 символов)',
  full_name_required:    'Введите ваше имя',
}

function getServerError(e: unknown): string {
  const err = e as { response?: { data?: { error?: string; code?: string } } }
  const code = err?.response?.data?.code
  if (code && SERVER_ERRORS[code]) return SERVER_ERRORS[code]
  return err?.response?.data?.error || 'Ошибка регистрации. Попробуйте позже'
}

const inputCls = (hasError: boolean) =>
  `w-full border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 transition-all ${
    hasError ? 'border-red-300 bg-red-50 focus:ring-red-300' : 'border-gray-200 bg-gray-50 focus:bg-white'
  }`

const FIELDS = [
  { name: 'full_name' as const, label: 'Имя и фамилия',           type: 'text',     placeholder: 'Иван Иванов',           autocomplete: 'name' },
  { name: 'email'     as const, label: 'Email',                   type: 'email',    placeholder: 'you@example.com',       autocomplete: 'email' },
  { name: 'password'  as const, label: 'Пароль',                  type: 'password', placeholder: 'Минимум 8 символов',    autocomplete: 'new-password' },
  { name: 'phone'     as const, label: 'Телефон (необязательно)', type: 'tel',      placeholder: '+7 (999) 000-00-00',    autocomplete: 'tel' },
]

export default function RegisterPage() {
  const navigate = useNavigate()
  const registerFn = useAuthStore((s) => s.register)
  const [serverError, setServerError] = useState('')

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setServerError('')
    try {
      await registerFn(data)
      navigate('/')
    } catch (e) {
      setServerError(getServerError(e))
    }
  }

  const isAlreadyExists = serverError.includes('уже зарегистрирован')

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center -mt-8 -mx-4 sm:-mx-6 lg:-mx-8 px-4 py-8">
      <div className="w-full max-w-sm animate-slide-up">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-brand-200">
            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Создать аккаунт</h1>
          <p className="text-sm text-gray-500 mt-1">Присоединяйтесь к TicketSwap</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-7">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {FIELDS.map(({ name, label, type, placeholder, autocomplete }) => (
              <div key={name}>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
                <input
                  {...register(name)}
                  type={type}
                  placeholder={placeholder}
                  autoComplete={autocomplete}
                  className={inputCls(!!errors[name])}
                />
                {errors[name] && (
                  <p className="mt-1.5 text-xs text-red-500">{errors[name]?.message}</p>
                )}
              </div>
            ))}

            {serverError && (
              <div className="bg-red-50 border border-red-100 text-red-700 px-4 py-3 rounded-xl text-sm flex items-start gap-2.5">
                <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>
                  {serverError}
                  {isAlreadyExists && (
                    <> —{' '}
                      <Link to="/login" className="underline font-semibold">войдите</Link>
                      {' '}или{' '}
                      <Link to="/forgot-password" className="underline font-semibold">восстановите пароль</Link>
                    </>
                  )}
                </span>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-brand-600 text-white py-3 rounded-xl font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors shadow-sm shadow-brand-200 mt-2"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  Регистрируем...
                </span>
              ) : 'Зарегистрироваться'}
            </button>
          </form>

          <div className="mt-5 pt-5 border-t border-gray-100 text-center text-sm text-gray-600">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="text-brand-600 hover:text-brand-700 font-semibold">
              Войти
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
