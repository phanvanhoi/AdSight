import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Users, ExternalLink } from 'lucide-react'
import { getAdvertiserGroup, getAdvertiserAds } from '../api/advertisers'

const platformBadge: Record<string, string> = {
  meta: 'bg-blue-100 text-blue-700',
  tiktok: 'bg-gray-900 text-white',
  google: 'bg-red-100 text-red-700',
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

export default function AdvertiserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [platform, setPlatform] = useState('')
  const [page, setPage] = useState(1)

  const { data: group, isLoading: groupLoading } = useQuery({
    queryKey: ['advertiser-group', id],
    queryFn: () => getAdvertiserGroup(id!),
    enabled: !!id,
  })

  const { data: adsData, isLoading: adsLoading } = useQuery({
    queryKey: ['advertiser-ads', id, platform, page],
    queryFn: () => getAdvertiserAds(id!, { platform: platform || undefined, page, limit: 20 }),
    enabled: !!id,
  })

  if (groupLoading) {
    return <div className="text-center py-12 text-gray-400">Dang tai...</div>
  }

  if (!group) {
    return <div className="text-center py-12 text-gray-500">Khong tim thay nha quang cao</div>
  }

  const totalPages = adsData ? Math.ceil(adsData.total / 20) : 0
  const platforms = group.platform_ids ? Object.keys(group.platform_ids) : []

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link to="/advertisers" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft size={16} />
        Quay lai danh sach
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
            <p className="text-xs text-gray-500">Tong ads</p>
            <p className="text-lg font-semibold text-gray-900">{formatNumber(group.total_ads)}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Est. chi tieu</p>
            <p className="text-lg font-semibold text-gray-900">
              {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', notation: 'compact' }).format(group.total_estimated_spend)}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Nen tang</p>
            <p className="text-lg font-semibold text-gray-900">{platforms.length}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-500">Slug</p>
            <p className="text-sm font-mono text-gray-700 truncate">{group.slug}</p>
          </div>
        </div>

        {/* Categories */}
        {group.categories && Object.keys(group.categories).length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-gray-500 mb-2">Danh muc</p>
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
              Tat ca
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
          <div className="text-center py-8 text-gray-400">Dang tai...</div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium text-gray-500">Ad</th>
                  <th className="px-4 py-3 font-medium text-gray-500">Platform</th>
                  <th className="px-4 py-3 font-medium text-gray-500">Loai</th>
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
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400">Khong co ads</td>
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
