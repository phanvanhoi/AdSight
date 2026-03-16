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

export interface AdDetail extends AdSummary {
  advertiser_page_url: string | null
  media_urls: string[] | null
  landing_page_url: string | null
  target_countries: string[]
  target_age_min: number | null
  target_age_max: number | null
  target_gender: string | null
  impressions_lower: number | null
  impressions_upper: number | null
  spend_lower: number | null
  spend_upper: number | null
  // Enrichment — Categorizer
  category_l1: string | null
  category_l2: string | null
  detected_offers: string[] | null
  emotional_triggers: string[] | null
  target_audience_guess: string | null
  // Enrichment — Estimator
  estimated_daily_spend: number | null
  estimated_total_spend: number | null
  cpm_estimate: number | null
  engagement_rate: number | null
  viral_score: number | null
  is_hot: boolean
  // Creative metadata
  creative_phash: string | null
  dominant_colors: string[] | null
  has_text_overlay: boolean | null
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
