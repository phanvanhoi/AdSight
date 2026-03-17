import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

vi.mock('../api/billing', () => ({
  getMe: vi.fn(),
  updateSettings: vi.fn(),
  createPortalSession: vi.fn(),
  connectTelegram: vi.fn(),
  disconnectTelegram: vi.fn(),
}))

import Settings from '../pages/Settings'
import { getMe, updateSettings } from '../api/billing'

function renderSettings() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Settings />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

const mockProfile = {
  id: '1',
  email: 'test@test.com',
  full_name: 'Test User',
  tier: 'pro',
  subscription_status: 'active',
  usage: {
    searches: { used: 0, limit: -1 },
    ai_credits: { used: 0, limit: 50 },
    boards: { limit: -1 },
    saved_ads: { limit: -1 },
  },
  email_alerts_enabled: true,
  daily_digest_enabled: true,
  telegram_connected: false,
  telegram_enabled: false,
  stripe_publishable_key: '',
}

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getMe).mockResolvedValue(mockProfile)
    vi.mocked(updateSettings).mockResolvedValue({ ok: true })
  })

  it('renders notification toggles', async () => {
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText(/email khi đối thủ/i)).toBeInTheDocument()
      expect(screen.getByText(/Daily Digest/)).toBeInTheDocument()
    })
  })

  it('shows user email', async () => {
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText('test@test.com')).toBeInTheDocument()
    })
  })

  it('shows Telegram connect button when not connected', async () => {
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText(/Kết nối$/)).toBeInTheDocument()
    })
  })

  it('shows Telegram disconnect when connected', async () => {
    vi.mocked(getMe).mockResolvedValue({
      ...mockProfile,
      telegram_connected: true,
      telegram_enabled: true,
    })
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText(/Đã kết nối Telegram/)).toBeInTheDocument()
      expect(screen.getByText(/Ngắt kết nối/)).toBeInTheDocument()
    })
  })

  it('shows subscription tier', async () => {
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText(/pro/i)).toBeInTheDocument()
    })
  })

  it('shows upgrade button for free tier', async () => {
    vi.mocked(getMe).mockResolvedValue({
      ...mockProfile,
      tier: 'free',
      subscription_status: null,
    })
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText(/Nâng cấp/)).toBeInTheDocument()
    })
  })
})
