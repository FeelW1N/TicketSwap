import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { authApi } from '../api/auth'

const schema = z.object({
  password: z.string().min(8, 'Пароль минимум 8 символов'),
  confirm: z.string(),
}).refine((d) => d.password === d.confirm, {
  message: 'Пароли не совпадают',
  path: ['confirm'],
})

type FormData = z.infer<typeof schema>

const inputCls = (hasError: boolean) =>
  `w-full border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 transition-all ${
    hasError ? 'border-red-300 bg-red-50 focus:ring-red-300' : 'border-gray-200 bg-gray-50 focus:bg-white focus:ring-brand-500'
  }`

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') || ''
  const [serverError, setServerError] = useState('')
  const [done, setDone] = useState(false)

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setServerError('')
    try {
      await authApi.resetPassword(token, data.password)
      setDone(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      setServerError(err?.response?.data?.error || 'Произошла ошибка. Попробуйте запросить новую ссылку')
    }
  }

  if (!token) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center -mt-8 -mx-4 sm:-mx-6 lg:-mx-8 px-4">
        <div className="w-full max-w-sm animate-slide-up">
          <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
            <div className="w-12 h-12 bg-red-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="font-bold text-red-800 mb-2">Ссылка недействительна</h2>
            <p className="text-sm text-red-600 mb-5">Токен сброса пароля отсутствует в ссылке.</p>
            <Link to="/forgot-password" className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700">
              Запросить новую ссылку →
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (done) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center -mt-8 -mx-4 sm:-mx-6 lg:-mx-8 px-4">
        <div className="w-full max-w-sm animate-slide-up">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
            <div className="w-14 h-14 bg-green-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-7 h-7 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Пароль изменён!</h2>
            <p className="text-gray-500 text-sm mb-5">Перенаправляем на страницу входа...</p>
            <Link to="/login" className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700">
              Войти сейчас →
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
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Новый пароль</h1>
          <p className="text-sm text-gray-500 mt-1">Придумайте надёжный пароль</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-7">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Новый пароль</label>
              <input
                {...register('password')}
                type="password"
                placeholder="Минимум 8 символов"
                className={inputCls(!!errors.password)}
                autoFocus
              />
              {errors.password && <p className="mt-1.5 text-xs text-red-500">{errors.password.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Повторите пароль</label>
              <input
                {...register('confirm')}
                type="password"
                placeholder="Введите пароль ещё раз"
                className={inputCls(!!errors.confirm)}
              />
              {errors.confirm && <p className="mt-1.5 text-xs text-red-500">{errors.confirm.message}</p>}
            </div>

            {serverError && (
              <div className="bg-red-50 border border-red-100 text-red-700 px-4 py-3 rounded-xl text-sm">
                {serverError}
                {serverError.includes('истекла') && (
                  <span> — <Link to="/forgot-password" className="underline font-semibold">запросить новую</Link></span>
                )}
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
                  Сохраняем...
                </span>
              ) : 'Сохранить пароль'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
