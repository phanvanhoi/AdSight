import client from './client'
import type { UserProfile } from '../types/billing'

export async function createCheckoutSession(plan: 'pro' | 'agency') {
  const res = await client.post('/billing/create-checkout-session', null, {
    params: { plan },
  })
  return res.data as { checkout_url: string; session_id: string }
}

export async function createPortalSession() {
  const res = await client.post('/billing/create-portal-session')
  return res.data as { portal_url: string }
}

// VNPay
export async function createVNPaySession(plan: 'pro' | 'agency') {
  const res = await client.post('/billing/vnpay/create', null, {
    params: { plan },
  })
  return res.data as { payment_url: string; order_id: string }
}

// MoMo
export async function createMoMoSession(plan: 'pro' | 'agency') {
  const res = await client.post('/billing/momo/create', null, {
    params: { plan },
  })
  return res.data as { pay_url: string; order_id: string; request_id: string }
}

export async function getMe() {
  const res = await client.get('/auth/me')
  return res.data as UserProfile
}

export async function updateSettings(data: { email_alerts_enabled?: boolean; full_name?: string }) {
  const res = await client.patch('/auth/settings', data)
  return res.data
}
