import { Link } from 'react-router-dom'
import { Heart, MessageCircle, Share2, Clock, Bookmark } from 'lucide-react'
import type { AdSummary } from '../../types/ad'

interface Props {
  ad: AdSummary
}

const platformColors: Record<string, string> = {
  meta: 'bg-blue-100 text-blue-700',
  tiktok: 'bg-gray-900 text-white',
  google: 'bg-red-100 text-red-700',
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
      className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow group"
    >
      {/* Thumbnail */}
      <div className="relative aspect-video bg-gray-100">
        {ad.thumbnail_url ? (
          <img
            src={ad.thumbnail_url}
            alt={ad.headline || 'Ad'}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
            No preview
          </div>
        )}
        {/* Platform badge */}
        <span
          className={`absolute top-2 left-2 px-2 py-0.5 rounded text-xs font-semibold ${
            platformColors[ad.platform] || 'bg-gray-100 text-gray-700'
          }`}
        >
          {ad.platform === 'meta' ? 'Facebook' : ad.platform}
        </span>
        {/* Ad type */}
        <span className="absolute top-2 right-2 px-2 py-0.5 rounded bg-black/50 text-white text-xs">
          {ad.ad_type}
        </span>
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
