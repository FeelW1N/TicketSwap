import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50 shadow-sm">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center shadow-md group-hover:bg-brand-700 transition-colors">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                </svg>
              </div>
              <div className="flex flex-col">
                <span className="text-lg font-bold text-gray-900 leading-none">TicketSwap</span>
                <span className="text-[10px] text-gray-400 leading-none font-medium tracking-wide">безопасная перепродажа</span>
              </div>
            </Link>

            {/* Nav */}
            <nav className="flex items-center gap-1">
              <Link
                to="/listings"
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors"
              >
                Все билеты
              </Link>

              {isAuthenticated ? (
                <>
                  <Link
                    to="/sell"
                    className="px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors shadow-sm"
                  >
                    + Продать
                  </Link>
                  <Link
                    to="/orders"
                    className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors"
                  >
                    Покупки
                  </Link>
                  <div className="flex items-center gap-2 pl-2 ml-1 border-l border-gray-100">
                    <div className="w-7 h-7 rounded-full bg-brand-100 flex items-center justify-center">
                      <span className="text-xs font-bold text-brand-700">
                        {user?.full_name?.charAt(0).toUpperCase() ?? '?'}
                      </span>
                    </div>
                    <span className="text-sm text-gray-700 font-medium max-w-[120px] truncate hidden sm:block">
                      {user?.full_name}
                    </span>
                    <button
                      onClick={handleLogout}
                      className="text-xs text-gray-400 hover:text-red-500 transition-colors px-1"
                    >
                      Выйти
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors"
                  >
                    Войти
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors shadow-sm"
                  >
                    Регистрация
                  </Link>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      <footer className="bg-white border-t border-gray-100 mt-auto">
        <div className="max-w-[1440px] mx-auto px-4 py-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-brand-600 flex items-center justify-center">
                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
                </svg>
              </div>
              <span className="text-sm font-semibold text-gray-700">TicketSwap</span>
            </div>
            <p className="text-xs text-gray-400 text-center">
              © 2026 TicketSwap — атомарная передача прав на билет. НИУ ВШЭ, БПМИ237.
            </p>
            <div className="flex items-center gap-1 text-xs text-gray-400">
              <span className="w-2 h-2 rounded-full bg-green-400 inline-block"></span>
              Защищено · Stripe · MinIO
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
