import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Users, TrendingUp, Activity } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell,
} from 'recharts'
import { getAdvertiserGroup, getAdvertiserAds, getAdvertiserAnalytics } from '../api/advertisers'

const platformBadge: Record<string, string> = {
  meta: 'bg-blue-100 text-blue-700',
  tiktok: 'bg-gray-900 text-white',
  google: 'bg-red-100 text-red-700',
}

const PLATFORM_COLORS: Record<string, string> = {
  meta: '#3b82f6',
  tiktok: '#111827',
  google: '#ef4444',
}

const AD_TYPE_COLORS = ['#6366f1', '#d946ef', '#f59e0b', '#10b981']

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

function formatCurrency(n: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1 }).format(n)
}

export default function AdvertiserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [platform, setPlatform] = useState('')
  const [page, setPage] = useState(1)

  const { data: group, isLoading: groupLoading } = useQuery({
    queryKey: ['advertiser-group', id],
    queryFn: () => getAdvertiserGroup(id!),
    enabled: !!id,
  })

  const { data: analytics } = useQuery({
    queryKey: ['advertiser-analytics', id],
    queryFn: () => getAdvertiserAnalytics(id!),
    enabled: !!id,
  })

  const { data: adsData, isLoading: adsLoading } = useQuery({
    queryKey: ['advertiser-ads', id, platform, page],
    queryFn: () => getAdvertiserAds(id!, { platform: platform || undefined, page, limit: 20 }),
    enabled: !!id,
  })

  if (groupLoading) {
    return <div className="text-center py-12 text-gray-400">Đang tải...</div>
  }

  if (!group) {
    return <div className="text-center py-12 text-gray-500">Không tìm thấy nhà quảng cáo</div>
  }

  const totalPages = adsData ? Math.ceil(adsData.total / 20) : 0
  const platforms = group.platform_ids ? Object.keys(group.platform_ids) : []

  // Pie chart data
  const platformPieData = analytics
    ? Object.entries(analytics.platform_breakdown).map(([name, data]) => ({ name, value: data.count }))
    : []
  const adTypePieData = analytics
    ? Object.entries(analytics.ad_type_breakdown).map(([name, data]) => ({ name, value: data }))
    : []

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link to="/advertisers" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft size={16} />
        Quay lại danh sách
      </Link>

      {/* Header card */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Users size={24} />
              {group.name}
            </h1>
            <div className="flex gap-2 mt-3">
              {platforms.map((plat) => (
                <span
                  key={plat}
                  className={`px-2.5 py-1 rounded text-xs font-medium ${
                    platformBadge[plat] || 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {plat === 'meta' ? 'Facebook/IG' : plat}
                </span>
              ))}
            </div>
          </div>
          {group.is_verified && (
            <span className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-lg font-medium">Verified</span>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Tổng ads</p>
            <p className="text-lg font-semibold text-gray-900">{formatNumber(group.total_ads)}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Est. chi tiêu</p>
            <p className="text-lg font-semibold text-gray-900">{formatCurrency(group.total_estimated_spend)}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Đang chạy</p>
            <p className="text-lg font-semibold text-gray-900">{analytics?.total_active_ads ?? '—'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Ads đầu tiên</p>
            <p className="text-lg font-semibold text-gray-900">{analytics?.first_ad_date ?? '—'}</p>
          </div>
        </div>

        {/* Extra stats row */}
        {analytics && (analytics.avg_engagement_rate > 0 || analytics.avg_viral_score > 0) && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
            {analytics.avg_engagement_rate > 0 && (
              <div className="bg-gray-50 rounded-lg p-3 flex items-center gap-2">
                <Activity size={14} className="text-green-500" />
                <div>
                  <p className="text-xs text-gray-500">Avg Engagement</p>
                  <p className="text-lg font-semibold text-gray-900">{analytics.avg_engagement_rate}%</p>
                </div>
              </div>
            )}
            {analytics.avg_viral_score > 0 && (
              <div className="bg-gray-50 rounded-lg p-3 flex items-center gap-2">
                <TrendingUp size={14} className="text-red-500" />
                <div>
                  <p className="text-xs text-gray-500">Avg Viral Score</p>
                  <p className="text-lg font-semibold text-gray-900">{analytics.avg_viral_score}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Categories */}
        {group.categories && Object.keys(group.categories).length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-2">Danh mục</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(group.categories).map(([cat, count]) => (
                <span key={cat} className="text-xs bg-primary-50 text-primary-700 px-2 py-1 rounded">
                  {cat} ({count})
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Ads Timeline Chart */}
      {analytics && analytics.ads_timeline.length > 1 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Ads Timeline</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={analytics.ads_timeline}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Breakdown charts row */}
      {analytics && (platformPieData.length > 0 || adTypePieData.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Platform breakdown */}
          {platformPieData.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="text-sm font-semibold text-gray-900 mb-4">Nền tảng</h2>
              <div className="flex items-center gap-6">
                <ResponsiveContainer width={140} height={140}>
                  <PieChart>
                    <Pie data={platformPieData} dataKey="value" cx="50%" cy="50%" outerRadius={60} strokeWidth={2}>
                      {platformPieData.map((entry) => (
                        <Cell key={entry.name} fill={PLATFORM_COLORS[entry.name] || '#9ca3af'} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2">
                  {Object.entries(analytics.platform_breakdown).map(([plat, data]) => (
                    <div key={plat} className="flex items-center gap-2 text-sm">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: PLATFORM_COLORS[plat] || '#9ca3af' }} />
                      <span className="text-gray-700 capitalize">{plat}</span>
                      <span className="text-gray-400">{data.count} ads</span>
                      <span className="text-gray-400">({formatCurrency(data.total_spend)})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Ad type breakdown */}
          {adTypePieData.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-6">
              <h2 className="text-sm font-semibold text-gray-900 mb-4">Loại quảng cáo</h2>
              <div className="flex items-center gap-6">
                <ResponsiveContainer width={140} height={140}>
                  <PieChart>
                    <Pie data={adTypePieData} dataKey="value" cx="50%" cy="50%" outerRadius={60} strokeWidth={2}>
                      {adTypePieData.map((_, i) => (
                        <Cell key={i} fill={AD_TYPE_COLORS[i % AD_TYPE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-2">
                  {adTypePieData.map((entry, i) => (
                    <div key={entry.name} className="flex items-center gap-2 text-sm">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: AD_TYPE_COLORS[i % AD_TYPE_COLORS.length] }} />
                      <span className="text-gray-700 capitalize">{entry.name}</span>
                      <span className="text-gray-400">{entry.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top Performing Ads */}
      {analytics && analytics.top_ads.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Top Performing Ads</h2>
          <div className="space-y-2">
            {analytics.top_ads.map((ad) => (
              <div
                key={ad.id}
                onClick={() => navigate(`/ads/${ad.id}`)}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${platformBadge[ad.platform] || 'bg-gray-100 text-gray-600'}`}>
                    {ad.platform}
                  </span>
                  <span className="text-sm text-gray-900 truncate">{ad.headline || 'Untitled'}</span>
                </div>
                <div className="flex items-center gap-4 flex-shrink-0 ml-4">
                  <span className="text-sm text-gray-500">{formatNumber(ad.likes)} likes</span>
                  <span className={`text-sm font-semibold ${ad.viral_score >= 70 ? 'text-red-600' : ad.viral_score >= 40 ? 'text-yellow-600' : 'text-gray-500'}`}>
                    {ad.viral_score}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ads section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">
            Ads ({adsData?.total ?? 0})
          </h2>
          <div className="flex gap-2">
            <button
              onClick={() => { setPlatform(''); setPage(1) }}
              className={`px-3 py-1.5 text-xs rounded-lg font-medium ${
                !platform ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200'
              }`}
            >
              Tất cả
            </button>
            {platforms.map((plat) => (
              <button
                key={plat}
                onClick={() => { setPlatform(plat); setPage(1) }}
                className={`px-3 py-1.5 text-xs rounded-lg font-medium ${
                  platform === plat ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200'
                }`}
              >
                {plat === 'meta' ? 'Facebook' : plat}
              </button>
            ))}
          </div>
        </div>

        {adsLoading ? (
          <div className="text-center py-8 text-gray-400">Đang tải...</div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium text-gray-500">Ad</th>
                  <th className="px-4 py-3 font-medium text-gray-500">Platform</th>
                  <th className="px-4 py-3 font-medium text-gray-500">Loại</th>
                  <th className="px-4 py-3 font-medium text-gray-500 text-right">Likes</th>
                  <th className="px-4 py-3 font-medium text-gray-500 text-right">Viral</th>
                  <th className="px-4 py-3 font-medium text-gray-500">First seen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {adsData?.results.map((ad) => (
                  <tr key={ad.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link to={`/ads/${ad.id}`} className="text-primary-600 hover:underline font-medium line-clamp-1">
                        {ad.headline || ad.advertiser_name || 'Untitled'}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        platformBadge[ad.platform] || 'bg-gray-100 text-gray-600'
                      }`}>
                        {ad.platform}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{ad.ad_type}</td>
                    <td className="px-4 py-3 text-right">{formatNumber(ad.likes)}</td>
                    <td className="px-4 py-3 text-right">
                      {ad.viral_score != null ? (
                        <span className={`font-medium ${ad.viral_score >= 70 ? 'text-red-600' : ad.viral_score >= 40 ? 'text-yellow-600' : 'text-gray-500'}`}>
                          {ad.viral_score}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{ad.first_seen ?? '—'}</td>
                  </tr>
                ))}
                {adsData?.results.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400">Không có ads</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 pt-4">
            {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => i + 1).map((pg) => (
              <button
                key={pg}
                onClick={() => setPage(pg)}
                className={`px-3 py-1.5 text-sm rounded-lg ${
                  pg === page
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                {pg}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
