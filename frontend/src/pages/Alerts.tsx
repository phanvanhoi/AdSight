import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Pause, Play, Radar, X, AlertCircle } from 'lucide-react'
import { Link } from 'react-router-dom'
import { listAlerts, createAlert, updateAlert, deleteAlert } from '../api/alerts'
import { useAuthStore } from '../stores/authStore'
import type { CompetitorAlert } from '../api/alerts'

const ALERT_TYPE_LABELS: Record<string, string> = {
  advertiser_name: 'Tên nhà quảng cáo',
  advertiser_group: 'Nhóm nhà quảng cáo',
  keyword: 'Từ khóa',
}

const PLATFORM_OPTIONS = ['meta', 'tiktok', 'google']

function timeAgo(dateStr: string | null) {
  if (!dateStr) return 'Chưa check'
  const diff = Date.now() - new Date(dateStr).getTime()
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return 'Vừa xong'
  if (hours < 24) return `${hours}h trước`
  return `${Math.floor(hours / 24)}d trước`
}

export default function Alerts() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', alert_type: 'advertiser_name', match_value: '', platforms: [] as string[] })
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const { data: alerts = [], isLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: listAlerts,
  })

  const createMut = useMutation({
    mutationFn: () => createAlert({
      name: form.name,
      alert_type: form.alert_type,
      match_value: form.match_value,
      platforms: form.platforms.length > 0 ? form.platforms : undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setShowCreate(false)
      setForm({ name: '', alert_type: 'advertiser_name', match_value: '', platforms: [] })
    },
  })

  const toggleMut = useMutation({
    mutationFn: (alert: CompetitorAlert) => updateAlert(alert.id, { is_active: !alert.is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const deleteMut = useMutation({
    mutationFn: deleteAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      setDeleteConfirm(null)
    },
  })

  const isFree = user?.tier === 'free'

  // Free tier gate
  if (isFree) {
    return (
      <div className="max-w-2xl mx-auto text-center py-16 space-y-4">
        <Radar size={48} className="mx-auto text-gray-300" />
        <h2 className="text-xl font-bold text-gray-900">Theo dõi đối thủ</h2>
        <p className="text-gray-500">
          Tự động phát hiện quảng cáo mới của đối thủ. Tính năng này chỉ có trong gói Pro trở lên.
        </p>
        <Link
          to="/pricing"
          className="inline-block px-6 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          Nâng cấp ngay
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Theo dõi đối thủ</h1>
          <p className="text-sm text-gray-500 mt-1">
            {alerts.length} alerts
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          <Plus size={16} />
          Tạo alert mới
        </button>
      </div>

      {/* Alert list */}
      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Radar size={40} className="mx-auto mb-3" />
          <p>Chưa có alert nào. Tạo alert đầu tiên để bắt đầu theo dõi đối thủ.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white rounded-xl border p-5 ${
                alert.is_active ? 'border-gray-200' : 'border-gray-100 opacity-60'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900">{alert.name}</h3>
                    <span
                      className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        alert.is_active
                          ? 'bg-green-50 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {alert.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {ALERT_TYPE_LABELS[alert.alert_type] || alert.alert_type}: <span className="font-medium text-gray-700">{alert.match_value}</span>
                  </p>
                  <div className="flex items-center gap-4 text-xs text-gray-400">
                    {alert.platforms && (
                      <span>Platforms: {alert.platforms.join(', ')}</span>
                    )}
                    <span>Tìm thấy: {alert.total_found} ads</span>
                    <span>Lần check: {timeAgo(alert.last_checked)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => toggleMut.mutate(alert)}
                    className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-50"
                    title={alert.is_active ? 'Tạm dừng' : 'Kích hoạt'}
                  >
                    {alert.is_active ? <Pause size={16} /> : <Play size={16} />}
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(alert.id)}
                    className="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50"
                    title="Xóa"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 shadow-lg max-w-md w-full space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Tạo alert mới</h3>
              <button onClick={() => setShowCreate(false)} className="p-1 text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>

            {createMut.error && (
              <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-3 rounded-lg">
                <AlertCircle size={16} />
                {(createMut.error as Error).message || 'Không thể tạo alert'}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tên alert</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="VD: Shopee Ads"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Loại</label>
                <select
                  value={form.alert_type}
                  onChange={(e) => setForm({ ...form, alert_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="advertiser_name">Tên nhà quảng cáo</option>
                  <option value="advertiser_group">Nhóm nhà quảng cáo</option>
                  <option value="keyword">Từ khóa</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {form.alert_type === 'keyword' ? 'Từ khóa' : 'Tên / ID'}
                </label>
                <input
                  type="text"
                  value={form.match_value}
                  onChange={(e) => setForm({ ...form, match_value: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder={form.alert_type === 'keyword' ? 'VD: giảm giá' : 'VD: Shopee'}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nền tảng (tuỳ chọn)</label>
                <div className="flex gap-3">
                  {PLATFORM_OPTIONS.map((p) => (
                    <label key={p} className="flex items-center gap-1.5 text-sm">
                      <input
                        type="checkbox"
                        checked={form.platforms.includes(p)}
                        onChange={(e) => {
                          setForm({
                            ...form,
                            platforms: e.target.checked
                              ? [...form.platforms, p]
                              : form.platforms.filter((x) => x !== p),
                          })
                        }}
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      {p.charAt(0).toUpperCase() + p.slice(1)}
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={() => createMut.mutate()}
              disabled={!form.name || !form.match_value || createMut.isPending}
              className="w-full py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createMut.isPending ? 'Đang tạo...' : 'Tạo alert'}
            </button>
          </div>
        </div>
      )}

      {/* Delete confirm modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 shadow-lg max-w-sm w-full space-y-4">
            <h3 className="font-semibold text-gray-900">Xác nhận xóa</h3>
            <p className="text-sm text-gray-500">Bạn có chắc muốn xóa alert này? Không thể hoàn tác.</p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                onClick={() => deleteMut.mutate(deleteConfirm)}
                disabled={deleteMut.isPending}
                className="flex-1 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMut.isPending ? 'Đang xóa...' : 'Xóa'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
