import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Check, MessageCircle, Unlink } from 'lucide-react'
import { Link } from 'react-router-dom'
import { getMe, updateSettings, createPortalSession, connectTelegram, disconnectTelegram } from '../api/billing'

export default function Settings() {
  const queryClient = useQueryClient()
  const { data: profile, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
  })

  const [fullName, setFullName] = useState('')
  const [nameSaved, setNameSaved] = useState(false)
  const pollRef = useRef<{ interval?: number; timeout?: number }>({})

  useEffect(() => {
    if (profile) setFullName(profile.full_name)
  }, [profile])

  useEffect(() => {
    return () => {
      if (pollRef.current.interval) clearInterval(pollRef.current.interval)
      if (pollRef.current.timeout) clearTimeout(pollRef.current.timeout)
    }
  }, [])

  const updateMut = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })

  const handleSaveName = () => {
    updateMut.mutate({ full_name: fullName }, {
      onSuccess: () => {
        setNameSaved(true)
        setTimeout(() => setNameSaved(false), 2000)
      },
    })
  }

  const handleToggleEmail = (enabled: boolean) => {
    updateMut.mutate({ email_alerts_enabled: enabled })
  }

  const handleToggleTelegram = (enabled: boolean) => {
    updateMut.mutate({ telegram_enabled: enabled })
  }

  const [telegramLoading, setTelegramLoading] = useState(false)
  const handleConnectTelegram = async () => {
    setTelegramLoading(true)
    try {
      const { connect_url } = await connectTelegram()
      window.open(connect_url, '_blank')
      // Poll for connection status
      const interval = setInterval(() => {
        queryClient.invalidateQueries({ queryKey: ['me'] })
      }, 3000)
      const timeout = setTimeout(() => clearInterval(interval), 120000)
      pollRef.current = { interval: interval as unknown as number, timeout: timeout as unknown as number }
    } catch {
      // ignore
    } finally {
      setTelegramLoading(false)
    }
  }

  const disconnectMut = useMutation({
    mutationFn: disconnectTelegram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })

  const [portalLoading, setPortalLoading] = useState(false)
  const handleManage = async () => {
    setPortalLoading(true)
    try {
      const { portal_url } = await createPortalSession()
      window.location.href = portal_url
    } catch {
      setPortalLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="animate-pulse max-w-xl mx-auto space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/4" />
        <div className="h-40 bg-gray-200 rounded-xl" />
      </div>
    )
  }

  if (!profile) return null

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Cài đặt</h1>

      {/* Profile */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Thông tin cá nhân</h2>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <p className="text-sm text-gray-500">{profile.email}</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tên hiển thị</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={handleSaveName}
              disabled={fullName === profile.full_name || updateMut.isPending}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              {nameSaved ? <><Check size={14} /> Đã lưu</> : 'Lưu'}
            </button>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Thông báo</h2>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={profile.email_alerts_enabled}
            onChange={(e) => handleToggleEmail(e.target.checked)}
            className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <div>
            <p className="text-sm font-medium text-gray-700">Nhận email khi đối thủ chạy ads mới</p>
            <p className="text-xs text-gray-400">Gửi email thông báo mỗi khi competitor alert phát hiện quảng cáo mới</p>
          </div>
        </label>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={profile.daily_digest_enabled}
            onChange={(e) => updateMut.mutate({ daily_digest_enabled: e.target.checked })}
            className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <div>
            <p className="text-sm font-medium text-gray-700">Nhận email tóm tắt mỗi sáng (Daily Digest)</p>
            <p className="text-xs text-gray-400">Tổng hợp trending ads và cập nhật đối thủ mỗi 7:00 AM</p>
          </div>
        </label>

        <div className="border-t border-gray-100 pt-4">
          <div className="flex items-center gap-2 mb-3">
            <MessageCircle size={16} className="text-blue-500" />
            <h3 className="text-sm font-semibold text-gray-900">Telegram</h3>
          </div>

          {profile.telegram_connected ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-green-600 font-medium">Đã kết nối Telegram</p>
                <button
                  onClick={() => disconnectMut.mutate()}
                  disabled={disconnectMut.isPending}
                  className="px-3 py-1.5 text-xs border border-gray-200 rounded-lg text-gray-600 hover:bg-gray-50 flex items-center gap-1.5"
                >
                  <Unlink size={12} />
                  Ngắt kết nối
                </button>
              </div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.telegram_enabled}
                  onChange={(e) => handleToggleTelegram(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <div>
                  <p className="text-sm font-medium text-gray-700">Nhận thông báo qua Telegram</p>
                  <p className="text-xs text-gray-400">Gửi alert nhanh qua Telegram bot khi phát hiện quảng cáo mới</p>
                </div>
              </label>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-700">Kết nối Telegram để nhận alert nhanh hơn</p>
                <p className="text-xs text-gray-400">Phổ biến tại VN, nhận thông báo real-time</p>
              </div>
              <button
                onClick={handleConnectTelegram}
                disabled={telegramLoading}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 flex items-center gap-1.5"
              >
                {telegramLoading && <Loader2 size={14} className="animate-spin" />}
                Kết nối
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Subscription */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="font-semibold text-gray-900">Gói dịch vụ</h2>

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-700">
              Gói hiện tại: <span className="font-semibold capitalize">{profile.tier}</span>
            </p>
            {profile.subscription_status && (
              <p className="text-xs text-gray-400 capitalize">Trạng thái: {profile.subscription_status}</p>
            )}
          </div>
          {profile.tier === 'free' ? (
            <Link
              to="/pricing"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
            >
              Nâng cấp
            </Link>
          ) : (
            <button
              onClick={handleManage}
              disabled={portalLoading}
              className="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-1.5"
            >
              {portalLoading && <Loader2 size={14} className="animate-spin" />}
              Quản lý subscription
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
