import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ShoppingBag, TrendingUp, Star } from 'lucide-react'
import { searchProducts, getTrending } from '../api/tiktokShop'

function formatVND(n: number): string {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(n)
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}

export default function TikTokShopPage() {
  const [query, setQuery] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState('sales')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['tiktok-shop', query, category, sort, page],
    queryFn: () => searchProducts({ q: query, category: category || undefined, sort, page, limit: 20 }),
  })

  const { data: trending } = useQuery({
    queryKey: ['tiktok-shop-trending'],
    queryFn: () => getTrending({ limit: 10 }),
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setQuery(searchInput)
    setPage(1)
  }

  const totalPages = data ? Math.ceil(data.total / 20) : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ShoppingBag size={24} />
          TikTok Shop VN
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Theo dõi sản phẩm, doanh thu và xu hướng trên TikTok Shop
        </p>
      </div>

      {/* Search + Filters */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Tìm sản phẩm..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <select
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="">Tất cả danh mục</option>
          <option value="Làm đẹp">Làm đẹp</option>
          <option value="Thời trang nữ">Thời trang nữ</option>
          <option value="Thời trang nam">Thời trang nam</option>
          <option value="Điện tử">Điện tử</option>
          <option value="Nhà cửa">Nhà cửa</option>
          <option value="Mẹ & Bé">Mẹ & Bé</option>
          <option value="Thực phẩm">Thực phẩm</option>
          <option value="Sức khỏe">Sức khỏe</option>
        </select>
        <select
          value={sort}
          onChange={(e) => { setSort(e.target.value); setPage(1) }}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
        >
          <option value="sales">Bán chạy nhất</option>
          <option value="revenue">Doanh thu cao</option>
          <option value="price">Giá thấp</option>
          <option value="rating">Đánh giá cao</option>
        </select>
        <button
          type="submit"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
        >
          Tìm
        </button>
      </form>

      {/* Trending section */}
      {trending && trending.results.length > 0 && !query && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-3">
            <TrendingUp size={20} />
            Sản phẩm trending
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {trending.results.slice(0, 5).map((p) => (
              <div key={p.product_id} className="bg-white border border-gray-200 rounded-lg p-3">
                <p className="text-sm font-medium text-gray-900 line-clamp-2">{p.product_name}</p>
                <p className="text-xs text-primary-600 font-semibold mt-1">{formatVND(p.price)}</p>
                <p className="text-xs text-gray-500 mt-1">{formatNumber(p.sales_count)} đã bán</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Results */}
      <div>
        <p className="text-sm text-gray-500 mb-3">
          {data ? `${data.total.toLocaleString()} sản phẩm` : 'Đang tải...'}
        </p>

        {isLoading ? (
          <div className="text-center py-12 text-gray-400">Đang tải...</div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left">
                <tr>
                  <th className="px-4 py-3 font-medium text-gray-500">Sản phẩm</th>
                  <th className="px-4 py-3 font-medium text-gray-500 text-right">Giá</th>
                  <th className="px-4 py-3 font-medium text-gray-500 text-right">Đã bán</th>
                  <th className="px-4 py-3 font-medium text-gray-500 text-right">Đánh giá</th>
                  <th className="px-4 py-3 font-medium text-gray-500 text-right">Doanh thu/ngày</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data?.results.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900 line-clamp-1">{p.product_name}</p>
                        {p.category && (
                          <span className="text-xs text-gray-400">{p.category}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <span className="text-primary-600 font-medium">{formatVND(p.price)}</span>
                      {p.original_price && p.original_price > p.price && (
                        <span className="text-xs text-gray-400 line-through ml-1">
                          {formatVND(p.original_price)}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-medium">{formatNumber(p.sales_count)}</td>
                    <td className="px-4 py-3 text-right">
                      {p.rating ? (
                        <span className="flex items-center justify-end gap-1">
                          <Star size={12} className="text-yellow-400 fill-yellow-400" />
                          {p.rating.toFixed(1)}
                        </span>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {p.estimated_daily_revenue
                        ? formatVND(p.estimated_daily_revenue)
                        : '—'}
                    </td>
                  </tr>
                ))}
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
