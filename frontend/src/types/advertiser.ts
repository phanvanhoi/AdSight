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
