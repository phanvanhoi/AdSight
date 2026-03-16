import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Download, LayoutGrid, List } from 'lucide-react'
import { searchAds, exportCsv } from '../api/ads'
import SearchBar from '../components/search/SearchBar'
import FilterPanel from '../components/search/FilterPanel'
import AdGrid from '../components/search/AdGrid'
import type { SearchParams } from '../types/ad'

export default function Search() {
  const navigate = useNavigate()
  const [params, setParams] = useState<SearchParams>({
    q: '',
    platform: '',
    country: 'VN',
    ad_type: '',
    sort: 'newest',
    min_likes: undefined,
    page: 1,
    limit: 20,
  })

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const [filters, setFilters] = useState({
    country: 'VN',
    ad_type: '',
    sort: 'newest',
    min_likes: '',
  })

  const { data, isLoading } = useQuery({
    queryKey: ['ads', params],
    queryFn: () => searchAds(params),
  })

  const handleSearch = (q: string) => {
    setParams((prev) => ({ ...prev, q, page: 1 }))
  }

  const handlePlatformChange = (platform: string) => {
    setParams((prev) => ({ ...prev, platform, page: 1 }))
  }

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setParams((prev) => ({
      ...prev,
      [key]: key === 'min_likes' ? (value ? parseInt(value) : undefined) : value,
      page: 1,
    }))
  }

  const handlePageChange = (page: number) => {
    setParams((prev) => ({ ...prev, page }))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const totalPages = data ? Math.ceil(data.total / (params.limit || 20)) : 0

  return (
    <div className="space-y-6">
      <SearchBar
        initialQuery={params.q}
        onSearch={handleSearch}
        platform={params.platform || ''}
        onPlatformChange={handlePlatformChange}
      />

      <div className="flex gap-6">
        {/* Sidebar filters */}
        <div className="hidden lg:block w-64 flex-shrink-0">
          <FilterPanel filters={filters} onChange={handleFilterChange} />
        </div>

        {/* Results */}
        <div className="flex-1 space-y-4">
          {/* Result count + view toggle + export */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {data ? `${data.total.toLocaleString()} kết quả` : 'Đang tải...'}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-primary-100 text-primary-700' : 'text-gray-400 hover:text-gray-600'}`}
              >
                <LayoutGrid size={18} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-primary-100 text-primary-700' : 'text-gray-400 hover:text-gray-600'}`}
              >
                <List size={18} />
              </button>
              {data && data.total > 0 && (
                <button
                  onClick={() => exportCsv(params)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 ml-2"
                >
                  <Download size={14} />
                  Export CSV
                </button>
              )}
            </div>
          </div>

          {/* Facets */}
          {data?.facets && (
            <div className="flex gap-2 flex-wrap">
              {Object.entries(data.facets.platforms).map(([name, count]) => (
                <span key={name} className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-600">
                  {name}: {count}
                </span>
              ))}
            </div>
          )}

          {/* Ad Grid / List */}
          {viewMode === 'grid' ? (
            <AdGrid ads={data?.results || []} loading={isLoading} />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-left">
                  <tr>
                    <th className="px-4 py-3 font-medium text-gray-500">Ads</th>
                    <th className="px-4 py-3 font-medium text-gray-500">Nhà quảng cáo</th>
                    <th className="px-4 py-3 font-medium text-gray-500">Platform</th>
                    <th className="px-4 py-3 font-medium text-gray-500 text-right">Likes</th>
                    <th className="px-4 py-3 font-medium text-gray-500 text-right">Comments</th>
                    <th className="px-4 py-3 font-medium text-gray-500 text-right">Shares</th>
                    <th className="px-4 py-3 font-medium text-gray-500 text-right">Running</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {isLoading ? (
                    <tr><td colSpan={7} className="px-4 py-12 text-center text-gray-400">Đang tải...</td></tr>
                  ) : (data?.results || []).length === 0 ? (
                    <tr><td colSpan={7} className="px-4 py-12 text-center text-gray-500">Không tìm thấy ads nào. Thử từ khóa khác.</td></tr>
                  ) : (
                    (data?.results || []).map((ad) => (
                      <tr key={ad.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/ads/${ad.id}`)}>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            {ad.thumbnail_url && (
                              <img src={ad.thumbnail_url} alt="" className="w-12 h-8 rounded object-cover flex-shrink-0" />
                            )}
                            <span className="font-medium text-gray-900 line-clamp-1">{ad.headline || ad.body_text?.slice(0, 60) || '—'}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{ad.advertiser_name || '—'}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 capitalize">{ad.platform}</span>
                        </td>
                        <td className="px-4 py-3 text-right">{ad.likes.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right">{ad.comments.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right">{ad.shares.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right text-gray-500">{ad.days_running}d</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 pt-4">
              {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => handlePageChange(page)}
                  className={`px-3 py-1.5 text-sm rounded-lg ${
                    page === params.page
                      ? 'bg-primary-600 text-white'
                      : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
