import client from './client'

export interface CompetitorAlert {
  id: string
  name: string
  alert_type: string
  match_value: string
  platforms: string[] | null
  is_active: boolean
  last_checked: string | null
  last_found_count: number
  total_found: number
  created_at: string
}

export interface NotificationItem {
  id: string
  type: string
  title: string
  body: string | null
  data: Record<string, unknown> | null
  is_read: boolean
  created_at: string
}

// Alerts
export async function listAlerts() {
  const res = await client.get('/alerts')
  return res.data as CompetitorAlert[]
}

export async function createAlert(data: {
  name: string
  alert_type: string
  match_value: string
  platforms?: string[]
}) {
  const res = await client.post('/alerts', data)
  return res.data
}

export async function updateAlert(id: string, data: { name?: string; is_active?: boolean; platforms?: string[] }) {
  const res = await client.patch(`/alerts/${id}`, data)
  return res.data
}

export async function deleteAlert(id: string) {
  await client.delete(`/alerts/${id}`)
}

// Notifications
export async function listNotifications(page = 1) {
  const res = await client.get('/notifications', { params: { page } })
  return res.data as { total: number; page: number; results: NotificationItem[] }
}

export async function getUnreadCount() {
  const res = await client.get('/notifications/unread-count')
  return res.data as { count: number }
}

export async function markRead(id: string) {
  await client.post(`/notifications/${id}/read`)
}

export async function markAllRead() {
  await client.post('/notifications/read-all')
}
