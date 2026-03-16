import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Download } from 'lucide-react'
import { searchAds, exportCsv } from '../api/ads'
import SearchBar from '../components/search/SearchBar'
import FilterPanel from '../components/search/FilterPanel'
import AdGrid from '../components/search/AdGrid'
import type { SearchParams } from '../types/ad'

export default function Search() {
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
          {/* Result count + export */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              {data ? `${data.total.toLocaleString()} ket qua` : 'Dang tai...'}
            </p>
            {data && data.total > 0 && (
              <button
                onClick={() => exportCsv(params)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <Download size={14} />
                Export CSV
              </button>
            )}
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

          {/* Ad Grid */}
          <AdGrid ads={data?.results || []} loading={isLoading} />

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
