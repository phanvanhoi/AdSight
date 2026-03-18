import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { getAdDetail } from '../api/ads'
import { useAuthStore } from '../stores/authStore'
import AIAnalysisPanel from '../components/ads/AIAnalysisPanel'

function formatRange(lower: number | null, upper: number | null, prefix = ''): string | null {
  if (lower == null && upper == null) return null
  if (lower != null && upper != null) return `${prefix}${lower.toLocaleString()} - ${prefix}${upper.toLocaleString()}`
  return `${prefix}${(lower ?? upper)!.toLocaleString()}`
}

export default function AdDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { isAuthenticated } = useAuthStore()

  const { data: ad, isLoading } = useQuery({
    queryKey: ['ad', id],
    queryFn: () => getAdDetail(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/4" />
        <div className="h-96 bg-gray-200 rounded-xl" />
      </div>
    )
  }

  if (!ad) {
    return <p className="text-center text-gray-500 py-16">Khong tim thay ad</p>
  }

  const hasEngagement = (ad.likes || 0) > 0 || (ad.comments || 0) > 0 || (ad.shares || 0) > 0
  const impressionsRange = formatRange(ad.impressions_lower, ad.impressions_upper)
  const spendRange = formatRange(ad.spend_lower, ad.spend_upper)

  return (
    <div className="space-y-6">
      <Link to="/search" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft size={16} />
        Quay lai ket qua tim kiem
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left — 2/3 */}
        <div className="lg:col-span-2 space-y-4">
          {/* Media card */}
          <div className="bg-white rounded-xl border border-gray-100 overflow-hidden shadow-card">
            <div className="aspect-video bg-gray-100">
              {ad.thumbnail_url?.includes('/ads/archive/render_ad') ? (
                <a
                  href={ad.thumbnail_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100 text-blue-600 hover:from-blue-100 hover:to-blue-200 transition-colors"
                >
                  <svg className="w-10 h-10 mb-3 opacity-60" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15H8v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3v3h-3v6.95c5.05-.5 9-4.76 9-9.95z" />
                  </svg>
                  <span className="text-sm font-semibold">Xem quảng cáo trên Facebook</span>
                  <span className="text-xs text-blue-400 mt-1">Nhấn để mở trong tab mới</span>
                </a>
              ) : ad.thumbnail_url ? (
                <img src={ad.thumbnail_url} alt={ad.headline || 'Ad'} className="w-full h-full object-contain" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">Chưa có preview</div>
              )}
            </div>
            <div className="p-6 space-y-4">
              {/* Platform + Status badges */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2.5 py-1 bg-primary-50 text-primary-700 text-xs font-semibold rounded-md">{ad.platform}</span>
                <span className="px-2.5 py-1 bg-gray-100 text-gray-600 text-xs rounded-md">{ad.ad_type}</span>
                {ad.is_active && <span className="px-2.5 py-1 bg-green-50 text-green-700 text-xs font-semibold rounded-md">Active</span>}
                {ad.is_hot && <span className="px-2.5 py-1 bg-red-50 text-red-600 text-xs font-semibold rounded-md">Hot Ad</span>}
                {ad.cta_type && <span className="px-2.5 py-1 bg-orange-50 text-orange-700 text-xs rounded-md">{ad.cta_type}</span>}
                {ad.language && <span className="px-2.5 py-1 bg-blue-50 text-blue-600 text-xs rounded-md">{ad.language.toUpperCase()}</span>}
              </div>

              {/* Headline */}
              {ad.headline && <h1 className="text-xl font-bold text-gray-900">{ad.headline}</h1>}

              {/* Body */}
              {ad.body_text && <p className="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed">{ad.body_text}</p>}

              {/* Metrics row */}
              <div className={`grid ${hasEngagement ? 'grid-cols-4' : 'grid-cols-3'} gap-4 py-4 border-t border-gray-100`}>
                {hasEngagement ? (
                  <>
                    <div className="text-center">
                      <p className="text-lg font-bold text-gray-900">{(ad.likes || 0).toLocaleString()}</p>
                      <p className="text-xs text-gray-400">Likes</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold text-gray-900">{(ad.comments || 0).toLocaleString()}</p>
                      <p className="text-xs text-gray-400">Comments</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold text-gray-900">{(ad.shares || 0).toLocaleString()}</p>
                      <p className="text-xs text-gray-400">Shares</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="text-center">
                      <p className="text-lg font-bold text-gray-900">{ad.viral_score != null ? ad.viral_score.toFixed(0) : '-'}</p>
                      <p className="text-xs text-gray-400">Viral Score</p>
                    </div>
                    <div className="text-center">
                      <p className="text-lg font-bold text-gray-900">{ad.collection_count || 1}</p>
                      <p className="text-xs text-gray-400">Thu thap</p>
                    </div>
                  </>
                )}
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900">
                    {ad.first_seen && ad.last_seen
                      ? `${Math.max(1, Math.ceil((new Date(ad.last_seen).getTime() - new Date(ad.first_seen).getTime()) / 86400000))}d`
                      : '-'}
                  </p>
                  <p className="text-xs text-gray-400">Running</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right sidebar — 1/3 */}
        <div className="space-y-4">
          {/* Advertiser card */}
          {ad.advertiser_name && (
            <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Nha quang cao</h3>
              <p className="font-semibold text-gray-900">{ad.advertiser_name}</p>
              {ad.advertiser_page_url && (
                <a href={ad.advertiser_page_url} target="_blank" rel="noopener noreferrer"
                   className="text-xs text-primary-600 hover:underline mt-1 block">
                  Xem trang quang cao
                </a>
              )}
            </div>
          )}

          {/* Targeting card */}
          {(ad.target_gender || ad.target_countries?.length > 0 || impressionsRange || spendRange) && (
            <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Targeting & Chi tieu</h3>
              <div className="space-y-2 text-sm">
                {ad.target_gender && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Gioi tinh</span>
                    <span className="font-medium">{ad.target_gender}</span>
                  </div>
                )}
                {ad.target_countries?.length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Quoc gia</span>
                    <span className="font-medium">{ad.target_countries.join(', ')}</span>
                  </div>
                )}
                {impressionsRange && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Impressions</span>
                    <span className="font-medium">{impressionsRange}</span>
                  </div>
                )}
                {spendRange && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Chi tieu (VND)</span>
                    <span className="font-medium">{spendRange}</span>
                  </div>
                )}
                {ad.language && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Ngon ngu</span>
                    <span className="font-medium">{ad.language.toUpperCase()}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Enrichment card — category, offers, triggers */}
          {(ad.category_l1 || ad.detected_offers?.length) && (
            <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Phan tich AI</h3>
              <div className="flex flex-wrap gap-1.5">
                {ad.category_l1 && <span className="px-2 py-1 bg-primary-50 text-primary-700 text-xs rounded-md">{ad.category_l1}</span>}
                {ad.category_l2 && <span className="px-2 py-1 bg-primary-50 text-primary-700 text-xs rounded-md">{ad.category_l2}</span>}
                {ad.detected_offers?.map((o: string) => (
                  <span key={o} className="px-2 py-1 bg-orange-50 text-orange-700 text-xs rounded-md">{o}</span>
                ))}
                {ad.emotional_triggers?.map((t: string) => (
                  <span key={t} className="px-2 py-1 bg-violet-50 text-violet-700 text-xs rounded-md">{t}</span>
                ))}
              </div>
              {ad.target_audience_guess && (
                <p className="text-xs text-gray-500 mt-2">Doi tuong: {ad.target_audience_guess}</p>
              )}
            </div>
          )}

          {/* Performance card */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Hieu suat</h3>
            <div className="space-y-2.5 text-sm">
              {ad.viral_score != null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Viral Score</span>
                  <span className="font-medium">{ad.viral_score.toFixed(0)}/100</span>
                </div>
              )}
              {ad.estimated_daily_spend != null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Chi tieu/ngay</span>
                  <span className="font-medium">${ad.estimated_daily_spend.toFixed(0)}</span>
                </div>
              )}
              {ad.engagement_rate != null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Engagement Rate</span>
                  <span className="font-medium">{ad.engagement_rate.toFixed(2)}%</span>
                </div>
              )}
              {ad.collection_count > 1 && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Lan thu thap</span>
                  <span className="font-medium">{ad.collection_count}</span>
                </div>
              )}
              {ad.is_hot && (
                <div className="mt-2">
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-red-50 text-red-600 text-xs rounded-md font-semibold">
                    Hot Ad
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Landing page card */}
          {ad.landing_page_url && (
            <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Landing Page</h3>
              <a href={ad.landing_page_url} target="_blank" rel="noopener noreferrer"
                 className="text-sm text-primary-600 hover:underline truncate block">
                {ad.landing_page_url}
              </a>
            </div>
          )}

          {/* Dates card */}
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-card">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Thoi gian</h3>
            <div className="space-y-2 text-sm text-gray-600">
              {ad.first_seen && <p>Phat hien: {new Date(ad.first_seen).toLocaleDateString('vi-VN')}</p>}
              {ad.last_seen && <p>Lan cuoi: {new Date(ad.last_seen).toLocaleDateString('vi-VN')}</p>}
            </div>
          </div>

          {/* AI Analysis */}
          {isAuthenticated && <AIAnalysisPanel adId={ad.id} />}
        </div>
      </div>
    </div>
  )
}
