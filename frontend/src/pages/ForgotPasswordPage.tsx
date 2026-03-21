import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link } from 'react-router-dom'
import { authApi } from '../api/auth'

const schema = z.object({
  email: z.string().email('Некорректный email'),
})

type FormData = z.infer<typeof schema>

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false)
  const [debugToken, setDebugToken] = useState('')
  const [serverError, setServerError] = useState('')

  const { register, handleSubmit, getValues, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setServerError('')
    try {
      const resp = await authApi.forgotPassword(data.email)
      setSent(true)
      if (resp.data.debug_token) {
        setDebugToken(resp.data.debug_token)
      }
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      setServerError(err?.response?.data?.error || 'Произошла ошибка. Попробуйте позже')
    }
  }

  if (sent) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center -mt-8 -mx-4 sm:-mx-6 lg:-mx-8 px-4">
        <div className="w-full max-w-sm animate-slide-up">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
            <div className="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Письмо отправлено</h2>
            <p className="text-gray-500 text-sm mb-5 leading-relaxed">
              Если адрес <strong className="text-gray-700">{getValues('email')}</strong> зарегистрирован —
              письмо со ссылкой придёт в течение минуты.
            </p>

            {debugToken && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-5 text-left">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-4 h-4 rounded bg-amber-400 flex items-center justify-center text-white text-[10px] font-bold">D</span>
                  <p className="text-xs font-bold text-amber-700">DEV — ссылка для сброса</p>
                </div>
                <Link
                  to={`/reset-password?token=${debugToken}`}
                  className="text-xs text-brand-600 break-all underline font-medium"
                >
                  /reset-password?token={debugToken.slice(0, 20)}…
                </Link>
              </div>
            )}

            <Link to="/login" className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700 transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              Вернуться к входу
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center -mt-8 -mx-4 sm:-mx-6 lg:-mx-8 px-4">
      <div className="w-full max-w-sm animate-slide-up">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-brand-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Забыли пароль?</h1>
          <p className="text-sm text-gray-500 mt-1">Пришлём ссылку для сброса на email</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-7">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
              <input
                {...register('email')}
                type="email"
                placeholder="you@example.com"
                className={`w-full border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 transition-all ${
                  errors.email
                    ? 'border-red-300 bg-red-50 focus:ring-red-300'
                    : 'border-gray-200 bg-gray-50 focus:bg-white focus:ring-brand-500'
                }`}
                autoFocus
              />
              {errors.email && <p className="mt-1.5 text-xs text-red-500">{errors.email.message}</p>}
            </div>

            {serverError && (
              <div className="bg-red-50 border border-red-100 text-red-700 px-4 py-3 rounded-xl text-sm">
                {serverError}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-brand-600 text-white py-3 rounded-xl font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors shadow-sm shadow-brand-200"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                  </svg>
                  Отправляем...
                </span>
              ) : 'Отправить ссылку'}
            </button>
          </form>

          <div className="mt-5 pt-5 border-t border-gray-100 text-center text-sm text-gray-600">
            Вспомнили пароль?{' '}
            <Link to="/login" className="text-brand-600 hover:text-brand-700 font-semibold">Войти</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
