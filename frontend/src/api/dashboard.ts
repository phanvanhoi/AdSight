import client from './client'

export async function getDashboardOverview() {
  const res = await client.get('/dashboard/overview')
  return res.data
}

export async function getTrendingAds() {
  const res = await client.get('/dashboard/trending')
  return res.data
}
