import { Link, useNavigate } from 'react-router-dom'
import { Search, LayoutDashboard, Bookmark, ShoppingBag, Users, LogOut } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'

export default function Header() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AD</span>
            </div>
            <span className="font-bold text-xl text-gray-900">AdSight</span>
          </Link>

          {/* Nav */}
          <nav className="hidden md:flex items-center gap-1">
            <Link
              to="/search"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 text-sm font-medium"
            >
              <Search size={18} />
              Tim kiem
            </Link>
            <Link
              to="/dashboard"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 text-sm font-medium"
            >
              <LayoutDashboard size={18} />
              Dashboard
            </Link>
            <Link
              to="/boards"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 text-sm font-medium"
            >
              <Bookmark size={18} />
              Boards
            </Link>
            <Link
              to="/tiktok-shop"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 text-sm font-medium"
            >
              <ShoppingBag size={18} />
              TikTok Shop
            </Link>
            <Link
              to="/advertisers"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 text-sm font-medium"
            >
              <Users size={18} />
              Advertisers
            </Link>
          </nav>

          {/* Auth */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">{user?.full_name}</span>
                <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full uppercase">
                  {user?.tier}
                </span>
                <button
                  onClick={handleLogout}
                  className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
                >
                  <LogOut size={18} />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg"
                >
                  Dang nhap
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg"
                >
                  Dang ky
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
