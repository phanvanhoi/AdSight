import client from './client'
import type { ProductSearchResponse, TikTokProductDetail, TikTokShop } from '../types/tiktokShop'

export async function searchProducts(params: {
  q?: string
  category?: string
  min_sales?: number
  max_price?: number
  sort?: string
  page?: number
  limit?: number
}): Promise<ProductSearchResponse> {
  const cleanParams = Object.fromEntries(
    Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== '')
  )
  const res = await client.get('/tiktok-shop/products', { params: cleanParams })
  return res.data
}

export async function getProduct(productId: string): Promise<TikTokProductDetail> {
  const res = await client.get(`/tiktok-shop/products/${productId}`)
  return res.data
}

export async function getShop(shopId: string): Promise<TikTokShop> {
  const res = await client.get(`/tiktok-shop/shops/${shopId}`)
  return res.data
}

export async function getTrending(params?: {
  category?: string
  limit?: number
}): Promise<{ period: string; results: TikTokProductDetail[] }> {
  const res = await client.get('/tiktok-shop/trending', { params })
  return res.data
}
