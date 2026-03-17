import { useState } from 'react'
import { ChevronUp, ChevronDown, X } from 'lucide-react'
import type { Facets } from '../../types/ad'

export interface FilterState {
  platform: string
  country: string
  ad_type: string
  category_l1: string
  date_from: string
  date_to: string
  min_spend: string
  max_spend: string
  min_viral_score: string
  min_likes: string
  is_hot: boolean
  has_discount: boolean
  sort: string
}

export const defaultFilters: FilterState = {
  platform: '',
  country: 'VN',
  ad_type: '',
  category_l1: '',
  date_from: '',
  date_to: '',
  min_spend: '',
  max_spend: '',
  min_viral_score: '',
  min_likes: '',
  is_hot: false,
  has_discount: false,
  sort: 'newest',
}

interface Props {
  filters: FilterState
  onChange: (key: string, value: string | boolean) => void
  onReset: () => void
  facets?: Facets
}

const PLATFORMS = [
  { value: 'meta', label: 'Meta' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'google', label: 'Google' },
]

export default function FilterPanel({ filters, onChange, onReset, facets }: Props) {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  // Count active filters (excluding defaults)
  const activeCount = [
    filters.platform,
    filters.country !== 'VN' ? filters.country : '',
    filters.ad_type,
    filters.category_l1,
    filters.date_from,
    filters.date_to,
    filters.min_spend,
    filters.max_spend,
    filters.min_viral_score,
    filters.min_likes,
    filters.is_hot,
    filters.has_discount,
  ].filter(Boolean).length

  const togglePlatform = (platform: string) => {
    const current = filters.platform ? filters.platform.split(',') : []
    const idx = current.indexOf(platform)
    if (idx >= 0) {
      current.splice(idx, 1)
    } else {
      current.push(platform)
    }
    onChange('platform', current.filter(Boolean).join(','))
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50"
      >
        <span className="font-semibold text-gray-900 text-sm">
          Bộ lọc{activeCount > 0 && ` (${activeCount})`}
        </span>
        {collapsed ? <ChevronDown size={16} className="text-gray-400" /> : <ChevronUp size={16} className="text-gray-400" />}
      </button>

      {!collapsed && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-100">
          {/* Platform toggle buttons */}
          <div className="pt-3">
            <label className="text-xs font-medium text-gray-500 uppercase">Nền tảng</label>
            <div className="flex gap-1.5 mt-1.5">
              {PLATFORMS.map((p) => {
                const active = filters.platform.split(',').includes(p.value)
                return (
                  <button
                    key={p.value}
                    onClick={() => togglePlatform(p.value)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                      active
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {p.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Country + Ad Type — 2 columns */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">Quốc gia</label>
              <select
                value={filters.country}
                onChange={(e) => onChange('country', e.target.value)}
                className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
              >
                <option value="">Tất cả</option>
                <option value="VN">Việt Nam</option>
                <option value="TH">Thái Lan</option>
                <option value="ID">Indonesia</option>
                <option value="PH">Philippines</option>
                <option value="MY">Malaysia</option>
                <option value="SG">Singapore</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">Loại ads</label>
              <select
                value={filters.ad_type}
                onChange={(e) => onChange('ad_type', e.target.value)}
                className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
              >
                <option value="">Tất cả</option>
                <option value="image">Hình ảnh</option>
                <option value="video">Video</option>
                <option value="carousel">Carousel</option>
              </select>
            </div>
          </div>

          {/* Category L1 */}
          {facets?.categories_l1 && Object.keys(facets.categories_l1).length > 0 && (
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">Ngành hàng</label>
              <select
                value={filters.category_l1}
                onChange={(e) => onChange('category_l1', e.target.value)}
                className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
              >
                <option value="">Tất cả</option>
                {Object.entries(facets.categories_l1)
                  .sort((a, b) => b[1] - a[1])
                  .map(([name, count]) => (
                    <option key={name} value={name}>
                      {name} ({count})
                    </option>
                  ))}
              </select>
            </div>
          )}

          {/* Date range */}
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase">Thời gian</label>
            <div className="grid grid-cols-2 gap-2 mt-1">
              <input
                type="date"
                value={filters.date_from}
                onChange={(e) => onChange('date_from', e.target.value)}
                className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
              />
              <input
                type="date"
                value={filters.date_to}
                onChange={(e) => onChange('date_to', e.target.value)}
                className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
              />
            </div>
          </div>

          {/* Advanced section toggle */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full text-xs font-medium text-primary-600 hover:text-primary-700 py-1"
          >
            {showAdvanced ? 'Ẩn bớt' : 'Hiện thêm bộ lọc nâng cao'}
          </button>

          {showAdvanced && (
            <div className="space-y-4 pt-1">
              {/* Spend range */}
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Chi tiêu ($/ngày)</label>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  <input
                    type="number"
                    value={filters.min_spend}
                    onChange={(e) => onChange('min_spend', e.target.value)}
                    placeholder="Min"
                    min={0}
                    className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                  />
                  <input
                    type="number"
                    value={filters.max_spend}
                    onChange={(e) => onChange('max_spend', e.target.value)}
                    placeholder="Max"
                    min={0}
                    className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                  />
                </div>
              </div>

              {/* Viral score */}
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Viral score tối thiểu</label>
                <input
                  type="number"
                  value={filters.min_viral_score}
                  onChange={(e) => onChange('min_viral_score', e.target.value)}
                  placeholder="0"
                  min={0}
                  step={0.1}
                  className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                />
              </div>

              {/* Min likes */}
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Likes tối thiểu</label>
                <input
                  type="number"
                  value={filters.min_likes}
                  onChange={(e) => onChange('min_likes', e.target.value)}
                  placeholder="0"
                  min={0}
                  className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
                />
              </div>

              {/* Checkboxes */}
              <div className="grid grid-cols-2 gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.is_hot}
                    onChange={(e) => onChange('is_hot', e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">Chỉ ads Hot</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={filters.has_discount}
                    onChange={(e) => onChange('has_discount', e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">Có khuyến mãi</span>
                </label>
              </div>
            </div>
          )}

          {/* Sort */}
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase">Sắp xếp</label>
            <select
              value={filters.sort}
              onChange={(e) => onChange('sort', e.target.value)}
              className="mt-1 w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm"
            >
              <option value="relevance">Liên quan nhất</option>
              <option value="newest">Mới nhất</option>
              <option value="engagement">Tương tác cao</option>
              <option value="viral">Viral score cao</option>
            </select>
          </div>

          {/* Reset */}
          {activeCount > 0 && (
            <button
              onClick={onReset}
              className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-sm text-gray-600 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100"
            >
              <X size={14} />
              Xóa bộ lọc
            </button>
          )}
        </div>
      )}
    </div>
  )
}
