export interface AdvertiserGroup {
  id: string
  name: string
  slug: string
  platform_ids: Record<string, string[]> | null
  total_ads: number
  total_estimated_spend: number
  is_verified: boolean
}

export interface AdvertiserGroupDetail extends AdvertiserGroup {
  categories: Record<string, number> | null
}

export interface AdvertiserGroupsResponse {
  total: number
  page: number
  limit: number
  results: AdvertiserGroup[]
}

export interface AdvertiserAnalytics {
  platform_breakdown: Record<string, { count: number; total_spend: number }>
  ads_timeline: { month: string; count: number }[]
  category_breakdown: Record<string, number>
  top_ads: { id: string; headline: string | null; likes: number; viral_score: number; platform: string }[]
  ad_type_breakdown: Record<string, number>
  avg_engagement_rate: number
  avg_viral_score: number
  total_active_ads: number
  first_ad_date: string | null
  latest_ad_date: string | null
}

export interface AdvertiserAd {
  id: string
  platform: string
  advertiser_name: string | null
  headline: string | null
  ad_type: string
  first_seen: string | null
  likes: number
  viral_score: number | null
}
