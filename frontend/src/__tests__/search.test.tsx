import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Search from '../pages/Search'
import type { SearchResponse } from '../types/ad'

// Mock ads API
vi.mock('../api/ads', () => ({
  searchAds: vi.fn(),
  exportCsv: vi.fn(),
}))

import { searchAds } from '../api/ads'

const mockSearchResponse: SearchResponse = {
  total: 3,
  page: 1,
  limit: 20,
  results: [
    {
      id: 'ad-1',
      platform: 'meta',
      advertiser_name: 'Shop ABC',
      ad_type: 'video',
      headline: 'Sale 50% kem chong nang',
      body_text: 'Mua ngay hom nay',
      thumbnail_url: null,
      cta_type: 'SHOP_NOW',
      likes: 1200,
      comments: 45,
      shares: 23,
      first_seen: '2026-03-01T00:00:00Z',
      last_seen: '2026-03-15T00:00:00Z',
      is_active: true,
      days_running: 14,
    },
    {
      id: 'ad-2',
      platform: 'tiktok',
      advertiser_name: 'Fashion VN',
      ad_type: 'image',
      headline: 'Thoi trang mua he',
      body_text: 'Bo suu tap moi',
      thumbnail_url: null,
      cta_type: 'LEARN_MORE',
      likes: 800,
      comments: 20,
      shares: 10,
      first_seen: '2026-03-05T00:00:00Z',
      last_seen: '2026-03-15T00:00:00Z',
      is_active: true,
      days_running: 10,
    },
    {
      id: 'ad-3',
      platform: 'meta',
      advertiser_name: 'Tech Store',
      ad_type: 'carousel',
      headline: 'iPhone giam gia soc',
      body_text: 'Chi con 2 ngay',
      thumbnail_url: null,
      cta_type: 'SHOP_NOW',
      likes: 3500,
      comments: 120,
      shares: 89,
      first_seen: '2026-03-10T00:00:00Z',
      last_seen: '2026-03-15T00:00:00Z',
      is_active: true,
      days_running: 5,
    },
  ],
  facets: {
    platforms: { meta: 2, tiktok: 1 },
    ad_types: { video: 1, image: 1, carousel: 1 },
    categories: {},
  },
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Search Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders search bar with input and button', async () => {
    vi.mocked(searchAds).mockResolvedValue(mockSearchResponse)
    renderWithProviders(<Search />)

    expect(
      screen.getByPlaceholderText('Tim kiem ads... vi du: kem chong nang, thoi trang, giam gia'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tim kiem' })).toBeInTheDocument()
  })

  it('submits search and calls API with correct params', async () => {
    const user = userEvent.setup()
    vi.mocked(searchAds).mockResolvedValue(mockSearchResponse)

    renderWithProviders(<Search />)

    const input = screen.getByPlaceholderText(
      'Tim kiem ads... vi du: kem chong nang, thoi trang, giam gia',
    )
    await user.type(input, 'kem chong nang')
    await user.click(screen.getByRole('button', { name: 'Tim kiem' }))

    await waitFor(() => {
      const calls = vi.mocked(searchAds).mock.calls
      const lastCall = calls[calls.length - 1][0]
      expect(lastCall.q).toBe('kem chong nang')
    })
  })

  it('renders search results correctly', async () => {
    vi.mocked(searchAds).mockResolvedValue(mockSearchResponse)
    renderWithProviders(<Search />)

    await waitFor(() => {
      expect(screen.getByText('3 ket qua')).toBeInTheDocument()
    })

    expect(screen.getByText('Sale 50% kem chong nang')).toBeInTheDocument()
    expect(screen.getByText('Thoi trang mua he')).toBeInTheDocument()
    expect(screen.getByText('iPhone giam gia soc')).toBeInTheDocument()
  })

  it('shows empty state when no results', async () => {
    vi.mocked(searchAds).mockResolvedValue({
      total: 0,
      page: 1,
      limit: 20,
      results: [],
      facets: { platforms: {}, ad_types: {}, categories: {} },
    })

    renderWithProviders(<Search />)

    await waitFor(() => {
      expect(screen.getByText('0 ket qua')).toBeInTheDocument()
    })
    expect(
      screen.getByText('Khong tim thay ads nao. Thu tu khoa khac.'),
    ).toBeInTheDocument()
  })

  it('renders platform filter buttons', async () => {
    vi.mocked(searchAds).mockResolvedValue(mockSearchResponse)
    renderWithProviders(<Search />)

    expect(screen.getByRole('button', { name: 'Tat ca' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Facebook/IG' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'TikTok' })).toBeInTheDocument()
  })

  it('clicking platform filter triggers new search', async () => {
    const user = userEvent.setup()
    vi.mocked(searchAds).mockResolvedValue(mockSearchResponse)

    renderWithProviders(<Search />)

    await user.click(screen.getByRole('button', { name: 'TikTok' }))

    await waitFor(() => {
      const calls = vi.mocked(searchAds).mock.calls
      const lastCall = calls[calls.length - 1][0]
      expect(lastCall.platform).toBe('tiktok')
    })
  })

  it('shows pagination when multiple pages exist', async () => {
    vi.mocked(searchAds).mockResolvedValue({
      ...mockSearchResponse,
      total: 100,
      limit: 20,
    })

    renderWithProviders(<Search />)

    await waitFor(() => {
      expect(screen.getByText('100 ket qua')).toBeInTheDocument()
    })

    // 100 / 20 = 5 pages
    expect(screen.getByRole('button', { name: '1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '2' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '5' })).toBeInTheDocument()
  })

  it('does not show pagination for single page results', async () => {
    vi.mocked(searchAds).mockResolvedValue(mockSearchResponse) // total: 3, limit: 20
    renderWithProviders(<Search />)

    await waitFor(() => {
      expect(screen.getByText('3 ket qua')).toBeInTheDocument()
    })

    // No page buttons should exist
    expect(screen.queryByRole('button', { name: '2' })).not.toBeInTheDocument()
  })
})
