import { useState, useEffect, useRef } from 'react'
import { Search } from 'lucide-react'
import { searchSuggest } from '../../api/ads'

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
  const [suggestions, setSuggestions] = useState<{ text: string; score: number }[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIdx, setSelectedIdx] = useState(-1)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()
  const wrapperRef = useRef<HTMLDivElement>(null)

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const fetchSuggestions = (q: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (q.length < 2) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchSuggest(q, 5)
        setSuggestions(results)
        setShowSuggestions(results.length > 0)
        setSelectedIdx(-1)
      } catch {
        setSuggestions([])
        setShowSuggestions(false)
      }
    }, 300)
  }

  const handleInputChange = (value: string) => {
    setQuery(value)
    fetchSuggestions(value)
  }

  const handleSelect = (text: string) => {
    setQuery(text)
    setShowSuggestions(false)
    onSearch(text)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setShowSuggestions(false)
    onSearch(query)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIdx((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIdx((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1))
    } else if (e.key === 'Enter' && selectedIdx >= 0) {
      e.preventDefault()
      handleSelect(suggestions[selectedIdx].text)
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
    }
  }

  return (
    <div className="space-y-3">
      <div ref={wrapperRef} className="relative">
        <form onSubmit={handleSubmit}>
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
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

        {/* Autocomplete dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSelect(s.text)}
                className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                  i === selectedIdx
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                {s.text}
              </button>
            ))}
          </div>
        )}
      </div>

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
