import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useState } from 'react'

const schema = z.object({
  full_name: z.string().min(2, 'Имя слишком короткое'),
  email: z.string().email('Некорректный email'),
  password: z.string().min(8, 'Пароль минимум 8 символов'),
  phone: z.string().optional(),
})

type FormData = z.infer<typeof schema>

export default function RegisterPage() {
  const navigate = useNavigate()
  const register_ = useAuthStore((s) => s.register)
  const [serverError, setServerError] = useState('')

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = async (data: FormData) => {
    setServerError('')
    try {
      await register_(data)
      navigate('/')
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      setServerError(err?.response?.data?.error || 'Ошибка регистрации')
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-12">
      <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">Регистрация</h1>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {([
            ['full_name', 'Имя', 'text', 'Иван Иванов'],
            ['email', 'Email', 'email', 'you@example.com'],
            ['password', 'Пароль', 'password', 'Минимум 8 символов'],
            ['phone', 'Телефон (необязательно)', 'tel', '+7 (999) 000-00-00'],
          ] as const).map(([name, label, type, placeholder]) => (
            <div key={name}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input
                {...register(name)}
                type={type}
                placeholder={placeholder}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              {errors[name] && (
                <p className="mt-1 text-xs text-red-500">{errors[name]?.message}</p>
              )}
            </div>
          ))}

          {serverError && (
            <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">{serverError}</div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-brand-600 text-white py-3 rounded-xl font-semibold hover:bg-brand-700 disabled:opacity-50 transition-colors"
          >
            {isSubmitting ? 'Регистрация...' : 'Зарегистрироваться'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          Уже есть аккаунт?{' '}
          <Link to="/login" className="text-brand-600 hover:text-brand-700 font-medium">Войти</Link>
        </p>
      </div>
    </div>
  )
}
