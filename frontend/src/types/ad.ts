export interface AdSummary {
  id: string
  platform: string
  advertiser_name: string | null
  ad_type: string
  headline: string | null
  body_text: string | null
  thumbnail_url: string | null
  cta_type: string | null
  likes: number
  comments: number
  shares: number
  first_seen: string | null
  last_seen: string | null
  is_active: boolean
  days_running: number
}

export interface Facets {
  platforms: Record<string, number>
  ad_types: Record<string, number>
  categories: Record<string, number>
}

export interface SearchResponse {
  total: number
  page: number
  limit: number
  results: AdSummary[]
  facets: Facets
}

export interface SearchParams {
  q?: string
  platform?: string
  country?: string
  ad_type?: string
  date_from?: string
  date_to?: string
  min_likes?: number
  sort?: string
  page?: number
  limit?: number
}
