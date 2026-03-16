import client from './client'
import type { SearchParams, SearchResponse, AdDetail } from '../types/ad'

export async function searchAds(params: SearchParams): Promise<SearchResponse> {
  const cleanParams = Object.fromEntries(
    Object.entries(params).filter(([_, v]) => v !== undefined && v !== null && v !== '')
  )
  const res = await client.get('/ads/search', { params: cleanParams })
  return res.data
}

export async function getAdDetail(id: string): Promise<AdDetail> {
  const res = await client.get(`/ads/${id}`)
  return res.data
}

export async function exportCsv(params: SearchParams) {
  const res = await client.get('/export/csv', {
    params,
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = 'ads_export.csv'
  a.click()
  window.URL.revokeObjectURL(url)
}
