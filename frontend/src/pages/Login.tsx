import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../api/auth'
import { useAuthStore } from '../stores/authStore'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const authLogin = useAuthStore((s) => s.login)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const tokens = await login(email, password)
      // Decode user from token (basic)
      const payload = JSON.parse(atob(tokens.access_token.split('.')[1]))
      authLogin(
        { id: payload.sub, email, full_name: email.split('@')[0], tier: 'free' },
        tokens.access_token,
        tokens.refresh_token,
      )
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Dang nhap that bai')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold">AD</span>
            </div>
            <span className="text-2xl font-bold text-gray-900">AdSight</span>
          </Link>
          <p className="text-gray-500 mt-2">Dang nhap de tiep tuc</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">{error}</div>
          )}

          <div>
            <label className="text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="email@example.com"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Mat khau</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
          >
            {loading ? 'Dang xu ly...' : 'Dang nhap'}
          </button>

          <p className="text-center text-sm text-gray-500">
            Chua co tai khoan?{' '}
            <Link to="/register" className="text-primary-600 hover:underline font-medium">
              Dang ky mien phi
            </Link>
          </p>
        </form>
      </div>
    </div>
  )
}
