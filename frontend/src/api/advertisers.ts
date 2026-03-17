import client from './client'
import type { AdvertiserGroupsResponse, AdvertiserGroupDetail, AdvertiserAd, AdvertiserAnalytics } from '../types/advertiser'

export async function listAdvertiserGroups(params?: {
  q?: string
  sort?: string
  page?: number
  limit?: number
}): Promise<AdvertiserGroupsResponse> {
  const res = await client.get('/advertisers', { params })
  return res.data
}

export async function getAdvertiserGroup(groupId: string): Promise<AdvertiserGroupDetail> {
  const res = await client.get(`/advertisers/${groupId}`)
  return res.data
}

export async function getAdvertiserAnalytics(groupId: string): Promise<AdvertiserAnalytics> {
  const res = await client.get(`/advertisers/${groupId}/analytics`)
  return res.data
}

export async function getAdvertiserAds(groupId: string, params?: {
  platform?: string
  page?: number
  limit?: number
}): Promise<{ total: number; page: number; limit: number; results: AdvertiserAd[] }> {
  const res = await client.get(`/advertisers/${groupId}/ads`, { params })
  return res.data
}
