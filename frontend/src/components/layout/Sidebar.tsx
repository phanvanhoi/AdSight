import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Search, LayoutDashboard, Bookmark, ShoppingBag,
  Users, ChevronLeft, ChevronRight, LogOut, CreditCard, Radar, Settings
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/authStore'
import { useUIStore } from '../../stores/uiStore'
import { getMe } from '../../api/billing'

const NAV_ITEMS = [
  { path: '/search', icon: Search, label: 'Tìm kiếm' },
  { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/boards', icon: Bookmark, label: 'Bảng lưu' },
  { path: '/tiktok-shop', icon: ShoppingBag, label: 'TikTok Shop' },
  { path: '/advertisers', icon: Users, label: 'Nhà quảng cáo' },
  { path: '/alerts', icon: Radar, label: 'Theo dõi đối thủ' },
  { path: '/settings', icon: Settings, label: 'Cài đặt' },
  { path: '/pricing', icon: CreditCard, label: 'Nâng cấp', freeOnly: true },
]

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUIStore()
  const location = useLocation()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuthStore()

  const { data: profile } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    enabled: isAuthenticated,
  })

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-surface-900 text-white flex flex-col transition-all duration-300 z-40 ${
        sidebarCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-white/10">
        <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <span className="text-white font-bold text-sm">AD</span>
        </div>
        {!sidebarCollapsed && (
          <span className="font-bold text-lg tracking-tight">AdSight</span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {NAV_ITEMS
          .filter((item) => {
            if ('freeOnly' in item && item.freeOnly && user?.tier !== 'free') return false
            return true
          })
          .map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
                title={sidebarCollapsed ? item.label : undefined}
              >
                <item.icon size={20} className="flex-shrink-0" />
                {!sidebarCollapsed && <span>{item.label}</span>}
              </Link>
            )
          })}
      </nav>

      {/* Usage indicator for free users */}
      {!sidebarCollapsed && isAuthenticated && user?.tier === 'free' && profile && (
        <div className="px-3 py-2 border-t border-white/10">
          <div className="text-xs text-gray-400 mb-1">
            Tìm kiếm: {profile.usage.searches.used}/{profile.usage.searches.limit}
          </div>
          <div className="w-full bg-white/10 rounded-full h-1.5">
            <div
              className="bg-primary-500 h-1.5 rounded-full transition-all"
              style={{ width: `${Math.min(100, (profile.usage.searches.used / profile.usage.searches.limit) * 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* AI credits indicator for paid users */}
      {!sidebarCollapsed && isAuthenticated && user?.tier !== 'free' && profile && profile.usage.ai_credits.limit > 0 && (
        <div className="px-3 py-2 border-t border-white/10">
          <div className="text-xs text-gray-400 mb-1">
            AI Credits: {profile.usage.ai_credits.used}/{profile.usage.ai_credits.limit}
          </div>
          <div className="w-full bg-white/10 rounded-full h-1.5">
            <div
              className="bg-fuchsia-500 h-1.5 rounded-full transition-all"
              style={{ width: `${Math.min(100, (profile.usage.ai_credits.used / profile.usage.ai_credits.limit) * 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Bottom — User + Collapse */}
      <div className="border-t border-white/10 p-3 space-y-2">
        {isAuthenticated && !sidebarCollapsed && (
          <div className="flex items-center gap-2 px-2">
            <div className="w-8 h-8 rounded-full bg-primary-700 flex items-center justify-center text-xs font-semibold">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-gray-400 capitalize">{user?.tier}</p>
            </div>
            <button onClick={handleLogout} className="p-1.5 text-gray-400 hover:text-white rounded">
              <LogOut size={16} />
            </button>
          </div>
        )}
        {isAuthenticated && sidebarCollapsed && (
          <button onClick={handleLogout} className="w-full flex items-center justify-center p-2 text-gray-400 hover:text-white rounded">
            <LogOut size={18} />
          </button>
        )}
        <button
          onClick={toggleSidebar}
          className="w-full flex items-center justify-center p-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg"
        >
          {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>
    </aside>
  )
}
