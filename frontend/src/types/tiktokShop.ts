export interface TikTokProduct {
  id: string
  product_id: string
  product_name: string
  price: number
  original_price: number | null
  sales_count: number
  rating: number | null
  category: string | null
  estimated_daily_revenue: number | null
}

export interface TikTokProductDetail extends TikTokProduct {
  product_url: string | null
  review_count: number
  images: string[] | null
  daily_sales: Array<{
    date: string
    sales_delta: number
    total_sales: number
    revenue_est: number
  }> | null
  estimated_monthly_revenue: number | null
}

export interface TikTokShop {
  id: string
  shop_id: string
  shop_name: string
  followers: number
  rating: number | null
  total_products: number
  is_verified: boolean
  products: Array<{
    product_id: string
    product_name: string
    price: number
    sales_count: number
  }>
}

export interface ProductSearchResponse {
  total: number
  page: number
  limit: number
  results: TikTokProduct[]
}
