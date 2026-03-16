import { Outlet } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { useUIStore } from '../../stores/uiStore'

export default function Layout() {
  const { sidebarCollapsed } = useUIStore()

  return (
    <div className="min-h-screen bg-surface-50">
      <Sidebar />
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'ml-16' : 'ml-60'}`}>
        <TopBar />
        <main className="max-w-7xl mx-auto px-6 py-6">
          <Outlet />
        </main>
      </div>
      <Toaster
        position="bottom-right"
        toastOptions={{
          duration: 3000,
          style: { background: '#1e293b', color: '#fff', fontSize: '14px' },
        }}
      />
    </div>
  )
}
