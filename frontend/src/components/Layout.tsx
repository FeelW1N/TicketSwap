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
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <span className="text-2xl font-bold text-brand-600">TicketSwap</span>
              <span className="text-sm text-gray-500">безопасная перепродажа</span>
            </Link>

            <nav className="flex items-center gap-6">
              <Link to="/listings" className="text-gray-600 hover:text-brand-600 transition-colors">
                Все билеты
              </Link>
              {isAuthenticated ? (
                <>
                  <Link to="/sell" className="bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors">
                    Продать билет
                  </Link>
                  <Link to="/orders" className="text-gray-600 hover:text-brand-600 transition-colors">
                    Мои покупки
                  </Link>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-gray-700">{user?.full_name}</span>
                    <button
                      onClick={handleLogout}
                      className="text-sm text-gray-500 hover:text-red-500 transition-colors"
                    >
                      Выйти
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <Link to="/login" className="text-gray-600 hover:text-brand-600 transition-colors">
                    Войти
                  </Link>
                  <Link to="/register" className="bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors">
                    Регистрация
                  </Link>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      <footer className="mt-auto bg-white border-t">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-500">
          TicketSwap © 2026 — атомарная передача прав на билет
        </div>
      </footer>
    </div>
  )
}
