import { useState } from 'react'
import { Search } from 'lucide-react'

interface Props {
  initialQuery?: string
  onSearch: (query: string) => void
  platform: string
  onPlatformChange: (platform: string) => void
}

const PLATFORMS = [
  { value: '', label: 'Tất cả' },
  { value: 'meta', label: 'Facebook/IG' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'google', label: 'Google' },
]

export default function SearchBar({ initialQuery = '', onSearch, platform, onPlatformChange }: Props) {
  const [query, setQuery] = useState(initialQuery)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(query)
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Tìm kiếm ads... ví dụ: kem chống nắng, thời trang, giảm giá"
          className="w-full pl-12 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent shadow-sm"
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700"
        >
          Tìm kiếm
        </button>
      </form>

      <div className="flex gap-2">
        {PLATFORMS.map((p) => (
          <button
            key={p.value}
            onClick={() => onPlatformChange(p.value)}
            className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
              platform === p.value
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>
    </div>
  )
}
