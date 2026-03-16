import { Search, Bell } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'

export default function TopBar() {
  const { user, isAuthenticated } = useAuthStore()

  return (
    <div className="h-14 border-b border-gray-200 bg-white flex items-center justify-between px-6">
      {/* Search shortcut */}
      <div className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer hover:text-gray-500">
        <Search size={16} />
        <span>Tìm kiếm nhanh...</span>
        <kbd className="hidden sm:inline px-1.5 py-0.5 bg-gray-100 rounded text-xs text-gray-500 border border-gray-200">Ctrl+K</kbd>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        <button className="relative p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        {isAuthenticated && user && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-sm font-semibold">
              {user.full_name?.charAt(0)?.toUpperCase()}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
