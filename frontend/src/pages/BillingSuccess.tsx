import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle } from 'lucide-react'
import { getMe } from '../api/billing'
import { useAuthStore } from '../stores/authStore'

export default function BillingSuccess() {
  const { data: profile } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  })

  const login = useAuthStore((s) => s.login)

  // Update local user data with new tier
  useEffect(() => {
    if (profile) {
      const accessToken = localStorage.getItem('access_token')
      const refreshToken = localStorage.getItem('refresh_token')
      if (accessToken && refreshToken) {
        login(
          {
            id: profile.id,
            email: profile.email,
            full_name: profile.full_name,
            tier: profile.tier,
          },
          accessToken,
          refreshToken,
        )
      }
    }
  }, [profile, login])

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center space-y-4">
        <CheckCircle size={64} className="text-green-500 mx-auto" />
        <h1 className="text-2xl font-bold text-gray-900">Nâng cấp thành công!</h1>
        {profile && (
          <p className="text-gray-600">
            Bạn đang sử dụng gói <span className="font-semibold capitalize">{profile.tier}</span>
          </p>
        )}
        <Link
          to="/dashboard"
          className="inline-block px-6 py-2.5 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
        >
          Bắt đầu sử dụng
        </Link>
      </div>
    </div>
  )
}
