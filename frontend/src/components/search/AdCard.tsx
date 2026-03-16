import { Link } from 'react-router-dom'
import { Heart, MessageCircle, Share2, Clock } from 'lucide-react'
import type { AdSummary } from '../../types/ad'

interface Props {
  ad: AdSummary
}

const platformColors: Record<string, string> = {
  meta: 'bg-blue-500/80 text-white',
  tiktok: 'bg-gray-900/80 text-white',
  google: 'bg-red-500/80 text-white',
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

export default function AdCard({ ad }: Props) {
  return (
    <Link
      to={`/ads/${ad.id}`}
      className="bg-white rounded-xl border border-gray-100 overflow-hidden hover:shadow-soft transition-all duration-200 group"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-100 overflow-hidden">
        {ad.thumbnail_url ? (
          <>
            <img
              src={ad.thumbnail_url}
              alt={ad.headline || 'Ad'}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm bg-gray-50">
            Chưa có preview
          </div>
        )}
        {/* Platform badge */}
        <span
          className={`absolute top-2.5 left-2.5 px-2 py-1 rounded-md text-xs font-semibold backdrop-blur-sm ${
            platformColors[ad.platform] || 'bg-white/80 text-gray-700'
          }`}
        >
          {ad.platform === 'meta' ? 'Facebook' : ad.platform === 'tiktok' ? 'TikTok' : ad.platform}
        </span>
        {/* Active badge */}
        {ad.is_active && (
          <span className="absolute top-2.5 right-2.5 flex items-center gap-1 px-2 py-1 rounded-md bg-green-500/90 backdrop-blur-sm text-white text-xs font-medium">
            <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
            Active
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-3 space-y-2">
        {/* Advertiser */}
        {ad.advertiser_name && (
          <p className="text-xs text-gray-500 font-medium truncate">{ad.advertiser_name}</p>
        )}

        {/* Headline */}
        {ad.headline && (
          <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 group-hover:text-primary-600">
            {ad.headline}
          </h3>
        )}

        {/* Body */}
        {ad.body_text && (
          <p className="text-xs text-gray-500 line-clamp-2">{ad.body_text}</p>
        )}

        {/* Metrics */}
        <div className="flex items-center gap-3 pt-1 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <Heart size={12} /> {formatNumber(ad.likes)}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle size={12} /> {formatNumber(ad.comments)}
          </span>
          <span className="flex items-center gap-1">
            <Share2 size={12} /> {formatNumber(ad.shares)}
          </span>
          <span className="flex items-center gap-1 ml-auto">
            <Clock size={12} /> {ad.days_running}d
          </span>
        </div>
      </div>
    </Link>
  )
}
