import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Users, Search } from 'lucide-react'
import { listAdvertiserGroups } from '../api/advertisers'

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

export default function AdvertisersPage() {
  const [query, setQuery] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [sort, setSort] = useState('total_ads')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['advertisers', query, sort, page],
    queryFn: () => listAdvertiserGroups({ q: query || undefined, sort, page, limit: 20 }),
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setQuery(searchInput)
    setPage(1)
  }

  const totalPages = data ? Math.ceil(data.total / 20) : 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Users size={24} />
          Nhà quảng cáo
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Cross-platform advertiser profiles — cùng 1 brand trên nhiều nền tảng
        </p>
      </div>

      {/* Search + Sort */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Tìm nhà quảng cáo..."
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <select
          value={sort}
          onChange={(e) => { setSort(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="total_ads">Nhiều ads nhất</option>
          <option value="total_spend">Chi tiêu cao nhất</option>
          <option value="name">Tên A-Z</option>
        </select>
        <button
          type="submit"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          Tìm
        </button>
      </form>

      {/* Results */}
      <div>
        <p className="text-sm text-gray-500 mb-3">
          {data ? `${data.total.toLocaleString()} nhà quảng cáo` : 'Đang tải...'}
        </p>

        {isLoading ? (
          <div className="text-center py-12 text-gray-400">Đang tải...</div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {data?.results.map((g) => (
              <Link
                key={g.id}
                to={`/advertisers/${g.id}`}
                className="bg-white border border-gray-200 rounded-xl p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{g.name}</h3>
                    <div className="flex gap-1 mt-2">
                      {g.platform_ids && Object.keys(g.platform_ids).map((plat) => (
                        <span
                          key={plat}
                          className={`px-2 py-0.5 rounded text-xs font-medium ${
                            platformBadge[plat] || 'bg-gray-100 text-gray-600'
                          }`}
                        >
                          {plat === 'meta' ? 'Facebook' : plat}
                        </span>
                      ))}
                    </div>
                  </div>
                  {g.is_verified && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Verified</span>
                  )}
                </div>
                <div className="mt-3 flex gap-4 text-xs text-gray-500">
                  <span>{formatNumber(g.total_ads)} ads</span>
                  <span>
                    {new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', notation: 'compact' }).format(g.total_estimated_spend)} est. spend
                  </span>
                </div>
              </Link>
            ))}
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
