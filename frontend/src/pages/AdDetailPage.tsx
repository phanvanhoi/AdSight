import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Heart, MessageCircle, Share2, Clock, ExternalLink, Calendar } from 'lucide-react'
import { getAdDetail } from '../api/ads'

export default function AdDetailPage() {
  const { id } = useParams<{ id: string }>()

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
    return <p className="text-center text-gray-500 py-16">Ad not found</p>
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Link to="/search" className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft size={16} />
        Quay lai ket qua tim kiem
      </Link>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {/* Media */}
        <div className="aspect-video bg-gray-100">
          {ad.thumbnail_url ? (
            <img src={ad.thumbnail_url} alt={ad.headline} className="w-full h-full object-contain" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">No preview</div>
          )}
        </div>

        {/* Info */}
        <div className="p-6 space-y-4">
          {/* Platform + Status */}
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-primary-100 text-primary-700 text-xs font-semibold rounded">
              {ad.platform}
            </span>
            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
              {ad.ad_type}
            </span>
            {ad.is_active && (
              <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded">
                Active
              </span>
            )}
            {ad.cta_type && (
              <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded">
                {ad.cta_type}
              </span>
            )}
          </div>

          {/* Advertiser */}
          {ad.advertiser_name && (
            <div>
              <p className="text-xs text-gray-400 uppercase font-medium">Advertiser</p>
              <p className="text-sm font-semibold text-gray-900">{ad.advertiser_name}</p>
            </div>
          )}

          {/* Headline */}
          {ad.headline && (
            <div>
              <p className="text-xs text-gray-400 uppercase font-medium">Headline</p>
              <h1 className="text-lg font-bold text-gray-900">{ad.headline}</h1>
            </div>
          )}

          {/* Body */}
          {ad.body_text && (
            <div>
              <p className="text-xs text-gray-400 uppercase font-medium">Ad Copy</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{ad.body_text}</p>
            </div>
          )}

          {/* Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-4 border-t border-gray-100">
            <div className="text-center">
              <Heart className="mx-auto text-red-400 mb-1" size={20} />
              <p className="text-lg font-bold text-gray-900">{(ad.likes || 0).toLocaleString()}</p>
              <p className="text-xs text-gray-400">Likes</p>
            </div>
            <div className="text-center">
              <MessageCircle className="mx-auto text-blue-400 mb-1" size={20} />
              <p className="text-lg font-bold text-gray-900">{(ad.comments || 0).toLocaleString()}</p>
              <p className="text-xs text-gray-400">Comments</p>
            </div>
            <div className="text-center">
              <Share2 className="mx-auto text-green-400 mb-1" size={20} />
              <p className="text-lg font-bold text-gray-900">{(ad.shares || 0).toLocaleString()}</p>
              <p className="text-xs text-gray-400">Shares</p>
            </div>
            <div className="text-center">
              <Clock className="mx-auto text-purple-400 mb-1" size={20} />
              <p className="text-lg font-bold text-gray-900">
                {ad.first_seen && ad.last_seen
                  ? `${Math.max(1, Math.ceil((new Date(ad.last_seen).getTime() - new Date(ad.first_seen).getTime()) / 86400000))}d`
                  : '-'}
              </p>
              <p className="text-xs text-gray-400">Running</p>
            </div>
          </div>

          {/* Dates & Targeting */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-4 border-t border-gray-100 text-sm">
            {ad.first_seen && (
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar size={14} />
                <span>First seen: {new Date(ad.first_seen).toLocaleDateString('vi-VN')}</span>
              </div>
            )}
            {ad.last_seen && (
              <div className="flex items-center gap-2 text-gray-600">
                <Calendar size={14} />
                <span>Last seen: {new Date(ad.last_seen).toLocaleDateString('vi-VN')}</span>
              </div>
            )}
            {ad.target_countries?.length > 0 && (
              <div className="text-gray-600">
                Countries: {ad.target_countries.join(', ')}
              </div>
            )}
            {ad.landing_page_url && (
              <a
                href={ad.landing_page_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-primary-600 hover:underline"
              >
                <ExternalLink size={14} />
                Landing page
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
